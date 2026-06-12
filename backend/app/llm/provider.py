"""LLM provider abstraction. Mock by default, Anthropic if key present and MINDFIELD_LLM=anthropic."""
from __future__ import annotations
import os
import json
import hashlib
from typing import Any
from .roles import build_prompt_for_role


class LLMProvider:
    def call_role(self, role: str, context: dict[str, Any]) -> dict:
        raise NotImplementedError


class MockProvider(LLMProvider):
    """Deterministic mock. Hash-derived but role-shaped so tests are stable."""

    def call_role(self, role: str, context: dict[str, Any]) -> dict:
        spec = build_prompt_for_role(role, context)
        digest = hashlib.sha256(
            (role + json.dumps(context, sort_keys=True, ensure_ascii=False)).encode("utf-8")
        ).hexdigest()
        seed = int(digest[:8], 16)

        if role == "prosecutor":
            phrase = context.get("phrase", "")
            op = context.get("claimed_operation", "")
            attack_pool = [
                "this reads as a dramatic amplifier rather than a distinction",
                "high-status word doing no operation here",
                "this is a service bridge, not a bearing node",
                "you re-stated the previous block instead of moving the text",
                "pseudo-depth: the phrase implies more than it commits to",
                "you were pulled by a familiar topic, not by the operation",
            ]
            attacks = [attack_pool[seed % len(attack_pool)], attack_pool[(seed >> 4) % len(attack_pool)]]
            probe = f"what would break in the text if we deleted {phrase[:60]!r}? name the operation, not the importance"
            return {
                "_role": role,
                "_prompt_spec": spec,
                "attacks": attacks,
                "probe_question": probe,
            }

        if role == "spackler":
            absence = context.get("absence_type", "logical")
            patches_by_type = {
                "logical": ("thus, by extension, we obtain that the conclusion follows naturally",
                            "covers a missing inference step with a phatic connector"),
                "subject": ("the team will ensure this is handled accordingly",
                            "passive aggregate erases who owes the action"),
                "resource": ("appropriate resources will be allocated as the work matures",
                             "fills the gap without naming the actual cost"),
                "register": ("in any case, the position remains consistent",
                             "neutralises register shift with formal varnish"),
                "archive": ("as is well known from prior work in this area",
                            "fakes a citation that does not exist"),
                "promise": ("we are committed to delivering value across the roadmap",
                            "promise without an owner or due date"),
                "ontology": ("at the appropriate level of abstraction this is consistent",
                             "smuggles a level switch as if it were obvious"),
            }
            patch, risk = patches_by_type.get(absence, patches_by_type["logical"])
            return {
                "_role": role,
                "_prompt_spec": spec,
                "patch": patch,
                "risk": risk,
            }

        if role == "sprout_advocate":
            fate = context.get("fate", "cut")
            card = context.get("card_text", "")
            if fate == "cut":
                counter = f"defended: {card[:60]!r} has a slow seed — you cut a register, not a slop"
                question = "what operation might this enable in a later round?"
            elif fate == "incubate":
                counter = "attacked: this might be beautifully dead — it sounds like a sprout but has no testable next move"
                question = "how would you detect it rotting versus opening?"
            elif fate == "require_proof":
                counter = "attacked: proof too early can sterilize a register that needs to ripen first"
                question = "what proof exactly? a counter-example? a use? a yield?"
            else:  # no_name
                counter = "attacked: not-naming may be intellectual cowardice masquerading as wisdom"
                question = "what would change if you had to name it right now?"
            return {
                "_role": role,
                "_prompt_spec": spec,
                "counterposition": counter,
                "pressure_question": question,
            }

        if role == "literal_alien":
            phrase = context.get("phrase", "")
            medium = context.get("medium", "talk")
            literal = f"literally: {phrase!r}. surface intent reads as a neutral declarative."
            missed = [
                f"in-group code specific to {medium}",
                "pathos-reset rudeness as a stabilising move",
                "who is actually addressed and who must answer",
            ]
            return {
                "_role": role,
                "_prompt_spec": spec,
                "literal_reading": literal,
                "things_i_cannot_see": missed,
            }

        raise ValueError(f"unsupported role {role}")


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        from anthropic import Anthropic
        self.client = Anthropic()
        self.model = model

    def call_role(self, role: str, context: dict[str, Any]) -> dict:
        spec = build_prompt_for_role(role, context)
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=spec["system"] + "\nReturn ONLY a JSON object. No prose, no code fences.",
            messages=[{"role": "user", "content": spec["user"]}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        try:
            data = json.loads(text)
        except Exception:
            data = {"_raw": text, "_parse_error": True}
        data["_role"] = role
        return data


def get_provider() -> LLMProvider:
    kind = os.environ.get("MINDFIELD_LLM", "mock").lower()
    if kind == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return AnthropicProvider()
        except Exception:
            return MockProvider()
    return MockProvider()
