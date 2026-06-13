"""Phase 18: remote playtest evaluation harness.

Captures enough evidence from a remote player to evaluate:
  · whether the player understood the action,
  · whether the LLM acted as game-organ or assistant,
  · whether the Operator Profile was specific or generic,
  · whether the replay targeted the detected weakness,
  · whether a 24h transfer signal appears outside the app.

Backend traces alone are insufficient — this router adds reflections + a 24h
follow-up token so a remote player produces a usable evidence record without
an observer.
"""
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any
from ..database import get_db
from ..models import PlaytestRun, ReflectionEvent, FollowUp24h


router = APIRouter(prefix="/api/playtests", tags=["playtests"])


VALID_STAGES = {
    "after_triage", "after_game_1", "after_profile", "after_replay",
    "after_game_2", "final",
}
VALID_VERDICTS = {
    "software_only", "profile_recognition", "replay_targeting",
    "transfer_candidate", "unclear",
}
VALID_YES_NO = {"yes", "no", "unclear"}
VALID_CONFIDENCE = {"low", "medium", "high"}


class StartRequest(BaseModel):
    mode: str = "self_test"
    selected_entry_id: Optional[str] = None
    session_ids: list[str] = []


@router.post("/start")
def start_run(
    payload: StartRequest,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    if payload.mode not in {"self_test", "remote_test", "moderated"}:
        raise HTTPException(400, "mode must be self_test | remote_test | moderated")
    run = PlaytestRun(
        mode=payload.mode,
        player_token=x_player_token,
        selected_entry_id=payload.selected_entry_id,
        session_ids=payload.session_ids or [],
    )
    db.add(run)
    db.flush()
    follow = FollowUp24h(
        run_id=run.id,
        token=secrets.token_urlsafe(24),
        due_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(follow)
    db.commit()
    db.refresh(run)
    db.refresh(follow)
    return _serialize_run(run, [], follow)


class ReflectionRequest(BaseModel):
    stage: str
    prompt: str
    answer: str


@router.post("/{run_id}/reflection")
def add_reflection(
    run_id: str,
    payload: ReflectionRequest,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    run = _get_run_or_404(db, run_id, x_player_token)
    if payload.stage not in VALID_STAGES:
        raise HTTPException(400, f"stage must be one of {sorted(VALID_STAGES)}")
    r = ReflectionEvent(
        run_id=run.id,
        stage=payload.stage,
        prompt=payload.prompt,
        answer=payload.answer or "",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize_reflection(r)


class CompleteRequest(BaseModel):
    final_verdict: str
    extra_session_ids: list[str] = []


@router.post("/{run_id}/complete")
def complete_run(
    run_id: str,
    payload: CompleteRequest,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    run = _get_run_or_404(db, run_id, x_player_token)
    if payload.final_verdict not in VALID_VERDICTS:
        raise HTTPException(400, f"final_verdict must be one of {sorted(VALID_VERDICTS)}")
    run.final_verdict = payload.final_verdict
    run.completed_at = datetime.now(timezone.utc)
    if payload.extra_session_ids:
        merged = list(run.session_ids or [])
        for sid in payload.extra_session_ids:
            if sid not in merged:
                merged.append(sid)
        run.session_ids = merged
    db.commit()
    db.refresh(run)
    reflections = _load_reflections(db, run.id)
    follow = db.query(FollowUp24h).filter(FollowUp24h.run_id == run.id).first()
    return _serialize_run(run, reflections, follow)


@router.get("/{run_id}")
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    run = _get_run_or_404(db, run_id, x_player_token)
    reflections = _load_reflections(db, run.id)
    follow = db.query(FollowUp24h).filter(FollowUp24h.run_id == run.id).first()
    return _serialize_run(run, reflections, follow)


@router.get("/{run_id}/export")
def export_run(
    run_id: str,
    db: Session = Depends(get_db),
    x_player_token: Optional[str] = Header(default=None, alias="X-Player-Token"),
):
    run = _get_run_or_404(db, run_id, x_player_token)
    reflections = _load_reflections(db, run.id)
    follow = db.query(FollowUp24h).filter(FollowUp24h.run_id == run.id).first()
    md = _markdown_export(run, reflections, follow)
    return {"format": "md", "body": md}


# ── 24h follow-up (no auth, token-only) ──────────────────────────────────────

@router.get("/followup/{token}")
def get_followup(token: str, db: Session = Depends(get_db)):
    f = db.query(FollowUp24h).filter(FollowUp24h.token == token).first()
    if not f:
        raise HTTPException(404, "no such followup")
    run = db.query(PlaytestRun).filter(PlaytestRun.id == f.run_id).first()
    return {
        "token": f.token,
        "due_at": f.due_at.isoformat() + "Z" if f.due_at else None,
        "completed_at": f.completed_at.isoformat() + "Z" if f.completed_at else None,
        "transfer_seen": f.transfer_seen,
        "outside_app_example": f.outside_app_example,
        "remembered_operation": f.remembered_operation,
        "confidence": f.confidence,
        "appeared_spontaneously": f.appeared_spontaneously,
        "game_helped": f.game_helped,
        "run_id": f.run_id,
        "run_completed_at": run.completed_at.isoformat() + "Z" if (run and run.completed_at) else None,
        "checklist": [
            {"key": "transfer_seen", "prompt": "Did you notice the operation outside Mindfield?", "type": "yes_no"},
            {"key": "outside_app_example", "prompt": "Give one concrete example.", "type": "text"},
            {"key": "appeared_spontaneously", "prompt": "Did it appear spontaneously, or only after reading this question?", "type": "yes_no"},
            {"key": "remembered_operation", "prompt": "Name the operation in your own words.", "type": "text"},
            {"key": "confidence", "prompt": "How confident are you in this answer?", "type": "low_medium_high"},
            {"key": "game_helped", "prompt": "Did the game make the operation more available?", "type": "yes_no"},
        ],
    }


class FollowUpSubmit(BaseModel):
    transfer_seen: Optional[str] = None
    outside_app_example: Optional[str] = None
    appeared_spontaneously: Optional[str] = None
    remembered_operation: Optional[str] = None
    confidence: Optional[str] = None
    game_helped: Optional[str] = None


@router.post("/followup/{token}")
def submit_followup(token: str, payload: FollowUpSubmit, db: Session = Depends(get_db)):
    f = db.query(FollowUp24h).filter(FollowUp24h.token == token).first()
    if not f:
        raise HTTPException(404, "no such followup")
    if payload.transfer_seen is not None:
        if payload.transfer_seen not in VALID_YES_NO:
            raise HTTPException(400, "transfer_seen must be yes | no | unclear")
        f.transfer_seen = payload.transfer_seen
    if payload.appeared_spontaneously is not None:
        if payload.appeared_spontaneously not in VALID_YES_NO:
            raise HTTPException(400, "appeared_spontaneously must be yes | no | unclear")
        f.appeared_spontaneously = payload.appeared_spontaneously
    if payload.game_helped is not None:
        if payload.game_helped not in VALID_YES_NO:
            raise HTTPException(400, "game_helped must be yes | no | unclear")
        f.game_helped = payload.game_helped
    if payload.confidence is not None:
        if payload.confidence not in VALID_CONFIDENCE:
            raise HTTPException(400, "confidence must be low | medium | high")
        f.confidence = payload.confidence
    if payload.outside_app_example is not None:
        f.outside_app_example = payload.outside_app_example
    if payload.remembered_operation is not None:
        f.remembered_operation = payload.remembered_operation
    f.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(f)
    return {"submitted_at": f.completed_at.isoformat() + "Z"}


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_run_or_404(db: Session, run_id: str, player_token: Optional[str]) -> PlaytestRun:
    run = db.query(PlaytestRun).filter(PlaytestRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "no such playtest run")
    # If the run was created with a player_token, only that token can access it.
    # Random run_id guessing is already mitigated by UUID4 size; this is a
    # defense-in-depth against the case where a run_id leaks via screenshot or
    # log and someone else tries to mutate the reflections.
    if run.player_token and run.player_token != player_token:
        raise HTTPException(403, "this run belongs to another player")
    return run


def _load_reflections(db: Session, run_id: str) -> list[ReflectionEvent]:
    return (
        db.query(ReflectionEvent)
        .filter(ReflectionEvent.run_id == run_id)
        .order_by(ReflectionEvent.created_at.asc())
        .all()
    )


def _serialize_run(run: PlaytestRun, reflections, follow: Optional[FollowUp24h]) -> dict[str, Any]:
    return {
        "id": run.id,
        "mode": run.mode,
        "player_token": run.player_token,
        "started_at": run.started_at.isoformat() + "Z" if run.started_at else None,
        "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None,
        "selected_entry_id": run.selected_entry_id,
        "session_ids": run.session_ids or [],
        "final_verdict": run.final_verdict,
        "reflections": [_serialize_reflection(r) for r in reflections],
        "followup": {
            "token": follow.token,
            "due_at": follow.due_at.isoformat() + "Z" if (follow and follow.due_at) else None,
            "completed_at": follow.completed_at.isoformat() + "Z" if (follow and follow.completed_at) else None,
        } if follow else None,
    }


def _serialize_reflection(r: ReflectionEvent) -> dict[str, Any]:
    return {
        "id": r.id,
        "stage": r.stage,
        "prompt": r.prompt,
        "answer": r.answer,
        "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
    }


def _markdown_export(run: PlaytestRun, reflections, follow: Optional[FollowUp24h]) -> str:
    lines = []
    lines.append(f"# Playtest Run · {run.id[:8]}")
    lines.append("")
    lines.append(f"- mode: **{run.mode}**")
    lines.append(f"- started: {run.started_at.isoformat() if run.started_at else '—'}Z")
    lines.append(f"- completed: {run.completed_at.isoformat() if run.completed_at else '— (still in progress)'}")
    lines.append(f"- final_verdict: **{run.final_verdict or '— (not yet set)'}**")
    if run.selected_entry_id:
        lines.append(f"- selected_corpus_entry: `{run.selected_entry_id}`")
    if run.session_ids:
        lines.append(f"- session_ids ({len(run.session_ids)}): " + ", ".join(f"`{s[:8]}`" for s in run.session_ids))
    lines.append("")
    lines.append("## Reflections")
    if not reflections:
        lines.append("(нет записанных рефлексий)")
    by_stage: dict[str, list[ReflectionEvent]] = {}
    for r in reflections:
        by_stage.setdefault(r.stage, []).append(r)
    for stage in ("after_triage", "after_game_1", "after_profile", "after_replay", "after_game_2", "final"):
        if stage not in by_stage:
            continue
        lines.append(f"### {stage}")
        for r in by_stage[stage]:
            lines.append(f"- **{r.prompt}**")
            lines.append(f"  - {r.answer.strip() or '(empty)'}")
        lines.append("")
    lines.append("## 24h follow-up")
    if not follow:
        lines.append("(нет привязанного follow-up)")
    else:
        if not follow.completed_at:
            lines.append(f"- status: **pending** · due {follow.due_at.isoformat() if follow.due_at else '—'}Z")
            lines.append(f"- token (share this link to the player): `{follow.token}`")
        else:
            lines.append(f"- status: **submitted** at {follow.completed_at.isoformat()}Z")
            lines.append(f"- transfer_seen: **{follow.transfer_seen or '—'}**")
            lines.append(f"- example: {follow.outside_app_example or '—'}")
            lines.append(f"- appeared_spontaneously: **{follow.appeared_spontaneously or '—'}**")
            lines.append(f"- remembered_operation: {follow.remembered_operation or '—'}")
            lines.append(f"- confidence: **{follow.confidence or '—'}**")
            lines.append(f"- game_helped: **{follow.game_helped or '—'}**")
    return "\n".join(lines)
