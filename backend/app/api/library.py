from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db, engine
from ..models import CorpusEntry, CorpusLink, LibraryComment, Material
from ..llm.provider import get_provider
from ..services.corpus_to_material import convert_entry_to_material_payload
from ..services.replay_mutator import MutatorError

router = APIRouter(prefix="/api/library", tags=["library"])


_KIND_LABEL = {
    "attractor":      "Аттракторы",
    "r_root":         "Корневые операционные аттракторы",
    "breed":          "Породы",
    "chimera":        "Химерная матрица",
    "precard":        "Карточки 1-7",
    "residual":       "Остатки",
    "genome":         "Геномы первых четырёх",
    "appspec":        "App-spec",
    "phase_doc":      "Документы фаз разработки",
    "micro_game":     "Микро-игры внутри аттракторов (малое/игра/большой)",
    "micro_numbered": "Нумерованные пункты",
    "micro_bullet":   "Bullet-пункты",
    "micro_aspect":   "Аспекты внутри пород / R-корней",
    "source_section": "Разделы исходного корпуса 4200",
    "source_card":    "Сырые карточки 4200",
}


@router.get("/sections")
def list_sections(db: Session = Depends(get_db)):
    rows = (
        db.query(CorpusEntry.kind, func.count(CorpusEntry.id))
        .group_by(CorpusEntry.kind)
        .all()
    )
    return [
        {"kind": k, "label": _KIND_LABEL.get(k, k), "count": c}
        for k, c in sorted(rows, key=lambda r: list(_KIND_LABEL.keys()).index(r[0]) if r[0] in _KIND_LABEL else 99)
    ]


@router.get("/entries")
def list_entries(
    db: Session = Depends(get_db),
    kind: str | None = None,
    pass_filter: str | None = Query(None, alias="pass"),
    limit: int = 500,
):
    q = db.query(CorpusEntry)
    if kind:
        q = q.filter(CorpusEntry.kind == kind)
    if pass_filter:
        q = q.filter(CorpusEntry.source_pass == pass_filter)
    rows = q.order_by(CorpusEntry.kind, CorpusEntry.order_key, CorpusEntry.code).limit(limit).all()
    return [
        {
            "id": e.id,
            "code": e.code,
            "kind": e.kind,
            "title": e.title,
            "source_pass": e.source_pass,
            "source_line": e.source_line,
        }
        for e in rows
    ]


@router.get("/entries/{entry_id}")
def get_entry(entry_id: str, db: Session = Depends(get_db)):
    e = db.query(CorpusEntry).filter(CorpusEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "no such corpus entry")
    parents = (
        db.query(CorpusEntry, CorpusLink.relation)
        .join(CorpusLink, CorpusLink.parent_id == CorpusEntry.id)
        .filter(CorpusLink.child_id == e.id)
        .all()
    )
    children = (
        db.query(CorpusEntry, CorpusLink.relation)
        .join(CorpusLink, CorpusLink.child_id == CorpusEntry.id)
        .filter(CorpusLink.parent_id == e.id)
        .all()
    )
    return {
        "id": e.id,
        "code": e.code,
        "kind": e.kind,
        "title": e.title,
        "body_md": e.body_md,
        "source_pass": e.source_pass,
        "source_line": e.source_line,
        "parents":  [{"id": p[0].id, "code": p[0].code, "title": p[0].title, "relation": p[1]} for p in parents],
        "children": [{"id": c[0].id, "code": c[0].code, "title": c[0].title, "relation": c[1]} for c in children],
    }


@router.get("/entries/{entry_id}/comments")
def list_comments(entry_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(LibraryComment)
        .filter(LibraryComment.entry_id == entry_id)
        .order_by(LibraryComment.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": c.id,
            "role": c.role,
            "angle": c.angle,
            "output": c.output,
            "model": c.model,
            "created_at": c.created_at.isoformat() + "Z" if c.created_at else None,
        }
        for c in rows
    ]


class SummonRequest(BaseModel):
    role: str
    angle: Optional[str] = None
    model: Optional[str] = None


def _context_for_role(role: str, entry_title: str, body: str, angle: str | None) -> dict:
    text_for_role = f"{entry_title}\n\n{body[:1500]}"
    if role == "prosecutor":
        return {"phrase": text_for_role, "claimed_operation": angle or "claims a discriminating operation"}
    if role == "spackler":
        return {"gap_context": text_for_role, "absence_type": angle or "logical"}
    if role == "sprout_advocate":
        return {"card_text": text_for_role, "fate": angle or "incubate"}
    if role == "literal_alien":
        return {"phrase": text_for_role, "medium": angle or "archival_text"}
    raise HTTPException(400, f"unsupported role {role}")


@router.post("/entries/{entry_id}/summon")
def summon_organ(
    entry_id: str,
    payload: SummonRequest,
    db: Session = Depends(get_db),
    x_player_token: str | None = Header(default=None, alias="X-Player-Token"),
):
    e = db.query(CorpusEntry).filter(CorpusEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "no such corpus entry")
    if payload.role not in {"prosecutor", "spackler", "sprout_advocate", "literal_alien"}:
        raise HTTPException(400, "role must be one of prosecutor/spackler/sprout_advocate/literal_alien")
    ctx = _context_for_role(payload.role, e.title, e.body_md, payload.angle)
    provider = get_provider()
    out = provider.call_role(payload.role, ctx, model=payload.model)
    spec = out.pop("_prompt_spec", None)
    out.pop("_role", None)
    used_model = out.pop("_model", None) or provider.default_model
    comment = LibraryComment(
        entry_id=e.id,
        role=payload.role,
        angle=payload.angle,
        output=out,
        player_token=x_player_token,
        model=used_model,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "role": comment.role,
        "angle": comment.angle,
        "output": comment.output,
        "model": comment.model,
        "created_at": comment.created_at.isoformat() + "Z" if comment.created_at else None,
    }


class ConvertRequest(BaseModel):
    game_id: str
    model: Optional[str] = None


@router.post("/entries/{entry_id}/convert")
def convert_entry_to_material(
    entry_id: str,
    payload: ConvertRequest,
    db: Session = Depends(get_db),
):
    e = db.query(CorpusEntry).filter(CorpusEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "no such corpus entry")
    try:
        new_title, new_payload = convert_entry_to_material_payload(e, payload.game_id, model=payload.model)
    except MutatorError as err:
        raise HTTPException(502, f"converter failure: {err}")
    mat = Material(
        game_id=payload.game_id,
        title=new_title,
        namespace="from_corpus",
        payload=new_payload,
        source_corpus_id=e.id,
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return {
        "material_id": mat.id,
        "game_id": mat.game_id,
        "title": mat.title,
        "namespace": mat.namespace,
        "source_corpus_id": e.id,
    }


@router.get("/search")
def search(q: str = Query(min_length=2), limit: int = 50, kind: str | None = None):
    # FTS5 expects a MATCH expression. Quote literally to avoid syntax errors.
    safe = q.replace('"', '""')
    fts_query = f'"{safe}"'
    sql = text(
        "SELECT e.id, e.code, e.kind, e.title, "
        "       snippet(corpus_fts, 1, '<mark>', '</mark>', '…', 18) AS snippet "
        "FROM corpus_fts JOIN corpus_entries e ON e.rowid = corpus_fts.rowid "
        "WHERE corpus_fts MATCH :q "
        + ("AND e.kind = :kind " if kind else "")
        + "ORDER BY rank LIMIT :limit"
    )
    with engine.connect() as conn:
        params = {"q": fts_query, "limit": limit}
        if kind:
            params["kind"] = kind
        rows = conn.execute(sql, params).fetchall()
    return [
        {"id": r[0], "code": r[1], "kind": r[2], "title": r[3], "snippet": r[4]}
        for r in rows
    ]
