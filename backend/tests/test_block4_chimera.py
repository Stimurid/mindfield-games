"""Block 4: chimera matrix cell → LLM-generated draft genome."""


def _first_chimera(client):
    rows = client.get("/api/library/entries?kind=chimera").json()
    assert rows
    return rows[0]


def test_chimera_generates_draft(client):
    e = _first_chimera(client)
    r = client.post(f"/api/library/entries/{e['id']}/generate-chimera-draft",
                    json={}, headers={"X-Player-Token": "b4"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["draft_id"]
    assert body["source_chimera_id"] == e["id"]
    assert body["selected_organs"]

    # The draft must show up in the configurator under the same token.
    drafts = client.get("/api/configurator/drafts?mine=true",
                        headers={"X-Player-Token": "b4"}).json()
    assert any(d["id"] == body["draft_id"] for d in drafts)


def test_chimera_draft_has_resolved_organ_ids(client):
    e = _first_chimera(client)
    body = client.post(f"/api/library/entries/{e['id']}/generate-chimera-draft",
                       json={}, headers={"X-Player-Token": "b4"}).json()
    organ_ids = [oid for ids in body["selected_organs"].values() for oid in ids]
    assert organ_ids
    all_organs = client.get("/api/configurator/organs").json()
    by_id = {o["id"]: o for o in all_organs}
    for oid in organ_ids:
        assert oid in by_id
        # No degradation organ may slip through.
        assert by_id[oid]["bank"] != "degradation"


def test_chimera_draft_runs_through_weaver(client):
    """The generated draft must also pass the playability_critic loop."""
    e = _first_chimera(client)
    body = client.post(f"/api/library/entries/{e['id']}/generate-chimera-draft",
                       json={}, headers={"X-Player-Token": "b4"}).json()
    did = body["draft_id"]
    v = client.post(f"/api/configurator/drafts/{did}/weaver", json={}).json()["verdict"]
    # Mock chimera weaver fills field+action+crisis+trace from canon, so it should be playable.
    assert v["playable_verdict"] == "playable"


def test_chimera_requires_chimera_kind(client):
    other = client.get("/api/library/entries?kind=r_root").json()[0]
    r = client.post(f"/api/library/entries/{other['id']}/generate-chimera-draft",
                    json={}, headers={"X-Player-Token": "b4"})
    assert r.status_code == 400


def test_chimera_creates_new_organs_when_names_unknown(client):
    """Mock weaver echoes existing names; verify the resolver matches them rather
    than creating dupes. Counts before / after must match for the canon set."""
    before = client.get("/api/configurator/organs?bank=field").json()
    e = _first_chimera(client)
    client.post(f"/api/library/entries/{e['id']}/generate-chimera-draft",
                json={}, headers={"X-Player-Token": "b4-match"})
    after = client.get("/api/configurator/organs?bank=field").json()
    # Mock returns canon name → no new organ created in field bank.
    assert len(after) == len(before)
