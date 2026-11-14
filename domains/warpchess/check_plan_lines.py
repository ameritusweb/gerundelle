"""Checks plans.plan_lines with no mind: for the opponent's one-move plans in the room and positions after random play, every line found
(m1, Black's reply r, m2) played out on the board must leave the plan gone (plans.one_move read in full, independent of the check the
lines use). Run: python -u -X utf8 check_plan_lines.py [positions]"""
import random
import sys
import time

import rung0  # noqa: F401
import plans
from warpworld import RUNG1_TWO, WarpBoard

POS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
WHITE, BLACK = True, False
rng = random.Random(11)
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
checked, wrong, n_plans, with_lines, every = 0, [], 0, 0, 0
for i, b in enumerate(boards):
    memo = {}
    for g in sorted(plans.one_move(b, BLACK, WHITE, memo)):
        n_plans += 1
        t0 = time.time()
        found = plans.plan_lines(b, g, BLACK, WHITE, memo)
        with_lines += bool(found)
        for m1, (n, by_m2) in found.items():
            for m2, replies in by_m2.items():
                every += len(replies) == n
                for r in replies:
                    c = b.copy(); c.push(m1); c.push(r); c.push(m2)
                    checked += 1
                    if g in plans.one_move(c, BLACK, WHITE, {}):
                        wrong.append((i, g, m1.uci(), r.uci(), m2.uci()))
    print(f"position {i}: {n_plans} plans so far, {with_lines} with lines, lines holding after every reply {every}", flush=True)
print(f"line-reply triples played out {checked}; plan still there after {len(wrong)}")
for x in wrong[:6]:
    print("  ", x)
