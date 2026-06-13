"""Replay loop: previous session profile → mutator role → new Material → new Session."""
from typing import Any
from ..models import GameSession, Material
from ..llm.provider import get_provider
from .genome_loader import get_genome


_REQUIRED_KEYS_BY_FIELD = {
    "clickable_text_units": {"type", "intro", "units"},
    "gap_click_text":       {"type", "intro", "blocks", "gaps"},
    "card_sorting":         {"type", "intro", "zones", "cards"},
    "medium_shift_phrase":  {"type", "intro", "phrase", "variants"},
    "promise_court_text":   {"type", "intro", "blocks"},
}


class MutatorError(RuntimeError):
    pass


def mutate_material(session: GameSession, material: Material, model: str | None = None) -> tuple[str, str, dict]:
    """Returns (new_title, mutation_directive, new_payload).

    Raises MutatorError if the LLM output cannot be coerced into the expected
    field_type schema. Caller persists the resulting Material.
    """
    genome = get_genome(session.game_id)
    if not genome:
        raise MutatorError(f"unknown game_id {session.game_id}")
    field_type = genome.field_type
    profile = session.trace_profile or {}
    directives = profile.get("replay_directives") or []
    if not directives:
        raise MutatorError("previous session has no replay directive — cannot mutate")
    directive = directives[0]
    verdicts = profile.get("dimensions", {}).get("verdict_distribution")

    provider = get_provider()
    out = provider.call_role(
        "material_mutator",
        {
            "game_id": session.game_id,
            "field_type": field_type,
            "previous_payload": material.payload,
            "directive": directive,
            "verdict_distribution": verdicts,
        },
        model=model,
    )
    new_title = out.get("new_title") or f"[mutated] {material.title}"
    new_payload = out.get("new_payload") or {}
    if not isinstance(new_payload, dict):
        raise MutatorError(f"mutator returned non-dict payload: {type(new_payload).__name__}")
    expected = _REQUIRED_KEYS_BY_FIELD.get(field_type)
    if expected and not expected.issubset(set(new_payload.keys())):
        missing = expected - set(new_payload.keys())
        raise MutatorError(f"mutator payload missing keys for {field_type}: {missing}")
    # Force the type tag — model sometimes drops it.
    new_payload["type"] = field_type
    return new_title, directive, new_payload
