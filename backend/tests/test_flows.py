"""Integration tests for each game's full loop."""


def _create_session(client, game_id):
    r = client.post("/api/sessions", json={"game_id": game_id})
    assert r.status_code == 200, r.text
    return r.json()


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    r = client.post(f"/api/sessions/{sid}/moves", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _llm(client, sid, role, context):
    r = client.post(
        f"/api/sessions/{sid}/llm-intervention",
        json={"role": role, "context": context},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _complete(client, sid):
    r = client.post(f"/api/sessions/{sid}/complete")
    assert r.status_code == 200, r.text
    return r.json()


def test_false_click_flow(client):
    s = _create_session(client, "false_click")
    sid = s["id"]
    _move(client, sid, "select_unit", "select", {"hint_bias": "dramatic_phrase"}, target="u4")
    _move(client, sid, "prove_operation", "prove", {"operation": "opens a contradiction between scale and ownership"}, target="u4")
    iv = _llm(client, sid, "prosecutor", {"phrase": "Это открывает фундаментально новые горизонты", "claimed_operation": "opens contradiction"})
    assert "attacks" in iv["output"]
    assert iv["output"]["_role"] == "prosecutor"
    _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="u4")
    s2 = _complete(client, sid)
    assert s2["status"] == "completed"
    assert s2["trace_profile"]["dimensions"]["false_click_bias"] == "dramatic_phrase"

    md = client.get(f"/api/sessions/{sid}/export?format=md").text
    assert "Operator profile" in md or "operator profile" in md.lower()


def test_missing_operation_flow(client):
    s = _create_session(client, "missing_operation")
    sid = s["id"]
    _move(client, sid, "click_gap", "gap", {"gap_id": "g2"}, target="g2")
    _move(client, sid, "assign_absence_type", "gap", {"absence_type": "subject"}, target="g2")
    iv = _llm(client, sid, "spackler", {"gap_context": "team will ensure...", "absence_type": "subject"})
    assert "patch" in iv["output"] and "risk" in iv["output"]
    _move(client, sid, "respond_to_patch", "patch", {"response": "reject", "reason": "no owner named"}, target="g2")
    _move(client, sid, "assign_fate", "fate", {"fate": "return_to_author"}, target="g2")
    s2 = _complete(client, sid)
    assert s2["trace_profile"]["dimensions"]["absence_focus"] == "subject"


def test_sprout_or_slop_flow(client):
    s = _create_session(client, "sprout_or_slop")
    sid = s["id"]
    for cid, fate in [("c01", "incubate"), ("c02", "cut"), ("c03", "incubate"), ("c06", "cut"), ("c10", "cut")]:
        _move(client, sid, "sort_card", "sort", {"fate": fate, "card_id": cid}, target=cid)
    iv = _llm(client, sid, "sprout_advocate", {"card_text": "Слоп — это знак без операции", "fate": "incubate"})
    assert "counterposition" in iv["output"]
    _move(client, sid, "revise_fate", "revise", {"card_id": "c02", "fate": "no_name", "criterion": "may carry register"})
    _move(client, sid, "set_incubation_test", "incubate", {"card_id": "c01", "test": "use it in 2 essays in 2 weeks"})
    s2 = _complete(client, sid)
    bias = s2["trace_profile"]["dimensions"]["selection_bias"]
    assert bias in {"overcuts", "oversaves", "balanced", "no_name_avoidance", "proof_addict"}


def test_register_sapper_flow(client):
    s = _create_session(client, "register_sapper")
    sid = s["id"]
    _move(client, sid, "assign_phrase_action", "first_read", {"phrase_action": "pathos_reset", "medium": "telegram"})
    _move(client, sid, "compare_medium_shift", "shift", {"from": "telegram", "to": "email", "changed": "addressee, risk"})
    iv = _llm(client, sid, "literal_alien", {"phrase": "ну ок, как скажешь", "medium": "telegram"})
    assert "literal_reading" in iv["output"]
    _move(client, sid, "repair_machine_reading", "blindness", {"missed": "pathos_reset, in_group_check"})
    _move(client, sid, "transfer_phrase", "transfer", {"target_medium": "voice", "new_phrase": "(пауза) хорошо.", "preserves_action": True})
    s2 = _complete(client, sid)
    assert s2["trace_profile"]["dimensions"]["transfer_accuracy"] == "action_transfer"


def test_export_json(client):
    s = _create_session(client, "false_click")
    sid = s["id"]
    _move(client, sid, "select_unit", "select", {"hint_bias": "pseudo_depth"}, target="u1")
    _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="u1")
    _complete(client, sid)
    j = client.get(f"/api/sessions/{sid}/export?format=json").json()
    assert j["session"]["status"] == "completed"
    assert len(j["moves"]) >= 2


def test_action_validation_against_genome(client):
    s = _create_session(client, "false_click")
    sid = s["id"]
    r = client.post(
        f"/api/sessions/{sid}/moves",
        json={"action": "sort_card", "round_id": "select", "payload": {}},
    )
    assert r.status_code == 400


def test_mock_llm_roles_are_role_shaped(client):
    s = _create_session(client, "false_click")
    sid = s["id"]
    out = _llm(client, sid, "prosecutor", {"phrase": "x", "claimed_operation": "y"})["output"]
    assert "attacks" in out and "probe_question" in out
    # Mock must NOT behave like a helpful assistant: no "answer" or "solution" keys
    assert "answer" not in out
    assert "solution" not in out
