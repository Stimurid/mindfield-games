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


class Organ(Base):
    """An entry in one of the 8 canonical organ banks (spec §8).

    The configurator selects organs from these banks to assemble a draft genome.
    Player-extracted organs (from the §4 triage of raw cards) also land here.
    """
    __tablename__ = "organs"
    id = Column(String, primary_key=True, default=_uuid)
    bank = Column(String, index=True, nullable=False)
    # field | object | action | llm_role | crisis | trace | mutation | degradation
    code = Column(String, unique=True, nullable=False)  # bank.slug
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    source = Column(String, default="canon_v0.1")
    source_entry_id = Column(String, ForeignKey("corpus_entries.id"), nullable=True)
    created_at = Column(DateTime, default=_now)


class Hypothesis(Base):
    """A researcher's hypothesis about an operation, a porода, or a player pattern.
    The researcher can summon any of the 4 organ roles against it and accumulate
    a discussion thread, then promote it into a game by linking it to a draft.
    """
    __tablename__ = "hypotheses"
    id = Column(String, primary_key=True, default=_uuid)
    title = Column(String, nullable=False)
    body_md = Column(String, default="")
    status = Column(String, default="draft")  # draft | published | abandoned
    tags = Column(JSON, default=list)
    player_token = Column(String, index=True, nullable=True)
    linked_draft_id = Column(String, ForeignKey("genome_drafts.id"), nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class HypothesisDiscussion(Base):
    __tablename__ = "hypothesis_discussions"
    id = Column(String, primary_key=True, default=_uuid)
    hypothesis_id = Column(String, ForeignKey("hypotheses.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    angle = Column(String, nullable=True)
    output = Column(JSON, nullable=False)
    model = Column(String, nullable=True)
    player_token = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=_now)


class TriageVerdict(Base):
    """One §4 fate assigned to a corpus entry by one player.

    Multiple verdicts per entry are allowed (different players, or the
    same player revising). The 'latest per (entry, player)' wins in the
    aggregate view.
    """
    __tablename__ = "triage_verdicts"
    id = Column(String, primary_key=True, default=_uuid)
    entry_id = Column(String, ForeignKey("corpus_entries.id"), index=True, nullable=False)
    player_token = Column(String, index=True, nullable=True)
    fate = Column(String, nullable=False)
    note = Column(String, nullable=True)
    extracted_organ_id = Column(String, ForeignKey("organs.id"), nullable=True)
    created_at = Column(DateTime, default=_now)


class GenomeDraft(Base):
    """A GameGenome assembled in the configurator. Lives outside game_genomes/
    JSON until it is promoted by the designer."""
    __tablename__ = "genome_drafts"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    function = Column(String, nullable=True)
    verb = Column(String, nullable=True)
    maturity_stage = Column(Integer, default=1)  # 0..5 (§3)
    selected_organs = Column(JSON, default=dict)  # {bank: [organ_id, ...]}
    weaver_verdict = Column(JSON, nullable=True)
    player_token = Column(String, nullable=True, index=True)
    # Promotion: turning a design draft into a runtime genome
    field_type = Column(String, nullable=True)  # set on promotion
    promoted = Column(String, default="no")     # "no" | "yes" — string for SQLite simplicity
    promoted_genome = Column(JSON, nullable=True)  # full game genome dict when promoted
    source_seed_material_id = Column(String, nullable=True)  # default material for the new game
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class CorpusEntry(Base):
    """A node in the Mindfield corpus library.

    Top-level pass ingests: attractors v0.1 + v0.2, R-roots, breeds,
    pre-cards, residuals, chimeras, genomes, app-specs, and our own
    phase docs as kind='phase_doc'. Small cards (4200+) come in a
    later pass.
    """
    __tablename__ = "corpus_entries"
    id = Column(String, primary_key=True, default=_uuid)
    kind = Column(String, index=True, nullable=False)
    # Stable user-visible code, e.g. "A01", "R3", "breed_05", "chimera_v2_12"
    code = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    body_md = Column(String, nullable=False)
    source_pass = Column(String, default="v0.2")
    source_line = Column(Integer, nullable=True)
    order_key = Column(Integer, default=0)
    maturity_stage = Column(Integer, nullable=True)  # 0..5 per §3 'Стадии зрелости'
    created_at = Column(DateTime, default=_now)


class LibraryComment(Base):
    """One organ pass over a corpus entry. NOT a chat — single shot. Persisted
    so the entry view shows the accumulated pressure from previous players."""
    __tablename__ = "library_comments"
    id = Column(String, primary_key=True, default=_uuid)
    entry_id = Column(String, ForeignKey("corpus_entries.id"), index=True, nullable=False)
    role = Column(String, nullable=False)  # prosecutor | spackler | sprout_advocate | literal_alien
    angle = Column(String, nullable=True)  # player-picked angle (verdict tag / absence_type / fate / medium)
    output = Column(JSON, nullable=False)
    player_token = Column(String, nullable=True, index=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)


class CorpusLink(Base):
    """Directed link between corpus entries. relation = derived_from |
    chimera_cross | refined | discussed_in.
    """
    __tablename__ = "corpus_links"
    id = Column(String, primary_key=True, default=_uuid)
    parent_id = Column(String, ForeignKey("corpus_entries.id"), index=True, nullable=False)
    child_id  = Column(String, ForeignKey("corpus_entries.id"), index=True, nullable=False)
    relation = Column(String, default="derived_from")


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
