# When the agent doesn't move, and what was done about it

A map of every mechanism that prevents the chess agent from going idle, each found as a traced failure in the
cognitive chess ladder. Written 2026-11-01 from `LADDER.md`, `HOW_IT_WORKS.md`, `chessworld.py`, `rung*.py`,
and `sov_agent.py`.

## The symptom

Each tick, `SovAgent.tick` perceives the board, runs the mind's tournament, and chooses a push. When nothing
wins (no experiment, no planned step, no noticed move), it calls `self.idle()`: one slice passes with no move
of White's, and the world reports whatever else changed. After `IDLE` (6) slices with no move the episode ends
and the position resets.

Before the idle limit was added, a mind with nothing worth doing simply never moved. Rung 1e, seed 4: 120
pushes in 800 ticks against 397 in other seeds. The episode waited for White's second move however long.

## The causes, in the order they were found

### 1. The planner has no actions

**Rung 1's failure.** `Model.actions` offers a push only where its configuration (the third part of the
invitation, `<object>_<gerund>`) is among the current facts. With the original fixed configuration `'piece'`,
that string was never a fact. The planner had zero actions in every chess position, so `plan_step` always
returned None, and no arm won a defended episode.

**The fix (rung 1).** A piece is two perceived objects: the piece itself (`present`, `captured`, `absent`) and
its safety (`<piece>_safety`: `safe`, `attacked`, `hanging`; a king's `safe`, `checked`, `mated`). A move's
configuration is the piece being present, a stable fact. Safety is a relation, perceived separately.

**Effect.** Rung 1 went from 0 defended episodes won to 535 (both arms). Rung 0 median tries fell from 6.5 to
5.

### 2. The planner's first push drowns in moves from other positions

**Rung 1, seed 6.** The planner knew Rxd5 wins (value 1.0 when asked directly). But `Model.actions` offered
every push the mind had ever known whose configuration held, including 75 rook moves seen from other squares
(Ra4, Re4, Rc6). Against a budget of 60 rollouts, MCTS chose Rc6, which was not on the board, and `plan_step`
returns only a move the world offers. In 23 of 28 cases where the knight hung, the planner found nothing.

**The fix (rung 1).** The first push of a plan is chosen from the pushes the world offers now (perceived);
deeper pushes come from the model. `Model(agent, goal, root=(state now, pushes offered))`, used by `plan_step`.

**Effect.** Rung 1 defended wins doubled (379 to 700 with both arms), and every seed found the combination.

### 3. Sub-wants that loop or linger

**Rung 3, seed 0.** The mind set the sub-want `material_even`, which already held (material was even). It was
"met" at once, the parent want taken up, the planner found no way, and the same sub-want was set again, every
three ticks, while playing Rxd5 and losing the exchange. Zero defended episodes won in 88 tries.

**Rung 1e.** With `sub_cost` blocking the costly means to a sub-want, the sub-want was not met at once (by the
sacrifice) and lingered up to its budget of 80 ticks. It was served at the start of the next episodes even
where the mate was on the board. About a tenth fewer mates.

**The fixes (rung 1e).**
- `Params.sub_yield`: a sub-want that already holds is had at once. And while sub-wants are stacked, the
  planner is asked about the root want; if it finds a way (not contradicted), the stack is dropped and the way
  is taken.
- `Params.sub_tested`: a split's condition is wanted only where the split's other half holds records (a
  condition never seen absent is not known to matter). Without this, a nested split whose other half was empty
  set "material down" as a want, and the mind met it by sacrificing a rook.

**Effect.** The lingering sub-wants were gone. Rung 1 defended wins rose from 693 to 700; rung 1c clean mates
from 107 to 168.

### 4. A coincidental condition, made true at a cost

**Rung 1c, seed 5.** The mind learned "Re8 mates when the f7 pawn is attacked" (true where it first mated,
after Rd7). It set the sub-want "f7 attacked", met it with Rd7, 326 times. Episodes here were one White move,
so the Re8 it prepared never came.

**Rung 1, seed 6 (after the label fix).** Learned "Rxd5 wins when my bishop on a6 is hanging", and lost the
exchange 43 times making it so. The tag was the bishop's rather than the knight's because at the first contrast
both were new and Gerundelle prefers the fact the mind's own last push made.

**The fixes (rung 1c).**
- Two-move episodes for rung 1c, so a sub-want can be followed by the move it prepared.
- `Params.sub_cost`: serving a sub-want, a push whose outcome moves the root want's object away from the root
  want, or changes something the way needs and has, is no means to it (`SovAgent.costly`, `SovAgent.undoes`,
  `Model.costly`).
- The world fix (cause 1 above) was what actually killed the "my bishop hanging" pathology: with a piece's
  safety split from its presence, the incidental state stopped entering the configuration.

### 5. Per-move learning alone can't reach new positions

**Rung 1e without convergence.** Each move's condition is learned from its own tries, so an untried move in a
new position has no record, no condition, no plan, and no sub-want. The agent idles or explores at random.
55 of 200 positions mated in 3000 ticks.

**The fix (rung 1d, ported into the agent at rung 1e): `Params.converge`.**
- Each root-want push records what the world said it would meet (`world.relations_of`) and what came of it.
- `constraints_from` extracts the smallest combination of relations each failure kind's attempts carried that
  no other attempt carried in full, weighted by receipts (1 - 1/2^n).
- `SovAgent.notice`: the untried push supported most in a tournament with candidate support (constraint
  molecules in superposition), ties by the push's order; nothing if the constraints don't tell the pushes
  apart.
- A direct way the planner finds that runs into a learned constraint is contradicted (not taken).
- Sub-wants come first; noticing is last.

**Effect.** 200 of 200 positions mated. 82-90 of 100 new positions mated at the first push.

### 6. Constraints say what fails but not what to change

**Rung 2, seed 2 (Stockfish coached).** The mind knew Rxd5 is taken ("a capture landing on a guarded square"),
constraints correctly vetoed it, but the mind had no condition about the knight to set as a sub-want. It knew
*that* the capture fails and not *what to change*. It went quiet.

**The fix (rung 2): `Params.bridge`.**
- Each time the mind considers a push, it keeps what the world said it would meet there, with the situation
  (`SovAgent.sample`).
- When a direct way is contradicted, the mind compares its samples: a fact present in every situation where the
  push would have cleared the constraints and absent from every one where it ran into them is what would clear
  them (`SovAgent.clearing`).
- If some known push makes that fact, it is set as a sub-want (`bridged`).

**Effect.** The traced seed went from 1 to 82 defended wins. Stockfish's word went from hurting (671 vs 773
alone) to helping a little (790 vs 770 alone).

## The stack, in the order `planned()` tries them

1. A sub-want that already holds is had (`sub_yield`).
2. If the planner finds a way to the root want, sub-wants yield.
3. `plan_step`: MCTS over the agent's own model, first push from real moves on offer.
4. A direct way that runs into a constraint is contradicted (`converge`); with `bridge`, its clearing fact is
   set as a sub-want.
5. Sub-wants: a way known's missing configuration or condition; or a situation never tried.
6. `notice`: the untried push the constraints converge on.
7. An experiment from inquiry.
8. Idle. After 6 idle slices the episode ends.

Each step is a `Params` switch, off by default, found by tracing a failure in a rung, and checked against
Gerundelle's suite before it was kept.

## What is still open

Problems traced in the ladder that can still leave the agent stuck or acting badly, and what the ladder's own
findings point to as next.

### The lesser loss: no reply meets the want

**The problem (finding 10, rungs 3 and on).** In a lost position (the defended configuration after the real
combination Bxb7), no reply restores material. The planner scores a reply only by whether it meets the want,
so every reply scores 0, and the mind runs experiments instead of taking back. Black takes back 33% of the
time when it could (46% as a keeper), not because taking back is unknown but because the planner can't prefer a
lesser loss over a greater one.

**What Gerundelle has.** `own_agent.py` values an outcome as the pulls it closes less the pulls it opens, and
acts on the best even when every option is negative. `Territory` makes a lost slot pull `1 + held`, and chess
pieces are now given territory (rung 3). But `SovAgent`'s planner does not read it: its reward is the share of
outcomes that met the want, and `plan_step` acts only when `v > 0`.

**What was proposed (LADDER.md, "The next rung").** Ranking outcomes by what they do to the territory (relation
form 12, competition/ranking). The planner would score replies by territory even when the want is not met, so
the reply that loses least is preferred. Arms: ranking off and on; scripted Black as control.

**The fix.** `Model.step` and `plan_step` fall back to territory when no path meets the want. `own_agent.py`
already computes this as `worth` (pulls closed minus pulls opened). The change: when `v <= 0` in `plan_step`,
score each available move by the territory change its predicted outcome would produce (lost slots opened, held
slots closed), and return the move that loses the least. The planner already has the territory register and
each move's predicted outcome from the meta register; it reads the territory pull on the outcome instead of
returning None. A `Params` switch (`Params.territory_fallback`, off by default) guards it.

### Coincidental conditions become sub-wants

**The problem (rungs 1c, 1, 1b, 3).** A condition from one contrast is acted on at once. A coincidental fact
(the f7 pawn attacked, the bishop hanging, the knight hanging when it was a bystander) becomes a sub-want, and
the mind spends hundreds of ticks making it true. The condition was never wrong where it was tested, so
contradiction has nothing to catch: self-confirmation.

**What was done.** `sub_cost` blocks means that undo the root want. `sub_tested` skips conditions never seen
absent. The world's piece/safety split removed some incidental states from the configuration. Constraint
receipts (1 - 1/2^n) let a constraint seen once weigh half. These reduced the pathology; they did not
eliminate it.

**What is still open.** A constraint seen once still weighs 0.5. A sub-want set from one contrast, even a
correct one, has no guard against the cost of making it true being higher than the benefit of the condition
holding. A mechanism that counts the cost of a sub-want's means against the benefit of what it enables is not
built.

**The fix.** Before setting a sub-want, estimate the cost of making it true against the benefit of the
condition holding. The benefit: the condition's success rate minus the unconditional rate, times the want's
pull. `constraints_from` already computes receipts per constraint; the same receipts give the condition's
evidence weight. The cost: what the means does to territory, from the agent's own records of that means
(its predicted outcome's territory change, as in the lesser-loss fix). A condition whose expected gain does
not exceed the expected cost of its means is not pursued. This generalizes `sub_cost` from "does it undo the
root want" (a binary check) to "does it cost more than it's worth" (a comparison). A `Params` switch
(`Params.sub_worth`, off by default) guards it, and the threshold (gain must exceed cost by at least a
margin) is a parameter.

### Fragmentation of a push's experience

**The problem (rung 3, finding 11).** A push tried a few times can be split three deep by the meta layer
(on safety states of pieces that happened to change). The half the current situation selects holds no records.
The push is treated as untried in this reading, and experiments are run.

**What is still open.** A split with too few records on one side might be a coincidence, and `sub_tested`
addresses the symptom (don't want a condition never seen absent), not the cause. A guard on splitting (minimum
records per half, or a minimum separation between the two halves' rates before a split is kept) is not built.

**The fix.** Guard not the formation of the split (that should stay sensitive) but the acting on it. A split
drives sub-wants through `SovAgent.needs`, which walks the split tree. It should skip a split whose smaller
half has fewer than N records (`Params.split_floor`, default 3). The split stays in the meta register and
accumulates evidence; it just does not drive sub-wants until its smaller half has earned enough. The meta
layer's `differentiate` already checks that each side has at least 2 outcomes and the minority is at least 25%
(`opposed`); this adds a floor on the minority's count before the split is trusted for planning.

### The sub-want loop

**The problem (rung 3, finding 6).** A sub-want that holds when set is met at once. The parent want is taken
up, the planner finds no way, and the same sub-want is set again. Every three ticks.

**What was done.** `sub_yield` catches the case where the root want's way is found while the sub-want is
stacked. The keeper's want switch-off catches the case where the state already holds.

**What is still open.** A sub-want that is met at once and set again (not because the root want's way is found
but because the planner still finds no other way) can still loop. A failed sub-want goes into `failed_subs`
and is not set again, but a sub-want that succeeds trivially is not failed. A cooldown or a count (don't set
the same sub-want twice running) is not built.

**The fix.** When a sub-want is met within 2 ticks of being set (it held already, or was made trivially), add
it to a cooldown set with a timer (`Params.sub_cooldown`, default 20 ticks). While cooled, it is not set
again. The `sub_log` already records when each sub-want was set and met, so the check is: if the met tick
minus the set tick is less than 2, cool it. After the cooldown expires, it can be set again (it is not
permanently failed, since the condition itself may be correct). This replaces the binary failed/not-failed
with a three-state: active, cooling, and failed.

### Noticing's exploration in positions with nothing to find

**The problem (rung 1e).** In the five rung-1c configurations with no mate, noticed moves are checks that are
taken. Noticing is restricted to moves untried in the exact situation, so any move tried once is not noticed
again, but the positions have many checks and each is tried once. 112-138 rooks lost to this.

**What is still open.** Noticing does not know when to stop. A meta-cognitive stopping rule (no surprise, a
settled choice, nothing new, repetition) was listed at rung 1b as not built, and is still not built.

**The fix.** A budget on noticing per episode: `Params.notice_budget` (default 6, roughly the number of
constraint kinds times two). After that many noticed moves in one episode without the want being met, noticing
is suspended for the rest of the episode, and the agent falls through to sub-wants, experiments, or idle.
The budget resets with each episode. A meta-cognitive version (the meta layer notices "my noticed moves keep
failing the same way" and emits a stopping molecule) is more principled but harder to calibrate; the budget
is the simpler mechanism and can be replaced later.

### The bridge's cost in new positions

**The problem (rung 2).** The bridge from constraints to sub-wants (`Params.bridge`) cost 4 positions mated in
rung 1e (197 to 193) and raised the second-half mean pushes per position (2.08 to 3.86). In new positions a
move's name ("Rd8") is another move in each, so its samples mix unrelated situations, and the clearing fact
found from mixed samples may be wrong.

**What is still open.** Samples should be scoped to the current position, or to positions where the same
constraints hold, not pooled across all positions a move was ever considered in.

**The fix.** Scope `met_samples` to the current configuration. `SovAgent.sample` stores
`(situation, relations)` pairs keyed by push; `SovAgent.clearing` filters them. The filter: only samples
whose situation shares the current position's set of present objects (the pieces on the board). In
`ChessWorld(sequence=True)` each position names its own pieces, so samples from different positions already
have different fact sets, but the filter must be explicit. The key is `frozenset(o for o, st in
world.states().items() if st == 'present')`, stored with each sample. `clearing` then compares only samples
whose key matches the current one. The last-60 cap on `met_samples` per push stays.

### A piece's square is not perceived

**The problem (rung 1e).** The d-rook's way to mate needs it to be on d8, and nothing in the world perceives
where a piece stands (rung 0's named choice: a state is what the rules make of a piece, not its square). The
means is consistent with everything the way is known to need, so sub_cost can't block it.

**What is still open.** A perceived relation between a piece and its file or rank ("on the d-file", "on the
back rank") would let the way's needs say where the piece must be. Listed at rung 1e, not built.

**The fix.** `ChessWorld` adds a perceived relation object per piece that is relevant to a mating pattern:
`<piece>_file` (state: `a` through `h`) and `<piece>_rank` (state: `1` through `8`), following the same
pattern as `<piece>_safety` (a separate object whose state changes with the piece). Not every piece needs
one: only pieces whose position matters to a known way (the rook that must be on the d-file for Rd8). The
world can offer them for every piece (`ChessWorld(file_rank=True)`) or the agent can request them for pieces
named in a way's needs (demand-driven perception, not built). The simpler version: the world perceives them
for every piece, and the planner's `needs` lists "rook on file d" as what the way requires. `sub_cost` can
then block a means that moves the rook off d.

### DuelWorld has no event objects

**The problem (rung 3).** In a duel, Black's answer is not perceived as an event (unlike the single-player
world's `reply`). The full arm's `converge` reads failure kinds from changes only, so its constraints are
noisier than in rung 1e.

**What is still open.** `DuelWorld` needs event objects describing what a failed push ran into (what the other
side did in response), so that convergence can distinguish "my capture was taken" from "my check was stepped
away from".

**The fix.** Follow what `ChessWorld` already does for the single-player world. `DuelWorld.act` tracks the
other side's move after each of ours; read its character as a `reply` relation exposed as an event object:
`took` (captured on the square just taken), `stepped` (the king moved out of check), `interposed` (a piece
blocked a check), `captured` (took something elsewhere), `moved` (a quiet move), `passed` (no legal move, or
skipped). Set `self.events = ("reply",)` on `DuelWorld`, and `SovAgent.facts_now` already excludes
`world.events` from the situation, so constraints bind to failure kinds like "my capture was taken back" vs
"my check was stepped away from". The `reply` object is delivered to the side whose move it answers, in the
same slice as the rest of that move's consequences (`pend[side]`).

## The world fixes that mattered as much as the mind fixes

- A piece's safety split from its presence (cause 1): the single largest effect in the ladder.
- A move's label without `+` and `#` (rung 1c): Re8 where it mates and Re8 where it checks are one action.
- A square held by a black piece reads `held`, not `open` (rung 1c): after Rd8 Nxd8 the knight on d8 is there.
- A mate ends the game (rung 1c): no moves offered, the episode set back.
- Black's reply perceived as an event (rung 2): failures have kinds, and constraints can bind to them.
- The idle limit (rung 1e): 6 slices with no move ends the episode.
- The turn schedule (rung 3): the answer must land inside the mover's watch, or no push is credited.
