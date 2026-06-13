"""Phase 6: cross-game Operator Profile aggregator.

Takes all completed sessions for one player_token, picks the latest
session per game_id, and stitches per-game qualitative dimensions into
a single picture. Output stays qualitative — no scores, no levels.
Connections between games are named, not summed.
"""
from collections import defaultdict
from typing import Iterable
from ..models import GameSession


# Map qualitative dimension tags to one-line meaning the cross-game view shows.
_BIAS_MEANING: dict[tuple[str, str], str] = {
    ("false_click", "pseudo_depth"):       "ловится на pseudo-depth — формы важности без операции",
    ("false_click", "dramatic_phrase"):    "ловится на драматических усилителях",
    ("false_click", "abstract_word"):      "ловится на high-status абстракциях",
    ("false_click", "conclusion_like_phrase"):"ловится на 'таким образом' — кликает на шов вывода",
    ("false_click", "familiar_topic"):     "ловится на знакомой теме, а не на операции",

    ("missing_operation", "subject"):      "не замечает пропавшего субъекта/владельца",
    ("missing_operation", "criterion"):    "не замечает пропавшего критерия успеха",
    ("missing_operation", "resource"):     "не замечает пропавшего ресурса/цены",
    ("missing_operation", "promise"):      "не замечает обещаний без owner/срока",
    ("missing_operation", "ontology"):     "не замечает скачка масштаба",
    ("missing_operation", "register"):     "не замечает смены регистра",

    ("sprout_or_slop", "overcuts"):        "режет ростки вместе со слопом",
    ("sprout_or_slop", "oversaves"):       "сохраняет красивый мёртвый слоп под видом ростка",
    ("sprout_or_slop", "proof_addict"):    "просит доказательств слишком рано — стерилизует ростки",
    ("sprout_or_slop", "no_name_avoidance"):"не выносит 'не называть' — называет преждевременно",

    ("register_sapper", "tone_instead_action"):  "оценивает тон, не действие фразы",
    ("register_sapper", "literalizes_joke"):     "уплощает шутку до команды",
    ("register_sapper", "misses_alibi"):         "не видит алиби и скрытых просьб",
    ("register_sapper", "loses_address"):        "теряет адресата при смене медиума",
}


# Cross-game patterns: when these named dimensions co-occur, name the
# higher-order pattern. Keys are sorted (game_id, dimension_value) tuples.
_CROSS_PATTERNS: list[tuple[set[tuple[str, str]], str]] = [
    (
        {("false_click", "pseudo_depth"), ("missing_operation", "accepts_smooth_bridge")},
        "принимает гладкие имитации под видом глубины — pseudo-depth снаружи + готовность купить шпаклёвку внутри",
    ),
    (
        {("sprout_or_slop", "oversaves"), ("missing_operation", "accepts_smooth_bridge")},
        "защищает мёртвую красоту и пропускает скрытые дыры — один и тот же 'не хочу выкидывать гладкое' в двух жанрах",
    ),
    (
        {("false_click", "pseudo_depth"), ("sprout_or_slop", "oversaves")},
        "глубина-форма по обоим контурам: вход — pseudo-depth, выход — сохранение dead beauty",
    ),
    (
        {("register_sapper", "tone_instead_action"), ("false_click", "conclusion_like_phrase")},
        "читает поверхности (тон, шов вывода), а не операцию",
    ),
    (
        {("missing_operation", "resists_patch"), ("sprout_or_slop", "overcuts")},
        "жёсткий ножницы-режим: режет всё что кажется гладким, без incubation",
    ),
]


def _per_game_latest(sessions: Iterable[GameSession]) -> dict[str, GameSession]:
    latest: dict[str, GameSession] = {}
    for s in sessions:
        if s.status != "completed":
            continue
        cur = latest.get(s.game_id)
        if cur is None or (s.completed_at or s.started_at) > (cur.completed_at or cur.started_at):
            latest[s.game_id] = s
    return latest


def build_operator_profile(player_token: str, sessions: Iterable[GameSession]) -> dict:
    latest = _per_game_latest(sessions)
    per_game: dict[str, dict] = {}
    flags: list[tuple[str, str]] = []  # (game_id, dim_value)
    for game_id, sess in latest.items():
        prof = sess.trace_profile or {}
        dims = prof.get("dimensions", {}) or {}
        per_game[game_id] = {
            "session_id": sess.id,
            "completed_at": (sess.completed_at or sess.started_at).isoformat() + "Z" if (sess.completed_at or sess.started_at) else None,
            "dimensions": dims,
            "replay_directives": prof.get("replay_directives", []),
        }
        # Pick the headline dimension per game for cross-pattern matching.
        headline_keys = {
            "false_click": "false_click_bias",
            "missing_operation": "absence_blindness",
            "sprout_or_slop": "selection_bias",
            "register_sapper": "register_blindness",
        }
        h = dims.get(headline_keys.get(game_id, ""))
        if isinstance(h, str):
            flags.append((game_id, h))
        # Also fold extra named dimensions that participate in patterns.
        for extra in ("patch_susceptibility",):
            v = dims.get(extra)
            if isinstance(v, str):
                flags.append((game_id, v))

    explicit_lines = []
    for game_id, val in flags:
        msg = _BIAS_MEANING.get((game_id, val))
        if msg:
            explicit_lines.append(f"**{game_id}**: {msg}")

    flag_set = set(flags)
    cross_patterns = [name for needed, name in _CROSS_PATTERNS if needed.issubset(flag_set)]

    games_played = sorted(latest.keys())
    coverage = f"{len(games_played)} / 4 жанров пройдено"
    if cross_patterns:
        verdict = "связки видны: " + " · ".join(cross_patterns[:3])
    elif len(games_played) < 2:
        verdict = "слишком мало материала — нужно пройти ещё хотя бы один жанр"
    else:
        verdict = "пока связок нет, профили по жанрам не пересекаются"

    return {
        "player_token": player_token,
        "coverage": coverage,
        "games_played": games_played,
        "per_game": per_game,
        "explicit_dimensions": explicit_lines,
        "cross_patterns": cross_patterns,
        "verdict": verdict,
    }
