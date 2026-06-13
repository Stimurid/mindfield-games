"""Translation cache + on-demand LLM translation.

Pure functions on a SQLAlchemy session. Identical source strings dedup by
SHA256 across the whole library — so a phrase that appears in 20 corpus
entries pays the LLM cost ONCE.

The cache is per (source_hash, target_lang) — a future second non-English
target language reuses the same source hash space.

Identifier-shaped fields are NEVER passed through this helper. See
TRANSLATE_PATHS_BY_KIND below for the explicit per-shape whitelist.
"""
from __future__ import annotations
import copy
import hashlib
import logging
import re
from typing import Any, Iterable
from sqlalchemy.orm import Session
from ..models import Translation


log = logging.getLogger(__name__)

# Strings that look like pure identifiers / codes — never sent to the LLM.
_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _looks_like_identifier(s: str) -> bool:
    return bool(_ID_RE.match(s.strip()))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def translate_text(text: str, target_lang: str, db: Session, provider=None) -> str:
    """Return the cached translation, or call the LLM and cache the result.

    `target_lang == 'ru'` is a no-op (source language).
    Empty / identifier-shaped strings pass through untouched.
    LLM error → return original text + log; never raise.
    """
    if target_lang == "ru" or not text:
        return text
    text_str = str(text)
    if not text_str.strip() or _looks_like_identifier(text_str):
        return text_str

    h = _hash(text_str)
    existing = (
        db.query(Translation)
        .filter(Translation.source_hash == h)
        .filter(Translation.target_lang == target_lang)
        .first()
    )
    if existing:
        return existing.target_text

    if provider is None:
        from ..llm.provider import get_provider
        provider = get_provider()
    try:
        out = provider.call_role("translator", {"text": text_str, "target_lang": target_lang})
        translated = (out.get("translated") or "").strip() or text_str
    except Exception as e:
        log.warning("translation failure (%s); returning source", e)
        return text_str

    row = Translation(
        source_hash=h,
        source_lang="ru",
        target_lang=target_lang,
        source_text=text_str,
        target_text=translated,
    )
    db.add(row)
    db.commit()
    return translated


def translate_dict(d: dict | list, paths: Iterable[str], target_lang: str, db: Session) -> dict | list:
    """Translate strings at the given dot-paths inside a dict (deep-copied).

    Path grammar:
      'title'                       — top-level key.
      'payload.intro'                — nested.
      'payload.units[].text'         — every item in a list.
      'rounds[].title'               — list of dicts.
    """
    if target_lang == "ru" or not d:
        return d
    out = copy.deepcopy(d)
    for p in paths:
        _apply(out, p.split("."), target_lang, db)
    return out


def _apply(obj: Any, parts: list[str], target_lang: str, db: Session):
    if not parts:
        return
    key = parts[0]
    rest = parts[1:]
    if isinstance(obj, list):
        for item in obj:
            _apply(item, parts, target_lang, db)
        return
    if not isinstance(obj, dict):
        return
    if key.endswith("[]"):
        list_key = key[:-2]
        lst = obj.get(list_key)
        if not isinstance(lst, list):
            return
        for item in lst:
            _apply(item, rest, target_lang, db)
        return
    if not rest:
        v = obj.get(key)
        if isinstance(v, str):
            obj[key] = translate_text(v, target_lang, db)
        elif isinstance(v, list):
            obj[key] = [translate_text(x, target_lang, db) if isinstance(x, str) else x for x in v]
        return
    child = obj.get(key)
    if isinstance(child, (dict, list)):
        _apply(child, rest, target_lang, db)


# ── Per-shape translation whitelists ────────────────────────────────────────
# Only fields that are human-readable language go here. Identifier-shaped
# fields stay as codes (verdicts, fates, absence_types, mediums, etc.).

GAME_PATHS = [
    "title", "short_title", "function",
    "rounds[].title", "rounds[].instruction",
    "toxins[]",
]

LIBRARY_ENTRY_LIST_PATHS = ["title"]
LIBRARY_ENTRY_DETAIL_PATHS = ["title", "body_md"]
LIBRARY_SECTION_PATHS = ["label"]

CONFIG_BANK_PATHS = ["label", "hint"]
CONFIG_ORGAN_PATHS = ["name", "description"]

TRIAGE_FATE_PATHS = ["label"]

# Material payload paths vary per field_type. Keys named for the 'type' field.
MATERIAL_PAYLOAD_PATHS_BY_FIELD_TYPE: dict[str, list[str]] = {
    "clickable_text_units": [
        "intro",
        "units[].text",
    ],
    "gap_click_text": [
        "intro",
        "blocks[].text",
    ],
    "card_sorting": [
        "intro",
        "zones[].label",
        "zones[].hint",
        "cards[].text",
    ],
    "medium_shift_phrase": [
        "intro",
        "phrase",
        "alt_phrase",
        "variants[].context",
    ],
    "promise_court_text": [
        "intro",
        "blocks[].text",
    ],
}


def translate_material_payload(payload: dict, target_lang: str, db: Session) -> dict:
    if target_lang == "ru" or not isinstance(payload, dict):
        return payload
    ftype = payload.get("type")
    paths = MATERIAL_PAYLOAD_PATHS_BY_FIELD_TYPE.get(ftype, ["intro"])
    return translate_dict(payload, paths, target_lang, db)


def t_field(s: Any, target_lang: str, db: Session) -> Any:
    """Top-level convenience: translate a single string field."""
    if not isinstance(s, str):
        return s
    return translate_text(s, target_lang, db)
