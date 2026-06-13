"""Phase 19: i18n cache. Mock translator role tags the source string
deterministically, so we can assert (a) translation happens on first read
and (b) the second read of the same string does NOT hit the LLM (cache reuse)."""
def _count_translations() -> int:
    # Import inside the function so the conftest's monkeypatched MINDFIELD_DB
    # is honored (top-level imports would bind to the pre-fixture engine).
    from sqlalchemy import func
    from app.database import SessionLocal
    from app.models import Translation
    db = SessionLocal()
    try:
        return db.query(func.count(Translation.id)).scalar() or 0
    finally:
        db.close()


def test_default_lang_is_ru_no_op(client):
    g = client.get("/api/games/false_click").json()
    assert "Ложный клик" in g["title"]
    g2 = client.get("/api/games/false_click?lang=ru").json()
    assert g == g2


def test_games_list_translation_caches(client):
    before = _count_translations()
    r1 = client.get("/api/games?lang=en").json()
    # Mock translator prefixes [en] — verify it was applied to all title strings.
    for g in r1:
        assert g["title"].startswith("[en] "), f"untranslated: {g['title']!r}"

    after_first = _count_translations()
    assert after_first > before, "first call should have created Translation rows"

    # Second call: zero new rows, identical output.
    r2 = client.get("/api/games?lang=en").json()
    after_second = _count_translations()
    assert after_second == after_first, "cached call must not write new rows"
    assert r1 == r2


def test_game_detail_translates_rounds_and_function(client):
    g = client.get("/api/games/false_click?lang=en").json()
    assert g["title"].startswith("[en] ")
    assert g["function"].startswith("[en] ")
    for r in g["rounds"]:
        assert r["title"].startswith("[en] ")
        assert r["instruction"].startswith("[en] ")
    # Identifier-shaped fields stay untranslated.
    assert g["field_type"] == "clickable_text_units"
    assert all(":" not in v and not v.startswith("[en]")
               for v in g["verdicts"])


def test_library_sections_translate_label(client):
    secs = client.get("/api/library/sections?lang=en").json()
    assert all(s["label"].startswith("[en] ") for s in secs)
    assert all(s["count"] > 0 for s in secs)


def test_library_entry_detail_translates_title_and_body(client):
    rows = client.get("/api/library/entries?kind=r_root&lang=en").json()
    assert rows
    one = rows[0]
    assert one["title"].startswith("[en] ")
    detail = client.get(f"/api/library/entries/{one['id']}?lang=en").json()
    assert detail["title"].startswith("[en] ")
    assert detail["body_md"].startswith("[en] ")


def test_material_payload_deep_translation(client):
    mats = client.get("/api/materials?gameId=false_click&lang=en").json()
    assert all(m["title"].startswith("[en] ") for m in mats)
    real = next(m for m in mats if m["namespace"] == "real")
    full = client.get(f"/api/materials/{real['id']}?lang=en").json()
    p = full["payload"]
    assert p["intro"].startswith("[en] ")
    for u in p["units"]:
        assert u["text"].startswith("[en] "), f"untranslated unit text: {u}"


def test_configurator_banks_and_organs_translate(client):
    banks = client.get("/api/configurator/banks?lang=en").json()
    for b in banks:
        assert b["label"].startswith("[en] ")
        # hint can be empty for some banks, but if present must translate
        if b["hint"]:
            assert b["hint"].startswith("[en] ")
    organs = client.get("/api/configurator/organs?bank=action&lang=en").json()
    for o in organs:
        assert o["name"].startswith("[en] ")


def test_triage_fates_translate(client):
    fates = client.get("/api/triage/fates?lang=en").json()
    assert all(f["label"].startswith("[en] ") for f in fates)


def test_identifier_strings_skip_translation(client):
    """Pure identifier-shaped strings ('false_click', 'pseudo_depth') must NOT
    be sent through the LLM — they pass through as-is."""
    # /api/games returns id which is identifier-shaped.
    games = client.get("/api/games?lang=en").json()
    for g in games:
        # id is bare identifier — preserved verbatim
        assert g["id"] == g["id"].lower().replace(" ", "_")
        assert not g["id"].startswith("[en]")