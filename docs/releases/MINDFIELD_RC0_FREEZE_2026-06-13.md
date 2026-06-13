# Mindfield RC-0 Feature Freeze · 2026-06-13

**Status:** RC-0. Feature freeze.
**Commit:** [`2d40bda`](https://github.com/Stimurid/mindfield-games/commit/2d40bda)
**Prod URL:** [https://mindfield.mindkampf.ru](https://mindfield.mindkampf.ru) (basic_auth, Let's Encrypt, Caddy on `81.26.176.248`)
**LLM provider:** `OpenAICompatibleProvider` → 302.ai (`gpt-4.1-mini`, `grok-4-0709`)
**Backend tests:** 127 / 127 green.

---

## What is deployed

| Layer | Surface |
|---|---|
| Games | 12 canonical жанра, 1 real seed per genre + 5 demo seeds |
| Field types | 5 (`clickable_text_units`, `gap_click_text`, `card_sorting`, `medium_shift_phrase`, `promise_court_text`) |
| LLM roles | 4 organ roles (`prosecutor`, `spackler`, `sprout_advocate`, `literal_alien`) + 4 design roles (`material_mutator`, `material_converter`, `playability_critic` aka GameWeaver, `chimera_weaver`) |
| Organ banks | 8 (field, object, action, llm_role, crisis, trace, mutation, degradation) seeded with 130 canonical organs; grow from triage and chimera generation |
| Corpus library | 4 720 entries across 13 kinds: 24 attractors v0.1 + 24 v0.2, 12 R-roots, 12 breeds, 40 chimeras, 7 precards, 8 residuals, 4 genomes, 4 appspecs, 7 phase docs, 72 micro-games, 170 micro-aspects, 160 source sections, **4 200 source cards** |
| Search | SQLite FTS5 across `title` + `body`, per-kind filter |
| Triage | 9 fates from spec §4; queue with kind filter; organ extraction creates new bank rows with `source='extracted'` and a backlink to the source card |
| Configurator | 8-bank chip picker, name/function/verb/stage inputs, draft persistence, manual run of GameWeaver, per-player draft list |
| GameWeaver | `playability_critic` LLM role; verb/crisis/trace status, degradation warnings, playable/not_playable_yet/rotten verdict, one-sentence critique |
| Chimera generator | one button per chimera cell → `chimera_weaver` → resolved organ ids → GenomeDraft in configurator |
| Replay loop | `material_mutator` + `/sessions/{id}/replay`; new material `namespace='mutated'`, parent_id chain, lineage in UI |
| Cross-game profile | `/api/operator/me` aggregates latest session per game for the cookie-bound `player_token`; named cross patterns |
| Material converter | from any library entry, generate a playable material for any of the 12 genres (`namespace='from_corpus'`) |
| Maturity stages | 0..5 per spec §3; kind-based defaults backfilled on startup; per-entry PATCH; UI badge + filter |
| Admin | `/admin/materials` CRUD over Materials |
| Debug | `/debug/session/:id` raw JSON |
| Operator Profile UX | `/operator` page with cross-pattern callouts, per-game cards, replay directives |
| Auth | Caddy basic_auth at the edge (shared hash with moderbober/quinta/whitecrow/litops); no app-level auth yet |

## Frontend route inventory

```
/                                Home — 12 games, links to Library / Triage / Configurator / Operator / Admin
/play/:gameId                    Play page — material picker, LLM picker, active-model badge, game shell
/session/:sessionId/profile      Per-session Operator Profile, replay button, .md export, debug raw link
/operator                        Cross-game Operator Profile aggregator
/library                         Library landing — 13 sections + FTS5 search
/library/section/:kind           Section listing with maturity filter
/library/entry/:id               Entry reader: markdown body, lineage, summon organs, triage panel,
                                 chimera generator (kind=chimera only), play-as-* buttons,
                                 maturity stage select
/configurator                    Draft GameGenome assembler + GameWeaver runner + drafts list
/triage                          Triage queue + per-fate stats
/admin/materials                 Materials CRUD (production gated by Caddy basic_auth)
/debug/session/:id               Raw session JSON
```

## Backend route inventory

Prefixes by file under `backend/app/api/`:

```
/api/games          games.py
/api/sessions       sessions.py    moves, llm-intervention, complete, export, replay
/api/materials      materials.py
/api/llm            llm.py         models
/api/operator       operator.py    me, by-token
/api/library        library.py     sections, entries, entries/:id, search, comments, summon,
                                   convert, generate-chimera-draft, maturity
/api/configurator   configurator.py banks, organs, drafts, drafts/:id/weaver
/api/triage         triage.py      fates, entries/:id, queue, stats
/api/admin          admin.py       materials CRUD
```

## The Freeze Rule

> **No new product features ship before one full-cycle human playtest produces evidence.**

A full-cycle playtest is defined in
[`docs/playtests/FULL_CYCLE_PLAYTEST_V1.md`](../playtests/FULL_CYCLE_PLAYTEST_V1.md) — it tests
the whole machine, not just one micro-app: triage → bank growth → game → profile → replay → second
session.

Until that evidence exists, the following changes are **blocked** under RC-0:

- new game genres (13th, 14th, …),
- new LLM roles,
- new organ banks,
- new field renderers,
- analytics dashboards,
- account systems / multiplayer,
- RAG / vector search,
- additional LLM providers,
- mobile-specific surfaces,
- Textopolis-shaped expansions.

## Blocker vs non-blocker

A change is a **blocker for RC-0 sign-off** if it falls into any of these:

1. A live LLM role drifts into assistant register (any of the 4 organ roles, or any of the 4 design roles) under real 302.ai output.
2. The replay loop produces a new material that is **not the same field_type** as the parent.
3. The configurator persists a draft whose organ ids do not resolve, or `weaver_verdict` returns a verdict outside `{playable, not_playable_yet, rotten}`.
4. The chimera generator returns a draft containing **any** organ from the `degradation` bank.
5. Triage `extract_organ` creates duplicate organs for the same `(bank, name)` and same source card.
6. Cross-game Operator Profile builds when `X-Player-Token` is missing (it should 400).
7. Markdown export of a completed session is empty or fails.
8. Production reachability: `https://mindfield.mindkampf.ru` does **not** return `401` without auth, or does not return `200` with auth.
9. Caddy TLS cert auto-renewal failure observable from logs.
10. Any commit lands an API key, env file, or local log containing secrets into the repo.

A change is **non-blocker** (can be deferred until after first full-cycle playtest) if it is one of:

- prompt-tuning a single LLM role unless the playtest evidence forces a redesign,
- copy edits to UI labels,
- additional seed materials for an existing genre,
- additional canonical organs,
- additional cross-pattern names in the Operator Profile aggregator,
- additional documentation,
- additional non-live tests,
- additional CSS,
- additional admin/debug affordances.

## What `Done` means for this RC

- All canonical pieces from spec §0–§11 implemented at structural level.
- Every endpoint is exercised by at least one automated test.
- Every LLM role has at least one live smoke against 302.ai recorded in `backend/scripts/smoke_*.py`.
- Every UI route renders without console errors from a cold cookie.
- All four cycle stages (triage / configurator / game / replay) link to each other in code and in UI.

## What `Done` does NOT mean for this RC

- It does **not** mean the game system has been validated as a psychotechnical instrument.
- It does **not** mean replay actually improves the player.
- It does **not** mean players understand what they're doing.
- It does **not** mean generated draft genomes are playable on humans.

Those claims belong in [`MINDFIELD_RC0_UNPROVEN_CLAIMS.md`](MINDFIELD_RC0_UNPROVEN_CLAIMS.md) and
their evidence is the job of the first full-cycle playtest.
