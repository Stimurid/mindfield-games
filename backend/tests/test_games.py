def test_list_games(client):
    r = client.get("/api/games")
    assert r.status_code == 200
    ids = {g["id"] for g in r.json()}
    assert ids == {"false_click", "missing_operation", "sprout_or_slop", "register_sapper", "promise_court"}


def test_get_game_genome(client):
    r = client.get("/api/games/false_click")
    assert r.status_code == 200
    g = r.json()
    assert g["field_type"] == "clickable_text_units"
    assert "prove_operation" in g["player_actions"]
    assert any(role["id"] == "prosecutor" for role in g["llm_roles"])


def test_unknown_game_404(client):
    assert client.get("/api/games/textopolis").status_code == 404
