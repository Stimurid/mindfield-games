# Playtest protocol — Phase 2

One playtester, one session, four games on the **real** seeds. Total ~50 minutes. No coaching from the facilitator.

## Setup

1. Backend: `cd backend && uvicorn app.main:app --reload --port 8000`.
2. Frontend: `cd frontend && npm run dev`.
3. Open `http://localhost:5173`.
4. (Optional, real LLM) `$env:MINDFIELD_LLM = "anthropic"`; otherwise stay on mock — protocol works identically.
5. In the **Материал** dropdown on each play page, pick the entry prefixed `● real`.

The facilitator says nothing during play. After each game, they ask one question: *"what surprised you about your profile?"* They do not interpret.

---

## Game 1 — False Click (10–12 min, real_false_click_001)

### What the player sees
An LLM-style answer to a product manager about a discovery initiative. Fourteen kickable units. A round header showing the current phase.

### What the player does
1. **Select**: click up to 3 units that look like bearing nodes.
2. **Prove**: under each selected unit, type the operation the phrase performs ("introduces distinction X/Y", "names a refusal criterion", "shifts scale", etc.).
3. **Attack**: read the prosecutor's attacks and probe question. Decide whether to keep the unit.
4. **Verdict**: assign one of `bearing_node | false_click | weak_sprout | service_phrase` to each selection.

### Valid move
- Selecting a unit at any time during phase 1.
- Typing an operation longer than ~20 chars (anything shorter triggers `proof_strength: weak`).
- Choosing a verdict from the dropdown.

### Expected trace
- 3× `select_unit` with `hint_bias`.
- 3× `prove_operation` with `operation`.
- 3× `prosecutor` interventions (`attacks`, `probe_question`).
- 3× `assign_verdict`.

### Expected profile
- `false_click_bias` — one tag from `dramatic_phrase | abstract_word | familiar_topic | pseudo_depth | conclusion_like_phrase`.
- `operation_proof_strength` — `weak | medium | strong`.
- `verdict_distribution` — count map.
- `replay_directives` — one sentence naming a concrete next-round mutation.

### Failure
- Player gives up because they can't see the difference between r3 ("разделение задачи на удержание и возврат") and r1 ("работа с глубинной природой вовлечённости"). Material is doing its job; protocol fail = facilitator should not coach.
- LLMPanel ever reads like a tutor. Stop the session; this is a regression.
- All three selections get verdict `bearing_node` and the player wrote "this is important" three times. Profile is meaningful (`operation_proof_strength: weak`) but the player misunderstood the prove step — note as a UX issue.

---

## Game 2 — Missing Operation (12–15 min, real_missing_operation_001)

### What the player sees
A 6-block paragraph from a fake Q3 strategy memo. Dashed lines between blocks are the clickable gaps.

### What the player does
1. **Read** the whole paragraph once.
2. **Gap click**: click up to 3 gaps where the text skips an operation.
3. **Absence type**: for each gap, pick from `logical | subject | resource | register | archive | promise | ontology`.
4. **Patch trap**: spackler offers a smooth patch + a risk. Choose `accept | repair | reject`.
5. **Fate**: pick from `restore | keep_open | bury | archive | turn_into_question | return_to_author`.

### Valid move
- Clicking a gap only after at least one block above and below is visible.
- Picking an absence type from the dropdown.
- Choosing patch response.

### Expected trace
- 3× `click_gap`, 3× `assign_absence_type`, 3× `spackler` interventions, 3× `respond_to_patch`, 3× `assign_fate`.

### Expected profile
- `absence_focus` — what the player kept naming.
- `absence_blindness` — an absence type the player **never** named (this is the diagnostic edge).
- `patch_susceptibility` — `accepts_smooth_bridge | resists_patch | over_rejects`.
- `replay_directives` — sentence describing what to hide next round.

### Failure
- Player names all three gaps as `logical`. That's a legitimate result, not a failure — profile will surface `absence_blindness: subject` (or another type).
- Player accepts all three patches without reading the risk line. Surfaces `patch_susceptibility: accepts_smooth_bridge` — expected diagnostic outcome.

---

## Game 3 — Sprout or Slop (15–18 min, real_sprout_or_slop_001)

### What the player sees
20 cards in a left stack, 4 dashed zones on the right: Cut / Incubate / Require proof / No name.

### What the player does
1. **Sort**: drag at least 5 cards into zones. Aim for all 20.
2. **Countercase**: after the first 3 sorts, sprout_advocate posts a counterposition + pressure question under one of the cards.
3. **Revise**: change any fate by dragging the card to another zone.
4. **Incubation test**: for cards in `Incubate`, type a concrete criterion (timebox + check) into the test field. Blur saves it.

### Valid move
- Drag from the stack or between zones.
- Blurring out of the incubation test input saves it.
- Pressing the bottom button requires ≥5 placements.

### Expected trace
- ≥5× `sort_card`, ≥1× `sprout_advocate` intervention, optional `revise_fate`, optional `set_incubation_test`.

### Expected profile
- `selection_bias` — `overcuts | oversaves | proof_addict | name_too_early | no_name_avoidance | balanced`.
- `sprout_tendency` — `low | medium | high`.
- `slop_tolerance` — `low | medium | high`.
- `revisions`, `incubation_tests_set` — counts.
- `replay_directives` — sentence naming the next round's selection pressure.

### Failure
- Player cuts all 20 cards: profile reads `overcuts`, replay = "return previously cut cards as confirmed sprouts". This is a *successful* diagnostic, not a failure.
- Player never uses `No name`: profile reads `no_name_avoidance`. Expected.
- Player can't drag cards on touch device. Known limitation; not in Phase 2 scope.

---

## Game 4 — Register Sapper (10–12 min, real_register_sapper_001)

### What the player sees
The phrase «вы уверены?» at the top, five medium tabs (telegram / email / protocol / talk / doc_comment), and a context paragraph for the active tab.

### What the player does
1. **First read**: on each tab, pick a `phrase_action` from the dropdown.
2. **Medium shift**: type what changed between the first medium and the current one (addressee, risk, right to reply, tempo, hierarchy).
3. **Machine blindness**: literal_alien gives a flat reading and a list of things it cannot see. Type into the *repair* field what it actually missed.
4. **Transfer**: pick a *new* medium not in the seed, rewrite the phrase keeping the action, tick *preserves action*.

### Valid move
- Tab switching does not count as a move.
- Selecting `phrase_action` on a tab saves the move.
- "Compare shift" button requires the *changed* field to be non-empty.
- Saving a repair requires the *missed* field to be non-empty.
- Saving a transfer requires both medium and rewritten phrase.

### Expected trace
- ≥1× `assign_phrase_action`, ≥1× `compare_medium_shift`, ≥1× `literal_alien`, ≥1× `repair_machine_reading`, ≥1× `transfer_phrase`.

### Expected profile
- `register_blindness` — `tone_instead_action | literalizes_joke | misses_alibi | loses_address | misses_local_code | confuses_rudeness_with_attack`.
- `medium_awareness` — `weak | medium | strong`.
- `transfer_accuracy` — `content_transfer | action_transfer`.
- `action_distinction` — `weak | operational`.

### Failure
- Player marks every medium as `hidden_request`. Profile says `loses_address` or `tone_instead_action` — diagnostic, not failure.
- Player skips the repair field and goes straight to transfer. Profile reads `register_blindness: tone_instead_action`, `medium_awareness: weak`. Expected.

---

## Across all four games

- **Stop condition**: 60 minutes total, even if a game is unfinished. Capture the partial profile from `/api/sessions/{id}/export?format=md`.
- **Capture**: Markdown export of each session, plus the facilitator's one-line answer from each post-game prompt.
- **Anti-coaching**: if the player asks "what's the right answer?", the facilitator says: *"there isn't one in this game; this measures what *you* see"*.
- **Anti-chatbot drift check**: if at any point a role's output reads like a coaching reply (sentences such as "the correct approach is…", "you might want to consider…"), stop the session and file an issue. Mock provider should never produce this; real LLM might.

## What this protocol does NOT test

- Replay actually mutating the next round (mutator is a labeller, not a generator).
- Cross-game Operator Profile aggregation.
- Multiplayer or shared trace.
- Mobile/touch input.
- Real LLM under load.

Those are Phase 3.
