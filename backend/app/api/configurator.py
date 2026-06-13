from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any
from ..database import get_db
from ..models import Organ, GenomeDraft
from ..llm.provider import get_provider
from ..services.organ_seed import BANK_LABEL, BANK_HINT

router = APIRouter(prefix="/api/configurator", tags=["configurator"])


@router.get("/banks")
def list_banks(db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = (
        db.query(Organ.bank, func.count(Organ.id))
        .group_by(Organ.bank)
        .all()
    )
    counts = dict(rows)
    return [
        {
            "bank": b,
            "label": BANK_LABEL.get(b, b),
            "hint": BANK_HINT.get(b, ""),
            "count": counts.get(b, 0),
            "is_degradation": b == "degradation",
        }
        for b in BANK_LABEL.keys()
    ]


@router.get("/organs")
def list_organs(
    db: Session = Depends(get_db),
    bank: Optional[str] = None,
):
    q = db.query(Organ)
    if bank:
        q = q.filter(Organ.bank == bank)
    rows = q.order_by(Organ.bank, Organ.name).all()
    return [
        {"id": o.id, "bank": o.bank, "code": o.code, "name": o.name,
         "description": o.description, "source": o.source}
        for o in rows
    ]


class DraftIn(BaseModel):
    name: str
    function: Optional[str] = None
    verb: Optional[str] = None
    maturity_stage: int = 1
    selected_organs: dict[str, list[str]] = {}  # {bank: [organ_id, ...]}


@router.post("/drafts")
def create_draft(
    payload: DraftIn,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    d = GenomeDraft(
        name=payload.name,
        function=payload.function,
        verb=payload.verb,
        maturity_stage=max(0, min(5, payload.maturity_stage)),
        selected_organs=payload.selected_organs,
        player_token=x_player_token,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return _serialize(d)


@router.get("/drafts")
def list_drafts(
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
    mine: bool = Query(False, description="filter by current X-Player-Token"),
):
    q = db.query(GenomeDraft)
    if mine and x_player_token:
        q = q.filter(GenomeDraft.player_token == x_player_token)
    rows = q.order_by(GenomeDraft.updated_at.desc()).all()
    return [_serialize(d) for d in rows]


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    d = db.query(GenomeDraft).filter(GenomeDraft.id == draft_id).first()
    if not d:
        raise HTTPException(404, "no draft")
    return _serialize(d)


class DraftPatch(BaseModel):
    name: Optional[str] = None
    function: Optional[str] = None
    verb: Optional[str] = None
    maturity_stage: Optional[int] = None
    selected_organs: Optional[dict[str, list[str]]] = None


@router.patch("/drafts/{draft_id}")
def patch_draft(draft_id: str, payload: DraftPatch, db: Session = Depends(get_db)):
    d = db.query(GenomeDraft).filter(GenomeDraft.id == draft_id).first()
    if not d:
        raise HTTPException(404, "no draft")
    if payload.name is not None: d.name = payload.name
    if payload.function is not None: d.function = payload.function
    if payload.verb is not None: d.verb = payload.verb
    if payload.maturity_stage is not None:
        d.maturity_stage = max(0, min(5, payload.maturity_stage))
    if payload.selected_organs is not None:
        d.selected_organs = payload.selected_organs
    db.commit()
    db.refresh(d)
    return _serialize(d)


class WeaverRequest(BaseModel):
    model: Optional[str] = None


@router.post("/drafts/{draft_id}/weaver")
def run_weaver(
    draft_id: str,
    payload: WeaverRequest,
    db: Session = Depends(get_db),
):
    d = db.query(GenomeDraft).filter(GenomeDraft.id == draft_id).first()
    if not d:
        raise HTTPException(404, "no draft")
    organs_by_bank = _resolve_organ_names(db, d.selected_organs or {})
    draft_view = {
        "name": d.name, "function": d.function, "verb": d.verb,
        "maturity_stage": d.maturity_stage,
    }
    provider = get_provider()
    out = provider.call_role(
        "playability_critic",
        {"draft": draft_view, "organs_by_bank": organs_by_bank},
        model=payload.model,
    )
    out.pop("_prompt_spec", None)
    out.pop("_role", None)
    d.weaver_verdict = out
    db.commit()
    db.refresh(d)
    return {"draft": _serialize(d), "verdict": out}


def _resolve_organ_names(db: Session, selected: dict[str, list[str]]) -> dict[str, list[str]]:
    """Replace organ IDs with their human names for the LLM prompt."""
    out: dict[str, list[str]] = {}
    all_ids = [oid for ids in selected.values() for oid in ids]
    if not all_ids:
        return out
    rows = db.query(Organ).filter(Organ.id.in_(all_ids)).all()
    by_id = {o.id: o.name for o in rows}
    for bank, ids in selected.items():
        out[bank] = [by_id[i] for i in ids if i in by_id]
    return out


def _serialize(d: GenomeDraft) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "function": d.function,
        "verb": d.verb,
        "maturity_stage": d.maturity_stage,
        "selected_organs": d.selected_organs or {},
        "weaver_verdict": d.weaver_verdict,
        "player_token": d.player_token,
        "created_at": d.created_at.isoformat() + "Z" if d.created_at else None,
        "updated_at": d.updated_at.isoformat() + "Z" if d.updated_at else None,
    }
