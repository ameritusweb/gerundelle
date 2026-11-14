# Tetris force world

Started 2026-11-09. The world is built (`world.py`); no mind is connected to it yet. This file keeps the user's decisions apart from what is only proposed or still open.

## Decided (the user)

- **A tetris force world:** a Gerundelle mind plays a falling-piece game in which it can move and rotate the falling tetromino.
- **The empty space is a form of territory.**
- **The mind perceives the whole well,** not just the cells near the piece.

## Carried from the other domains (settled principles, not new decisions)

These come from the mystery maze and Warp chess (see `mysterymaze/`, `warpchess/`, and the force-world memory):

- **Grounded in forces.** Everything perceived is a doing (a gerund), never a state label. Pushes are potential forces read from what they reach. No finite state machine.
- **Legal-only offers,** as Warp chess offers only legal moves: a push is offered only where the world allows it.
- **Principle 0** (`civilization/PHYSICS.md`): in a push's slice only the thing pushed changes; what follows lands in later slices.
- **The mind notices changes itself:** what it perceives now against what it last perceived. The world reports no list of changes (news).
- **Wants come from the ownership slots,** with no goal placed (Warp chess's `own_wants`; REORG step 4).
- **Affordance is enable** (form 14 of `relations/RELATION_TYPES.md`): what holds whenever a push is on offer, kept per way in.
- **Temperament is range:** for example `acceptance`, how long a question is pursued before it is let go.

## Proposed (mine, for the user to confirm or change)

**Objects and their doings**

| Object | Doings |
|---|---|
| each cell of the well | `bearing` (a settled block on it), `free` (empty), `pressed` (the piece landing on it) |
| the falling piece (a whole of four parts, the part/whole form) | `falling` (gravity unopposed), `resting` (cells bear it) |
| each row (a whole made of its cells) | `coming apart` when every cell bears: the row clears and what is above it falls |
| gravity | the world's own push every slice; not the mind's doing |

**Potential forces**

- Shift left, shift right, rotate and drop are pushes on the piece, offered only where the cells the piece would occupy are free.
- Each push's force is read from what it reaches: the cells it would make the piece come to rest on. A push that would complete a row reaches every cell of that row; one that would seal a free cell under blocks reaches the cell it takes away.

**Territory**

- A free cell the mind can still reach from above is its own: it can place into it.
- A free cell covered over is lost: a hole it can no longer reach.
- The stack rising shrinks its territory; topping out is losing all of it.
- Clearing a row takes territory back (the joy of a slot closed by a claim).
- So the wants arise from the slots: a lost cell is a want to get it back, a nearly full row a want to complete it.

**From the maze**

- Affords chains: a free column below enables a drop there; a rotation enables a shift into a gap. A way's needs are wanted whole ("rotated and over the gap", then drop).
- Dreams between games manipulate one force at a time (add a block, free a cell) to find where the mind's understanding is thin.

**Whole-well perception, consequences**

- Every cell is perceived every slice: about 200 cell objects in a 10 x 20 well.
- The territory register holds the whole space, so it can tell a reachable free cell from one sealed under the stack.
- The cost is attention, not perception: the tournament has to find the few cells that matter (the piece, the surface of the stack, rows nearly full). The world shouldn't filter what the mind sees.

## Open questions

- The size of the well, and which piece shapes.
- Where a new piece enters, and whether the mind sees the next piece.
- How fast gravity acts relative to the mind's pushes (one row per slice, or slower).
- What a game is: does the well reset on topping out, and is that the unexplained event the mind has to let go of or explain?
- Whether reachability of a free cell is perceived directly or worked out by the mind from the forces.

## Built (2026-11-09): the world, `world.py`

The user: "build the 'tetris force world' part, keeping with the no finite state machine rule".

- **No state machine:** the world changes only when a quantity crosses a reserve (PHYSICS.md, principle 1).
  - gravity: the piece's weight against the reserve of the cells under it (a free cell has none; a block, the floor, a wall can't be crossed);
  - the mind's pushes: a push's force against the reserves of the cells the piece would enter;
  - rows: a row's load (its bearing cells) against its capacity (just under the well's width).
- **Principle 0:** in the mind's push's slice only the piece moves; resting, settling, a row coming apart, rows falling and a new piece forming land in later slices.
- **Perceived, the whole well, all doings:** each cell `free`, `bearing`, `carrying` or `pressed`; each row `free`, `holding` or `coming_apart`; the piece `falling`, `resting` or `forming`. 221 objects in a 10 x 20 well.
- **Pushes:** shift left, shift right, rotate, drop, offered only when legal. `potentials()` reads each push's force from what it reaches (3 if the piece would rest there and complete a row, 2 if it would rest there, 1 otherwise); `reaches()` names the cells it would enter.
- **Interface:** the one the minds read in the maze (`objs`, `states()`, `invitations()`, `act()`, `diffs`, `renew()`, `still`, `gamma`, `horizon`).
- **Checked:** random legal pushes play games of 16 to 25 pieces until the well fills; a row with one gap, completed by a dropped piece, comes apart, and the rows above fall one row as a whole.
- **My choices where the questions above are open:** a 10 x 20 well; the seven shapes in a seeded order; a new piece at the top centre; the next piece not shown; gravity every 2 slices, in slices without a push; topping out ends the game and the well is set back empty.

## Blocks (2026-11-09)

The user: break each piece into individual blocks with a force holding them together, so a full row can be perceived; the cells stay as the space; a block reads each side, and spanning when both are pressed.

- Each block is an object (`block_<n>`): `falling` (in the falling piece), `resting` (settled), `spanning` (settled, pressed on both sides).
- Its sides (`block_<n>_left`, `block_<n>_right`): `pressed` (a settled block or the wall against it) or `free`. Its bond (`block_<n>_bond`): `binding` (held to a block of its piece) or `parted`.
- A piece's blocks are bound by cohesion: a push or gravity carries all four through their bonds, or none. When a row comes apart its blocks leave the well and every bond reaching into it tears; the rows above fall a row.
- So a full row is perceived block by block: every block in it `spanning`, wall to wall; a nearly full row shows a block with a `free` side at the gap.
- Checked: a row with one gap reads its edge block `resting` with its right side `free`; a dropped piece's block arriving beside it turns that side `pressed` and the block `spanning`; the row comes apart, clears, and a new piece of four new blocks forms. Random play runs games to the top without errors.
- A side is `pressed` only by a settled block or the wall (the user: only once it's settled); a falling block passing by presses nothing.

## The mind connected (2026-11-09)

- **`run.py`:** the mystery maze's mind (SovAgent with ForceMind, every switch the user decided on, `acceptance` 6), no goal placed: wants form through ownership (the user). The dream is off: which forces a tetris dream manipulates isn't decided.
- **Gravity is a force like any other** (the user): no category of its own; what it does is perceived as anything the forces do.
- **Horizon 4** (was 2): a push that brings the piece to rest where it completes a row sees the row come apart inside its watch (gravity finds the piece borne 1 or 2 slices later, it settles and the row comes apart the slice after). A random-play measurement first suggested no horizon would do; that came from a 4-wide test well (pieces boxed in, rows completed by pieces never pushed), not this one.
- **Cleared blocks leave the world's objects** (`forget`), and the well's blocks when it is set back.
- **The alignment gerund** (the user: "a gerund for 'aligning' that flips when a piece would eventually clear a row; like we had for decreasing in the mysterymaze"): `piece_alignment` reads `aligning` when the piece, falling straight down from where it is, would come to rest completing a row, `straying` otherwise (my word). It follows a push in the next slice (Principle 0). Why: the potential forces read only one push ahead, so in random play force 3 (completes a row) was on offer 9 times in 20,000 slices.
- **Luck, on a dial** (the user: "randomly initially placing a tetrimino in the optimal place like 'luck', on a dial until it starts learning"): `luck` (0-1, `run.py --luck`) is the chance a new piece forms in the column and rotation from which falling straight down lands it best. Best (my reading): completing the most rows; where none would, covering no free cell and filling the fullest rows most. Its own random source, so the shapes' order is the same at any luck. With no pushes at all: luck 0, no rows (about 11 pieces a game); 0.5, 29 rows in 20,000 slices; 1, 257.
- **Luck 0.5, the mind** (2,000 slices): no rows; of 23 lucky pieces in the first 1,000 slices the mind pushed 16 elsewhere, and the fullest row reached 9 of 10.
- **Luck 0.7, and no potential force for a piece in an optimal position** (the user: "remove any potential force from a piece that is already in an optimal position, no matter whether the mind put it there or if it was just luck"): `optimal()`, the piece's straight-down landing as good as any it could have from the height it is at (the same worth luck uses); then nothing is on offer and gravity carries it in. Random pushes, 20,000 slices: luck 0, 5 rows; luck 0.7, 76 rows.
- **The SOV trace** (600 slices, `trace_sov.py`): the gerund read `straying` every slice (the fullest row held 6 of 10 blocks); all four pushes were closed in all five slots by slice 119 (caused_by by being offered; causes and co_occurs by one try, each moving several cells at full weight; conditions by the first split on one cell; role by one worked role), and the mind had no open questions.
- **Proposed, not decided:** free cells as given territory (the empty space is the mind's), a cell a settled block fills read as lost, so a lost cell's want is to be free again and a row coming apart is the only way back.
- **First run** (seed 0, before the gerund): three games of 12-13 pieces, no rows; the wants set were nearly all cells the falling piece passes through (`cell_2_17_carrying`).

## Runs clear pieces (2026-11-10)

The user: "If there is a row of at least 4, with at least two blocks of one tetrimino and two blocks of another tetrimino, then that 'clears' both pieces"; the whole pieces clear, the blocks above fall, full rows still clear, and the space a cleared piece leaves is the mind's for good.

- **As a force:** a run is blocks side by side in a row, each pressing the next; its load crosses its reserve (`RUN_RESERVE`, just under 4) when it holds at least 4. Its pieces with at least two blocks in it come apart, if there are at least two such pieces; their blocks read `coming_apart`, and the next slice every block of those pieces leaves the well.
- **Blocks above fall:** groups of settled blocks bound by their bonds, none resting on the floor or on a held block, are `falling` and drop a row each time gravity acts, until all are held; then rows and runs are read again (a cascade), and only then does a new piece form.
- **Everywhere a row counted, a run counts too:** the alignment gerund, the potential forces (3: completes a row or a run), luck's "optimal place", and the force predictions (`run+<k>_coming_apart`, the run's blocks pressing one another, named as the piece's parts, `run+<k>:other` for the other pieces' blocks, `run+<k>:settled`).
- **Territory:** when a block comes apart within the watch of the mind's push, the cells its piece leaves join the given territory (`run.py`), as a cleared row does.
- **Checked** (12,000 slices): luck 0.7 with no pushes, 16 rows and 312 pieces cleared, the well never filled, 184 predictions (168 runs, 16 rows) all confirmed; luck 0 with random pushes, 3 rows and 14 pieces cleared over 5 games.

## Territory, optimal places and blame (2026-11-11, evening)

The user's decisions, from watching the 18,000 checkpoint in `watch_mind.py`:

- **Territory:** empty rows are held while empty and lost when the stack reaches them (`run.own_open_rows`); a cleared row and a cleared block are the mind's for good, held in view or not ("cleared blocks and rows ARE TERRITORY", as a capture in warpchess; `run.own_clears`, from `world.cleared_log`). Blocks still in the well and cells are no one's to claim (`TetrisWorld.unclaimable`, read by Gerundelle: no claims, no regions, no root wants about them). First every cell a push moved the piece into was claimed, the tower was the mind's territory, and it stacked.
- **The optimal placement is next to a piece, not on top of one:** a landing's worth is the rows and runs it completes, then how many of its blocks' sides press against another piece's blocks (walls don't count). My earlier reading (fewest cells covered, then fullest rows) made a flat tower top optimal.
- **At luck 0 pushes are always on offer:** the optimal-position rule applies only while luck is above 0.
- **Anti-wants:** a push threatens what was lost only if the SOV says it prevents it (a push that causes it is the way back); a prediction is blamed only on the push after which the forces stopped predicting it (first every push made in between was blamed, every push came to carry `prevents`, and a lost prediction's anti-want pushed down the clearing pushes). `repair_blame.py` takes the old blame out of a checkpoint (`decisions_18000_repaired.pkl`).
- **Viewer:** `watch_mind.py` opens with the well set back and that game forgotten (`amnesia`, the viewer's, not the mind's); `--as-saved` shows the checkpoint as it was. It names an anti-want as the loss it is.

## Predicting after pushes, and wanting owned predictions (2026-11-12)

- **Prediction after a push** (the user: "you use a force to rotate it, you then predict the new force configuration"): `potential_effects(pushes)` follows the forces after a sequence of pushes made a watch apart; `push_predictions()` tries every count of rotations then every shift the piece can make, and runs the forces only for those landing where they would clear. Followed exactly, 60 one-push and 60 sequence predictions all came true.
- **The pushes carry what the forces predict from here:** a push on offer is tagged `causes:potential:<effect>` only from this slice's predictions (not from what it was once told), refreshed every slice on the molecules already in the pool.
- **Wanting an owned prediction** (the user: "a correct prediction is ownership"): an owned prediction offers its potential effect as a candidate want while none of it stands and some push on offer leads there; held, it pulls the push the forces say leads there; met when a prediction of it stands again. From `clean_3000`: 3 of 6 clears in reach made (1 of 5 before), luck 0.66 -> 0.52 in 600 slices.
- **Only standing predictions reach Abstract:** a prediction SOV's forces are written into the register only once it stands (the push was made, or it is what falling does); the hypothetical ones only tag pushes (the user: "only when the prediction stands"). Writing every hypothetical one made Abstract's pairwise search grow until a slice took minutes.
- **One luck step per clear:** a clear the mind made earns one step, however many of its predictions of it came true (first a row and a run predicted for one clear earned two).
- **Speed, exact** (bench_from.py signatures unchanged): the funding index kept on through `analogize`; one index of the perception log for the planner's `states_of`; a shape check before each exclusion embedding in `shared()`; each structure's candidate patterns ranked once per `analogize`.
