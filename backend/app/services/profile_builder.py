"""Qualitative Operator Profile — no numeric scores. Counts collapsed into qualitative tags."""
from collections import Counter
from typing import Any


def _verdicts(moves: list[dict]) -> Counter:
    c = Counter()
    for m in moves:
        if m["action"] == "assign_verdict":
            v = m["payload"].get("verdict")
            if v:
                c[v] += 1
    return c


# --- replay directive vocabulary -------------------------------------------------
# A directive is a sentence-shaped instruction for the next round mutator.
# It must name a concrete operation on the next material, not "try harder".

_FALSE_CLICK_DIRECTIVES = {
    "dramatic_phrase":      "next round: increase dramatic intensifier nodes — these pulled you off the operation",
    "abstract_word":        "next round: pack more high-status abstract nouns without verbs — you mistook status for action",
    "familiar_topic":       "next round: stage the bearing node in a topic you don't recognise — your familiarity bias picked up the wrong unit",
    "pseudo_depth":         "next round: increase pseudo-depth phrases that imply more than they commit to — you fell for this shape",
    "conclusion_like_phrase":"next round: insert more 'таким образом'/'thus' decoys — you clicked the conclusion-shape, not the operation",
    "mixed":                "next round: rotate the slop type the player kept missing across recent sessions",
}

_MISSING_OPERATION_DIRECTIVES = {
    "logical":  "next round: hide a different absence type — you already track logical leaps; suppress a subject or criterion next",
    "subject":  "next round: keep hiding the acting subject in passive aggregates — you correctly surface this, push harder by adding a fake owner",
    "resource": "next round: replace the missing resource with an abstract 'will be allocated' phrase — push your resource-radar",
    "register": "next round: shift register mid-paragraph without flagging it",
    "archive":  "next round: insert a fake citation gap ('as is well known…')",
    "promise":  "next round: add a promise without owner or due date — verify whether you detect it without subject prompting",
    "ontology": "next round: smuggle a scale/level switch and see if you surface it as ontology rather than logic",
    "criterion":"next round: hide the success criterion behind a smooth bridge",
}

_SPROUT_OR_SLOP_DIRECTIVES = {
    "overcuts":         "next round: return three previously cut cards as confirmed sprouts — you cut too hard",
    "oversaves":        "next round: salt the deck with dead-beauty phrases that match what you saved — you preserve slop that sounds like sprout",
    "proof_addict":     "next round: include sprouts that lose their seed if proof is demanded too early",
    "name_too_early":   "next round: include borderline mutants where naming kills the sprout",
    "no_name_avoidance":"next round: force at least two cards into a 'no_name' allowance you avoid using",
    "balanced":         "next round: introduce a harder borderline tier — half slop, half sprout, indistinguishable by surface",
}

_PROMISE_COURT_DIRECTIVES = {
    "missed_no_owner":   "next round: stage more passive 'будет сделано' / 'мы займёмся' — you accepted owner-less promises",
    "missed_no_deadline":"next round: hide deadlines behind soft adverbs ('в обозримой перспективе') — you let temporal vagueness pass",
    "missed_no_criterion":"next round: replace concrete criteria with mood words ('значительно улучшим') — you accepted unfalsifiable wins",
    "missed_no_fallback":"next round: drop the refusal/escape clause — you accepted promises with no exit path",
    "court_overload":    "next round: include several COMPLETE promises (owner+deadline+criterion+fallback) — you send too much to the court",
    "completeness_strict":"next round: include borderline promises with one strong field and three weak — you reject too quickly",
    "balanced":          "next round: stage a 'we' / collective-subject promise — verify you still surface the missing owner",
}


_REGISTER_SAPPER_DIRECTIVES = {
    "literalizes_joke":       "next round: add a phrase that only works as a joke — verify you no longer flatten it into a command",
    "misses_local_code":      "next round: stage the phrase in an in-group chat with hidden shared past — verify you mark in_group_check",
    "confuses_rudeness_with_attack":"next round: include a pathos_reset grubness that holds a thread together",
    "misses_alibi":           "next round: replay the same phrase as a covert alibi — verify you stop treating it as a refusal",
    "loses_address":          "next round: keep the words identical but rotate the addressee — verify you re-read the action",
    "tone_instead_action":    "next round: strip tone signals entirely; force you to name the action without prosody cues",
}


def build_false_click_profile(moves: list[dict], interventions: list[dict]) -> dict:
    verdicts = _verdicts(moves)
    proofs = [m["payload"].get("operation") for m in moves if m["action"] == "prove_operation"]
    proofs = [p for p in proofs if p]
    bias_pool = []
    for m in moves:
        if m["action"] == "select_unit":
            tag = m["payload"].get("hint_bias")
            if tag:
                bias_pool.append(tag)
    bias = Counter(bias_pool).most_common(1)
    bias_label = bias[0][0] if bias else "mixed"
    proof_strength = (
        "weak" if not proofs or all(len(p) < 20 for p in proofs)
        else "strong" if all(len(p) >= 40 for p in proofs)
        else "medium"
    )
    target = bias_label if bias_label in _FALSE_CLICK_DIRECTIVES else "pseudo_depth"
    return {
        "dimensions": {
            "false_click_bias": bias_label,
            "operation_proof_strength": proof_strength,
            "verdict_distribution": dict(verdicts),
        },
        "replay_targets": [target],
        "replay_directives": [_FALSE_CLICK_DIRECTIVES[target]],
        "markdown_summary": (
            f"## False Click profile\n"
            f"- Dominant click-bias: **{bias_label}**\n"
            f"- Proof strength on bearing nodes: **{proof_strength}**\n"
            f"- Verdict mix: {dict(verdicts)}\n"
            f"- Replay directive: {_FALSE_CLICK_DIRECTIVES[target]}\n"
        ),
    }


def build_missing_operation_profile(moves: list[dict], interventions: list[dict]) -> dict:
    absences = Counter()
    fates = Counter()
    patch_responses = Counter()
    for m in moves:
        if m["action"] == "assign_absence_type":
            absences[m["payload"].get("absence_type", "unknown")] += 1
        if m["action"] == "assign_fate":
            fates[m["payload"].get("fate", "unknown")] += 1
        if m["action"] == "respond_to_patch":
            patch_responses[m["payload"].get("response", "unknown")] += 1
    most_named = absences.most_common(1)
    most_named_label = most_named[0][0] if most_named else "subject"
    # absence_blindness: what the player keeps missing — the OPPOSITE of what they keep naming.
    # If they over-name "logical", they likely miss "subject"/"resource"/"criterion".
    blindness_candidates = ["subject", "resource", "criterion", "register", "promise", "ontology"]
    blindness = next((c for c in blindness_candidates if c != most_named_label and absences.get(c, 0) == 0),
                     "criterion" if most_named_label != "criterion" else "subject")
    if patch_responses.get("accept", 0) > patch_responses.get("reject", 0):
        susceptibility = "accepts_smooth_bridge"
    elif patch_responses.get("reject", 0) > patch_responses.get("accept", 0) + patch_responses.get("repair", 0):
        susceptibility = "over_rejects"
    else:
        susceptibility = "resists_patch"
    target = blindness if blindness in _MISSING_OPERATION_DIRECTIVES else "criterion"
    return {
        "dimensions": {
            "absence_focus": most_named_label,
            "absence_blindness": blindness,
            "patch_susceptibility": susceptibility,
            "absence_distribution": dict(absences),
            "fate_distribution": dict(fates),
        },
        "replay_targets": [target],
        "replay_directives": [_MISSING_OPERATION_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Missing Operation profile\n"
            f"- Most named absence: **{most_named_label}**\n"
            f"- Likely blindness (never named): **{blindness}**\n"
            f"- Patch behaviour: **{susceptibility}**\n"
            f"- Fates: {dict(fates)}\n"
            f"- Replay directive: {_MISSING_OPERATION_DIRECTIVES[target]}\n"
        ),
    }


def build_sprout_or_slop_profile(moves: list[dict], interventions: list[dict]) -> dict:
    fates = Counter()
    revisions = 0
    incubation_tests = 0
    for m in moves:
        if m["action"] == "sort_card":
            fates[m["payload"].get("fate", "unknown")] += 1
        if m["action"] == "revise_fate":
            revisions += 1
        if m["action"] == "set_incubation_test":
            incubation_tests += 1
    total = sum(fates.values()) or 1
    cut_ratio = fates.get("cut", 0) / total
    save_ratio = (fates.get("incubate", 0) + fates.get("no_name", 0)) / total
    if cut_ratio > 0.5:
        bias = "overcuts"
    elif save_ratio > 0.6:
        bias = "oversaves"
    elif fates.get("require_proof", 0) / total > 0.4:
        bias = "proof_addict"
    elif fates.get("no_name", 0) == 0:
        bias = "no_name_avoidance"
    else:
        bias = "balanced"
    sprout_tendency = "high" if fates.get("incubate", 0) >= 3 else "medium" if fates.get("incubate", 0) >= 1 else "low"
    slop_tolerance = "low" if cut_ratio >= 0.4 else "medium" if cut_ratio >= 0.2 else "high"
    return {
        "dimensions": {
            "selection_bias": bias,
            "sprout_tendency": sprout_tendency,
            "slop_tolerance": slop_tolerance,
            "revisions": revisions,
            "incubation_tests_set": incubation_tests,
            "fate_distribution": dict(fates),
        },
        "replay_targets": [bias],
        "replay_directives": [_SPROUT_OR_SLOP_DIRECTIVES[bias]],
        "markdown_summary": (
            f"## Sprout or Slop profile\n"
            f"- Selection bias: **{bias}**\n"
            f"- Sprout tendency: **{sprout_tendency}** · Slop tolerance: **{slop_tolerance}**\n"
            f"- Revisions after advocate pressure: {revisions}\n"
            f"- Incubation tests set: {incubation_tests}\n"
            f"- Fates: {dict(fates)}\n"
            f"- Replay directive: {_SPROUT_OR_SLOP_DIRECTIVES[bias]}\n"
        ),
    }


def build_register_sapper_profile(moves: list[dict], interventions: list[dict]) -> dict:
    actions = Counter()
    repairs = 0
    transfers = 0
    transfer_kind = "content_transfer"
    for m in moves:
        if m["action"] == "assign_phrase_action":
            actions[m["payload"].get("phrase_action", "unknown")] += 1
        if m["action"] == "repair_machine_reading":
            repairs += 1
        if m["action"] == "transfer_phrase":
            transfers += 1
            if m["payload"].get("preserves_action"):
                transfer_kind = "action_transfer"
    if repairs == 0:
        blindness = "tone_instead_action"
    elif "joke" not in actions and any(a in actions for a in ("threat", "command", "refusal")):
        blindness = "literalizes_joke"
    elif "alibi" not in actions and "hidden_request" not in actions:
        blindness = "misses_alibi"
    else:
        blindness = "loses_address"
    awareness = "strong" if repairs >= 2 and transfer_kind == "action_transfer" else (
        "weak" if repairs == 0 else "medium"
    )
    target = blindness if blindness in _REGISTER_SAPPER_DIRECTIVES else "tone_instead_action"
    return {
        "dimensions": {
            "register_blindness": blindness,
            "medium_awareness": awareness,
            "transfer_accuracy": transfer_kind,
            "action_distinction": "weak" if transfer_kind == "content_transfer" else "operational",
            "phrase_action_distribution": dict(actions),
        },
        "replay_targets": [target],
        "replay_directives": [_REGISTER_SAPPER_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Register Sapper profile\n"
            f"- Register blindness: **{blindness}**\n"
            f"- Medium awareness: **{awareness}**\n"
            f"- Transfer accuracy: **{transfer_kind}**\n"
            f"- Replay directive: {_REGISTER_SAPPER_DIRECTIVES[target]}\n"
        ),
    }


def build_promise_court_profile(moves: list[dict], interventions: list[dict]) -> dict:
    # Track per-promise form completeness from fill_obligation_form moves.
    forms_by_promise: dict[str, dict] = {}
    verdicts: Counter = Counter()
    for m in moves:
        if m["action"] == "fill_obligation_form":
            pid = m.get("target_unit_id") or m["payload"].get("promise_id")
            if pid:
                forms_by_promise[pid] = m["payload"]
        if m["action"] in ("send_to_court", "accept_promise"):
            verdicts["sent_to_court" if m["action"] == "send_to_court" else "accepted"] += 1

    # Which field is most often missing among promises actually filled?
    missing_counts = Counter()
    for pid, form in forms_by_promise.items():
        for key in ("owner", "deadline", "criterion", "fallback"):
            v = form.get(key)
            if not isinstance(v, str) or not v.strip():
                missing_counts[key] += 1

    total_promises = sum(verdicts.values()) or 1
    court_ratio = verdicts.get("sent_to_court", 0) / total_promises
    if court_ratio >= 0.75:
        court_load = "court_overload"
    elif court_ratio >= 0.4:
        court_load = "balanced"
    else:
        court_load = "completeness_strict"

    # If the player accepted promises with empty fields, name what they kept missing.
    accepted_with_holes = Counter()
    for pid, form in forms_by_promise.items():
        # accept came AFTER fill, deduce by action sequence
        # heuristic: if verdict for this pid was 'accepted' but a field is empty
        pass  # we don't carry verdict-per-promise yet; rely on counts

    blindness = "balanced"
    if court_ratio < 0.4 and missing_counts:
        worst = missing_counts.most_common(1)[0][0]
        blindness_key = {"owner": "missed_no_owner", "deadline": "missed_no_deadline",
                         "criterion": "missed_no_criterion", "fallback": "missed_no_fallback"}.get(worst)
        if blindness_key:
            blindness = blindness_key

    target = blindness if blindness != "balanced" else court_load
    if target not in _PROMISE_COURT_DIRECTIVES:
        target = "balanced"

    return {
        "dimensions": {
            "promise_blindness": blindness,
            "court_load": court_load,
            "completeness_demand": "strict" if court_load == "completeness_strict" else ("loose" if court_load == "court_overload" else "balanced"),
            "missing_field_distribution": dict(missing_counts),
            "verdict_distribution": dict(verdicts),
        },
        "replay_targets": [target],
        "replay_directives": [_PROMISE_COURT_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Promise Court profile\n"
            f"- Promise blindness: **{blindness}**\n"
            f"- Court load: **{court_load}** (court ratio {court_ratio:.0%})\n"
            f"- Verdicts: {dict(verdicts)}\n"
            f"- Missing fields: {dict(missing_counts)}\n"
            f"- Replay directive: {_PROMISE_COURT_DIRECTIVES[target]}\n"
        ),
    }


_GENERIC_CARD_SORTING_DIRECTIVES = {
    "skewed_to_first":   "next round: include cards that look like the player's preferred zone but actually belong to another — flush that bias",
    "skewed_to_last":    "next round: salt the deck with cards that match the player's safe last-zone but carry a different operation",
    "no_revisions":      "next round: stage borderline cards where the advocate's pushback should produce at least one revision",
    "balanced":          "next round: introduce a harder borderline tier — half-and-half by surface, split by operation",
}


def _generic_card_sorting_profile(moves: list[dict], interventions: list[dict],
                                   game_id: str,
                                   primary_dim_name: str = "selection_bias") -> dict:
    """Reusable profile shape for the card_sorting-based породы.

    Tracks fate distribution, revisions, and computes a 'skewed_to_<zone>' bias
    when the player overuses a single zone.
    """
    fates = Counter()
    revisions = 0
    for m in moves:
        if m["action"] == "sort_card":
            fates[m["payload"].get("fate", "unknown")] += 1
        if m["action"] == "revise_fate":
            revisions += 1
    total = sum(fates.values()) or 1
    top = fates.most_common(1)
    bias_tag = "balanced"
    if top and top[0][1] / total >= 0.55:
        bias_tag = "skewed_to_first"
    elif revisions == 0 and total >= 6:
        bias_tag = "no_revisions"
    target = bias_tag if bias_tag in _GENERIC_CARD_SORTING_DIRECTIVES else "balanced"
    return {
        "dimensions": {
            primary_dim_name: bias_tag,
            "fate_distribution": dict(fates),
            "revisions": revisions,
            "dominant_zone": top[0][0] if top else None,
        },
        "replay_targets": [target],
        "replay_directives": [_GENERIC_CARD_SORTING_DIRECTIVES[target]],
        "markdown_summary": (
            f"## {game_id} profile\n"
            f"- {primary_dim_name}: **{bias_tag}**\n"
            f"- Fates: {dict(fates)}\n"
            f"- Revisions: {revisions}\n"
            f"- Replay directive: {_GENERIC_CARD_SORTING_DIRECTIVES[target]}\n"
        ),
    }


def build_assistant_as_foreign_profile(moves, interventions):
    return _generic_card_sorting_profile(moves, interventions, "assistant_as_foreign", "alien_blindness")


def build_agent_passport_profile(moves, interventions):
    return _generic_card_sorting_profile(moves, interventions, "agent_passport", "agency_detection_bias")


def build_false_consensus_profile(moves, interventions):
    return _generic_card_sorting_profile(moves, interventions, "false_consensus", "consensus_bias")


def build_burn_cognitor_profile(moves, interventions):
    return _generic_card_sorting_profile(moves, interventions, "burn_cognitor", "idol_attachment")


# Прсомпт-снасть / Игра под захватом — reuse the False Click clickable_text shape
# but rename the bias and tweak the directive ladder.
_PROMPT_TACKLE_DIRECTIVES = {
    "load_bearing_addict": "next round: include scaffold pieces that the player WILL identify as load-bearing — push them to find the operation that replaces them",
    "shed_addict":         "next round: include genuinely load-bearing constraints that look like scaffolds — punish over-shedding",
    "balanced":            "next round: include a piece labelled scaffold whose removal silently changes the operation — verify you notice the drift",
}

_CAPTURE_DIRECTIVES = {
    "lost_field":    "next round: increase decorative noise blocks — verify you don't lose the field first under pressure",
    "lost_proof":    "next round: shorten the prove step — verify you don't drop the operation proof first",
    "lost_subject":  "next round: hide the speaker tag — verify subject is what you defend",
    "lost_register": "next round: switch register mid-message — verify register is what you defend",
    "held":          "next round: increase pressure along the axis where you LAST broke — calibration",
}


def build_prompt_tackle_profile(moves, interventions):
    verdicts = Counter()
    for m in moves:
        if m["action"] == "assign_verdict":
            v = m["payload"].get("verdict")
            if v:
                verdicts[v] += 1
    total = sum(verdicts.values()) or 1
    if verdicts.get("load_bearing", 0) / total > 0.6:
        bias = "load_bearing_addict"
    elif verdicts.get("removable", 0) / total > 0.6:
        bias = "shed_addict"
    else:
        bias = "balanced"
    target = bias
    return {
        "dimensions": {
            "scaffold_dependency": bias,
            "verdict_distribution": dict(verdicts),
        },
        "replay_targets": [target],
        "replay_directives": [_PROMPT_TACKLE_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Prompt Tackle profile\n"
            f"- Scaffold dependency: **{bias}**\n"
            f"- Verdicts: {dict(verdicts)}\n"
            f"- Replay directive: {_PROMPT_TACKLE_DIRECTIVES[target]}\n"
        ),
    }


def build_game_under_capture_profile(moves, interventions):
    verdicts = Counter()
    for m in moves:
        if m["action"] == "assign_verdict":
            v = m["payload"].get("verdict")
            if v:
                verdicts[v] += 1
    if verdicts.get("held_operation", 0) >= max(1, sum(verdicts.values()) - 1):
        bias = "held"
    else:
        # Pick the most common 'lost_*' as the first-dropped axis.
        lost_only = {k: v for k, v in verdicts.items() if k.startswith("lost_")}
        bias = max(lost_only, key=lost_only.get) if lost_only else "held"
    target = bias if bias in _CAPTURE_DIRECTIVES else "held"
    return {
        "dimensions": {
            "first_dropped_axis": bias.replace("lost_", "") if bias != "held" else "none",
            "pressure_dropoff": "stable" if bias == "held" else "weak",
            "verdict_distribution": dict(verdicts),
        },
        "replay_targets": [target],
        "replay_directives": [_CAPTURE_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Game Under Capture profile\n"
            f"- First dropped axis: **{bias}**\n"
            f"- Verdicts: {dict(verdicts)}\n"
            f"- Replay directive: {_CAPTURE_DIRECTIVES[target]}\n"
        ),
    }


# Ontology Customs reuses medium_shift_phrase actions but with a different
# semantic axis: 'preserved | distorted | smuggled | forbidden | new_organ'.
_CUSTOMS_DIRECTIVES = {
    "smuggling_blind": "next round: stage a ход which only LOOKS preserved across ontologies — verify you spot the smuggled change",
    "over_distortion": "next round: include a ход whose distortion is correct adaptation — verify you don't over-reject",
    "preserved_addict":"next round: ввести ход который реально не переносится — verify you stop declaring 'preserved'",
    "balanced":        "next round: include a ход whose translation creates a genuine new organ — verify you name it correctly",
}


def build_ontology_customs_profile(moves, interventions):
    actions = Counter()
    repairs = 0
    transfers = 0
    transfer_action = None
    for m in moves:
        if m["action"] == "assign_phrase_action":
            actions[m["payload"].get("phrase_action", "unknown")] += 1
        if m["action"] == "repair_machine_reading":
            repairs += 1
        if m["action"] == "transfer_phrase":
            transfers += 1
            if m["payload"].get("preserves_action"):
                transfer_action = m["payload"].get("target_medium")
    total = sum(actions.values()) or 1
    if actions.get("preserved", 0) / total >= 0.55:
        bias = "preserved_addict"
    elif actions.get("smuggled", 0) == 0 and total >= 3:
        bias = "smuggling_blind"
    elif actions.get("distorted", 0) / total >= 0.55:
        bias = "over_distortion"
    else:
        bias = "balanced"
    target = bias
    return {
        "dimensions": {
            "transfer_accuracy": "action_transfer" if transfer_action else "content_transfer",
            "smuggling_blindness": bias,
            "action_distribution": dict(actions),
            "repairs": repairs,
        },
        "replay_targets": [target],
        "replay_directives": [_CUSTOMS_DIRECTIVES[target]],
        "markdown_summary": (
            f"## Ontology Customs profile\n"
            f"- Smuggling read: **{bias}**\n"
            f"- Declarations: {dict(actions)}\n"
            f"- Transfer to new ontology: **{transfer_action or '—'}**\n"
            f"- Replay directive: {_CUSTOMS_DIRECTIVES[target]}\n"
        ),
    }


BUILDERS = {
    "false_click": build_false_click_profile,
    "missing_operation": build_missing_operation_profile,
    "sprout_or_slop": build_sprout_or_slop_profile,
    "register_sapper": build_register_sapper_profile,
    "promise_court": build_promise_court_profile,
    "prompt_tackle": build_prompt_tackle_profile,
    "assistant_as_foreign": build_assistant_as_foreign_profile,
    "agent_passport": build_agent_passport_profile,
    "ontology_customs": build_ontology_customs_profile,
    "game_under_capture": build_game_under_capture_profile,
    "false_consensus": build_false_consensus_profile,
    "burn_cognitor": build_burn_cognitor_profile,
}


def build_profile(game_id: str, moves: list[dict], interventions: list[dict]) -> dict:
    fn = BUILDERS.get(game_id)
    if not fn:
        return {
            "dimensions": {},
            "replay_targets": [],
            "replay_directives": [],
            "markdown_summary": "(no profile builder)",
        }
    profile = fn(moves, interventions)
    profile["game_id"] = game_id
    # Sanity: replay_directives must be actionable sentences, not adjectives.
    profile["replay_directives"] = [
        d for d in profile.get("replay_directives", []) if isinstance(d, str) and len(d) > 25
    ]
    return profile
