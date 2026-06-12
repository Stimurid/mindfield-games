"""Phase 2: real seeds load, complete full flow, profiles are game-specific,
replay directives are actionable, LLM mock stays non-assistant."""
import pytest

REAL_SEED_IDS = {
    "false_click": "real_false_click_001",
    "missing_operation": "real_missing_operation_001",
    "sprout_or_slop": "real_sprout_or_slop_001",
    "register_sapper": "real_register_sapper_001",
}


def _materials(client, game_id):
    return client.get(f"/api/materials?gameId={game_id}").json()


def _move(client, sid, action, round_id, payload=None, target=None):
    body = {"action": action, "round_id": round_id, "payload": payload or {}}
    if target:
        body["target_unit_id"] = target
    r = client.post(f"/api/sessions/{sid}/moves", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _llm(client, sid, role, ctx):
    r = client.post(f"/api/sessions/{sid}/llm-intervention", json={"role": role, "context": ctx})
    assert r.status_code == 200, r.text
    return r.json()


def _complete(client, sid):
    r = client.post(f"/api/sessions/{sid}/complete")
    assert r.status_code == 200, r.text
    return r.json()


def _new_session_on_real(client, game_id):
    mats = _materials(client, game_id)
    real = next((m for m in mats if m["namespace"] == "real"), None)
    assert real is not None, f"no real-namespace material for {game_id}"
    assert real["id"] == REAL_SEED_IDS[game_id]
    r = client.post("/api/sessions", json={"game_id": game_id, "material_id": real["id"]})
    assert r.status_code == 200
    return r.json()


def test_real_seeds_listed_with_namespace(client):
    for gid, expected in REAL_SEED_IDS.items():
        mats = _materials(client, gid)
        ids = {m["id"] for m in mats}
        assert expected in ids
        nms = {m["id"]: m["namespace"] for m in mats}
        assert nms[expected] == "real"


# -- Per-game real-seed flows ------------------------------------------------


def test_real_false_click_full_flow(client):
    s = _new_session_on_real(client, "false_click")
    sid = s["id"]
    # player selects 3 phrases — two pseudo_depth biases (so dominant)
    for uid, bias in [("r1", "pseudo_depth"), ("r11", "pseudo_depth"), ("r10", "dramatic_phrase")]:
        _move(client, sid, "select_unit", "select", {"hint_bias": bias}, target=uid)
        _move(client, sid, "prove_operation", "prove",
              {"operation": f"claims operation for {uid} — but it is a fabric phrase"}, target=uid)
        out = _llm(client, sid, "prosecutor", {"phrase": uid, "claimed_operation": "x"})["output"]
        assert "attacks" in out and "probe_question" in out
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target=uid)
    s2 = _complete(client, sid)
    dims = s2["trace_profile"]["dimensions"]
    assert dims["false_click_bias"] == "pseudo_depth"
    assert dims["operation_proof_strength"] in {"weak", "medium", "strong"}
    assert "verdict_distribution" in dims


def test_real_missing_operation_full_flow(client):
    s = _new_session_on_real(client, "missing_operation")
    sid = s["id"]
    sequence = [
        ("rg1", "subject", "reject"),
        ("rg2", "logical", "accept"),
        ("rg4", "resource", "repair"),
    ]
    fates = ["return_to_author", "keep_open", "restore"]
    for (gid, atype, presp), fate in zip(sequence, fates):
        _move(client, sid, "click_gap", "gap", {"gap_id": gid}, target=gid)
        _move(client, sid, "assign_absence_type", "gap", {"absence_type": atype}, target=gid)
        out = _llm(client, sid, "spackler", {"gap_context": "...", "absence_type": atype})["output"]
        assert "patch" in out and "risk" in out
        _move(client, sid, "respond_to_patch", "patch", {"response": presp}, target=gid)
        _move(client, sid, "assign_fate", "fate", {"fate": fate}, target=gid)
    s2 = _complete(client, sid)
    dims = s2["trace_profile"]["dimensions"]
    assert "absence_focus" in dims
    assert "absence_blindness" in dims
    assert "patch_susceptibility" in dims
    # Player named subject, logical, resource — blindness must be one of the unnamed
    assert dims["absence_blindness"] in {"criterion", "register", "promise", "ontology"}


def test_real_sprout_or_slop_full_flow(client):
    s = _new_session_on_real(client, "sprout_or_slop")
    sid = s["id"]
    placements = [
        ("rc01", "cut"), ("rc02", "cut"), ("rc03", "cut"), ("rc04", "cut"),
        ("rc06", "incubate"), ("rc07", "incubate"), ("rc11", "cut"),
        ("rc16", "no_name"), ("rc19", "require_proof"),
    ]
    for cid, fate in placements:
        _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": fate}, target=cid)
    out = _llm(client, sid, "sprout_advocate", {"card_text": "Слоп — это знак без операции", "fate": "cut"})["output"]
    assert "counterposition" in out and "pressure_question" in out
    _move(client, sid, "revise_fate", "revise", {"card_id": "rc11", "fate": "no_name", "criterion": "may carry register"})
    _move(client, sid, "set_incubation_test", "incubate", {"card_id": "rc07", "test": "use in 2 essays in 2 weeks"})
    s2 = _complete(client, sid)
    dims = s2["trace_profile"]["dimensions"]
    assert "selection_bias" in dims
    assert "sprout_tendency" in dims
    assert "slop_tolerance" in dims
    assert dims["selection_bias"] in {
        "overcuts", "oversaves", "proof_addict", "name_too_early", "no_name_avoidance", "balanced"
    }


def test_real_register_sapper_full_flow(client):
    s = _new_session_on_real(client, "register_sapper")
    sid = s["id"]
    _move(client, sid, "assign_phrase_action", "first_read",
          {"phrase_action": "hidden_request", "medium": "telegram"}, target="rv1")
    _move(client, sid, "compare_medium_shift", "shift",
          {"from": "telegram", "to": "email", "changed": "addressee, risk, право ответа"})
    out = _llm(client, sid, "literal_alien", {"phrase": "вы уверены?", "medium": "telegram"})["output"]
    assert "literal_reading" in out and "things_i_cannot_see" in out
    _move(client, sid, "repair_machine_reading", "blindness",
          {"missed": "hidden_request, pathos_reset"})
    _move(client, sid, "transfer_phrase", "transfer",
          {"target_medium": "voice", "new_phrase": "(пауза) точно?", "preserves_action": True})
    s2 = _complete(client, sid)
    dims = s2["trace_profile"]["dimensions"]
    assert "register_blindness" in dims
    assert "transfer_accuracy" in dims
    assert "action_distinction" in dims
    assert dims["transfer_accuracy"] == "action_transfer"


# -- Cross-cutting Phase 2 contracts ----------------------------------------


@pytest.mark.parametrize("game_id", list(REAL_SEED_IDS.keys()))
def test_replay_directive_is_actionable_sentence(client, game_id):
    """Replay directive must be a concrete sentence, not 'try harder'."""
    s = _new_session_on_real(client, game_id)
    sid = s["id"]
    # Minimal moves to drive a profile
    if game_id == "false_click":
        _move(client, sid, "select_unit", "select", {"hint_bias": "dramatic_phrase"}, target="r10")
        _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="r10")
    elif game_id == "missing_operation":
        _move(client, sid, "click_gap", "gap", {"gap_id": "rg2"}, target="rg2")
        _move(client, sid, "assign_absence_type", "gap", {"absence_type": "logical"}, target="rg2")
        _move(client, sid, "assign_fate", "fate", {"fate": "restore"}, target="rg2")
    elif game_id == "sprout_or_slop":
        for cid in ["rc01", "rc02", "rc03", "rc04", "rc05"]:
            _move(client, sid, "sort_card", "sort", {"card_id": cid, "fate": "cut"}, target=cid)
    else:  # register_sapper
        _move(client, sid, "assign_phrase_action", "first_read",
              {"phrase_action": "hidden_request", "medium": "telegram"}, target="rv1")
        _move(client, sid, "transfer_phrase", "transfer",
              {"target_medium": "voice", "new_phrase": "точно?", "preserves_action": True})

    s2 = _complete(client, sid)
    profile = s2["trace_profile"]
    directives = profile.get("replay_directives", [])
    assert directives, f"{game_id} produced no replay directive"
    for d in directives:
        assert isinstance(d, str) and len(d) >= 25, f"directive too short: {d!r}"
        lo = d.lower()
        for banned in ("try harder", "be more precise", "improve attention", "do better"):
            assert banned not in lo, f"directive must be concrete; got: {d!r}"
        # actionable directive should name a concrete next-round operation
        assert any(verb in lo for verb in (
            "increase", "hide", "stage", "return", "salt", "include", "force",
            "introduce", "rotate", "shift", "smuggle", "insert", "replace",
            "strip", "keep", "replay", "add",
        )), f"directive lacks concrete verb: {d!r}"


@pytest.mark.parametrize("role,ctx", [
    ("prosecutor", {"phrase": "это открывает новые горизонты", "claimed_operation": "opens scale shift"}),
    ("spackler", {"gap_context": "team will ensure...", "absence_type": "subject"}),
    ("sprout_advocate", {"card_text": "наш продукт меняет жизни", "fate": "cut"}),
    ("literal_alien", {"phrase": "вы уверены?", "medium": "telegram"}),
])
def test_llm_roles_remain_non_assistant(client, role, ctx):
    s = _new_session_on_real(client, "false_click")
    sid = s["id"]
    out = _llm(client, sid, role, ctx)["output"]
    flat = " ".join(str(v).lower() for k, v in out.items() if not k.startswith("_"))
    # Forbidden assistant-shaped keys
    for k in ("answer", "solution", "explanation_for_player", "helpful_tip"):
        assert k not in out, f"{role} should not return assistant-shaped key {k!r}"
    # Forbidden assistant phrasing
    for s_ in ("here is the answer", "the correct answer is", "let me help you", "you should think about"):
        assert s_ not in flat, f"{role} drifted into assistant register: {flat!r}"


def test_export_markdown_includes_replay_directive(client):
    s = _new_session_on_real(client, "false_click")
    sid = s["id"]
    _move(client, sid, "select_unit", "select", {"hint_bias": "pseudo_depth"}, target="r1")
    _move(client, sid, "assign_verdict", "verdict", {"verdict": "false_click"}, target="r1")
    _complete(client, sid)
    md = client.get(f"/api/sessions/{sid}/export?format=md").text
    assert "Replay directive" in md or "replay directive" in md.lower()
