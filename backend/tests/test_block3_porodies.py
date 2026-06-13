"""Block 3: 7 new canonical породы — full flow through each."""
import pytest


SEVEN = [
    ("prompt_tackle",        "real_prompt_tackle_001"),
    ("assistant_as_foreign", "real_assistant_as_foreign_001"),
    ("agent_passport",       "real_agent_passport_001"),
    ("ontology_customs",     "real_ontology_customs_001"),
    ("game_under_capture",   "real_game_under_capture_001"),
    ("false_consensus",      "real_false_consensus_001"),
    ("burn_cognitor",        "real_burn_cognitor_001"),
]


@pytest.mark.parametrize("game_id,seed_id", SEVEN)
def test_genome_loads(client, game_id, seed_id):
    g = client.get(f"/api/games/{game_id}").json()
    assert g["id"] == game_id
    assert g["field_type"] in {"clickable_text_units", "card_sorting", "medium_shift_phrase"}


@pytest.mark.parametrize("game_id,seed_id", SEVEN)
def test_real_seed_loads(client, game_id, seed_id):
    mats = client.get(f"/api/materials?gameId={game_id}").json()
    real = next((m for m in mats if m["namespace"] == "real"), None)
    assert real is not None, f"{game_id} missing real seed"
    assert real["id"] == seed_id


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    return client.post(f"/api/sessions/{sid}/moves", json=body).json()


def _new(client, game_id):
    mats = client.get(f"/api/materials?gameId={game_id}").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions", json={"game_id": game_id, "material_id": real["id"]},
                    headers={"X-Player-Token": "b3"}).json()
    return s["id"]


def test_prompt_tackle_full_flow(client):
    sid = _new(client, "prompt_tackle")
    for uid in ["pt1", "pt4", "pt6"]:
        _move(client, sid, "select_unit", "select", {"hint_bias": "scaffold"}, target=uid)
        _move(client, sid, "prove_operation", "prove", {"operation": "я могу написать это сам"}, target=uid)
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "removable"}, target=uid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    dims = final["trace_profile"]["dimensions"]
    assert "scaffold_dependency" in dims


def test_assistant_as_foreign_full_flow(client):
    sid = _new(client, "assistant_as_foreign")
    for cid, fate in [("af01", "moral_smoothing"), ("af04", "literal"), ("af07", "lost_register"), ("af11", "smooth"), ("af18", "smooth")]:
        _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": fate}, target=cid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    dims = final["trace_profile"]["dimensions"]
    assert "alien_blindness" in dims
    assert "fate_distribution" in dims


def test_agent_passport_full_flow(client):
    sid = _new(client, "agent_passport")
    for cid, fate in [("ap02", "confirmed_agent"), ("ap03", "decorative_mask"), ("ap05", "fail"),
                      ("ap08", "confirmed_agent"), ("ap10", "decorative_mask"), ("ap14", "confirmed_agent")]:
        _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": fate}, target=cid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    assert "agency_detection_bias" in final["trace_profile"]["dimensions"]


def test_ontology_customs_full_flow(client):
    sid = _new(client, "ontology_customs")
    _move(client, sid, "assign_phrase_action", "declare",
          {"phrase_action": "preserved", "medium": "psychology"}, target="oc1")
    _move(client, sid, "assign_phrase_action", "declare",
          {"phrase_action": "smuggled", "medium": "engineering"}, target="oc2")
    _move(client, sid, "compare_medium_shift", "declare",
          {"from": "psychology", "to": "engineering", "changed": "ЗБР стало HR-метрикой"})
    _move(client, sid, "transfer_phrase", "transfer",
          {"target_medium": "music", "new_phrase": "ансамблевая репетиция", "preserves_action": True})
    final = client.post(f"/api/sessions/{sid}/complete").json()
    dims = final["trace_profile"]["dimensions"]
    assert dims["transfer_accuracy"] == "action_transfer"
    assert "smuggling_blindness" in dims


def test_game_under_capture_full_flow(client):
    sid = _new(client, "game_under_capture")
    for uid in ["gc2", "gc4", "gc9"]:
        _move(client, sid, "select_unit", "select", {"hint_bias": "bearing"}, target=uid)
        _move(client, sid, "prove_operation", "prove",
              {"operation": "критическое решение для релиз-окна"}, target=uid)
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "held_operation"}, target=uid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    assert final["trace_profile"]["dimensions"]["first_dropped_axis"] in {"none", "field", "proof", "subject", "register"}


def test_false_consensus_full_flow(client):
    sid = _new(client, "false_consensus")
    for cid, fate in [("fc01", "text_only"), ("fc02", "real_action"), ("fc04", "synchrony_only"),
                      ("fc07", "silent_dissent"), ("fc08", "real_action")]:
        _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": fate}, target=cid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    assert "consensus_bias" in final["trace_profile"]["dimensions"]


def test_burn_cognitor_full_flow(client):
    sid = _new(client, "burn_cognitor")
    for cid, fate in [("bc01", "transferred"), ("bc03", "idol_kept"), ("bc06", "burned"),
                      ("bc09", "organ_extracted"), ("bc12", "transferred")]:
        _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": fate}, target=cid)
    final = client.post(f"/api/sessions/{sid}/complete").json()
    assert "idol_attachment" in final["trace_profile"]["dimensions"]


@pytest.mark.parametrize("game_id,_seed", SEVEN)
def test_replay_loop_works_for_new_porodies(client, game_id, _seed):
    """Each new порода must round-trip through complete → replay → playable session."""
    sid = _new(client, game_id)
    # Drive a minimal completion path.
    if game_id == "prompt_tackle":
        _move(client, sid, "select_unit", "select", {"hint_bias": "scaffold"}, target="pt1")
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "removable"}, target="pt1")
    elif game_id == "game_under_capture":
        _move(client, sid, "select_unit", "select", {"hint_bias": "bearing"}, target="gc2")
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "held_operation"}, target="gc2")
    elif game_id == "ontology_customs":
        _move(client, sid, "assign_phrase_action", "declare",
              {"phrase_action": "preserved", "medium": "psychology"}, target="oc1")
        _move(client, sid, "transfer_phrase", "transfer",
              {"target_medium": "music", "new_phrase": "ансамбль", "preserves_action": True})
    else:  # card_sorting породы
        # Pick a card id that exists across the seeds.
        first_card = client.get(f"/api/materials?gameId={game_id}").json()
        real_id = next(m for m in first_card if m["namespace"] == "real")["id"]
        mat = client.get(f"/api/materials/{real_id}").json()
        first = mat["payload"]["cards"][0]
        first_fate = mat["payload"]["zones"][0]["id"]
        _move(client, sid, "sort_card", "sort", {"card_id": first["id"], "fate": first_fate}, target=first["id"])

    client.post(f"/api/sessions/{sid}/complete")
    r = client.post(f"/api/sessions/{sid}/replay", json={})
    assert r.status_code == 200, r.text
    new = client.get(f"/api/materials/{r.json()['new_material_id']}").json()
    assert new["payload"]["type"]
