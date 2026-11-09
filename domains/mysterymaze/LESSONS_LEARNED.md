# Mystery maze: lessons learned (2026-11-07 to 2026-11-09)

The goal: a web page showing a Gerundelle mind learning monotonically to find the cheese in a grounded maze. This file records what two days of building and tracing taught, so it isn't learned again. The maze is `maze.py`, the run is `run.py`, the dream is `dream_maze.py`; the Gerundelle switches named here are in `reference/v2` (all off by default).

## 1. The world: ground everything

- **Build on forces, never a state machine.** The first maze was labels switched by if-statements, and a day of patching the mind followed. A mind run on symbols has Harnad's grounding problem; the force world is what grounds Gerundelle (objects, forces, potential forces).
- **Anything a force acts on is an object.** Positions (walked onto), walls (spoken to), the controller (pressed), the voice (the words' doer), the cheese. A wall's state belonged on the position in front at first, so one fact meant different walls from different sides.
- **Every reading is a doing, never a state.** `bearing`, `free`, `pressed`, `blocking`, `yielding`, `pointing_east`, `resting`, `borne`; not `open`, `here`, `unseen`, `absent`, `had`. A label I invented (`body: pressing/free`) became a confound with the cheese and cost hours.
- **A potential force reads what the push would do to what it reaches.** The mind perceives a wall's type through the words' forces on it: 3 with no reserve against it (its own word), 2 where its reserve holds, 1 reaching nothing. A force that is the same whatever it acts on is a label (every word read 2 at every wall at first).
- **No news.** The world narrating changes to the mind is sabotage; the mind notices changes itself, against what it last perceived (things out of view remembered). Coming into view is not a change (the mind read seeing a wall as its walk opening it).
- **Offer only what is legal, and only what has something to act on** (a word only facing a closed wall, as a walk only onto a free position).
- **The world says what a push reaches** (`reaches`): a word the wall in front, a walk the position it pushes off from and the one it lands on, a button the controller.

## 2. The mind: what was missing, found by tracing

Each line: the failure a trace showed, and the fix (its switch).

- Ties broken by the alphabet: conditions split on the first name (`did_*` won every tie) → hold tied conditions in superposition, the outcome collapses them (`split_superposition`); tied sub-want candidates set by name (a wall wanted closed again) → none set until something separates them (`tie_superposition`).
- Stale halves of one push competing at once → a wrong half leaves with its descendants (`reread_whole`).
- A move not on offer supported pushes for conditions already met → only unmet ones (`setup_unmet`); and only if it serves a held want (`setup_for_wants`).
- A held want counted as arriving every slice, so nothing could be seen to precede the cheese → wants aren't arrivals (`wants_not_arrivals`); the SOV couldn't link a rare event to its reliable company → read evidence against the rarer event (`predecessor_evidence`).
- The dream (`dream_maze.py`): the cheese's company was a confound only another approach breaks; the dream reaches it, promotes what survives to an imagined cause, which supports a sub-want (`stack_supports`). The tournament, not my list order, chooses which manipulations the dream follows.
- An untried push chosen for the worth of the line behind it → a push expected to change nothing has no line of its own (`lines_need_change`).
- Dropped sub-wants stayed in the pool as wants and froze the mind → a want leaves the pool once not pursued; only the current goal competes (`held_wants_only`).
- A word said anywhere counted as a failed claim on every wall it ever opened → a push tries only what its force reaches now (`force_reach_claims`).
- The way from position to position: standing on one affords walking onto the next (form 14, enable; `relations/RELATION_TYPES.md`) → what holds whenever a push is offered enables it, kept per way in (`affords_chain`).
- A loop's own pushes were lifted by the loop → the loop lifts only pushes outside it, judged by this loop, not any old one (`loop_spares_looping`).
- A way's needs set one at a time, the heading undone on the way, 107 times in one trip → want the way whole, the planner finds the order (`ways_whole`).
- Unexplained events (the maze resetting) pull forever → the mind can let a question go, released from attention, not forgotten, until something new arrives; when is temperament (`acceptance`).

## 3. What failed, and why (reverted or left off)

- **Blame from "caused by"** blamed the pushes that had helped, not what was in the way.
- **Every tie in the tournament's slots held at once** flooded the top level (up to 86 winners).
- **Splits with no count gate** made things worse; built on an explanation I hadn't checked.
- **A lived condition closing the conditions question** stopped the experiments that find more conditions. Knowing one condition is where the next question starts.
- **Lived relations as analogy edges** removed every abstraction instead.
- **Enablers from what held at every offer** threw away every way in but what never changes.

## 4. How to work on it

- Trace before fixing, and report traces, not reasoning. Most of my wrong turns came from stating an untraced explanation as fact.
- When a trace says "next", run it at once; don't wait to be asked.
- Judge a change over the five mazes, one change at a time; single runs swung from 254 slices to no cheese.
- When the mind misbehaves, look at the world's forces first; most fixes to the mind were patches over my world.
- Read each reading for what it is in the theory, not how it looks in code. Don't add rules; find the structure that already decides it, or ask.
- The human metaphor usually points at the mechanism: cued recall, blame, affordances, a loop, letting go.

## 5. Results (5 mazes, 2,000 slices each, cheeses reached)

| Setup | Total | Note |
|---|---|---|
| state-machine maze, first build | 1 in 20 runs | seed 0 only |
| forces, before today's fixes | 9 | |
| + dream, tournament-chosen | 25 | |
| + dropped wants leave the pool | 36 | |
| + force-reach claims | 39 | |
| + affords chain (per way in) | 31–49 | |
| + only the goal in the pool | 63 | every maze ten times or more |
| + ways whole | 59 | worst trip 957 → 665 |
| + acceptance 6 | **78** | seed 0: last 15 trips 42–86 slices |
| + acceptance 3 | 44 | letting go too quickly |

## 6. Open

- Monotonic learning holds on seed 0 (and nearly seed 3) at acceptance 6, not on every maze; long trips still occur.
- Letting go quickly may release questions the mind still needs (seed 2 at acceptance 3: three trips of 24 slices, then none).
- My choice, not the user's: the maze closes every opened wall at each reset, so words are relearned each trip; and the reset itself is an unexplained event to the mind.
- The confound experiment (`confound_experiments`) never fired; the dream did that work.
