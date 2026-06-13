"""Phase 9: convert a CorpusEntry into a playable Material for a chosen game."""
from ..models import CorpusEntry
from ..llm.provider import get_provider
from .genome_loader import get_genome
from .replay_mutator import _REQUIRED_KEYS_BY_FIELD, MutatorError


def convert_entry_to_material_payload(entry: CorpusEntry, game_id: str, model: str | None = None) -> tuple[str, dict]:
    genome = get_genome(game_id)
    if not genome:
        raise MutatorError(f"unknown game_id {game_id}")
    field_type = genome.field_type
    provider = get_provider()
    out = provider.call_role(
        "material_converter",
        {
            "game_id": game_id,
            "field_type": field_type,
            "source_title": entry.title,
            "source_body": entry.body_md,
        },
        model=model,
    )
    new_title = out.get("new_title") or f"[from corpus] {entry.title}"
    new_payload = out.get("new_payload") or {}
    if not isinstance(new_payload, dict):
        raise MutatorError("converter returned non-dict payload")
    expected = _REQUIRED_KEYS_BY_FIELD.get(field_type)
    if expected and not expected.issubset(set(new_payload.keys())):
        missing = expected - set(new_payload.keys())
        raise MutatorError(f"converter payload missing keys for {field_type}: {missing}")
    new_payload["type"] = field_type
    return new_title, new_payload
