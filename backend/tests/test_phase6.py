"""Phase 6: cross-game Operator Profile via X-Player-Token."""


TOK = "tok-phase6"
H = {"X-Player-Token": TOK}


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    return client.post(f"/api/sessions/{sid}/moves", json=body).json()


def _real(client, gid):
    mats = client.get(f"/api/materials?gameId={gid}").json()
    return next(m for m in mats if m["namespace"] == "real")


def _play_false_click(client):
    mat = _real(client, "false_click")
    s = client.post("/api/sessions", json={"game_id": "false_click", "material_id": mat["id"]}, headers=H).json()
    sid = s["id"]
    _move(client, sid, "select_unit", "select", {"hint_bias": "pseudo_depth"}, target="r1")
    _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="r1")
    client.post(f"/api/sessions/{sid}/complete")
    return sid


def _play_sprout(client, fates_cut=True):
    mat = _real(client, "sprout_or_slop")
    s = client.post("/api/sessions", json={"game_id": "sprout_or_slop", "material_id": mat["id"]}, headers=H).json()
    sid = s["id"]
    if fates_cut:
        for cid in ["rc01", "rc02", "rc03", "rc04", "rc05"]:
            _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": "cut"}, target=cid)
    else:
        for cid in ["rc06", "rc07", "rc11", "rc12", "rc13"]:
            _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": "incubate"}, target=cid)
    client.post(f"/api/sessions/{sid}/complete")
    return sid


def test_empty_when_no_sessions(client):
    r = client.get("/api/operator/me", headers={"X-Player-Token": "nobody"})
    assert r.status_code == 200
    body = r.json()
    assert body["games_played"] == []
    assert "слишком мало материала" in body["verdict"] or "0 / 4" in body["coverage"]


def test_one_game_played(client):
    _play_false_click(client)
    body = client.get("/api/operator/me", headers=H).json()
    assert "false_click" in body["games_played"]
    assert body["per_game"]["false_click"]["dimensions"]["false_click_bias"] == "pseudo_depth"
    assert any("false_click" in s for s in body["explicit_dimensions"])


def test_cross_pattern_surfaces(client):
    """false_click pseudo_depth + sprout_or_slop oversaves should name the connection."""
    _play_false_click(client)
    _play_sprout(client, fates_cut=False)  # oversaves
    body = client.get("/api/operator/me", headers=H).json()
    assert "false_click" in body["games_played"]
    assert "sprout_or_slop" in body["games_played"]
    pattern_match = any("pseudo-depth" in p or "глубина-форма" in p for p in body["cross_patterns"])
    assert pattern_match, f"expected cross-pattern, got {body['cross_patterns']!r}"


def test_per_game_latest_session_wins(client):
    sid1 = _play_false_click(client)
    sid2 = _play_false_click(client)
    body = client.get("/api/operator/me", headers=H).json()
    assert body["per_game"]["false_click"]["session_id"] == sid2
    assert sid1 != sid2
