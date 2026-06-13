"""Smoke the new prosecutor prompt against the actual phrase the player picked.

This is the exact text from the screenshot: bearing_node 'r9' from
real_false_click_001, with the player's claimed operation.
"""
import json, sys, urllib.request

B = "http://localhost:8000/api"


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{B}{path}", data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode())


PHRASE = ("Когнитивная стоимость одного запуска эксперимента важнее, чем его "
          "потенциальный ROI: дорогие эксперименты убивают цикл обучения.")
CLAIMED = "различение, вводит разведение не понятий а даже онтологических плоскостей"


def run(model):
    mats = _req("GET", "/materials?gameId=false_click")
    real = next(m for m in mats if m["namespace"] == "real")
    s = _req("POST", "/sessions", {"game_id": "false_click", "material_id": real["id"]})
    iv = _req("POST", f"/sessions/{s['id']}/llm-intervention", {
        "role": "prosecutor",
        "context": {"phrase": PHRASE, "claimed_operation": CLAIMED},
        "model": model,
    })
    print(f"\n=== {model} ===")
    for a in iv["output"].get("attacks", []):
        print(f"• {a}")
    print(f"? {iv['output'].get('probe_question')}")


if __name__ == "__main__":
    for m in ("gpt-4.1-mini", "grok-4-0709"):
        run(m)
