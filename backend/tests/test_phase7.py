"""Phase 7: Library — corpus ingest, sections, entries, FTS5 search."""


def test_sections_have_expected_kinds(client):
    secs = client.get("/api/library/sections").json()
    kinds = {s["kind"] for s in secs}
    # The corpus has at least these top-level shapes after ingest.
    assert "attractor" in kinds
    assert "r_root" in kinds
    assert "breed" in kinds
    assert "phase_doc" in kinds


def test_attractors_present(client):
    rows = client.get("/api/library/entries?kind=attractor").json()
    codes = {r["code"] for r in rows}
    # v0.2 canonical map should ship 24 attractors
    v02 = [r for r in rows if r["source_pass"] == "v0.2"]
    assert len(v02) == 24, f"expected 24 v0.2 attractors, got {len(v02)}"
    assert "A01_v0.2" in codes


def test_r_roots_present(client):
    rows = client.get("/api/library/entries?kind=r_root").json()
    assert len(rows) == 12
    assert {r["code"] for r in rows} == {f"R{i:02d}" for i in range(1, 13)}


def test_breeds_present(client):
    rows = client.get("/api/library/entries?kind=breed").json()
    assert len(rows) == 12
    titles = [r["title"] for r in rows]
    assert "Ложный клик" in titles
    assert "Росток или слоп" in titles


def test_entry_detail_has_body_and_lineage_shape(client):
    rows = client.get("/api/library/entries?kind=r_root").json()
    e = client.get(f"/api/library/entries/{rows[0]['id']}").json()
    assert e["body_md"] and len(e["body_md"]) > 100
    assert "parents" in e and "children" in e


def test_phase_docs_ingested(client):
    rows = client.get("/api/library/entries?kind=phase_doc").json()
    # All docs/*.md except spec.md
    titles = " ".join(r["title"].lower() for r in rows)
    assert "playtest" in titles or "acceptance" in titles or "phase" in titles


def test_fts_search_finds_known_term(client):
    res = client.get("/api/library/search?q=ложный+клик").json()
    assert res, "search returned nothing"
    titles = " ".join(r["title"].lower() for r in res)
    assert "ложный" in titles or "false" in titles


def test_fts_search_filters_by_kind(client):
    res = client.get("/api/library/search?q=поле&kind=r_root").json()
    for r in res:
        assert r["kind"] == "r_root"
