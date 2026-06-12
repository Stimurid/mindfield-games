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
    return {
        "dimensions": {
            "false_click_bias": bias_label,
            "operation_proof_strength": proof_strength,
            "verdict_distribution": dict(verdicts),
        },
        "replay_targets": [bias_label] if bias_label != "mixed" else ["pseudo_depth"],
        "markdown_summary": (
            f"## False Click profile\n"
            f"- Dominant click-bias: **{bias_label}**\n"
            f"- Proof strength on bearing nodes: **{proof_strength}**\n"
            f"- Verdict mix: {dict(verdicts)}\n"
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
    blindness = absences.most_common(1)
    blindness_label = blindness[0][0] if blindness else "subject"
    if patch_responses.get("accept", 0) > patch_responses.get("reject", 0):
        susceptibility = "accepts_smooth_bridge"
    elif patch_responses.get("reject", 0) > patch_responses.get("accept", 0) + patch_responses.get("repair", 0):
        susceptibility = "over_rejects"
    else:
        susceptibility = "resists_patch"
    return {
        "dimensions": {
            "absence_focus": blindness_label,
            "patch_susceptibility": susceptibility,
            "absence_distribution": dict(absences),
            "fate_distribution": dict(fates),
        },
        "replay_targets": ["subject" if blindness_label != "subject" else "criterion"],
        "markdown_summary": (
            f"## Missing Operation profile\n"
            f"- Most named absence: **{blindness_label}**\n"
            f"- Patch behaviour: **{susceptibility}**\n"
            f"- Fates: {dict(fates)}\n"
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
    return {
        "dimensions": {
            "selection_bias": bias,
            "revisions": revisions,
            "incubation_tests_set": incubation_tests,
            "fate_distribution": dict(fates),
        },
        "replay_targets": [bias],
        "markdown_summary": (
            f"## Sprout or Slop profile\n"
            f"- Selection bias: **{bias}**\n"
            f"- Revisions after advocate pressure: {revisions}\n"
            f"- Incubation tests set: {incubation_tests}\n"
            f"- Fates: {dict(fates)}\n"
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
    return {
        "dimensions": {
            "register_blindness": blindness,
            "medium_awareness": awareness,
            "transfer_accuracy": transfer_kind,
            "phrase_action_distribution": dict(actions),
        },
        "replay_targets": [blindness],
        "markdown_summary": (
            f"## Register Sapper profile\n"
            f"- Register blindness: **{blindness}**\n"
            f"- Medium awareness: **{awareness}**\n"
            f"- Transfer accuracy: **{transfer_kind}**\n"
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
        return {"dimensions": {}, "replay_targets": [], "markdown_summary": "(no profile builder)"}
    profile = fn(moves, interventions)
    profile["game_id"] = game_id
    return profile
