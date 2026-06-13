# Full-Cycle Playtest V1 · Mindfield RC-0

This protocol tests **the whole machine**, not the four micro-apps. One playtester, one
observer. Total: 90 minutes (60 active + 30 reflection). The observer never coaches.

## Pre-flight (observer alone, 10 min before the player arrives)

- Open [https://mindfield.mindkampf.ru](https://mindfield.mindkampf.ru) in a fresh browser
  profile so the localStorage `player_token` is fresh.
- Confirm in DevTools that `mindfield.player_token` is set on first call to any session
  endpoint.
- Confirm in the active-model badge that the right model is auto-selected for the chosen
  game (Register Sapper / Assistant as Foreign → `grok-4-0709`, others → `gpt-4.1-mini`).
- Open `/library`, `/triage`, `/configurator`, `/operator` in 4 tabs. Confirm all 4 load.
- Pre-pick **one** raw `source_card` from the library (recommended: a card in `src_section_I`
  that the observer can roughly characterize ahead of time, e.g. `1. Пальцы` or `5. Хромая
  обезьяна`). Note the card's title, body, and the observer's pre-session guess of which
  fate would fit (just write it on paper; this is your control).

The observer does NOT show the player any of this setup.

## Session window (60 minutes with the player)

### Step 1 — Triage one raw card (10 min)

Player opens `/triage`, sees the queue. Observer points only at "this is the queue of cards
that need a fate". No further explanation.

Player picks the first card in the queue (this can be different from the observer's
pre-pick — that's fine). They read it, assign a fate from the 9-button menu, optionally
type a note.

If they pick `extract_organ`:
- they choose a bank and name the organ.
- observer notes the bank and the name verbatim.

If they pick any other fate: observer notes the fate.

**Observer fields:**

| Field | Recording |
|---|---|
| card chosen | code + title |
| fate selected | one of 9 |
| seconds until first click | |
| where player hesitated | the timestamp + what they re-read |
| in their own words, what does this fate mean? | one sentence from the player |
| if extract_organ: bank + organ name | |

### Step 2 — Inspect organ bank growth (5 min)

Open `/configurator` in a new tab. Player navigates to the bank they extracted into (or
any bank if no extraction in step 1).

**Observer fields:**

| Field | Recording |
|---|---|
| did the player FIND the new organ? | yes / no — note search time |
| does the new organ visibly differ from canonical ones? | observer reads the description; player reads the chip |
| player one-sentence answer to "what does this organ do?" | |

### Step 3 — Choose game route (5 min)

Two paths. Let the player pick which path they prefer; the observer does not steer.

**Path A — Use the configurator.** Player assembles a draft genome by picking organs from
banks. Name, function, verb, maturity stage. Run GameWeaver. Read the verdict.

**Path B — Open one of the 12 canonical жанров.** Player goes to Home, picks any game, lets
the page open it with the default real seed.

If Path A: **the observer notes the GameWeaver verdict and critique sentence.** If the
verdict is `not_playable_yet` or `rotten`, the player must either fix the draft or fall
through to Path B; either way is fine evidence.

If Path B: the observer notes which game and which model was auto-selected.

**Observer fields:**

| Field | Recording |
|---|---|
| chosen path (A or B) | |
| if A: GameWeaver verdict + critique sentence | |
| if A: did the player adjust the draft? | yes / no |
| if B: game chosen + model on the active badge | |
| player's one-sentence answer to "what kind of pressure do you expect?" | |

### Step 4 — Play one live session (15 min)

Player plays. Observer does NOT explain anything in the field. If the player asks "what
do I do here?", the observer reads back the round instruction verbatim and stops.

**Observer fields (during play):**

| Field | Recording |
|---|---|
| seconds from material load to first move | |
| how many LLM interventions did the player invoke? | |
| did any LLM output start to sound like coaching? | yes / no + which turn |
| did the player read the TracePanel between turns? | yes / no |
| where did the player most visibly hesitate? | timestamp + which decision |
| **after each LLM intervention:** player's one-line reaction (recorded verbatim) | |

When the session completes, Profile page loads.

### Step 5 — Inspect Operator Profile (5 min)

Player reads the per-session profile (dimensions + replay directive). Observer says only:
"take 2 minutes, read it."

**Observer fields:**

| Field | Recording |
|---|---|
| did the profile feel specific or generic? | specific / partial / generic + WHY in one line |
| which dimension landed for the player? | name the key + value |
| which dimension landed as wrong? | name the key + value |
| player's one-sentence answer to "did this name a real pattern you have?" | |

Then player opens `/operator` (the cross-game page). Even if only one game has been
played, the page renders with one card. Observer notes whether the player navigated there
on their own or had to be pointed at it.

### Step 6 — Read and act on the replay directive (5 min)

Back on the per-session profile, the player reads the directive in the bordered block at
the bottom.

**Observer asks, verbatim:**
> "Before you press the button — predict in one sentence what the next material will
> look like differently."

Record the prediction. Then the player presses `Сыграть мутировавший раунд`.

### Step 7 — Play the second (mutated) session (15 min)

Player plays the new material end to end. Observer DOES NOT compare the prediction to
the material yet — just watches.

**Observer fields:**

| Field | Recording |
|---|---|
| seconds from material load to first move (compare to step 4) | |
| how many LLM interventions this time? | |
| did the player visibly notice the SAME pattern from step 4 in the new material? | yes / no + timestamp |
| did the player change strategy mid-session? | yes / no + how |
| second-session profile dimension that moved relative to step 4 | name the key + before-after |

Session completes. Profile page loads for the second time.

### Step 8 — Reflection (5 min in-session)

Observer asks, in order, **without interpreting**:

1. "What did you think you were doing in this session?"
2. "What did this game force you to do that a chat with ChatGPT does not?"
3. "Was the LLM an organ or an assistant? In which moment specifically?"
4. "Was the second material actually harder along the axis the directive named, or
   different on a different axis?"
5. "Name one operation you can do now that you couldn't before. Or say 'none'."

Record VERBATIM. Do not paraphrase. If the player says "none" or "I don't know", that
is the evidence; do not try to extract a better answer.

## Out-of-session reflection (24h–48h later)

The observer reaches out within 1–2 days and asks **one** question, no preamble:

> "Tell me one situation in the last 24 hours where you noticed what you trained, without
> me prompting you. Or say 'none'."

Record the answer VERBATIM. This is the C2 transfer evidence.

## Maps to Unproven Claims

| Step | Claim addressed |
|---|---|
| 1 | C5 — triage fate quality at scale (single observation; many cards in V2) |
| 1 + 2 | C5 + C8 (player understanding action) |
| 3 (if A) | C4 — draft genome playability |
| 4 | C6 — LLM role stability under real load; C8 in real time |
| 5 | C7 — Operator Profile usefulness |
| 6 + 7 | C3 — replay improves the player; C8 in second session |
| 8 | C1 — psychotechnical function formation |
| 24h | C2 — transfer outside the app |

## Observer's filled-in sheet template

Make a copy of this section for each playtest. **Verbatim entries are required;** paraphrase
is not evidence.

```
Player code (pseudonym): ____________________________
Date / time start: ____________________________
Browser: ____________________________
Active model on game: ____________________________
Pre-pick fate guess (observer only): ____________________________

STEP 1 — TRIAGE
  card_code:
  card_title:
  fate_selected:
  seconds_to_first_click:
  hesitation_notes:
  player_says_fate_means:                 // verbatim
  if extract_organ: bank/name:

STEP 2 — BANK GROWTH
  found_extracted_organ: y/n in __s
  organ_visible_difference: y/n + note
  player_says_organ_does:                 // verbatim

STEP 3 — ROUTE CHOICE
  path: A/B
  weaver_verdict_if_A:
  weaver_critique_if_A:
  adjusted_draft_if_A: y/n
  game_if_B:
  model_if_B:
  player_expects_pressure:                // verbatim

STEP 4 — SESSION 1
  time_to_first_move: __s
  intervention_count:
  any_assistant_drift_turn:
  read_trace_panel: y/n
  hesitation_timestamps:
  reaction_after_intervention_1:          // verbatim
  reaction_after_intervention_2:
  reaction_after_intervention_3:
  ...

STEP 5 — PROFILE
  felt_specific_or_generic:
  landed_dimension:
  wrong_dimension:
  player_says_pattern_real:               // verbatim

STEP 6 — REPLAY PREDICTION
  player_predicts_next_material:          // verbatim

STEP 7 — SESSION 2
  time_to_first_move: __s
  intervention_count:
  noticed_same_pattern: y/n + when
  strategy_change: y/n + what
  moved_dimension: key, before -> after

STEP 8 — REFLECTION (verbatim)
  Q1 what_did_you_think:
  Q2 what_chat_does_not:
  Q3 organ_or_assistant_moment:
  Q4 harder_on_axis_or_different:
  Q5 one_operation:

OUT-OF-SESSION 24-48h LATER (verbatim)
  situation_or_none:
```

## When to repeat

V1 = one playtester, one cycle. Run V1 with three different playtesters before changing the
protocol. If two of three name an operation at step 8 AND at least one names a situation at
the 24h check, C1 has first evidence and product work can resume on a directed agenda. If
fewer than that, the gap is real and informs the next iteration.
