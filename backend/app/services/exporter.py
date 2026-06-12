import json
from typing import Any


def export_session_markdown(session: dict, moves: list[dict], interventions: list[dict]) -> str:
    lines = [
        f"# Session {session['id']}",
        f"- Game: **{session['game_id']}**",
        f"- Material: {session['material_id']}",
        f"- Status: {session['status']}",
        f"- Started: {session['started_at']}",
        f"- Completed: {session.get('completed_at') or '-'}",
        "",
        "## Moves",
    ]
    for m in moves:
        target = f" → unit `{m['target_unit_id']}`" if m.get("target_unit_id") else ""
        lines.append(f"- **{m['action']}** (round `{m['round_id']}`){target}")
        if m["payload"]:
            lines.append(f"  - payload: `{json.dumps(m['payload'], ensure_ascii=False)}`")
    lines += ["", "## LLM interventions"]
    for iv in interventions:
        lines.append(f"- **{iv['role']}** at {iv['created_at']}")
        for k, v in iv["output"].items():
            if k.startswith("_"):
                continue
            lines.append(f"  - {k}: {v}")
    lines += ["", "## Operator profile"]
    profile = session.get("trace_profile") or {}
    if profile.get("markdown_summary"):
        lines.append(profile["markdown_summary"])
    else:
        lines.append("(no profile)")
    if profile.get("replay_targets"):
        lines.append(f"**Replay targets next round:** {', '.join(profile['replay_targets'])}")
    return "\n".join(lines)


def export_session_json(session: dict, moves: list[dict], interventions: list[dict]) -> dict:
    return {
        "session": session,
        "moves": moves,
        "interventions": interventions,
    }
