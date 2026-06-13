"""Phase 18: remote playtest evaluation harness."""
import uuid


H = {"X-Player-Token": "p18"}


def test_start_run_returns_run_and_followup_token(client):
    r = client.post("/api/playtests/start",
                    json={"mode": "remote_test"},
                    headers=H)
    assert r.status_code == 200, r.text
    run = r.json()
    assert run["id"] and run["mode"] == "remote_test"
    assert run["player_token"] == "p18"
    assert run["completed_at"] is None
    assert run["followup"] and run["followup"]["token"]
    assert run["followup"]["due_at"]


def test_save_reflection_persists(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    r = client.post(f"/api/playtests/{run['id']}/reflection",
                    json={"stage": "after_game_1",
                          "prompt": "What did you think you were doing?",
                          "answer": "I thought I was picking the strongest sentence"},
                    headers=H)
    assert r.status_code == 200, r.text
    saved = r.json()
    assert saved["stage"] == "after_game_1"
    assert "strongest sentence" in saved["answer"]

    full = client.get(f"/api/playtests/{run['id']}", headers=H).json()
    assert any(x["id"] == saved["id"] for x in full["reflections"])


def test_reflection_rejects_unknown_stage(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    r = client.post(f"/api/playtests/{run['id']}/reflection",
                    json={"stage": "after_dinner", "prompt": "x", "answer": "y"},
                    headers=H)
    assert r.status_code == 400


def test_complete_run_with_verdict(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    r = client.post(f"/api/playtests/{run['id']}/complete",
                    json={"final_verdict": "profile_recognition",
                          "extra_session_ids": ["sess-aaa", "sess-bbb"]},
                    headers=H)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["final_verdict"] == "profile_recognition"
    assert body["completed_at"]
    assert body["session_ids"] == ["sess-aaa", "sess-bbb"]


def test_complete_run_rejects_unknown_verdict(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    r = client.post(f"/api/playtests/{run['id']}/complete",
                    json={"final_verdict": "winner"},
                    headers=H)
    assert r.status_code == 400


def test_followup_get_and_submit(client):
    run = client.post("/api/playtests/start",
                     json={"mode": "remote_test"},
                     headers=H).json()
    token = run["followup"]["token"]

    # GET — no auth needed
    r = client.get(f"/api/playtests/followup/{token}")
    assert r.status_code == 200
    body = r.json()
    assert body["transfer_seen"] is None
    assert body["completed_at"] is None
    assert len(body["checklist"]) == 6
    keys = {q["key"] for q in body["checklist"]}
    assert keys == {
        "transfer_seen", "outside_app_example", "appeared_spontaneously",
        "remembered_operation", "confidence", "game_helped",
    }

    # POST — submit answers
    r2 = client.post(f"/api/playtests/followup/{token}",
                     json={"transfer_seen": "yes",
                           "outside_app_example": "Заметил в письме коллеги — pseudo_depth.",
                           "appeared_spontaneously": "yes",
                           "remembered_operation": "ложный клик на форму вместо операции",
                           "confidence": "medium",
                           "game_helped": "yes"})
    assert r2.status_code == 200
    assert r2.json()["submitted_at"]

    # Idempotent re-read
    r3 = client.get(f"/api/playtests/followup/{token}").json()
    assert r3["transfer_seen"] == "yes"
    assert r3["confidence"] == "medium"
    assert r3["completed_at"]


def test_followup_rejects_bad_token(client):
    r = client.get(f"/api/playtests/followup/{uuid.uuid4().hex}")
    assert r.status_code == 404
    r2 = client.post(f"/api/playtests/followup/{uuid.uuid4().hex}",
                     json={"transfer_seen": "yes"})
    assert r2.status_code == 404


def test_followup_rejects_invalid_values(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    token = run["followup"]["token"]
    r = client.post(f"/api/playtests/followup/{token}",
                    json={"transfer_seen": "maybe"})
    assert r.status_code == 400
    r2 = client.post(f"/api/playtests/followup/{token}",
                     json={"confidence": "extreme"})
    assert r2.status_code == 400


def test_no_cross_run_leak_by_different_player(client):
    run = client.post("/api/playtests/start", json={}, headers=H).json()
    # Different player token must NOT be able to read or mutate this run.
    other = {"X-Player-Token": "stranger"}
    r1 = client.get(f"/api/playtests/{run['id']}", headers=other)
    assert r1.status_code == 403
    r2 = client.post(f"/api/playtests/{run['id']}/reflection",
                     json={"stage": "final", "prompt": "x", "answer": "y"},
                     headers=other)
    assert r2.status_code == 403
    r3 = client.post(f"/api/playtests/{run['id']}/complete",
                     json={"final_verdict": "unclear"}, headers=other)
    assert r3.status_code == 403


def test_unknown_run_returns_404(client):
    r = client.get(f"/api/playtests/{uuid.uuid4().hex}", headers=H)
    assert r.status_code == 404


def test_export_markdown(client):
    run = client.post("/api/playtests/start", json={"mode": "self_test"}, headers=H).json()
    client.post(f"/api/playtests/{run['id']}/reflection",
                json={"stage": "after_game_1",
                      "prompt": "What did you think you were doing?",
                      "answer": "I was picking bearing nodes"},
                headers=H)
    client.post(f"/api/playtests/{run['id']}/reflection",
                json={"stage": "after_profile",
                      "prompt": "Specific or generic?",
                      "answer": "specific — pseudo_depth landed"},
                headers=H)
    client.post(f"/api/playtests/{run['id']}/complete",
                json={"final_verdict": "profile_recognition"},
                headers=H)

    r = client.get(f"/api/playtests/{run['id']}/export", headers=H)
    assert r.status_code == 200
    md = r.json()["body"]
    assert "profile_recognition" in md
    assert "after_game_1" in md
    assert "after_profile" in md
    assert "bearing nodes" in md
    assert "24h follow-up" in md
    assert run["followup"]["token"] in md   # token shown for pending followup
