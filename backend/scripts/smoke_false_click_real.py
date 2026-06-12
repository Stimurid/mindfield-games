"""End-to-end smoke against a running backend on :8000.

Plays the real False Click seed as a synthetic player and prints
prosecutor responses + final qualitative profile + replay directives.
This is what a live tester will see (minus the rendering)."""
import json, sys, urllib.request

import os
B = "http://localhost:8000/api"
MODEL = os.environ.get("SMOKE_MODEL")  # None = backend default


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{B}{path}", data=data, method=method,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r) as resp:
        raw = resp.read().decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main():
    mats = _req("GET", "/materials?gameId=false_click")
    real = next((m for m in mats if m["namespace"] == "real"), None)
    if not real:
        sys.exit("no real-namespace material — backend not freshly seeded")
    print(f"[material] {real['id']} · {real['title']}")

    sess = _req("POST", "/sessions", {"game_id": "false_click", "material_id": real["id"]})
    sid = sess["id"]
    print(f"[session] {sid[:8]} · status={sess['status']}")

    def move(action, payload=None, target=None, rnd="select"):
        body = {"action": action, "round_id": rnd, "payload": payload or {}}
        if target:
            body["target_unit_id"] = target
        return _req("POST", f"/sessions/{sid}/moves", body)

    def llm(role, ctx):
        body = {"role": role, "context": ctx}
        if MODEL: body["model"] = MODEL
        return _req("POST", f"/sessions/{sid}/llm-intervention", body)

    # Player picks two pseudo_depth phrases — same bias dominating
    rounds = [
        ("r1",  "pseudo_depth",  "claims operation: глубинная природа вовлечённости"),
        ("r11", "pseudo_depth",  "claims operation: умение слышать на новом уровне"),
        ("r10", "dramatic_phrase","claims operation: фундаментально новые горизонты"),
    ]
    for uid, bias, op in rounds:
        move("select_unit", {"hint_bias": bias}, target=uid)
        move("prove_operation", {"operation": op}, target=uid, rnd="prove")
        pros = llm("prosecutor", {"phrase": uid, "claimed_operation": op})["output"]
        print(f"\n[prosecutor on {uid}]")
        for a in pros.get("attacks", []):
            print(f"  attack: {a}")
        print(f"  probe : {pros.get('probe_question')}")
        move("assign_verdict", {"verdict": "false_click"}, target=uid, rnd="verdict")

    final = _req("POST", f"/sessions/{sid}/complete")
    prof = final["trace_profile"]
    print(f"\n[profile] game={prof['game_id']}")
    for k, v in prof["dimensions"].items():
        print(f"  {k}: {v}")
    print("\n[replay_directives]")
    for d in prof.get("replay_directives", []):
        print(f"  → {d}")

    md = _req("GET", f"/sessions/{sid}/export?format=md")
    print(f"\n[export size] {len(md)} chars · /api/sessions/{sid[:8]}.../export?format=md")


if __name__ == "__main__":
    main()
