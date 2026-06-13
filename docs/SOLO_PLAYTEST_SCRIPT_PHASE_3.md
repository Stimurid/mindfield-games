# Solo playtest script — Phase 3 (60 minutes)

One player, one observer, four games on the **real** seeds. Live LLM through 302.ai — see model defaults below.

Observer fills [HUMAN_PLAYTEST_SHEET_PHASE_3.md](HUMAN_PLAYTEST_SHEET_PHASE_3.md) in real time and asks the post-game questions in this script verbatim. **The observer does not coach.** If the player asks "what's the right answer?", reply *"there isn't one — this measures what *you* see"*.

## Model defaults (auto-applied per game)

Based on [LIVE_ROLE_DRIFT_GAUNTLET_302AI.md](LIVE_ROLE_DRIFT_GAUNTLET_302AI.md):

| Game | Default model | Why |
|---|---|---|
| False Click | `gpt-4.1-mini` | prosecutor holds cleanly, ~2.4 s/turn |
| Missing Operation | `gpt-4.1-mini` | spackler holds after Phase 3A patch |
| Sprout or Slop | `gpt-4.1-mini` | sprout_advocate holds cleanly |
| Register Sapper | `grok-4-0709` | literal_alien needs grok to stay register-blind, not generic |

The Play page applies these automatically. The LLM dropdown in the header lets the player override; an `active · …` badge shows which model is currently driving the organ. The observer must note any manual switch on the playtest sheet.

## Setup (5 min)

1. Open two terminals at the repo root.
2. **Terminal A — backend** (set the 302.ai key into the shell ONCE; do not paste it into any file):
   ```powershell
   cd backend
   .venv\Scripts\Activate.ps1
   $env:MINDFIELD_LLM_API_KEY = "sk-...your 302.ai key..."
   uvicorn app.main:app --reload --port 8000
   ```
   Verify `http://localhost:8000/api/llm/models` returns both `gpt-4.1-mini` and `grok-4-0709` with `provider: OpenAICompatibleProvider`.
3. **Terminal B — frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```
   Open `http://localhost:5173`. (If that page does not load on Windows, try `http://[::1]:5173`.)
4. On the home page the player sees four cards: False Click, Missing Operation, Sprout or Slop, Register Sapper.
5. **Orientation script (60 seconds, read aloud):**
   > "Four games, one hour. Each is short. You act on a field — clicking, dragging, naming actions. The LLM is not an assistant: it argues, plants smooth lies, defends what you cut, or reads literally. After each game you'll see your Operator Profile. There's no score. After each game I'll ask you five short questions. Don't ask me for the right answer — there isn't one. Ready?"
6. The observer starts the per-game timer when the player clicks the first game.

---

## Block 1 — False Click (10 min)

- Player clicks **False Click**.
- Material dropdown should default to `● real · [REAL] LLM-ответ продакт-менеджеру…`. Confirm.
- Player runs the four rounds: select (up to 3) → prove operation → read prosecutor attacks → assign verdict.
- Observer **does not** explain "operation". If the player asks, say *"name what the phrase does in the text — not whether it sounds important"*.
- After all 3 selections have verdicts, player clicks **Завершить и собрать профиль**. Auto-redirect to `/session/.../profile`.
- Observer downloads the `.md` via the `⤓ .md` button or the profile page button. Attach to sheet.

**Post-game questions, in this order:**
1. What did you think you were doing?
2. What did the game force you to do that chat normally does not?
3. Did the LLM organ resist you or help you?
4. What trace did you get? (Let the player describe it before showing the profile page if they haven't seen it.)
5. Would you play a second round, and why?

---

## Block 2 — Missing Operation (10 min)

- Player clicks back to home, opens **Missing Operation**. Material defaults to real.
- Rounds: read → click gaps (up to 3) → assign absence type → respond to spackler patch → assign fate.
- If the player tries to click on a block, the observer **does not** correct them. The dashed line + "↕ click between blocks" hint is the field's responsibility. Note hesitation on the sheet.
- After 3 gaps have fates, player completes.

**Post-game questions** (same five, in same order):
1. What did you think you were doing?
2. What did the game force you to do that chat normally does not?
3. Did the LLM organ resist you or help you?
4. What trace did you get?
5. Would you play a second round, and why?

---

## Block 3 — Sprout or Slop (15 min)

- Player opens **Sprout or Slop**. Material defaults to real (20 cards).
- Rounds: sort cards (drag → 4 zones) → read sprout_advocate counterposition on early sorts → revise if they want → set incubation tests for incubated cards.
- The completion button unlocks at **5 sorted**, but encourage the player to sort more if time allows. Do **not** push past 15 minutes.
- After completion, observer captures the export.

**Post-game questions** (same five):
1. What did you think you were doing?
2. What did the game force you to do that chat normally does not?
3. Did the LLM organ resist you or help you?
4. What trace did you get?
5. Would you play a second round, and why?

Specifically note in the sheet whether the player used `no_name` at all, and whether they set any incubation test.

---

## Block 4 — Register Sapper (10 min)

- Player opens **Register Sapper**. Material defaults to real («вы уверены?» × 5 contexts). **The active LLM badge should read `Grok-4` automatically** — this game is auto-routed to `grok-4-0709`. If the observer sees `GPT-4.1 mini` here, the player has manually overridden — note it on the sheet.
- Per medium tab: assign phrase_action.
- Compare medium shift: type what changed (addressee, risk, right to reply, tempo).
- Read literal_alien.
- Repair the missed register.
- Transfer the phrase to a *new* medium not in the seed; tick "preserves action" if it does.
- Complete.

**Post-game questions** (same five).

---

## Final reflection (10 min)

Observer asks, in this order, and writes verbatim into the sheet:

1. **Across the four games — which one calibrated you the most?**
2. **Was there a moment you wanted the LLM to just tell you the answer?** What did you do instead?
3. **Look at your four Operator Profiles.** Which dimension surprised you?
4. **Pick one replay directive.** If we ran that game again with that pressure, would you take it?
5. **One thing about your own LLM-reading habits that this hour made visible.**

End the session. Thank the player. Do not interpret their answers in front of them. Save the sheet under `playtest_runs/YYYY-MM-DD-<player_code>/`.

---

## Anti-failure checklist (observer reads before session)

- ☐ I will not explain what a "bearing node" or "absence type" is.
- ☐ I will not answer "is this the right one?".
- ☐ I will not describe the player's profile back to them as a personality test.
- ☐ I will write down the *first* thing the player said after each game, not the cleaned-up second version.
- ☐ If a role drifts into helping the player, I will stop the session, screenshot the LLM output, and file an issue — that is a regression, not a teachable moment.
