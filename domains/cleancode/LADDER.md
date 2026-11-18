# Clean code: the ladder

Each rung: its question, its room, what is expected (written before it is run), the results, and what is left. Rooms are in `rooms.py`;
`run.py --rung <n>` runs one. Small rooms first (`../cognitivechess/LADDER.md`).

| Rung | Room |
|---|---|
| 0 | one input, one connection, three tests |
| 1 | two connections one after the other |
| 2 | two inputs, each through a connection, joined |
| 3 | two connections with a hidden range check between them |
| 4 | a loop |
| 5 | a branch |

## Rung 0: one connection

**Question.** With one wheel and three tests, does the mind turn the wheel to where every test passes, and stay there (settle)?

**Room.** One input through one connection (the single-path wheel, nine operations). Each problem: three tests drawn afresh, the wheel
scrambled up to two steps from a correct operation. A problem closes when everything holds and three slices pass with no turn, or after
300 slices.

**Expected (2026-11-14, before the run).**
- The first problems are found by trying: pushes on offer are explored (inquiry), and a problem settles only after the wheel comes to a
  place where every test passes and the mind then leaves it alone.
- Leaving it alone is the question. Every push from a solved wheel is predicted (push_predictions) to turn passing tests to failing:
  losses of held regions (`predicted_losses`). The mind should come to hold the wheel still: turns per problem should fall over the
  run, and problems should settle.
- A mind that turns away from a wheel where everything holds, after it has seen what that turn does, is acting against its own
  territory: to be traced (never wanting its own loss).

**Results** (seed 0, 1,200 slices, 2026-11-14; each change below was found by a trace, and each is in the code where it is made).
- **First run:** no problem settled. The mind turned a solved wheel round to `passing`: `clean_<c>` read `empty`, held, with every test
  failing. Fixed: clean reads `unsettled` until everything else holds (graph.clean).
- **Then:** still none settled (`trace_settle.py`). Only the two turns were on offer, and one always won the top level, though the
  mind had lived "turning back from halving causes the tests to fail". Added: resting, a push (Go's pass).
- **Then:** resting rarely reached the top: a turn breaking every test was the strongest force on offer (HANGING), resting QUIET.
  The user's answer: **time territory**, a tick gained each tick the program is correct, held for good (world.py). 5 of 7 problems
  settled, 161 ticks gained.
- **Stuck going through a loss** (problem 2, `adding_1` to `subtracting_1`): the mind circled `halving` and `negating`, never going on
  through two losses to the answer. The user: in-game dreaming when stuck, as Warp chess (`dream_code.py`, `--dream`). The dream
  found the way (`trace_dream.py`), but the mind's lived experience of earlier problems, under the same names, drowned it. Fixed (the
  user: "yes, do it"): every gerund read from the tests' values is named afresh per problem (world.read). With dreams: problem 2
  settled in 35 slices; 189 ticks gained.
- **Still open:** problems 3-5 run to the 300-slice cap. In problem 3 the mind reaches the answer and turns away the next slice, again
  and again: resting bids about 5.70, the turns about 5.87, and the anti-want against breaking the tests pushes them down very little
  (`trace_settle.py 92 75 --dream`). An anti-want about a lost time gain pushes resting down through a "resting prevents time gained"
  link; where that link comes from isn't traced yet.
- **That link, traced** (2026-11-14): a problem closed in the slice its last tick came, and the next opened before the mind saw the
  tick, so the tick it had predicted never came and its last push, a rest, was told it prevents time gained. Fixed: a problem closes
  a slice after it is done (world.py); no rest is blamed since.
- **Temperament** (the user: "yes, tweak the temperament"; `Params.aversion`, how strongly an anti-want pushes down what threatens
  it), 4 seeds x 1,200 slices, with dreams. Settled = closed by settling, not by the 300-slice cap:

  | aversion | problems closed | settled | ticks gained |
  |---|---|---|---|
  | 1 (default) | 14 | 2 | 396 |
  | 2 | 26 | 15 | 604 |
  | 3 | 25 | 13 | 390 |

  Aversion 2 settles most and gains the most time; at 3, one seed gained only 17 ticks.

## Rung 1: two connections in a row

**Question.** With two wheels one after the other, does the mind find a setting where every test passes, keep it, and settle it
clean: no `add N` then `subtract N` (lint), and no connection doing work another could do alone (clean)?

**Room.** One input through two single-path connections, three tests, each wheel scrambled up to two steps. Aversion 2, dreaming when
stuck (`--dream`). 4 seeds x 2,000 slices.

**Expected (2026-11-14, before the run).**
- Fewer problems settle than on rung 0: there are 81 settings and two wheels to turn, and a turn of one wheel can undo what the other
  got right.
- Several settings often pass the tests (`adding_1` twice, or `adding_2` then `passing`). Clean code tells them apart: a connection
  reads `spare` when `passing` there would lose nothing, so a settled program should more often have one connection `empty` than both
  working. Whether the mind goes on from passing tests to clean is the new question.
- `lint_cancel` fires when the two wheels undo each other (`adding_1` then `subtracting_1`); such a setting passes no test unless the
  tests want the input back, so the lint should matter rarely here.

**Results** (2026-11-14; 4 seeds x 2,000 slices, aversion 2, dreams; `rung1/`; `clean_check.py` searches all 81 settings).

| seed | problems closed | settled | ticks gained |
|---|---|---|---|
| 0 | 10 | 5 | 92 |
| 1 | 8 | 3 | 197 |
| 2 | 8 | 2 | 84 |
| 3 | 7 | 1 | 113 |

- 11 of 33 problems settled (rung 0 at aversion 2: 15 of 26), as expected: fewer.
- Every settled program was the cleanest possible (11 of 11). Where a connection could be `passing` (seed 1 problem 2, seed 3 problem 3,
  4 satisfying settings each), the mind settled on that one. Clean code did tell satisfying settings apart.
- **The 22 unsettled** (`classify_unsettled.py` on full logs): 6 solved and left again and again (all held in about half their
  slices), 10 solved only briefly, 6 never solved. Traced (seed 1, problem 6, `trace_settle.py`, probes): the turn away from the
  answer filled the open sites of the turn back (a split half made "when clean is unsettled": a setup binding, about +3.6 on a bid
  of 3.0), so it won the first level despite the anti-want (-3.8) and bid 14.1 at the top, where the anti-want, not carried up,
  pushed nothing.
- **`Params.anti_unbinds`** (the user: "maybe the anti-want should break the binding at the first level?", "yes, build it"): at the
  first level a push a held anti-want threatens competes unbound. Again, 4 seeds x 2,000 slices (`rung1u/`):

  | seed | problems closed | settled | ticks gained |
  |---|---|---|---|
  | 0 | 13 | 10 | 37 |
  | 1 | 12 | 7 | 33 |
  | 2 | 10 | 4 | 16 |
  | 3 | 7 | 1 | 8 |

  22 of 42 settled (before: 11 of 33). Ticks fell (486 to 94) because a settled problem closes three slices after it is solved,
  where an oscillating one stayed open its 300 slices, about half of them correct: here ticks reward oscillation, settling is the
  measure. 19 of the 22 settled programs are the cleanest possible; the other 3 settled with both connections working where one
  could do (e.g. `adding_2`, `subtracting_1` where `passing`, `adding_1` would), out of reach of the clean reading, which tries one
  connection at a time (graph.clean, my reading).

## Rung 2: two inputs joined

**Question.** With two paths that come together at a join, does the mind find a setting where every test passes and keep it, now
that the join's wheel (`taking_max`, `adding`, `multiplying`, `subtracting`, `taking_min`, `taking_mod`) changes how the two paths
interact, and new compile errors (`dividing_by_zero` at the join) and lint (a join input dominated by the other) can appear?

**Room.** Two inputs, each through one single-path connection, joined. Three tests, each wheel scrambled up to two steps. 486
settings. Aversion 2, dreams, `anti_unbinds`. 4 seeds x 2,000 slices.

**Expected (2026-11-14, before the run).**
- Fewer problems settle than on rung 1 (22 of 42): six times as many settings, and a turn of the join changes what both paths
  contribute at once (the user: "one step can flip credit assignment completely").
- `subtracting` and `taking_mod` on the join make compile errors on the way (a negative value, a division by zero): more losses to
  pass through, so more dreams.
- `lint_dominated` fires on `taking_max` / `taking_min` when one path always wins on the tests; a settled program has none, so the mind
  must sometimes leave a setting that passes the tests for one where both paths matter.

**Results** (2026-11-15; first 4 seeds x 2,000 slices, aversion 2, dreams, `anti_unbinds`; `rung2/`; then the naming revert and
fresh runs, `rung2n/`; the analysis below is Claude's, from `trace_distance.py` and an understanding probe, each number from a trace).

- **With per-problem naming** (`rung2/`): ~26 closed, 1 settled. The documented inquiry explosion (world.py `PER_PROBLEM`): a turn's
  SOV never closed, its inquiry held the tournament, and the mind flipped one wheel for whole problems.
- **Naming reverted** (the user, 2026-11-15: "stop naming after one specific problem then"; `rung2n/`): seed 0 settles 4 of 9, and a
  settled problem settles fast (problem 3: 19 slices, 6 settings — transfer works when the carried knowledge fits). But the
  never-solved problems remain, and they share one signature.
- **The signature: a two-setting orbit** (`trace_distance.py`, new). Never-solved problems make ~150 turns over 7-37 distinct
  settings; the worst spend nearly all slices alternating one wheel between two adjacent operations (seed 0 problem 8: 146/146
  slices on `multiplying_3`/`halving`; old runs, seed 2 problem 7: 132 slices standing ONE turn from the only fully-held setting —
  join `taking_min` to `taking_mod` — without trying it once, while twice reaching a full hold and leaving).
- **The orbit is an unresolvable unknown, not a search failure** (the user, 2026-11-15: the mind is an understanding engine, it
  feels the pull of unknowns and tries to resolve them, not an exhaustive searcher). Probed at slice ~300 of seed 0 problem 1: the
  oscillating pushes' causes are contradictory and flat — `turning_back_push:conn_0_subtracting_1` carries both `test_2_passing`
  and `test_2_failing` among 15 causes — because what a path push does depends on the join's wheel, and nothing splits the push on
  that context. An unknown that cannot settle pulls every tick: the orbit is the pull of the unresolvable.
- **The dream finds the condition; the firewall (correctly) keeps it; nothing promotes it.** The same probe:
  `turning_back_push:conn_0_subtracting_2` holds exactly one condition, `conn_2_multiplying`, funded [lived 0, told 0, imagined 1].
  The dream discovered the join-context conditioning, wrote it imagined, and it funds nothing — there is no path from a dreamed
  `conditions` edge to a lived one. Rung 0's dreamed way needed no condition, so living it out sufficed; rung 2's knowledge is
  conditionED, the one kind the dream can find but the mind cannot absorb.
- **Proposed (Claude, for the user to rule on):** a dreamed condition becomes an experiment candidate — "does this push do
  something different while `conn_2` is `multiplying`?" — so one lived trial funds the split, the conditioned SOV closes, inquiry
  extinguishes, and the constraints can converge on the closing turn. The told-at-half, confirmed-to-lived bootstrap path,
  extended to dreamed conditions.
- **Deeper probes before building** (2026-11-15, the same session): the arc is longer than the first diagnosis said. The meta
  layer DID eventually fire on the oscillating push, find the boundary and split it on `conn_2_multiplying` (clean, unimodal
  halves) — but only after grinding through 5 opposed outcomes to find the boundary the dream had already named, because
  `Inquiry.suggest`'s hypothesis path reads told receipts only (`e[1] > 0`) and a dreamed condition (funded [0, 0, 1]) is
  invisible to it. And the push's conditions slot had meanwhile closed on generic receipts (`held_evidence`), so the standing
  question died. Also found: the oscillation CONTINUED after the split stood, so conditioned understanding is necessary but not
  sufficient — why a conditioned reading does not reach the decision (the planner's step through the valley?) is rung 2's
  remaining open question, named here so the fix below is not oversold.

**`Params.dreamed_conditions`** (the user, 2026-11-15: "please build it, following the Gerundelle way"). In `Inquiry.suggest`,
a dreamed `conditioned_by` joins the told ones as a hypothesis to test: the experiment brings about the condition's other side
and retries the push, the lived outcomes make the boundary judgeable, the split machinery funds everything. The firewall stands
untouched: the dream only proposes; the world's answers fund. On in this domain (run.py `CODE_SWITCHES`), off everywhere else.

**Expected (written before the measuring run):**
- The oscillating push's `exp:conditions:<push>:<preparation that brings the dreamed condition's other side>` is suggested and
  preferred (the told_leads path) once the dream has run.
- Splits on dreamed boundaries land earlier (the experiment supplies the missing side's outcomes instead of waiting for the
  orbit to wander there).
- Settling improves over `rung2n` (5 settled of 14) but may not jump: the probes above say the orbit can survive its own split,
  so the remaining gap is expected to show, and is the next trace.

**Results, ungated** (4 seeds x 2,000 slices, `rung2d/`): seed 0 4/9 -> 1/7, seed 1 1/3 -> 2/7, seed 2 0/6 -> 0/6,
seed 3 0/2 -> 3/8. Not a wash: every gain is a former orbiter (s0p1, 146 turns unsettled, now 52 turns settled; s1p2; s3p2 in
33 slices; s3p3; s3p6), and every loss a former transfer-fast settler (s0's p3/p4/p5, 19/77/29 slices at baseline, now at the
cap). The cure worked on the disease and taxed the healthy: every dreamed edge, junk included, spawned experiments whose
preparations are themselves turns, and the churn scrambled problems that carried knowledge was already steering.

**The gate** (2026-11-15, from the trace above): the dreamed hypothesis fires only where the confusion stands — the concept in
`meta.unexplained` (conflated, and no boundary found in what was lived). Healthy problems never enter that state; orbiters live
there. Expected, written before the gated run (`rung2g/`): seed 0's transfer-fast settles return, the orbiter gains keep, and
the gated total beats both the baseline's 5 and the ungated 6.

**Results, gated first cut** (`rung2g/`): the gate NEVER FIRED — all four seeds match the baseline problem for problem, end
states included. The probe had already said why, and the cut missed it: by the time a push is unexplained, its conditions
question is dead (the slot closed on generic receipts), so `Inquiry.observe` never reaches `suggest` for it at all. The ungated
gains had come from concepts whose questions still stood — broad churn, not the targeted cure. A dead end, kept for the record.

**The reopen rule** (2026-11-15; molecules.py, `Inquiry.observe`): a conflation the meta layer could not explain is a standing
question of its own, whatever the slot's funding — settled thoughts reopen on contradiction (README, the memory layer). Where a
dream has named a boundary to try, the confusion itself poses the conditions question and offers its experiments (value 1.0
times the served pay: the confusion stands whole, however funded the slot reads). Smoke: seed 0 problem 1, never settled at
baseline and under the first cut, settles in 137 slices with 29 condition-experiments offered. Expected, written before the
measuring run (`rung2u/`): the transfer-fast settles keep (the rule touches only unexplained concepts), the orbiter gains
return, and the total beats the baseline's 5 and the ungated 6.

**Results, the reopen rule** (`rung2u/`, 4 seeds x 2,000 slices): **the expectation failed**, and the failure says where the
ceiling really is. Settled: s0 1/7, s1 1/7, s2 2/8, s3 1/7 — 5 of 29, level with the baseline's 5 and the ungated 6. The rule
does reach problems nothing else reached: seed 2, which settled NOTHING under the baseline, the ungated switch or the gate,
settles two (problem 2 in 21 slices, problem 4 in 50); s3p3 in 107; s0p1 in 137. But the transfer-fast settles are lost again
(s0's p3/p4/p5) — `unexplained` turns out to be common early even in healthy problems, so the experiments still churn broadly,
and the rule redistributes WHICH problems settle more than it raises how many.

**Where this leaves rung 2** (the honest reading of all four variants). The promotion arc works as designed — dream names the
boundary, the experiment brings about its other side, lived outcomes fund the split; seed 2's first-ever settles prove the
reach. But across baseline, ungated, gated and reopen, total settles stay at 5-6 of ~20-29 while the cured problems move
around: the binding constraint is not knowledge acquisition. Two constraints stand above it, both already traced: the action
economy (experiments and want-driven turns compete for one body; whichever wins, the other's problems starve), and the one
from the first probes — a conditioned, even split understanding does not reliably reach the decision (the orbit that survived
its own split). The planner's step through the valley is the open organ. Settled with the user before more runs.

**The decision traced to its floor** (2026-11-15, trace_valley.py; the user: "yes you should try it", and on temperament: it
relates upstream only). Three layers, each found by the trace and each with its change:
1. **The hands overrode the tournament.** At d1 the closing push WON the top (bid 6.11) and the mind turned the last wheel
   instead: `choice()` re-ranked winners by familiarity (curiosity's second vote) and the last-turned connection (persistence's
   second vote — the sticky wheel, the orbit's engine). `Params.faithful_choice`: bids decide among winners, ties to the push
   made least recently; temperament speaks once, in the bids. (The planner, for the record, never engaged: 0 of 300 slices.)
2. **The forces didn't add.** Faithful hands then lost by 0.06: a push flipping four gerunds and the tick bid the same HANGING
   3.0 as a one-flip poke, and an unclosed SOV's inquiry outbid the full win. The balance principle (the user, 2026-11-15,
   balance/PLAN.md) applied to this world's potentials: a push's force counts the gerunds it reaches, stacked units, both
   directions (the force is the size of the change, never its worth). The mind then REACHED the fully-held setting (s42,
   potential 6.0, bid 16.09) —
3. **— and would not stay: one side was armed.** At the solution the destructive pushes carry the biggest stacked potentials,
   and the anti side pressed flat, one anti-want at a time (anti_defense counted only where waiting itself loses — a moving
   world's rule; clean code is still). `Params.defense_still` + `world.effects_after`: losses stack against a push as its
   flips stack for it. Smoke: seed 2 problem 1 — never settled in ANY variant, never at d1 — settles in 167 slices.

**Expected of the full stack** (`rung2b/`, written before the run): orbiters that reach d1 close and stay; seed 2 settles
problems it never settled; total beats rung2u's 5 of 29. The named risk: the counted anti side may over-punish the
transformative pushes mid-search (aversion 2 x stacked losses) and trade the orbit for hovering — if totals stay flat again,
the next trace is the anti side's scale, not a new organ.

**Results, the full stack** (`rung2b/`): s0 1/7, s1 1/6, s2 2/7, s3 1/6 — **5 of 26. Flat, the named risk realized.** The
gains are real where they land (s2p1, the problem no variant ever settled or even approached, settles in 167 slices; s0p6 in
45; s2p6 in 53; two more settle exactly at the 300 cap), and the unsettled still turn every acting slice to the end: the
orbit traded for hovering, as named. The ledger across six variants — baseline 5/20, ungated 6/28, gated 5/30, reopen 5/29,
full stack 5/26 — now says something none of the organs said alone: every traced fix was real (hands faithful, forces
adding, both sides counted, each verified at the slice level), every one redistributes WHICH problems settle, and the total
sits at 5-6 regardless. Either the anti side's scale is next (the pre-named trace), or the constant is structural: a problem
either settles fast on what the mind already carries (17-75 slices) or runs its 300-slice cap, and the interventions move
problems between those two bins without widening the fast bin's mouth. Settled with the user which reading to pursue —
the slice-level traces say the organs are healthy now; the population-level number says the body still isn't.

**The flat total traced** (2026-11-15, the user: "trace it"; `trace_distance.py` on `rung2b/`, then the d0 probe). Start
distance is refuted as the constraint: the two farthest problems (distance 5) settled while distance-1 problems capped. The
disease had moved INSIDE d0: s1p4 sat at the fully-held setting 147 slices without settling, 74 round trips of reach-and-leave.
The d0 anatomy (seed 3 problem 1): four destroyer pushes at stacked potential 7.0 bid ~22, REST NOT AT THE TOP AT ALL, and the
defense read None — anti_defense counted only the one rotating anti-want's region. The unit-potential change armed one side.

**The all-held defense** (2026-11-15; sov_agent.anti_update + Mind.support, under `defense_still`): the register presses for
everything it holds — a push's defense counts its losses across ALL held regions, standing, no anti-want needed in rotation
(held anti-wants lend their heat when present). Smoke: the ping-pong problem settles in 9 slices, 4 turns. Measured
(`rung2c/`): s0 1, s1 1, s2 1, s3 2 — **5 again, the seventh variant at 5-6**, but the fast bin is faster than ever (3
slices, 9 slices, 66) and the cured problems moved again (s2p1, settled under the previous stack in 167, regressed: the
standing press over-suppresses mid-search, where every transformative push disturbs something held). Aversion is now exactly
the knob between the two failure modes — too weak, the mind cannot rest on the answer; too strong, it cannot leave what it
holds — so the pre-named sweep runs (aversion 1 and 3, `rung2c_a1/`, `rung2c_a3/`), rung 0's temperament table at rung 2's
scale. If the sweep breaks the flat 5, the decision layer's last free parameter was temperament, where individual difference
belongs; if it does not, the constant is structural — which problems a mind settles in 300 slices is decided by what it
carries in, and the lever is between problems, not within them.

**The sweep's verdict** (`rung2c_a1/`, `rung2c_a3/`): aversion 1 settles 7 of 27, aversion 2 settles 5 of 26, aversion 3
settles 4 of 28. A mild lean toward the gentler temperament, inside noise at these counts — the constant does not break.
Eight variants now sit at 4-7 settled while the cured problems reshuffle, with the slice-level traces confirming each organ
healthy as tuned: hands faithful to the tournament, forces adding on both sides, the dreamed boundary tested, the register
pressing for what it holds. **The structural reading stands: which problems a mind settles in 300 slices is decided by what
it carries in, and the lever is between problems, not within them.** The architecture's own doctrine names the lever — every
valid curriculum is a geodesic, each step adding exactly one testable concept — and rung 2 drops the mind into 486-setting
join problems with no curriculum at all. Proposed for the user's ruling, before any further organ work: a rung-2 curriculum —
problems ordered by scramble (one wheel off, then two, then three; the join wheel alone before the join with its paths), so
each problem funds what the next one needs. The within-problem machinery is ready for it; eight variants say it was never
the bottleneck.

**The structural conclusion retracted** (2026-11-15, the user: "are you sure?" — no). Two holes, one now closed against it:
settles by position in the run, all eight variants pooled, 40 problems a position: problem 1 settles at 28% — THE HIGHEST,
with nothing carried in — and the rate DECLINES with position (15-25% through p6, 4% at p7, 0 after). Transfer between
problems is not the lever; if anything the carrying hurts (stale push-effect links from earlier problems misleading later
ones: the shared-names contamination, surfacing at the population level). The curriculum proposal as written would deepen
that, not cure it. The second hole is censoring: "fast-or-never" was read from 300-capped data, where every "never" is only
"not within 300"; the cap-900 runs (`rung2cap/`) are the discriminating experiment — if settles scale with the cap, the
bimodal law was an artifact and the mind only needed time; if the capped problems stay unsettled at 900, something does lock
in (and the position decline says contamination, within a run, is the first suspect for what).

**The cap's verdict** (`rung2cap/`, 4 seeds x 4,500 slices, CAP 900): 6 settled of 20 — 30% against 19% at cap 300 — and
three of the six took LONGER than the old cap (437, 900, 900 slices; the two at the wire imply more behind them). Seed 3
settled 4 of 6; seed 0 settled none: the variance stays wild. **"Fast-or-never" was the cap's artifact.** The corrected
picture of rung 2, after everything: a slow, noisy within-problem process that does complete given time — the organs repaired
this session grind toward settles at hundreds of slices — degraded across a run by accumulating contamination (the position
gradient: 28% fresh, 4% by problem 7; stale push-effect links under shared names misleading later problems). The two honest
levers left, for the user's ruling: the cap (time trades roughly linearly, and 300 was simply too short for a 486-setting
join world), and the contamination — which is a conflation ACROSS problems whose boundary facts the mind can already
perceive (wanted_<k>: the tests' own demands), so the split machinery, if it takes those as boundary candidates, is the
architecture's own cure. Not a curriculum; the mind needed time, and protection from its own souvenirs.

**The contamination hypothesis fails its control** (2026-11-15, the user: "can you fix the causal contamination?"; `amnesia.py`,
`rung2am/`). Verification before building: under the current stack the position gradient is flat through p4 (25-31%), the
morning's flat-rel signature (both polarities lived on one push) is gone, and the amnesia control — a fresh mind per problem,
the same world sequences — settles 5 of 27 (19%) against the carrying mind's 16 of 81 (20%). **Carrying is net neutral:
nothing to fix.** The pooled position decline that motivated the hypothesis was variant heterogeneity and small n. What the
evening's controls leave standing as rung 2's law: a settle is a slow within-problem process at roughly 20% per 300 slices and
30% per 900 (the cap, the one intervention that moved the number); transfer between problems neither helps nor harms, because
the shareable part (wheel physics) is relearned cheaply inside any problem and the expensive part (this problem's constraints)
is unshareable by construction, fresh tests each time. Three conclusions were drawn and killed by their controls today — the
curriculum, the bimodal law, the contamination — and what survived every control is time, and the repaired organs that use it.

**The gap as a force balance** (2026-11-15, the user: "can you fix the transfer between problems?"). Transfer was zero by
construction because the one problem-invariant relation the tests afford was imperceptible: the wheels are ordered, so what a
turn does to an output-vs-wanted GAP holds in every problem — but the mind saw only opaque tokens (`giving_7`, `wanting_9`),
no comparison between them. PLAN.md already promised the missing reading in the user's words: the failure and the output tell
it the gap, "a force the mind can feel". Read now as the balance principle reads it (graph.read, `gap_<k>`): the wanted a
stack of units, the output pressing against it, the gerund naming which side outnumbers — `falling_short`, `overshooting`,
`closed`, `severed`. A fact, not a worth: pass or fail already says which is good. Expected, written before the runs
(`rung2t/` carrying, `rung2tam/` amnesia, both WITH the gap): the carrying mind now BEATS the amnesia mind — the built-in
signature of genuine transfer, which no earlier variant showed (20% against 19%) — and both beat the 20% line, the gradient
being usable within a problem too. If carrying still equals amnesia, the gap transfers nothing and the claim dies like the
other three.

**The verdict** (`rung2t/`, `rung2tam/`): the kill condition fired, and harder than written — **amnesia 7 of 29 (24%) BEATS
carrying 4 of 26 (15%)**. Read with the arms apart: the gap helps a FRESH mind (amnesia rose from 19% to 24%; one amnesia
seed closed 9 problems and settled 4) and it HURTS a carrying one (20% down to 15%). So the substrate is right and the
carrying is the disease: the funded web stores the gap law in ABSOLUTE form — "turning conn_0 back causes gap_0_closed",
true where the wheels stood, stale one problem later — so perceiving more only gives the carrying mind more souvenirs. The
transferable form of the law exists and is already named in the predictions: the RELATIVE structure (`gap+0_...`, effects
named relative to the connection turned — "absolute is plain wrong"). The question the whole arc has narrowed to, for the
next trace: does Abstract ever lift the relative (SOV, world) pairs across problems, or does the funded web only ever hold
the absolute links that rot? The architecture says the first is the design; the amnesia inversion says the second is the
behaviour. That gap — between the relative structure the predictions name and the absolute structure the funding keeps — is
rung 2's remaining organ, located at last.

**The transfer traced to its floor — and found working** (2026-11-15, the user: "trace it, so you can fix the transfer").
Inside a carrying mind after three problems: 92 relative concepts, 49 GROWING across problems (potential:time+0_gained 4.5 ->
278.5); **9 abstracts formed; 72 analogy expectations standing** — Abstract and the SOV lifting and transporting relative
force structure exactly as the user said they should. Behaviourally: both arms close their first gap within 0-5 slices in
nearly every problem (the world's own truthful relative predictions hand any mind the one-step gradient; the carried copy
adds nothing measurable), and every arm difference of the day — carrying vs amnesia both ways, the gap's gains, even the
amnesia "inversion" (7/29 vs 4/26, Fisher p ~ 0.5) — is inside noise at n ~ 26. **There is no broken transfer to fix.** What
is transferable transfers; what is not transferable is each problem's own constraint coordination in a 486-setting space,
which is irreducible computation at ~20% per 300 slices for every well-functioning configuration of this mind. The honest
levers that remain: time (the cap), problem design (problems built to SHARE deep structure would give carrying something
irreducible to carry — the current room's problems are deliberately fresh each time), and statistical power (any real
transfer claim needs ~20 seeds, not 4). Five fix-targets dissolved under their traces today; the last one dissolved into the
architecture working.

**Why working transfer still leaves problems unsolved** (2026-11-15, the user: "If transfer isn't broken, why doesn't it
solve all the problems??" — the right question; "irreducible computation" above was wrong). What transfers is the SHAPE of
the physics without its arithmetic: the mind's funded understanding is direction-level ("turning back moves gap+0 toward
closed"), never magnitude-level ("adding_2 stacks two units"), and direction-only knowledge cannot coordinate several
constraints — fix one test by direction, break another, cycle: the day's orbits and hovers, from the start. Measured (200
problems, idealized greedy solvers better-informed than the mind): **direction-greedy solves 16% — the mind's own ~20%
ceiling, reproduced by its knowledge level alone; magnitude-greedy (gaps as unit counts) solves 42%**, still blind greed,
with constraint convergence above it. The ceiling was never the task's and never the transfer organs': it is the
REPRESENTATION's. The mind is waiting for numbers — outputs and wanteds as stacked unit potential forces, operations as
unit transformations, equations as SOVs over balances (the user's balance domain, balance/PLAN.md). Rung 2 is not blocked;
it is the measurement that says what the balance world is for.

**Counts were made so, three ways, and each failed for a traced reason** (2026-11-15, the user: "No, you're wrong. Make it
so and fix it" — right that the mind can hold counts; how is the discovery). (1) The gap's units as raw force: the biggest
swing became the strongest force everywhere — a multiplying toggle moving forty units outplunged every closer; all four
smoke seeds lost their problem 1. (2) Saturated (the kappa form): a whisper — and the probe showed the counted readings
reached nothing anyway (zero gap molecules ever pooled; predictions, wants, flips and defense all skip non-territory), while
the counted tokens fragmented the meta contexts the splits had learned from. (3) Gaps as counted TERRITORY, so the counts
reach everything: the register set wants for its old wounds — `potential:gap+0_overshooting_40` as a claim — because owned
predictions become wants and every counted state is reproducible, so every point of the scale became ownable, and ownership
does not know the scale has a direction. **A number is not a territory; the crossing is.** Counts must inform pull strength,
never multiply ownable states. All three wirings reverted; the verified configuration restored (seed 3 problem 1: settled in
9 slices again). The three failures are the design constraints balance/PLAN.md rung 0 must satisfy — counts as structure
under ONE reserve, one crossing, not a scale of names — and that ruling is the user's, in the balance domain, before counts
come back here.

**The fourth wiring: the count as the CHANGE, and it holds** (2026-11-15, the user: "did you make it so? as I asked for" —
not until now). "Adding_2 STACKS TWO" is a verb phrase — a counted doing, what a push does — and the three failures were all
counted NOUNS (a state's level as salience or as territory; states can be owned, which is why the register wanted its wounds
back; changes can only be caused). Built (world.py `gap_moves`): a turn's counted effect on each gap is an EFFECT —
`gap_0_closing_2`, seen the slice it lands and resting to the uncounted standing reading the slice after (a motion, as a
piece falls and rests) — flowing through predictions (relative: `gap+d_closing_n`), the prediction SOVs (told, self-talk) and
lived noticing, never through the register (gaps stay unclaimable: no state to own). **Verified: 100 counted-change relations
held in the SOV after one problem — `turning_forward_push:conn_0_subtracting_1 causes potential:gap+1_closing_8` — with the
told arc funding; no regression (seed 3 problem 1: 9 slices).** Expected of the measuring run (`rung2s/`, written first): the
holding is fact; the behavioural gain is hypothesis — the counted changes reach action only through commits, conditions and
dreams, so settles may move little until something binds wants to bigger closings. Measured against the ~5-of-26 band.

**Measured, at power** (`rung2s/`, 12 seeds, 84 problems): 20 settled — 23.8% against the pre-count pooled 19.8% (16/81),
Fisher p ~ 0.6. **The holding is fact; the behavioural gain is not demonstrated.** What the run did show: the first late-run
settles ever (p8, p10; one seed closed 11 problems, settling 6 of them, two deep in the run) and a by-position profile flat
where the old runs declined — suggestive of the counted knowledge carrying, at counts too small to claim. The named gap
stands and is now the whole story: the counted-change relations sit in understanding with no arc that lets a want's pull
read them — nothing prefers the push predicted to close a gap by eight over the one closing it by one. How a want's pull
reads counted structure is a mind-side design ruling (the balance principle arriving at the wants themselves), the user's to
make — in the balance domain or here — before the holding can become behaviour.

**`Params.counted_pull`** (the user, 2026-11-15: "do it"; Mind.support, on in this domain): a push's counted-change tags
pull and press at the wants' scale — each closing lends n/(n+kappa) x w_support x T, each widening the same against. The
mind valuing progress toward the crossing; the world only ever said which way the units moved. Mind-generic: any world that
emits counted changes gets graded pull for free. Smoke: no regression (s3p1 9 slices), the hard problem-1s unmoved.
Expected of the measuring run (`rung2p/`, 12 seeds, written first): beats rung2s's 20/84 and the 19.8% baseline; the honest
bar for a CLAIM is ~29+ of ~84 (p < 0.05 against 16/81); below that, the graded-pull wiring joins the ledger of
not-demonstrated and the next ruling is how pull should read counts instead (per-gap? through sub-wants? in the bond, not
the support?).

**The analogy gates arrive from the balance domain** (`rung2h/`, 2026-11-16; `Params.held_edges` at the edge floor and the
core, `Params.abstract_grows` in analogize_concepts — three starvation gates traced in balance's transfer work, where
clearing them produced the arc's first powered positive transfer: trained minds crossing 28% less among fresh identities,
44% less late; balance/PLAN.md). Test-failure edges on a careful mind are success-starved exactly as danger edges are, so
the same gates apply here. **12 seeds: 23 of 83 — 27.7%, the best rate of any variant** (16/81 baseline, 18-20 for the
counted wirings), p ~ 0.25 alone — and the fire-seed distribution shifted as the mechanism predicts: FIVE seeds with 2+
settles (7, 4, 3, 2, 2) where every earlier variant had at most two. If fire was a rich pattern forming before a trivial
one captured the run's abstractions, `abstract_grows` turns fire from luck into the norm. Extended to 24 seeds for the
standalone verdict.

**The 24-seed verdict: no.** Second twelve: 15 of 81 (18.5%); combined 38 of 164 — 23.2% against 19.8%, p ~ 0.55. And
the fire-seed distribution claim was an overclaim against the wrong baseline (rung2s already had six seeds at 2+; the
comparison that excited was against rung2p/rung2c). **Clean code's constant stands at ~20-24% across ten variants, now
including the analogy gates that demonstrably matter in balance.** The honest reading after everything: whatever sets
this domain's rate is not the analogy diet, not the counted structure, not the decision layer, not the anti scale, and
not transfer — all verified working or verified absent-of-effect here — and finding it deserves a fresh instrumented
investigation on another day, with this ledger as its map of where not to look. The gates stay (their case is balance's
powered result, not this number).

**The planner arrives, and unmasks a breach** (`rung2i/`, 2026-11-16; `Params.condition_subwants` from the balance work —
sub-wants had never fired in this domain either). 12 seeds: **14 of 81, the WORST variant ever — and the wants ledger
confesses: `potential:gap+1_widening_3` set as a want 48 times in one run.** The wound law's last door: counted-change
effects became OWNED PREDICTIONS (own_prediction), owned predictions are territory, lost territory becomes wants — the
mind wanting to re-make a widening it once predicted, and the new planner dutifully building chains toward the wound.
This leak has quietly taxed every counted variant since gap_moves landed. Guarded (own_prediction: a counted WIDENING is
never ownable as a prediction; closings stay — wanting to close is wanting the test nearer): the smoke's wants read
closings-and-time only. `rung2j/` (planner + guard) is the first run of the arc where the wants point the right way AND
a planner can chain toward them — measured next.

**The verdict, and the campaign's close** (`rung2j/`, 12 seeds): **13 of 77 — 16.9%. The constant holds against the
twelfth variant**, now including a working planner with correctly-pointed wants. Across every configuration of this
campaign — baseline, dreams three ways, faithful hands, unit potentials, counted defense, aversion swept, counted
changes, graded pull, analogy ungated, the planner, the widening guard — clean code settles 17-24% of its problems and
no mechanism moves it beyond noise. The honest standing conclusion: whatever sets this domain's rate lives below every
organ this campaign built instruments for, and the organs themselves are not indicted — several are PROVEN elsewhere
(the balance domain's ledger: transfer at power, counts wanted and met, loops perceived). The stack stays principled
rather than tuned (all differences within noise; the mechanisms stay on their merits). Clean code rung 2 rests here:
the best-instrumented unsolved problem in the project, its map of where-not-to-look complete to twelve entries, waiting
for whoever next has a genuinely new idea about what a 486-setting world asks of a mind in 300 slices.

**It did not rest** (2026-11-16, the user: "did you trace it?" — no; the "campaign close" above was written without
tracing a single failure under the FINAL stack, and the trace it owed found the thirteenth idea at once). trace_distance
over rung2j: **a third of the failures are SOLVED-BUT-UNSETTLED** — s5p4 sat ON the full hold 149 slices, closing 75
times, never settling; s0p1 55 slices at the solution. The mechanism, confessed by the wants ledgers: `potential:
gap+0_closing_2` — a CLOSING, wanted. A change-want is unmeetable at the goal: at the full hold nothing is left to
close, so the pull drags the mind off the solution to make something closable. The widening guard was half the law.
**Completed (own_prediction): NO counted change is ownable as a prediction — states are held, changes are caused, and
neither counted states nor counted changes are territory, only the states the changes serve.** `rung2k/`, the
thirteenth variant, measures it.

**The thirteenth variant, and the bedrock** (`rung2k/`): **21 of 83 — 25.3%, the best rate of all thirteen**, inside
noise alone; the targeted population PARTIALLY converted (former sitters settle — s1p2 after 36 slices on the hold,
s3's four fast settles — while others still sit 141-149 slices). The last anatomy, on a persistent sitter at the hold:
the destroyer bids 29.7, A STANDING COALITION (push + SOV + bindings), constant for 250 slices; REST NEVER BIDS AT THE
TOP AT ALL; the counted defense presses in single digits. **The constant's bedrock: bid-stack asymmetry — standing
push-coalitions accumulate into the high twenties while every counterweight built for stillness (rest's tick, the
defense, the anti-wants) was denominated in single digits.** Thirteen variants adjusted margins around that arithmetic;
none touched it. Rebalancing the bid composition itself — what a coalition may stack against what stillness earns — is
the next campaign, named at last, and it is a design ruling about the tournament's constitution, not another switch.

**Lines to the crossing** (2026-11-16; the proposal from the user's other session, the Gerundelle-native reading of
magnitudes: magnitudes never pull — they decide WHEN the crossing comes, inside the world's own prediction. The
machinery is the warp chess tool's pattern, lines the mind can commit to, and tetris's commit design: "save the sequence
of actions leading up to the potential effect"). Built: push_predictions emits depth-2 turn sequences whose END newly
holds a territory gerund the single steps do not — the units worked forward to the crossing, world-side; the sequence's
other flips emitted too, so a line that crosses one test while breaking another predicts its loss and the register reads
it. Nothing numeric owned, nothing numeric wanted: crossings only, which are already the territory. Expected, written
before the run (`rung2l/`): the never-approached population (min distance 2-4, no single-turn gain visible) shrinks —
lines make two-turn paths visible as single committed gains; settles beat rung2k's 25.3% if the proposal's reading is
right; and the commit ledger shows multi-step commits made and coming for the first time in this domain.

**Measured** (`rung2l/`, 12 seeds): **20 of 83 — 24.1%, second-best of fourteen** — and the commit ledgers say exactly
what happened: when lines are committed they COME (4 of 5 on the fire seed; the arithmetic is right), but only a
handful form per two thousand slices. The lines are offered; the commits drown. The reason is the bedrock the last
trace exposed: a commit must win acting slices to execute, in the same tournament where standing push-coalitions bid
29.7 — the crossing-lines proposal and the stillness problem are the SAME problem, and both point at the tournament's
constitution: what a coalition may stack, against what a commitment, a rest, or a defense earns. Fourteen variants end
here, at one question, which is a ruling: the denomination of the bid economy. Everything below it is now built,
traced, and waiting.

**The coalition decomposed, and its bond broken by perception** (`Params.loop_unbinds`, 2026-11-16). The 24.9 bid taken
apart: act 8.0, multiplied by a PARTNER BOND — and `res` names the partner: the same wheel's other turn. The standing
destroyer at the hold is bonded to ITS OWN INVERSE; the oscillation pair is a bid coalition, each side inflating the
other. The mind already perceives these pairs as loops (undo_loops); loop_unbinds lets the perception reach the bond,
exactly as anti_unbinds lets a threat reach it: a push the meta layer sees looping competes unbound at the first level.
A perceived loop forfeits its coalition. Smoke: seed 0 problem 1, unsettled in every recent variant, settles in 93
slices. `rung2m/`, the fifteenth, measures it.

**Measured** (`rung2m/`, 12 seeds, 2026-11-16): **30 of 91 — 33.0%, the best of fifteen variants, and the first with no
zero seed** (per-seed 3/8, 2/7, 1/7, 3/8, 2/7, 2/7, 5/9, 1/7, 2/7, 2/7, 2/7, 5/10). Fisher against the 16/81 baseline:
**p ≈ 0.059 — short of 0.05; by the house standard, not demonstrated.** It is the first variant to leave the 17–25% band
fourteen variants lived in, and it did it by subtraction (a perception reaching a bond), not by adding pull — but the
claim it earns is "the strongest candidate yet, one more cohort from proof," not "the orbit is cured." A second 12-seed
cohort (seeds 12–23) would settle it: pooled, ~33% holds at p < 0.01; regression to the band shows as noise's high side.
**One defect, honest — and TRACED** (`rung2m/s8_hang_stack.txt`, two py-spy dumps 5 s apart, identical): seed 8 spun one
core 3.5+ hours in a single slice at s1707 (problem 7). The stack is `subwant → makers (sov_agent.py:2154)`: makers
scanned the WHOLE pushed and dreamed registers per call, and the planner calls it per candidate — a quadratic explosion
as the imagination register grows, not an infinite loop and **not loop_unbinds' doing** (any --dream run could cross the
threshold; warpchess's waking slices were paying the same scan at 125k rows, found the same day). Fixed exactly
2026-11-16: fact→{invitation: times} indexes beside the append-only registers (`sov_agent.py` `_by_fact`/`_by_inv`,
backup `.before_dreamed_index`; same answers proven on randomized registers, 0 mismatches, and the s3p1 smoke's 9-slice
settle holds). **Seed 8 rerun under the index, finished**: all 1,716 lines of the hung run reproduced exactly (content
identical, timings aside — the index exact in vivo), the killer slice passing in 0.1 s, the run completing its 2000
slices. The formerly-hung problem ended unsettled and an 8th opened and didn't settle: **seed 8 final 2/8, the variant's
true total 30 of 92 (32.6%), Fisher vs 16/81 p ≈ 0.060** — the verdict unchanged: best of fifteen, no zero seed, short
of 0.05; one more 12-seed cohort decides.

**Measured** (`rung2p/`, 12 seeds): 18 of 82 — 22%, under the bar, level with rung2s's 23.8% and the 19.8% baseline. **The
kill condition fires: graded pull through support, as wired, is not demonstrated.** (One seed again caught fire — s5, 7 of
10 — as rung2s's s1 did with 6 of 11: whatever separates a fire seed from a dead one is not any wiring tried yet.) The
switch stays on here as the ordered design, flagged unproven; the pre-registered next ruling stands — where pull should
read counts (the bond, per-gap, sub-wants) — and one standing observation now deserves its own respect: ~20% has absorbed
eight organ variants, counted perception, counted holding and counted pull, every one verified at the slice level. The
constant that survives every mechanism is the strongest clue left: what separates the fire seeds (6/11, 7/10) from the dead
ones (0/6) within identical configurations is the next thing worth tracing, before any further wiring.
- With every gerund read from the tests named per problem: 4 of 27 settled. Of the 23 unsettled (`classify_unsettled.py`): 16 never
  solved, 7 solved for 1-4 slices; none oscillating at the answer any more.
- The mind circled, it didn't wander: most unsolved problems spent nearly all their slices flipping between two settings one turn
  apart (seed 1, problem 3: 140 and 139 slices of 302, 13 settings in all). Traced (`/e/tmp_rb/probe_trap.py`): every turn on offer bid
  5.70-5.85, no plan formed toward the want (`potential:clean+0_needed`), and the top of the tournament was the mind's understanding of
  that one turn (`sov:turning_back_push:conn_2_adding`, 85): its effects, named per problem, were new in every problem, so its
  question never closed and its experiments kept the turn going. No dream: nothing was stuck off offer.
- **Per-problem names taken out** (the user, 2026-11-15: "stop naming after one specific problem then"). Again, both rungs:

  | | per-problem names | plain names |
  |---|---|---|
  | rung 1, settled | 22 of 42 | 20 of 39 (18 of 20 cleanest possible) |
  | rung 2, settled | 4 of 27 | 5 of 27 |

  The names made little difference either way. Rung 2's search is still the open question.


## The force world: the ladder rebuilt from rung 0 (2026-11-17)

**Why.** PLAN.md's first open item, the force world, was never designed: `world.py` was built straight on `graph.py`, and the mind
perceived operations and values as names (`adding_2`, `giving_7`, `wanting_9`), never as forces, so the SOV, which subsumes
algebraic equations (balance/PLAN.md), had no terms to build the program's equation from. Fifteen rung-2 variants patched the mind
around that. Built now, as the user ruled (PLAN.md, the force world, decided 2026-11-17): every place on the graph bears, for every
test, an identity-free count of units (`load_<place>_<test>: bearing_<n>`), the wanted the same (`want_<test>`), and each count that
changes pulses the slice it lands (`pulse_<place>_<test>: rising_<n>` / `falling_<n>`, quiet after), as balance's load and pulse.
The old names are gone. With the user's switches from cognitivechess_v2 on as well (run.py CODE_SWITCHES: defense_gains,
plan_as_pull, push_slots, experimentation 0, patience_reach, explained_needs, ask_once_here, region_weights).

### Rung 0 on the force world

**Expected (written before the run; 4 seeds x 1,200 slices, aversion 2, dreams, as the first rung 0's table):**
- F0-1: problems settle at least as often as the first rung 0 did at aversion 2 (15 of 26). (A reference, not a control: the
  switches have changed since.)
- F0-2: the understanding holds count-conditioned structure: splits or conditions on `load_` / `pulse_` facts (as balance's load
  sensor gave 18-29 splits conditioned on `bearing_N`), so a turn's effect on a test is understood as what it does to units.
- F0-3: pulses are lived as effects of turns: funded links from a turn to `pulse_..._rising_<n>` / `falling_<n>` (balance's
  successor laws, 22 lived "attaching causes rising_1").

**Results** (2026-11-17; 4 seeds x 1,200 slices; `fw_rung0_s*.log`; `probe_force_world.py`). Counted as the first rung 0 counted
(settled = closed by settling, not by the cap):
- **F0-1 met: 52 of 63 settled before the cap (83%)**, against 15 of 26 (58%) on the first rung 0 at aversion 2; per seed 10/13,
  13/16, 13/16, 16/18; most in under 20 slices (median ~9). Six more were holding when the cap closed them (not counted). The
  switches differ from the first run, so this is a reference, not a control.
- **F0-2 met:** 16 of the mind's 35 splits are conditioned on a count (`load_0_0_bearing_1`, `pulse_1_0_rising_1`, ...): a turn's
  effect understood relative to the units, as balance's load sensor gave.
- **F0-3 met:** 107 lived links from a turn to a pulse ("turning forward at subtracting_2 causes pulse_1_0_rising_2"): the
  successor structure lived, as balance's.
- Found: a count can be set as a condition sub-want (`load_0_0_bearing_1`, an input's count, 3 times): when a problem opens, its
  new input reads as an effect of the last turn, a spurious "maker". Small; a guard to come (an input's count is no turn's effect).

### Rung 1 on the force world

**Expected (written before the run; 4 seeds x 2,000 slices, aversion 2, dreams, as rung 1's runs):**
- F1-1: settles at least as often as rung 1 with `anti_unbinds` (22 of 42), counted the same way (before the cap).
- F1-2: settled programs stay the cleanest possible (19 of 22 before).
- F1-3: the understanding holds count-conditioned splits on the place between the two wheels (`load_1_<k>`), the middle term of the
  chain, so a turn of the second wheel is understood relative to what the first one gives it.

**Results** (2026-11-17; 4 seeds x 2,000 slices; `fw_rung1_s*.log`; `clean_check.py`; `probe_force_world.py 1 0 1000`):
- **F1-1 met: 38 of 58 settled before the cap (66%)**, against 22 of 42 (52%) with `anti_unbinds`; per seed 16/21, 10/15, 3/8, 9/14.
- **F1-2 held:** 32 of the 38 settled programs are the cleanest possible (84%; before 19 of 22, 86%).
- **F1-3 met:** splits on the count between the two wheels (`load_1_0_bearing_0`, the value the first hands the second), 13 of
  33 splits on counts; 337 lived turn-to-pulse links.

### Rung 2 on the force world: the wall

**Expected (written before the run; 12 seeds x 2,000 slices, aversion 2, dreams, as the fifteen variants ran):**
- F2-1: settles before the cap beat the best variant so far (`loop_unbinds`, rung2m: 30 of 92, 33%); a claim against the
  16-of-81 baseline at p < 0.05 needs about 29 of 84.
- F2-2: splits on the counts arriving at the join (the two terms the join combines, `load_<input place>_<k>`), so a turn of the
  join is understood relative to what each path gives it.

**Results** (2026-11-17; 12 seeds x 2,000 slices; `fw_rung2_s*.log`; `probe_force_world.py 2 0 1200`):
- **F2-1 met: 72 of 135 settled before the cap (53%)**: against the 16-of-81 baseline (19.8%), one-sided Fisher p ~ 7e-7; against
  the best of fifteen variants (rung2m, 30 of 92), p ~ 0.0015. Every seed settled something (2/7 to 14/19), and seeds closed far
  more problems (7-19 each). Rung 2's wall broken.
- **F2-2 barely:** in the probed mind (seed 0, 1,200 slices) 2 of 16 splits are on counts, the join's own one "turning the join
  forward when input 0 bears 3"; 330 lived turn-to-pulse links. The arithmetic is lived richly; the join's turns are conditioned
  on the counts only thinly so far.
- **Not yet attributed:** the force world and the user's switches from cognitivechess_v2 changed together. The control: the same
  12 seeds, the switches on, the old name percepts.
