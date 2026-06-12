from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GameSession, PlayerMove, LLMIntervention, Material
from ..schemas import SessionCreate, MoveCreate, InterventionRequest
from ..services.genome_loader import get_genome
from ..services.profile_builder import build_profile
from ..services.exporter import export_session_markdown, export_session_json
from ..llm.provider import get_provider
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _serialize_move(m: PlayerMove) -> dict:
    return {
        "id": m.id,
        "session_id": m.session_id,
        "round_id": m.round_id,
        "action": m.action,
        "target_unit_id": m.target_unit_id,
        "payload": m.payload or {},
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _serialize_intervention(iv: LLMIntervention) -> dict:
    return {
        "id": iv.id,
        "session_id": iv.session_id,
        "role": iv.role,
        "input_move_ids": iv.input_move_ids or [],
        "prompt": iv.prompt,
        "output": iv.output,
        "created_at": iv.created_at.isoformat() if iv.created_at else None,
    }


def _serialize_session(s: GameSession) -> dict:
    return {
        "id": s.id,
        "game_id": s.game_id,
        "material_id": s.material_id,
        "status": s.status,
        "current_round_id": s.current_round_id,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "trace_profile": s.trace_profile,
        "moves": [_serialize_move(m) for m in s.moves],
        "interventions": [_serialize_intervention(iv) for iv in s.interventions],
    }


@router.post("")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    genome = get_genome(payload.game_id)
    if not genome:
        raise HTTPException(404, "unknown game")
    material_id = payload.material_id
    if not material_id:
        m = db.query(Material).filter(Material.game_id == payload.game_id).first()
        if not m:
            raise HTTPException(400, "no material for this game")
        material_id = m.id
    else:
        m = db.query(Material).filter(Material.id == material_id).first()
        if not m:
            raise HTTPException(404, "unknown material")
    s = GameSession(
        game_id=payload.game_id,
        material_id=material_id,
        status="in_progress",
        current_round_id=genome.rounds[0].id if genome.rounds else None,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _serialize_session(s)


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "no session")
    return _serialize_session(s)


@router.post("/{session_id}/moves")
def create_move(session_id: str, payload: MoveCreate, db: Session = Depends(get_db)):
    s = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "no session")
    if s.status == "completed":
        raise HTTPException(400, "session completed")
    genome = get_genome(s.game_id)
    if genome and payload.action not in genome.player_actions:
        raise HTTPException(400, f"action {payload.action} not in genome.player_actions")
    move = PlayerMove(
        session_id=s.id,
        round_id=payload.round_id,
        action=payload.action,
        target_unit_id=payload.target_unit_id,
        payload=payload.payload,
    )
    s.current_round_id = payload.round_id
    db.add(move)
    db.commit()
    db.refresh(move)
    return _serialize_move(move)


@router.post("/{session_id}/llm-intervention")
def intervene(session_id: str, payload: InterventionRequest, db: Session = Depends(get_db)):
    s = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "no session")
    provider = get_provider()
    out = provider.call_role(payload.role, payload.context, model=payload.model)
    spec = out.pop("_prompt_spec", None)
    if spec:
        prompt_text = f"[system]\n{spec.get('system','')}\n[user]\n{spec.get('user','')}"
    else:
        prompt_text = f"role={payload.role}"
    iv = LLMIntervention(
        session_id=s.id,
        role=payload.role,
        input_move_ids=payload.move_ids,
        prompt=prompt_text,
        output=out,
    )
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return _serialize_intervention(iv)


@router.post("/{session_id}/complete")
def complete_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "no session")
    moves = [_serialize_move(m) for m in s.moves]
    ivs = [_serialize_intervention(iv) for iv in s.interventions]
    profile = build_profile(s.game_id, moves, ivs)
    s.trace_profile = profile
    s.status = "completed"
    s.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(s)
    return _serialize_session(s)


@router.get("/{session_id}/export")
def export_session(session_id: str, format: str = "md", db: Session = Depends(get_db)):
    s = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "no session")
    session_dict = _serialize_session(s)
    moves = session_dict["moves"]
    ivs = session_dict["interventions"]
    if format == "md":
        return Response(content=export_session_markdown(session_dict, moves, ivs), media_type="text/markdown")
    if format == "json":
        return export_session_json(session_dict, moves, ivs)
    raise HTTPException(400, "format must be md or json")


@router.get("")
def list_sessions(db: Session = Depends(get_db)):
    return [
        {"id": s.id, "game_id": s.game_id, "status": s.status, "started_at": s.started_at.isoformat()}
        for s in db.query(GameSession).order_by(GameSession.started_at.desc()).limit(50).all()
    ]
