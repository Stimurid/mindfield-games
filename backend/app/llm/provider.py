"""LLM provider for Mindfield.

Real LLM is mandatory for live runs — without a model, the games are not games.
Default provider is OpenAI-compatible against 302.ai (the gateway that works
inside RF). Mock exists ONLY for unit tests and is opt-in via MINDFIELD_LLM=mock.

Env contract (read at request time, not at import):

  MINDFIELD_LLM        = "openai_compatible" (default) | "mock"
  MINDFIELD_LLM_API_BASE = base URL incl. /v1   (default: https://api.302.ai/v1)
  MINDFIELD_LLM_API_KEY  = key for that gateway
  MINDFIELD_LLM_MODEL    = chat model id        (default: gpt-4.1-mini)

If MINDFIELD_LLM_API_KEY is absent we also accept LLM_API_KEY, then
QUINTA_MAI_API_KEY as a last-resort shared gateway key (this is the
shared 302.ai key already present in the workstation env).
"""
from __future__ import annotations
import os
import json
import hashlib
import urllib.request
import urllib.error
from typing import Any
from .roles import build_prompt_for_role


MODEL_PRESETS = [
    {"id": "gpt-4.1-mini",  "label": "GPT-4.1 mini",  "gateway": "302.ai"},
    {"id": "grok-4-0709",   "label": "Grok-4",        "gateway": "302.ai"},
]


class LLMProvider:
    default_model: str | None = None

    def call_role(self, role: str, context: dict[str, Any], *, model: str | None = None) -> dict:
        raise NotImplementedError


# Per-role JSON contract — the provider enforces shape and key whitelist.
_ROLE_SHAPE: dict[str, dict[str, type]] = {
    "prosecutor":      {"attacks": list, "probe_question": str},
    "spackler":        {"patch": str, "risk": str},
    "sprout_advocate": {"counterposition": str, "pressure_question": str},
    "literal_alien":   {"literal_reading": str, "things_i_cannot_see": list},
    "material_mutator":{"new_title": str, "new_payload": dict},
    "material_converter":{"new_title": str, "new_payload": dict},
}

_NON_ASSISTANT_FOOTER = (
    "\nHard rules:\n"
    "- You are an organ inside the game, not an assistant.\n"
    "- Do NOT explain the right answer. Do NOT coach. Do NOT apologise.\n"
    "- Do NOT include keys named 'answer', 'solution', 'explanation_for_player',\n"
    "  'helpful_tip', 'guidance', or 'feedback'.\n"
    "- Output ONLY the JSON object specified, with the exact keys, nothing else.\n"
    "- No markdown, no code fences, no leading or trailing prose.\n"
)


def _coerce(role: str, data: dict) -> dict:
    """Trim to allowed keys and validate shape; raise on contract break."""
    shape = _ROLE_SHAPE[role]
    out: dict[str, Any] = {}
    for k, t in shape.items():
        v = data.get(k)
        if not isinstance(v, t):
            if t is list and isinstance(v, str):
                v = [v]
            elif t is str and isinstance(v, list):
                v = " · ".join(str(x) for x in v)
            else:
                raise ValueError(f"role {role} returned bad shape: {k!r} is {type(v).__name__}, expected {t.__name__}")
        out[k] = v
    return out


class MockProvider(LLMProvider):
    """Deterministic mock — TESTS ONLY. Never used at runtime by default."""
    default_model = "mock"

    def call_role(self, role: str, context: dict[str, Any], *, model: str | None = None) -> dict:
        spec = build_prompt_for_role(role, context)
        digest = hashlib.sha256(
            (role + json.dumps(context, sort_keys=True, ensure_ascii=False)).encode("utf-8")
        ).hexdigest()
        seed = int(digest[:8], 16)

        if role == "prosecutor":
            phrase = context.get("phrase", "")
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
            return {"_role": role, "_prompt_spec": spec, "attacks": attacks, "probe_question": probe}

        if role == "spackler":
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
            patch, risk = patches_by_type.get(context.get("absence_type", "logical"), patches_by_type["logical"])
            return {"_role": role, "_prompt_spec": spec, "patch": patch, "risk": risk}

        if role == "sprout_advocate":
            fate = context.get("fate", "cut")
            card = context.get("card_text", "")
            if fate == "cut":
                counter = f"defended: {card[:60]!r} has a slow seed — you cut a register, not a slop"
                question = "what operation might this enable in a later round?"
            elif fate == "incubate":
                counter = "attacked: this might be beautifully dead — sounds like a sprout but has no testable next move"
                question = "how would you detect it rotting versus opening?"
            elif fate == "require_proof":
                counter = "attacked: proof too early can sterilize a register that needs to ripen first"
                question = "what proof exactly? a counter-example? a use? a yield?"
            else:
                counter = "attacked: not-naming may be intellectual cowardice masquerading as wisdom"
                question = "what would change if you had to name it right now?"
            return {"_role": role, "_prompt_spec": spec, "counterposition": counter, "pressure_question": question}

        if role == "literal_alien":
            phrase = context.get("phrase", "")
            medium = context.get("medium", "talk")
            return {
                "_role": role,
                "_prompt_spec": spec,
                "literal_reading": f"literally: {phrase!r}. surface intent reads as a neutral declarative.",
                "things_i_cannot_see": [
                    f"in-group code specific to {medium}",
                    "pathos-reset rudeness as a stabilising move",
                    "who is actually addressed and who must answer",
                ],
            }

        if role == "material_converter":
            field_type = context.get("field_type", "")
            title = (context.get("source_title") or "corpus entry")[:60]
            tag = f"from[{title}]"
            if field_type == "clickable_text_units":
                np = {"type": "clickable_text_units", "intro": tag,
                      "units": [{"id": f"c{i}", "index": i, "text": f"{tag} unit {i}", "dev_role": "pseudo_depth"} for i in range(12)]}
            elif field_type == "gap_click_text":
                np = {"type": "gap_click_text", "intro": tag,
                      "blocks": [{"id": f"cb{i}", "index": i, "text": f"{tag} block {i}"} for i in range(5)],
                      "gaps":   [{"id": f"cg{i}", "index": i, "between": [f"cb{i}", f"cb{i+1}"], "dev_absence": "subject", "dev_note": "mock"} for i in range(4)]}
            elif field_type == "card_sorting":
                np = {"type": "card_sorting", "intro": tag,
                      "zones": [{"id":"cut","label":"Cut","hint":""},{"id":"incubate","label":"Incubate","hint":""},
                                {"id":"require_proof","label":"Require proof","hint":""},{"id":"no_name","label":"No name","hint":""}],
                      "cards": [{"id": f"cc{i}", "text": f"{tag} card {i}", "dev_kind": "explicit_slop"} for i in range(20)]}
            elif field_type == "medium_shift_phrase":
                np = {"type": "medium_shift_phrase", "intro": tag, "phrase": "вы уверены?",
                      "variants": [{"id": f"cv{i}", "medium": ["telegram","email","protocol","talk","doc_comment"][i],
                                    "context": f"{tag} medium ctx {i}", "dev_action": "hidden_request", "dev_note": "mock"} for i in range(5)],
                      "alt_phrase": "хорошо."}
            else:
                np = {"type": field_type, "intro": tag}
            return {
                "_role": role,
                "_prompt_spec": spec,
                "new_title": f"[mock-from-corpus] {title}",
                "new_payload": np,
            }

        if role == "material_mutator":
            field_type = context.get("field_type", "")
            prev = context.get("previous_payload", {}) or {}
            directive = context.get("directive", "")
            tag = f"mutated[{directive[:40]}]"
            if field_type == "clickable_text_units":
                new_payload = {
                    "type": "clickable_text_units",
                    "intro": f"{tag} {prev.get('intro', '')}",
                    "units": [
                        {"id": f"m{i}", "index": i, "text": f"{tag} unit {i}", "dev_role": "pseudo_depth"}
                        for i in range(12)
                    ],
                }
            elif field_type == "gap_click_text":
                blocks = [{"id": f"mb{i}", "index": i, "text": f"{tag} block {i}"} for i in range(5)]
                gaps = [
                    {"id": f"mg{i}", "index": i, "between": [f"mb{i}", f"mb{i+1}"],
                     "dev_absence": "subject", "dev_note": "mock"}
                    for i in range(4)
                ]
                new_payload = {"type": "gap_click_text", "intro": tag, "blocks": blocks, "gaps": gaps}
            elif field_type == "card_sorting":
                new_payload = {
                    "type": "card_sorting",
                    "intro": tag,
                    "zones": prev.get("zones") or [
                        {"id": "cut", "label": "Cut", "hint": ""},
                        {"id": "incubate", "label": "Incubate", "hint": ""},
                        {"id": "require_proof", "label": "Require proof", "hint": ""},
                        {"id": "no_name", "label": "No name", "hint": ""},
                    ],
                    "cards": [{"id": f"mc{i}", "text": f"{tag} card {i}", "dev_kind": "explicit_slop"} for i in range(20)],
                }
            elif field_type == "medium_shift_phrase":
                new_payload = {
                    "type": "medium_shift_phrase",
                    "intro": tag,
                    "phrase": prev.get("phrase") or "тест?",
                    "variants": [
                        {"id": f"mv{i}", "medium": prev.get("variants", [{}])[i % max(len(prev.get("variants", [])), 1)].get("medium", "talk"),
                         "context": f"{tag} ctx {i}", "dev_action": "hidden_request", "dev_note": "mock"}
                        for i in range(5)
                    ],
                    "alt_phrase": prev.get("alt_phrase") or "",
                }
            else:
                new_payload = {"type": field_type, "intro": tag}
            return {
                "_role": role,
                "_prompt_spec": spec,
                "new_title": f"[mock-mutated] {directive[:60]}",
                "new_payload": new_payload,
            }

        raise ValueError(f"unsupported role {role}")


class OpenAICompatibleProvider(LLMProvider):
    """Talks to any OpenAI-compatible /chat/completions endpoint.

    Default target is 302.ai (https://api.302.ai/v1) which is the working
    gateway inside RF and the one used by sister projects (Quinta, Litops).
    """

    def __init__(self, *, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = model

    def call_role(self, role: str, context: dict[str, Any], *, model: str | None = None) -> dict:
        if role not in _ROLE_SHAPE:
            raise ValueError(f"unknown role {role}")
        chosen = model or self.default_model
        allowed = {p["id"] for p in MODEL_PRESETS}
        if chosen not in allowed:
            chosen = self.default_model
        spec = build_prompt_for_role(role, context)
        system = spec["system"] + _NON_ASSISTANT_FOOTER
        body = {
            "model": chosen,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": spec["user"]},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 3500 if role in ("material_mutator", "material_converter") else 600,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:400]
            raise RuntimeError(f"LLM gateway HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"LLM gateway unreachable: {e.reason}") from None

        payload = json.loads(raw)
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise RuntimeError(f"LLM gateway returned no content: {raw[:300]}")
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"LLM returned non-JSON: {text[:300]}")

        data = _coerce(role, data)
        data["_role"] = role
        data["_model"] = chosen
        return data


def get_provider() -> LLMProvider:
    kind = os.environ.get("MINDFIELD_LLM", "openai_compatible").lower()
    if kind == "mock":
        return MockProvider()
    if kind in ("openai_compatible", "openai", "302ai", "302"):
        base = os.environ.get("MINDFIELD_LLM_API_BASE", "https://api.302.ai/v1")
        key = (
            os.environ.get("MINDFIELD_LLM_API_KEY")
            or os.environ.get("LLM_API_KEY")
            or os.environ.get("QUINTA_MAI_API_KEY")
        )
        model = os.environ.get("MINDFIELD_LLM_MODEL", "gpt-4.1-mini")
        if not key:
            raise RuntimeError(
                "LLM key not found. Set MINDFIELD_LLM_API_KEY (or LLM_API_KEY, "
                "or use the shared QUINTA_MAI_API_KEY already in env). To run "
                "tests without a real model, set MINDFIELD_LLM=mock explicitly."
            )
        return OpenAICompatibleProvider(base_url=base, api_key=key, model=model)
    raise RuntimeError(f"MINDFIELD_LLM={kind!r} is not a known provider")
