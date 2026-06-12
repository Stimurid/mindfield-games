"""Live role-drift gauntlet.

Runs every (model x role) combination against real seed contexts and
writes sanitized outputs to docs/live_gauntlet/<model>__<role>.md.

Usage: backend already running on :8000 with MINDFIELD_LLM_API_KEY set.

  python backend/scripts/live_role_gauntlet.py

No keys, no env, no raw HTTP bodies leak into the report.
"""
from __future__ import annotations
import json, sys, time, urllib.request
from pathlib import Path

B = "http://localhost:8000/api"
MODELS = ["gpt-4.1-mini", "grok-4-0709"]
OUT = Path(__file__).resolve().parents[2] / "docs" / "live_gauntlet"
OUT.mkdir(parents=True, exist_ok=True)


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{B}{path}", data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=90) as resp:
        return json.loads(resp.read().decode())


def _seed_session(game_id):
    mats = _req("GET", f"/materials?gameId={game_id}")
    real = next(m for m in mats if m["namespace"] == "real")
    s = _req("POST", "/sessions", {"game_id": game_id, "material_id": real["id"]})
    return s["id"], real["id"]


PROBES = {
    # role -> (game_id, intervention_context, why_this_is_a_drift_test)
    "prosecutor": (
        "false_click",
        {
            "phrase": "Discovery — это про умение слышать пользователя на новом уровне.",
            "claimed_operation": "this phrase introduces a distinction between hearing and listening",
        },
        "honest-looking but pseudo-depth claim; drift = praising or fixing the operation",
    ),
    "spackler": (
        "missing_operation",
        {
            "gap_context": "Соответственно было принято решение перейти к новой модели работы с длинной "
                           "когортой, опирающейся на проактивный success management. "
                           "Это позволит существенно повысить вовлечённость, удержание и общую лояльность.",
            "absence_type": "criterion",
        },
        "missing success criterion; drift = honestly repairing instead of offering a smooth-but-hollow patch",
    ),
    "sprout_advocate": (
        "sprout_or_slop",
        {
            "card_text": "Мы помогаем людям раскрывать свой максимальный потенциал.",
            "fate": "cut",
        },
        "obvious slop the player cut; drift = agreeing with the player instead of defending the slop",
    ),
    "literal_alien": (
        "register_sapper",
        {
            "phrase": "вы уверены?",
            "medium": "telegram",
        },
        "covert hidden_request in a chat; drift = correctly reading it as hidden_request",
    ),
}

ASSISTANT_KEYS = {"answer", "solution", "explanation_for_player", "helpful_tip", "guidance", "feedback"}
ASSISTANT_PHRASES = [
    "here is the answer", "the correct answer is", "let me help you",
    "you should think about", "you might want to consider", "a good approach is",
    "the right way is", "i suggest you", "i recommend",
]

ROLE_REQUIRED_KEYS = {
    "prosecutor":      {"attacks", "probe_question"},
    "spackler":        {"patch", "risk"},
    "sprout_advocate": {"counterposition", "pressure_question"},
    "literal_alien":   {"literal_reading", "things_i_cannot_see"},
}


def sanitize(out: dict) -> dict:
    return {k: v for k, v in out.items() if not k.startswith("_")}


def heuristic_flags(role: str, out: dict) -> list[str]:
    flags = []
    keys = set(out)
    # 1. assistant-shaped keys
    if keys & ASSISTANT_KEYS:
        flags.append(f"assistant_keys:{sorted(keys & ASSISTANT_KEYS)}")
    # 2. required keys present
    missing = ROLE_REQUIRED_KEYS[role] - keys
    if missing:
        flags.append(f"missing_required:{sorted(missing)}")
    # 3. assistant phrasing
    flat = " ".join(str(v).lower() for v in out.values())
    for p in ASSISTANT_PHRASES:
        if p in flat:
            flags.append(f"assistant_phrase:{p!r}")
            break
    # 4. role-specific drift
    if role == "prosecutor":
        for v in (out.get("attacks") or []):
            s = str(v).lower()
            if any(t in s for t in ("well done", "good catch", "valid choice", "you are correct")):
                flags.append("prosecutor_praise")
        if any(t in flat for t in ("the operation is", "the correct operation", "the real operation")):
            flags.append("prosecutor_gives_operation")
    if role == "spackler":
        # spackler must NOT honestly name the missing operation; risk should describe the *concealment*
        risk = str(out.get("risk", "")).lower()
        if "actually missing" in risk or "real gap" in risk:
            flags.append("spackler_too_honest")
    if role == "sprout_advocate":
        flat_lower = flat
        if "i agree" in flat_lower or "you are right" in flat_lower:
            flags.append("advocate_agrees")
    if role == "literal_alien":
        # literal_alien must NOT correctly name hidden_request / alibi / in_group_check
        if any(t in flat for t in ("hidden request", "covert request", "alibi", "in-group code identified")):
            flags.append("alien_reads_register_correctly")
    return flags


def run_one(model: str, role: str):
    game_id, ctx, why = PROBES[role]
    sid, mid = _seed_session(game_id)
    t0 = time.monotonic()
    try:
        iv = _req("POST", f"/sessions/{sid}/llm-intervention",
                  {"role": role, "context": ctx, "model": model})
    except Exception as e:
        return {
            "model": model, "role": role, "game_id": game_id,
            "material_id": mid, "context": ctx, "why_probed": why,
            "elapsed_sec": round(time.monotonic() - t0, 2),
            "error": str(e), "output": None, "flags": ["http_error"],
        }
    dt = time.monotonic() - t0
    raw = iv["output"]
    flags = heuristic_flags(role, raw)
    return {
        "model": model, "role": role, "game_id": game_id,
        "material_id": mid, "context": ctx, "why_probed": why,
        "elapsed_sec": round(dt, 2),
        "error": None, "output": sanitize(raw), "flags": flags,
    }


def render_md(rec):
    lines = [
        f"# {rec['model']} · {rec['role']}",
        "",
        f"- game: `{rec['game_id']}`",
        f"- material: `{rec['material_id']}`",
        f"- elapsed: {rec['elapsed_sec']}s",
        f"- drift test: {rec['why_probed']}",
        "",
        "## context sent",
        "```json",
        json.dumps(rec["context"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## raw output (sanitized — internal `_*` keys removed)",
    ]
    if rec["error"]:
        lines.append(f"_error: {rec['error']}_")
    else:
        lines += ["```json", json.dumps(rec["output"], indent=2, ensure_ascii=False), "```"]
    lines += ["", "## heuristic flags"]
    if rec["flags"]:
        for f in rec["flags"]:
            lines.append(f"- `{f}`")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main():
    print(f"[gauntlet] models={MODELS}\n", flush=True)
    results = []
    for model in MODELS:
        for role in ROLE_REQUIRED_KEYS:
            print(f"  · {model} · {role}", flush=True)
            r = run_one(model, role)
            fname = f"{model.replace('.','_').replace('/','_')}__{role}.md"
            (OUT / fname).write_text(render_md(r), encoding="utf-8")
            results.append(r)
    # index
    idx = ["# Live role-drift gauntlet — raw outputs\n",
           "| model | role | elapsed | flags |",
           "| --- | --- | --- | --- |"]
    for r in results:
        flags = ", ".join(r["flags"]) or "—"
        idx.append(f"| `{r['model']}` | `{r['role']}` | {r['elapsed_sec']}s | {flags} |")
    (OUT / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"\n[gauntlet] wrote {len(results)} runs to {OUT}", flush=True)
    # one-line summary to stdout
    for r in results:
        tag = ",".join(r["flags"]) if r["flags"] else "clean"
        print(f"  {r['model']:14} {r['role']:18} {r['elapsed_sec']:5}s  {tag}")


if __name__ == "__main__":
    main()
