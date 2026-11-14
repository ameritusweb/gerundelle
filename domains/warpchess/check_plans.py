"""Checks plans.py with no mind (PLAN.md step 2): on positions from the ladder's rooms and from random play out of them,
- two-move plans as read (candidates from what a second move would gain if the mind passed, replies searched until one refutes) against a
  full search (every first move, every reply, the whole set of gains after it, intersected): the same plans, no more, no fewer;
- every one-move plan is made by the move it names (pushed, the gain is there);
- a thwarting move, when one is named, leaves the plan no plan; when none is, no move of the mind's does (a full search over its moves);
- the time each takes.
Run: python -u -X utf8 check_plans.py [positions]"""
import random
import sys
import time

import rung0  # noqa: F401  (Gerundelle and the engine on the path)
import plans
from warpworld import RUNG1_TWO, RUNG2B, WarpBoard

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
WHITE, BLACK = True, False
rng = random.Random(5)


def full_two(board, them, me, memo):
    one = plans.one_move(board, them, me, memo)
    b, firsts = plans.moves(board, them, memo)
    out = set()
    for m1 in firsts:
        b1 = plans._after(b, m1)
        r_board, replies = plans.moves(b1, me, memo)
        inter = None
        for r in replies:
            g = set(plans.one_move(plans._after(r_board, r), them, me, memo))
            inter = g if inter is None else inter & g
        out |= (inter or set()) - set(one)
    return out


positions = []
for fen in (RUNG1_TWO, RUNG2B):
    b = WarpBoard.from_fen(fen)
    positions.append(b.copy())
    for _ in range(N // 2 - 1):
        c = b.copy()
        for _ in range(rng.randrange(1, 6)):
            ms = list(c.legal_moves)
            if not ms:
                break
            c.push(rng.choice(ms))
        positions.append(c)

bad = []
for k, b in enumerate(positions):
    memo = {}
    t0 = time.perf_counter()
    read = plans.plans(b, BLACK, WHITE, memo)
    t1 = time.perf_counter()
    fmemo = {}
    full = full_two(b, BLACK, WHITE, fmemo) | set(plans.one_move(b, BLACK, WHITE, fmemo))
    t2 = time.perf_counter()
    if set(read) != full:
        bad.append((k, "plans differ", sorted(set(read) ^ full)[:6]))
    one = plans.one_move(b, BLACK, WHITE, memo)
    bb, _ = plans.moves(b, BLACK, memo)
    for g, ms in one.items():
        if g not in plans.gains(bb, plans._after(bb, ms[0]), BLACK, WHITE, memo):
            bad.append((k, "one-move plan not made by its move", g))
    t3 = time.perf_counter()
    h = plans.held(b, BLACK, WHITE, memo)
    t4 = time.perf_counter()
    wb, wmoves = plans.moves(b, WHITE, memo)
    for g, (depth, x) in h.items():
        if x is not None:
            if plans.still_plan(g, plans._after(wb, x), BLACK, WHITE, fmemo):
                bad.append((k, "named thwart doesn't thwart", g))
        elif any(not plans.still_plan(g, plans._after(wb, y), BLACK, WHITE, fmemo) for y in wmoves):
            bad.append((k, "a thwart exists but none was named", g))
    kinds = {}
    for g, (depth, x) in h.items():
        key = (g[0], depth, "held" if x is not None else "unstoppable")
        kinds[key] = kinds.get(key, 0) + 1
    print(f"position {k}: plans {len(read)} (read {t1 - t0:.2f}s, full search {t2 - t1:.2f}s); held/unstoppable read {t4 - t3:.2f}s; "
          f"{dict(sorted(kinds.items()))}", flush=True)
print("problems:", bad[:10] if bad else "none")
