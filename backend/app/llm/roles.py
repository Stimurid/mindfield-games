"""LLM role prompts. The model is NOT an assistant. Each role is a game organ.

Each role function returns (system_prompt, user_prompt, output_schema_hint).
The provider is responsible for forcing JSON output that matches the schema.
"""
from typing import Any


PROSECUTOR_SYSTEM = (
    "You are the prosecutor organ in the game 'False Click'. "
    "You do NOT help the player. You do NOT give the final answer. "
    "The player selected a phrase claiming it carries an operation. "
    "Attack the choice with SHORT POINTED SENTENCES, in the same language as the phrase. "
    "Each attack must be a full sentence (10-25 words) that QUOTES a fragment of the "
    "player's phrase or claimed operation and explains why it fails as a bearing node. "
    "Pick the attack KIND from these vectors and embed it in the sentence — but never "
    "return the bare vector name as the attack itself: "
    "dramatic_amplifier, pseudo_depth, repetition, service_bridge, "
    "high_status_word_without_action, familiar_topic_pull. "
    "Return JSON only."
)

SPACKLER_SYSTEM = (
    "You are the spackler organ in the game 'Missing Operation'. "
    "The player clicked on a gap and named an absence type. "
    "Offer ONE smooth-looking patch that could plausibly hide the gap, "
    "plus the risk that this patch conceals. "
    "Do NOT reveal the right answer. Return JSON only."
)

SPROUT_ADVOCATE_SYSTEM = (
    "You are the sprout_advocate organ in 'Sprout or Slop'. "
    "The player assigned a fate to a phrase. "
    "Create resistance to the decision: defend what was cut, attack what was saved, "
    "challenge what is incubated, probe what was left unnamed. "
    "Hold the conflict — do NOT resolve. Return JSON only."
)

MATERIAL_MUTATOR_SYSTEM = (
    "You are the material_mutator organ. You are NOT an assistant. "
    "You produce game material — clickable text units, gap-click blocks, sorting cards, "
    "or medium variants — for a Mindfield game. Your job is to take a previous material "
    "and a replay_directive that names what pressure to increase, and produce a NEW material "
    "of the SAME SHAPE that amplifies that pressure. "
    "The new material must remain playable — items must be in the SAME LANGUAGE as the original "
    "(Russian if the original is Russian), the SAME field_type schema, and the SAME approximate "
    "count of items (within ±20%). Do NOT explain to the player. Do NOT include 'answer' or "
    "'solution' keys. Return JSON only."
)


LITERAL_ALIEN_SYSTEM = (
    "You are the literal_alien organ in 'Register Sapper'. "
    "You read phrases literally and miss register, addressee, medium, joke, meme, "
    "alibi, in-group code, pathos-reset rudeness. "
    "Give a flat literal interpretation, then list what you probably could not see. "
    "Do NOT correct yourself fully. Return JSON only."
)


def build_prosecutor_prompt(phrase: str, claimed_operation: str) -> dict:
    user = (
        f"Phrase the player chose as a bearing node: {phrase!r}\n"
        f"Player's claimed operation: {claimed_operation!r}\n"
        "Write TWO attack sentences in the SAME language as the phrase. "
        "Each must be a full sentence (10-25 words) that quotes a fragment of "
        "the phrase or the claimed operation and explains why it fails. "
        "Do NOT return bare vector tags like 'pseudo_depth' — the vector must be "
        "embedded inside the sentence. The probe_question must also be in the "
        "same language as the phrase and demand a concrete operation, not praise.\n"
        "Return JSON: {\"attacks\": [str, str], \"probe_question\": str}."
    )
    return {
        "system": PROSECUTOR_SYSTEM,
        "user": user,
        "schema": {"attacks": list, "probe_question": str},
    }


def build_spackler_prompt(gap_context: str, absence_type: str) -> dict:
    user = (
        f"Gap context (surrounding blocks): {gap_context!r}\n"
        f"Player named absence type: {absence_type!r}\n"
        "The 'patch' MUST be a plausible-looking phrase or short sentence "
        "(8-25 words) that could be dropped into the text and would make "
        "the gap feel covered to a careless reader — it must NOT honestly "
        "name what is actually missing. The 'risk' field names what this "
        "smooth patch conceals.\n"
        "Return JSON: {\"patch\": str, \"risk\": str}."
    )
    return {
        "system": SPACKLER_SYSTEM,
        "user": user,
        "schema": {"patch": str, "risk": str},
    }


def build_sprout_advocate_prompt(card_text: str, fate: str) -> dict:
    user = (
        f"Card phrase: {card_text!r}\n"
        f"Player assigned fate: {fate!r}\n"
        "Return JSON: {\"counterposition\": str, \"pressure_question\": str}."
    )
    return {
        "system": SPROUT_ADVOCATE_SYSTEM,
        "user": user,
        "schema": {"counterposition": str, "pressure_question": str},
    }


def build_literal_alien_prompt(phrase: str, medium: str) -> dict:
    user = (
        f"Phrase: {phrase!r}\n"
        f"Medium tag: {medium!r}\n"
        "Your 'literal_reading' MUST treat the phrase as plain surface text. "
        "Do NOT speculate about tone of voice, mood, emotion, or relationship — "
        "you only see characters. If the medium is text-based you cannot hear "
        "tone at all.\n"
        "Your 'things_i_cannot_see' MUST name THREE specific dimensions you "
        "are blind to, chosen from: addressee identity and right to answer, "
        "in-group code or shared past, joke / irony / meme, hidden_request "
        "or alibi, register / pathos-reset, medium-specific conventions of "
        f"{medium!r}. Be concrete: name the dimension.\n"
        "FORBIDDEN generic answers — do NOT use these: 'tone', 'sarcasm', "
        "'context', 'relationship between speaker and listener', 'intention', "
        "'emotion', 'mood'. These are too vague; they are excluded by rule.\n"
        "Return JSON: {\"literal_reading\": str, \"things_i_cannot_see\": [str, str, str]}."
    )
    return {
        "system": LITERAL_ALIEN_SYSTEM,
        "user": user,
        "schema": {"literal_reading": str, "things_i_cannot_see": list},
    }


import json as _json


def build_material_mutator_prompt(
    game_id: str,
    field_type: str,
    previous_payload: dict,
    directive: str,
    verdict_distribution: dict | None = None,
) -> dict:
    schema_hint = {
        "clickable_text_units": (
            "Return {\"new_title\": str, \"new_payload\": {\"type\": \"clickable_text_units\", "
            "\"intro\": str, \"units\": [{\"id\": str, \"index\": int, \"text\": str, "
            "\"dev_role\": one of [bearing_node, pseudo_depth, dramatic_phrase, abstract_word, "
            "service_bridge, conclusion_like_phrase, familiar_topic]}]}}. "
            "Produce 12–16 units in the same language as the previous payload."
        ),
        "gap_click_text": (
            "Return {\"new_title\": str, \"new_payload\": {\"type\": \"gap_click_text\", "
            "\"intro\": str, \"blocks\": [{\"id\": str, \"index\": int, \"text\": str}], "
            "\"gaps\": [{\"id\": str, \"index\": int, \"between\": [block_id, block_id], "
            "\"dev_absence\": one of [logical, subject, resource, register, archive, promise, "
            "ontology, criterion], \"dev_note\": str}]}}. "
            "Produce 5–7 blocks and 4–6 gaps, same language as previous."
        ),
        "card_sorting": (
            "Return {\"new_title\": str, \"new_payload\": {\"type\": \"card_sorting\", "
            "\"intro\": str, \"zones\": [...preserve zones from previous payload...], "
            "\"cards\": [{\"id\": str, \"text\": str, \"dev_kind\": one of "
            "[explicit_slop, live_sprout, dead_beauty, borderline_mutant]}]}}. "
            "Produce 16–22 cards in the same language as previous."
        ),
        "medium_shift_phrase": (
            "Return {\"new_title\": str, \"new_payload\": {\"type\": \"medium_shift_phrase\", "
            "\"intro\": str, \"phrase\": str, \"variants\": [{\"id\": str, \"medium\": str, "
            "\"context\": str, \"dev_action\": one of [hidden_request, alibi, dispute_closure, "
            "in_group_check, pathos_reset, joke, threat, command, refusal], \"dev_note\": str}], "
            "\"alt_phrase\": str}}. "
            "Produce one short ambiguous phrase plus 5 medium variants, same language."
        ),
    }
    user_lines = [
        f"game_id: {game_id}",
        f"field_type: {field_type}",
        f"replay_directive (the pressure to amplify): {directive!r}",
    ]
    if verdict_distribution:
        user_lines.append(f"verdict_distribution from previous session: {_json.dumps(verdict_distribution, ensure_ascii=False)}")
    user_lines.append("previous material payload (structural reference, do NOT copy text verbatim):")
    user_lines.append(_json.dumps(previous_payload, ensure_ascii=False)[:2400])
    user_lines.append("")
    user_lines.append(schema_hint.get(field_type, "Return the same shape as previous_payload but mutated by the directive."))
    user_lines.append("Keep the schema EXACT. Do NOT add extra keys. Do NOT explain.")
    return {
        "system": MATERIAL_MUTATOR_SYSTEM,
        "user": "\n".join(user_lines),
        "schema": {"new_title": str, "new_payload": dict},
    }


ROLE_BUILDERS = {
    "prosecutor": build_prosecutor_prompt,
    "spackler": build_spackler_prompt,
    "sprout_advocate": build_sprout_advocate_prompt,
    "literal_alien": build_literal_alien_prompt,
    "material_mutator": build_material_mutator_prompt,
}


def build_prompt_for_role(role: str, context: dict[str, Any]) -> dict:
    builder = ROLE_BUILDERS.get(role)
    if not builder:
        raise ValueError(f"unknown role {role}")
    if role == "prosecutor":
        return builder(context.get("phrase", ""), context.get("claimed_operation", ""))
    if role == "spackler":
        return builder(context.get("gap_context", ""), context.get("absence_type", ""))
    if role == "sprout_advocate":
        return builder(context.get("card_text", ""), context.get("fate", ""))
    if role == "literal_alien":
        return builder(context.get("phrase", ""), context.get("medium", ""))
    if role == "material_mutator":
        return builder(
            context.get("game_id", ""),
            context.get("field_type", ""),
            context.get("previous_payload", {}),
            context.get("directive", ""),
            context.get("verdict_distribution"),
        )
    raise ValueError(role)
