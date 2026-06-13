"""Phase 12: the raw 4200 cards from docs/raw_corpus_4200.md."""


def test_raw_cards_count(client):
    rows = client.get("/api/library/entries?kind=source_card&limit=5000").json()
    assert len(rows) == 4200


def test_raw_sections_present(client):
    rows = client.get("/api/library/entries?kind=source_section").json()
    assert len(rows) >= 150
    # First Roman-numeral section is always I.
    assert any(r["code"] == "src_section_I" for r in rows)


def test_first_and_last_cards_are_correct(client):
    e1 = client.get("/api/library/entries?kind=source_card&limit=5000").json()
    by_code = {r["code"]: r for r in e1}
    first = by_code.get("src_card_0001")
    last = by_code.get("src_card_4200")
    assert first and "Пальцы" in first["title"]
    assert last and "останавливает-список" in last["title"]


def test_raw_card_links_to_section(client):
    # src_card_0001 lives under section I.
    rows = client.get("/api/library/entries?kind=source_card&limit=5000").json()
    by_code = {r["code"]: r for r in rows}
    card = client.get(f"/api/library/entries/{by_code['src_card_0001']['id']}").json()
    parent_codes = {p["code"] for p in card["parents"]}
    assert "src_section_I" in parent_codes


def test_raw_card_search_finds_known_name(client):
    res = client.get("/api/library/search?q=Хромая+обезьяна").json()
    titles = " ".join(r["title"] for r in res)
    assert "Хромая обезьяна" in titles


def test_section_membership_via_FTS_no_overload(client):
    """4200 + 165 + previous ~360 entries — search must still be fast and accurate."""
    res = client.get("/api/library/search?q=деконцентрация&kind=source_card").json()
    assert res
    for r in res:
        assert r["kind"] == "source_card"
