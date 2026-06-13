"""Live smoke for the GameWeaver (playability_critic) against a running backend."""
import json, os, urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8000/api")
MODEL = os.environ.get("SMOKE_MODEL")


def _req(method, path, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=90) as resp:
        return json.loads(resp.read().decode())


def _pick_first(bank):
    organs = _req("GET", f"/configurator/organs?bank={bank}")
    return organs[0]["id"]


def run(name, draft_payload, expected_verdict):
    print(f"\n=== {name} ===")
    d = _req("POST", "/configurator/drafts", draft_payload, {"X-Player-Token": "smoke-p13"})
    r = _req("POST", f"/configurator/drafts/{d['id']}/weaver", {"model": MODEL} if MODEL else {})
    v = r["verdict"]
    print(f"  verb_status: {v['verb_status']}")
    print(f"  crisis_status: {v['crisis_status']}")
    print(f"  trace_status: {v['trace_status']}")
    print(f"  playable_verdict: {v['playable_verdict']}")
    print(f"  critique: {v['critique']}")
    if v["degradation_warnings"]:
        print(f"  degradation_warnings: {v['degradation_warnings']}")
    if expected_verdict and v["playable_verdict"] != expected_verdict:
        print(f"  ⚠ expected {expected_verdict}, got {v['playable_verdict']}")


def main():
    # Case 1: minimal complete draft
    run("minimal complete", {
        "name": "ОК-draft",
        "verb": "кликнуть",
        "maturity_stage": 2,
        "selected_organs": {
            "field":  [_pick_first("field")],
            "action": [_pick_first("action")],
            "crisis": [_pick_first("crisis")],
            "trace":  [_pick_first("trace")],
            "llm_role": [_pick_first("llm_role")],
        },
    }, expected_verdict="playable")

    # Case 2: no verb
    run("no verb", {
        "name": "без глагола",
        "verb": "",
        "selected_organs": {
            "crisis": [_pick_first("crisis")],
            "trace":  [_pick_first("trace")],
        },
    }, expected_verdict="not_playable_yet")

    # Case 3: degradation organ picked
    run("with degradation", {
        "name": "корпоративный тренинг",
        "verb": "кликнуть",
        "selected_organs": {
            "field":       [_pick_first("field")],
            "action":      [_pick_first("action")],
            "crisis":      [_pick_first("crisis")],
            "trace":       [_pick_first("trace")],
            "degradation": [_pick_first("degradation")],
        },
    }, expected_verdict="rotten")


if __name__ == "__main__":
    main()
