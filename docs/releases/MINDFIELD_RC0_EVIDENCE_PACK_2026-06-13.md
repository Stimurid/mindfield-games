# Mindfield RC-0 Evidence Pack · 2026-06-13

Commit [`2d40bda`](https://github.com/Stimurid/mindfield-games/commit/2d40bda). What is actually proven, what is only smoked, what is unproven.

## 1. Automated test surface — 127 / 127 green

Backend tests (Phase / Block grouping):

| File | Coverage area | Tests |
|---|---|---|
| `tests/test_games.py` | genome catalog matches expected 12-genre roster | 6 |
| `tests/test_flows.py` | Phase 1 end-to-end per-game flow on demo seeds | 4 |
| `tests/test_phase2.py` | real seeds, qualitative profiles, replay directive shape, LLM role non-assistant contract | 14 |
| `tests/test_llm_picker.py` | live LLM provider config (gpt-4.1-mini + grok-4-0709 present, intervention round-trip) | 4 |
| `tests/test_phase5.py` | replay loop: completed session → mutator → new session per game | 6 |
| `tests/test_phase6.py` | cross-game Operator Profile aggregator + cookie token | 4 |
| `tests/test_phase7.py` | corpus ingest + FTS5 search + reader endpoints | 7 |
| `tests/test_phase8.py` | summon 4 organs over library entry, comment thread ordering | 4 |
| `tests/test_phase9.py` | material conversion corpus → playable seed per genre | 6 |
| `tests/test_phase10.py` | Promise Court (5th canonical genre) full flow + replay | 5 |
| `tests/test_phase12.py` | raw 4200 cards present, sections, FTS5 hits a known card name | 6 |
| `tests/test_phase13.py` | configurator: 8 banks, 130 organs, draft lifecycle, GameWeaver verdicts | 7 |
| `tests/test_phase14.py` | triage: 9 fates, organ extraction grows the action bank by one | 8 |
| `tests/test_block3_porodies.py` | 7 new canonical породы — genome load, real seed load, full flow, replay | 23 |
| `tests/test_block4_chimera.py` | chimera generator → draft → no degradation slips through → GameWeaver = playable | 5 |
| `tests/test_blocks_5_6.py` | maturity backfill defaults, filter, PATCH; admin materials CRUD; debug session view | 8 |
| `tests/test_runtime.py` | session lifecycle invariants | 2 |
| `tests/test_export.py` | markdown export shape | 2 |
| `tests/test_replay.py` | replay endpoint refuses incomplete sessions | 1 |
| `tests/test_role_drift.py` | mock-level role drift contract | 1 |
| `tests/test_seed_files.py` | seed JSON files load and validate | 4 |

Total **127 / 127** in 226 seconds (includes 4200 cards ingest per fixture).

## 2. Frontend build

```
dist/index.html            0.43 kB
dist/assets/index.css      4.14 kB · gzip 1.33 kB
dist/assets/index-….js   229.43 kB · gzip 71.87 kB
✓ built in 1.06 s
```

TypeScript: clean, no errors.

## 3. Prod smoke (`2026-06-13`)

Edge probe from the workstation:

```
GET https://mindfield.mindkampf.ru/                401  (basic_auth gate alive)
GET https://mindfield.mindkampf.ru/ -u timur:wrong 401
```

Internal probes via `docker exec mindfield-api` (bypassing the edge):

```
/api/library/sections     13 sections present
/api/configurator/banks    8 banks present
/api/llm/models            provider=OpenAICompatibleProvider · presets=[gpt-4.1-mini, grok-4-0709]
/api/games                12 games
/api/triage/fates          9 fates
/api/admin/materials       9 materials (12 real + 5 demo were planned; admin lists what is in the prod
                            sqlite at this moment — see note below)
```

Note on the materials count: the prod SQLite at `/opt/mindfield/data/mindfield.db` carries the
seeds loaded at first boot; subsequent additions (Block 3 seeds for the 7 new породы, Promise
Court real seed) are picked up by `seed_materials_if_empty()` only when the table is empty. On
this RC-0 freeze the live DB shows 9 materials; the remaining 8 canonical real seeds are present
in the repo and will be seeded on a fresh DB or can be loaded via `/api/admin/materials POST`.
This is a **known non-blocker** — the seeds are reproducible and the API surface is the same.

Live LLM smoke results stored in repo:
- `backend/scripts/smoke_user_phrase.py` — prosecutor on the False Click real seed, both models.
- `backend/scripts/smoke_replay.py` — full replay loop probe: completed session → real mutator
  call → new material has same field_type + valid item count, on prod.
- `backend/scripts/smoke_weaver.py` — playability_critic against 3 drafts (minimal complete /
  no verb / with degradation organ). Real model returned correct verdict in each case with
  one-sentence Russian critique.
- `backend/scripts/smoke_chimera.py` — chimera_v0.1_001 (`Смысловой клик × Антислоп`) → real
  `chimera_weaver` call produced `name='Сминёр'`, function naming both родов, verb `'кликнуть'`,
  organ ids per bank, critique sentence; the resulting draft passed GameWeaver = `playable`.

## 4. Canonical cycle proof

The full cycle is implemented and the API path is proven end to end in tests, smoke, or both:

```
RAW CARD  (corpus_entries kind=source_card)
  │
  │ proven by: test_phase12 + library_entry view + /api/triage/queue
  ▼
TRIAGE    POST /api/triage/entries/{id} fate=extract_organ
  │
  │ proven by: test_phase14::test_extract_organ_creates_new_bank_entry
  │            (asserts the action bank gained exactly one row,
  │             source='extracted', name matches the input)
  ▼
ORGAN BANK (organs.source='extracted', source_entry_id=card.id)
  │
  │ proven by: same test + /api/configurator/organs?bank=action listing
  ▼
CONFIGURATOR  POST /api/configurator/drafts {selected_organs={action: [organ_id]}}
  │
  │ proven by: test_phase13::test_draft_lifecycle
  │            test_phase13::test_weaver_playable_when_minimums_present
  │            test_block4_chimera::test_chimera_draft_runs_through_weaver
  │            live smoke: smoke_weaver.py against gpt-4.1-mini
  ▼
GAME WEAVER   POST /api/configurator/drafts/{id}/weaver
  │           verdict ∈ {playable, not_playable_yet, rotten}
  │
  │ proven by: same test_phase13 set + degradation-flagging test +
  │            smoke_weaver.py for all 3 verdict classes
  ▼
GAME ROUTE    Play the assembled genre. (For RC-0 the player typically picks
              one of the 12 canonical genres rather than running the assembled
              draft as a genome — promoting a draft into a runtime genome is
              an explicit Phase 17+ feature.)
  │
  │ proven by: test_phase2 + test_block3 + test_phase10 (every genre has a
  │            real-seed full-flow test)
  ▼
PROFILE       POST /api/sessions/{id}/complete
  │           returns dimensions + replay_directives
  │
  │ proven by: per-genre profile assertions in test_phase2 and
  │            test_block3_porodies
  ▼
REPLAY        POST /api/sessions/{id}/replay
  │           creates a new Material namespace='mutated' with parent_id
  │
  │ proven by: test_phase5 + parametrized
  │            test_block3_porodies::test_replay_loop_works_for_new_porodies
  │            for all 12 genres; live smoke_replay.py on prod False Click
  ▼
MATERIAL MUTATOR → NEW SESSION
  │
  │ proven by: same tests + the new session is a normal session that the
  │            UI navigates to automatically
  ▼
NEXT SESSION   (UI redirects via Profile.tsx::startReplay)
```

**Gap to note:** the cycle does **NOT yet** prove that the player's second session ACTUALLY
TARGETS A DETECTED WEAKNESS. The mutator returns the right shape of material; whether the
mutated content correctly amplifies the directive (e.g. "more pseudo-depth nodes") is an
**LLM-output-quality claim** — see [`MINDFIELD_RC0_UNPROVEN_CLAIMS.md`](MINDFIELD_RC0_UNPROVEN_CLAIMS.md)
§4 and the full-cycle playtest protocol §5.

## 5. Coverage breakdown

| Cycle component | Automated | Live smoke | Human playtest |
|---|---|---|---|
| Corpus parse / ingest | YES (test_phase7 + test_phase12) | — | — |
| FTS5 search | YES | — | — |
| Triage fate assignment | YES (test_phase14) | — | — |
| Triage `extract_organ` grows bank | YES | — | — |
| Configurator draft CRUD | YES (test_phase13) | — | — |
| Playability critic verdict shape | YES (mock) | YES (smoke_weaver against real model, 3 cases) | — |
| Playability critic critique quality | — | partial (single-sentence assertions) | NO |
| Chimera generator → draft | YES (test_block4) | YES (smoke_chimera against real model) | — |
| Chimera draft contains no degradation organ | YES | YES | — |
| Per-genre genome load | YES | — | — |
| Per-genre real-seed flow | YES (test_phase2 + test_block3 + test_phase10) | — | — |
| LLM organ role contract (4 roles) | YES (mock — test_phase2 forbids assistant keys) | YES (smoke_user_phrase real model on prosecutor) | partial (gauntlet doc only) |
| LLM role drift over a long session | — | — | NO |
| Replay loop creates valid new material | YES (test_phase5 + parametrized block3) | YES (smoke_replay) | — |
| Mutated material actually amplifies the directive | partial (mock returns tagged stubs) | YES on False Click only (see smoke_replay output stored in Phase 5 report) | NO across 12 genres |
| Cross-game Operator Profile aggregation | YES (test_phase6) | — | — |
| Operator Profile usefulness for a human | — | — | NO |
| Material converter (corpus → seed) | YES (test_phase9) | — | — |
| Converter output quality on a player | — | — | NO |
| Maturity backfill defaults | YES (test_blocks_5_6) | — | — |
| Maturity filter | YES | — | — |
| Admin Materials CRUD | YES | YES (prod GET /api/admin/materials) | — |
| Debug session raw JSON | YES (uses /api/sessions/{id}) | YES | — |
| Caddy basic_auth gate | — | YES (curl edge 401) | — |
| TLS auto-renewal | — | implicit (Caddy log on prod) | — |
| Cookie-bound player_token survives replay | YES (test_phase5) | — | — |

## 6. Bill of files supporting RC-0

- 12 game genomes in `backend/game_genomes/`
- 12 real seeds in `backend/seed_materials_real/<game_id>/real_<game_id>_001.json`
- 5 demo seeds in `backend/seed_materials/`
- 4 live smoke scripts in `backend/scripts/smoke_*.py`
- 130 canonical organs seeded by `app/services/organ_seed.py`
- 4 720 corpus entries seeded by `app/services/corpus_ingest.py`
- 30+ commits between the start of the implementation pass and `2d40bda`

## 7. What this evidence does NOT cover

Listed for completeness; full treatment in
[`MINDFIELD_RC0_UNPROVEN_CLAIMS.md`](MINDFIELD_RC0_UNPROVEN_CLAIMS.md):

- whether the games form psychotechnical functions in a human player,
- whether anything learned transfers outside the app,
- whether replay improves the player rather than just mutating text,
- whether generated drafts are playable on humans,
- whether triage fate quality scales over many cards,
- whether LLM role stability holds over many turns,
- whether players know what action they are performing,
- whether the cross-game Operator Profile is useful as a diagnostic.

These are all addressed by the full-cycle playtest protocol below
([`docs/playtests/FULL_CYCLE_PLAYTEST_V1.md`](../playtests/FULL_CYCLE_PLAYTEST_V1.md)).
