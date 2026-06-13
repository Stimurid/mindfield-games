"""Phase 11: micro-cards inside top-level entries (second-pass parse).

Adds two new kinds: micro_game (24×3 attractor exercises) and micro_aspect
(label:value lines inside breeds / R-roots). Each is linked back to its
top-level parent via CorpusLink, so the library reader surfaces them as
children of the parent entry.
"""


def test_micro_games_present(client):
    rows = client.get("/api/library/entries?kind=micro_game").json()
    # 24 attractors v0.2 × 3 (малое / игра / большой)
    assert len(rows) == 72
    triples = {r["title"].split(":")[0] for r in rows}
    assert triples == {"малое", "игра", "большой"}


def test_micro_aspects_present(client):
    rows = client.get("/api/library/entries?kind=micro_aspect").json()
    assert len(rows) >= 100
    # All 12 breeds should each have several aspect entries.
    parents = {r["code"].rsplit("_", 1)[0] for r in rows if r["code"].startswith("mc_breed_")}
    assert len(parents) == 12


def test_micro_card_links_to_parent(client):
    # Pick a breed and verify it has child links to micro-aspects.
    breeds = client.get("/api/library/entries?kind=breed").json()
    e = client.get(f"/api/library/entries/{breeds[0]['id']}").json()
    children_kinds = {c["relation"] for c in e["children"]}
    assert "contains" in children_kinds
    # The child list should include at least the breed's aspect rows.
    assert len(e["children"]) >= 4
    for child in e["children"]:
        assert child["code"].startswith("mc_breed_")


def test_micro_card_search_finds_known_phrase(client):
    res = client.get("/api/library/search?q=Семантический+сапёр").json()
    assert any("Семантический сапёр" in r["title"] or "Семантический сапёр" in r.get("snippet", "")
               for r in res)
