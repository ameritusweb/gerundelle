# Go force world

Started 2026-11-11. A Gerundelle mind plays Go on a 7 x 7 board against random replies. The world is `world.py`, the run is `run.py`. This file keeps the user's decisions apart from what is carried from other domains and what is only my choice.

Read before building: `E:/vscode/analogy/DRIFT.md` (the rules), `civilization/PHYSICS.md`, `mysterymaze/LESSONS_LEARNED.md`, `tetris/README.md`. My choices are also recorded in DRIFT.md.

## Decided (the user)

- **A 7 x 7 board**, in its own folder, built following the principles already laid out.
- **The other colour places random legal stones, with a luck dial:** with chance `luck`, its reply is the one best for the mind.
- **The mind's given territory is its stones and its captures,** as Warp chess's pieces: the stones it places are its own, and stones it takes are its for good. Free points aren't given; they are claimed by play.
- **Luck falls when the mind keeps its stones:** a step each game it loses fewer stones than in the game before.

## Carried from the other domains (settled principles, not new decisions)

- **Grounded in forces, no state machine.** The board changes only when a quantity crosses a reserve (PHYSICS.md, principle 1).
- **Every reading is a doing,** never a state label.
- **Principle 0:** in the slice a stone lands, only its point changes; what follows lands in later slices.
- **Legal-only offers,** each a potential force read from what it reaches (3 where no reserve is left against it, 2 where the reserve holds, 1 reaching nothing).
- **The mind notices changes itself** (`self_noticed`); the world reports no news.
- **Wants come from the ownership slots,** with no goal placed (`own_wants`).
- **No designer reward** (DRIFT.md rule 10): the mind is shown no score.
- **The whole board is perceived,** as tetris's whole well.
- **Each stone reads each of its sides,** as a tetris block does.
- **The mind is tetris's**, which is the maze's: `SovAgent` with `ForceMind` and every switch the user decided on. `run.py` reads the switch set from `tetris/run.py` itself. No switch was added and Gerundelle's code wasn't touched.

## The world as forces

- **Placing** is a push onto a point. A free point has no reserve against it; a point bearing a stone holds.
- **A group** is stones of one colour side by side, bound as a tetris piece's blocks are. The points around it are its breath.
- **Its load** is how many of those points bear a stone of the other colour. **Its reserve** is just under the number of points around it, as a tetris row's is just under the well's width.
- **Coming apart:** when every point around a group bears, the load crosses the reserve. The group's stones leave the board and their points are free again.
- **The stone that lands presses:** the other colour's loads are read first, so a stone may land where its only breath is what it takes. A stone that couldn't hold where it lands isn't on offer.

**What the mind perceives**

| Object | Doings |
|---|---|
| each point (`point_<x>_<y>`) | `free`, `bearing` |
| each stone (`black_<n>`, `white_<n>`) | `resting`, `coming_apart` |
| each side of a stone (`_up`, `_down`, `_left`, `_right`) | `free` (breath), `pressed` (the other colour, or the edge), `binding` (its own colour) |

**A stone's three slices**

1. The stone lands: its point reads `bearing`, and the stone comes into view.
2. The loads are read: the sides of the stones beside it change, and a group whose load crossed reads `coming_apart`.
3. The stones of that group leave.

The other colour replies the slice after. The mind's watch (`horizon`) is 3, so a capture its stone makes falls inside it.

**Force predictions** (`potential_effects`, tetris's): once a stone has landed, each group whose load now crosses is predicted to come apart next slice, with the structure read relative to the stone that landed.

## My choices (each can change)

- Black for the mind, placing first; turns strictly alternate.
- The mind passes by placing nothing for 6 slices on offer. There is no pass push: a pass acts on nothing.
- A game ends when both pass in a row or after 98 stones, and the board is set back empty.
- The rule against taking straight back is written as a rule on what is offered. I found no force reading of it.
- "Best for the mind", for a lucky reply: the other's stones the mind could take next, less the mind's stones the reply takes; then the breath its groups keep.
- Luck starts at 0.7 and falls 0.02 a step, both tetris's numbers.
- Each stone is a new object, never named again. A stone of the mind's that is taken is gone, so it is lost for good. A stone on the board when it is set back is kept: nothing took it.
- The dream is off: which forces a Go dream manipulates isn't decided.

## Open, for the user

- **Whether a lost stone stays lost across games.** As built it does, and every loss is an ownership slot open for good. The register reached 1,939 regions and 1,039 open slots in 1,200 slices, which is what slows the run.
- **Luck against chance.** Losing fewer stones than the game before happens by chance about every other game. Luck falling only on the fewest lost so far would be steadier.
- **Whether a group about to come apart needs its own gerund,** as tetris's `aligning`. Now it is read only through the sides.
- **Tetris's names in Gerundelle.** `SovAgent.force_predict`'s `kind` and `Understanding.ranked` name tetris's roles (`row+`, `run+`, `wall_`). Go's `group+` nodes aren't anchored on the effect's side as tetris's are.

## Checked

`check_world.py`, with no mind:

- A corner stone with one breath left is taken a slice at a time, and only the point changes in the landing slice.
- A stone that couldn't hold isn't on offer, unless it takes what presses it.
- No taking straight back.
- Random legal play on both sides, 20,000 slices: 66 games; no group whose load has crossed is left standing once the board settles; Principle 0 holds in every landing slice.

## First run (seed 0, 1,200 slices, luck from 0.7; `trace_first.py`)

This run used tetris's luck rule (a capture the mind made and predicted), since replaced.

| Game | Mind took | Mind lost | Groups on offer, taken | Random player took | Random player lost |
|---|---|---|---|---|---|
| 1 | 35 | 49 | 16 of 16 | 35 | 45 |
| 2 | 39 | 56 | 20 of 20 | 24 | 41 |
| 3 | 35 | 49 | 18 of 19 | 25 | 40 |

- **It takes a group whenever one is on offer,** from the first game: a capturing placement enters with potential force 3.
- **It loses more stones than a random player,** in every game.
- **All 86 predictions were confirmed.** A capture is certain a slice ahead, so the prediction filters nothing.
- **Luck fell from 0.7 to 0.16** with no improvement in play, which is why the rule changed.
- **Wants set:** 26 for a point to be free, 12 for a point to be bearing, 8 on stones' sides.
- **Anti-wants:** 544 set, 10 dropped.
- **Speed:** 502 s for 1,200 slices, the last 200 taking 140 s.

Not traced yet: why it loses more stones than a random player.

## Filling its own breath (2026-11-11; `trace_games.py`, `trace_boards.py`, `trace_eyes.py`)

Luck held at 0.7 (the "keeping its stones" rule; it didn't fall in these runs).

- **The mind takes the board, then gives it away.** By its 40th stone it has taken about 34 of the other's stones and lost 1 to 3. It then places into the free points inside its own group until one is left, and the other's random stone takes every stone at once: 48 to 51 lost a game.
- **It fills only when nothing else is on offer:** 11 of its 13 fills in game 1, 16 of 17 in game 2. With another kind of placement on offer it places elsewhere (top-level bids about 2.4 for a fill against 5.8 for the other).
- **The watch was 3 slices, my choice,** so the loss fell outside the watch of the stone that caused it. Widened to 6, as Warp chess's watch spans the other side's answer. The SOV then holds 101 links from a placement to one of the mind's stones coming apart, each naming one point and one stone, at weight 0.24.
- **Not learned.** With the wider watch, games 1 and 2 ended the same way (49 and 51 lost). A board seen at the mind's 50th stone of game 2, full but for two separate free points, was a moment before it filled them.
- **Anti-wants don't hold:** 268 set in 760 slices, none held more than a slice. An anti-want is dropped when no push on offer threatens it, and between the mind's turns nothing is on offer at all. It is also on one named stone, which is gone.

## Relative anti-wants (2026-11-11; Gerundelle changed in the other session; `trace_eyes.py`, `trace_wait.py`)

Gerundelle now holds an anti-want as "a region I hold, <doing>", and drops it only when pushes are on offer and none threatens it. The Go world gained `role_of`, and its predicted effect names the group's colour, not "mine/theirs".

| Game (seed 0) | Mind took | Mind lost | Area | Ended |
|---|---|---|---|---|
| 1 | 38 | 49 | 11 to 4 | the cap |
| 2 | 37 | 48 | 17 to 3 | the cap |
| 3 | 33 | 0 | 49 to 0 | both passed |

- **The anti-want caused game 3's ending, not rest.** With 14 breath-filling placements on offer, 11 were threatened (the SOV links them to a held region coming apart). The mind filled the 3 that weren't, one at a time. With only the 11 left, no placement reached the top level for six slices, its turn passed, and the game ended. Its energy was 1.0 throughout.
- **What it avoids is points, not a kind of placement.** The 11 are points whose placement was once followed by a loss inside its watch. That every free point left in game 3 was one of them is partly how the first two games went.

## Why seed 1 kept losing (2026-11-11; `trace_seed.py`, dormancy on)

Seeds 0 and 1, three games each: seed 0 lost 49, 48, 0; seed 1 lost 48, 48, 48.

- **The aversion lowers a placement's bid; it doesn't keep it out.** In seed 1's game 3, on 24 slices every placement on offer was threatened, and threatened placements still took the top level's slots: nothing else was competing for them. The mind made 9 threatened fills. In seed 0's game 3 the anti-want's own molecule and two candidate sub-wants held those slots, so no placement won.
- **Until every free point is threatened, it fills the ones that aren't.** Seed 1, game 2: 16 fills, none of them threatened.
- **Threatened points grow each game:** 17, 28, 36 of 49 in seed 1; 20, 32, 40 in seed 0.
- **Many anti-wants are on the wrong doing.** A lost stone's sides were last seen `binding` or `pressed`, so the relative anti-want reads "a region I hold, binding": 243 set in seed 1 against 144 for `coming_apart`. Only the latest is held.

## The pass, and placements read by their situation (2026-11-11)

Decided by the user: a placement keeps its point and adds its situation; the SOV is left to generalize across points.

- **The pass is a push on the mind's hand** (`hand`: `holding` on its turn with the board at rest, else `resting`). The hand as an object is my reading. Before, there was no pass push.
- **A placement is named by its point and what the stone would meet on its four sides,** counted, not by direction: `free_b<n>_w<n>_e<n>` (black stones, white stones, the edge). The breath its group would have once landed isn't in the name.
- **Gerundelle (the other session):** the anti-want is read from the whole object lost, not its sides. Confirmed here: every anti-want set was "a region I hold, coming apart".

Three games each, seeds 1 and 0 (`trace_seed.py`): stones lost 1, 49, 0 and 0, 48, 2.

- **Every kept game ended with a pass made with no anti-want held and nothing threatened.** With only breath-filling placements and the pass on offer, the pass is one push among them, and the mind tries it.
- **The aversion hardly fires now.** Each point-and-situation is its own push, so the link from a placement to the loss sits on one push that rarely comes round again: none of the placements on offer was threatened in any endgame slice.
- **Nothing to generalize from yet.** A loss is linked to one point per situation (3 situations, 1 point each). Abstract's concept abstracts (6 to 8) are all about stones' sides; none holds a placement followed by a loss.

## What the mind feels, and what its decisions rest on (2026-11-11; `trace_feel.py`, seeds 0 and 1, three games each)

- **Play:** joy, mostly at a side of its own stone (about 119 formed) and at points (about 50); some curiosity at points; a little sadness.
- **Endgame** (only breath-filling placements and the pass on offer): almost nothing forms. It waits on about 95 turns, places on 46, passes on 2. No frustration or anxiety while it fills its own breath.
- **The loss** (48 stones at once): 131 sadness phases form in 13 slices, 48 on the stones and 83 on their sides, each side read as its own loss. Sadness holds 85% of the top level's phase winners.
- **Never formed:** frustration, anger, anxiety, calm, resignation, gratitude.
- **Decisions are spread thin:** about 195 decisions, the most used placement 5 times. None of the 826 to 900 bonds and SOV links behind them rests on a prediction or potential effect (tetris: 3.4%).
- **Meta targets:** about 215 formed, 8 to 12 targeted, most on a single placement (138 and 207 of them).
- **Checkpoints** (`run.py --checkpoint`, `run.resume`; `check_checkpoint.py`): a run resumed at slice 200 matched a straight run for the next 60 slices.

## The world as it stands (end of 2026-11-11)

Everything above this section is the day's history, in order. This is what `world.py` reads now. Decided by the user unless marked mine.

**Objects and their doings**

| Object | Doings |
|---|---|
| each point | `bearing`; `free`; `free_white_pressing`, `free_white_cutting`, `free_white_choking`, `free_white_taking` (what a white stone there would do to black's groups); `barring_white`, `barring_black` (also `barring_black_white_taking`), `barring_both` (a stone of that colour couldn't hold there) |
| each stone | `breathing`, `straining` (one breath, its own colour places next), `hanging` (one breath, the other places next), `coming_apart` |
| each side of a stone | `free`, `pressed`, `binding` |
| `black_breath`, `white_breath` | as a stone, by the colour's worst-off group; `black_breath` is given territory |
| `hand` | `holding` (the mind's turn, the board at rest), `resting` |

**Pushes**

- `place` on a point, named `free_<own>_<theirs>_<after>`: what it would do to the mind's groups (`alone`, `extending`, `joining`, `saving`), to the other's (`quiet`, `pressing`, `cutting`, `choking`, `taking`), and what the stone would be doing once landed (`breathing`, `hanging`).
- `pass` on the hand.

**The watch** is 6 slices: the mind's stone, the loads read, what came apart leaving, then the same three for the other's reply.

**The dream** (`dream_go.py`, `run.py --dream`): between games, over the boards of the game just played, most recent first; one stone of either colour added or one taken away; the tournament chooses which to follow.

**Checkpoints** (`run.py --checkpoint 1000`, `run.resume`): in `checkpoints/`, `seed<n>_<slice>.pkl` and `dream_seed<n>_<slice>.pkl`.

**Words that are mine:** `straining`; `barring_*`; `white_pressing` and the rest on points; `alone`, `extending`, `joining`, `saving`, `quiet`, `cutting`, `choking`; the hand as an object; dreamed stones named by colour and point; 60 trials a dream.

**In Gerundelle, changed today in the other session and used here:** anti-wants read relative ("a region I hold, <doing>") and from the whole object lost; not dropped while nothing is on offer; roles of prediction nodes given by the world (`role_of`); dormancy; speed fixes.

**Found and still open**

- Given territory can't be contested: the other colour moved `black_breath` about 40 times in three games and it stayed "mine", so no anxiety forms.
- The anti-want looks one link deep; "this placement makes my breath hang, and hanging is followed by coming apart" is two.
- Sadness forms for every side of every lost stone (the anti-wants' whole-object fix isn't in the phases).
- Luck falls on a one-stone difference between games.
- A lost stone is lost for good, and the register grows with every stone.

## Noted, not changed (2026-11-12)

In tetris the user ruled out having the world tell the mind what a push costs it ("that's cheating, it needs to learn when to trust its own predictions") and designed commit instead: the mind commits to a sequence saved in the prediction SOV and sees it through (`E:/vscode/analogy/DRIFT.md`, "Commit").

By that standard part of this world is suspect. A placement's name says what the stone would do to the mind's own group (`saving`, `extending`, `joining`, and `_hanging` or `_breathing` for the stone once landed). That is the world giving the mind the consequence for what it holds.

- **Suspect, my reading:** the own-group part of a placement's name.
- **Probably fine, my reading:** what a placement does to the other colour's groups, and the gerunds on stones, points and each colour's breath, which are physics the world shows anyway.
- **The candidate replacement:** the Go mind commits to sequences and learns from how they come out, the commitment dissolving when the other colour does the unexpected. Go would first need predictions that reach past one slice, and an expected reply.

Nothing here has been changed. The user: "just make a similar note for the Go thing".

## Territory as White's dead opportunity forces (2026-11-12 to 2026-11-13)

The user's design is `go-design.md`: "Territory in Go isn't what you hold. It's what the opponent *can't do*." The user's rulings, in order, with what was built for each. My readings are marked. Backups of each step are `world.py.before_*`, `run.py.before_*`, and in Gerundelle `molecules.py.before_*` / `sov_agent.py.before_*`.

**The world (`world.py`)**

- **White's opportunity force at each point** is an object, `opportunity_<x>_<y>`, read by physics one reply forward: `bearing` (a stone is there), `failing` (a white stone couldn't hold), `hanging` (it would hold with one breath and Black's next stone takes it), `breathing` (it would hold and Black couldn't take it at once). The words are mine.
- **Dead = `failing` or `hanging`** (the user: "can't hold or would hang"; `world.DEAD`). Whether a breathing one can truly live is for the mind's SOV to learn.
- **Points, stones and both breaths are unclaimable** (`unclaimable`), as tetris's cells and blocks. Without it the mind's pushes still claimed stones and points (9 stones, 80 sides, 26 points "mine" in 1,500 slices).
- **Opportunities are held by reading only** (`read_held = ("opportunity_",)`; the user, "Held by reading only"): claims on them are kept but never make them the mind's.
- **A placement's force reaches the opportunity at its point** (`reaches`).
- **`push_predictions`**: for each placement, every opportunity it would kill (`opportunity+<d>_<failing|hanging>`, d = steps from the stone) and every dead one that would live again or be borne by the stone (`opportunity+0_bearing` for a fill, `opportunity+<d>_breathing` for an eye collapsing). Checked by `check_opportunity.py`: every predicted change in the slice predicted, nothing changing unpredicted (670 in 6,000 random slices).

**Territory (`run.py` `give`)**

- The user, "Replace it": the stones, captures and `black_breath` are no longer given territory. Each opportunity is the mind's while it reads dead, lost when it lives again, held again when it dies again (`SovAgent.track_region`).
- **My reading:** when the board is set back between games, the opportunity regions are let go with no loss (nothing made them live).

**The switches on in Go only (`run.GO_SWITCHES`)**, all off by default in Gerundelle; the reason for each is the trace that found the gap:

| Switch | The user's ruling | What it does |
|---|---|---|
| `reach_relations` | "Reach as a relation" | each push on offer holds a seen `reaches` link to what its force reaches |
| `transfer_tells` | "Transfer tells a relation" | Abstract's transfer tells the missing `causes` link, the target named as the same state of an object the structure holds (`Understanding.transfer_target`, my reading) |
| `reach_claims` | "yes, build it" | a push on offer is a claim on what its force reaches, so a never-made fill is served, matters and is attended |
| `predicted_losses` | "Yes, as a loss" | a prediction whose effect is on a region the register holds is a loss: kept and answered, never owned or wanted; it threatens a `held_<doing>` anti-want of that doing, relatively |
| `commit_told` | "Keep, told on offer" | each commit on offer is told it causes its potential effect |
| `situational_told` | "Told links are situational" | a push's told link from a push prediction is taken back when the forces no longer predict it |
| `no_loss_means` | "No loss as a means" | a sub-want can't be another state of a region the register holds now |
| `held_state_wants` | "Held states", "The held doings" | a lost/contested slot offers the states the region was held in; on a never-held region held by reading, a control/unclaimed slot offers the doings regions of its kind were held in |

**Also changed in Gerundelle, not behind a switch:** a sequence's push can be named by its whole id (Go's placements all share the name `place`); a `held_<doing>` anti-want counts `causes` as a threat (the user, "Causes = threat"; an owned prediction's anti-want keeps `prevents` only). Tetris ran identical to `clean5` through 2,000 slices after each.

**`commit=True`** is in `tetris/run.py`'s switch set, which Go reads (the user: "it should default to on").

**Untouched:** `dream_go.py` keeps opportunity objects through a dream's set-up (one line, no backup). `affords_chain` (a way's needs are the board as it stood) was left as it is (the user, "Not now"), though it made a whole old board a means in one chain.

**What each trace found** (seed 0, 1,470 slices; scripts in this folder):

| Step | Kept games | What the trace showed |
|---|---|---|
| Territory replaced | 3 of 5 | the mind fills its own territory every game; kept or lost depends on whether the pass wins before the last eye (`trace_opp_games.py`) |
| Causes = threat | 3 of 5 | the anti-want holds, but only exact placements already seen losing are threatened; the mind fills with new ones (`trace_aversion.py`) |
| reach_relations, transfer_tells | 3 of 5 | Abstract never reads a fill: links below its floor, fills never attended, one giant component, cores cut to 12 links without the reach (`trace_abstract.py`, `trace_attention.py`) |
| reach_claims | 4 of 5 | fills attended; no pattern formed (the core cut) |
| predicted_losses | 3 of 5 | fills made by a want's plan (stale told links), by commits on losses, and by the tournament (`trace_choice_source.py`) |
| commit_told, situational_told | 5 of 6 | plans stop making fills; game 6 lost to a want for a held point's opportunity alive (`trace_want.py`) |
| no_loss_means, held_state_wants | 5 of 6 | root wants still chose loss states: `reach_claims` let claims hold opportunities while alive |
| read_held | 4 of 5 | a control slot's root want (`opportunity_5_5_breathing`, where the mind's own stone stood) led through `affords_chain` to "my stones straining" (`trace_wants_all.py`) |
| held doings | **7 of 7** (one game lost 1 stone) | all 49-0, the mind passing after 56-66 stones, 6-14 fills a game |

**Open**

- **Fixed 2026-11-13:** `breathing` had got into the held doings. When the board was set back, every held opportunity read `breathing` for the one slice before `give()` let it go, and `own_states` recorded it. Now a state is recorded as held only if the region was in it at the register's previous reading too. After the fix: 7 of 7 games kept (game 7 lost 1 stone), and no root want on an opportunity is `breathing`.
- The `breathing` wants left (slices 887, 977, 1008, 1092) are all parts of a whole set as a way's needs (`affords_chain`: the board as it stood), on points the mind doesn't hold, serving roots that want an opportunity dead. `affords_chain` was left as it is (the user, "Not now").
- Only seed 0 has been run on the final state.
- Predictions still filter nothing for kills: a kill shows before White can reply.
- The suspect own-group words in a placement's name (above) are unchanged.

## Two minds, the league and the evolution (2026-11-13)

**The two-mind world (the user: "build the two-mind world")**
- **`world.py` is seated by colour** (`GoWorld(me=...)`): what the mind places and passes, the other colour's opportunities, its predictions, reach and threat names. Stones keep their own colour's names. Alone, the mind is Black, as before: `check_world.py` and `check_opportunity.py` gave the same numbers. Backup `world.py.before_seats`.
- **`goduel.py` (`Duel`, `GoSeat`):** each mind has its own seat, a full GoWorld from its colour.
  - **One game, kept in step:** a seat's "other colour's stone" is the stone the other mind placed in its own seat that slice, or `WAITING`. Both seats act once a slice, the side to move first, and `end_slice` checks they are one game.
  - **Set-back and lifelong seats:** the duel sets both seats back together. A lifelong mind keeps its seat across games, so its stone names and clock go on, and the duel keeps its own clock.
  - **An empty game:** a game both pass before any stone is a 0-0 draw. It crashed the evolution round once.
- **`check_duel.py`:** with no minds, the seats stayed one game every slice, and every predicted kill or loss showed as predicted from both seats.
- **`duel_run.py`:** two minds against each other, with Params per colour.

**The temperament league (the user: "keep ELO rankings for different temperament profiles; have them compete")**
- **Decided by the user:**
  - lifelong minds;
  - two minds per profile, one per colour, each keeping its colour (names are by real colour);
  - area scoring, no komi, equal area a draw;
  - `fiction/temperament.py`'s profiles that have a home in Gerundelle's Params, with aversion 2.0/0.5 and acceptance 3/12 added. Stubbornness has no home yet and was left out.
- **My choices (`league.py` header):**
  - Elo from 1500, K = 24, pooled over a profile's two minds;
  - interleaved rounds: in sub-round k, the Black mind of profile i meets the White mind of i+k, the games in parallel processes;
  - a game called at 1,500 duel slices;
  - every mind saved after each game.
- **Resuming:** `recover_subround.py` finishes a sub-round a crash cut short, replaying only games with no result in their logs.
- **Watching:** `watch_league.py <folder>` is a tkinter viewer: standings, the pairing grid, games running, recent games.
- **First league (`league/`):** stopped by the user after 6 sub-rounds. Unflinching 1577, trusting 1560, grieving 1529 led; patient (1402) and impatient (1442) were last. Games with a patience profile could end after 3-14 stones: a patient mind waits before acting (`SovAgent.winner`), and a turn passes after 6 slices.

**The evolution (`evo/`; the user: mutate "unflinching, trusting, and grieving ... 9-11 minds", then "Parents + 2 mutants each", "One generation", "All six, about +-30%")**
- **`evo_make.py`:** each parent's learned minds copied, the six traits multiplied by exp(N(0, 0.3)). The seed and every value are in `evo/population.json`.
- **Changes during the generation**, recorded in `population.json`:
  - after 4 sub-rounds, the three mutants that had been given a patience were set back to unset (the user: "restore patience None for the mutants");
  - and `affords_relation` was turned on in every mind (the user: "on please").

**Speed (analogy/DRIFT.md, "Speed, and Abstract's input")**
- **What was slow:** Abstract was about 80% of a slice.
- **Exact fixes:** `core`'s cut, the core memo, and the per-concept edge cache.
- **Design change:** the `affords` split.
- **Together:** Abstract went to 7% of a slice in the test game, 2.6 times faster than with the first fix alone.

**Frozen play and study (`FROZEN_PLAY.md`, `STUDY_MODE.md`; designs, the POC in `frozen_poc.py`)**
- **Speed:** frozen slices were 5-8 times faster.
- **But frozen minds churn:** they play to the cap on near-empty boards. Told links, affordances, or Abstract live did not fix it (`frozen_diverge.py`: the games part at the third placement in one pair). What in-game writes play depends on is open.
