# Acceptance audit — Phase 2

Question: is the current MVP a **psychotechnical game instrument**, or just a working CRUD-shaped game UI?

Approach: walk the runtime against the spec invariants (spec.md §0–§7 of section "App-spec"), check each layer against the code, name what's earned and what's still risk.

## 1. Runtime cycle: `material → field → move → LLM intervention → verdict → trace → mutation`

| Stage | Where | Verdict | Evidence |
|---|---|---|---|
| material | [genome_loader.py](../backend/app/services/genome_loader.py), [main.py](../backend/app/main.py) seed loader, both `seed_materials/` and `seed_materials_real/` namespaces | PASS | Seeds load both demo and real namespaces; `/api/materials?gameId=...` returns both, with namespace tag. |
| field | per-`field_type` renderer in [components/fields/](../frontend/src/components/fields/); shell at [GameShell.tsx](../frontend/src/components/GameShell.tsx) switches by `genome.field_type` | PASS | One renderer per `field_type`. No game is special-cased in shell. |
| move | [POST /api/sessions/{id}/moves](../backend/app/api/sessions.py) validates `action` against `genome.player_actions` | PASS | `test_action_validation_against_genome` confirms 400 on out-of-genome action. |
| LLM intervention | [POST /api/sessions/{id}/llm-intervention](../backend/app/api/sessions.py) → [provider.py](../backend/app/llm/provider.py) → [roles.py](../backend/app/llm/roles.py) | PASS | Role-bound prompt builders; output stored as structured JSON, not chat. |
| verdict / fate | each genome declares its own `verdicts`/`fates`/`absence_types`/`phrase_actions`; UI reads from genome | PASS | UI options are populated from genome arrays; no hard-coded enum in components. |
| trace | every move and intervention persisted to `moves` + `interventions` tables; TracePanel renders chronological merge | PASS | Trace shows action, target, and *why* the move mattered (phase-2 patch). |
| mutation | [profile_builder.py](../backend/app/services/profile_builder.py) returns `replay_targets` + `replay_directives` per game | PASS (after phase-2 patch) | Directives are sentences naming next-round operations, not adjectives. |

## 2. GameGenome actually controls the runtime

Manual check against each genome JSON:

- `field_type` is the only thing that picks a renderer (`GameShell.tsx`).
- `player_actions` is enforced at write-time by `POST /moves`.
- `llm_roles[].id` populates LLMPanel header strings.
- `verdicts`/`fates`/`absence_types`/`mediums`/`phrase_actions` populate UI select options inside fields.
- `rounds[].instruction` populates RoundHeader.

Conclusion: **adding a fifth game = one JSON + (only if a new field type) one renderer**. There is no `if game_id == "false_click"` anywhere in `api/` or `services/`. (`profile_builder.py` has per-game functions, but that is correct — profiles are inherently game-specific.)

Tested via `test_phase2.py::test_real_seeds_listed_with_namespace` and the four per-game flow tests.

## 3. LLM roles are not generic assistant roles

Each role has a system prompt that forbids helping. The Phase 2 test `test_llm_roles_remain_non_assistant` asserts:

- no `answer`, `solution`, `explanation_for_player`, `helpful_tip` keys appear in output;
- no "here is the answer", "the correct answer is", "let me help you", "you should think about" strings appear in output.

Role table:

| Role | System prompt obligation | Output shape |
|---|---|---|
| `prosecutor` | attack, no answer, no help | `{attacks: [str], probe_question: str}` |
| `spackler` | offer smooth patch that hides, name risk | `{patch: str, risk: str}` |
| `sprout_advocate` | hold conflict, do not resolve | `{counterposition: str, pressure_question: str}` |
| `literal_alien` | read literally, list what you cannot see | `{literal_reading: str, things_i_cannot_see: [str]}` |

Mock provider is deterministic and role-shaped (no fallback to "general response"). When swapped to AnthropicProvider, the system prompt is reused verbatim and JSON output is forced.

Risk note: with a real LLM, model can technically write *attacks* that read as helpful coaching. There's no adversarial test against a real model yet. Flagged in §"what remains unproven".

## 4. Operator Profile is qualitative, not a score

- No field named `score`, `points`, `level`, `rating`, `percent`, `accuracy` exists anywhere in profile builders.
- Dimensions are qualitative tags: `false_click_bias`, `absence_blindness`, `selection_bias`, `register_blindness`, `transfer_accuracy`, etc.
- The Profile route renders dimensions as key/value rows without progress bars.
- The Markdown export uses bullets and bold tags, not totals.

Tested via `test_real_*_full_flow` which assert tag identity, not numeric thresholds.

## 5. Replay mutation is actionable

Before Phase 2, `replay_targets` was a bare tag like `pseudo_depth`. That is consumable by a mutator but unreadable for a human, and easy to drift into "improve attention" if the wrapper layer is ever added carelessly.

Phase 2 adds `replay_directives: list[str]` — sentence-shaped instructions, e.g.:

- *"next round: increase pseudo-depth phrases that imply more than they commit to — you fell for this shape"*
- *"next round: hide a different absence type — you already track logical leaps; suppress a subject or criterion next"*
- *"next round: return three previously cut cards as confirmed sprouts — you cut too hard"*
- *"next round: add a phrase that only works as a joke — verify you no longer flatten it into a command"*

The test `test_replay_directive_is_actionable_sentence` enforces:

- non-empty,
- ≥25 chars,
- no banned strings (`try harder`, `be more precise`, `improve attention`, `do better`),
- presence of a concrete verb (`increase`, `hide`, `stage`, `return`, `salt`, `include`, `force`, …).

## 6. What was earned vs. what is still risk

### Earned

- Cycle is real, end-to-end, and tested with real-namespace seeds for all four games.
- Genome is the only configuration surface; no per-game branching in the runtime.
- LLM roles are structurally non-assistant.
- Profile is qualitative, with game-specific dimensions matching spec §6.6.
- Replay directives are actionable sentences, not adjectives.
- Real materials are in their own namespace, surfaced in the Play picker.

### Unproven

- **Real-LLM adversarial behaviour.** Mock is deterministic. With a real model, role drift toward assistant tone is the most likely failure mode. Mitigation: system prompt + JSON enforcement; tested only at mock layer.
- **Cross-app Operator Profile.** Spec §4 envisions a single Operator Profile after all 4 games. Right now profiles are per-session. Aggregation page does not exist; not in Phase 2 scope.
- **Replay actually executing.** The mutator is a *labeller* of the next round, not a transform of the next material. To honour a directive like "increase pseudo-depth nodes", the material generator/curator must use the directive. This is named, not built.
- **Human playtest.** All evidence is from synthetic moves. The first real human session is in Phase 3.

### Failure modes the runtime now actively resists

- Chatbot drift: `test_llm_roles_remain_non_assistant`.
- Edtech quiz drift: no numeric score field exists; all dimensions are categorical.
- Generic prompt-trainer drift: every game has a *specific* field type and a specific organ role.
- Over-abstract platform drift: this is still 4 games + 1 runtime + 1 JSON schema, not a marketplace.
- Slop summary drift: replay directives are concrete next-round operations, not pep talks.

## 7. Verdict

Ready for first human playtest on the real seeds. See [PLAYTEST_PROTOCOL_PHASE_2.md](PLAYTEST_PROTOCOL_PHASE_2.md).
