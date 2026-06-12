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


BUILDERS = {
    "false_click": build_false_click_profile,
    "missing_operation": build_missing_operation_profile,
    "sprout_or_slop": build_sprout_or_slop_profile,
    "register_sapper": build_register_sapper_profile,
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
