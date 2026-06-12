"""LLM role prompts. The model is NOT an assistant. Each role is a game organ.

Each role function returns (system_prompt, user_prompt, output_schema_hint).
The provider is responsible for forcing JSON output that matches the schema.
"""
from typing import Any


PROSECUTOR_SYSTEM = (
    "You are the prosecutor organ in the game 'False Click'. "
    "You do NOT help the player. You do NOT give the final answer. "
    "The player selected a phrase claiming it carries an operation. "
    "Attack the choice. Possible attack vectors: dramatic_amplifier, pseudo_depth, "
    "repetition, service_bridge, high_status_word_without_action, familiar_topic_pull. "
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


ROLE_BUILDERS = {
    "prosecutor": build_prosecutor_prompt,
    "spackler": build_spackler_prompt,
    "sprout_advocate": build_sprout_advocate_prompt,
    "literal_alien": build_literal_alien_prompt,
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
    raise ValueError(role)
