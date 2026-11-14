# The Warp chess ladder

Each rung is written up the same way as `../cognitivechess/LADDER.md`. The table is a sketch of where the ladder might go, and each rung is still made from the last one's residue.

| Rung | Question |
| --- | --- |
| **0** | In a small position, can it find a winning capture by acting? |
| **1** | Can it learn what flipping does, including where the rules refuse a flip? |
| **2** | Does it find a tactic only flipping makes possible? |
| **3** | Does what it learned carry to new positions? This is where pairs and the aha come in. |
| **4** | Can it play full games, against a random player and then a stronger one? |
| **5** | Is a mind that has learned standard chess reminded of it by Warp? |

## Rung 0: win the hanging piece (`warpworld.py`, `rung0.py`), 2026-11-04

**Question.** One want (material up), the world pushing back, no reply. Does a mind find a winning capture on a Warp board, and how does it compare with plain enumeration and a random mover?

**The world** (`WarpWorld`, the user's engine behind the interface a mind reads, after `../cognitivechess/chessworld.py`):
- **Objects:** every piece by identity (`black_knight_Ld5`), each piece's safety as an object of its own, and `material`.
- **States:** a piece is `present` or `captured`. Its safety is `safe`, `attacked` or `hanging`. Material is `even`, `up` or `down`.
- **Invitations:** the legal moves, flips included. A move's label is ranked by seed, so ties don't follow a name. A move not on offer does nothing.
- **A move's slices:** in its own slice only the piece moved can change. What happens to anything else lands a slice later (principle 0).
- **Episodes:** each try starts from the position, and Black passes.

**The position.** On White's board: White Kc1, Rd1, Bb2, pawns f2 g2 h2. Black's knight on d5 hangs to the rook, and Black's bishop on f6 is attacked by the bishop on b2 but defended by Black's knight on e4. Black's king is on the other board. Flips are on offer, and none is needed.

**Arms.** A mind with the want, at the planner's default budget and at 500. Plain enumeration and a random mover. 10 seeds, 400 ticks.

**What the theory says should come out, written before running.**
1. The mind finds a winning capture in every seed.
2. Each failure teaches, and with no reply a try costs little, so it takes few tries, in the range of enumeration.
3. It settles on what worked: renewed, the want is met nearly every time late in the run.
4. It explores some flips, since open slots pull at every move on offer.

**Results (10 seeds, 400 ticks).** 26 moves on offer, 2 winning (Rxd5, Bxf6: with no reply, a defended bishop still counts), 4 flips.

| | Found | Tries to first win: median, range | Winning share, late |
| --- | --- | --- | --- |
| Mind, budget 60 | 10/10 | 5, 1-13 | 1.00 |
| Mind, budget 500 | 10/10 | 5, 1-13 | 1.00 |
| Plain enumeration | always | 5.5, 1-12 | |
| Random mover | always | 4.5, 1-20 | |

**Against what the theory said.**
1. **Held.** It finds a winning capture in every seed.
2. **Held.** Few tries, in the range of enumeration.
3. **Held.** Once it has a way, every late move wins, and it keeps to one of the two winning moves.
4. **Held only weakly.** It tried a median of 1 flip, and none in 4 of 10 seeds, because it stops exploring as soon as it can win.

**Findings.**
1. **The world works.** The mind reads your engine like any other world, with no refused moves, and no change to Gerundelle.
2. **The planner's budget made no difference,** with identical runs: one good move needs no search.
3. **This position asks little.** No reply and one move is a low bar, and nothing about Warp matters here yet: flips are on offer and never needed.

**Residue.** The mind has touched flipping only by accident. Rung 1 needs a position where a want can only be met by flipping.

## Rung 1: a want only a flip can meet (`rung1.py`), 2026-11-04

**Question.** When the only way to what it wants is across the boards, does the mind find it, and does it hold what it found?

**The positions.** White Kc1, a rook, pawns f2 g2 h2 on White's board. Black's knight on d4 and king on e1, both on the other board. Black passes.
- **One move:** the rook on d6. 47 moves on offer, 24 of them flips, and exactly one wins: flip, then take the knight.
- **Two moves:** the rook on d3, where a forward flip isn't allowed (rule 4). An episode is two moves: it must advance to rank 6 or 7, and only then can it cross.

**Arms.** A mind at budget 500, against enumeration and a random mover on the one-move position. 10 seeds, 1000 ticks.

**What the theory says should come out, written before running.**
1. In the one-move position, open slots pull it through the moves until it finds the flip, and it holds it after that: late, it plays the flip every time.
2. It takes about as many tries as enumeration, since one try here teaches little about the next.
3. The two-move position is harder but reachable: experiments are a preparation and an action, which is exactly its shape. It should find it in most seeds.

**Results (10 seeds, 1000 ticks, budget 500).**

| | Found | First win at try: median, range | Winning share, late |
| --- | --- | --- | --- |
| One move: mind | 10/10 | 29, 1-49 | 1.00 |
| One move: enumeration | always | 29, 1-45 | |
| One move: random mover | always | 42.5, 15-101 | |
| Two moves: mind | **1/10** | 6 | 0.32 in that seed, 0 elsewhere |

**Against what the theory said.**
1. **Held.** With 47 moves and one winner, it finds the flip in every seed and then plays it every time.
2. **Held.** The same median as enumeration.
3. **Did not hold.** I expected most seeds to find two moves. In 9 of 10 it made only 36-49 tries in 1000 ticks and went quiet. Why isn't traced. It looks like the freezing in Nim, and `winner_acts` wasn't on here.

**A finding from the one seed that did.** It didn't use the rook, as I'd assumed. Its king jumped to c3, flipped across, and took the knight with the king (`Lc1Lc3=Rc3`, then `Rc3Rd4`). With Black passing, nothing punishes that. That's a route I hadn't considered when setting up the position.

**A bug in the engine, found by checking the world against it.** In `board.py`'s `push`, any 2-square sideways king move from the e-file on rank 1 is treated as castling, regardless of rights, and it moves the corner piece onto the square next to the king, destroying what stood there. Reported to the user, not changed. These positions start with the king on c1, so they're barely touched by it.

**The trace: why it goes quiet in the two-move position.** It isn't the freeze from Nim: 29 of 32 moves are in the pool, and experiments keep winning. Of about 860 experiments in each of seeds 1 and 2, about 835 were reported by `foreseen` and never made. An experiment here is a preparation and an action, and `foreseen` rules that in a still world, one whose steps were already done in the situations they'd meet comes out as those did. That's right for what the mind perceives, and what it perceives is the cause: after the rook goes from d3 to d6, **nothing it can perceive changes**. A piece's state is `present`, and its safety doesn't move, so every rook move reads as `no_change`, and it met 38-41 pushes in only 2 distinct situations. So it concludes, correctly on what it can see, that a preparation changes nothing.

This is my world's design, carried over from chess, where a piece's state deliberately isn't its square. Its safety only counts direct attacks on the same board, and a rook on d6 threatening a flip-capture isn't read as an attack. It also explains the seed that solved it: a king on c3 of the other board does attack the knight, so the knight read `hanging`, which the mind could see. So it found the only route that showed anything.

## Rung 1b: reading the world as forces (`warpworld.py` with `forces=True`, `rung1b.py`), 2026-11-05

**Why.** The user: a piece on a different square is doing something different, a doing is a force, and pressure on the e-file is a force. Rung 1's trace showed a mind that couldn't see a move change anything. The state shouldn't be the square (the README: no coordinates), and it shouldn't be a label I chose. It should be read off the forces.

**The change, in the world only.** A force is a capture a piece could make next move, flips included, onto a square, whether something stands there or not. Moves that can't capture (a pawn's push, a two-square jump) exert none.
- `<piece>_exerting`: `pressing` if it puts a force on an enemy piece, otherwise `idle`.
- `<piece>_bearing`: `free`, `pressed` if under force and defended, `hanging` if under force and not.
- `file_<board><file>`: `white`, `black`, `contested` or `open`, by who presses at least 3 of its squares (my threshold).

**What the theory says should come out, written before running.**
1. Rook to d6 is visible now: the rook goes `pressing`, and the knight `hanging`. Situations multiply, so `foreseen` stops closing experiments early.
2. So the mind makes many more pushes in the two-move position, and it finds the crossing in most seeds, not 1 of 10.
3. The one-move position stays solved.

**Results (two moves, 10 seeds; one move, 5 seeds; 1000 ticks).**

| | Before, rung 1 | Read as forces |
| --- | --- | --- |
| Two moves: tries | 36-49 in 9 seeds | 78-238 |
| Two moves: found | 1/10 | **0/10** |
| One move: found | 10/10 | 5/5 |
| One move: first win at try, median | 29 | 100 |
| One move: winning share late, median | 1.00 | 1.00 (0.65 in one seed) |

**Against what the theory said.**
1. **Held.** The rook's move is visible now, and the mind makes more pushes.
2. **Did not hold.** It finds the crossing in none of the seeds. I expected most.
3. **Held, slower.** The one-move position stays solved, at about three times the tries.

The first trace, of seed 0: 78 pushes, all from experiments, with `foreseen` still reporting 470 experiments against 63 that went on, and the rook never going to d6 as a first move.

**The wider trace (seeds 0, 3, 6, 2).** The mind does get its chance: 13-29 second moves made with a capture of the knight on offer, 89 in all, and none takes it. Every push came from experiments. In 3 of the 4 seeds the winning move is among the pushes it knows. While a capture was on offer, it also sat for 18-67 ticks across a run, and my world sets a position back after 6 idle slices. Not yet established: why the capture isn't chosen. With 30-47 moves on offer, chance alone would give about 2 of those 89, so 0 doesn't say much by itself. A possibility: a move new to this position needs its question to win attention before an experiment can come of it, and the position may not last long enough.

## Rung 1c: one mind carried up the ladder (`rung1c.py`), 2026-11-05

**Why.** The trace showed a fresh mind can't tell which untried move matters: every new move reduces uncertainty about as much as the next, and it has never seen a capture make the knight disappear and material go up. The user: maybe it doesn't have enough experience yet. The README's curriculum: each step adds one concept, tested on what's already confirmed.

**The setup.** One mind, carried: rung 0's position (400 ticks), then the one-move position (1000), then the two-move position (1000). All read as forces. Pieces are named by their starting squares, so the rook is `Ld1`, then `Ld6`, then `Ld3`: what carries over has to go by structure, not by name. The comparison is a fresh mind in the two-move position: 0 of 10 in rung 1b. 10 seeds.

**What the theory says should come out, written before running.**
1. The carried mind finds the two-move crossing in most seeds, against 0 of 10 fresh.
2. It finds the one-move crossing in fewer tries than a fresh mind did (median 100), having captured before.
3. Some of this shows as recall by shape or as experiments led by what it learned, not only by chance.

**Results (10 seeds).**

| Position | Carried mind: found | First win at try, median | Fresh mind, read as forces (rung 1b) |
| --- | --- | --- | --- |
| Rung 0 | 10/10 | 4 | |
| One move | **6/10** | 37 | 5/5, median 100 |
| Two moves | **1/10** | 56 | 0/10 |

Recall by shape fired in no seed, at any stage.

**Against what the theory said.**
1. **Did not hold.** The carried mind finds the two-move crossing in 1 of 10, not most.
2. **Mixed.** Where it found the one-move crossing, it took fewer tries (37 against 100), but it failed in 4 of 10 seeds, where every fresh mind found it. Carrying rung 0's experience hurt there.
3. **Did not hold.** No recall at all.

Not traced: why experience from rung 0 makes the one-move position harder in 4 seeds, and why nothing is recalled. The pieces are named by starting square, so nothing learned about `Ld1` is about `Ld6` by name, and recall matches by gerund and push strength, not by name.

## Rung 1d: a mind for each piece (`pieceminds.py`, `rung1d.py`), 2026-11-05

**The idea (the user).** One main mind, and each piece has its own mind and its own wants, like a sub-mind. The thoughts that win in the piece minds compete in the main tournament, and one of the minds wins out. The main tournament has its own bid, with binding and support, so a piece's bid doesn't carry over: its thought enters the main pool as a molecule, and the main mind bids on it fresh. A piece's wants strive for uniqueness, which is a form of ownership. A piece's thought counts as lived in the main mind (the user: whichever).

**How it's built, with Gerundelle unchanged.**
- **Each White piece** has a Gerundelle agent that perceives the whole board and is offered only its own moves. It thinks each tick and doesn't act itself. When the main mind plays its move, the piece lives the outcome through `SovAgent.observe_other`.
- **Its want: uniqueness.** The world reads `<piece>_unique`: `alone` if it presses an enemy piece no other White piece presses, `shared` if it presses one another piece also presses, `none` otherwise. Each piece wants `alone`.
- **Into the main pool:** a piece's top-level winners among its own moves, and the move its planner holds if it has one, enter the main pool with their activation in the piece's mind.
- **The main mind:** the same agent as before, with `winner_acts` on, so a tournament winner can be played when it has no plan.
- **Control:** the main mind alone, with `winner_acts`, so a difference comes from the piece minds.

**What the theory says should come out, written before running.**
1. Once the rook reaches d6, taking the knight is something only the rook can do: it's `alone` there, and its mind wants that, so it puts the capture forward.
2. So with piece minds, the main mind finds the two-move crossing in most seeds, against 1 of 10 for one mind.
3. The control does about as one mind did.

**Results (6 seeds each, 1000 ticks).**

| | Found | First win at try, median | Winning share late, median |
| --- | --- | --- | --- |
| Piece minds | **3/6** | 127 | 0.01 (0.50 in seed 0) |
| Control: main mind alone, `winner_acts` | 1/6 | 327 | 0.00 |
| One mind, rung 1b (no `winner_acts`) | 0/10 | | |

The rook's own want was met (`alone`) in 5 of 6 seeds, from 3 to 46 times. It put the knight capture forward only 0-2 times per seed.

**Against what the theory said.**
1. **Did not hold as predicted.** The rook reached `alone` often, but rarely put the capture forward.
2. **Partly.** Piece minds found the crossing in 3 of 6 against 1 of 6 for the control. That's better, and short of most. Only seed 0 settled on it.
3. **Held.** The control did about as one mind did.

**A finding about the want.** The rook's want, uniqueness, is met by *pressing* the knight. Taking the knight ends what it alone presses, so the capture undoes its want. So once the rook stands at d6 pressing the knight alone, its own mind has what it wants, and has no reason to take. Uniqueness as I read it rewards holding a threat, not carrying it out. The main mind's want (material up) is what the capture serves.

**The user: if it captures it, it owns the knight for eternity.** Pressing alone is a claim that can still be contested, and a capture is ownership that can't be undone, so a capture is the fullest form of the piece's uniqueness. So `<piece>_unique` is now `owns` once that piece has captured something this game, and stays so. A piece wants `owns`, and `alone` is the way there.

**What the theory says should come out, written before running.** The rook's mind now wants the capture, so it puts it forward, and the piece minds find the two-move crossing in most of 6 seeds, settling on it.

**Results with ownership by capture (6 seeds, 1000 ticks).** Found in 3/6, as before (seeds 0, 1 and 5), with seed 5 settling (80 wins, 0.43 late). The rook reached `owns` in no seed, and put the knight capture forward 0-2 times per seed. So the wins came from another piece, most likely the king route seen in rung 1, though which piece isn't recorded here.

**Against what the theory said. Did not hold.** Making the capture the rook's own want didn't make its mind put the capture forward. Not traced.

**The trace of the rook's mind (seed 3).** The rook could take the knight on 14 ticks, in windows of about 2 ticks.
- **First tick of a window:** the capture isn't in the rook's mind yet. Its pool still holds the last position's thoughts, and a newly offered move enters on the next perception.
- **Second tick:** the capture is in its pool, bidding 1.95-2.44, the same as the rook's other new moves from that square. Its top level takes four of them, and they tie, so the tie is broken by the move's name. The four that win have the lowest seeded labels (`041`, `076`, `170`, `283` against the capture's `541`; `037`, `063`, `066`, `072` against `657`). The capture won the rook's top level once in 14 ticks.
- **The rook's planner** returned no plan every time: it has never captured, so nothing it has lived links the capture to `owns`. Its want has no way to point at the move.
- **The main mind** made no move on 7 of those ticks and played another piece's move on the other 7, 6 times from an experiment already under way.

So the want can't pick out the capture before the capture has ever been made, and among equal new moves the order seed decides. That's what the seeded labels were for, so that ties don't follow a name, and here the capture's label happened to rank low.

## Rung 1e: potential forces (`potential.py`), 2026-11-05

**Why.** The trace: before a capture has ever been made, nothing gives it a pull of its own, so it ties with every other new move and the tie goes by label. The user's potential forces: a possible capture is a potential force.

**The change.** Each move on offer carries the force it would exert, read from the position before it's tried: onto a `hanging` enemy piece (no reserve against it) 3, onto a `pressed` one (held by a defender) 2, a quiet move 1 (my scale). That is the move's activation when it enters the tournament, in place of the flat 1.0 every invitation gets now. The rest of the bid is unchanged. Gerundelle is unchanged: it's a subclass of `Mind` here.

**What the theory says should come out, written before running.**
1. In the rook's mind, the capture now outbids its other new moves when it appears, and the rook puts it forward.
2. With piece minds, the two-move crossing is found in most of 6 seeds, and taken by the rook.
3. The main mind alone improves too, since its invitations carry the same force.

**Results (6 seeds each, 1000 ticks).** A note on reading the winning share here: each episode is two moves and only the second can win, so 0.50 means every episode won.

| | Found | First win at try, median | Seeds winning every episode late (0.50) |
| --- | --- | --- | --- |
| Piece minds, with potential forces | **5/6** | 84 | 2 |
| Main mind alone, with potential forces | **5/6** | 82 | 1 |
| Piece minds, without (rung 1d) | 3/6 | 127 | 1 |
| Main mind alone, without | 1/6 | 327 | 0 |

With piece minds, the rook took the knight itself (`owns`) in 4 of 6 seeds, and put the capture forward 2-15 times.

**Against what the theory said.**
1. **Held in part.** The rook puts the capture forward now (up to 15 times), and takes it in 4 seeds.
2. **Held.** 5 of 6 with piece minds.
3. **Held.** The main mind alone improves as much: 5 of 6.

**Findings.**
1. **Potential forces are what fixed it.** Both arms went to 5 of 6. Here, piece minds add little once moves carry their force.
2. **Finding isn't settling.** In 3 seeds of each arm, it found the crossing and won only a few more times.

**The trace: why most seeds don't settle (seeds 3 and 2, the main mind alone).** After the first win, nearly every episode's first move came from an experiment (58 of 61 in seed 3, 42 of 43 in seed 2), and the planner held no way from the start (value 0). When an experiment's first move happened to put the rook on d6, the planner did take the capture as the second move. So the mind holds the second step, and not the first.

Why the planner can't see two moves ahead here: `Model.actions` offers a push wherever its configuration holds, and here a move's configuration is `<piece>_present`, which holds everywhere. So after its first move, the model considers every push the mind knows from any position: 349 of them in seed 2, at the second step of a three-deep search. With 500 rollouts, it finds no way. With 5,000 it finds one, and with 20,000 it picks the rook to d6 (value 2). It's the same root as rung 1: a piece's state doesn't say what it's doing, so where a move can be made isn't read from the state, and the planner's search spreads over moves that aren't on offer there.

(Seed 0, which won every episode, gave no episodes in this trace: a fault in how the trace splits episodes, not looked into.)

## Rung 1f: the planner reads what was on offer (`offers.py`), 2026-11-05

**Why.** The trace: the planner's model offers every push the mind knows wherever its configuration (`<piece>_present`) holds, which is everywhere, so its search spreads over 349 moves at the second step, almost none on offer there. Chess fixed this at the root only (`plan_step`'s comment, cognitive chess rung 1).

**The change.** The mind already perceives what's on offer each tick. It now remembers it: for each situation it has been in, the moves offered there. The model then considers only those in a situation it knows, and is unchanged in one it doesn't. It's the mind's own experience, with nothing about the rules. Gerundelle is unchanged: a subclass of `Model` here.

**What the theory says should come out, written before running.** From the start, the planner now finds rook to d6, then the capture, at budget 500, so most seeds settle: winning every episode late (0.50) in most of 6 seeds, against 1-2 before.

**Results (6 seeds each, 1000 ticks).** Winning every episode late (0.50) is what settling means here.

| | Found | Settled (0.50 late) | Not settled |
| --- | --- | --- | --- |
| Piece minds, potential forces, offer memory | 5/6 | **4** (seeds 0, 1, 2, 5) | seed 3 found and didn't settle; seed 4 never found |
| Main mind alone, potential forces, offer memory | 5/6 | **3** (seeds 0, 1, 2) | seeds 3 and 5 found and didn't settle; seed 4 never found |
| Piece minds, potential forces (rung 1e) | 5/6 | 2 | |
| Main mind alone, potential forces (rung 1e) | 5/6 | 1 | |

**Against what the theory said. Held for piece minds,** settling in 4 of 6, against 2 before. The main mind alone settles in 3 of 6, against 1.

**Findings.**
1. **Remembering what was on offer is what lets the mind plan the first move.** Settling doubled or tripled in both arms.
2. **The settled line isn't always the rook.** With piece minds, the rook reached `owns` in 2 seeds at most once: in the settled seeds another piece takes the knight, most likely the king's route across.
3. **Not traced:** seed 4, which never finds the crossing in any arm, and seed 3, which finds it and doesn't settle.

## Rung 2: Black gets minds too (`duel.py`, `rung2.py`), 2026-11-05

**Why.** A forced win against a defending Black couldn't be found by trying positions: in 7 fork positions, no White first move won against Black's escape every time. The user chose: Black's pieces get minds, each wanting safety, the way White's pieces want to own. The question becomes how the minds play over many games, not whether one forced line is found.

**The world** (after chess's `DuelWorld`). Only the side to move is offered moves, and its mind steps until it moves (at most 5 slices). What a move came to reaches the mind that made it in its own next slice. A side's standing (`standing_white`, `standing_black`: up, even or down, from that side's view) is read when its turn comes round, after the reply. An episode is 4 half-moves, from rung 2's position (RUNG2: the rook on d3, Black's knight on d4, bishop on a6, king on e1 on the other board).

**The minds.** Each side has a main mind (potential forces, offer memory, `winner_acts`) wanting its standing up, and a mind for each piece. A piece's want comes from where it stands: `free` while it bears a force (safety), otherwise `owns` (a capture). Gerundelle is unchanged.

**Arms.** White with piece minds, and White's main mind alone, each against Black with piece minds. 6 seeds, 600 rounds.

**What the theory says should come out, written before running.**
1. Black's pieces learn to get out of the way: a hanging Black piece is moved to safety more often late than early.
2. White wins material in some episodes, less often than against a passing Black.
3. White with piece minds does better than White's main mind alone, now that both sides have more than one thing to attend to.

**First run (void: a bug of mine).** Medians over 6 seeds: White up late 0.00 (pieces) / 0.01 (alone), White down late 1.00 / 0.97; Black's rescues early 0.30 -> late 0.49 / 0.28 -> 0.42. Logs kept as `rung2_*_prefix.log`.

**Trace** (`trace_rung2.py`, seed 1). Most material changes were Black's turn moving a *White* piece (`Lg2Lg3`, `Ld4Ld6`), which the engine then coloured Black: the move pushed with Black to move. Cause: `warpworld.pressure()` and `black_safety()` set `board.turn` directly, and the engine caches legal moves by Zobrist hash, which only `push`/`pop` keep current. A board turned to the other side was served the first side's cached moves. So Black was offered White's moves in the duel, and in every forces reading since rung 1 one side's pressure was read from the other side's moves. Not the engine's bug: I bypassed its interface. Fix: `rehash()` after every direct turn or en passant change.

**After the fix** (same trace, 120 rounds): Black moves only its own pieces. Black's captures come from the position: its king on e1 flip-captures the f2 pawn in one move (`Re1Rf2=Lf2`), and its bishop on a6 flips onto the rook on d3 (`Ra6>La6Ld3`). RUNG2 hands Black a free capture at the start of every episode.

**Rerun, 2026-11-05.** New start `RUNG2B` (my choice, agreed by the user): RUNG2 with Black's bishop on a5 and king on a1, the nearest squares where neither side can capture on its first move (`find_rung2b.py`). The rook-and-knight fork is unchanged. Predictions stand as written. Rungs 1b-1d are being rerun on the fixed forces reading into `rerun/`.

### Rerun on the fixed forces reading (2026-11-06)

**Rung 1b-1f** (`rerun/`). Old figures in brackets.

| | Found | Settled (0.50 late, or near) |
|---|---|---|
| 1b fresh mind, forces: one move | 9/10 [5/5] | |
| 1b fresh mind, forces: two moves | 2/10 [0/10] | 0 |
| 1c carried mind: one move / two moves | 5/10 / 0/10 [6/10 / 1/10] | |
| 1d piece minds | 1/6 [3/6] | 0 |
| 1d main mind alone | 2/6 [1/6] | 0 |
| 1e piece minds, potential forces | 5/6 [5/6] | 1, seed 2 at 0.41 [2] |
| 1e main mind alone, potential forces | 5/6 [5/6] | 1 [1] |
| 1f piece minds, potential + offer memory | 5/6 [5/6] | 2, seeds 3 and 2 at 0.49 and 0.43 [4] |
| 1f main mind alone, potential + offer memory | 5/6 [5/6] | 2 [3] |

The conclusions stand: potential forces lift finding from 1-2/6 to 5/6, and offer memory lifts settling. One change: with the forces read right, the rook itself takes the knight in 1f seed 3 (reached `owns` 102 times, put the capture forward 110 times). Before, the rook reached `owns` at most once.

**Rung 2, from RUNG2B** (6 seeds, 600 rounds, medians).

| White | White up early | late | White down late | Black's rescues early -> late |
|---|---|---|---|---|
| Piece minds | 0.04 | 0.05 | 0.02 | 0.39 -> 0.43 |
| Main mind alone | 0.07 | 0.15 | 0.03 | 0.34 -> 0.32 |

1. **Black learns to rescue: barely or not.** Slightly up with White's piece minds (0.39 to 0.43), flat against White alone.
2. **White wins material in some episodes: held** (5% and 15% late). Against a passing Black wasn't run in rung 2, so "less often" has no figure yet.
3. **Piece minds beat the main mind alone: missed.** Alone did better late (0.15 against 0.05), rising in 4 of 6 seeds.
Black's want (`standing_black_up`) was met 0 times in every seed: from RUNG2B Black never wins material.

**Trace of the miss on 3** (`trace_rung2_white.py`, seed 5, where alone was up in 0.52 of late episodes and piece minds in 0.05).
- Late, both arms move mostly by plan (piece minds 99 of 110 moves, alone 57 of 99). Both move on about half their turns within 5 slices.
- With a capture on offer, alone's plan took it 27 of 30 times; the piece-minds arm's plan 1 of 14.
- What each main mind lived: alone, 30 standing changes in 513 pushes, 23 of them from one capture, `Lc3Ld4=Rd4` (onto the knight). Piece minds, 6 in 468, from king moves (`Lc1Ld2=Rd2` twice, `Ld1Le2=Re2`, `Rd1Re2`).
- So the piece-minds arm's plan follows the king's route, which worked twice: late it plays `Lc1Ld1` with the capture `Re2Rf3` on offer, a capture it never lived. Its planner knows only what it lived, and nothing tells it a capture it hasn't made raises material.
- Not yet traced: why the piece-minds arm never came on the rook's `Lc3Ld4=Rd4` early, when its moves came from experiments (49) and attention (44), 28 of them from the pieces' ideas (king 18, rook 9, pawn 1).

**Trace of the early half** (`trace_rung2_white.py` per-turn records, `trace_white_*.json`, seed 5).
- Correction to the line above: neither arm came on the knight capture in the first half. `Lc3Ld4=Rd4` is the *king's*: `Lc1Lc3` (its jump) then across onto the knight. It was on offer in no early turn in either arm.
- Alone: an experiment played `Lc1Lc3` at turn 236 (episode 60 of 108); the capture was on offer next turn and attention took it. After that the plan played the pair 23 times, the capture on offer in 23 of 25 turns after the jump.
- Piece minds: `Lc1Lc3` was played twice, at turns 98 and 99 (an experiment, then attention, the king's own idea 27 times early), and neither time was the capture on offer next turn: the first ended the episode, after the second Black's answer left nothing to take. Then it lived king captures elsewhere (`Lc1Ld2=Rd2` twice, `Ld1Le2=Re2`), and from turn 175 its plan took the king's `Lc1Ld1`, `Ld1Le1` route.
- Moves by 50 turns (plan/experiment/attention). Piece minds: 0/15/19, 0/16/11, 0/8/12, 17/8/2, 24/9/0, 34/1/0, 34/1/1. Alone: 0/15/18, 0/15/11, 1/13/11, 0/1/10, 11/3/7, 30/1/1, 16/0/13. A want with a way known is acted on before any experiment (`SovAgent.tick`): once the piece-minds arm had a way, experiments fell to 1 in 50 turns, and the jump was never tried again. The alone arm had no settled way until turn 239, and was still experimenting when it found the jump.

## Rung 3: does what it learned carry to new positions? Pairs and the aha (`rooms3.py`, `pairs3.py`, `rung3.py`), 2026-11-06

**Rooms** (checked against the engine in `rooms3.py`, Black passing, episodes of 2 White moves).
- *Learn*: rung 1's two-move room (RUNG1_TWO). The knight is two White moves away, by 7 lines (the king's jump or flip, or the rook's crossing).
- *Same*: that room shifted two files over. Every piece stands elsewhere and so has another name; the same 7 lines exist, two files over.
- *Loose*: as *same*, the knight one square further (on what was e4). It's three White moves away, so no episode can take it.

**The mind.** Rung 1f's main mind (potential forces, offer memory, `winner_acts`), alone. It lives the learn room for 1000 slices, then is carried into *same* or *loose* for 600.

**Pairs** (`pairs3.py`, after `../structuralsimilarity/forward.py`). A relation is read from the mind's own trials: in this reading, a move by A leaves B's reading at X within these slices, kept only if every trial in that reading shows it. A known node's pair is the relations that specify it: for a move, what it does; for a reading, the moves that bring it about. My choices where the theory doesn't settle them: the force a relation carries is the reading it leaves (Warp has no light or hard pushes); with no physics between moves, no relation is implied by others, so nothing is reduced away; a structure is compared with its move carried as the piece making it (the square it goes to is the move's name); objects are named with their room. Pairs are re-read every 20 slices and scored against the learn room's sealed pairs; a score is written as `similar_to` in the SOV, and its first writing presents the aha molecule (`aha.py`).

**What the theory says should come out, written before running.**
1. In *same*, once the mind takes the knight there, its capture structures are scored against the learn room's: aha molecules between capture and capture, in most seeds.
2. In *loose*, no capture-to-capture aha: nothing is taken, so there is no capture structure in that room.
3. Ahas of other structures (a move pressing a piece, a piece left alone) come in both rooms: those structures are in both.

**Results** (6 seeds; `rung3_logs/`).

| | Took the knight in the new room | Ahas, median | Reached the top | Capture ~ capture |
|---|---|---|---|---|
| *Same* | 5 of 6 seeds (late 0.50 in all 5) | 627 | 2-33 per seed | **0** in every seed |
| *Loose* | 0 (as built) | 1921 | 22-55 per seed | 0 |

1. **Missed.** No capture-to-capture aha in any seed, though in seeds 1, 2 and 5 the learn room had capture pairs and the mind took the knight in *same* 150, 86 and 141 times.
2. Held, trivially (nothing taken).
3. Held: ahas of other structures (files, a piece pressing, alone) in both rooms, more in *loose*.
Side result: seeds 3 and 4 barely won in the learn room (late 0.05, 0.00), then won every episode in *same* (0.50).

**Trace of 1** (seeds 1 and 5). Seed 5's learn room and *same* hold the same line two files apart: the rook's `Rd7Rd4` and `Rb7Rb4`, each leaving the knight `captured` one slice later. They score 0. The learn room's relation carries conditions, the mind's own split of that move (`black_king_Re1_exerting_pressing`, `black_knight_Rd4_bearing_hanging`); in *same* the move was never split, so its relation has none. The score counts a relation as shared only if its conditions map too, so a split relation never matches an unsplit one. Seed 1 is the same (the king's `Rc3Rd4` split on the same two readings against the rook's unsplit `Lb6>Rb6Rb4`).

**The user's decision (A):** a relation is scored as its parts, its core (a move by X leaves Y at this reading within these slices) and each condition it holds under, tied to that core (`pairs3.parts`). Seed 5's two rook captures now score 0.5 (rook to rook, knight to knight): alike in what the move does, different in when the mind knows it holds. Rerun into `rung3_logs/`; the first run's logs are in `rung3_logs/v1/`.

**Results with relations scored by parts** (6 seeds, `rung3_logs/`).

| Seed | Learn room had a capture pair | Took the knight in *same* | Capture ~ capture ahas in *same* | Best score | First, slices into *same* | In *loose* |
|---|---|---|---|---|---|---|
| 0 | yes | no | 0 | | | 0 |
| 1 | yes | 150 | 4 | 0.50 | 20 | 0 |
| 2 | yes | 86 | 4 | 0.40 | 260 | 0 |
| 3 | no | 101 | 0 | | | 0 |
| 4 | no | 150 | 0 | | | 0 |
| 5 | yes | 141 | 4 | 0.50 | 40 | 0 |

1. **Held where it could.** In every seed that had a capture in both rooms (1, 2, 5), the capture structures were scored alike: the knight taken there ~ the knight taken here (0.40-0.50), and the move that took it ~ the move that took it (0.36-0.44, the rook to the rook in seeds 2 and 5, the rook to the king in seed 1). Seeds 0, 3 and 4 lacked a capture in one of the rooms.
2. **Held.** None in *loose*.
3. **Held.** Other ahas in both rooms: medians 863 (*same*) and 2586 (*loose*), 2-40 reaching the top per seed.
No capture aha reached the top level in any seed. Each enters with its score as activation (0.40-0.50), among hundreds to thousands of other ahas scored 0.33-0.67 at the median.

## Rung 2b: patience (rung 2, `--patience`), 2026-11-06

**Why.** Rung 2's trace (seed 5): the piece-minds arm settled on the king's route, which had worked twice, and a want with a way known is acted on before any experiment, so it never tried the jump that the mind alone found. Gerundelle's own answer to a way that keeps failing is temperament's patience (`Params.patience`): when the wanted region's claims fail as many times running as the mind's patience, the want is given up and its slot parked, until a try on that region takes again.

**Set-up.** Rung 2 from RUNG2B, White's main mind with patience 2 (fiction's "impatient") and 6 ("patient"), both arms, 6 seeds, 600 rounds. Black as before (no patience). `rung2.py` sets a given-up want again at the next slice (my choice, as before): the want is the same, and Gerundelle decides whether its region stays parked. Patience also makes a mind watch before acting on attention, up to its patience and never past the world's watch (3 slices); that comes with the switch.

**What the theory says should come out, written before running.**
1. White gives its want up in every seed (the king's route fails far more often than it takes).
2. With the want parked, experiments and attention return, so the piece-minds arm's White wins material late more often than without patience (0.05).
3. The gap between piece minds and the main mind alone narrows.

## Rung 4: full games (`gameworld.py`, `rung4.py`), 2026-11-06 (set up; not run)

**Set-up.** The rulebook's starting position (`WarpBoard.starting_position()`). White is rung 1f's main mind, its want to win the game (`outcome_white_won`, read from the engine's result; my choice, as the Nim mind's `outcome_won`). Black plays a uniformly random legal move. A game ends by the engine's rules (a king taken, no legal move, fifty moves) or after 80 half-moves (my cap). Arms: carried (the mind lives rung 3's learn room first) and fresh.

**Found while setting up, before any run.** From the starting position White wins in one move: `Le7Le5=Re5`, the king's two-square jump over its own pawn, flipping onto Black's board. After it the engine gives Black 0 legal moves with Black in check (cross-board check, `is_in_check`), result 1-0. Black's pieces don't attack the White king there (`is_attacked_by` is False). Black has the mirror: after any quiet White first move, `Re7Re5=Le5` mates White (the random Black found it in the first game). A fresh mind in a 200-round smoke test found White's and won every later game in one half-move. Reported to the user, who asked whether I had read the rules. I hadn't. The rulebook (`game/rulebook_pages`, page 2) starts the pawns in a chevron (a2, b3, c4, d5, e5, f4, g3, h2), and the engine's `WarpBoard.starting_position()` builds exactly that. `move.py`'s `STARTING_FEN`, which I had used, isn't the rulebook's start: its pawns are all on one rank and its back row is on rank 7, which kings can't enter. From the real start neither side has a one-move win, and no Black reply to any of White's 43 first moves ends the game. Rung 4 now starts from `starting_position()`; the engine is unchanged.

**Rooms (the user's decision, 2026-11-06): the user's openings and the rulebook start, both.** The mini games (`E:/vscode/warponechess/mini_games`) come from `warp_self_play.py`: each iteration plays one game from one of 12 set openings and the engine's best move after it (`line_A`), and every mini game of that iteration is a proven line from that one position. So they are 11 start positions (iterations 281-293; 293 repeats 281's opening with another move), not 6,492 rooms. Each start is a room here (`gameworld.opening_rooms`), and so is the rulebook start (`chevron`). The proven lines are kept for measuring and never reach the mind. Where Black is to move at the start, the random player moves first.

**Runs (my choices).** Every room with a carried mind (rung 3's learn room, 1000 slices, then 2000 rounds in the room), 3 seeds; the rulebook start also with a fresh mind, 3 seeds. One room per run: a world's piece names are fixed by its start, so one world can't change rooms between games.

**What the theory says should come out, written before running.**
1. The mind wins games against the random player, and more often late than early: a mate it has lived becomes a way its planner knows.
2. It wins more in the rooms whose proven lines are mostly White mates (iterations 286, 288-291) than in the others.
3. Captures come first: material up in most games, before wins, since a capture is the first thing a carried mind has lived.

### Rung 2b results (6 seeds per arm, `rung2b_logs/`)

| White | Patience | White up late, median | By seed | Gave its want up, by seed |
|---|---|---|---|---|
| Piece minds | none (rung 2) | 0.05 | | |
| Piece minds | 2 | 0.01 | 0.05, 0, 0, 0.06, 0.02, 0 | 430, 0, 0, 249, 1091, 0 |
| Piece minds | 6 | 0.00 | 0, 0, **0.44**, 0, 0.21, 0 | 0, 1089, 107, 0, 905, 0 |
| Main mind alone | none (rung 2) | 0.15 | | |
| Main mind alone | 2 | 0.04 | 0.04, 0.08, 0.02, 0, 0.03, 0.30 | 684, 1313, 320, 0, 770, 1183 |
| Main mind alone | 6 | 0.03 | 0.28, 0.13, 0, 0, 0.05, 0 | 132, 153, 0, 1695, 571, 0 |

1. **Missed.** White gave its want up in 15 of 24 runs; in 9 it never did.
2. **Missed at the median.** With piece minds White was up late less often than without patience (0.01 and 0.00 against 0.05), though two seeds at patience 6 did better than any without it (0.44, 0.21).
3. **Narrowed, the wrong way.** The gap closed because the main mind alone fell (0.15 to 0.03-0.04), not because piece minds rose.
Not traced yet: why 9 runs never gave up, and why patience lowered the mind alone.

**Trace of 2b** (`trace_rung2_white.py --patience`, main mind alone, seed 5; `trace_white_alone_p*_s5.json`).

| Patience | White turns | Turns with no move | Moves on attention, early | Lived standing up | Gave up |
|---|---|---|---|---|---|
| none | 396 | 197 | 50 | 30 (23 the king's jump-then-capture) | 0 |
| 2 | 421 | 233 | 5 | 17 (14 the same capture) | 1183 |
| 6 | 504 | 400 (late: 375 of 428) | 5 | 0 | 0 |

- **Why patience lowered the mind alone.** Patience is two things in Gerundelle: the give-up, and a patient mind watching before it acts on attention, up to its patience in quiet slices and never past the world's watch (`SovAgent.winner`: here min(patience, 3)). A side has 5 slices to move (`TURN_STEPS`, my choice), and the first of them often goes on watching its last move's answer. So a move on attention mostly no longer fits in a turn: moves on attention fell from 50 to 5 early, and at patience 6 White moved in 12% of its late turns (51% without). Fewer moves, fewer tries: at patience 6 it never came on the jump and the capture.
- **Why 9 runs never gave up.** A want is given up when its region's claims fail as many times running as the patience. Failures are counted only on a region a try touched (`Territory`: the regions of a push are the one pushed, the ones that changed, and those it has claims on). In the 9 runs White's standing never changed, so its region had no claims and no count: at patience 6 seed 5 the `standing_white` row has no `fails` at all. All 9 are runs where White's want was never met.

**Rerun of 2b (the user agreed).** A side's turn is now `TURN_STEPS` plus the patient wait, min(patience, the world's watch of 3): 7 slices at patience 2, 8 at 6. Without patience it stays 5, as rung 2 ran. Gerundelle unchanged. First run's logs in `rung2b_logs/v1/`. Predictions as written above.

**Rerun results** (wait fitted in the turn; 6 seeds per arm).

| White | Patience | White up late, median | By seed | Gave up, by seed |
|---|---|---|---|---|
| Piece minds | none | 0.05 | | |
| Piece minds | 2 | 0.02 | 0.03, 0.07, 0, 0, 0, 0.12 | 2108, 1986, 0, 277, 2688, 1403 |
| Piece minds | 6 | 0.05 | 0.05, 0, 0.05, 0, 0.10, 0.04 | 0, 0, 0, 0, 983, 0 |
| Main mind alone | none | 0.15 | | |
| Main mind alone | 2 | 0.04 | 0.03, 0.38, 0, 0.05, 0, 0.08 | 1092, 714, 844, 1826, 2500, 937 |
| Main mind alone | 6 | 0.02 | 0, 0.02, 0, 0.04, 0.25, 0.02 | 0, 399, 0, 1029, 465, 1705 |

All three predictions still miss. With piece minds, patience leaves White where it was (0.02 and 0.05 against 0.05); the mind alone still falls (0.04 and 0.02 against 0.15). At patience 6, the piece-minds arm gave up in 1 seed of 6. Not traced yet.

**Trace of the rerun** (`trace_*_v2.log`, `trace_white_*_p*_s*.json`; main mind alone seed 5 at patience 2 and 6, piece minds seed 0 at patience 6).
- **Moves came back, plans didn't.** The mind alone at patience 2 moved in 64% of its turns (50% without patience). But its late moves were 93 experiments, 16 on attention and 6 by plan, where without patience they were 57 by plan. With a capture on offer it took it 5 times in 34 (28 in 33 without patience).
- **Once given up, the want stays given up.** The check runs at the start of every slice: if the wanted region's failures running are at least the patience, the want is given up. The count resets only when a try on that region takes. `rung2.py` sets the want again each slice (my choice), and it is given up again in the same slice: 937 times at patience 2, 1705 at 6. While the count stands, the planner never runs for the want, so the way it found (the king's jump then the capture onto the knight, lived 3 times at patience 2) is never planned again. The mind is left to experiments, which don't aim at captures.
- **Correction to the first trace: why piece minds at patience 6 seed 0 never gave up.** Its `standing_white` row exists and its failure count is 0 in all 305 turns that read it. A try counts against a region only if it touched that region; White's standing changed twice in the run, both as predicted, so both took. Every other try left the standing alone and counted for nothing. A want whose region rarely changes accrues no failures.
- Not traced: why the mind alone at patience 6 moved in only 30% of its late turns, 73 of the unmoved turns with its want set.

**The user: "isn't that a conflation?" Yes.** The king's route worked when a Black piece stood where it landed and not otherwise: one move, two outcomes, a situation the mind hadn't separated. That is the meta layer's job (a conflated push is split), not patience's, so rung 2b answered the wrong question.

**Trace** (`trace_split.py`, seed 5, piece minds, no patience; White's main mind split 18 pushes in the run).

| Push the plan chose | Chosen | Tries | Brought the want | Split |
|---|---|---|---|---|
| `Lc1Ld1` (king) | 54 | 59 | 0 | no |
| `Ld1Le2=Re2` (king) | 13 | 14 | 1 | no |
| `Lc1Ld2=Rd2` (king) | 3 | 6 + 10 + ... in its readings | 2 | yes, on `file_Lh_white`, then `file_Lc_open`, then `file_Ld_open` |

- **Rare success isn't seen as conflation.** The meta layer calls a push conflated when an outcome came in some tries and not others, twice or more each way, the rarer side at least a quarter (`Meta.opposed`). `Ld1Le2=Re2` brought the want once in 14: never conflated on it, never split.
- **Where it split, it split on the files.** `Lc1Ld2=Rd2` was split, but the boundary is the tag that best separates any of its opposed changes (`Meta.mode_boundary`), and file pressure changed more than the want. Its two successes sit in the reading `file_Lh_white | file_Lc_open | not file_Ld_open` (2 of 4), a split on files, not on what stood where it landed.
- **Any past success keeps a route in the plan.** The planner values a push in a reading by the share of its tries there that brought the want (`Model.recorded`), and a plan with a value above 0 is acted on before any experiment. `Lc1Ld1` never brought the want itself (0 of 59): it was chosen 54 times for what came after it, `Ld1Le2=Re2` at 1 in 14.

## Rung 2c: the want judged as a conflation (`Params.want_split`, the user's decision), 2026-11-06

**The change, in Gerundelle** (`molecules.py`, behind `Params.want_split`, off by default; the file before it is kept as `molecules.py.before_want_split`). Two rules of the meta layer, for the mind's want only:
1. A push that brought the want in some tries and not others, twice or more each way, is conflated, however rare the want. Before, the rarer side also had to be a quarter of the tries (`Meta.opposed`).
2. When the want is among a conflated push's mixed outcomes, the split separates the want's tries from the rest. Before, the split went to whichever change a tag separated best (`Meta.mode_boundary`), and in seed 5 that was the files.
The planner is unchanged: it already values each half of a split by its own record.

**Set-up.** Rung 2 from RUNG2B, no patience, `want_split` on in every mind of the run (both sides, main and pieces; my choice, as a trait of the minds, not of one side). Both arms, 6 seeds, 600 rounds.

**What the theory says should come out, written before running.**
1. The king's capture in seed 5 is split on a reading about what stands where it lands, not on the files.
2. With piece minds, White is up late more often than in rung 2 (0.05).
3. The gap to the main mind alone narrows, with piece minds rising.

**Results** (6 seeds per arm, `rung2c_logs/`; trace `trace_split_ws.log`).

| White | White up late, median | By seed | Rung 2 (switch off) |
|---|---|---|---|
| Piece minds | 0.05 | 0.19, 0, 0.06, 0.04, 0, 0.05 | 0.05 |
| Main mind alone | 0.21 | 0.25, 0.17, 0.02, 0.12, 0.27, 0.72 | 0.15 |

1. **Missed.** In seed 5 with piece minds the run with the switch on is the same run as with it off, push for push: 468 pushes, the same 18 splits, the king's capture split on the same three files. The files split the move first, before the want had come twice, and that scattered the want's tries over file readings too small to judge: the want came twice only in a reading of 4 tries (2 of 4), and no split came of it (not traced further: most likely no reading separates 2 from 2 by `mode_boundary`'s rule). `Ld1Le2=Re2`, the step the plan leaned on, brought the want once in 14, which no rule can read as a conflation.
2. **Missed.** Piece minds unchanged (0.05).
3. **Missed.** The gap widened: the main mind alone rose (0.15 to 0.21; seed 5 to 0.72).

**Trace of 2c** (`trace_split.py`, seed 5; `trace_split_ws.log`, `trace_split_alone.log`, `trace_split_alone_ws.log`).
- **Piece minds: the files came first.** The king's `Lc1Ld2=Rd2` was split on `file_Lh_white` (t1368) and `file_Lc_open` (t1393) while the want had come at most once, so on the files' changes. The want's two successes then sat in a reading of 6 tries, split (with the switch, on the want) on `file_Ld_open`, leaving them in a half of 4 tries, 2 with the want. There the split rule finds no reading: it needs two tries on each side of a reading, one side 75% one way, the two 0.5 apart, and no reading of those 4 tries does that.
- **Main mind alone: the switch did its job on the rook.** `Rd6Rd4` brought the want 3 times in 18. Off, that's under a quarter, so never conflated, though one reading separated it exactly (`white_rook_Ld3_exerting_pressing`: 3 of 3 against 0 of 15). On, it was split on `white_rook_Ld3_exerting_idle` (t855): 0 of 16 when the rook was idle, 3 of 3 when it was pressing. The capture is now known to work when the rook bears on the knight. In both runs the king's `Lc3Ld4=Rd4` was split on `black_knight_Rd4_captured` (0 of 7 when the knight was already gone, 23 of 23 / 33 of 33 otherwise). Wants met: 29 off, 39 on. Which split made the difference isn't separated here.

**Rung 4's first launch crashed** (35 of 39 runs; logs in `rung4_logs/v1_crashed/`). The engine's castling bug, reported in rung 1: Black's king made its 2-square jump e1-g1 with no castling rights, and `push` castled anyway, moving the h1 rook onto f1 and destroying Black's own bishop there. My identity tracking (`warpworld.play`) didn't follow a piece onto a square its own side had held, and lost the rook's name. Fixed in my tracking (a piece of the mover's colour that appears on any square whose piece changed is followed). **The engine fixed at the user's word** (2026-11-06): `WarpBoard._is_castle`, used by `_is_legal_after` and `push`: a king's 2-square move from e1 is castling only with the wing's right, the rook on the corner and the squares between empty, as `_gen_castling` asks; otherwise it's the jump and no rook moves. The engine before the fix is kept as `board.py.before_castling_fix`. Checked: the rung 4 position now leaves the bishop on f1 and the rook on h1; real castling still moves the rook; the engine's tests (run through a `warp1` alias) give the same results before and after (one cross-board pin test fails in both). The Rust board (`rust_board/src/board.rs`) has the same check and is unchanged. Relaunched.

## Rung 1g: the tournament at each imagined level (`Params.imagined_tournament`, the user's design), 2026-11-06

**Why.** Rung 4 ran slowly, and the trace showed why: the planner (`mcts`) searched every move the model allowed at each imagined step, each once before any was favoured, up to 2,500 at a step in a full game, most from other positions. The tournament entered only as a prior at the first step. The user: the planner is supposed to use the thought molecule tournament at each imagined level.

**The change, in Gerundelle** (off by default; `molecules.py.before_imagined_tournament`, `sov_agent.py.before_imagined_tournament` kept).
- `Mind.imagined_winners(pool)`: the tournament's levels (bids, slots) on a throwaway pool; nothing formed, learned or funded (the firewall).
- `Model.actions`: at an imagined step, the pool is the mind's as it stands (its want, questions, what it attends to; the user chose this over a fresh pool), the moves on offer now taken out and the moves that fit the imagined position put in. Only top-level winners are considered there. The first step is unchanged (the moves on offer, the real tournament's winners as prior).
- `Model.candidates` holds the old rule; `offers.OfferedModel` now narrows candidates (offer memory) before the tournament.
- First version (void): `imagined_winners` was a trimmed copy of `think()`'s levels, filling only the thoughts' track and breaking ties by name. I gave no reason for either because there was none, and the user stopped it ("don't make shortcuts again without a reason"). Its run is kept in `rung1g_logs/v1_shortcuts/` and tests nothing: main mind alone late 0.14 to 0.06, piece minds 0.46 to 0.05.
- Now: the level loop is taken out of `think()` into `Mind.levels_of`, which `think()` and `Mind.imagined_winners` both run, so they are the same tournament: every track, the same order of bids. The tournament reads two things of the present situation, and the imagined one is given both: the pool (each imagined move entered as the half of its splits the imagined facts select, as `perceive()` enters the half the present selects) and what is perceived (the imagined moves, for the imagined lane). A move not already in the pool enters at 1.0, as an offer does without a potential force, because potential forces are read off the board and an imagined position has none. `Meta.reread` isn't run, because it picks halves by the present facts.
Checked off: rung 1f seeds 0, 2 and 3 (and piece minds seed 3) reproduce their earlier results exactly, before and after the refactor of `think()`.
- Second version, stopped before it finished (`rung1g_logs/v2_search/`): the tournament chose the moves at each imagined step, but `mcts` still ran 500 simulations over them. The user: why more than one simulation at all? The model is deterministic and attention now picks the moves, so there is nothing to sample. **Now** (`sov_agent.imagined_lines`): planning is a train of thought. Each move on offer that won the top level of this slice's tournament is imagined forward; at each imagined position each move that wins the tournament there is imagined in turn (the user: "each winner"), to the horizon (3). A line is worth what `mcts` would sum along it; the plan is the first move of the line worth most, acted on if worth more than 0. No move on offer at the top level: no plan this slice. At most 1 + 4 + 16 tournaments per slice (4 top slots), against 500 simulations. Checked off again: seed 2 reproduces.

**What the theory says should come out, written before running** (rung 1f's arms, 6 seeds, 1000 ticks, the switch on in every mind).
1. Each plan is faster: at most 21 tournaments instead of 500 simulations.
2. The two-move crossing is found as often as without (5/6 per arm), since the first step is unchanged and the second is now chosen by attention.
3. More seeds settle: the planner reaches past the first step.

**Results (train of thought; `rung1g_logs/`).**

| Arm | Found (off -> on) | Winning share late by seed, off | on |
|---|---|---|---|
| Main mind alone | 5/6 -> 5/6 | 0.50, 0.50, 0.22, 0.05, 0, 0.05 | 0.01, 0.06, 0.15, 0.03, 0, 0.03 |
| Piece minds | 5/6 -> 5/6 | 0.50, 0.50, 0.43, 0.49, 0, 0.11 | 0, 0, 0.01, 0.40, 0, 0 |

Wall time, same seeds under the same load (main mind alone): seed 2 108 s off, 162 s on; seed 3 123 s off, 187 s on.
1. **Missed.** About 1.5 times slower.
2. **Held.** Every seed first wins at the same try as before: those first wins come from experiments.
3. **Missed.** Almost nothing settles. Seed 0 finds the capture on its second try either way; off it wins every episode after, on it wins 7 in 227 tries. Not yet traced.

**Trace of 3** (`trace_tops.py`, seed 0, main mind alone). On every slice where a move that had brought the want was on offer (30 with the switch on, 148 off), that move had no bid at level 0: it wasn't in the pool. It was perceived, and `Mind.present` didn't let it in, because its box was settled: "a finished thought, perceived again: it stays in storage until something needs or questions it" (`molecules.py`, `present`). The king's `Rc3Rd4`, which brought the want at seed 0's second try, was settled from t4 on. Off, this didn't matter to planning: `mcts` started from every move on offer, pool or not. On, the planner starts from the moves that win the top level, and a settled move can't. So the mind's one way to the want is never imagined. (Same mechanism as the Nim freeze: settled boxes.)

**`Params.want_site` (the user's decision, 2026-11-06; in Gerundelle, off by default; `*.before_want_site` kept).** The want had no open site because `perceive()` built it as `clause(goal, tags=("goal",))`; no reason is recorded. A want is an open question, what brings it about, so with the switch it is held with an open site `causes:<want>`; a move carries `causes:<change>` tags for the changes its funded relations say it causes (provenance decides: lived and worked count, told at credulity, imagined never, so a tag carries nothing unfunded); and a settled thought perceived again comes back when it fills an open site in the pool (`Mind.present`, `needed_now`: Gerundelle's own "until something needs it"). A split half keeps the perceived move's `causes:` tags, because it is the same move read in a situation. Checked off: seed 2 reproduces.

**Mechanism check before predicting** (`trace_tops.py --want-site`, seed 0, 200 slices): the king's `Rc3Rd4` is back in the pool when offered, with the highest bid at level 0 and a top-level win in 9 of the 14 slices it was offered (none before); wants met 10 (2 in 300 slices with `imagined_tournament` alone).

**Rung 1g with both switches; what the check says should come out.**
1. A move that has brought the want wins the top level when it's offered again, so seeds that found the crossing settle on it more than with `imagined_tournament` alone (late medians 0.03 main mind alone, 0.00 piece minds).
2. Time per run doesn't fall: the imagined tournaments are what cost, and this adds none.

**Results, both switches** (`rung1g_logs/`; earlier versions in `v1_shortcuts/`, `v2_search/`, `v3_no_site/`).

| Arm | Found | Winning share late by seed | Median | Off (1f) | `imagined_tournament` alone |
|---|---|---|---|---|---|
| Main mind alone | **6/6** | 0.02, 0, 0.05, 0.01, 0.07, 0.02 | 0.02 | 0.14 | 0.03 |
| Piece minds | **6/6** | 0.24, 0, 0.50, 0.03, 0.05, 0.04 | 0.05 | 0.46 | 0.00 |

Wall time 112-188 s per run, 6 at a time.
1. **Mostly missed.** Piece minds settle a little more than with `imagined_tournament` alone (seed 2 every episode, seed 0 a quarter), the main mind alone no more; both far below the switches off. New: every seed finds the crossing, seed 4 for the first time in any rung, and several on their second try. Seed 0, main mind alone, met the want 10 times in its first 200 slices in the mechanism check and 12 in the whole run (late 0.02): what it found early fades. Not traced.
2. **Held.** No faster.

**Speed: `Understanding.related` remembered across a slice's imagined tournaments** (`molecules.py.before_related_memo` kept). The profile of one run (250 slices, 67 s): 46 s in the tournament's binding (`resolve`), most of it in `related`/`evidence`, 4.5 million calls asking the SOV whether two molecules are related, the same questions in every imagined tournament of a slice. Their answers read only the mind's records and the two molecules, which no imagined tournament changes, so they are computed once per slice and read afresh whenever the slice, the SOV's log or the meta layer moves on. The real tournament doesn't use it. Checked: seed 2, both switches, gives the identical result (248 tries, 22 wants met, late 0.05); 101 s against 118 s (not under identical load).

**Trace of the fade** (`trace_fade.py`, seed 0, main mind alone, both switches). Wants met at slices 3, 25, 33, 53, 57, 63, 113, 135, 163, 175, 504, 634. The king's `Rc3Rd4`, when on offer: in the pool and at the top level 9 of 14 times in slices 0-199, then 0 of 22, 0 of 14, 1 of 8, 0 of 10. Its funding as a cause of the want kept rising (0.7 to 4.2) and its reading brought the want 6 times in 6: never refuted, only left in storage.
- The want lost its open site at slice 23. The capture filled the site (`rec["filled"]`: material_up by `Rc3Rd4`), the want closed into a box and left the pool. Presented again at 24, it was filled again in the same slice, and stayed in the pool with no site. Met at 25, wanted again from 26 (the episode set back), it is the same molecule: `present()` on a molecule already in the pool only raises its activation, so the site never reopens. From then nothing in the pool has a site the capture fills, so it's never needed, and its settled box keeps it out.
- **Fix (the user's decision):** under `want_site`, while the wanted change isn't had, the want's site is open again (`SovAgent.perceive`): wanted again after the change came and went is a new wanting. Kept: `sov_agent.py.before_want_reopen`. Same trace after it: wants met 79 (12 before); the capture in the pool when offered 19 of 20, 8 of 12, 15 of 20, 36 of 38, 66 of 66 by 200-slice window, and met every 6 slices from slice 701 to the end. Traced: (1) from slice 200 the capture is in the pool as a split half, `|file_Lc_open`, and stays: `Mind.settled` skips split halves ("a split record has more to learn"), so it never goes back into storage and needs nothing to come in (it came in by filling a site once in 15 askings, at slice 23). (2) `trace_fade.py` saw no `goal` molecule exactly on the slices the capture was on offer because the capture fills the reopened site then, and a want whose site is filled closes into a box and leaves the pool that slice; between those slices it's there (`material_up`, tagged `goal`).

**Rerun of rung 1g, both switches with the want reopening.** From the check: seeds that find the crossing settle on it (late share near 0.50 where the crossing is found early), above the switches off (0.14 main mind alone, 0.46 piece minds) at the median.

**Results, want reopening** (`rung1g_logs/`; the run before it in `v4_site_closes/`).

| Arm | Found | Late by seed | Median | Before reopening | Switches off |
|---|---|---|---|---|---|
| Main mind alone | 6/6 | 0.40, 0.03, 0.16, 0.01, 0.01, 0.02 | 0.03 | 0.02 | 0.14 |
| Piece minds | 6/6 | 0.01, 0, 0.44, 0.21, 0.01, 0.07 | 0.04 | 0.05 | 0.46 |

**Missed.** Seed 0 alone settled (0.02 to 0.40), as the check on it showed, and so did seed 2 alone (0.05 to 0.16) and piece minds seed 3 (0.03 to 0.21); piece minds seed 0 fell (0.24 to 0.01). The medians didn't move. I predicted the median from one seed's check, which was the mistake. Seeds that find the crossing early and don't settle (main mind alone seed 4, found at try 18, late 0.01; piece minds seed 0, found at try 2, late 0.01) are untraced.

**Trace: two seeds that find the crossing early and don't settle** (`trace_fade.py 4`, `trace_fade.py 0 pieces`; main mind alone seed 4, wants met at 39 ... 441 and then 998 only; piece minds seed 0, met 16 times by slice 223, then once). In both, from about slice 270 the move that brought the want is settled and out of the pool whenever it's offered, and the want isn't in the pool either. Seed 4: the want's own box settled at slice 273 (met at 272, its site filled by `Rc3Rd4`): a thought with no hole that keeps winning precipitates into a settled box (`Mind.settled`), and a settled thought perceived again stays in storage. The reopening (`perceive`) acts only on a want held in the pool, so a settled want is never presented again, never reopens, and nothing needs the capture. The want is still set (`goal` material_up) for the rest of the run.
- **Fix (the user's decision: a held want doesn't settle).** Under `want_site`, `Mind.settled` skips a molecule tagged `goal`, and `perceive` unsettles a want's box settled earlier while the want is set and not had. Kept: `*.before_want_unsettled`.
  Same traces after it: main mind alone seed 4 met the want 26 times (14 before), piece minds seed 0 32 times (17). The want stays in the pool, and the capture is in the pool when offered 7 of 8, 11 of 15, 15 of 17 (seed 4) and 13 of 14 ... 7 of 10 (seed 0), falling to 2 of 6 in seed 0's last 200 slices. Seed 4 meets the want last at slice 746, and from slice 800 the capture is never on offer: the move before it isn't played. Not traced.

**Trace: why seed 4 stops reaching the capture** (`trace_prep.py 4`, the 122 episode starts from slice 600). The mind knows 6 setup moves (moves played just before one that brought the want: the rook to d6 or d7, the king to c3). At an episode's first move all 6 are on offer and in the pool, but they rarely reach the top level. What wins the top level is the rook's capture `Rd6Rd4`, which isn't on offer then (the rook is still on d3): it's in the pool because it fills the want's open site, and its bid is the highest. The first move was chosen by attention in 104 of the 122 starts, and from slice ~800 every time it was `Rd6Rd4`: `winner_acts` tries a move that won the top level even when it isn't on offer, the world pushes back, and the episode's move is spent. The planner started from no setup move (it starts only from moves on offer that won the top level): 2 plans in 122 starts.

**`Params.setup_support` (the user: "if the capture is not on offer, the thought molecule should 'support' the moves that set it up"; in Gerundelle, off by default, needs `want_site`; `*.before_setup_support` kept).** A move in the pool that isn't on offer holds an open site for each condition its funded relations say it holds under (`conditioned_by`: `causes:<condition>`), dropped when it's on offer again (`SovAgent.perceive`); it lends its activation to every competitor filling one of them, through the support term, `w_support x T` (`Mind.support_unsetup`). The setup moves fill them by their `causes:` tags (`want_site`). The SOV had no relation saying a move brings the capture on offer, but the capture's split had funded its conditions (`black_knight_Rd4_bearing_hanging`, `file_Lc_open`).

Trace, seed 4 (`trace_prep.py 4 setup`): the setup moves now reach the top level at episode starts (the rook to d6 at level 2 in most, the king's flip at 1-2), where before they rarely got past level 0. But the capture `Rd6Rd4`, not on offer, still has the highest bid, and attention still acts on it: 200 of 200 first moves, each refused by the world. Wants met 9, last at slice 317 (26 without the switch).
- Then, at the user's word (the intent was that a move not on offer supports, and isn't acted on): under `setup_support`, attention acts only on moves on offer (`SovAgent.winner`). Seed 4: wants met 4 (last at 818). The mind still moves (about 110 moves per 250 slices; the episode-start count in `trace_prep.py` misses most starts and isn't reliable here). On the slices it doesn't move (from 500), the top level holds no move on offer in 238 of 278: of its slots, 1940 are held by moves not on offer, 331 SOV molecules, 278 phases, 278 ownership, 44 moves on offer. Moves not on offer, now holding open sites (their conditions), bid with those sites' tension and fill the top level.
- Then (the user: a move not on offer supports, it doesn't compete): under `setup_support`, a move not on offer with open sites takes no slot at any level and stays among the competitors at every level, so its support reaches the moves that set it up at each (`Mind.levels_of`; `molecules.py.before_support_no_slot` kept). Off, seed 2 reproduces. Seed 4: wants met 87 (4 before this, 26 without `setup_support`), every 4 slices through slices 646-734 and again at the end. Moves not on offer with no funded conditions have no sites and still take slots (858 of the top-level slots on unmoved slices from 500).

**Rung 1g, every switch** (`imagined_tournament`, `want_site` with reopening and no settling of a held want, `setup_support`; `rung1g_logs/`, the run before in `v5_site_reopens/`).

| Arm | Found | Late by seed | Median | Switches off (1f) |
|---|---|---|---|---|
| Main mind alone | 5/6 | 0.06, 0.50, 0.21, 0, 0.29, 0 | 0.14 | 0.14 |
| Piece minds | 4/6 | 0, 0, 0.33, 0, 0.18, 0 | 0 | 0.46 |

Wall time 101-189 s per run, 6 at a time. Not found: main mind alone seed 3, piece minds seeds 1 and 3. Found and not settled: main mind alone seeds 0 and 5, piece minds seeds 0 and 5. Not traced.

**Trace: seeds that no longer find the crossing** (`trace_find.py`, main mind alone seed 3, switches off and on; piece minds seed 1, on).
- Seed 3, every switch on: a move taking the knight was on offer in 207 slices (102 with the switches off) and was never taken. The captures win the top level when first offered (slice 10: `Lc3>Rc3Rd4` and `Lc3Ld4=Rd4` at the top, bid 4.2), but an experiment is acted on first (`SovAgent.tick`: a plan, then an experiment under way or a new one, then attention), and the planner has no line through a move never tried (its recorded reward is 0).
- Then the captures settle without ever having been tried: `Lc3>Rc3Rd4`'s box is settled by slice 51, and from then on it's out of the pool when offered. A settled thought comes back when it fills an open site, and an untried move has no `causes:` tags to fill the want's.
- Piece minds seed 1, the same: four knight captures offered (4 to 19 times each), at the top level 2-3 times each, settled between slices 311 and 592, tried 0 times.
- **Fix (the user's decision): a move never tried doesn't settle** (under `want_site`; a move's `causes` relations are written as lived only when it's tried and watched; `molecules.py.before_untried_unsettled`). Seed 3 then found the crossing at slice 96 and stalled from slice 100: four untried captures not on offer, with no conditions known and so no open sites, kept their slots (only moves with sites gave them up, my restriction, no reason given), held the thoughts' top level, and attention acts only on moves on offer: no move for 900 slices.
- **Fix: under `setup_support` every move not on offer takes no slot** (the user's intent: it supports, it doesn't compete; with no known conditions it supports nothing; `molecules.py.before_all_unoffered_no_slot`). Seed 3 alone: found at slice 39, wants met 241, from slice 200 every move by plan, the same two-move line each episode. Piece minds seed 1: found at 308, wants met 35, plans taking over by the end (98 of the moves in the last 200 slices). Before these two fixes both met the want 0 times.

**Rung 1g, every switch, after the last two fixes** (`rung1g_logs/`; earlier runs kept in `v1`-`v6`). Off check: seed 2 with the switches off reproduces exactly.

| Arm | Found | Late by seed | Median | Switches off (1f) |
|---|---|---|---|---|
| Main mind alone | **6/6** | 0.50, 0.41, 0.50, 0.50, 0.41, 0.50 | **0.50** | 0.14 |
| Piece minds | **6/6** | 0.50, 0.14, 0.50, 0.50, 0.50, 0.50 | **0.50** | 0.46 |

0.50 is every episode won (an episode is two tries, the crossing and the capture). Every seed of both arms finds the crossing, most within 40 tries, and 10 of 12 win every late episode. Piece minds seed 1 found it at try 130 and wins 0.14 late; in its trace above, plans take over only near the end. Wall time 65-237 s per run, 6 at a time.

**Rung 4 launched with rung 1g's switches** (`--switches`: `imagined_tournament`, `want_site`, `setup_support`; the learn room's mind too), 6 runs at a time, each printing its progress every 100 rounds. The stopped second launch (no switches, 39 at once, no progress output) is in `rung4_logs/v2_stopped/`. The expectations written above for rung 4 stand.

## Rung 4: the dream planner (the user, 2026-11-07), design

**The world as teacher** (the user): the world can tell what is possible and what isn't; the mind can manipulate the force structure and still have a valid configuration, see whether the response after interacting is what its SOV and thought molecules expected, and so find the edge of its understanding and improve it there, manipulating further as it goes, rather than searching exhaustively or going move by move from a start. It is a dream planner: it surfaces suggestions, and the mind acts on them to make them lived, as when you wake from a dream.

1. **When:** between games, on the positions the game just went through (the user: "between games").
2. **Manipulation, one force at a time** (the user: "if there are two forces, and one potential force, maybe it adds a potential force"): add a potential force (place a piece where it bears on an occupied square) or take one away (remove a piece that bears on something). Only configurations the world says are valid.
3. **Checking itself:** in the manipulated configuration, for a move, the mind's expectation (its records, `SovAgent.predict`, and the relations carried onto it, `carry.py`) against what the world shows follows. A mismatch, or no expectation, is the edge.
4. **Suggestions:** each edge is kept as a posited structure (SOV's Posit: "seeds the imagination register"); it funds nothing (the firewall).
5. **Waking:** in the next game, where a position holds a suggestion's structure, the suggestion surfaces as an experiment molecule for that move; acted on, its outcome is lived (Fit), confirming or dropping it.

My choices, stated: the dream starts from the game's own positions; which manipulations it tries is where the mind's expectations are weakest.
6. **Dreams make sub-wants possible** (the user: "before, we didn't have sub-wants because a certain move or position wasn't 'experienced' yet. The dreaming would change that through the imagination"). Sub-wants decompose the gap from what the mind knows; a position or move never experienced gave them nothing (the planner found a way 3 times in 181 tries, `trace_planner.py`). A dream's trials go into an imagination register kept apart from what was lived; the planner and the sub-want decomposition read it where they have no lived record (believed at credulity, as the planner already reads imagined outcomes), so a way known only from a dream can give a sub-want. It funds nothing (the firewall); acted on in a game, the way becomes lived.

## Next, after the dream planner: reading games (the user, 2026-11-07)

A Gerundelle mind should be able to read a game record and imagine and have empathy for the situation at each step. Records: `E:/vscode/vitchess/mini_games` (207,347 Warp games from self-play, iterations 10 onward, same format as `warponechess/mini_games`: start position, the line, the final position). At each step: imagine the position (as the dream does), put itself in the mover's shoes before reading the move (what it would play, how the position feels from that side: affect read off that side's territory), compare with the move played (a match confirms its understanding; a difference is evidence of how the player thinks differently), and take what followed as told receipts (SOV's Attest: another's receipts at a discount; funded at credulity, kept as told until lived). Earlier iterations first, later ones as it understands more: the world as teacher choosing what it meets.

**Also built (2026-11-07):** situations remember the sub-wants they co-occur with (the user): a sub-want met co-occurs with the news while it was held, one dropped with not:<that news>; a sub-want's support rises and falls with the news present now (`SovAgent.situations_remember`, `Mind.support_subwants`, under `own_wants`).

## Rung 1h: rung 1g on today's mind (PLAN.md step 1), 2026-11-13

The user, 2026-11-13: "write it up and start step 1". The question: does rung 1g's puzzle still come out as it did, (a) on today's Gerundelle with rung 1g's own switches, and (b) with the shared switch set every other domain runs on (tetris/run.py's SWITCHES, plus affords_relation)? `rung1d.py --potential --offered --imagined --want-site --setup-support [--shared]`, arms control (main mind alone) and pieces, seeds 0-5, 1,000 ticks.

**Expectations, written before running:**
- (a) **Rung 1g's own switches: the same as rung 1g, seed for seed** (6/6 found in both arms; late 0.50, 0.41, 0.50, 0.50, 0.41, 0.50 alone and 0.50, 0.14, 0.50, 0.50, 0.50, 0.50 with piece minds). Since 11-07 every Gerundelle change has been behind a switch rung 1g doesn't turn on, or exact (the core cut, the edge cache). There are two exceptions, which shouldn't reach this rung: causes as a threat (anti-wants are off) and sequence pushes named by full id (commit is off). A difference means one of those reaches it after all, and gets traced.
- (b) **The shared set: still solved (found in at least 5/6 per arm), late median at least 0.41.** I can't predict it seed by seed: the shared set turns on about 40 switches rung 1g never had. Some can't act here, because the Warp world has no `potential_effects` or `push_predictions`, so `force_predictions` and `commit` find nothing to read. Others can:
  - own wants beside the placed want;
  - anti-wants;
  - dormancy;
  - mental energy and rest, which spend ticks;
  - concept abstracts.

  A miss is traced, not tuned.

**Results** (`rung1h_logs/`):

| Arm | Found | Late by seed | Median |
|---|---|---|---|
| (a) main mind alone, rung 1g's switches | 6/6 | 0.50, 0.41, 0.50, 0.50, 0.41, 0.50 | 0.50 |
| (a) piece minds, rung 1g's switches | 6/6 | 0.50, 0.14, 0.50, 0.50, 0.50, 0.50 | 0.50 |
| (b) main mind alone, shared set | 6/6 | 0.21, 0.07, 0.10, 0.10, 0.07, 0.07 | **0.09** |
| (b) piece minds, shared set | 6/6 | 0.09, 0.09, 0.03, 0.23, 0.15, 0.13 | **0.11** |

- **(a) As expected: identical to rung 1g, seed for seed, in both arms.** Nothing since 11-07 reaches this puzzle with its own switches.
- **(b) Missed the expectation** (a late median of at least 0.41). The crossing is found as early (first want at tries 2-62), but met 18-61 times against 93-241, with fewer moves (354-436 tries against 449-499). Being traced: `trace_1h.py`.
- **Found on the way:** Gerundelle's force predictions kept their "what each push leads to" as `situational`, the name warpchess's piece minds already used for a flag, and the piece-mind arm crashed with the shared set. Renamed `push_leads` in `sov_agent.py` (backup `.before_push_leads`); two tetris trace scripts updated.

## Rung 1i: the opponent's plans as territory (PLAN.md step 2), 2026-11-13

Rung 1h's (b) arm, with the new territory: `plansworld.PlansWorld`. The opponent's one-move plans (a gain of a piece, a square or an outpost) are objects, held while the mind can stop them, lost when they become unstoppable. Pieces and files are unclaimable. Go's territory switches are on as well (`go/run.py` GO_SWITCHES). `rung1d.py --potential --offered --imagined --want-site --setup-support --shared --plans`, both arms, seeds 0-5.

**Expectations, written before running:**
- **The crossing found as before** (6/6 per arm): the placed want and its way are unchanged.
- **The mind's own wants point at the opponent's plans.** The sub-wants it sets are about plan objects (a plan stoppable again), not files or its own pieces, since those are no longer claimable. No want for a loss of its own (`no_loss_means`, `held_state_wants`).
- **The late score:** I don't predict a number. If own wants still take the mind away from the placed want, the late median stays low as in rung 1h. That would say a placed puzzle is the wrong test for a mind with territory, not that the territory is wrong. Traced either way.
- **Cost:** slower per slice than rung 1h by the plan reading (about 1-1.5 s per new position, memoized).

**Results** (`rung1i_logs/`; trace `trace_1h.py 2 1000 --plans`, `trace_1i_s2.log`):

| Arm | Found | Late by seed | Median |
|---|---|---|---|
| main mind alone | 6/6 | 0.14, 0.03, 0.03, 0.09, 0.09, 0.04 | 0.06 |
| piece minds | 6/6 | 0.07, 0.02, 0.00, 0.00, 0.01, 0.04 | 0.03 |

- **As expected: the crossing found every seed.**
- **As expected: the mind's own wants are about the opponent's plans.** Seed 2: 116 plan wants set and 83 met (`plan_square_Lf3_stoppable` 249 ticks, `plan_outpost_Ld1_stoppable`, `plan_piece_Ld1_stoppable`, ...). Every plan want asks for a plan to be stoppable, so no want for a loss of its own. Files appear only inside whole wants as means (`affords_chain`'s needs).
- **The late score is low, for the reason expected:** the placed want was the goal 157 of 1,000 ticks. The rest went to the mind's territory, with the anti-want `held_unstoppable` held 996 ticks. A placed puzzle measures how often a mind with territory sets it aside, so it is no longer the yardstick. Full games are.
- **The tool's trigger arises:** questions about plans stand in the pool (`q:caused_by:plan_piece_Ld1_stoppable`, `q:caused_by:plan_outpost_Ld1_stoppable`), "what causes this plan to be stoppable?", which the tool answers.

## Rung 4p: games from the start with the plans territory, the tool, commit and dreams (2026-11-13 to 2026-11-14)

Full account: `PLAN.md`, steps 2-4 and "Games from the start, the same mind throughout".
- **The mind:** plays White from the rulebook's start against random Black (`rung4p.py --start`).
- **Its territory:** the opponent's plans (`plansgame.py`), with no placed want.
- **The tool, commit and dreams:**
  - it asks the tool about plans and two-move lines;
  - it commits to predicted gains;
  - it dreams at once when stuck on something no longer on offer (10 trials).
- **Games:** each ends at 50 half-moves or at the mind's Nth dream slice in that game. A checkpoint is saved after each.

**Results (seed 0):**
- **Games 1-19:** the same lifelong mind. White's balance by game: +1, -3, 0, +4, +2, 0, +2, 0, 0, 0, 0, +2, +3, +2, 0, +1, 0, +3, **+33**.
- **From game 8 on:** no game ended behind, and every commit came (19 of 19).
- **Wants for its own loss:** none, but for one untraced flag.
- **Game 19** (14-dream stop, 40 half-moves, 17 dreams) set the record at +33.
