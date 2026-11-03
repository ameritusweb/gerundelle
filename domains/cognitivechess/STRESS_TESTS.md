# Stress tests

Full games played with the mind as it stands, to find what the next rungs might be (`MAKING_RUNGS.md`, "Finding residue
early"). Not rungs: nothing is built to pass them. Each section is one run, dated; rerun after a few rungs and compare.

## 2026-11-01: the mind after rung 3 (`experiments/fullgame.py`; `logs/fullgame_s*.log`)

**Setup.** The standard starting position. Two Gerundelle minds as rung 3 left them: base arm (polarity, sub-wants,
sub_yield, sub_tested), pieces as given territory, White wanting its standing up, Black a keeper of what it holds
(`keep_wait=False`), the `turns` schedule. Games of up to 120 half-moves; a game also ends at mate, a draw by the rules,
or six idle slices once a move has been made. Three seeds, 16,000 mind-steps each, `PYTHONHASHSEED=0`.

### What happened

| Seed | games finished | half-moves per game | ended by | then |
|---|---|---|---|---|
| 0 | 18 | 124, 109, 58, 120, 57, 4, 7, then eleven of 1 | cap 2, mate 1, idle 15 | froze at the start of game 19 |
| 1 | 4 | 124, 48, 123, 14 | cap 2, idle 2 | froze at the start of game 5 |
| 2 | 7 | 124, 113, 66, 90, 49, 62, 17 | cap 1, mate 1, idle 5 | froze at the start of game 8 |

- **29 games, 2 mates.** Most games end because a side stops moving, not by the rules.
- **Moves came from experiments, almost never the planner:** 1,281 by experiments against 39 by the planner (23 of
  them seed 2's White). Over a full game neither mind has a known way to its want; it plays by curiosity.
- **White ended down material in 10 of the 14 games of 20 or more half-moves.** Not traced.
- **Speed is not the limit:** 8–20 seconds per long game. The time went into the frozen stretches.
- Feelings: sadness 48–59 and joy 30–53 per mind per run (pieces lost and won back); anger and frustration rare.

### Traced

**1. A mind with nothing new to try at a position it knows makes no move** (all three seeds, both colours).
- *Black, seed 0, games 8–18* (`fullgame` replay): Black is a keeper, and at the start of a game nothing of its own is
  lost, so it has no want and its turn runs on curiosity alone. Experiments it considered per game fell from 21–58
  (games 1–5) to 2 (game 6 on). From game 8 every one of them was **foreseen**: in a still world an experiment already
  done in the situation it would meet is reported, not played. Black's situation after White's first move looks the
  same in every game, because it perceives each piece's state and safety, not squares, and most first moves change no
  Black piece's safety (White's first moves did differ: e4, e3, c3, f4, Nc3, ...). On its other stalled ticks no
  experiment won at all. No move: six idle slices, the game ends, the next begins the same way.
- *White, seed 1, game 5*: the want is active (`standing_white_up`), the planner finds no way, and on all 2,535 of its
  ticks at the start of the game there is **no experiment in the pool**. The starting position is exactly the same
  every game; after four games nothing new is left to try there.

**2. `DuelWorld` claims to be still, and isn't.** `still = True` (from `ChessWorld`) means nothing moves between the
mind's pushes unless it acts; in a duel the other mind moves between every push. As a diagnostic only, with
`still = False` seed 0's collapse comes later (game 12, not 8) and differently: 27 of Black's 28 stalled ticks were
won by **wait-and-watch** experiments (`caused_by:…:wait`, no steps), which a still world doesn't suggest. Correcting
the flag moves the failure; it doesn't remove it.

**3. A game no one starts never ends.** The idle rule ends a game only once a move has been made
(`self.moved and self.idle >= IDLE`), so a frozen start freezes the rest of the run.

### Candidate residue, sorted

| Residue | Kind | How often, how early | Notes |
|---|---|---|---|
| **A turn the mind must take.** With no active want and nothing new to try, a mind treats its own move as time to watch, or makes none | missing structure: Gerundelle has no obligation (a slot that must be filled now) | every seed; stops all play within 5–8 games | the strongest; never showed in the four-half-move rungs |
| **Exploration runs out at a known position** (experiments decay with repetition; foreseen in a still world) | pathology of inquiry under repetition | every seed, both colours | the start position is identical every game |
| **Openings look the same to the mind** (pieces' states, not squares) | perception granularity | seed 0's Black: one situation for many first moves | bears on recall by shape |
| `DuelWorld.still` is wrong for two minds | world | always | correcting it changes the failure, not the outcome |
| A game no one starts never ends | world | every seed, at the end | a test-harness limit; the residue is the freeze, not this |
| White ends down material in most long games | not traced | 10 of 14 long games | next to trace |
| The planner is almost never used over a full game | follows from the want having no known way | all games | expected at this stage |

### Follow-up, same day: what wins, and what is acted on

**`Params.winner_acts`** (Gerundelle, off by default; backup `backup/molecules_2026-11-01/`, suite matched). The user:
"Something has to win, which results in a move." Traced: in seed 1's frozen game a push won White's top level on 261 of
300 ticks, but the planner's best value was 0.0 on all 1,871 searches and no experiment was left, so nothing acted. Now,
when neither the planner nor an experiment gives a push, a winning push is made, chosen by temperament
(`SovAgent.winner`: patience, how long to watch first, bounded by the world's watch; curiosity, the unfamiliar against
the familiar; persistence, staying with the last piece; each neutral at its default). White no longer freezes.

**Black still stopped: the winning pushes could not be played.** At Black's stalled turns (seed 1, from game 9) pushes
won its top level 219 times in 120 ticks, but not playable ones: `Ng8`, `Ke8`, `Ra8`, moves back to starting squares,
from earlier positions, at a starting position where none is legal. The moves on offer bid lower (best about 1.77,
against about 1.9 for a thought slot).

**The world pushing back** (the user: "curiosity, boredom, patience, meta-cognition, and the world pushing back on
unplayable moves, should work"). `DuelWorld.playable`: a move not legal now for its own piece is tried and nothing
happens. Seed 1: 172 unplayable moves tried, the same ones again and again (`Bd4` 30 times). Traced
(`experiments/stale3.py`): over 30 rejected tries `Bd4`'s activation stayed at 1.87 (a winner never decays), its top
wins rose from 95 to 224 (lengthening its half-life), its surprise fell to 0 by the third try, it has no open sites for
`stuck` or `looping` to park, and the 86 records of "nothing happens" are read by nothing in its bid. `bored` fired 8
times without effect.

**An imagination lane** (`Params.imagined_lane`, off by default; backup `backup/molecules_2026-11-01c/`, suite
matched). The user: "if it's thinking about something that can't be played, shouldn't that be closer to imagination or
another lane in the tournament?" A push the world does not offer now is imagined (Posit, not Fit): it competes in its
own slots, not for the thoughts', and nothing imagined is acted on. Seed 1, 4,000 steps:

| | before the lane | with the lane |
|---|---|---|
| one-move games | 40 of 48 | **23 of 41** |
| games of 100+ half-moves | 0 | **7** (the first seven) |
| Black's pushes | about 240 | **597** |

The Lean development's `bid_filter_imagined` (`SOV/Market.lean`: "imagined evidence is inert") concerns evidence, not
attention, but in its spirit an imagined winner should not gain top-level wins that lengthen its half-life; as built it
does. Not changed.

**Still open from this run:** the 23 one-move games with the lane on (not traced); whether imagined winners should count
toward top wins; the temperament comparison (running).

### Rerun: news in the structure (`Params.news_in_structure`; `KNOWNS_AND_UNKNOWNS.md`; `logs/fullgame_news_s*.log`)

The same stress test with all three switches on (`winner_acts`, `imagined_lane`, `news_in_structure`), default temperament.
Stopped by hand before the 16,000 steps, because of the slowdown below. Backup `backup/molecules_2026-11-01d/`; suite
matched the reference.

| | first run, 3 seeds | **rerun, 3 seeds** |
|---|---|---|
| games finished | 29, then frozen on every seed | **105**, none frozen |
| ended at the 120-half-move cap | 5 | **95** |
| mate / draw by the rules | 2 / 0 | 5 / 1 |
| ended by idling | 22 | **4** |
| White up / down / even at the end | down in 10 of 14 long games | **47 / 49 / 9** (mean +0.54) |
| moves by experiment / planner / the winner | 1,281 / 39 / – | 9,153 / 2,415 / 842 |

**New failure: speed.** Seconds per game on seed 0: 9, 1, 16, 15, 21 (games 1–5); 65–155 (games 11–15); 447–752 (games
21–25); 1,201–3,003 (last five). The other seeds match: roughly 200 times slower after 35 games. The earlier "speed is not
the limit" held only because the minds froze before their records grew. Being profiled (`experiments/profile_full.py`).

### The slowdown, traced (`experiments/growth3.py`; `logs/growth3_*.log`)

Seed 1, 20 games, ms per tick by component next to the record sizes. From game 5 to game 20 the whole tick grew from 57 to
about 700 ms; `relation_of` from 0.5 to 311 (the largest and fastest-growing), `novelty` from 8 to 132, `resolve` from
18 to 62, `analogize` from 7 to 57. Sizes (both minds): relations 1,029 to 31,938, edges 40 to 11,080, splits 11 to 838,
plans 575 to 16,775, moves by others 262 to 6,713, pool 357 to 1,485. All sizes grow together, so fits against them can't
separate causes; the causes below come from the code and direct measurement.

**Speedups with identical results** (every game's ticks and sizes match; suite matched; backups
`backup/molecules_2026-11-01e/`, `f/`):
- `concept_of` remembered per id; `core` reads link funding from one index per `analogize`: `analogize` 184 to 48 ms, `core`
  144 to 8, at game 17.
- One `relation_of` pass reuses `needed_states` and `responsive` per pair: about half (217 to about 109 at game 17, adjusted
  by untouched components, since the machine ran slower during that run).
- `novelty` returns 0 at once for an identical signature: **no real gain**; it fires for 46 of 410 molecules.

**Correction.** "The pool is almost entirely pushes" (1,304 of 1,443) was a counting bug: the test `"_push:" in id` also
matched meta molecules about pushes. The earlier "218 pushes of 316" has the same flaw.

**What actually fills the pool** (Black, game 10): 410 molecules, of which **256 are `meta:stuck`**, 123 are pushes, 56
ownership instances. A `stuck` molecule predicts its subject stays open; when it does, it is refreshed and predicts again
(`Meta.settle`), and it parks its subject only if it wins one of the few meta slots. So each long-open question keeps a
molecule alive for good. Each has a unique `about:` tag, so `novelty` compares each with all the others: about 75,000
comparisons per tick at game 10. Stopping this build-up changes behaviour: a design decision, not a speedup.

**`Params.stuck_earns`** (off by default; backup `backup/molecules_2026-11-01g/`, suite matched): a `stuck` molecule's
confirmed prediction refreshes it only if it won a slot that tick; otherwise it fades, and can form again. Seed 1
(`logs/growth3_stuck.log`), against the same run without it: pool at game 20, 1,485 to 226 (8 of them `stuck`); ms per tick
at game 20, 773 to 528; `novelty` off the top costs, `resolve` 92 to 15. Not an exact-result change: splits at game 20
went from 838 to 761. Play holds on seeds 0 and 2 (`logs/fullgame_stuck_s*.log`, in progress): 34 of 35 games to the cap, 1
mate. Largest cost left: `relation_of`, 288 of 528 ms at game 20.

**`relation_of`, the rest of it** (backup `backup/molecules_2026-11-01h/`; identical ticks and sizes over 20 games; suite matched
the reference). Profiled first (`logs/profile_full2_s1.log`): 106 of its 131 seconds were `needed_states`, re-walking the
same outcome histories for about 120 region pairs per tick. Now the facts of the situations a claim on a region took in are
gathered once per region (`Territory.took_facts`) and kept until the meta layer's records change (`Meta.version`), and
each pair only filters them; `responsive` looks moves up in a set. ms per tick at game 20: `relation_of` 288 to 24, the
whole tick 528 to 264; `resolve` and `analogize`, untouched, did not move. Over the day, game 20's tick went from 1,330 ms
to 264. Largest cost left: `Understanding.observe`, 105 of 264 ms (58 of it `analogize`). Ticks still grow with experience,
25 to 264 ms over 20 games.
