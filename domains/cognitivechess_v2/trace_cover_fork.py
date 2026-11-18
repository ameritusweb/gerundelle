"""Which of White's moves end Black's a1 and e1 plans in the fork position (check_covers.py's), and how many plans of each kind stand."""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import rung0  # noqa: F401
import plans
from plansworld import coverage
from rustboard import WarpBoard, square_name

b = WarpBoard.from_fen("6k1/8/8/8/8/8/2n5/R3Q1K1 w - - 0 1")
memo = {}
stoppable, stops = coverage(b, memo, True, False)
one = plans.one_move(b, False, True, memo)
print("plans:", Counter(k for k, _ in one), "| stoppable:", Counter(k for k, _ in stoppable))
a1, e1 = ("piece", 0), ("piece", 4)
for x, s in stops.items():
    if a1 in s or e1 in s:
        print(f"{x.uci()}: ends a1 {a1 in s}, e1 {e1 in s}")
print("Black's moves making a1:", [m.uci() for m in one.get(a1, [])], "e1:", [m.uci() for m in one.get(e1, [])])
