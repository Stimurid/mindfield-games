"""Phase 17: researcher workbench — hypotheses + organ discussion."""
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any
from ..database import get_db
from ..models import Hypothesis, HypothesisDiscussion, GenomeDraft
from ..llm.provider import get_provider


router = APIRouter(prefix="/api/research", tags=["research"])


class HypothesisIn(BaseModel):
    title: str
    body_md: Optional[str] = ""
    status: Optional[str] = "draft"
    tags: Optional[list[str]] = []
    linked_draft_id: Optional[str] = None


class HypothesisPatch(BaseModel):
    title: Optional[str] = None
    body_md: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    linked_draft_id: Optional[str] = None


class SummonRequest(BaseModel):
    role: str
    angle: Optional[str] = None
    model: Optional[str] = None


@router.post("/hypotheses")
def create_hypothesis(
    payload: HypothesisIn,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    h = Hypothesis(
        title=payload.title,
        body_md=payload.body_md or "",
        status=payload.status or "draft",
        tags=payload.tags or [],
        linked_draft_id=payload.linked_draft_id,
        player_token=x_player_token,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return _serialize(h)


@router.get("/hypotheses")
def list_hypotheses(
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
    mine: bool = Query(False),
):
    q = db.query(Hypothesis)
    if mine and x_player_token:
        q = q.filter(Hypothesis.player_token == x_player_token)
    rows = q.order_by(Hypothesis.updated_at.desc()).all()
    return [_serialize(h) for h in rows]


@router.get("/hypotheses/{hyp_id}")
def get_hypothesis(hyp_id: str, db: Session = Depends(get_db)):
    h = db.query(Hypothesis).filter(Hypothesis.id == hyp_id).first()
    if not h:
        raise HTTPException(404, "no hypothesis")
    return _serialize(h)


@router.patch("/hypotheses/{hyp_id}")
def patch_hypothesis(hyp_id: str, payload: HypothesisPatch, db: Session = Depends(get_db)):
    h = db.query(Hypothesis).filter(Hypothesis.id == hyp_id).first()
    if not h:
        raise HTTPException(404, "no hypothesis")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    db.commit()
    db.refresh(h)
    return _serialize(h)


@router.delete("/hypotheses/{hyp_id}")
def delete_hypothesis(hyp_id: str, db: Session = Depends(get_db)):
    h = db.query(Hypothesis).filter(Hypothesis.id == hyp_id).first()
    if not h:
        raise HTTPException(404, "no hypothesis")
    db.delete(h)
    db.commit()
    return {"deleted": hyp_id}


@router.get("/hypotheses/{hyp_id}/discussions")
def list_discussions(hyp_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(HypothesisDiscussion)
        .filter(HypothesisDiscussion.hypothesis_id == hyp_id)
        .order_by(HypothesisDiscussion.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": c.id, "role": c.role, "angle": c.angle, "output": c.output,
            "model": c.model,
            "created_at": c.created_at.isoformat() + "Z" if c.created_at else None,
        }
        for c in rows
    ]


def _context_for_role(role: str, title: str, body: str, angle: Optional[str]) -> dict:
    text = f"{title}\n\n{body[:1500]}"
    if role == "prosecutor":
        return {"phrase": text, "claimed_operation": angle or "claims a discriminating operation"}
    if role == "spackler":
        return {"gap_context": text, "absence_type": angle or "logical"}
    if role == "sprout_advocate":
        return {"card_text": text, "fate": angle or "incubate"}
    if role == "literal_alien":
        return {"phrase": text, "medium": angle or "research_note"}
    raise HTTPException(400, f"unsupported role {role}")


@router.post("/hypotheses/{hyp_id}/summon")
def summon(
    hyp_id: str,
    payload: SummonRequest,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    h = db.query(Hypothesis).filter(Hypothesis.id == hyp_id).first()
    if not h:
        raise HTTPException(404, "no hypothesis")
    if payload.role not in {"prosecutor", "spackler", "sprout_advocate", "literal_alien"}:
        raise HTTPException(400, "role must be one of the 4 organ roles")
    ctx = _context_for_role(payload.role, h.title, h.body_md or "", payload.angle)
    provider = get_provider()
    out = provider.call_role(payload.role, ctx, model=payload.model)
    out.pop("_prompt_spec", None)
    out.pop("_role", None)
    used_model = out.pop("_model", None) or provider.default_model
    c = HypothesisDiscussion(
        hypothesis_id=h.id,
        role=payload.role,
        angle=payload.angle,
        output=out,
        model=used_model,
        player_token=x_player_token,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {
        "id": c.id, "role": c.role, "angle": c.angle, "output": c.output,
        "model": c.model,
        "created_at": c.created_at.isoformat() + "Z" if c.created_at else None,
    }


def _serialize(h: Hypothesis) -> dict[str, Any]:
    return {
        "id": h.id,
        "title": h.title,
        "body_md": h.body_md or "",
        "status": h.status,
        "tags": h.tags or [],
        "linked_draft_id": h.linked_draft_id,
        "player_token": h.player_token,
        "created_at": h.created_at.isoformat() + "Z" if h.created_at else None,
        "updated_at": h.updated_at.isoformat() + "Z" if h.updated_at else None,
    }
