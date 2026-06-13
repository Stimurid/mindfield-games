"""Phase 10: Promise Court — 5th genre end-to-end."""


def test_promise_court_genome_loads(client):
    g = client.get("/api/games/promise_court").json()
    assert g["field_type"] == "promise_court_text"
    assert "mark_promise" in g["player_actions"]
    assert "fill_obligation_form" in g["player_actions"]
    assert "accept_promise" in g["player_actions"]
    assert "send_to_court" in g["player_actions"]


def test_promise_court_real_seed_loads(client):
    mats = client.get("/api/materials?gameId=promise_court").json()
    real = next((m for m in mats if m["namespace"] == "real"), None)
    assert real is not None
    assert real["id"] == "real_promise_court_001"


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    return client.post(f"/api/sessions/{sid}/moves", json=body).json()


def test_promise_court_full_flow_court_overload(client):
    mats = client.get("/api/materials?gameId=promise_court").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions",
                    json={"game_id": "promise_court", "material_id": real["id"]},
                    headers={"X-Player-Token": "p10"}).json()
    sid = s["id"]
    # Mark 4 promises, send all to court (none filled completely)
    for pid in ["pb2", "pb3", "pb5", "pb6"]:
        _move(client, sid, "mark_promise", "mark", target=pid)
        _move(client, sid, "fill_obligation_form", "fill",
              payload={"owner": "", "deadline": "", "criterion": "", "fallback": ""}, target=pid)
        _move(client, sid, "send_to_court", "verdict", payload={"verdict": "sent_to_court"}, target=pid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    dims = final["trace_profile"]["dimensions"]
    assert dims["court_load"] == "court_overload"
    assert "promise_blindness" in dims
    assert dims["verdict_distribution"] == {"sent_to_court": 4}


def test_promise_court_full_flow_accepting_loose_promises(client):
    mats = client.get("/api/materials?gameId=promise_court").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions",
                    json={"game_id": "promise_court", "material_id": real["id"]},
                    headers={"X-Player-Token": "p10"}).json()
    sid = s["id"]
    # Mark and accept with deadlines mostly missing — triggers missed_no_deadline
    for pid in ["pb2", "pb3", "pb5", "pb6"]:
        _move(client, sid, "mark_promise", "mark", target=pid)
        _move(client, sid, "fill_obligation_form", "fill",
              payload={"owner": "Команда", "deadline": "", "criterion": "лучше станет", "fallback": "посмотрим"}, target=pid)
        _move(client, sid, "accept_promise", "verdict", payload={"verdict": "accepted"}, target=pid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    dims = final["trace_profile"]["dimensions"]
    assert dims["court_load"] in ("completeness_strict", "balanced")
    # deadline was missing on all four — blindness should name it
    assert dims["promise_blindness"] == "missed_no_deadline"
    assert dims["missing_field_distribution"].get("deadline") == 4


def test_promise_court_replay_loop_works(client):
    mats = client.get("/api/materials?gameId=promise_court").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions",
                    json={"game_id": "promise_court", "material_id": real["id"]},
                    headers={"X-Player-Token": "p10"}).json()
    sid = s["id"]
    for pid in ["pb2", "pb3"]:
        _move(client, sid, "mark_promise", "mark", target=pid)
        _move(client, sid, "fill_obligation_form", "fill",
              payload={"owner": "", "deadline": "", "criterion": "", "fallback": ""}, target=pid)
        _move(client, sid, "send_to_court", "verdict", payload={"verdict": "sent_to_court"}, target=pid)
    client.post(f"/api/sessions/{sid}/complete")
    # Replay must work for the 5th genre too
    r = client.post(f"/api/sessions/{sid}/replay", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    new_mat = client.get(f"/api/materials/{body['new_material_id']}").json()
    assert new_mat["payload"]["type"]
