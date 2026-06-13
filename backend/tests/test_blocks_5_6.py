"""Blocks 5+6: maturity_stage filter on the library + admin materials CRUD + debug session view."""


def test_maturity_backfilled_on_startup(client):
    # source_card defaults to 0, breed to 3.
    cards = client.get("/api/library/entries?kind=source_card&limit=5").json()
    assert all(c["maturity_stage"] == 0 for c in cards)
    breeds = client.get("/api/library/entries?kind=breed").json()
    assert all(b["maturity_stage"] == 3 for b in breeds)
    attractors = client.get("/api/library/entries?kind=attractor").json()
    assert all(a["maturity_stage"] == 4 for a in attractors)


def test_filter_by_exact_maturity(client):
    rows = client.get("/api/library/entries?maturity=0&limit=10").json()
    assert rows
    assert all(r["maturity_stage"] == 0 for r in rows)


def test_filter_by_maturity_range(client):
    rows = client.get("/api/library/entries?maturity_min=2&maturity_max=3&limit=200").json()
    assert rows
    assert all(2 <= r["maturity_stage"] <= 3 for r in rows)


def test_patch_maturity(client):
    breeds = client.get("/api/library/entries?kind=breed").json()
    e = breeds[0]
    r = client.patch(f"/api/library/entries/{e['id']}/maturity", json={"maturity_stage": 5})
    assert r.status_code == 200
    refreshed = client.get(f"/api/library/entries/{e['id']}").json()
    assert refreshed["maturity_stage"] == 5


def test_patch_maturity_rejects_out_of_range(client):
    breeds = client.get("/api/library/entries?kind=breed").json()
    e = breeds[0]
    r = client.patch(f"/api/library/entries/{e['id']}/maturity", json={"maturity_stage": 9})
    assert r.status_code == 400


# ── Admin materials CRUD ─────────────────────────────────────────────────────

def test_admin_lists_all_materials(client):
    rows = client.get("/api/admin/materials").json()
    assert len(rows) >= 12  # at least one per shipped genre


def test_admin_create_update_delete(client):
    payload = {
        "game_id": "false_click",
        "title": "[admin-test] handmade material",
        "namespace": "demo",
        "payload": {"type": "clickable_text_units", "intro": "x", "units": []},
    }
    r = client.post("/api/admin/materials", json=payload)
    assert r.status_code == 200, r.text
    mid = r.json()["id"]

    r2 = client.put(f"/api/admin/materials/{mid}",
                    json={"title": "[admin-test] renamed"})
    assert r2.status_code == 200
    assert r2.json()["title"] == "[admin-test] renamed"

    r3 = client.delete(f"/api/admin/materials/{mid}")
    assert r3.status_code == 200

    r4 = client.get(f"/api/materials/{mid}")
    assert r4.status_code == 404


def test_debug_session_view_is_existing_session_endpoint(client):
    """The 'debug session' page is just a frontend wrapper around the
    already-existing GET /api/sessions/{id}, so the data surface is unchanged.
    This test just confirms the underlying API still returns the full shape."""
    mats = client.get("/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions",
                    json={"game_id": "false_click", "material_id": real["id"]}).json()
    full = client.get(f"/api/sessions/{s['id']}").json()
    assert full["id"] == s["id"]
    assert "moves" in full
    assert "interventions" in full
    assert "trace_profile" in full
