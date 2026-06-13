# Mindfield RC-0 · Unproven Claims Register

These claims **must NOT be treated as proven** at RC-0. Each one is the kind of thing that
sounds true from the architecture, sounds true from the green test count, sounds true from
the smoke output — and is not true until a human cycle confirms it.

Each entry: claim · evidence currently available · evidence missing · minimal playtest
observation that would change the verdict.

---

## C1 — The games form psychotechnical functions in a human

**Claim:** after playing one of the 12 жанров, the player can perform an operation in the
world that they could not perform before, and they can do it WITHOUT the app.

**Evidence available:**
- per-genre real seeds carry the expected play shape (4 real LLM organ verdicts;
  4 absence types; 4 sorting zones; 4 false-consensus zones; etc.);
- automated tests confirm the cycle produces a qualitative profile dimension matching
  the canonical name (e.g. `false_click_bias: pseudo_depth` on the False Click real seed).

**Evidence missing:**
- any observation of a player using the operation OUTSIDE the app within ≥24 hours of
  the session;
- any observation that the player can NAME the operation without referencing the game
  vocabulary;
- any observation that the operation survives in a different context (different text /
  different medium / different topic).

**Minimal playtest observation:**
> 24h–48h after playing False Click on the real seed, the player is shown an unrelated
> LLM answer and asked: "what kind of fail does this have? what's the operation?". They
> must name the bias type without prompting from the observer and without re-reading
> their .md export.

---

## C2 — Transfer outside the app

**Claim:** the trained operation transfers to a substrate the game did not stage —
voice, group meeting, document review, code review, conversation.

**Evidence available:**
- the medium_shift_phrase field and the Ontology Customs porода explicitly stage
  transfer as the gameplay verb;
- the test `test_block3::test_ontology_customs_full_flow` asserts the trace records
  a transfer move with `preserves_action=True`.

**Evidence missing:**
- any observation that operations trained in False Click (clickable text)
  carry into Register Sapper (medium variants), and from there into actual chat
  or meeting practice;
- any observation that the player initiates the operation unprompted.

**Minimal playtest observation:**
> Within one week of completing the full cycle, the observer asks: "tell me one
> situation in this week where you noticed what you trained, without us prompting
> you." A YES requires the player to name the SITUATION, the OPERATION, and what they
> would have done before. NO answer or vague answer = transfer unproven.

---

## C3 — Replay improves the player, not only mutates text

**Claim:** the second session, played on a mutated material, EXERCISES the weakness named
by the directive — and the player's profile on the second session reflects movement on the
named axis.

**Evidence available:**
- `material_mutator` returns a structurally valid new material with the same field_type
  schema as the parent (all 12 жанров);
- the new material's `mutation_directive` is persisted alongside `parent_id` for trace.

**Evidence missing:**
- no test asserts that the CONTENT of the new material amplifies the directive's named
  axis (e.g. "more pseudo-depth phrases that imply more than they commit to");
- no observation that the player's second-round profile DIFFERS from the first round in
  the direction the directive predicted (e.g. `operation_proof_strength` shifts from
  `weak` to `medium`).

**Minimal playtest observation:**
> Player plays a real seed of any жанр. After completion they read the directive and
> the observer asks them to predict, in one sentence, what the next material will do
> differently. The player plays the mutated material. The observer compares (a) the
> player's prediction to (b) the actual new material content and (c) the new profile.
> The cycle counts as proving C3 only if (a)≈(b) AND the new profile shows movement
> on the axis named in (a).

---

## C4 — Generated draft genomes are playable on humans

**Claim:** drafts produced by `chimera_weaver` from any of the 40 chimera cells can be
opened in the configurator and the playability verdict reflects what a human player would
say.

**Evidence available:**
- `test_block4_chimera::test_chimera_draft_runs_through_weaver` confirms that the
  chimera-generated draft passes `playability_critic = playable` when sufficient banks
  are populated;
- live smoke (`smoke_chimera.py`) produced a draft `Сминёр` for `Смысловой клик × Антислоп`
  with a credible function and verb.

**Evidence missing:**
- the configurator does not yet expose a "promote draft to runtime genome" path —
  the design loop ends at `playable` verdict, not at a playable session;
- no human has attempted to TURN a chimera-generated draft INTO a session and play it;
- the LLM-named organs in the draft are not validated against the canonical bank's
  intent — only their existence in the bank is checked.

**Minimal playtest observation:**
> A designer-player picks one chimera cell, generates a draft, opens it in the
> configurator, and answers (without help): "could I run a 30-minute session from
> this draft right now?" — naming material type, the bearing move, and one expected
> failure mode. If they can answer all three, C4 has first evidence.

---

## C5 — Triage fate quality at scale

**Claim:** the 9 §4 fates remain meaningful as the player works through 4 200 cards.
A fate assignment in card #2 014 is as load-bearing as one in card #14.

**Evidence available:**
- per-card automated test of the fate API surface;
- the fate menu is canonical (matches §4 of the spec);
- triage UI is the same for every card.

**Evidence missing:**
- no observation that fate distribution stabilizes after a meaningful number of cards
  (does the player just spam `keep_seed` after 100 cards?);
- no observation that the EXTRACTED organs from triage end up actually USED in
  configurator drafts (i.e. that organ extraction is connected to design action and
  not just to bank growth).

**Minimal playtest observation:**
> One playtester triages 50 cards in one sitting. The observer records:
> · fate distribution per 10-card window — does the player keep using the full menu,
>   or does it collapse to 1-2 fates after the first 20 cards?
> · how many of the cards triaged as `extract_organ` lead to an actual organ being
>   selected by the same player in a configurator draft within the same session?

---

## C6 — Live LLM role stability over long sessions

**Claim:** the four organ roles (`prosecutor`, `spackler`, `sprout_advocate`,
`literal_alien`) hold their role contract across many turns within one session and
across many sessions on the same player.

**Evidence available:**
- `test_phase2::test_llm_roles_remain_non_assistant` (mock provider only — deterministic);
- `smoke_user_phrase.py` shows a single-turn prosecutor on `gpt-4.1-mini` and `grok-4-0709`
  producing in-language attacks that quote the player's claim;
- Phase 3A gauntlet doc records that `grok-4-0709` outperforms `gpt-4.1-mini` for
  `literal_alien` over a small N.

**Evidence missing:**
- no automated test of role behavior under live LLM;
- no observation of role behavior under >5 interventions in the same session;
- no observation of role drift across model versions over weeks.

**Minimal playtest observation:**
> One playtester runs a 25-turn session in False Click, each turn pressing the
> prosecutor again on different units. Observer records:
> · does the attack stop quoting the player's text after turn N?
> · does the probe_question ever turn into a coaching question?
> · does the JSON contract ever break?

---

## C7 — Usefulness of cross-game Operator Profile

**Claim:** the `/operator` page's named cross-pattern callouts (e.g. "глубина-форма по
обоим контурам: вход — pseudo-depth, выход — сохранение dead beauty") tell the player
something they did not already know, and they can act on it.

**Evidence available:**
- the aggregator produces structured per-game dimensions and named patterns when
  prerequisite games are played;
- the pattern list is hand-written, not statistical (avoiding the worst Barnum failure).

**Evidence missing:**
- no observation that a player who has played 2+ games READS the cross-pattern panel;
- no observation that the player CONFIRMS the pattern when shown it;
- no observation that the player NAMES a behavior outside the app that the pattern
  predicts.

**Minimal playtest observation:**
> Two games played on real seeds. Observer asks: "before you look at the page, what
> do you think your profile says about how you read?" Then opens `/operator`.
> Player reads. Observer asks: "anything correct? anything wrong? anything new?"
> Score is qualitative — the page passes if at least one named pattern lands as
> "correct AND new".

---

## C8 — Players understand what action they are performing

**Claim:** at every step of every game, the player can NAME the action they are
performing in their own words, without referring to the genome.

**Evidence available:**
- field renderers were patched (Phase 14 from playtest screenshots) to add verbose
  explanations of what `bearing_node` / `weak_sprout` / `false_click` / `service_phrase`
  mean as defenses;
- TracePanel labels each action with a "what this changed" sentence;
- LLMPanel labels the organ as "NOT an assistant".

**Evidence missing:**
- no observation that the player can name the action while playing;
- no observation that the player can name the action AFTER playing;
- no observation that the player would describe the action differently from the
  observer's description (a "yes I get it" might mean "I read the words" not "I see
  the operation").

**Minimal playtest observation:**
> Mid-session, the observer pauses the player and asks: "right now, what are you
> actually doing? what would happen if you did it badly?" The action recognized
> must be the verb in the genome's `player_actions`. If the player names a different
> action ("I'm picking the smart one"), the action was unclear despite the verbose
> labels.

---

## Summary

| Claim | Code-side evidence | Smoke evidence | Playtest evidence |
|---|---|---|---|
| C1 — psychotechnical function | partial | — | NONE |
| C2 — transfer outside app | partial | — | NONE |
| C3 — replay improves the player | weak | single genre | NONE |
| C4 — draft genomes playable | structural | one chimera cell | NONE |
| C5 — triage fate quality at scale | structural | — | NONE |
| C6 — LLM role stability long-form | mock only | single-turn | NONE |
| C7 — Operator Profile usefulness | structural | — | NONE |
| C8 — players know their action | label-only | — | NONE |

Until at least the first three are addressed by playtest evidence, RC-0 must not be
treated as a finished product. The protocol that addresses every one of these in a single
session is [`docs/playtests/FULL_CYCLE_PLAYTEST_V1.md`](../playtests/FULL_CYCLE_PLAYTEST_V1.md).
