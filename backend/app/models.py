from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Material(Base):
    __tablename__ = "materials"
    id = Column(String, primary_key=True, default=_uuid)
    game_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    namespace = Column(String, default="demo", index=True)  # "demo" | "real" | "mutated" | "from_corpus"
    payload = Column(JSON, nullable=False)  # raw seed (text blocks, cards, phrase variants)
    parent_id = Column(String, ForeignKey("materials.id"), nullable=True, index=True)
    mutation_directive = Column(String, nullable=True)
    source_session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    source_corpus_id = Column(String, nullable=True, index=True)  # set in Phase 9
    created_at = Column(DateTime, default=_now)


class GameSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=_uuid)
    game_id = Column(String, index=True, nullable=False)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    status = Column(String, default="created")  # created | in_progress | completed
    player_token = Column(String, nullable=True, index=True)  # cookie-bound, set in Phase 6
    current_round_id = Column(String, nullable=True)
    trace_profile = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=_now)
    completed_at = Column(DateTime, nullable=True)

    moves = relationship("PlayerMove", back_populates="session", cascade="all, delete-orphan")
    interventions = relationship("LLMIntervention", back_populates="session", cascade="all, delete-orphan")


class PlayerMove(Base):
    __tablename__ = "moves"
    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), index=True, nullable=False)
    round_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_unit_id = Column(String, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=_now)

    session = relationship("GameSession", back_populates="moves")


class LLMIntervention(Base):
    __tablename__ = "interventions"
    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    input_move_ids = Column(JSON, default=list)
    prompt = Column(String, nullable=False)
    output = Column(JSON, nullable=False)  # structured: {text, attacks: [...], risk: "..."} etc
    created_at = Column(DateTime, default=_now)

    session = relationship("GameSession", back_populates="interventions")
