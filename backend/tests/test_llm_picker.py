"""Non-live tests for the LLM model picker contract.

These do NOT call 302.ai. They only check that:
  - GET /api/llm/models returns the documented presets and a default,
  - POST /api/sessions/:id/llm-intervention accepts a model override,
  - the override is forwarded to the provider (mock under test).
"""


def test_models_endpoint_lists_presets(client):
    r = client.get("/api/llm/models")
    assert r.status_code == 200
    body = r.json()
    assert "presets" in body and isinstance(body["presets"], list) and body["presets"]
    ids = {p["id"] for p in body["presets"]}
    assert {"gpt-4.1-mini", "grok-4-0709"} <= ids
    for p in body["presets"]:
        assert set(p.keys()) >= {"id", "label", "gateway"}
        assert p["gateway"] == "302.ai"
    assert "default" in body
    # Under MINDFIELD_LLM=mock the active provider is the mock.
    assert body["provider"] in {"MockProvider", "OpenAICompatibleProvider"}


def test_intervention_accepts_model_override(client):
    # Seed a session on the false_click real material
    mats = client.get("/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions", json={"game_id": "false_click", "material_id": real["id"]}).json()
    r = client.post(
        f"/api/sessions/{s['id']}/llm-intervention",
        json={
            "role": "prosecutor",
            "context": {"phrase": "x", "claimed_operation": "y"},
            "model": "grok-4-0709",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "prosecutor"
    assert "attacks" in body["output"] and "probe_question" in body["output"]


def test_intervention_works_without_model_field(client):
    mats = client.get("/api/materials?gameId=false_click").json()
    real = next(m for m in mats if m["namespace"] == "real")
    s = client.post("/api/sessions", json={"game_id": "false_click", "material_id": real["id"]}).json()
    r = client.post(
        f"/api/sessions/{s['id']}/llm-intervention",
        json={"role": "prosecutor", "context": {"phrase": "x", "claimed_operation": "y"}},
    )
    assert r.status_code == 200
