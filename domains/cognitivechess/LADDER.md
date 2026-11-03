# The cognitive chess ladder

Each rung is written up after it runs, the same way as `../fiction/LADDER.md`, `../cognitivecode/LADDER.md` and
`../civilization/LADDER.md`. The design is `../chess-sov-plan.md`; the decisions are in [README.md](README.md).

## Rung 0: win the hanging piece (`chessworld.py`, `rung0.py`), 2026-10-30

**Question.** One want (material up), the world pushing back, no reply. Does Gerundelle find a winning capture, and at
what cost against plain enumeration and a random mover?

**The world** (`ChessWorld`, python-chess behind the interface Gerundelle reads; cognitivecode's `CodeWorld` and
civilization's `PotentialWorld` are the precedents):
- **Objects:** every piece by identity (`black_knight_d5`, its colour, kind and starting square), and `material`.
- **States:** what the rules make of a piece, not its square: `safe`, `attacked` (attacked and defended), `hanging`
  (attacked, undefended), `captured`; material `even`, `up`, `down`.
- **Invitations:** the legal moves, `(move, piece, 'piece')`.
- **Principle 0** (civilization PHYSICS.md): in the slice a move lands only the piece moved changes; the piece taken,
  material and the other pieces' states change a slice later (`horizon` 2).
- **Episodes:** each try starts from the puzzle's position. Inside an experiment the position is not set back, and
  Black passes, so an experiment's preparation and action are two White moves.
- **The puzzle** (`RUNG0`): White Kc1, Rd1, Bb2, pawns f2 g2 h2; Black Kg8, a knight on d5 hanging to the rook, a
  bishop on f6 attacked by the bishop on b2 but defended twice (the decoy), pawns f7 g7 h7. 23 legal moves; with no
  reply, two win material: Rxd5 and Bxf6.

**My choices (named):**
- The invitation's third part was fixed (`'piece'`), not the piece's state: the code world's finding that a state there
  makes every change of state make every move untried again. **Revised at rung 1** (below): it is now the piece's
  state, and rung 0's numbers are given both ways.
- A move's label is its SAN, so "Rd3" is one action from d1 or from d4; where the rook stands is part of the situation.
- An order seed ranks each move by a draw keyed on the seed and the move (`042 Rxd5`), so ties aren't broken by a
  move's name and a move keeps its rank in every position it is legal in.

### A change inside Gerundelle (`sov_agent.py`), under its discipline

| Step | Result |
|---|---|
| backup before the change | `backup/molecules_2026-10-30/` (all `*.py`, `SHA1SUMS` verified) |
| the change | `SovAgent.foreseen`, called where an experiment starts (`tick`) |
| suite after the change | 72/80, 2 pending: **identical to the reference** (`backup/tests_after_foreseen.log`, `backup/fails_after_foreseen.txt`) |
| civilization P0 (a still world) rerun | identical: 10 pushes, written at t34, conservation holds |

**In a still world, an experiment whose every step was already done in the situation it would meet comes out as those
did: it is reported, not done.** For a preparation and an action: the preparation was pushed before in exactly the
present facts, the situation it leaves follows from what it did then, and the action was pushed before in that
situation. Whether the action would come out as it usually does is read off the agent's own pushes (`predict`), and
`Inquiry.result` rules the preparation out as usual. For the action alone, an action already pushed in the present facts.
This is cognitivecode's rule for an experiment's known last step, for the whole experiment.

The failure first: in seed 0, 24 of 56 pushes repeated a move in exactly a position it had already been made in. Conditions
experiments on the rook's moves ("does Rg1 come out otherwise after Ra1?") replayed their preparation from the start,
and the known last step was then skipped: the push bought nothing. Two seeds took 30 and 53 tries.

### Results (10 seeded orders)

| | Tries to the want (median, range) |
|---|---|
| Gerundelle, unchanged (seeds 0-1 only) | 41.5, 30-53 |
| **Gerundelle** | **11.5, 3-41** (reached 10/10; Rxd5 in 5, Bxf6 in 5) |
| plain enumeration (each move once, in the same order) | 7, 2-21 |
| random mover (with repeats) | 11.5, 5-52 |

With the two winning moves given the largest rank: Gerundelle 2.5 (2-64), enumeration 22. With the smallest rank:
Gerundelle 1 in every seed.

**Rerun after rung 1's revision of the world** (the invitation's gerund is the piece's state, so Gerundelle's planner
has actions; `logs/rung0_state_gerund.log`): shuffled, median **6.5**, range 3-56, 193 tries over the 10 seeds (against
11.5, 3-41, 164 tries with the fixed gerund). With the winners ranked last, median 23 (2-88). A better median and a
heavier tail: three seeds take 39-56 tries, because a move made while its piece is attacked is a different action from
the same move while it is safe, and preparations that change a piece's state make more untried actions.

### Findings

1. **Gerundelle finds the capture every time, at about a random mover's cost, and somewhat above enumeration.** The plan
   expected roughly enumeration (no partial credit: a quiet move changes nothing material). Gerundelle sits between
   enumeration and the random mover's median.
2. **What it costs above enumeration is curiosity in real new situations.** After the change, 35 of the 164 pushes to
   the want (10 seeds) still repeat a move in a position it was made in, and each is an experiment's preparation
   replayed so that the action meets a situation it never met: the position is set back between tries, so the only way
   there is to make the preparation again. In chess nearly every
   move changes some piece's state (a king step leaves the bishop undefended, a rook off the d-file frees the knight), so
   the preparations that make a new situation for another move are many, and Gerundelle tests them. That is Inquiry
   doing what it is for, in a world where everything touches everything. It is what rung 1 needs (conditions), and it is
   a cost here.
3. **What it learns on the way is chess.** Splits learned before the want: a rook leaving the d-file frees the knight
   only when the knight was hanging (`Rf1` on `black_knight_d5_hanging`); `Rd4` and `h4` change the bishops only when the
   f6 bishop is safe (a nested split); a king step leaves the b2 bishop hanging only when it was merely attacked. None
   is about material: they are the board's structure, found by contrast.
4. **There is no rank that is Gerundelle's worst case.** The winners ranked first take one try, ranked last a median of
   2.5. Gerundelle's first push takes the smallest rank, and its next experiments don't go in rank order. Unlike
   cognitivecode's rung 0, a worst case can't be built by placing the answer, so the shuffled orders are the measure.

### Not yet done

- cognitivecode's rung 0 (also a still world) has not been rerun with the change.
- More seeds; one puzzle only.

## Rung 1: the defender (`chessworld.py` `RUNG1`, `rung1.py`), 2026-10-30

**Question.** Does Gerundelle learn by contrast that taking the knight wins only when it is undefended, and then bring
that condition about (remove the defender first) by setting its own sub-want? And does the first relation-form pair,
enable and prevent, change that?

**The world** (rung 0's, extended; rung 0 still reproduces):
- **Two configurations, one drawn per episode by the seed**, differing in one fact: the knight on d5 defended by the
  bishop on b7 (`black_knight_d5_attacked`) or hanging, the bishop on c8. White Kg1, Rd1, Ba6, pawns b5 f2 g2 h2; Black
  Kg8, Rb8, the bishop, Nd5, pawns b6 f7 g7 h7 (b6 blocks the b-file, which otherwise made a second fact differ).
- **The authored reply** (a rule of this world, as the wind is): Black takes on the square just taken, if it can, with
  its least valuable attacker; otherwise it passes. Consequences of White's move and of the reply land together, a
  slice after the move (principle 0), so material is read after the reply.
- **An episode is two of White's moves.** Undefended: Rxd5 wins a knight. Defended: Rxd5 loses the exchange (Bxd5); the
  combination is Bxb7 (Rxb7, an even trade), then Rxd5.
- **A piece keeps its name across configurations** (the bishop on c8 is `black_bishop_b7`): names come from the first
  configuration, a piece elsewhere matched by colour and kind.

**A revision of the world, a failure first: the invitation's gerund is the piece's state.** Gerundelle's planner
offers a push only where its configuration `<object>_<gerund>` is a fact (`Model.actions`). With the fixed `'piece'`
none ever was, the planner had no actions, and a mind that set and met the sub-want "knight hanging" (t230: Bxb7, the
knight hanging) then played f4, the next step of an experiment under way. No defended episode was won in any arm. The
same holds in cognitivecode's world (`CodeWorld.invitations`: the fixed `'slot'`): **Gerundelle's planner has had no
actions in the code world**, which bears on its rung 0 comparison (`../cognitivecode/GERUNDELLE_ARM.md`). Not changed
there.

### The change inside Gerundelle: polarity (`Params.polarity`, off by default)

The first relation forms (`../relations/RELATION_TYPES.md` 14 enable, 15 prevent) in SovAgent's own reasoning. They
existed only in the older ForceAgent (`force_world.polarity`). In `SovAgent.needs` (what a push needs to bring a want,
which sub-wants read):
- a split whose half with the condition brought the want: the condition **enables** the push, and is wanted (as before);
- a split whose half *without* the condition brought the want: the condition **prevents** the push, and what is wanted is
  the condition's object as it stood where the push brought the want. Before, this case gave nothing ("a condition that
  must not hold is no want");
- each is written once in the understanding register (`enables` / `prevents`, worked). `level()` averages only over
  `RELS`, so curiosity's calibration is untouched.

Discipline: backup as at rung 0 (`backup/molecules_2026-10-30/`). The suite after the change: 72/80, 2 pending,
**identical to the reference** (`backup/tests_after_polarity.log`).

### Results (10 seeds, 800 ticks; a seed draws the episodes and orders the moves; `logs/rung1.log`)

| Arm | Defended episodes won (the combination) | Exchanges lost | Hanging episodes won | Seeds with 15+ defended wins |
|---|---|---|---|---|
| off | 31 | 123 | 251 | 0 / 10 |
| polarity | 31 | 123 | 251 | 0 / 10 (identical to off, number for number) |
| sub-wants | 186 | 89 | 318 | 4 / 10 |
| **both** | **379** | **31** | 315 | **8 / 10** |

By the condition the mind learned for Rxd5 (which half came first decides it):

| Learned | Seeds | Sub-wants alone: defended won / lost | Both: defended won / lost | Polarity read |
|---|---|---|---|---|
| `black_knight_d5_hanging` (met the defended case first) | 0, 1, 2, 5, 7 | 54/2, 18/7, 45/1, 49/4, 7/11 | the same | enables |
| `black_knight_d5_attacked` (met the undefended case first) | 3, 4, 6, 8, 9 | 2/7, 3/12, 2/7, 3/10, 3/28 (as off) | **21/1, 16/1, 6/1, 79/1, 84/2** | prevents |

### Findings

1. **The condition is learned by contrast in every seed**, and which fact it is depends on which configuration the mind
   met second: the new fact at the contrast. Five seeds learned "taking works when the knight hangs", five "taking fails
   when the knight is attacked". Both are true; they are the two polarities of one condition.
2. **Sub-wants bring the condition about: the combination is found, not searched.** Where the mind holds "knight
   hanging" as what Rxd5 needs, it sets it as a sub-want, meets it with Bxb7 (it has seen Bxb7 make the knight hang),
   and then takes: 45-54 defended wins in three seeds against 2-5 without sub-wants, and the exchange lost 1-4 times
   against 8-19. The plan's two-move combination, "built from a condition, not searched for", happens.
3. **Without polarity, half the minds can't use what they learned.** A mind that learned the failing case ("attacked")
   holds a true condition that sets no sub-want: a condition that must not hold was no want. Those five seeds behave
   exactly as with sub-wants off.
4. **Polarity closes that gap.** Read as "the defender's attack prevents the capture", the same split sets the sub-want
   "knight hanging", and those seeds win 6-84 defended episodes and lose about one exchange each. Defended wins double
   (186 to 379) and lost exchanges fall by two thirds (89 to 31). The relation form changes what the mind does with what
   it knows, not what it learns: polarity alone is identical to off.
5. **Two seeds stayed low, and the planner's first push was the reason for one** (resolved below).
   - Seed 7 learned an over-general condition, nested: "the bishop captured", then "the knight hanging". In the
     undefended configuration the bishop on c8 is the same bishop, and taking it (Bxc8) also preceded wins, so its
     sub-want "bishop captured" was set and met 61 times, mostly where it didn't matter.
   - Seed 6 met its sub-want (Bxb7, the knight hanging) but then, in 23 of 28 cases, the planner found no way.
6. **The largest single effect in this rung was the world's revision, not a mechanism:** with no configuration a
   fact, Gerundelle's planner had no actions, and no arm won a defended episode. With the piece's state as the gerund,
   31-379.

### A second change inside Gerundelle: the planner's first push is one on offer

Seed 6 traced (finding 5): asked directly at the moment the knight hung, the planner's MCTS found Rxd5 with value 1.0,
but `plan_step` returned nothing. `Model.actions` offered every push the mind knew whose configuration held, and a
rook's configuration is its state wherever it stands: 75 rook moves seen from other squares (Ra4, Re4, Rc6) were first
pushes, against a budget of 60 rollouts. With the attention prior on two of them, MCTS chose Rc6, which was not on the
board, and `plan_step` returns only a push the world offers.

**The first push of a plan is chosen from the pushes the world offers now (perceived); deeper ones from the model.**
`Model(agent, goal, root=(state now, pushes offered))`, used by `plan_step`. In a force world the two sets nearly
coincide. The suite after the change: 72/80, 2 pending, **identical to the reference**
(`backup/tests_after_rootplan.log`). Rung 0 is unchanged, number for number (`logs/rung0_rootplan.log`): no plan
reaches the want there.

### Results after the change (10 seeds, 800 ticks; `logs/rung1_rootplan.log`)

| Arm | Defended won (before → after) | Exchanges lost | Hanging won | Seeds with 15+ defended wins |
|---|---|---|---|---|
| off | 31 → 42 | 123 → 139 | 251 → 347 | 0 / 10 |
| polarity | 31 → 42 | 123 → 139 | 251 → 347 | 0 / 10 (identical to off) |
| sub-wants | 186 → 407 | 89 → 88 | 318 → 478 | 5 / 10 |
| **both** | 379 → **700** | 31 → **17** | 315 → 483 | **10 / 10** |

Per seed, sub-wants alone and both: the five seeds that learned "knight hanging" win 59-96 defended episodes either way
(seed 7, the over-general condition, now 75: its sub-wants still aim at the bishop, but the knight is taken after); the
five that learned "knight attacked" win 2-6 with sub-wants alone and **21-101 with polarity**, losing one exchange each.

7. **With the planner choosing among real moves, the rung's answer is clean.** Every seed with both mechanisms finds
   the combination and makes it routine, losing the exchange once or twice in 800 ticks. Without polarity, half the
   seeds can't, for the reason in finding 3, and that is the whole difference between the arms.

### Not yet done

- **Gerundelle's planner in the code world, checked** (`experiments/code_planner.py`, `logs/code_planner_*.log`):
  cognitivecode's rung 0 with the fixed `'slot'` under today's Gerundelle (all three of this ladder's changes):
  median 124 tries, 46-157, 10/10, 486 s, against 125, 46-157 recorded in `../cognitivecode/logs/arms0.log`. The
  changes leave the code track's rung 0 where it was. With the slot's state as the gerund (the planner given fills to
  plan with), seeds 0-2 took 159, not reached (329), and 90, and over an hour; stopped at seed 3. In the code world the
  fixed `'slot'` stays: there a slot's state changes with nearly every fill, and every change made every fill untried
  again. A fill's configuration that is a fact *and* stable is what both worlds need; not built.
- Rung 1b (lookahead, Stockfish 15.1 at `E:/vscode/vitchess/ParallelReverseAutoDiff/bin/Debug/net6.0/Stockfish15/`),
  and the next relation forms as rungs need them.

## Rung 1b: counterfactual lookahead (`rung1b.py`; Gerundelle `Params.imagine`), 2026-10-30

**Question.** Rung 1's world and mind (polarity and sub-wants on), now able to imagine before moving. Is the defended
capture refused before it is made, is the combination found before any lived try, and what does imagining cost, and
leave behind?

**The world's side** (`ChessWorld.imagine(line)`): a line of White's pushes played from the board now by the rules,
the other side's reply to each from a named source; the facts the last push leaves and the changes it made, or None if
a push is not a move there. The world is not changed. Sources:
- `rules`: Black passes (the naive line: everything taken is kept);
- `stockfish`: Stockfish 15.1 at depth 6 (`E:/vscode/vitchess/.../Stockfish15/`), its word: **told**. It is a better
  opponent than the world's authored reply: after Bxb7 it does not recapture (Rxb7 would leave the knight hanging to
  Rd1) but saves the knight and gives up the bishop. So its word about this world is sometimes not what this world does:
  the plan's honestly wrong teller, unauthored.

### The change inside Gerundelle: imagination in the planner's model (`Params.imagine`, off by default)

`Model.step`: with `Params.imagine` and a world that can imagine, a push **whose conditions question is still open**
(funding below 1.0) is imagined from the board now along the line of pushes that led to the state (carried in it as
`line:...`); a push whose conditions are understood is read off the records as before. So depth follows what is not
understood. An imagined push that brings the want scores at the mind's credulity (believed as far as it believes what it
has not lived). **Nothing imagined is written in the register**: imagined outcomes only score plans, the firewall.
The suite after the change: 72/80, 2 pending, **identical to the reference** (`backup/tests_after_imagine.log`). With
imagination off the rung reproduces rung 1 exactly (700 defended wins, 17 lost).

### Results (10 seeds, 800 ticks; `logs/rung1b_*.log`)

| Source | Defended won | Exchanges lost (before the first defended win) | First defended win, median episode | Positions imagined per move |
|---|---|---|---|---|
| none (rung 1) | 700 | 17 (16) | 17.5 | 0 |
| rules (naive) | 819 | 8 (2) | 2 | 3.7 |
| stockfish | 603 | 41 (**0**) | **1** | 8.8 |

What the minds learned about Rxd5 (`experiments/learned1b.py`):

| Source | Seeds with a condition on Rxd5 |
|---|---|
| none | 10 / 10 |
| rules | 5 / 10 (3 the defender's attack; 2 the bishop attacked) |
| stockfish | **1 / 10** |

What survives when imagination is taken away (`experiments/withdraw1b.py`; the same mind imagines for 400 ticks, then
not for 400):

| | First half: defended won / lost (of episodes) | Second half, imagination off |
|---|---|---|
| imagined with Stockfish | **400 / 1** (404) | 327 / 9 (343) |
| never imagined | 289 / 17 (389) | **408 / 0** (412) |

### Findings

1. **With Stockfish's word, the defended capture is refused before it is made, and the combination is played at once.**
   No seed lost an exchange before its first defended win, which came in episode 1-4. The plan's "known answer" for
   1b, met, with about nine positions imagined per move: not a search of the board, only of the pushes the mind does not
   yet understand.
2. **But the mind plays it without understanding it.** Nine of ten minds that imagined with Stockfish never learned the
   defender's condition: nothing imagined funds a slot, and imagination steered them away from the lived loss the
   contrast needs. Competence came from the teller's word; the register stayed empty.
3. **Taken away, the teller's competence costs one lived lesson to become the mind's own.** Every Stockfish-trained mind
   lost the exchange exactly once after imagination was turned off, learned "the knight attacked prevents the capture"
   from that loss (polarity), and went on winning. But in the second half it did worse than a mind that had lived it
   all (327 against 408 wins), and some seeds played far fewer episodes (seed 8: 6, seed 4: 11): questions imagination
   had answered for it had to be asked now. The plan's "gap between alone and courted" measured: courted plays better
   sooner; alone ends with more of its own.
4. **The naive line works here for a reason the puzzle can't test.** Imagining "everything taken is kept", the best line
   in the defended position is Bxb7 then Rxd5, two captures, which happens to be the combination. This puzzle can't tell
   a naive opponent model from a good one; a puzzle where the naive line loses (a capture that is a trap) is needed.
5. **Seed 2 with Stockfish lost 41 exchanges, from a sub-want, not from imagination.** From episode 78 it played Rxd5
   (losing the exchange) then Bc8, 37 times, under the sub-want "white bishop on a6 hanging". The push it wanted was
   "Bxc8 with the white bishop hanging", seen to win in the undefended configuration; with a piece's state as its
   configuration, `needs` lists "my bishop hanging" as what that move needs, and the mind brought it about by giving up
   the exchange. The configuration problem again (the code world's, above): a move's configuration must be a fact, but
   not drag incidental states into what the move needs.

### Not yet done

- **Meta-cognitive stopping** (no surprise, a settled choice, nothing new, repetition): not built. Imagination here
  stops where the records understand and at the planner's own budget and horizon; the stop reasons the plan asks for
  are not measured.
- The mind's own model of the opponent as a source (its conditions applied to Black's pieces).
- A puzzle where the naive line loses (finding 4).
- A move's configuration that is a fact and doesn't drag in incidental states (finding 5; shared with the code world).

## Rung 1c: constraint convergence on a back rank (`rung1c.py`; `RUNG1C` in `chessworld.py`), 2026-10-30, in progress

**Question** (the user, after a pasted exchange: "is it able to find constraint sets that have 'JustOne' solution?").
Today's mind learns one condition and acts on it through one chain of sub-wants. Does it notice the one move where
several constraints, each learned from its own failure, converge (embodied/CONSTRAINT_DISCOVERY.md)?

**Decided by the user:** port the convergence mechanism (`Mind.support`, candidate support in superposition) from
`embodied/gerundelle` into `analogy/molecules`, opt-in; relations perceived as objects of their own.

### The port (Gerundelle `molecules.py`)

`Params.support` (None, "resolved", "candidates"; **off by default**) and `w_support`; `Mind.support`; `Mind.think`
resolves every binding first and bids after; a molecule tagged `constraint` keeps its open site when filled. Backup
`backup/molecules_2026-10-30b/`. The suite: 72/80, 2 pending, **identical to the reference**
(`backup/tests_after_support.log`); rung 0 identical, number for number. Not yet wired to anything in chess.

### The world

Eight configurations, three independent facts: a black knight on b7 (guards d8), a black bishop on b5 (guards e8, and
so can interpose on e8 against a check from d8), the h-pawn on h6 (the king's flight to h7) or h7. Relations as objects:
`d8`, `e8` (open, guarded, or held: a black piece on it), `flight` (open or none); the black king safe, checked or mated.
The authored reply to a check: take the checker (least valuable), else step the king out, else interpose; otherwise
recapture. Verified with python-chess: Rd8 mates only with d8 and e8 open and no flight; Re8 only with e8 open and no
flight. **In one configuration (knight, no bishop, no flight) only Re8 mates**; in one both do; in six neither.

Two fixes on the way, each a failure first:
- **A move's label is its SAN without `+` or `#`.** First `Re8#` where it mated and `Re8+` where it did not: two
  actions, nothing learned about either. This changes earlier rungs where a check was possible: rung 0's shuffled orders
  identical (one winners-last seed 68 → 50 tries); rung 1 (both) 700 → **600** defended wins, 17 → **68** exchanges lost,
  nearly all of it one seed (below).
- **A square a black piece stands on is `held`, not `open`.** First, after Rd8 Nxd8 nothing attacked d8, it read open,
  and three seeds met their sub-want "d8 open" by sacrificing the rook, every episode.

### Baseline (today's mind, polarity and sub-wants on, no support; 10 seeds, 800 ticks; `logs/rung1c_baseline_held.log`)

| | JustOne configuration (only Re8) | Both mate | Rooks lost |
|---|---|---|---|
| mated | 90 of 240 episodes | 145 of 246 | 108 |

Five seeds converge (1, 6, 7, 8, 9: Re8 opened 12-22 times in the JustOne configuration, every time a mate; "Re8 mates
only when e8 is open and there's no flight" learned exactly in some). Two never mate there (0, 3). Seed 5 loops.

### What blocks the baseline: a coincidental condition, made true at a cost

The same pathology three times, in three rungs:
- **Rung 1c, seed 5:** learned "Re8 mates when the f7 pawn is attacked" (true where it first mated, after Rd7), set the
  sub-want "f7 attacked" and met it with Rd7, **326 times**. Episodes here are one White move, so the Re8 it prepared
  never came: in one-move episodes a sub-want can only cost. My design error; rung 1 had two-move episodes.
- **Rung 1 after the label fix, seed 6:** learned "Rxd5 wins when my bishop on a6 is hanging", and lost the exchange 43
  times making it so (before the label fix: 70 wins, 1 lost).
- **Rung 1b, Stockfish seed 2:** "Bxc8 needs my bishop hanging", 37 exchanges lost.

A condition from one contrast is acted on at once. CONSTRAINT_DISCOVERY.md met the same thing in the grasp ("a
coincidence forbids the attempts it covers... never caught") and answered it with weight by receipts (1 - 1/2^n: a
constraint seen once weighs half what one met again and again does).

### Not yet done

- Two-move episodes for rung 1c, so a sub-want can be followed by the move it prepared.
- Guarding sub-wants against coincidental conditions (receipts), a Gerundelle change that touches every track where
  sub-wants are on (civilization P6-P14).
- `Params.support` wired into chess, against this baseline.

### Why contradiction didn't catch the coincidence, and the fixes (the user: "isn't that solved by contradiction machinery?"; "fix them")

Traced (`experiments/trace_s6.py`, `trace_s6b.py`; rung 1, both, seed 6 after the label fix):
- **The belief was never wrong where it was tested.** "Rxd5 wins when my bishop on a6 is hanging" held 52 times of 52:
  the bishop could be made to hang only in the undefended configuration (Bb7, b7 empty), where Rxd5 wins anyway. The
  test that refutes it (Rxd5 in the undefended configuration *without* the bishop hanging) was playable, but its
  sub-want always made the bishop hang first: self-confirmation, so contradiction had nothing to catch. The tag was the
  bishop's rather than the knight's because at the first contrast both were new and Gerundelle prefers the fact the
  mind's own last push made.
- **The lost exchanges were means, not tests.** In the defended configuration: want material → Rxd5 needs "bishop
  hanging" → made by Bc8, *as seen with the bishop safe* (the piece's safety was the move's configuration) → sub-want
  "bishop safe" → made by Rxd5 (after Bxd5 nothing attacks a6). Each step met its sub-want; nothing failed, so nothing
  was contradicted; the rook lost on the way was a side effect sub-wants did not count.

Fixes:
1. **World: a piece is two perceived objects** (`ChessWorld(safety=True)`, now the default): the piece (present,
   captured, absent) and its safety (`<piece>_safety`: safe, attacked, hanging; a king's safe, checked, mated). A move's
   configuration is the piece being there, a stable fact; safety is a relation, perceived. Rung 0: median **5** tries,
   3-28 (against 6.5, 3-56; enumeration 7, 2-21); winners last 3 (2-30).
2. **Gerundelle: `Params.sub_cost`** (off by default, needs sub-wants): serving a sub-want, a push whose outcome has
   moved the root want's object away from the root want is no means to it (`SovAgent.costly`, `Model.costly`). The suite:
   72/80, 2 pending, identical to the reference (`backup/tests_after_subcost.log`).
3. **The world: a mate ends the game** (no moves on offer, the episode set back). With two-move episodes, play went on
   after a mate and seven seeds learned "Re8 mates when the king is mated".

### Rung 1 on the split world (both; `logs/rung1_safety_both.log`, `rung1_safety_cost.log`)

| | Defended won | Exchanges lost | Seed 6 |
|---|---|---|---|
| before the label fix | 700 | 17 | 70 / 1 |
| after the label fix | 600 | 68 | 0 / **43** ("my bishop hanging") |
| **split world** | 535 | **15** | **83 / 0** ("the black bishop captured") |
| split world, `sub_cost` | identical, number for number | | |

Every seed learns a real condition (the knight hanging, the knight attacked, or the defender captured); "my bishop
hanging" appears in none. `sub_cost` was never exercised: with the configuration fixed there is no costly chain left.
It stays, opt-in. Seeds 1 and 8 find the combination less often (9 and 16 defended wins) while holding the right
condition: not traced.

### Rung 1c after the fixes (two-move episodes, a mate ends the game; `logs/rung1c_mateends.log`)

| Baseline | JustOne configuration mated |
|---|---|
| one-move episodes | 90 of 240 (38%) |
| two-move episodes, play on after a mate | 35 of 117 (30%) |
| **two-move episodes, a mate ends it** | **56 of 107 (52%)** |

`sub_cost` is identical to the baseline here: the want is the king mated, and a lost rook doesn't move it.

1. **The conjunctions are learned, nearly exactly.** Re8: "the bishop absent and no flight"; Rd8: "the knight absent,
   the bishop absent, no flight", a three-part AND, by the conjunction learner. Five seeds (1, 3, 4, 7, 9) open with Re8
   in nearly every JustOne episode and mate.
2. **The mind uses the pieces' presence, not the square relations.** In this puzzle "e8 open" and "the bishop absent"
   always go together, so experience can't tell them apart. The relations never vary independently of the pieces: a
   limit of the puzzle for testing relational constraints.
3. **Seed 8 found a real, wasteful mate:** Rd8, the knight takes on d8, Re8 mates (a knight on d8 doesn't guard e8). It
   learned "Re8 mates when d8 is held" and met that sub-want by giving up a rook, 35 times; in the JustOne position Re8
   mates directly. The want is only the mate, so the rook costs it nothing: a mind that should prefer mating without
   losing material has to want that.
4. **Without `Params.support`, the baseline does what the pasted answer said it couldn't, in half the seeds**: per-move
   conditions, each an AND of what its failures lacked, and the planner choosing the move whose conditions hold. Support
   is not yet wired; where it should matter is a constraint carrying to a move whose own conditions were never learned.

### Not yet done

- `Params.support` wired into chess, against this baseline, on a puzzle where the relations vary independently of the
  pieces (finding 2) and a constraint must carry to a move never tried in that position.
- The want as "mate without losing material" (finding 3).
- Seeds 1 and 8 of rung 1 (fewer combinations, the condition held).

## Rung 1d: constraints that converge on a move never tried (`rung1d.py`), 2026-10-30

**Question** (the user's pasted plan, after 1c): rung 1c's mind learned each move's own conditions from its own
failures. Does a move the mind has never tried in a position win because constraints learned from *other* moves'
failures all bind to it (JustOne, CONSTRAINT_DISCOVERY.md), with `Params.support` (ported at 1c) doing the noticing?

**The setup**, following `embodied/body/grasp.py` step for step:
- **Positions**, generated (`positions`): a black king on its back rank behind pawns (sometimes with luft), White's
  rooks and queen, Black's knights, bishops and rooks at random; kept if exactly one move mates in one and at least two
  checks fail, for at least two reasons. Every position is new, so the mating move has never been tried there; guards,
  flights and interposers come from different pieces in different places, so relations vary independently of pieces
  (1c's finding 2). Ten sequences of twenty positions (seeds 1000-1009); legal moves median 38.
- **An attempt is perceived before it is made** (`perceived`): read off the board by the rules as the move would meet
  it, the relations (it checks; where it lands is guarded; the king would have a flight; Black could interpose) and what
  is not a cause (the piece's kind, whether it captures, whether it lands on the back rank).
- **A failure is an event**, what the world's reply did (ChessWorld.answer's rule): no check, the checking piece taken,
  the king stepped out, interposed.
- **A failure's constraint** (`constraints_from`, grasp.py's): the smallest combination of its tags no attempt that did
  not fail that way carried in full; merged while they still tell apart.
- **Noticing** (`choose`): each untried move a molecule tagged with the constraints it clears, each constraint a
  standing molecule whose open site is clearing it; Gerundelle's Mind ticks once; the move made is the top bid, ties by
  a seeded order. Support off, the bids tie: a scan.
- Each attempt is one move from the position as given, so a rook given up for a mate is simply a failure: 1c's "mate
  without losing material" doesn't arise here.
- **Named:** the attempt loop is this arm's (as grasp.py's is the hand's), not SovAgent's tick; the noticing is
  Gerundelle's tournament. No Gerundelle code changed in this rung.

### Results (attempts to the mate per position; constraints carried along a sequence; `logs/rung1d*.log`)

| Mode | 1st half mean | 2nd half mean (median) | 2nd half mated at the first attempt | 2nd half worst | 2nd half over 5 attempts |
|---|---|---|---|---|---|
| support off (a scan) | 18.37 | 18.97 (17) | 2 / 100 | 49 | 88 |
| resolved support | 17.92 | 21.35 (18.5) | 0 / 100 | 50 | 98 |
| **candidate support** | 6.47 | **1.82 (1)** | **87 / 100** | 37 | 2 |
| candidate, no relational tags | 12.43 | 8.12 (5) | 9 / 100 | | |
| candidate, who guards and whether backed (`--fine`) | 6.69 | 1.79 (1) | 90 / 100 | 37 | 2 |
| **candidate, fine, each combination weighed by receipts** | **3.38** | **1.39 (1)** | 86 / 100 | **25** | **1** |

### Findings

1. **Yes: a move never tried in a position is noticed because constraints from other moves' failures converge on it.**
   With candidate support the mate is found at the first attempt in 87 of 100 new positions, against 2 by scanning. The
   pasted plan's JustOne, as the hand's grasp through the handle from the right, now in chess.
2. **The grasp's three-way result reproduces.** Support from resolved bindings (each constraint commits to one move by
   argmax) is worse than scanning (21.35 against 18.97): support scatters. Only bindings in superposition converge.
3. **The relations do the work.** Without check, guarded landing, flight and interposition in the perception, the same
   mechanism manages 9 of 100 at the first attempt: the constraints have nothing to bind to but pieces and squares.
4. **The misses were of two kinds** (`experiments/misses1d.py`):
   - **ties** (11 of 13 with candidate support): the mate cleared every constraint and so did another move;
     under-constraint, the tie-space where style would decide. Two attempts each.
   - **an over-general constraint from too coarse a perception** (2, at 36 and 37 attempts): a queen's mate next to
     the king (Qxg7#, Qxb7#) lands on a square the king guards, but the queen is backed, so the king can't take.
     "A check landing on a guarded square is taken" forbade it. Perceiving who guards (a piece, the king only) and
     whether White backs the square (`--fine`) was not enough on its own: the mind then learned "taken when only the
     king guards", every such check it had met being unbacked, the shortest description that fit, and the first backed
     one it met was the mate. **Weighing each combination by its receipts** (1 - 1/2^n for the failures of its kind
     that carried it; grasp.py's rule, there per kind) lets a constraint seen once weigh half: the worst case fell to 25
     attempts, one position of 100 over 5, and learning in the first half halved (3.38 against 6.69). The price: a few
     more ties (86 against 90 at the first attempt).
5. **Some constraints are proxies.** "No check" was learned in one sequence as "lands elsewhere" (not on the back
   rank), true of this family of positions, where most mates land on the back rank. Positions whose mates land
   elsewhere (most of them queen captures) are where it would cost.

### Not yet done

- The tie-space: a temperament or style that breaks ties among equally supported moves (CONSTRAINT_DISCOVERY.md,
  "Under-constraint: style").
- Positions beyond mate-in-one on the back rank, where the proxies (finding 5) would be tested.
- This loop inside SovAgent's own choice (rung 1c's mind and this one are two arms; the noticing is the same Mind).

## Rung 1e: convergence in the agent's own choice (`rung1e.py`; Gerundelle `Params.converge`), 2026-10-30

**Question.** Rung 1d's noticing lived in a loop of its own (as the hand's in grasp.py). Put it in SovAgent's choice: a
mind that learns per-move conditions (rungs 1-1c) *and* notices the move its constraints converge on (1d). Does it keep
1d's result, and does it do no harm where per-move learning already worked?

### The change inside Gerundelle (`Params.converge`, off by default; backup `backup/molecules_2026-10-30c/`)

- **Trials:** before a push made for the root want, the world says what it would meet (`world.relations_of`); after it,
  what came of it: the want, or a failure's kind, read from the world's event objects as they are after the push
  (`world.events`, here Black's `reply`). Not while a sub-want is served: those pushes are means.
- **Constraints** (`constraints_from`, grasp.py's, now in `sov_agent.py`), each combination weighing by its receipts.
- **Order in `planned()`:** the planner; then sub-wants; then, for the root want only, **noticing** (`notice`): the
  untried push supported most in a tournament with candidate support, ties by the push's order; nothing if the
  constraints don't tell the pushes apart.
- **Contradiction:** a direct way the planner finds (the push itself expected to bring the want) that runs into a
  learned constraint is not taken (`runs_into`). A means (the first step of a longer way) is not judged by constraints
  on direct ways.
- **Speed, behaviour unchanged:** `Model.states_of` keeps what it has read of the perception log instead of rescanning it
  on every planner step (a third of the run's time).
- The suite after all of it: 72/80, 2 pending, **identical to the reference** (`backup/tests_after_converge_final.log`).

**The world** (`ChessWorld`): `sequence` (rung 1d's positions in order, the next after a mate, each naming its own
pieces); a relation `reply` (Black's last answer: passed, took, stepped, interposed); a relation `game` (on, mate), so
the want is one fact whatever the king is called; `relations_of(inv)` (1d's perception).

Each a failure first:
- the planner came first, and in new positions a move's name that had mated elsewhere ("Ra8") was a way known: 297 of
  486 pushes, nearly all failing. Hence contradiction.
- failure kinds were read from what the event objects *changed to*: the same reply twice running is no change, and
  thirty kinds were filed where there were four. Now what they *are*.
- `notice` first demanded a push clearing every constraint (one over-general constraint left nothing to notice among
  50 moves), then one supported above every other (ties left 287 of 296 pushes to experiments). Now grasp's rule.
- noticing first came before sub-wants, and in rung 1 the sub-want that sets up the combination was pre-empted, and the
  trade that removes the defender was vetoed as a failed direct way. Now sub-wants first, and only direct ways judged.
- rung 1's world did not perceive Black's reply, so its failure kinds were whatever else changed, and its constraints
  were noise ("no change ← a pawn moved"). With `reply` perceived (`rung1.py --reply`), clean.

### Results

**Rung 1e** (rung 1d's positions, 10 seeds × 20, 3000 ticks; `logs/rung1e_*.log`):

| Arm | Positions mated | 2nd half pushes per position (mean) | 2nd half mated at the first push |
|---|---|---|---|
| converge off | 55 / 200 (no seed past its tenth position in 3000 ticks; one position took 378 pushes) | | |
| converge on, noticing before sub-wants | 200 / 200 | 1.42 | 90 / 100 (86 s for all ten seeds) |
| **converge on, sub-wants first (kept)** | 196 / 200 | 1.99 | 82 / 96 |

**Rung 1** (the defender), Black's reply perceived in both arms (`logs/rung1_reply_*.log`):

| Arm | Defended won | Exchanges lost | Hanging won |
|---|---|---|---|
| polarity and sub-wants | 443 | 22 | 370 |
| **and converge** | **678** | **11** | **622** |

**Rung 1c** (the back rank), converge on (`logs/rung1c_converge.log`): JustOne configuration mated 112 of 204 episodes
(55%; without: 56 of 107, 52%), both-mate configuration 103 of 208 (50%; without: 77 of 110, 70%), in twice the episodes
for the same ticks.

### Findings

1. **One mind does both.** With convergence in its own choice, Gerundelle's agent mates new positions at the first push
   (82-90 of 100) where per-move learning alone mates a few positions in thousands of ticks, and in rung 1 it finds the
   defender's combination more often and loses the exchange half as often (678 / 11 against 443 / 22).
2. **The two kinds of knowledge have to be ordered, and contradiction is how they meet.** The planner's per-move ways
   come first, sub-wants next, noticing last; where a direct way meets a constraint learned from other pushes' failures,
   the way is contradicted. Noticing first was faster in new positions (1.42 against 1.99) but pre-empted the
   sub-wants combinations need; kept: sub-wants first.
3. **Convergence needs the world's events perceived.** Without Black's reply as an object, a failure's kind was whatever
   happened to change, and convergence hurt rung 1 (381 against 535). It is only as good as what the mind can see of
   what went wrong.
4. **Rung 1c was mixed, and the cause was perception again** (traced, `experiments/trace1c_both.py`, `cons1c.py`).
   Rung 1c's world did not perceive Black's reply: 161 trials of one seed were filed as "no change", the constraints
   barely told moves apart, and in the both-mate configuration dozens of moves tied at the top, the tie broken by
   order: 88 episodes opened with a noticed move that was not a mate. With the reply perceived (`rung1c.py --reply`),
   both arms in the same world:

   | Rung 1c, reply perceived | JustOne mated | Both-mate mated | Rooks lost |
   |---|---|---|---|
   | baseline | 29 / 108 (27%) | 68 / 134 (51%) | 74 |
   | **converge** | **103 / 160 (64%)** | **113 / 167 (68%)** | 427 |

   Noticed non-mating openings in the both-mate configuration fell from 88 to 10; the planner opens with a mate 104
   times. Perceiving the reply also made the baseline worse (52% and 70% without it): one more fact for per-move
   learning to confuse with a condition. **The rooks:** 268 lost to sub-wants' means and 94 to noticed moves, nearly all
   in the six configurations with no mate: the "Rd8 sacrifice, then Re8" line (seed 8 at 1c), tried where it can't
   work. The want is the mate alone, so a rook costs nothing; `sub_cost` can't weigh it (material is not the want's
   object). The cost belongs in the want: 1c's "mate without losing material".

### Not yet done

- The want as "mate without losing material" (finding 4's rooks; 1c finding 3).
- The tie-space (style), positions beyond mate in one, meta-cognitive stopping for lookahead (carried over).

### The want as "mate without losing material" (the user: "yes"), 2026-10-30

**The choice (named):** the world perceives the outcome whole. With `ChessWorld(clean=True)` the relation `game` reads
`mate` only for a mate with material not down, and `costly_mate` for one bought with material; the want stays one fact
(`game_mate`), so Gerundelle is unchanged and the mind learns for itself that the sacrifice line doesn't bring it. The
alternative, a want of a goal plus facts to keep, would change how wants are read throughout the agent, planner and
sub-wants. `rung1c.py --clean`.

**Results** (rung 1c, Black's reply perceived, 10 seeds, 800 ticks; `logs/rung1c_{plain,clean}_{baseline,converge}.log`):

| | JustOne mated | of which no material lost | Both-mate mated | Rooks lost |
|---|---|---|---|---|
| baseline, the mate | 29 / 107 | 29 | 68 / 134 | 81 |
| baseline, the clean mate | 29 / 88 | 29 | 60 / 105 | 81 |
| converge, the mate | 103 / 160 | 86 | 114 / 168 | 428 |
| **converge, the clean mate** | **112 / 193** | **102** | **121 / 187** | 401 |

1. **The clean want gives more clean mates where there were costly ones** (converge: 86 → 102 in the JustOne
   configuration); the baseline never bought a mate, so it is unchanged.
2. **It barely moves the rooks lost** (428 → 401): most are not the sacrifice line. Not traced; exploration in the five
   configurations with no mate is the likely place, unverified.
3. **A two-move mate where there is no mate in one.** In configuration 4 (the bishop, no knight, no flight) converge
   mates 54-58 times: Rd8+ forces the bishop to interpose on e8, and Rxe8 is mate, winning the bishop on the way. Not
   designed into the puzzle.

### Where the rooks went (traced, `experiments/rooks1c.py`; the user: "trace it")

Converge, the clean want, 10 seeds: 390 of 401 rooks lost were in configurations with no mate.
- **235 were means the planner chose for a sub-want, 201 of them for "e8 held".** The two-move mate the mind found
  (Rd8+, the bishop interposes on e8, Rxe8 mate) made "Rxe8 mates" need a black piece on e8; the move most often seen to
  put one there was Re8 itself, taken by the bishop: the sub-want met, the rook that was to mate gone.
- **138 were noticed moves:** checks that are taken, in positions with nothing to find, noticing being restricted to
  moves untried in the situation.

**A change inside Gerundelle, `sub_cost` extended** (still off by default): while a sub-want is served, a push whose
outcome changed something the way it serves needs and has now (the way's `needs`, e.g. its rook present) is no means to
it (`SovAgent.undoes`; `Model.costly` reads what the way needs from `SovAgent.serving`). The suite: 72/80, 2 pending,
identical to the reference (`backup/tests_after_undoes.log`).

| Converge, the clean want | Clean mates, JustOne | Both-mate mated | Rooks lost |
|---|---|---|---|
| without sub_cost | 102 | 121 | 401 |
| with sub_cost extended | 90 | 109 | **280** |

What is left (`logs/rooks1c_cost.log`):
- **106 still for "e8 held"**, and not a failure of the rule: the way is the mate by the *d*-rook (Rdxe8 after Rd8), which
  needs the d-rook present and e8 held, and the e-rook's sacrifice undoes neither. What the mind can't perceive is that
  the d-rook must be *on d8*: a piece's square is not a fact in this world (rung 0's choice, so that a state is what the
  rules make of a piece, not where it stands). The means is consistent with everything the way is known to need.
- **112 noticed** checks in positions with no mate: exploration.
- **19 for the sub-want "material down"**, traced (`experiments/matdown1c*.py`): a sub-want of a sub-want. To get "e8
  held" (itself a sub-want, for Rxe8), the mind read its records of Rd8 (Rd8+ makes the bishop interpose on e8), and
  Rd8 had a split: it brought "e8 held" where material was down. Those records were the situations just after its own
  sacrifice of the e-rook on e8 (Re8 Bxe8: e8 held, material down). So "material down" was set as a want, and met by
  sacrificing a rook. Self-confirmation inside the recursion: the condition was the mind's own earlier move, and nothing
  failed, so nothing was contradicted (Gerundelle's "a condition one makes oneself is a sign, not the cause" fires only
  when the push then fails). (A first reading of this trace computed "brought the want" against the root want and was
  wrong: the records hold no mate.)
- **About a tenth fewer mates**, traced (`experiments/trace1c_both.py`, the first move of each episode in the two
  mating configurations): the planner's direct Re8 mate fell from 92 + 81 to 76 + 73 episodes, and the planner serving
  a sub-want with a non-mating move rose from 27 + 14 to 56 + 37. With its costly means blocked, a sub-want is not met
  at once (by the sacrifice) and lingers, up to its budget of 80 ticks, and is served at the start of the next episodes
  even where the mate is on the board. A sub-want is set because the planner finds no way to the want (P6); when a way
  to the want it serves appears, nothing makes it yield.

### Not yet done (rung 1e, updated)

- A move's relation to where its piece stands (a perceived "on the file", "on the rank") so a way's needs can say it.
- A sub-want that yields when the want it serves has a way again (the lost mates).
- A condition the mind made itself, held as a want (the sub-want "material down").
- Noticing's exploration in positions with nothing to find.

### Sub-wants that yield, and conditions never seen absent (the user: "yes"), 2026-10-31

**Two changes inside Gerundelle** (backup `backup/molecules_2026-10-31/`), off by default:
- **`Params.sub_yield`:** while sub-wants are stacked, the planner is asked about the root want; if it finds a way (not
  contradicted), the stack is dropped (`yielded`) and the way taken. A sub-want is set because the planner finds no way
  to the want (P6); when one appears, its reason is gone. And a sub-want whose fact already holds is had.
- **`Params.sub_tested`:** what a way needs (`needs`) counts a split's condition only where the split's other half
  holds records: a condition never seen absent is not known to matter. The trace behind it (`experiments/
  matdown1c_why.py`): the sub-want "material down" came from a nested split on Rd8 whose other half was empty; every
  record of Rd8 with e8 held also had material down, the bishop having reached e8 only by taking a rook the mind gave
  up. ("A condition one makes oneself" was the first idea and is wrong as a rule: civilization's jar is charged only by
  the mind's own dip, and is the cause.)

**A change to the world, a failure first: an episode also ends after six slices with no move of White's** (`IDLE`).
With `sub_yield` alone rung 1 fell from 678 to 536 defended wins, all of it in three seeds that *stopped moving*
(seed 4: 120 pushes in 800 ticks against 397): after taking the hanging knight on its first move the mind had nothing
worth doing, and the world waited for White's second move however long (`experiments/yield1*.py`). Gerundelle's force
worlds end episodes by time; this one now does too.

The suite after all of it: 72/80, 2 pending, identical to the reference.

### Final comparison, the corrected world (`logs/final_*.log`)

"Full": polarity, sub-wants, converge, sub_cost (extended), sub_yield, sub_tested.

| | Baseline (polarity, sub-wants) | Converge | **Full** |
|---|---|---|---|
| Rung 1, reply perceived: defended won / exchanges lost / hanging won | 476 / 20 / 395 | 693 / 16 / 636 | **700 / 14 / 806** |
| Rung 1c, clean want: JustOne mated (clean) | 56 / 111 (56) | 117 / 200 (107) | **173 / 187 (168)** |
| Rung 1c: both-mate mated | 83 / 128 | 128 / 193 | **174 / 187** |
| Rung 1c: rooks lost | 134 | 432 | 267 |
| Rung 1e: positions mated; 2nd half at the first push | 55 / 200 (earlier world) | 196 / 200; 82 / 96 | **200 / 200; 87 / 100** |

Findings:
1. **With every principle on, one mind does best in all three rungs**: the defender's combination (rung 1), the back
   rank where several constraints decide (1c, 93% of the mating episodes mated, nearly all without losing material),
   and new positions where only constraints from other moves can help (1e).
2. **Each principle was found as a failure first, by tracing, and each is Gerundelle's own:** a direct way contradicted
   by what other pushes' failures revealed; sub-wants before noticing, noticing for the root want; a means that undoes
   what its way needs is no means; a sub-want yields when the want it serves has a way, and is had when it holds; a
   condition never seen absent is not wanted.
3. **The world had to be fixed as often as the mind:** a move's label carried its outcome (`+`, `#`); a square held by
   a black piece read open; a piece's safety was its configuration; play went on after a mate; Black's reply was not
   perceived; an episode could wait forever for a move. Each made the mind look worse, or better, than it was.
4. **Rooks are still lost in rung 1c (267)**, mostly in the five configurations with no mate: exploration, and the
   d-rook's square not being perceived (above).

## Rung 2: told knowledge, Stockfish as a coach (`rung2.py`), 2026-10-31

**Question** (chess-sov-plan.md, "Feedback"): the mind is told what to play by a coach whose word counts at half
weight. Does being told help, what does it cost, and what is left when the coach goes?

**The setup.** The mind is rung 1e's "full" one. When it holds its want, has no way to it, and is neither serving a
sub-want nor running an experiment, it asks the coach, once per situation; the answer, the coach's best move, enters
Gerundelle's register as a told way (`causes`, told, the teller named), believed by the planner as far as the mind's
credulity goes, refuted by Gerundelle's own rule when the world contradicts it. Its own records of a move come first.
Coaches: none; Stockfish 15.1 at depth 8; at depth 1; an ignorant coach (a legal move at random), the plan's control
that a gain is the coach's knowledge and not being told something. A named choice: the asking lives in this arm, not in
fiction's `consult` (which asks only about pushes on the wanted object; here `material` and `game` are never pushed).

**A fix to fiction's shared arm, a failure first:** a refuted told way makes Gerundelle feel anger at the teller whose
word failed; that phase has no goal, and `read_phase_log` called `.split` on None. Now it falls back to the instance
(`gerundelle_arm.py`, backed up as `backup/gerundelle_arm_2026-10-31.py`); nothing changes where a goal is set.

**A change inside Gerundelle, a failure first: an event is not a condition.** A world may name event objects
(`world.events`: what just happened, an outcome); `SovAgent.facts_now` leaves them out of the situation, and a failure's
kind is read from them directly. Only the chess world names one (Black's `reply`), so other worlds read as before.
First the reply was a standing state, part of every later situation, and a coached mind learned "Rxd5 wins when Black's
last answer was a pass" and stood still for 300 ticks; the uncoached baseline had leaned on the same confound. The
suite: `backup/tests_after_events.log`.

A fix tried and reverted: letting a refuted word block only later telling, not the mind's own receipts. It changed
nothing: the planner reads its records of what pushes did (`meta.modes`), not the `causes` relation refutation blocks.

### Results (rung 1, Black's reply perceived as an event, 10 seeds, 800 ticks; `logs/ev_*.log`)

| Coach | Defended wins | Wants met, 1st half / 2nd half | Told | Refuted |
|---|---|---|---|---|
| none | 773 | 767 / 800 | 0 | 0 |
| Stockfish, depth 8 | 671 | 727 / 659 | 42 | 31 |
| Stockfish, depth 1 | 621 | 683 / 648 | 47 | 35 |
| ignorant | **802** | 791 / 821 | 43 | 19 |

Withdrawing the coach halfway changed nothing: the mind asks only early, when it has no way at all.

The comparison of rungs 1, 1c and 1e under the event change:

| | Baseline | Converge | Full |
|---|---|---|---|
| Rung 1: defended / exchanges lost / hanging | 286 / 28 / 356 | 669 / 11 / 587 | **773 / 10 / 794** |
| Rung 1c (clean want): JustOne mated; both-mate mated; rooks lost | 61/101; 67/111; 170 | 110/179; 134/174; 432 | **171/196; 190/197; 225** |
| Rung 1e: positions mated; first-push mates | | 197/200; 84/97 | **197/200; 85/97** |

### Findings

1. **Stockfish's word makes this mind worse, and a worse Stockfish worse still**; a random word is harmless (a little
   better). The plan expected the coach to save search; here it costs.
2. **Why, in the seed traced (seed 2: alone 73 defended wins, coached 6):** the coach told Rxd5 where it wins; the mind
   later lost with it in the defended configuration, a loss that changed several facts at once, so no split formed and
   the mind never learned Rxd5's condition. Noticing's constraints did learn that Rxd5 there is taken ("a capture
   landing on a guarded square"), and veto it, rightly, which blocks the one test that would teach the condition. Sub-
   wants need a fact about a piece to want ("the knight hanging"); constraints are relations of moves ("lands on a
   guarded square"); nothing turns one into the other. The mind knows *that* the capture fails and not *what to change*,
   and goes quiet. The coach makes it likely by deciding which experiences come first.
3. **Removing the event from the situation helped the full mind** (rung 1: 700 → 773 defended wins; 1c: rooks lost 267
   → 225) and hurt the plain baseline (476 → 286), which had leaned on the confound.

### Not yet done

- A bridge between constraints (relations of moves) and sub-wants (facts about pieces): from "Rxd5 is taken because
  d5 is guarded" to "make d5 unguarded".
- A world where being told pays: a coach whose word saves search the mind can't do (the plan: rung 2's book opening).

### The bridge from constraints to sub-wants (the user: "OK, continue"), 2026-10-31

**The change inside Gerundelle (`Params.bridge`, off by default, needs converge and sub-wants; backup
`backup/molecules_2026-10-31b/`).** Each time the mind considers a push (noticing, or a direct way checked against the
constraints) it keeps what the world said the push would meet there, with the situation (`SovAgent.sample`). When a
direct way is contradicted by a constraint, the mind compares its samples of that push: a fact present in every
situation where the push would have cleared the constraints it meets and absent from every one where it ran into them
(this one too) is what would clear them (`SovAgent.clearing`), and, if some known push makes it, it is set as a
sub-want (`bridged` in the sub-want log). From "Rxd5 lands on a guarded square" to "want the knight hanging", by the
mind's own contrast.

The traced seed (rung 2, seed 2, Stockfish at depth 8): 1 defended win without the bridge, **82** with it.

### Results (10 seeds; `logs/br_*.log`)

| Rung 2 (rung 1's defender), defended wins | Full | **Full + bridge** |
|---|---|---|
| alone | 773 | 770 |
| Stockfish, depth 8 | 671 | **790** |
| Stockfish, depth 1 | 621 | **778** |
| ignorant | 802 | 802 |

| | Full | Full + bridge |
|---|---|---|
| Rung 1: defended / exchanges lost / hanging | 773 / 10 / 794 | 770 / **7** / 800 |
| Rung 1c (clean want): JustOne mated; both-mate mated; rooks lost | 171/196; 190/197; 225 | 161/186; 180/188; 227 |
| Rung 1e: positions mated; 2nd half mean; first-push mates | 197/200; 2.08; 85/97 | 193/200; 3.86; 77/93 |

1. **With the bridge, Stockfish's word helps a little instead of hurting** (790 against 770 alone; 671 without the
   bridge). What the coach's word left behind, a push known to fail and no condition to want, is now something to do.
2. **Neutral in rungs 1 and 1c** (fewer exchanges lost in rung 1).
3. **A cost in rung 1e:** 193 against 197 positions mated, and fewer first-push mates. Not traced; the likely place is
   that in new positions a move's name ("Rd8") is another move in each, so its samples mix unrelated situations.

### Not yet done

- The bridge's cost in rung 1e.
- A world where being told pays: a mate in two whose first move is quiet. Gerundelle's told knowledge is one push as a
  direct way to the want, so a coach's right quiet move would be refuted at once; it needs the coach to tell a line one
  move at a time with the first as a means, or Gerundelle to take a told sequence.

## Rung 2b: a world where being told pays (`rung2b.py`; Gerundelle `Params.told_effects`), 2026-10-31

**Question** (the plan's "book"): told knowledge the mind could not find by itself in the time it has. Does a book that
knows the line make the difference, and does the gain come from its knowledge?

**The world.** Each position is new and a mate in two whose first move is quiet: no move mates at once; one to five quiet
first moves (no check, no capture; Black then passes, by this world's answer) let a move mate next; 30-46 legal moves.
Built from rung 1d's mates in one by a White bishop put on the mating line (positions drawn at random: none in 400,000
tries). Episodes of three White moves (the line's two and room for one: with two, the mind's first move went to an
experiment under way, the book's quiet move came second, and the mate never came). The mind: the full one with the
bridge.

**The book** knows the line (a full search under this world's own rules). Asked once per position, at an episode's start,
when the mind has no way, it tells Gerundelle's told receipts: the quiet move causes the facts it changes; the mating
move, as it will stand after the quiet one, causes the mate, **after** the quiet move. A wrong book tells a quiet move
and a move at random the same way (the control).

**The change inside Gerundelle (`Params.told_effects`, off by default; backup `backup/molecules_2026-10-31c/`), each
part a failure first:**
- **Told effects:** the planner's model reads a push never tried in the reading at hand by what it was told to cause (not
  only the want), so told steps chain into a line; a told effect the world does not bring is refuted, as a told way is.
- **Told after:** a told way may be told to work after another push (relation `after`): read only along a line where
  that push was just made, refuted only if it fails right after it. First unconditional: tried before its quiet move the
  mate failed and the true line was refuted for good (seeds 1, 2, 6 stuck in their first position).
- **A push just made** stays marked while the world stands as it left it, so the planner continues a told line from the
  real position (first the root of every plan was the bare situation, and "after the quiet move" never held there).
- **Nothing known, still made:** a push with no known outcome still marks the state it leads to as made by it, so a line
  can be read on from a quiet move that changes nothing the mind perceives (seed 3: the quiet move's told effects were
  empty).

The suite after all of it: `backup/tests_after_after.log`.

### Results (10 seeds × 12 positions, 2400 ticks; `logs/r2b*.log`)

| | Positions mated | Told | Refuted |
|---|---|---|---|
| alone | 37 / 120 | 0 | 0 |
| a wrong book | 65 / 120 | 69 | 30 |
| the book, read without told effects (only a told way to the want) | 68 / 120 | 71 | 5 |
| **the book, with told effects** | **112 / 120** | 114 | 11 |

### Findings

1. **Being told pays where the mind can't search far enough alone:** 112 of 120 positions against 37 alone. Rung 2's
   result (a coach costs) is not the last word on telling: it depends on whether the word saves search the mind can't
   do.
2. **The gain is the book's knowledge**, not being told something: a wrong book reaches 65 (prompting helps, as at rung
   2), the right one 112.
3. **The extension to Gerundelle is what turns the book's words into a line:** the same book, read only as told ways to
   the want, reaches 68. A line has to be told as steps whose effects and order the planner can read.
4. **Lived evidence still comes first.** A quiet move the mind has tried and seen do nothing is read off its own record,
   and the book's word for it no longer counts: that is why episodes need room for the whole line.

## Rung 3: two minds on one board (`rung3.py`; `DuelWorld` in `chessworld.py`), 2026-10-31

**Question** (the plan's "two minds, contested territory"): with Black a Gerundelle mind instead of the authored reply,
what does White learn, and what does each side feel?

**The world.** Rung 1's defender family (knight on d5 defended by the bishop on b7, or hanging; one drawn per episode).
`DuelWorld`, a subclass so earlier rungs are unchanged:
- only the side to move is offered moves;
- what a move does reaches its maker in the maker's next slice, and in the move's own slice only the moved piece
  changes (principle 0);
- each side wants its **standing** up (`standing_white_up`, `standing_black_up`): the material balance from its own
  view, read when its turn comes round again, so a capture is judged after the reply;
- an episode is four half-moves, a mate, or six idle slices; a watch spans three slices.

**Opponents for the same White mind:** Black a mind, with the same arm as White, or Black scripted (rung 1's rule:
take back on the square just taken, else pass). **Arms:** `base` (polarity, sub-wants, sub_yield, sub_tested) and
`full` (adds converge, sub_cost, bridge).

**A change inside Gerundelle (backup `backup/molecules_2026-10-31d/`; suite `backup/tests_after_poisson.log`: 72/80, 2
pending, the fail list identical to `fails_after_after.txt`).** The first runs with a thinking Black crashed in
`Territory.relation_of` (`OverflowError`). `GerundelleMind.look` reports every move of the other mind as something else
moving a region, so in a duel those counts grow without limit, and the Poisson tail `lam ** j / j!` overflowed.
`relation_of` now checks `n >= 5 and _outside <= 0.1` before it computes the tail, and the tail is computed in log space
(`poisson_cdf`). It matches the old sum to 3e-15 wherever that didn't overflow.

**A change in the world's schedule (`--schedule`, a named choice).** The first schedule was civilization P4's: each
round every mind steps once (`rounds`). Against a thinking Black, the standing count fell to half while the boards showed
White up as often as against the rule. The cause (`experiments/delivery3.py`, seeds 0–1):

| White's standing outcome | Black scripted | Black a mind |
|---|---|---|
| inside the watch of White's own move (credited) | 269 / 269 | 59 / 151 |
| after the watch ended | 0 | 52 |
| dropped (White moved in the slice that would have shown it) | 0 | 41 |
| Black's answer after (White's slices) | 0 always | 0: 36, 1: 116, 2: 165 |

A thinking Black takes one or two of White's slices to answer (watching its own push, choosing), so two thirds of White's
outcomes credited no push. The scripted Black answers at once, which is why it never showed. Under **`turns`**, the side
to move steps until it moves (at most 5 slices, under the world's idle limit of 6), then the other side takes one slice
to see the answer: every outcome lands inside the mover's watch (162 / 162, answer delay 0). Both schedules spend
2 × 800 mind-steps per seed. A thinking Black spends steps thinking, so fewer episodes fit.

### Results (10 seeds, 1600 mind-steps each; `logs/rung3_*.log`; every episode's end read just before the board is set back)

| | Black scripted | Black a mind, base | Black a mind, full |
|---|---|---|---|
| **turns:** episodes | 1574 | 856 | 897 |
| **turns:** White's wants met (per episode) | 1370 (0.87) | 587 (0.69) | 658 (0.73) |
| **turns:** episodes ending White up, defended | 626 / 778 (80%) | 322 / 417 (77%) | 358 / 440 (81%) |
| **turns:** episodes ending White up, hanging | 521 / 796 (65%) | 341 / 439 (78%) | 369 / 457 (81%) |
| **turns:** Black's wants met | – | 89 | 35 |
| rounds: White's wants met (per episode) | 994 (0.82) | 512 (0.43) | 352 (0.26) |
| rounds: episodes ending White up, defended / hanging | 79% / 70% | 77% / 68% | 81% / 81% |

What the sides did (`experiments/trace3.py`, 10 seeds, **under `rounds`**; `logs/trace3_*.log`):

| | Black scripted | Black a mind, base | Black a mind, full |
|---|---|---|---|
| Black's answer to a White capture: takes back | 624 | 34 | 89 |
| knight flees d5 | – | 270 | 201 |
| other quiet moves | – | 393 | 489 |
| White's first move, defended | Bxb7 515 / 621 | Bxb7 494 / 603 | Bxb7 533, Rxd5 67 |
| White's first move, hanging | Rxd5 448, Bxc8 67 | Bxc8 289, Rxd5 141 | Bxc8 409, Rxd5 159 |

### Findings

1. **What a mind is credited with depends on when the other side's answer comes.** Under one step per mind per round,
   a thinking opponent's answer fell outside the mover's watch two times in three, and White's wins credited no push.
   The fault was in the world's schedule, not the minds: every world where two minds take turns needs the answer
   inside the mover's watch. `turns` does that; `rounds` stays for comparison.
2. **On the board, White does as well against a thinking Black as against the rule:** 77–81% of episodes end with White
   up in both configurations, against 80% and 65% against the rule. Its counted wants per episode come close once
   outcomes are delivered (0.69–0.73 against 0.87).
3. **The thinking Black rarely takes back** (34 and 89 times, against the rule's 624). After a capture it moves its
   knight away or plays something else. White adapts to the opponent it has, not the combination: in the hanging
   configuration it mostly opens `Bxc8`, which is an even trade against the rule and wins a bishop against a Black that
   doesn't take back. In the full arm it sometimes plays the direct `Rxd5` in the defended configuration, which loses
   the exchange against the rule and is roughly a coin flip against this Black.
4. **Why Black doesn't defend: likely its want (a hypothesis, not yet tested).** `standing_black_up` is met only by
   winning material, and taking back after a capture only restores even, so nothing pays a defence. Black meets its
   want only on White's mistakes (89 times in the base arm, 35 in the full, where White makes fewer). The design sketch
   had Black wanting "material not down"; one fact can't say "even or up", and it became the symmetric `up`.
5. **Both minds form feelings** (turns, base): White joy 196, frustration 99, anxiety 51, sadness 13, anger 5; Black joy
   178, frustration 105, anxiety 35, sadness 8, anger 4. Anger stays rare, since a capture taken in view is conceded
   (`grievance` is off).
6. **A stuck seed is a sub-want loop.** Seed 0 against the rule under `turns` (0 of 88 defended episodes up) set the
   sub-want `material_even`, met it at once because it already held, and set it again every three ticks, while playing
   `Rxd5`. Rounds seed 6 against the rule also met no want; it was not traced.

### Not yet done

- Black wanting "not down" (a defender's want), and whether a defending Black brings back the combination.
- The move trace (finding 3) under `turns`.
- The sub-want loop of finding 6: a sub-want that holds when set is met at once and set again.
- What `relation_of` makes of the other mind now that it runs: whether either side reads the other as answering.
- `DuelWorld` has no event objects describing what a failed push ran into, so the full arm's `converge` reads failure
  kinds from changes only.

### Black as a defender (`--black-want kept`; `DuelWorld(holding=True)`), 2026-10-31

**Question** (finding 4's hypothesis): does Black take back when its want is to win back what was taken, and does White
then go back to the combination?

**The world** (opt-in, off by default; earlier runs reproduce exactly): each side also perceives `holding_<side>`, which
is `kept` while its standing is even or up and `lost` while it is down, read and delivered with the standing. Black wants
`holding_black_kept`; a Gerundelle want is a change, so it is met when Black's holding goes from `lost` back to `kept`.
That is what a defender wants. White's want is unchanged. Backups before the change: `backup/chessworld_before_holding.py`,
`backup/rung3_before_holding.py`. The schedule is now one function (`rung3.play`) that the trace scripts share.

#### Results (10 seeds, `turns`; `logs/rung3_*_turns_kept.log`, `logs/trace3_*_turns*.log`)

| | Black wants **up** (gain) | Black wants **kept** (defender) |
|---|---|---|
| Black takes back after a White capture, base / full | 79 / 79 | **249 / 281** |
| Black's answer to a capture, defended, base: takes back / flees / quiet / other capture | 58 / 111 / 270 / 37 | 190 / 42 / 248 / 51 |
| Black's wants met, base / full | 89 / 35 | 155 / 234 |
| episodes ending White up, defended, base / full | 77% / 81% | 71% / 64% |
| episodes ending White up, hanging, base / full | 78% / 81% | 70% / 66% |
| White's first move, hanging, base | Rxd5 239, Bxc8 130 | **Rxd5 282**, Bxc8 75 |
| White's first move, hanging, full | **Bxc8 323**, Rxd5 70 | **Rxd5 288**, Bxc8 110 |
| White's first move, defended, base / full | Bxb7 302, Rxd5 96 / Bxb7 383, Rxd5 24 | Bxb7 316, Rxd5 100 / Bxb7 280, Rxd5 105 |

The move trace with Black wanting `up` is now also under `turns` (above, first column; it replaces the `rounds` trace
for that question). It agrees with the `rounds` trace: a Black wanting gain rarely takes back.

#### Findings

7. **The want makes the defender.** With the same mind and only its want changed, Black takes back three to three and
   a half times as often (249 and 281 against 79), and its wants met rise (155 and 234). Finding 4's hypothesis holds.
8. **White adapts back.** In the hanging configuration, where `Bxc8` only pays against a Black that doesn't take back,
   White's first move returns to `Rxd5` (282 and 288 against 239 and 70). In the defended configuration, `Bxb7` stays
   White's commonest first move under either want. White still ends up in 64–71% of episodes, against 77–81% when
   Black only wanted gain.
9. **A partial defender.** Taking back is still a minority answer (190 of 531 in the defended configuration, base),
   and Black captures elsewhere more often (238 and 256 captures against 219 and 76). The defender's want pays any
   way back to even, not taking back as such.

#### Reproducibility

The same seed gives slightly different results in different processes. Seed 1 (base, turns) with `PYTHONHASHSEED=1`
twice: 34 White wants met, 8 defended wins, 100 episodes; with `PYTHONHASHSEED=2` twice: 37, 6, 99. String-hash
randomization changes the iteration order of sets inside the minds; a fixed hash seed reproduces exactly. The
differences are small against the comparisons above, but a single figure is exact only under a fixed `PYTHONHASHSEED`.
Earlier rungs' logs were run without one.

#### Not yet done (updated)

- Why taking back stays a minority answer for a defending Black; whether more time (rounds) or the full arm's
  `sub_cost` changes it.
- Fix `PYTHONHASHSEED` for future runs (or make Gerundelle's iteration order independent of it).
- The sub-want loop of finding 6; what `relation_of` makes of the other mind; no event objects in `DuelWorld`.

#### Why the defender takes back so seldom (traced; `experiments/why3.py`, `PYTHONHASHSEED=0`, base arm, seeds 0–2)

At every Black move right after a White capture, the trace records what in Black's agent chose the move, Black's want
and sub-wants, and what Black's own records say of the take-back in the reading the situation selects
(`logs/why3_s*.log`).

**First, the measure was too broad.** In the hanging configuration White mostly takes with `Rxd5`, and then nothing can
take back, so "a third of the answers" counted many moments with no take-back on offer. Counting only the moments where
one was:

| Seed | take-back on offer | taken | taken by |
|---|---|---|---|
| 0 | 43 | 10 (23%) | planner 5, experiment 5 |
| 1 | 42 | 5 (12%) | planner 4, experiment 1 |
| 2 | 48 | **44 (92%)** | planner 44 |

**Seed 2 defends.** White kept playing the direct `Rxd5` in the defended configuration; Black's take-back `Bxd5` wins
the exchange, its holding comes back when its turn comes round, and the planner plays it every time it is on offer but
four.

**Seed 0: the take-back never pays, by Black's own records.** White plays the combination. Black's `Rxb7` after `Bxb7`
was tried twice in this reading and never brought the want (29 of the 33 refusals); Black's model predicts it gives
`material_even` and not `holding_black_kept`. Checked: both times White answered `Rxd5` and Black's standing was read
down. After `Bxb7` Black is a piece down whatever it plays, so no reply meets the want. The take-back is still the
best reply, but a reply judged only by where things stand after the opponent's next move can't be preferred in a lost
position: every reply looks equally bad, and Black runs `conditions` experiments instead.

**Seed 1: the take-back was never tried in the reading Black is in.** Black's experience of `Rxb7` is split three deep
(on `black_knight_d5_safety_safe`, `black_pawn_h7_safety_safe`, `black_pawn_b6_safety_hanging`), and the half the
situation selects holds no records (32 of 37 refusals). Meanwhile the planner serves sub-wants such as
`black_pawn_g7_safety_hanging` and `black_bishop_b7_safety_attacked`: conditions read off a past success that are
coincidence, the pathology of rung 1c.

#### Findings

10. **A defending mind takes back when taking back pays by the time it is judged.** Against a mistake (the direct
    `Rxd5`) it defends nearly always (seed 2: 44 of 48). Against the combination, no reply restores what was lost, so
    the correct reply is not preferred.
11. **Splits can fragment a push's experience until the case at hand has none** (seed 1), and coincidental conditions
    then become sub-wants. Both are older pathologies, now in the opponent.

#### Not yet done (updated)

- A want that can tell a lesser loss from a greater one: in a lost position, the reply that loses least.
- Seed 1's fragmentation: splits three deep on a push tried a few times.
- The rest as before: `PYTHONHASHSEED` for all runs; the sub-want loop of finding 6; what `relation_of` makes of the
  other mind; no event objects in `DuelWorld`.

### Pieces as given territory (`--given`; Gerundelle `Territory.given`; `DuelWorld(owned=True)`), 2026-10-31

**Why** (the user, asked which way of preferring a lesser loss aligns most with Gerundelle): Gerundelle's own answer is
territory. `own_agent.py` "never reads the world's reward"; an outcome's worth is what it does to the agent's territory
(pulls closed less pulls opened), and a lost slot pulls `1 + held`. That needs a side's pieces to be its territory, and
they were not.

**What the check found.** Black's claims on its own pieces never took (over 400 rounds the bishop was 30 tried, 0
taken; every piece was the same): moving a piece leaves it `present`, because squares are not perceived (rung 0's named
choice). So no piece was ever Black's, and a capture cost nothing in the register. A captured piece also stayed in view
as `captured`, so it was never "gone".

**The change (the user chose "given territory").**
- Gerundelle (backup `backup/molecules_2026-10-31e/`; suite `backup/tests_after_given_final.log`: 72/80, 2 pending, fail
  list identical to the reference): `Territory.given`, regions the agent's own from the start, like the body in
  `own_agent`. Held while in view, `lost` while gone from it, held again when back. Empty unless the world names them,
  so every other mind runs as before.
- First version: a given region held asked nothing (no "is it mine alone?"). Both chess minds then found nothing to try
  and never moved, the calm `Territory.open_slots` warns of ("an agent that perceived everything as its own ... went
  calm"). Now a held given region asks "is it mine alone?" as any held region does.
- World (`DuelWorld(owned=True)`, opt-in): a captured piece leaves view, with its safety object; the capture is still
  delivered as a change. `rung3.py --given` gives each mind its own pieces. Backups: `backup/chessworld_before_owned.py`,
  `backup/rung3_before_owned.py`.

#### Results (10 seeds, base arm, `turns`, Black wants `kept`, `PYTHONHASHSEED=0`; `logs/*_kept_h0.log`, `logs/*_kept_given.log`)

| | not given | **given** |
|---|---|---|
| Black's sadness / frustration | 20 / 101 | **170 / 29** |
| White's sadness / frustration | 22 / 95 | **182 / 45** |
| Black takes back after a capture, defended / hanging | 193 / 26 | 188 / 84 |
| Black's knight flees after a capture, defended / hanging | 42 / 11 | 99 / 53 |
| episodes ending White up, defended / hanging | 73% / 75% | 72% / 77% |
| Black's wants met | 132 | 145 |

#### Why the knight moves more (traced; `experiments/flee3.py`, every Black knight move off d5, 10 seeds; `logs/flee3_*.log`)

| | not given | given |
|---|---|---|
| knight moves off d5 / right after a capture | 129 / 53 | 222 / 152 |
| chosen by the planner | 19 | 75 (62 of them seed 7) |
| chosen by experiments | 110 | 147 |
| slot kinds at the top when an experiment moved it | control 76, lost 8 | **lost 93**, control 3 |

#### Findings

12. **Captures are now losses, and both minds grieve them.** Sadness rises eightfold, about the minds' own pieces
    (`phase:sadness:own:lost:black_knight_d5`), and frustration falls: a capture is a loss now, not a want that keeps
    failing.
13. **Grief pays for experiments with the threatened piece.** With given territory, the experiments that move the knight
    are funded by lost slots (93 of 147), most by the knight's own safety object (41), where before control slots funded
    them. The safety object is where the knight's moves do take, so it is held, and when the knight is captured it leaves
    view and reads lost.
14. **The rest of the rise is one seed.** Seed 7's planner moved the knight 62 times with given territory and never
    without; seeds 1 and 9 went the other way (7 and 10 planned knight moves without, none with). Without seed 7, knight
    moves rise from 118 to 148. Board results barely move (72–77% White up either way), as expected: the planner still
    scores a reply only by whether it meets the want.
15. **A change-want for a state already held makes its opposite a sub-want.** Seed 7's planner served stacks with the
    sub-want `holding_black_lost` (17 knight moves), and seed 0's trace showed it too: to bring about `lost -> kept`
    while kept, the mind first wants lost. A defender's want written as "win back" can make a mind seek the loss.

#### Not yet done

- Step B: the planner valuing a reply by what it does to the territory (`own_agent`'s worth: pulls closed less pulls
  opened). Open decision: what the planner does when every reply loses something.
- A defender's want that is not a change from lost (finding 15).

### Black as a keeper (`--black-want keeper`; the fiction arm's `GerundelleMind(keep=True)`), 2026-11-01

**Why** (finding 15; the user, asked what aligns most with Gerundelle): a want of `holding_black_kept` written as a change
made "lose first" a sub-want. The fiction arm already has a defender: a keeper, whose want is a state to hold. While the
state holds it has no goal; when the state is undone the want comes back, and restoring it meets it.

**The change** (in the arm, opt-in; backups `backup/gerundelle_arm_before_keepwait.py`, `backup/rung3_before_keeper.py`):
- `GerundelleMind(keep_wait=False)`: a keeper whose state holds no longer waits. A chess side must move on its turn,
  and a waiting Black would stand still until the idle limit ended the episode. It takes its turns with the rest of
  its mind and plans for the want only once the state is undone. The default (`True`) is the fiction ladder's keeper,
  which `rung7_gerundelle.py` and `run_ladder.py` use unchanged. Fiction has no test suite of its own.
- Black keeps `holding_black_kept` with `want_count=1`: below its count the arm sets a met want again, which would
  hold the goal while the state already holds.

#### Results (10 seeds, base arm, `turns`, given territory, `PYTHONHASHSEED=0`; `logs/*_keeper_given.log`, `logs/subs_kept_given.log`)

| | Black's want a change (`kept`) | **Black a keeper** |
|---|---|---|
| Black's sub-want `holding_black_lost` ("lose first") | 112 | **27** |
| Black takes back after a capture, defended | 188 / 567 (33%) | **220 / 480 (46%)** |
| Black's other captures after a capture, hanging | 96 | **264** |
| episodes ending White up, defended / hanging | 72% / 77% | **66% / 63%** |
| White's wants met / Black's | 518 / 145 | 384 / 161 |
| Black's frustration | 29 | 23 |

#### Findings

16. **A keeper is the defender's want.** "Lose first" falls by three quarters (112 to 27), Black takes back more in the
    defended configuration, and White ends up less often in both.
17. **A keeper defends by any way back, not only by taking back.** In the hanging configuration nothing can take back
    after `Rxd5`; the keeper captures elsewhere (264 times, against 96), the bishop on c8 taking White's bishop on a6.
    "Takes back" undercounts a defender there; the episode ends are the measure (77% to 63% White up).
18. **The arm switches a keeper's want on, never off.** When the state is restored by something else (the board set
    back), the want stays set until a push meets it, and 8 of 86 keeper moves in a 300-round check were made with the
    want set while the state held. This is the likely source of the remaining 27 "lose first" sub-wants (not yet
    verified). The keeper's start-up already switches it off ("a keeper whose state holds: nothing to pursue"); each
    step doesn't.

Per-seed variation is large (defended take-backs from 0 of 77 to 56 of 73); the totals are the level to read.

#### Not yet done

- Switch a keeper's want off when its state holds, as its start-up does (finding 18), and check that "lose first" goes
  to zero.
- Step B: the planner valuing a reply by what it does to the territory, limited to positions where given territory is
  at stake (scope to be shown to the user first).

#### The keeper's want switched off when its state holds (finding 18 fixed), 2026-11-01

In the arm (backup `backup/gerundelle_arm_before_keeper_off.py`): a keeper with `keep_wait=False` whose state holds
while it still has a want or sub-wants (the state restored by something else, as the board set back) drops them and
marks the region had, as the keeper's start-up does. Waiting keepers (the fiction ladder's) are unchanged. 10 seeds,
base arm, `turns`, given territory, `PYTHONHASHSEED=0` (`logs/*_keeper2_given.log`):

| | keeper, before | **keeper, fixed** |
|---|---|---|
| Black's sub-want `holding_black_lost` ("lose first") | 27 | **0** |
| episodes ending White up, defended / hanging | 66% / 63% | 71% / **52%** |
| Black takes back / knight flees after a capture, defended | 220 / 45 | 87 / 117 |
| White's first move the direct `Rxd5`, defended | 87 | 54 |
| Black's wants met / White's | 161 / 384 | 203 / 544 |

19. **"Lose first" is gone** (112 for the change-want, 27 for the first keeper, 0 now). A keeper wanting its state only
    while it is undone is the defender's want without that pathology.
20. **Defence is mixed by configuration.** Better in the hanging configuration (52% White up, the best of any Black so
    far), worse in the defended one (71%), where Black takes back less and moves the knight away more. White also opens
    with the direct `Rxd5`, the one line where taking back pays, less often (87 to 54). Not traced; per-seed variation
    is large.

Black still sets coincidental sub-wants, such as its own knight hanging (`black_knight_d5_safety_hanging`, 12): the
rung 1c pathology, not the keeper's. Not traced.

#### The next rung, made by `MAKING_RUNGS.md` (proposed, 2026-11-01)

1. **Residue.** Finding 10, which findings 12–20 keep returning to: in a lost position no reply meets the want, so the
   mind cannot prefer the reply that loses least (the defended position against the real combination). Also:
   coincidental sub-wants (findings 11, 20), fragmentation of a push's records (11), the sub-want loop (6).
2. **Missing structure.** A ranking of outcomes the mind owns: one loss smaller than another. In the relation forms
   that is **12, competition / ranking (force, social, scalar)**. A want only says met or not; a scalar comparison of
   outcomes is not in the planner.
3. **What Gerundelle has.** *Partial.* `own_agent.py` values an outcome as the pulls it closes less the pulls it
   opens, and acts on the best even when every option is negative; `Territory` already makes a lost slot pull
   `1 + held`, and chess pieces are now given territory (rung 3). `SovAgent`'s planner does not read it: its reward is
   the share of outcomes that met the want, and `plan_step` acts only when `v > 0`.
4. **World.** Rung 3's duel, keeper Black, given territory, defended position. Today's failure, measured: against the
   real combination the keeper takes back seldom and runs experiments (finding 10; 71% White up, finding 20).
5. **Question:** when every reply loses, does a mind that ranks outcomes by what they do to its territory prefer the
   reply that loses least? Arms: ranking off and on; the scripted Black as control. Measures: Black's reply after
   `Bxb7` (take back, flee, other), what each reply cost Black in pieces lost by the episode's end, episodes ending
   White up, Black's sadness per episode.

So the next rung, made this way, is the **lesser loss: ranking outcomes by territory** (relation form 12). Whether it
is a section of rung 3 or rung 4 is the user's call: it answers rung 3's question of what a defender does, but it
brings a new relation form.
