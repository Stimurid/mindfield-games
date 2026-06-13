"""Live smoke for the Phase 5 replay loop against a running backend.

Runs inside the docker network or against http://localhost:8000 — pass
BASE_URL env to override.
"""
import json, os, sys, urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8000/api")
MODEL = os.environ.get("SMOKE_MODEL")  # None = backend default


def _req(method, path, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        raw = resp.read().decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main(game_id="false_click"):
    mats = _req("GET", f"/materials?gameId={game_id}")
    real = next(m for m in mats if m["namespace"] == "real")
    s = _req("POST", "/sessions",
             {"game_id": game_id, "material_id": real["id"]},
             {"X-Player-Token": "smoke-tok-phase5"})
    sid = s["id"]
    print(f"[parent session] {sid[:8]} on {real['id']}")

    def move(action, rnd, payload, target=None):
        body = {"action": action, "round_id": rnd, "payload": payload}
        if target:
            body["target_unit_id"] = target
        _req("POST", f"/sessions/{sid}/moves", body)

    if game_id == "false_click":
        move("select_unit", "select", {"hint_bias": "pseudo_depth"}, "r1")
        move("prove_operation", "prove", {"operation": "claims operation: глубинная природа вовлечённости"}, "r1")
        move("assign_verdict", "verdict", {"verdict": "false_click"}, "r1")
    elif game_id == "missing_operation":
        move("click_gap", "gap", {"gap_id": "rg2"}, "rg2")
        move("assign_absence_type", "gap", {"absence_type": "logical"}, "rg2")
        move("assign_fate", "fate", {"fate": "restore"}, "rg2")
    elif game_id == "sprout_or_slop":
        for cid in ["rc01", "rc02", "rc03", "rc04", "rc05"]:
            move("sort_card", "sort", {"card_id": cid, "fate": "cut"}, cid)
    else:  # register_sapper
        move("assign_phrase_action", "first_read",
             {"phrase_action": "hidden_request", "medium": "telegram"}, "rv1")

    final = _req("POST", f"/sessions/{sid}/complete")
    dims = final["trace_profile"]["dimensions"]
    print(f"[parent profile] {dims}")
    directive = final["trace_profile"]["replay_directives"][0]
    print(f"[parent directive] {directive}")

    rep = _req("POST", f"/sessions/{sid}/replay", {"model": MODEL} if MODEL else {})
    print(f"\n[replay]")
    print(f"  new_session_id     : {rep['new_session_id'][:8]}")
    print(f"  new_material_id    : {rep['new_material_id'][:8]}")
    print(f"  mutation_directive : {rep['mutation_directive']!r}")

    mat = _req("GET", f"/materials/{rep['new_material_id']}")
    pl = mat["payload"]
    items = pl.get("units") or pl.get("blocks") or pl.get("cards") or pl.get("variants") or []
    print(f"\n[mutated material]")
    print(f"  title         : {mat['title']!r}")
    print(f"  namespace     : {mat['namespace']}")
    print(f"  parent linked : {bool(mat['parent_id'])}")
    print(f"  payload.type  : {pl.get('type')}")
    print(f"  item count    : {len(items)}")
    print(f"  first 3 items :")
    for u in items[:3]:
        txt = u.get("text") or u.get("context") or json.dumps(u, ensure_ascii=False)
        print(f"    · {txt[:140]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "false_click")
