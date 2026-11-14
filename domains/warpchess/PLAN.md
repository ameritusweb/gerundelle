# Improving Warp chess with what Go and tetris taught (plan, 2026-11-13)

The user, 2026-11-13: "can we take what we have learned, to propose a plan to improve warpchess?", then "write it up and start step 1".

Warp chess was last worked on 2026-11-07. Everything below was learned in Go (`go/README.md`) and tetris (`tetris/README.md`, `tetris/CLEAN5_WANTS_REPORT.md`) since. The Gerundelle record is `analogy/DRIFT.md`.

## Where Warp chess stands (from `LADDER.md` and the code)

- **Puzzles:** rung 1g solves them, 6/6 in both arms. Its three switches are `imagined_tournament`, `want_site` and `setup_support`.
- **Full games:** rung 4 (`rung4.py`, `gameworld.py`) is set up with those switches and `--own`.
- **The dream planner** (`dream.py`) is designed and partly built.
- **Territory** (`rung4.py --own`) is "White's pieces are given, captures are the mind's". That is the mapping Go started with and had to replace: the mind valued its stones, not what they shape (go/README.md, "Territory as White's dead opportunity forces").
- **Not used yet:**
  - from tetris and Go: force predictions and potential effects, prediction SOVs, commit, anti-wants, predicted losses, unclaimable and read-held regions;
  - the shared switch set (`tetris/run.py SWITCHES`).
- **Two-mind play:** `duel.py` exists, but there is no Elo, no temperament league and no checkpointed lifelong minds.
- **Game records:** the 207,347 records in `E:/vscode/vitchess/mini_games` are unused.

## The steps (each checked before the next)

1. **Catch up with the shared mind.**
   - Run Warp chess on the shared switch set (the user's rule: every user-decided switch on), with today's speed work (the exact `core()` cut and edge cache, which need nothing; `affords_relation` where `affords_chain` is on).
   - First its tests (`test_warpchess.py`) and rung 1g's puzzles, to see what changes.
   - Trace what breaks before changing anything.
2. **Map ownership to the game** (the user's decision).
   - Go's answer, carried over: territory is where the opponent's opportunity forces are dead. In chess, **the squares where an opponent piece couldn't land without being taken for nothing**, read by the board's physics one reply forward, as Go's `hanging` is.
   - Material is then what shapes territory, not territory itself.
   - I propose readings; the user decides.
3. **Gains and losses as potential effects.**
   - The world follows each move's forces forward and reports, relative to the piece:
     - gains: squares killed, captures;
     - losses: own pieces left hanging, controlled squares freed.
   - Go's machinery then applies as built: prediction SOVs, wants, `predicted_losses` and anti-wants, `no_loss_means`, `held_state_wants`, `read_held`.
   - Every predicted change gets a check with no mind, as `go/check_opportunity.py` did.
4. **Commit through forced replies** (the user's note, 2026-11-12, in `DRIFT.md` under Commit).
   - The world follows a line through the opponent's reply and says when it is the only legal one, so a forcing sequence can be committed to and owned.
   - A reply that is expected but not forced is where a commitment dissolves.
5. **Duel, league, evolution.**
   - `duel.py` brought onto Go's pattern (`go/goduel.py`): seats, lockstep checks, lifelong checkpointed minds.
   - Then `league.py`, `watch_league.py` and `evo_make.py`, with temperament profiles.
   - One lesson to test: in Go, patience lost games because a turn passes while a patient mind waits (`SovAgent.winner`). Warp chess's turn rules decide whether that holds here.
6. **Study from real games** (`go/STUDY_MODE.md`; the user: replaying a game on a real board is lived).
   - The self-play records become positions to study between league games.
   - It needs steps 2-3 first, to know what each position meant to the mind.
7. **Speed, measured first.**
   - Before optimizing anything, find where a Warp chess slice goes.
   - Today it was Abstract in Go (80% of a slice) but not in tetris (about 15%).

## Decisions for the user

- The territory mapping (step 2).
- Whether reading game records as study counts as lived (step 6).
- The order. My recommendation: steps 1-3 before any league, since Go's league only meant anything once the mind kept its territory.

## Step 1 (started 2026-11-13)

Results are recorded in `LADDER.md` as a rung, with expectations written before running.

## Step 1 result (rung 1h, LADDER.md)

- **Rung 1g's own switches on today's Gerundelle: identical, seed for seed.**
- **The shared set: still solved (6/6), but late medians fell to 0.09 and 0.11.**
- **Why** (`trace_1h.py`): `own_wants` stacked the mind's own sub-wants (file states, piece states, some of them its own losses such as `white_rook_Ld3_bearing_hanging`) above the placed want for 787 of 1,000 ticks. Experiments drained its energy.
- **What it means:** the shared set needs Warp chess's territory to mean something. That is step 2.

## Step 2: territory is thwarting the opponent's plans (the user, 2026-11-13)

The user: "I think it's being able to 'thwart' the hypothetical plans of the opponent"; "a plan is a gain of a piece, a square, or an outpost".

**Decided (the user):**
- **A piece gained:** a capture of the mind's piece.
- **A square gained:** "a safe landing or more pressure than the opponent has on it". One of their pieces can land on the square and not be taken at once, or they press the square more than the mind does (`WarpWorld.pressure`).
- **An outpost:** both kinds count:
  - a safe landing where the landed piece is also defended by another of theirs;
  - a safe landing no piece of the mind's could attack.
- **Depth:** "one or two". Plans one or two of the opponent's moves away.

**What it is in Gerundelle's terms:** Go's mapping one level up. In Go the mind holds a point while the opponent's chance there is dead. Here the mind holds the opponent's plans while it can kill them.

**My readings, for the user to change:**
- **What "able to thwart" means:** the mind has a move now after which the forces no longer show that gain. For a two-move plan, no longer along that sequence of the opponent's two moves (the mind's reply between them isn't read; that is what a plan is from the opponent's side).
- **"Could attack" in the second kind of outpost:** at one move of the mind's.
- **How plans are named:** by kind and square (`plan_piece_<square>`, `plan_square_<square>`, `plan_outpost_<square>`), as Go's opportunities are by point. The world reports their changes as potential effects relative to the moved piece, for step 3.
- **Objects:** pieces and files stop being territory (unclaimable). Plans are held by reading only (`read_held`).

**Still open (asked):** whether a plan the opponent can't make at all counts as held, like Go's dead points, or only one it could make that the mind can stop.

## Tool use (the user, 2026-11-13)

The user: "use 'tool use'. Meaning, the mind comes up with an unknown, like 'can anything thwart my plan or prediction for some potential effect', through the tournament; if it chooses an experiment, it then uses tool use, which runs mcts with alpha beta pruning and tables and heuristics to get an answer to a question; so the mind decides whether to invoke tool use or not based on experience".

**Decided (the user):**
- **A tool's answer is told** ("told of course"): funded at credulity, as self-talk is, until the world answers.
- **Which questions:** about plans and potential effects only (can this plan be thwarted? will this potential effect come?).
- **Where the heuristics live:** inside the tool, not in the mind. The answer comes back as an answer, never a recommendation (DRIFT.md rule 10, no designer reward).

**How it fits (my reading):**
- **The question:** an unknown about a plan or a potential effect poses a question (`q:`), and inquiry offers its experiments. Calling the tool is one of those experiments, and it competes in the tournament like any other.
- **Learning when to call it:** the mind's record of each call (what it asked, the answer, what it cost, and whether the world later bore the answer out) funds the tool experiment. That is how commit earns trust. A tool whose answers keep holding for a kind of question becomes worth calling for it.
- **The search:** MCTS or alpha-beta over the real rules (WarpBoard), with tables and heuristics, outside the mind.
- **How it fits step 2:** the deep reading (two-move plans, can the mind thwart this) moves from every slice into the tool, run when the mind asks. The cheap reading (one-move plans) stays as perception.

**What a call costs (the user: "it just costs time of course"):** slices. The mind waits for the answer, and in play its turn runs on while it does.

## Step 2, checked (`plans.py`, `check_plans.py`, 2026-11-13)

- **Exact:** on 4 positions (the two rooms, and one position after random play from each), the plans read were exactly those of a full search: 75-98 per position. Every one-move plan is made by the move it names. Every thwarting move named removes its plan, and where none was named, none exists.
- **Cost:** the read takes 8.5-15 s a position (a full search took 50-97 s). Finding which plans the mind can thwart adds 19-43 s. That is too slow for every slice, so the deep reading goes into the tool (above), and one-move plans stay as perception.
- **Which squares matter:** squares are most of the plans (59 of 77 at the first position). The user: "the mind should learn which squares matter over time, structurally, via SOVs for the force structure, based on experience". The world reports every plan, with its force structure relative to the pieces involved (what presses what), as tetris's and Go's predictions do. Each structure has its prediction SOV, and what followed each plan funds it. No square is filtered out by rule.
- **Then, the user:** "these should be 'told' heuristics that get learned, that the mind is able to scrutinize through thoughts as it goes".
  - Which squares and force structures matter starts as told relations, funded at credulity.
  - The mind can question them like any told link: they pose questions, inquiry can test them, and the tool can be asked about them.
  - Experience settles them. A heuristic the world bears out gains lived receipts; one it contradicts has its told receipt taken back (belied), as a rejected prediction's is.
  - Where the heuristics come from: asked, below.
- **Then, the user (where the heuristics come from):** "kind of like how we have the MOU decision tree, it's which force structures were deemed most important in decisions". The mind's most-often-used decision tree (`Params.decision_paths`, `SovAgent.record_decision`) already traces each decision back to its winning thought, the bonds at each level and the SOV relations behind them. It counts each node and marks failed paths (`tree["failed"]`, when a broken prediction is blamed on a push). `Params.meta_targets` already raises what it says was relevant (`meta:relevant`).
  - **What is new:** plans report their relative force structure, each structure has a prediction SOV, and the tree counts the structures decisions rested on.
  - **The told heuristics:** the most-used structures are told back to the mind as mattering (credulity), scrutinized like any told link. Failed paths count against them, and experience confirms them (lived) or belies them.
  - Harvested from the mind's own decisions, nothing authored.

## The tool, built and checked (`tool.py`, `check_tool.py`, 2026-11-13)

- **What it answers:** "can the mind thwart this plan?" and "is this a plan of theirs?".
- **How:** an AND-OR search over the real rules through `plans.py`, with cut-offs. The table (positions, pressures, answers) is kept across calls. Its move ordering, the plan's square first, stays inside the tool.
- **What it costs:** positions searched, 2,000 a slice (my number).
- **Checked:** 32 questions on 4 positions with no problems. Every named move stops its plan, every "nothing stops it" was confirmed by a full search, and a repeated question is answered from the table in 1 slice.
- **Cost seen:** most calls 50-900 positions, under 0.5 s, 1 slice. Some 2,700-10,000 positions, 1-6 s, 2-6 slices. The worst 24,587 positions, 19 s, 13 slices.

**The mind's side (proposed, not built; behind a Gerundelle switch, off by default):**
- **When it's on offer:** when a question about an opponent plan is up (a `q:` molecule about a plan concept in the pool), the agent offers an ask push on that plan (`ask_push:<plan>`), as it offers commit pushes. It competes in the tournament with the moves.
- **Made:**
  - the mind waits the slices the call took;
  - the answer is told: "move x causes `<plan>_none`" (x stops it), or the plan's unstoppability.
- **Learned:** if the mind later makes x and the plan ends, the told link gains lived receipts; if not, it is belied. The ask push's own record (answers that held, and their cost) is what makes asking worth it or not, as commit earns trust.

## The tool's mind side, built (2026-11-13)

- **Gerundelle:** `Params.tool_use`, off by default. An ask push is offered when a question about a concept the agent's tool can answer stands in the pool. Made, the mind waits the slices the tool took. The answer is written as told (`SovAgent.answer_told`), with a seen record that asking brought an answer. Backups `*.before_tool_use`.
- **Warp chess:** `tool.MindTool`. A question about a plan the world shows now becomes "can the mind thwart it?". A stopping move is told as "<its push> causes <plan>_none"; when nothing stops it, nothing is told.
- **First trace** (`trace_1h.py 2 600 --plans --tool`, `trace_tool_s2.log`):
  - 89 calls in 600 ticks, 1 slice each.
  - 33 told "this move stops the plan" links standing at the end, 6 of them borne out by play (lived).
  - The mind came to question its own asking (`q:conditions:ask_push:...`).
- **Fixed after the trace:** it also asked about plans that weren't plans at the time, where any move trivially "stops" one. `can_answer` now takes only plans the world shows as stoppable or unstoppable.

## Step 3: a move's effect on the plans (2026-11-13)

**Decided (the user):**
- "Ending a plan is a gain". A new plan for them, or one made unstoppable, is a loss.
- "Yes, three levels": no plan there, held; a plan the mind can stop, contested; one it can't, lost.
- "Stoppability as the tool's prediction".

**Built:**
- **Gerundelle** (backups `*.before_contested_reading`, `*.before_tool_predictions`):
  - `SovAgent.track_region(..., contested=)`, read by `Territory.update`.
  - `predicted_losses` on a contested region: a loss only into a state it was never held in.
  - `force_predict` reads the agent's tool predictions (under `tool_use`).
- **`plansworld.py`:**
  - `give()` tracks every plan region in three levels.
  - `push_predictions()`: for each move, the plans it ends and the plans it creates (stoppable or not, read afresh), a slice after the move, relative to it (the plan's kind, its distance from the landing square or "x" across boards, and what presses its square: `p0`, `mine`, `theirs`).
- **`tool.MindTool`:** an answer "move x stops plan g" also stands as the prediction "x leads to g none", for as long as the board is as it was asked on.

**Checked** (`check_plans_effects.py`, 16 random moves in the two rooms):
- 200 predicted changes, all shown.
- Unpredicted: 60, all stoppability changes on plans already there (49 unstoppable to stoppable, 11 back), which are the tool's. Ended or created and not predicted: 0.
- The first version also re-read stoppability for the plans a move touched: 12 s a slice, and still missed those 60, because a rook flipped across makes far-away plans stoppable.

**Cost:** 7.6 s a slice on average (2.4-14.4) for all of a position's moves, before memo hits in play. That is the next thing to bring down.

## Speed: the Rust board (2026-11-13)

**Where the time went:** profiling `push_predictions` showed about 90% of it was the Python board generating legal moves (`reach` worst). The user: "Build the Rust board".

**The Rust board** (`E:/vscode/warponechess/WarpOneChess/rust_board`, the `warp_board` wheel, already installed):
- **Fixed:** it lacked the Python board's 2026-11-06 castling fix. Any king 2-square move from e1 was treated as castling, and in one checked position that moved Black's king on h1 to f1, so an illegal jump looked legal.
  - `WarpBoardInner::is_castle` is ported from Python's `_is_castle`: castling needs the right, the rook on the corner, and the squares between empty.
  - It is read where Python reads it: after the king moves in legality, before in push.
  - Rebuilt with maturin and reinstalled. The original source is in `rust_board/src.before_castle_fix`.
- **Checked** (`check_rust_board.py`): legal moves identical on 7,200 positions, and the board identical after all 288,327 moves made in both. 0.036 ms a position against Python's 0.70 ms.

**`plans.py` uses it** (backup `plans.py.before_rust`; `WARP_PURE=1` for the Python board):
- Legal moves come from Rust, as the Python board's move objects. The two engines list moves in another order, so a search that names the first stopping move can name another, equally valid one.
- **A line stops at a king capture** (the user, "Stop at a king capture"). A position with a king gone has no moves: the game is over. The capture is still a gain.
  - Why: the search had gone past captures. Rust panicked there, and the Python board read a kingless side's legality off wrapped-around squares (king square -1).
  - Kings are counted on the board, because the Python board's own `_king_sq` was stale after a capture (it put White's king on 82 with none there). That is a bug in the Python engine, left for the user.

**Results on the Rust board:**

| Check | Python board | Rust board |
|---|---|---|
| `check_plans.py` (4 positions vs a full search) | no problems; reads 8.5-15.4 s | no problems, the same plan counts (77, 98, 75, 85); reads 1.6-3.0 s |
| `check_tool.py` (32 questions) | no problems; 0.15-0.17 s a call | no problems; 0.01-0.04 s |
| `check_plans_effects.py` | 200 shown, 0 ended/created unpredicted; 7.6 s a slice (14.4 at most) | the same; **1.7 s a slice (3.3 at most)** |

## Step 4: commit through lines, built (2026-11-13)

**Decided (the user):**
- "Plans on the game world": step 4 is built where Black really replies.
- "Have the mind make the decision": how far a line goes and what counts as forced are the mind's. The world reports physics, and nothing is labelled forced.
- "Nothing: no idle limit": in a game the mind keeps its turn however long it thinks.
- "Why not have the tool answer the questions about the opponent's plans?": the plan questions get two-move lines too.
- "When it is stuck on something not on offer, it should go straight into the dream planner and pause the game"; "it should still satisfy the meta layer".

**Built:**
- **`plansgame.py` (`PlansGame`):** PlansWorld's plans on GameWorld; a game is set back only when it is over or at the half-move cap. `check_plansgame.py`: 218 predicted changes all shown, none ended or created unpredicted; 16.8 s a White turn from the starting position.
- **`plans.lines`, `plans.plan_lines`:** after a move of mine, each reply of theirs, my moves that end one of their plans. They record which replies each line holds after. The tool's heuristic tries only moves that touch the plan's square.
  - `check_lines.py`: 2,835 line-reply pairs played out, the plan gone after every one.
  - `check_plan_lines.py`: 602, all gone.
  - Cost: about 1 s a question in the room, about 12 s at the full start.
- **`tool.MindTool`:** a plan question is now also answered with its two-move lines, each standing as a prediction (my move, then my move; due 3 slices on; `line`: `every` or `some` reply). A question about a move on offer is answered with lines too.
- **Gerundelle:** `Params.commit_waits_turn` (a commitment waits for its turn), `Params.dream_when_stuck` (see DRIFT.md), and the planner's step cached exactly (`Model.split`).
- **`rung4p.py`:** games against random Black with the plans territory, the tool, commit and (`--dreams`) the dream planner. No want is placed. It reports a STALL if no half-move is played for 50 slices.
- **The dream:**
  - `dream.dream(focus=...)` can start from given positions.
  - `rung4p.dreamer` finds the latest position of this game where the stuck move was on offer, and dreams from there with it.
  - `DreamingGame` remembers positions and imagines lines. `DreamingPlayer` wakes with `dream.wake`. `carry.Carries` was left out: it imagined every untried move every slice, 72% of an 18 s slice.

**Found:**
- **Line commits:** they reached the tournament but lost at its first level (2.4-2.6 against about 2.65 for one-move commits). Only 1 of 9 plan questions found lines, and the lines lasted 3 slices. None was ever made.
- **Unknowns** (the user: "if they are new and untried, they are unknowns"): the line commits were served (pay 1.0 for "causes") and mattered. But a concept is attended only when it, or an ownership instance serving it, wins the top level, so they were never attended, never questioned, never tried.
- **Stuck questions:** a commit was on offer for slices 2-4, its question formed at 4 as the mind moved the king, and the question stood blocked for 12 slices. A commit named by its exact move exists for only a few slices.
- **Stale "stuck" signals:** one whose question was stored away by dormancy (no box) is confirmed every check and keeps a top-level place. The user declined a fix.
- **The dream when stuck** (seeded, 42 slices):
  - It worked as wired: two stuck commits at slice 7, two dreams, both found their position, game paused, and neither question went stuck again.
  - Every trial was at the edge (200 of 200), each dream ran its full budget, and each took 112-152 s.
  - Whether a dream reaches the stuck question is untraced (the user: not now).

## Dreaming in play, made fast enough to use (2026-11-13 to 2026-11-14)

**The user's rules:**
- "When it is stuck on something not on offer, it should go straight into the dream planner and pause the game", and "it should still satisfy the meta layer".
- In-game dreams: "lower it to 50", then "lower dream trials to 10" (`rung4p.IN_GAME_TRIALS`). Dreams between games keep `dream.DREAM_TRIALS` = 200.
- Games from the real start, not the room.
- "Count only dreams that ran".
- "EACH game can stop at the second dream", later the 4th, then the 14th (`rung4p.py --stop-at-dream N`).

**What a dream cost, and what was cut** (every exact change checked on the same seeded game, before and after):

| Change | Exact? | Saving |
|---|---|---|
| The planner's step caches a state's stripped form (`sov_agent.Model.split`) | identical over 80 slices | the room game 3x faster (678 s to 224 s) |
| Waking reads only a move's start, kept across slices; imagined moves not recorded as game positions (`imagine.py`) | identical over 30 slices | waking slices 2-3x faster |
| The mind pickled once per dream, not once per trial (`dream.snapshot`) | identical, all 400 trials' edges | a dream 13% faster |
| `Mind.candidates` uses a per-level index (Gerundelle) | identical, and tetris identical to clean5 | none measurable |
| Waking reads no plans: a start never keeps them, `carry.start_of` (`plansworld.read_forces` `no_plans`) | identical over 30 slices | waking slices a further 3-4x faster |
| `carry.Carries` left out of the game mind | (not the dream planner) | it was 72% of an 18 s slice |

**Dream waves (the user: "Yes, waves"):** built, but not in use (`dream_worker.py`, `dream.dream` with `agent.dream_workers`, `rung4p.py --dream-workers N`).
- One worker is exact: 140 s against 197 s for 400 trials.
- Waves are slower. A wave tries many new positions at once, and each needs a plan reading in the main process: 221-311 new positions against 5 one-at-a-time; at the full start, 10-trial dreams took 67-78 s in a wave against 26-42 s.
- Making them pay would mean whole trials in the workers (the world sent with the mind). Not built.

**Found:**
- One trial at a time, a dream reached only 5 distinct positions in 200 trials, and every trial was at the edge: it circles.
- What a dream costs now is unpickling a fresh copy of the mind for each trial: 58% of dream time at game 16. The mind grows, so later dreams are slower (about 50-100 s for 10 trials by game 19).

## Games from the start, the same mind throughout (2026-11-14)

**The runs:** `rung4p.py --start --half-moves 50 --dreams --stop-at-dream N`.
- Seed 0, random Black.
- Each game ends at its own end, the 50 half-move cap, or when the mind is about to run a real dream on its Nth slice with dreams in that game.
- A checkpoint is saved after every game (`checkpoints/rung4p_start_s0_g<n>.pkl`). `--resume` goes on from one: `save_run`/`load_run`, checked identical to an unbroken run.

| Games | Stop at | White's balance, by game | Notes |
|---|---|---|---|
| 1-7 | 2nd dream (attempts counted, my error) | +1, -3, 0, **+4**, +2, 0, +2 | most stopped by attempts with nothing to dream from; real dreams only in game 4, which set the record |
| 8-14 | 2nd real dream | 0, 0, 0, 0, +2, +3, +2 | 9 commits made, 9 came |
| 15-18 | 4th | 0, +1, 0, +3 | 14-18 half-moves a game |
| 19 | 14th | **+33** | 40 half-moves, 17 dreams; the checkpoint grew to 196 MB |

- **Over games 8-19:** no game ended behind. Every commit came: 19 made, 19 came by game 19.
- **The ownership check:** no want for a loss of its own, but for one flag at slice 432 (`plan_square_Rb6_stoppable`, a region held), untraced. A flag at slice 326 (`material_up`) is my check's mistake: wanting material up while even is a gain.
- **Fixed along the way:**
  - **A Gerundelle crash:** a whole want's region name holds ":", and `own:control:all:...` broke `Territory.observe`'s id split. Ids are now split on the first two colons only.
  - **Checkpoints and `__main__`:** pickle named rung4p's classes `__main__.*` when it ran as a script; it now runs through the module, and load maps the old names.
  - **A stale dream count:** a checkpoint saved by the attempt-counting code carried its count into the next game; load now clears it.
  - **Waiting for Black's news:** a game ended on White's move waited forever for random Black to read it.

**Open:**
- Game 20 on: the run continues (`rung4p_14games_start_s0_from_g18.log`).
- The mind's growth: checkpoints 15 MB, then 60 MB, then 196 MB, and dreams slowing with it.
- Whole-trial dream workers, if dreams need to be faster still.
