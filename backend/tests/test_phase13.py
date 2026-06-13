"""Phase 13: Configurator + GameWeaver (playability_critic).

Eight canonical organ banks seeded on startup. Designer assembles a draft
genome by picking organs, runs the GameWeaver critic, gets a structured
verdict that flags missing verb / crisis / trace and any degradation organs.
"""
import pytest


def test_banks_present(client):
    banks = client.get("/api/configurator/banks").json()
    keys = {b["bank"] for b in banks}
    assert keys == {"field", "object", "action", "llm_role", "crisis", "trace", "mutation", "degradation"}
    for b in banks:
        assert b["count"] >= 10
    # Degradation bank flagged for the UI to warn users away.
    assert next(b for b in banks if b["bank"] == "degradation")["is_degradation"] is True


def test_canon_organs_seeded(client):
    organs = client.get("/api/configurator/organs").json()
    assert len(organs) >= 130
    names = {o["name"] for o in organs}
    assert "семантический поток" in names           # field bank
    assert "промпт-костыль" in names                # object bank
    assert "кликнуть" in names                      # action bank
    assert "слопогенератор" in names                # llm_role bank
    assert "красивая пустая фраза" in names         # crisis bank
    assert "карта кликов" in names                  # trace bank
    assert "усложнить слоп" in names                # mutation bank
    assert "summary-сервис" in names                # degradation bank


def _pick_first(client, bank):
    rows = client.get(f"/api/configurator/organs?bank={bank}").json()
    return rows[0]["id"]


def test_draft_lifecycle(client):
    payload = {
        "name": "test-draft",
        "function": "тренируем различение слопа",
        "verb": "кликнуть",
        "maturity_stage": 2,
        "selected_organs": {
            "field":  [_pick_first(client, "field")],
            "action": [_pick_first(client, "action")],
            "crisis": [_pick_first(client, "crisis")],
            "trace":  [_pick_first(client, "trace")],
        },
    }
    r = client.post("/api/configurator/drafts", json=payload, headers={"X-Player-Token": "p13"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["name"] == "test-draft"
    assert d["maturity_stage"] == 2
    assert d["player_token"] == "p13"

    fetched = client.get(f"/api/configurator/drafts/{d['id']}").json()
    assert fetched["id"] == d["id"]

    patched = client.patch(f"/api/configurator/drafts/{d['id']}",
                           json={"maturity_stage": 3, "verb": "удалить"}).json()
    assert patched["maturity_stage"] == 3
    assert patched["verb"] == "удалить"


def test_weaver_playable_when_minimums_present(client):
    payload = {
        "name": "playable-draft",
        "verb": "кликнуть",
        "maturity_stage": 2,
        "selected_organs": {
            "field":  [_pick_first(client, "field")],
            "action": [_pick_first(client, "action")],
            "crisis": [_pick_first(client, "crisis")],
            "trace":  [_pick_first(client, "trace")],
        },
    }
    d = client.post("/api/configurator/drafts", json=payload, headers={"X-Player-Token": "p13"}).json()
    r = client.post(f"/api/configurator/drafts/{d['id']}/weaver", json={})
    body = r.json()
    v = body["verdict"]
    assert v["verb_status"] == "present"
    assert v["crisis_status"] == "present"
    assert v["trace_status"] == "present"
    assert v["playable_verdict"] == "playable"
    assert isinstance(v["critique"], str) and len(v["critique"]) > 10
    # The verdict persists on the draft.
    fetched = client.get(f"/api/configurator/drafts/{d['id']}").json()
    assert fetched["weaver_verdict"]["playable_verdict"] == "playable"


def test_weaver_rejects_missing_verb(client):
    payload = {
        "name": "no-verb",
        "verb": "",
        "selected_organs": {
            "crisis": [_pick_first(client, "crisis")],
            "trace":  [_pick_first(client, "trace")],
        },
    }
    d = client.post("/api/configurator/drafts", json=payload, headers={"X-Player-Token": "p13"}).json()
    v = client.post(f"/api/configurator/drafts/{d['id']}/weaver", json={}).json()["verdict"]
    assert v["verb_status"] == "missing"
    assert v["playable_verdict"] == "not_playable_yet"


def test_weaver_flags_degradation_organ(client):
    payload = {
        "name": "rotten",
        "verb": "кликнуть",
        "selected_organs": {
            "field":       [_pick_first(client, "field")],
            "action":      [_pick_first(client, "action")],
            "crisis":      [_pick_first(client, "crisis")],
            "trace":       [_pick_first(client, "trace")],
            "degradation": [_pick_first(client, "degradation")],
        },
    }
    d = client.post("/api/configurator/drafts", json=payload, headers={"X-Player-Token": "p13"}).json()
    v = client.post(f"/api/configurator/drafts/{d['id']}/weaver", json={}).json()["verdict"]
    assert v["playable_verdict"] == "rotten"
    assert v["degradation_warnings"]


def test_drafts_mine_filter(client):
    p1 = {"name": "mine", "verb": "x"}
    p2 = {"name": "theirs", "verb": "y"}
    client.post("/api/configurator/drafts", json=p1, headers={"X-Player-Token": "p13-a"})
    client.post("/api/configurator/drafts", json=p2, headers={"X-Player-Token": "p13-b"})
    rows = client.get("/api/configurator/drafts?mine=true", headers={"X-Player-Token": "p13-a"}).json()
    assert all(d["player_token"] == "p13-a" for d in rows)
    assert any(d["name"] == "mine" for d in rows)
    assert not any(d["name"] == "theirs" for d in rows)
