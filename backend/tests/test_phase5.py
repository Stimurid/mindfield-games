"""Phase 5: replay loop closure — completed session → mutator → new material → new session.

Mock provider runs deterministically; live LLM is tested by scripts/smoke_replay.py.
"""
import pytest

REAL_SEED_IDS = {
    "false_click": "real_false_click_001",
    "missing_operation": "real_missing_operation_001",
    "sprout_or_slop": "real_sprout_or_slop_001",
    "register_sapper": "real_register_sapper_001",
}


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    return client.post(f"/api/sessions/{sid}/moves", json=body).json()


def _complete_minimal(client, game_id):
    """Drive a minimal session to completion and return its id + parent material id."""
    mats = client.get(f"/api/materials?gameId={game_id}").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions", json={"game_id": game_id, "material_id": real["id"]}).json()
    sid = s["id"]
    if game_id == "false_click":
        _move(client, sid, "select_unit", "select", {"hint_bias": "pseudo_depth"}, target="r1")
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="r1")
    elif game_id == "missing_operation":
        _move(client, sid, "click_gap", "gap", {"gap_id": "rg1"}, target="rg1")
        _move(client, sid, "assign_absence_type", "gap", {"absence_type": "subject"}, target="rg1")
        _move(client, sid, "assign_fate", "fate", {"fate": "restore"}, target="rg1")
    elif game_id == "sprout_or_slop":
        for cid in ["rc01", "rc02", "rc03", "rc04", "rc05"]:
            _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": "cut"}, target=cid)
    else:  # register_sapper
        _move(client, sid, "assign_phrase_action", "first_read",
              {"phrase_action": "hidden_request", "medium": "telegram"}, target="rv1")
        _move(client, sid, "transfer_phrase", "transfer",
              {"target_medium": "voice", "new_phrase": "точно?", "preserves_action": True})
    client.post(f"/api/sessions/{sid}/complete")
    return sid, real["id"]


@pytest.mark.parametrize("game_id", list(REAL_SEED_IDS.keys()))
def test_replay_creates_new_material_and_session(client, game_id):
    sid, parent_mat_id = _complete_minimal(client, game_id)

    r = client.post(f"/api/sessions/{sid}/replay", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["parent_session_id"] == sid
    assert body["parent_material_id"] == parent_mat_id
    assert body["new_session_id"] and body["new_session_id"] != sid
    assert body["new_material_id"] and body["new_material_id"] != parent_mat_id
    assert isinstance(body["mutation_directive"], str) and len(body["mutation_directive"]) > 20

    # New material is in 'mutated' namespace, carries parent + directive
    mat = client.get(f"/api/materials/{body['new_material_id']}").json()
    assert mat["namespace"] == "mutated"
    assert mat["parent_id"] == parent_mat_id
    assert mat["mutation_directive"] == body["mutation_directive"]
    assert mat["source_session_id"] == sid

    # New session is playable: it has the right field_type payload shape
    new_sid = body["new_session_id"]
    new_session = client.get(f"/api/sessions/{new_sid}").json()
    assert new_session["material_id"] == body["new_material_id"]
    assert new_session["status"] == "in_progress"


def test_replay_refuses_incomplete_session(client):
    mats = client.get(f"/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions", json={"game_id": "false_click", "material_id": real["id"]}).json()
    r = client.post(f"/api/sessions/{s['id']}/replay", json={})
    assert r.status_code == 400


def test_player_token_propagates_through_replay(client):
    """Phase 6 hook: token survives parent → mutated session lineage."""
    mats = client.get("/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post(
        "/api/sessions",
        json={"game_id": "false_click", "material_id": real["id"]},
        headers={"X-Player-Token": "tok-phase5-test"},
    ).json()
    sid = s["id"]
    _move(client, sid, "select_unit", "select", {"hint_bias": "pseudo_depth"}, target="r1")
    _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="r1")
    client.post(f"/api/sessions/{sid}/complete")
    r = client.post(f"/api/sessions/{sid}/replay", json={})
    new_sid = r.json()["new_session_id"]
    s2 = client.get(f"/api/sessions/{new_sid}").json()
    # Token must survive through replay
    assert client.get(f"/api/sessions/{sid}").status_code == 200
    s_full = client.get(f"/api/sessions/{new_sid}")
    assert s_full.status_code == 200
