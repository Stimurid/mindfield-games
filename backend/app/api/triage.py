"""Phase 14: triage 4200 — assign one of 9 §4 fates to a corpus entry.

When the fate is 'extract_organ', the player additionally picks a bank
and names the organ; a new Organ row is created with source='extracted'
and source_entry_id pointing at the card. The configurator (Phase 13)
then sees this organ in its bank like any canonical one.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_db
from ..models import CorpusEntry, Organ, TriageVerdict
from ..services.organ_seed import BANK_LABEL


router = APIRouter(prefix="/api/triage", tags=["triage"])


FATES = [
    "bury",                  # похоронить
    "extract_organ",         # извлечь орган
    "keep_seed",             # оставить семенем
    "shrink_to_exercise",    # сжать до упражнения
    "lift_to_game_exercise", # поднять до игры-упражнения
    "cross",                 # скрестить
    "breed",                 # вырастить как породу
    "defer_to_interface",    # отложить до интерфейса
    "forbid",                # запретить/ограничить
]


FATE_LABEL = {
    "bury":                  "Похоронить",
    "extract_organ":         "Извлечь орган",
    "keep_seed":             "Оставить семенем",
    "shrink_to_exercise":    "Сжать до упражнения",
    "lift_to_game_exercise": "Поднять до игры-упражнения",
    "cross":                 "Скрестить",
    "breed":                 "Вырастить как породу",
    "defer_to_interface":    "Отложить до интерфейса",
    "forbid":                "Запретить",
}


class TriageRequest(BaseModel):
    fate: str
    note: Optional[str] = None
    # Only used when fate == "extract_organ":
    organ_bank: Optional[str] = None
    organ_name: Optional[str] = None


def _slug(s: str) -> str:
    import re
    s = s.lower().strip()
    s = re.sub(r"[ /]+", "_", s)
    s = re.sub(r"[^a-zа-яё0-9_]", "", s)
    return s or "_"


@router.post("/entries/{entry_id}")
def assign_fate(
    entry_id: str,
    payload: TriageRequest,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    e = db.query(CorpusEntry).filter(CorpusEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "no such corpus entry")
    if payload.fate not in FATES:
        raise HTTPException(400, f"fate must be one of {FATES}")

    extracted_organ_id: Optional[str] = None
    if payload.fate == "extract_organ":
        if not payload.organ_bank or payload.organ_bank not in BANK_LABEL:
            raise HTTPException(400, f"organ_bank must be one of {list(BANK_LABEL.keys())}")
        if not payload.organ_name or len(payload.organ_name.strip()) < 2:
            raise HTTPException(400, "organ_name required when fate is extract_organ")
        # De-dup by (bank, slug-of-name) — extracting the same organ from the
        # same card twice is a no-op.
        code = f"{payload.organ_bank}.{_slug(payload.organ_name)}_from_{e.code[-12:]}"
        existing = db.query(Organ).filter(Organ.code == code).first()
        if existing:
            extracted_organ_id = existing.id
        else:
            o = Organ(
                bank=payload.organ_bank,
                code=code,
                name=payload.organ_name.strip(),
                description=f"extracted from {e.code} · {e.title[:80]}",
                source="extracted",
                source_entry_id=e.id,
            )
            db.add(o)
            db.flush()
            extracted_organ_id = o.id

    v = TriageVerdict(
        entry_id=e.id,
        player_token=x_player_token,
        fate=payload.fate,
        note=payload.note,
        extracted_organ_id=extracted_organ_id,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return _serialize(v)


@router.get("/entries/{entry_id}")
def list_for_entry(entry_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(TriageVerdict)
        .filter(TriageVerdict.entry_id == entry_id)
        .order_by(TriageVerdict.created_at.desc())
        .all()
    )
    return [_serialize(v) for v in rows]


@router.get("/queue")
def triage_queue(
    db: Session = Depends(get_db),
    kind: str = Query("source_card", description="corpus entry kind to triage"),
    limit: int = Query(25, ge=1, le=100),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    """Return next entries that the current player_token has NOT yet triaged."""
    already = (
        db.query(TriageVerdict.entry_id)
        .filter(TriageVerdict.player_token == x_player_token)
        .subquery()
    )
    q = (
        db.query(CorpusEntry)
        .filter(CorpusEntry.kind == kind)
        .filter(~CorpusEntry.id.in_(already))
        .order_by(CorpusEntry.order_key, CorpusEntry.code)
        .limit(limit)
    )
    rows = q.all()
    return [
        {"id": e.id, "code": e.code, "title": e.title, "kind": e.kind, "body_md": e.body_md}
        for e in rows
    ]


@router.get("/stats")
def triage_stats(
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
    mine: bool = Query(False),
):
    q = db.query(TriageVerdict.fate, func.count(TriageVerdict.id))
    if mine and x_player_token:
        q = q.filter(TriageVerdict.player_token == x_player_token)
    by_fate = dict(q.group_by(TriageVerdict.fate).all())

    total_q = db.query(func.count(TriageVerdict.id))
    if mine and x_player_token:
        total_q = total_q.filter(TriageVerdict.player_token == x_player_token)
    total = total_q.scalar() or 0

    extracted = (
        db.query(func.count(Organ.id))
        .filter(Organ.source == "extracted")
        .scalar()
        or 0
    )
    return {
        "total_verdicts": total,
        "by_fate": [
            {"fate": f, "label": FATE_LABEL[f], "count": by_fate.get(f, 0)}
            for f in FATES
        ],
        "extracted_organs": extracted,
    }


@router.get("/fates")
def list_fates():
    return [{"fate": f, "label": FATE_LABEL[f]} for f in FATES]


def _serialize(v: TriageVerdict) -> dict:
    return {
        "id": v.id,
        "entry_id": v.entry_id,
        "fate": v.fate,
        "note": v.note,
        "extracted_organ_id": v.extracted_organ_id,
        "player_token": v.player_token,
        "created_at": v.created_at.isoformat() + "Z" if v.created_at else None,
    }
