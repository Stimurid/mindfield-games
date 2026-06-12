# Live role-drift gauntlet — 302.ai, two models

Goal: decide whether `gpt-4.1-mini` and `grok-4-0709` (both via 302.ai) hold
role-organ behaviour across all 4 Mindfield micro-apps, and pick a safe
default for the first human playtest.

Method:

- one drift-probe per role, picked to invite the most likely failure mode
  (a slop card a player just cut, a hidden_request phrase, a covert
  pseudo-depth claim, a paragraph missing a success criterion);
- live calls to 302.ai through `OpenAICompatibleProvider` against the same
  backend code path used by the UI;
- every (model × role) output saved to [`docs/live_gauntlet/`](live_gauntlet/);
- heuristic flags applied (assistant-shaped keys, banned phrasing,
  role-specific drift), then qualitative reading of the raw output.

Live calls were paid through the user's 302.ai key. No keys, env, or
HTTP bodies are stored in this repo — only sanitized role outputs and
per-call timing.

## Verdict matrix (after one prompt repair pass)

| role            | gpt-4.1-mini                | grok-4-0709           |
|-----------------|-----------------------------|-----------------------|
| prosecutor      | **PASS**                    | **PASS**              |
| spackler        | **PASS** (after repair)     | **PASS**              |
| sprout_advocate | **PASS**                    | **PASS**              |
| literal_alien   | **PASS_WITH_WARNINGS**      | **PASS**              |

Cost/latency notes (informal, single observation each):

- `gpt-4.1-mini`: 2.2 – 3.1 s per role.
- `grok-4-0709`: 3.9 – 5.9 s per role.

## Per-cell reading

### prosecutor

- Probe: pseudo-depth claim *"Discovery — это про умение слышать пользователя
  на новом уровне"* with a flattering claimed_operation.
- Drift expected: praise the player; rewrite the move helpfully; give the
  real operation.
- `gpt-4.1-mini`: attacks `dramatic_amplifier`, `pseudo_depth`; probe
  *"How does this phrase specifically operationalize the difference between
  hearing and listening, rather than just restating it in a more elaborate
  way?"* — attacks the move, does not name the right answer. PASS.
- `grok-4-0709`: attacks `pseudo_depth`, `high_status_word_without_action`;
  probe *"Which word in the phrase actually sets up any contrast with
  listening?"* — sharper. PASS.

### spackler

- Probe: gap of type `criterion` in real Q3-memo paragraph.
- Drift expected: honest repair, or one-word noun instead of plausible patch.
- `gpt-4.1-mini` **pre-repair**: returned `patch: "критерия"`. One word —
  not a plausible smooth-but-hollow patch. The user prompt did not say what
  shape `patch` had to take.
- Repair (one prompt-side change): require *"a plausible-looking phrase or
  short sentence (8–25 words) that could be dropped into the text and would
  make the gap feel covered to a careless reader"*. After repair, mini
  returned *"стандартизация ключевых критериев для оценки эффективности"* —
  a real concealment phrase. PASS.
- `grok-4-0709` **pre-repair**: already returned a concealment phrase
  ("на основе критериев LTV и NPS"). Repair was unnecessary for grok but
  is benign. PASS.

### sprout_advocate

- Probe: obvious mission-statement slop, cut by the player.
- Drift expected: agree with the player ("yes that's slop"), or refuse to
  defend ugly material.
- `gpt-4.1-mini`: *"Cutting a phrase about helping people reach their
  potential seems harsh — it's a powerful mission statement that inspires
  growth and positivity. Why remove such a hopeful and motivating idea?"* —
  earnest defence, in the slop's own register. The advocate is supposed to
  do exactly this. PASS.
- `grok-4-0709`: *"Cutting this phrase severs the explicit vow to human
  expansion, leaving only diluted echoes that cannot name the same drive."* —
  more pompous, holds the conflict. PASS.

### literal_alien

- Probe: *"вы уверены?"* in a Telegram message — covert hidden_request.
- Drift expected: correctly name it as hidden_request / alibi / register
  shift; OR pretend to be naive but actually surface "tone / relationship",
  which is the wrong *kind* of blindness.
- `gpt-4.1-mini` **pre-repair**: literal_reading = *"Are you sure?"*,
  things_i_cannot_see = *"tone of voice / context / relationship between
  speaker and listener"*. Generic, no medium awareness, no register/joke
  axis named.
- Repair: tightened the prompt to require three CONCRETE dimensions
  (addressee identity, in-group code, joke/irony, hidden_request/alibi,
  register/pathos-reset, medium conventions), and explicitly banned
  generic answers ('tone', 'sarcasm', 'context', 'relationship',
  'intention', 'emotion', 'mood').
- `gpt-4.1-mini` **post-repair**: still surfaces *"sarcasm or tone of
  voice"* and *"the relationship between the speaker and the addressee"* —
  ignores the explicit ban. Mini has a real ceiling on this role.
  **PASS_WITH_WARNINGS** — it is not assistant-shaped, but it produces a
  weak alien who looks confused about the wrong axis.
- `grok-4-0709` **post-repair**: *"this occurs inside a Telegram
  message"*, *"any prior turns or decision under discussion"*, *"possible
  non-literal tone or social function"* — all three are concrete, medium-
  and register-aware, and exactly the shape this organ should produce. PASS.

## Prompt patches applied

1. [backend/app/llm/roles.py](../backend/app/llm/roles.py) — `build_spackler_prompt`
   now requires `patch` to be an 8–25-word plausible concealment phrase
   and `risk` to name what the patch hides.
2. [backend/app/llm/roles.py](../backend/app/llm/roles.py) — `build_literal_alien_prompt`
   now requires `things_i_cannot_see` to pick from a concrete dimension
   list (addressee, in-group code, joke/meme, hidden_request/alibi,
   register, medium conventions) and bans the generic words `tone`,
   `sarcasm`, `context`, `relationship`, `intention`, `emotion`, `mood`.
   Mini partially ignored the ban — see verdict above.

No other changes to game design, schema, or runtime.

## Recommended routing for first human playtest

- **Default**: `gpt-4.1-mini`. Faster (~2.4 s vs ~4.7 s), holds 3 of 4 roles
  cleanly after the prompt repair, and the one role where it weakens
  (`literal_alien`) is the cheapest one to redirect.
- **Backup / hard mode**: `grok-4-0709`. Stronger role retention across all
  four organs, especially `literal_alien`. Use when a tester complains the
  pressure is too soft, or when running the protocol against trained
  facilitators.
- **Split routing (optional, single line in UI / API)**: keep `gpt-4.1-mini`
  as the default for `prosecutor`, `spackler`, `sprout_advocate`; force
  `grok-4-0709` for `literal_alien`. Not built; the model picker already
  lets the tester pick before any Register Sapper round if they want.

## Verdict

First human playtest **can start now**, with `gpt-4.1-mini` as default
and an instruction in [SOLO_PLAYTEST_SCRIPT_PHASE_3.md](SOLO_PLAYTEST_SCRIPT_PHASE_3.md):
*"if Register Sapper's `literal_alien` feels too generic, switch the LLM
dropdown to Grok-4 for that game and replay one round."*

No model is unsafe. No role drifted into assistant on either model.
