"""Phase 14: triage 4200 — 9 fates per corpus card + organ extraction."""


def _first_card(client):
    rows = client.get("/api/library/entries?kind=source_card&limit=5").json()
    assert rows
    return rows[0]


def test_fates_list(client):
    fates = client.get("/api/triage/fates").json()
    keys = {f["fate"] for f in fates}
    assert keys == {
        "bury", "extract_organ", "keep_seed", "shrink_to_exercise",
        "lift_to_game_exercise", "cross", "breed", "defer_to_interface", "forbid",
    }


def test_assign_simple_fate(client):
    e = _first_card(client)
    r = client.post(f"/api/triage/entries/{e['id']}",
                    json={"fate": "bury", "note": "красивое название, нет глагола"},
                    headers={"X-Player-Token": "p14"})
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["fate"] == "bury"
    assert v["extracted_organ_id"] is None

    listed = client.get(f"/api/triage/entries/{e['id']}").json()
    assert any(x["id"] == v["id"] for x in listed)


def test_extract_organ_creates_new_bank_entry(client):
    e = _first_card(client)
    before = client.get("/api/configurator/organs?bank=action").json()
    before_count = len(before)

    r = client.post(f"/api/triage/entries/{e['id']}",
                    json={
                        "fate": "extract_organ",
                        "note": "достаём глагол",
                        "organ_bank": "action",
                        "organ_name": "удержать-внимание-на-пальцах",
                    },
                    headers={"X-Player-Token": "p14"})
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["fate"] == "extract_organ"
    assert v["extracted_organ_id"]

    after = client.get("/api/configurator/organs?bank=action").json()
    assert len(after) == before_count + 1
    new_organ = next(o for o in after if o["id"] == v["extracted_organ_id"])
    assert new_organ["source"] == "extracted"
    assert "удержать-внимание-на-пальцах" in new_organ["name"]


def test_extract_organ_rejects_missing_bank(client):
    e = _first_card(client)
    r = client.post(f"/api/triage/entries/{e['id']}",
                    json={"fate": "extract_organ", "organ_name": "something"},
                    headers={"X-Player-Token": "p14"})
    assert r.status_code == 400


def test_extract_organ_rejects_missing_name(client):
    e = _first_card(client)
    r = client.post(f"/api/triage/entries/{e['id']}",
                    json={"fate": "extract_organ", "organ_bank": "action"},
                    headers={"X-Player-Token": "p14"})
    assert r.status_code == 400


def test_unknown_fate_400(client):
    e = _first_card(client)
    r = client.post(f"/api/triage/entries/{e['id']}",
                    json={"fate": "promote"}, headers={"X-Player-Token": "p14"})
    assert r.status_code == 400


def test_queue_excludes_already_triaged(client):
    e = _first_card(client)
    before = client.get("/api/triage/queue?limit=10", headers={"X-Player-Token": "p14"}).json()
    assert any(c["id"] == e["id"] for c in before)
    client.post(f"/api/triage/entries/{e['id']}",
                json={"fate": "keep_seed"}, headers={"X-Player-Token": "p14"})
    after = client.get("/api/triage/queue?limit=10", headers={"X-Player-Token": "p14"}).json()
    assert not any(c["id"] == e["id"] for c in after)


def test_stats_reflect_assignments(client):
    e = _first_card(client)
    client.post(f"/api/triage/entries/{e['id']}",
                json={"fate": "bury"}, headers={"X-Player-Token": "p14-stat"})
    stats = client.get("/api/triage/stats?mine=true",
                       headers={"X-Player-Token": "p14-stat"}).json()
    bury_count = next(f["count"] for f in stats["by_fate"] if f["fate"] == "bury")
    assert bury_count >= 1
    assert stats["total_verdicts"] >= 1
