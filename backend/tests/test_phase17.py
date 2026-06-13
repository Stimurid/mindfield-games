"""Phase 17: researcher workbench — hypotheses + organ discussion + game promotion."""
import pytest


H = {"X-Player-Token": "p17"}


def test_hypothesis_lifecycle(client):
    r = client.post("/api/research/hypotheses",
                    json={"title": "ZPD via LLM", "body_md": "тестовая гипотеза"},
                    headers=H)
    assert r.status_code == 200
    h = r.json()
    assert h["title"] == "ZPD via LLM"
    assert h["player_token"] == "p17"

    # patch
    r2 = client.patch(f"/api/research/hypotheses/{h['id']}",
                      json={"status": "published", "tags": ["zpd", "outils"]})
    assert r2.status_code == 200
    assert r2.json()["status"] == "published"

    # list mine
    rows = client.get("/api/research/hypotheses?mine=true", headers=H).json()
    assert any(x["id"] == h["id"] for x in rows)

    # get
    one = client.get(f"/api/research/hypotheses/{h['id']}").json()
    assert one["id"] == h["id"]

    # delete
    r4 = client.delete(f"/api/research/hypotheses/{h['id']}")
    assert r4.status_code == 200
    r5 = client.get(f"/api/research/hypotheses/{h['id']}")
    assert r5.status_code == 404


def test_summon_each_organ_on_hypothesis(client):
    h = client.post("/api/research/hypotheses",
                    json={"title": "Is pseudo-depth a real bias?",
                          "body_md": "Утверждение: LLM-ответы с pseudo-depth заставляют игроков переоценивать качество. ..."},
                    headers=H).json()
    for role in ("prosecutor", "spackler", "sprout_advocate", "literal_alien"):
        r = client.post(f"/api/research/hypotheses/{h['id']}/summon",
                        json={"role": role}, headers=H)
        assert r.status_code == 200
        out = r.json()["output"]
        # contract: no assistant-shaped keys leak in
        for k in ("answer", "solution", "explanation_for_player", "helpful_tip"):
            assert k not in out

    listed = client.get(f"/api/research/hypotheses/{h['id']}/discussions").json()
    roles = {c["role"] for c in listed}
    assert roles == {"prosecutor", "spackler", "sprout_advocate", "literal_alien"}


def test_summon_rejects_unknown_role(client):
    h = client.post("/api/research/hypotheses",
                    json={"title": "x", "body_md": "y"},
                    headers=H).json()
    r = client.post(f"/api/research/hypotheses/{h['id']}/summon",
                    json={"role": "ghostwriter"}, headers=H)
    assert r.status_code == 400


# ── Draft promotion to runtime ───────────────────────────────────────────────

def _pick(client, bank):
    rows = client.get(f"/api/configurator/organs?bank={bank}").json()
    return rows[0]["id"]


def test_field_types_endpoint(client):
    rows = client.get("/api/configurator/field-types").json()
    ids = {r["id"] for r in rows}
    assert ids == {
        "clickable_text_units", "gap_click_text", "card_sorting",
        "medium_shift_phrase", "promise_court_text",
    }


def test_promote_draft_creates_runtime_game(client):
    # build minimum-viable draft
    d = client.post("/api/configurator/drafts", json={
        "name": "Тестовая игра исследователя",
        "function": "тест функции",
        "verb": "кликнуть",
        "maturity_stage": 2,
        "selected_organs": {
            "field":    [_pick(client, "field")],
            "action":   [_pick(client, "action")],
            "crisis":   [_pick(client, "crisis")],
            "trace":    [_pick(client, "trace")],
            "llm_role": [_pick(client, "llm_role")],
        },
    }, headers=H).json()

    r = client.post(f"/api/configurator/drafts/{d['id']}/promote",
                    json={"field_type": "clickable_text_units"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["promoted_game_id"].startswith("promoted_")
    assert body["field_type"] == "clickable_text_units"

    # The promoted game must appear in /api/games and be openable.
    games = client.get("/api/games").json()
    gids = {g["id"] for g in games}
    assert body["promoted_game_id"] in gids

    g = client.get(f"/api/games/{body['promoted_game_id']}").json()
    assert g["field_type"] == "clickable_text_units"
    assert g["player_actions"]
    assert g["rounds"]
    assert g["llm_roles"]


def test_promote_rejects_unknown_field_type(client):
    d = client.post("/api/configurator/drafts", json={
        "name": "x", "verb": "y",
    }, headers=H).json()
    r = client.post(f"/api/configurator/drafts/{d['id']}/promote",
                    json={"field_type": "magic_field"})
    assert r.status_code == 400


def test_session_runs_on_promoted_genome(client):
    d = client.post("/api/configurator/drafts", json={
        "name": "Готовая игра",
        "verb": "кликнуть",
        "selected_organs": {
            "field": [_pick(client, "field")],
            "action": [_pick(client, "action")],
            "crisis": [_pick(client, "crisis")],
            "trace":  [_pick(client, "trace")],
        },
    }, headers=H).json()
    pr = client.post(f"/api/configurator/drafts/{d['id']}/promote",
                     json={"field_type": "clickable_text_units"}).json()
    gid = pr["promoted_game_id"]

    # Need a material for the new game — reuse a real seed from False Click for shape.
    mats = client.get("/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    full = client.get(f"/api/materials/{real['id']}").json()

    # Create a material under the new game with the same payload shape.
    new_mat = client.post("/api/admin/materials", json={
        "game_id": gid,
        "title": "[promoted-test] reuse seed",
        "namespace": "demo",
        "payload": full["payload"],
    }).json()

    s = client.post("/api/sessions",
                    json={"game_id": gid, "material_id": new_mat["id"]},
                    headers=H).json()
    assert s["status"] == "in_progress"
    assert s["material_id"] == new_mat["id"]


def test_hypothesis_link_to_draft(client):
    d = client.post("/api/configurator/drafts", json={
        "name": "linked draft", "verb": "x",
    }, headers=H).json()
    h = client.post("/api/research/hypotheses",
                    json={"title": "linked hypothesis", "linked_draft_id": d["id"]},
                    headers=H).json()
    assert h["linked_draft_id"] == d["id"]
