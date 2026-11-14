"""Checks the tool with no mind (tool.py): on the ladder's rooms and positions after random play from them, for each of the opponent's
plans (plans.plans), the tool's answer to "can the mind thwart it?" against a full search (every move of the mind's, the plan read in full
after each): a named move must stop the plan; None only if no move does. Also what each call cost (positions, slices), and a second call
on the same position answered from the table.
Run: python -u -X utf8 check_tool.py [positions] [plans per position]"""
import random
import sys
import time

import rung0  # noqa: F401
import plans
from tool import Tool
from warpworld import RUNG1_TWO, RUNG2B, WarpBoard

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
K = int(sys.argv[2]) if len(sys.argv) > 2 else 12
WHITE, BLACK = True, False
rng = random.Random(9)
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
        positions.append(plans.turned(c, WHITE))
tool = Tool()
bad, n_calls = [], 0
for k, b in enumerate(positions):
    found = plans.plans(b, BLACK, WHITE, {})
    sample = sorted(found)[:K] if len(found) <= K else rng.sample(sorted(found), K)
    wb, wmoves = plans.moves(b, WHITE, {})
    for g in sample:
        t0 = time.perf_counter()
        answer, slices = tool.ask(("thwart", g), b)
        dt = time.perf_counter() - t0
        n_calls += 1
        fmemo = {}
        if answer is not None:
            if plans.still_plan(g, plans._after(wb, answer), BLACK, WHITE, fmemo):
                bad.append((k, g, "the named move doesn't stop it"))
        elif any(not plans.still_plan(g, plans._after(wb, y), BLACK, WHITE, fmemo) for y in wmoves):
            bad.append((k, g, "a move stops it but the tool said none"))
        again, slices2 = tool.ask(("thwart", g), b)
        if again != answer or slices2 != 1:
            bad.append((k, g, "the table didn't answer the same"))
        q, a, searched, s = tool.calls[-2]
        print(f"position {k} {g}: {'stops it: ' + a.uci() if a is not None else 'nothing stops it'}; {searched} positions, {s} slices, "
              f"{dt:.2f}s", flush=True)
print(f"{n_calls} questions; problems: {bad[:8] if bad else 'none'}")
