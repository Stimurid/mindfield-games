"""Phase 8: discussion organs on library entries — reuses the 4 existing roles."""


def _first_entry(client, kind="r_root"):
    rows = client.get(f"/api/library/entries?kind={kind}").json()
    assert rows, f"no entries of kind {kind}"
    return rows[0]


def test_summon_each_role_persists_comment(client):
    e = _first_entry(client, "r_root")
    for role in ("prosecutor", "spackler", "sprout_advocate", "literal_alien"):
        r = client.post(f"/api/library/entries/{e['id']}/summon",
                        json={"role": role}, headers={"X-Player-Token": "p8-tester"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["role"] == role
        assert isinstance(body["output"], dict) and body["output"]
        for forbidden in ("answer", "solution", "explanation_for_player", "helpful_tip"):
            assert forbidden not in body["output"]

    listed = client.get(f"/api/library/entries/{e['id']}/comments").json()
    roles_in_thread = {c["role"] for c in listed}
    assert roles_in_thread == {"prosecutor", "spackler", "sprout_advocate", "literal_alien"}


def test_summon_rejects_unknown_role(client):
    e = _first_entry(client)
    r = client.post(f"/api/library/entries/{e['id']}/summon",
                    json={"role": "concierge"}, headers={"X-Player-Token": "p8"})
    assert r.status_code == 400


def test_summon_rejects_missing_entry(client):
    r = client.post("/api/library/entries/does-not-exist/summon",
                    json={"role": "prosecutor"}, headers={"X-Player-Token": "p8"})
    assert r.status_code == 404


def test_comments_thread_orders_newest_first(client):
    e = _first_entry(client)
    headers = {"X-Player-Token": "p8-thread"}
    first = client.post(f"/api/library/entries/{e['id']}/summon",
                        json={"role": "prosecutor"}, headers=headers).json()
    second = client.post(f"/api/library/entries/{e['id']}/summon",
                         json={"role": "spackler"}, headers=headers).json()
    listed = client.get(f"/api/library/entries/{e['id']}/comments").json()
    assert listed[0]["id"] == second["id"]
    assert listed[1]["id"] == first["id"]
