from pydantic import BaseModel, Field
from typing import Any, Optional


class GameRound(BaseModel):
    id: str
    title: str
    instruction: str
    time_sec: int


class LLMRoleSpec(BaseModel):
    id: str
    triggered_on_action: str


class GameGenome(BaseModel):
    id: str
    title: str
    short_title: str
    function: str
    roots: list[str]
    field_type: str
    rounds: list[GameRound]
    llm_roles: list[LLMRoleSpec]
    player_actions: list[str]
    verdicts: list[str] = []
    fates: list[str] = []
    absence_types: list[str] = []
    mediums: list[str] = []
    phrase_actions: list[str] = []
    trace_schema: list[str]
    replay_mutation: dict
    toxins: list[str] = []
    profile_dimensions: list[str] = []


class GameListItem(BaseModel):
    id: str
    title: str
    short_title: str
    function: str


class SessionCreate(BaseModel):
    game_id: str
    material_id: Optional[str] = None


class MoveCreate(BaseModel):
    round_id: str
    action: str
    target_unit_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class MoveOut(BaseModel):
    id: str
    round_id: str
    action: str
    target_unit_id: Optional[str]
    payload: dict
    created_at: str


class InterventionRequest(BaseModel):
    role: str
    move_ids: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class InterventionOut(BaseModel):
    id: str
    role: str
    output: dict
    created_at: str


class SessionOut(BaseModel):
    id: str
    game_id: str
    material_id: str
    status: str
    current_round_id: Optional[str]
    started_at: str
    completed_at: Optional[str]
    trace_profile: Optional[dict]
    moves: list[MoveOut] = []
    interventions: list[InterventionOut] = []


class MaterialOut(BaseModel):
    id: str
    game_id: str
    title: str
    payload: dict
