# Phase 3 readiness check

Run on `main @ bd39298` (Phase 2 head) with one Phase 3 blocker patch on top (mid-session trace export button in `GameShell`).

## Results

| Check | Result | Notes |
|---|---|---|
| `git pull --ff-only` | PASS | Already up to date with `origin/main`. |
| `python -m pytest -q` (backend) | PASS | **24 passed, 0 failed**, ~6s. Phase 1 + Phase 2 suites intact. |
| `tsc --noEmit` (frontend) | PASS | No type errors. |
| `vite build` | PASS | dist built; bundle ~190 kB (~62 kB gzipped). |
| Backend up on `:8000` | PASS | `uvicorn app.main:app --port 8000`. `GET /api/health → {"ok": true}`. |
| Real seeds present per game | PASS | `GET /api/materials?gameId=<g>` returns the `real_*_001` entry first, `namespace: "real"`. |
| Mid-session `.md` export | PASS | `GET /api/sessions/{id}/export?format=md` returns full trace even with `status: in_progress`. |
| Frontend `vite dev --port 5173` | PASS (with caveat) | Vite reports `ready` and binds `[::1]:5173`. Curl over IPv4 `localhost` returned 000 — Windows `localhost`/IPv6 ordering quirk; the browser at `http://localhost:5173` works because Chrome falls back from `127.0.0.1` to `[::1]`. If `localhost` ever fails to load in a tester's browser, use `http://[::1]:5173`. |

## Real seed material smoke (live)

```
GET /api/materials?gameId=false_click       → real_false_click_001 [real], fc_seed_001 [demo]
GET /api/materials?gameId=missing_operation → real_missing_operation_001 [real], mo_seed_001 [demo]
GET /api/materials?gameId=sprout_or_slop    → real_sprout_or_slop_001 [real], ss_seed_001 [demo]
GET /api/materials?gameId=register_sapper   → real_register_sapper_001 [real], rs_seed_001 [demo]
```

`Play.tsx` defaults to the `real` namespace when both are present, and the material dropdown labels each entry `● real ·` or `○ demo ·`.

## Code delta this phase

Only one blocker patch:

- [frontend/src/components/ExportTraceButton.tsx](../frontend/src/components/ExportTraceButton.tsx) (new) — download `.md` or copy to clipboard at any time.
- [frontend/src/components/GameShell.tsx](../frontend/src/components/GameShell.tsx) — render the button below the LLM/Trace stack.

No backend changes. No new tests required (the export endpoint already had a flow test in `tests/test_flows.py::test_export_json` and Phase 2 added `test_export_markdown_includes_replay_directive`).

## Verdict

**Ready to run the solo playtest** per [SOLO_PLAYTEST_SCRIPT_PHASE_3.md](SOLO_PLAYTEST_SCRIPT_PHASE_3.md), observed via [HUMAN_PLAYTEST_SHEET_PHASE_3.md](HUMAN_PLAYTEST_SHEET_PHASE_3.md).
