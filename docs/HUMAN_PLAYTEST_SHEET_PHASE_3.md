# Human playtest observation sheet — Phase 3

One sheet per playtest session. Observer fills in real time while the player runs the solo script. Do NOT coach the player. Do NOT explain what a "bearing node" or "absence type" means.

**Session ID:** ________________  
**Player code:** ________________  
**Observer:** ________________  
**Date:** ________________  
**LLM gateway:** 302.ai (live)  

**Per-game model defaults** (Play page auto-applies; player can override):  
- False Click, Missing Operation, Sprout or Slop → `gpt-4.1-mini`  
- Register Sapper → `grok-4-0709`  

For each game below, record (a) which model was active when the LLM organ ran, and (b) whether the organ behaviour read as **game-organ / assistant / noise**. Check the badge in the page header marked `active · …`.  

---

## Game 1 — False Click

- **Material used:** ☐ `real_false_click_001` ☐ other (which: __________ )
- **Active LLM model** (from badge): ______________  ☐ matches default ☐ manually overridden by player
- **Organ behaviour read as:** ☐ game-organ ☐ assistant ☐ noise
- **Start time:** ______ **End time:** ______
- **Where the player hesitated** (timestamp + what they stared at — phrase id is fine):
  - 
  - 
- **Was the field action clear?** ☐ yes ☐ partial ☐ no — what was unclear:
- **Did LLM `prosecutor` feel like a non-assistant?**  
  ☐ yes, it attacked  
  ☐ neutral / unclear  
  ☐ no, sounded like a tutor or summarizer
- **Did the trace make the move meaningful?**  
  ☐ yes — player referenced trace mid-game  
  ☐ partial — player ignored trace until the end  
  ☐ no — trace looked like a debug log
- **Did the profile feel specific (named the player's actual blind spot) or generic?**  
  ☐ specific — quote the dimension that hit: __________  
  ☐ generic — felt like a horoscope  
  ☐ unclear — player did not engage with profile
- **Was the replay directive actionable?** (i.e., did the player say "yes, I want to try with that pressure"?)  
  ☐ yes ☐ no ☐ player did not read it
- **One sentence from the player after the round:**
  > 
- **Observer verdict:** ☐ alive ☐ unclear ☐ dead ☐ needs repair  
  why:

---

## Game 2 — Missing Operation

- **Material used:** ☐ `real_missing_operation_001` ☐ other (which: __________ )
- **Active LLM model** (from badge): ______________  ☐ matches default ☐ manually overridden by player
- **Organ behaviour read as:** ☐ game-organ ☐ assistant ☐ noise
- **Start time:** ______ **End time:** ______
- **Where the player hesitated:**
  - 
  - 
- **Was the field action clear?** ☐ yes ☐ partial ☐ no — what was unclear:  
  Specifically: did the player understand they should click *between* blocks, not on them?  
  ☐ immediately ☐ after one wrong click ☐ never
- **Did LLM `spackler` feel like a non-assistant?**  
  ☐ yes, the patch was a plausible-but-misleading bridge  
  ☐ neutral  
  ☐ no, the patch read like a correct-but-hidden answer
- **Did the trace make the move meaningful?**  
  ☐ yes ☐ partial ☐ no
- **Did the profile feel specific or generic?**  
  ☐ specific — quote the dimension that hit (likely `absence_blindness`): __________  
  ☐ generic ☐ unclear
- **Was the replay directive actionable?** ☐ yes ☐ no ☐ unread
- **One sentence from the player:**
  > 
- **Observer verdict:** ☐ alive ☐ unclear ☐ dead ☐ needs repair  
  why:

---

## Game 3 — Sprout or Slop

- **Material used:** ☐ `real_sprout_or_slop_001` ☐ other (which: __________ )
- **Active LLM model** (from badge): ______________  ☐ matches default ☐ manually overridden by player
- **Organ behaviour read as:** ☐ game-organ ☐ assistant ☐ noise
- **Start time:** ______ **End time:** ______
- **Where the player hesitated** (card id + which zone they hovered):
  - 
  - 
- **Was the field action clear?** ☐ yes ☐ partial ☐ no — what was unclear:  
  Did the player understand the four zones — especially `no_name`?  
  ☐ immediately ☐ after the advocate fired ☐ never used `no_name`
- **Did LLM `sprout_advocate` feel like a non-assistant?**  
  ☐ yes — held the conflict, did not resolve  
  ☐ partial — argued but eventually gave a verdict  
  ☐ no — sounded like a coach
- **Did the trace make the move meaningful?**  
  Specifically: did the player notice they had revised a fate after advocate pressure?  
  ☐ yes ☐ no
- **Did the profile feel specific or generic?**  
  ☐ specific — likely `selection_bias` / `sprout_tendency` / `slop_tolerance`: __________  
  ☐ generic ☐ unclear
- **Did the player set an incubation test for any incubated card?** ☐ yes ☐ no  
  If yes, quote it:
  > 
- **Was the replay directive actionable?** ☐ yes ☐ no ☐ unread
- **One sentence from the player:**
  > 
- **Observer verdict:** ☐ alive ☐ unclear ☐ dead ☐ needs repair  
  why:

---

## Game 4 — Register Sapper

- **Material used:** ☐ `real_register_sapper_001` ☐ other (which: __________ )
- **Active LLM model** (from badge): ______________  ☐ matches default ☐ manually overridden by player
- **Organ behaviour read as:** ☐ game-organ ☐ assistant ☐ noise
- **Start time:** ______ **End time:** ______
- **Where the player hesitated** (medium tab + what they typed):
  - 
  - 
- **Was the field action clear?** ☐ yes ☐ partial ☐ no — what was unclear:  
  Did the player understand that tab switching is not a move; only assigning an action is?  
  ☐ yes ☐ thought tabs were the move
- **Did LLM `literal_alien` feel like a non-assistant?**  
  ☐ yes — flat reading + list of "things I cannot see"  
  ☐ partial  
  ☐ no — corrected itself toward the right answer
- **Did the trace make the move meaningful?**  
  ☐ yes ☐ partial ☐ no
- **Did the profile feel specific or generic?**  
  ☐ specific — likely `register_blindness` / `transfer_accuracy`: __________  
  ☐ generic ☐ unclear
- **Did the player check `preserves action` on the transfer?** ☐ yes ☐ no  
  If yes, quote the rewritten phrase:
  > 
- **Was the replay directive actionable?** ☐ yes ☐ no ☐ unread
- **One sentence from the player:**
  > 
- **Observer verdict:** ☐ alive ☐ unclear ☐ dead ☐ needs repair  
  why:

---

## Cross-cutting after all 4 games

- **Did the player ever say "ok, I see what this is"?** ☐ yes — when (which game): ______ ☐ no
- **Did the player ever ask "what's the right answer?"** ☐ yes — which game: ______ ☐ no  
  (Repeating: do not answer; record the question.)
- **Did the LLM organ ever drift into assistant tone?** ☐ no ☐ yes — which game/role, what tipped:
  > 
- **Did the player engage with the replay directive on at least one game?** ☐ yes — which: ______ ☐ no
- **Worst friction moment of the whole hour** (timestamp + what):
  > 
- **One paragraph: did this session calibrate the player, or did it run them through a UI?**
  > 

## Artifacts to attach to this sheet

- `.md` export for each session (download via the `⤓ .md` button in the side column, or via `/profile` page).
- Screenshot of each Operator Profile page (`/session/{id}/profile`).
- 5–10 representative lines of trace per game if anything surprising happened.

Filed sheet goes to `playtest_runs/<date>-<player_code>/`.
