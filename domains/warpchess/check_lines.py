"""Checks plans.lines (the tool's line reading, PLAN.md step 4) with no mind: from the room and from positions after random play out of it,
for a few of White's moves m1, every line found (m2 ends plan g after Black's reply r) played out on the board: after m1, r and m2, g must
not be among Black's one-move plans as plans.one_move reads them in full (a reading independent of the single-gain check the lines use).
Run: python -u -X utf8 check_lines.py [positions] [moves per position]"""
import random
import sys
import time

import rung0  # noqa: F401
import plans
from warpworld import RUNG1_TWO, WarpBoard

POS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
M1 = int(sys.argv[2]) if len(sys.argv) > 2 else 3
WHITE, BLACK = True, False
rng = random.Random(5)
boards = [WarpBoard.from_fen(RUNG1_TWO)]
while len(boards) < POS:
    b = WarpBoard.from_fen(RUNG1_TWO)
    for _ in range(rng.randrange(2, 8)):
        ms = b.legal_moves
        if not ms or b.is_game_over():
            break
        b.push(rng.choice(ms))
    if b.turn == WHITE and b.legal_moves and not b.is_game_over():
        boards.append(b)
checked, wrong = 0, []
for i, b in enumerate(boards):
    memo = {}
    _, ms = plans.moves(b, WHITE, memo)
    for m1 in rng.sample(ms, min(M1, len(ms))):
        t0 = time.time()
        n, out = plans.lines(b, m1, BLACK, WHITE, memo)
        dt = time.time() - t0
        for (m2, g), replies in out.items():
            for r in replies:
                c = b.copy()
                c.push(m1)
                c.push(r)
                c.push(m2)
                checked += 1
                if g in plans.one_move(c, BLACK, WHITE, {}):
                    wrong.append((i, m1.uci(), r.uci(), m2.uci(), g))
        print(f"position {i} {m1.uci()}: {n} replies, {len(out)} lines, {sum(len(v) for v in out.values())} (line, reply) pairs, {dt:.1f}s", flush=True)
print(f"line-reply pairs played out {checked}; plan still there after the line {len(wrong)}")
for x in wrong[:8]:
    print("  ", x)
