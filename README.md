# Mindfield Games — LLM Game Field Runtime

First MVP of the *Operator Calibration Pack*: four psychotechnical micro-apps that build a qualitative **Operator Profile** of how a person handles LLM-shaped text. Not a chatbot, not a quiz, not a prompt trainer.

The full design spec lives in [`docs/spec.md`](docs/spec.md).

## What this is

Four games, one runtime, one cycle: **material → field → move → LLM intervention → verdict → trace → mutation**.

| Game | Field type | LLM role | What it calibrates |
|---|---|---|---|
| **False Click** | clickable_text_units | `prosecutor` | distinguishing operation from beautiful imitation of meaning |
| **Missing Operation** | gap_click_text | `spackler` | seeing the place where an operation is missing, not patching it |
| **Sprout or Slop** | card_sorting | `sprout_advocate` | assigning fates to weak material without sterilising or hoarding |
| **Register Sapper** | medium_shift_phrase | `literal_alien` | reading the *action* of a phrase across mediums, not its tone |

The LLM is never an assistant. Each role attacks, patches-deceptively, argues against the player, or reads literally and loses meaning. Profiles are qualitative tags (`false_click_bias: dramatic_phrase`, `selection_bias: overcuts`), not numeric scores.

## What this is NOT in MVP

No auth, payments, multiplayer, RAG, marketplace, Textopolis, mobile app, Docker/cloud deploy, complex analytics. See spec §1 and the risk list.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite, Pydantic v2, Python 3.13.
- **Frontend:** Vite + React 18 + TypeScript, react-router.
- **LLM:** provider abstraction with deterministic `MockProvider` (default, no key needed) and optional `AnthropicProvider`.
- **GameGenome:** JSON files in `backend/game_genomes/`. Adding a fifth game = one JSON + (if a new field type) one renderer.

## Run locally

### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API listens on `http://localhost:8000`. Health: `GET /api/health`.

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Vite serves `http://localhost:5173` and proxies `/api` to `:8000`.

### Tests
```powershell
cd backend
.venv\Scripts\python.exe -m pytest -q
```

Ten tests cover the full per-game loop (`select → prove → attack → verdict → profile`, etc.), action validation against genome, JSON/Markdown export, and the contract that mock LLM roles do not behave like an assistant.

## Switching to a real LLM

```powershell
$env:MINDFIELD_LLM = "anthropic"
$env:ANTHROPIC_API_KEY = "sk-..."
uvicorn app.main:app --reload
```

Falls back to mock if either is missing. The role system prompts in `backend/app/llm/roles.py` force JSON-only output and pin the model to a non-assistant register.

## Architecture at a glance

```
backend/
  app/
    main.py                FastAPI app, seeds materials on startup
    database.py            SQLite engine
    models.py              Material, GameSession, PlayerMove, LLMIntervention
    schemas.py             Pydantic v2 in/out
    api/
      games.py             GET /api/games, GET /api/games/{id}
      sessions.py          POST /sessions, /moves, /llm-intervention, /complete, GET /export
      materials.py         materials list/get
    llm/
      roles.py             prosecutor / spackler / sprout_advocate / literal_alien
      provider.py          MockProvider (deterministic), AnthropicProvider
    services/
      genome_loader.py     loads /game_genomes/*.json
      profile_builder.py   qualitative Operator Profile per game
      exporter.py          Markdown + JSON export
  game_genomes/            *.json — declarative game specs
  seed_materials/          one seed per game
  tests/
frontend/
  src/
    routes/                Home, Play, Profile
    components/            GameShell, RoundHeader, LLMPanel, TracePanel
    components/fields/     one renderer per field_type
    api/client.ts          thin fetch wrapper
```

## Adding a fifth game

1. Drop a JSON into `backend/game_genomes/`.
2. If it reuses an existing `field_type`, you're done. Add a seed in `backend/seed_materials/{game_id}/`.
3. If you need a new field type: implement the renderer in `frontend/src/components/fields/` and wire it in `GameShell.tsx`. Add a profile builder in `backend/app/services/profile_builder.py`.

The runtime must stay a runtime — if you find yourself special-casing a game inside `api/sessions.py`, push the case back into the genome.

## License

TBD.
