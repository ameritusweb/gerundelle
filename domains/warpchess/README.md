# Warp chess

**The track's question:** what does a Gerundelle mind come to understand of Warp 1 Chess by playing it, with nothing written into it?

Warp 1 Chess is the author's game: two 8x7 boards back to back, pieces that flip between them, and crabs. Its Rust board (`rust_board/`,
the game engine's move generator, built as a Python module; `rustboard.py` puts it behind the interface used here) is the world's
physics. No rules, piece values, strategy or engine evaluation reach the mind:
it is offered the legal moves and perceives what they do. Setting up a position is setting up a room, as fiction does, and what the mind
comes away with is its own. The rules below are for the reader.

The lessons carried in from the other tracks:
- The world pushes back: a move not on offer does nothing (`../worldbuilding`, and `DuelWorld` in `../cognitivechess`).
- Small positions first, and full games later (`../cognitivechess/LADDER.md`).
- Rungs are made as `../cognitivechess/MAKING_RUNGS.md` says, with what's expected written down before running.

## The rules (from the official rulebook, `rulebook/`)

The rulebook's 20 pages are in `rulebook/` (`page_02.png` to `page_08.png` are the rules; `page_12.png` is a quick reference).

**The board** (page 2). One board of 8 files and 7 ranks standing for two overlapping dimensions: every square is split diagonally into
a Left half (White's side) and a Right half (Black's side). In notation each square carries its side: `La2` is a2 on the Left, `Ra2` on
the Right (page 8). Rank 6 is the warp zone, and rank 7 the forced-flip rank.

**The start** (page 2). White's pieces on the Left, Black's on the Right. The back rank as in chess; the pawns in a chevron, the centre
ones advanced and the edge ones near the back rank: a2, b3, c4, d5, e5, f4, g3, h2.

**Moving** (page 3). Every piece moves as in chess, across the whole board, on whichever side it stands. Pawns move forward on their own
side, and keep going in the same direction (downward) once they have flipped to the other side.

**Flipping** (page 3), the game's core: a piece can flip to the same square on the other side, either before its move or after it.
- **Pre-flip** (flip, then move): illegal if the flip puts the piece in immediate danger of capture. Written `La2>Ra2Rb4`.
- **Post-flip** (move, then flip): illegal if the move was a capture. Written `La2Lb4=Rb4`.
- **Forward flips** (own side to the opponent's) only from ranks 6-7; **backward flips** from any rank. Kings and crabs may flip forward
  from any rank.
- A flip can't land on rank 7 of the side it lands on, and a friendly piece there always blocks it.

**Post-flip captures** (page 4). An enemy piece on the flip's destination is captured, unless the move was one that can never capture
(a pawn's push forward, a crab's or king's two-square jump): then the destination must be empty.

**Forced flips** (page 4). A piece that reaches rank 7 on its home side must flip to the other side. Whatever stands on the destination,
friend or enemy, is removed from the game, and the flipping piece takes its place. On the away side a piece may stay on rank 7.

**Captures and check** (page 4). Captures as in chess, on either side. A piece can't flip if that would put its own king in check. Check
and checkmate count threats from both sides, including a piece that could flip across and attack. Kings can't enter rank 7 on either
side.

**The King Crab** (page 6). The king moves one square as in chess, and also jumps two squares orthogonally, over pieces, to an empty
square (never a capture). It may flip forward from any rank.

**Pawns and crabs** (pages 6-7). A pawn that reaches the last rank promotes, always to a crab: on its own side it promotes and is forced
to flip; on the other side it stays. A **crab** moves one square up or down (moving or capturing), one square in any other direction only
to capture, and two squares orthogonally over pieces to an empty square (never a capture). It may flip forward from any rank. A crab that
reaches the last rank of the side opposite its origin promotes to a queen, rook, bishop or knight, once.

**The end** (page 8). Checkmate (threats from both sides counted), or the capture of a king. Draws: stalemate, insufficient material,
threefold repetition.

Pages 9-20: two example games, opening principles, the crab ladder (two crabs leapfrogging up the board), tips, the quick reference, eight
openings found in self-play ("The Wild Eight") and four mating patterns.

## What is here

The full record is `PLAN.md` (the plan and each step since 2026-11-13) and `LADDER.md` (every rung: its question, what was expected,
results and residue).

| Files | What they hold |
| --- | --- |
| `rust_board/`, `rustboard.py` | The rules: the Rust board's source (with the castling fix, and the setters and plain reads this domain uses, both 2026-11-14), and the board, moves and square helpers on it |
| `warpworld.py`, `gameworld.py`, `duel.py` | Warp 1 Chess behind the interface a mind reads: rooms, full games, two sides |
| `plans.py`, `plansworld.py`, `plansgame.py` | The opponent's plans (a gain of a piece, a square, an outpost); territory as those plans thwarted: none there is held, one the mind can stop is contested, one it can't is lost |
| `tool.py` | The search tool the mind can ask about plans, in told answers and two-move lines |
| `dream.py`, `imagine.py`, `carry.py`, `shoes.py` | The dream planner, imagined lines, carrying experience by force structure, the opponent's reply as the mind would make it |
| `rung0.py` ... `rung4p.py` | The rungs (`LADDER.md`) |
| `check_*.py`, `test_warpchess.py` | Checks with no mind: the world, the plans, the tool, the lines |
| `trace_*.py` | The traces each finding in `PLAN.md` / `LADDER.md` came from |

## Run

First build the Rust board and install it (needs Rust and `pip install maturin`):

```bash
cd domains/warpchess/rust_board
maturin build --release
pip install target/wheels/warp_board-*.whl
```

Then:

```bash
cd domains/warpchess
python -X utf8 rung0.py                                    # rung 0
PYTHONHASHSEED=0 python -u -X utf8 rung4p.py --start --half-moves 50 --dreams --stop-at-dream 14 --games 20
```

`rung4.py --room <iteration>` also reads the game's self-play openings (`$MINI_GAMES`), which aren't in this repository; the default
room, the chevron start, doesn't need them.
