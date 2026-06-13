"""Phase 9: convert a corpus entry into a playable Material per genre."""
import pytest


GAMES = ["false_click", "missing_operation", "sprout_or_slop", "register_sapper"]


def _entry(client, kind="breed"):
    rows = client.get(f"/api/library/entries?kind={kind}").json()
    assert rows
    return rows[0]


@pytest.mark.parametrize("game_id", GAMES)
def test_convert_entry_to_material(client, game_id):
    e = _entry(client)
    r = client.post(f"/api/library/entries/{e['id']}/convert",
                    json={"game_id": game_id}, headers={"X-Player-Token": "p9"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["game_id"] == game_id
    assert body["source_corpus_id"] == e["id"]
    mat = client.get(f"/api/materials/{body['material_id']}").json()
    assert mat["namespace"] == "from_corpus"
    assert mat["source_corpus_id"] == e["id"]
    assert mat["payload"]["type"]


def test_converted_material_playable_in_a_session(client):
    e = _entry(client)
    conv = client.post(f"/api/library/entries/{e['id']}/convert",
                       json={"game_id": "false_click"}, headers={"X-Player-Token": "p9"}).json()
    s = client.post("/api/sessions",
                    json={"game_id": "false_click", "material_id": conv["material_id"]},
                    headers={"X-Player-Token": "p9"}).json()
    assert s["status"] == "in_progress"
    assert s["material_id"] == conv["material_id"]


def test_convert_unknown_entry_returns_404(client):
    r = client.post("/api/library/entries/does-not-exist/convert",
                    json={"game_id": "false_click"}, headers={"X-Player-Token": "p9"})
    assert r.status_code == 404
