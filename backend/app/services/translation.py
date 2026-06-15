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
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterable
from sqlalchemy.orm import Session
from ..models import Translation
from ..database import SessionLocal


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


_PARALLEL_WORKERS = 8
_MAX_LLM_TIMEOUT_S = 60.0  # hard upper bound per single string


def _prefetch_and_translate_batch(texts: list[str], target_lang: str, db: Session) -> dict[str, str]:
    """Translate a batch of unique strings concurrently.

    Returns dict {source_text → target_text}. Strings already in cache are
    served from cache. Misses are dispatched in a thread pool (each thread
    opens its own DB session because LLM calls are blocking I/O and the
    parent session is single-threaded).
    """
    if target_lang == "ru" or not texts:
        return {}

    # Filter pass-throughs.
    real = [s for s in set(texts) if s and s.strip() and not _looks_like_identifier(str(s))]
    if not real:
        return {}

    # Single batch lookup against the cache.
    by_hash = {_hash(s): s for s in real}
    hits = (
        db.query(Translation)
        .filter(Translation.target_lang == target_lang)
        .filter(Translation.source_hash.in_(by_hash.keys()))
        .all()
    )
    result: dict[str, str] = {by_hash[h.source_hash]: h.target_text for h in hits}
    misses = [s for s in real if s not in result]
    if not misses:
        return result

    from ..llm.provider import get_provider
    provider = get_provider()

    def _one(src: str) -> tuple[str, str]:
        own_db = SessionLocal()
        try:
            # Re-check inside the worker — another worker may have just cached.
            h = _hash(src)
            row = own_db.query(Translation).filter(
                Translation.source_hash == h,
                Translation.target_lang == target_lang,
            ).first()
            if row:
                return src, row.target_text
            try:
                out = provider.call_role(
                    "translator", {"text": src, "target_lang": target_lang}
                )
                translated = (out.get("translated") or "").strip() or src
            except Exception as e:
                log.warning("translation failure (%s); returning source", e)
                return src, src
            # Persist
            try:
                own_db.add(Translation(
                    source_hash=h, source_lang="ru", target_lang=target_lang,
                    source_text=src, target_text=translated,
                ))
                own_db.commit()
            except Exception:
                own_db.rollback()  # race: another worker won; fine
            return src, translated
        finally:
            own_db.close()

    with ThreadPoolExecutor(max_workers=_PARALLEL_WORKERS) as ex:
        for src, tgt in ex.map(_one, misses, timeout=_MAX_LLM_TIMEOUT_S * 2):
            result[src] = tgt
    return result


def _collect_strings(obj: Any, parts: list[str], acc: list[str]):
    """Walk dot-path WITHOUT translating — just collect target strings."""
    if not parts:
        return
    key = parts[0]
    rest = parts[1:]
    if isinstance(obj, list):
        for item in obj:
            _collect_strings(item, parts, acc)
        return
    if not isinstance(obj, dict):
        return
    if key.endswith("[]"):
        list_key = key[:-2]
        lst = obj.get(list_key)
        if not isinstance(lst, list):
            return
        for item in lst:
            _collect_strings(item, rest, acc)
        return
    if not rest:
        v = obj.get(key)
        if isinstance(v, str):
            acc.append(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    acc.append(x)
        return
    child = obj.get(key)
    if isinstance(child, (dict, list)):
        _collect_strings(child, rest, acc)


def _apply_with_table(obj: Any, parts: list[str], table: dict[str, str]):
    """Same as _apply but uses a precomputed lookup table instead of calling LLM."""
    if not parts:
        return
    key = parts[0]
    rest = parts[1:]
    if isinstance(obj, list):
        for item in obj:
            _apply_with_table(item, parts, table)
        return
    if not isinstance(obj, dict):
        return
    if key.endswith("[]"):
        list_key = key[:-2]
        lst = obj.get(list_key)
        if not isinstance(lst, list):
            return
        for item in lst:
            _apply_with_table(item, rest, table)
        return
    if not rest:
        v = obj.get(key)
        if isinstance(v, str):
            obj[key] = table.get(v, v)
        elif isinstance(v, list):
            obj[key] = [table.get(x, x) if isinstance(x, str) else x for x in v]
        return
    child = obj.get(key)
    if isinstance(child, (dict, list)):
        _apply_with_table(child, rest, table)


def translate_dict(d: dict | list, paths: Iterable[str], target_lang: str, db: Session) -> dict | list:
    """Translate strings at the given dot-paths inside a dict (deep-copied).

    Two-pass strategy:
      1. Walk the paths and COLLECT all target strings (no LLM).
      2. Batch-translate the unique set in parallel (up to 8 workers).
      3. Walk again and substitute from the lookup table.

    This turns N serial LLM round-trips into ceil(N / 8) parallel batches.
    """
    if target_lang == "ru" or not d:
        return d
    out = copy.deepcopy(d)
    targets: list[str] = []
    for p in paths:
        _collect_strings(out, p.split("."), targets)
    if not targets:
        return out
    table = _prefetch_and_translate_batch(targets, target_lang, db)
    for p in paths:
        _apply_with_table(out, p.split("."), table)
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


def translate_strings_batch(texts: list[str], target_lang: str, db: Session) -> dict[str, str]:
    """Public wrapper around the parallel batch translator. Useful for endpoints
    that loop over a list of dicts and need to translate one or two fields
    on each (games list, materials list, etc.) — collect all strings first,
    call this, then look up each field in the returned dict."""
    return _prefetch_and_translate_batch(texts, target_lang, db)
