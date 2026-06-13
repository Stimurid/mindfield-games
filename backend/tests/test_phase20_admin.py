"""Phase 20: admin ontology — organ CRUD + read-only fates/cross-patterns."""


def _count_organs(client, source=None):
    rows = client.get("/api/admin/organs").json()
    if source:
        rows = [o for o in rows if o["source"] == source]
    return len(rows)


def test_admin_lists_all_organs(client):
    rows = client.get("/api/admin/organs").json()
    # 130 canonical + 0 admin-authored at startup
    assert len(rows) >= 130
    assert all(r["source"] == "canon_v0.1" for r in rows)


def test_admin_filter_organs_by_bank(client):
    rows = client.get("/api/admin/organs?bank=action").json()
    assert all(r["bank"] == "action" for r in rows)
    assert len(rows) == 20  # canonical action bank size


def test_admin_create_organ(client):
    before = _count_organs(client)
    r = client.post("/api/admin/organs",
                    json={"bank": "action", "name": "test-verb", "description": "a test"})
    assert r.status_code == 200, r.text
    o = r.json()
    assert o["bank"] == "action"
    assert o["source"] == "admin_authored"
    assert _count_organs(client) == before + 1


def test_admin_create_duplicate_rejected(client):
    r1 = client.post("/api/admin/organs",
                     json={"bank": "field", "name": "dup-test"})
    assert r1.status_code == 200
    r2 = client.post("/api/admin/organs",
                     json={"bank": "field", "name": "dup-test"})
    assert r2.status_code == 409


def test_admin_create_bad_bank(client):
    r = client.post("/api/admin/organs",
                    json={"bank": "fake_bank", "name": "x"})
    assert r.status_code == 400


def test_admin_update_admin_organ(client):
    o = client.post("/api/admin/organs",
                    json={"bank": "object", "name": "patch-target"}).json()
    r = client.patch(f"/api/admin/organs/{o['id']}",
                     json={"description": "now described"})
    assert r.status_code == 200
    assert r.json()["description"] == "now described"


def test_admin_cannot_modify_canonical(client):
    canon = next(o for o in client.get("/api/admin/organs").json()
                 if o["source"] == "canon_v0.1")
    r = client.patch(f"/api/admin/organs/{canon['id']}",
                     json={"name": "renamed"})
    assert r.status_code == 409
    r2 = client.delete(f"/api/admin/organs/{canon['id']}")
    assert r2.status_code == 409


def test_admin_delete_admin_organ(client):
    o = client.post("/api/admin/organs",
                    json={"bank": "trace", "name": "delete-me"}).json()
    r = client.delete(f"/api/admin/organs/{o['id']}")
    assert r.status_code == 200
    listed = client.get("/api/admin/organs").json()
    assert not any(x["id"] == o["id"] for x in listed)


def test_ontology_fates_readonly(client):
    r = client.get("/api/admin/ontology/fates").json()
    assert len(r["fates"]) == 9
    assert r["editable"] is False
    assert "triage.py" in r["source_file"]


def test_ontology_cross_patterns_readonly(client):
    r = client.get("/api/admin/ontology/cross-patterns").json()
    assert len(r["patterns"]) >= 5
    assert len(r["bias_meanings"]) >= 10
    assert r["editable"] is False
    assert "operator_profile.py" in r["source_file"]


def test_extracted_organs_visible_from_admin_list(client):
    """Phase 14 triage extractions and Phase 17 chimera-generated organs
    should appear in the admin list alongside canonical ones."""
    # Trigger a triage extraction
    card = client.get("/api/library/entries?kind=source_card&limit=1").json()[0]
    client.post(f"/api/triage/entries/{card['id']}",
                json={"fate": "extract_organ", "organ_bank": "action",
                      "organ_name": "test-extraction"},
                headers={"X-Player-Token": "p20"})
    rows = client.get("/api/admin/organs?bank=action").json()
    extracted = [r for r in rows if r["source"] == "extracted"]
    assert extracted
    assert any("test-extraction" in r["name"] for r in extracted)
