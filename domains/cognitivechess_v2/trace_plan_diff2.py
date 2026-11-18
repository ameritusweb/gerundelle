"""For one differing gain (full only): the first moves whose replies all leave it, and what plans.two_move's candidate set does with
each. python -X utf8 trace_plan_diff2.py "<fen>" <kind> <square name>"""
import sys

import plans
from rustboard import WarpBoard, square_from_name

WHITE, BLACK = True, False
sys.stdout.reconfigure(encoding="utf-8")
b = WarpBoard.from_fen(sys.argv[1])
g = (sys.argv[2], square_from_name(sys.argv[3]))
memo = {}
one = set(plans.one_move(b, BLACK, WHITE, memo))
bt, firsts = plans.moves(b, BLACK, memo)
for m1 in firsts:
    b1 = plans._after(bt, m1)
    cands = set(plans.one_move(b1, BLACK, WHITE, memo))
    rb, replies = plans.moves(b1, WHITE, memo)
    if not replies:
        inter = cands & plans.no_reply(rb, replies, WHITE)
    else:
        inter = None
        for r in replies:
            gg = set(plans.one_move(plans._after(rb, r), BLACK, WHITE, memo))
            inter = gg if inter is None else inter & gg
    if g not in (inter or set()):
        continue
    print(f"first {m1.uci()}: full has it; replies {len(replies)}; in their one-move after m1: {g in cands}; already a one-move plan: {g in one}")
    print(f"   after m1, White in check: {rb.is_in_check(WHITE)}; replies: {[r.uci() for r in replies][:10]}")
    for r in replies:
        b2 = plans._after(rb, r)
        print(f"   reply {r.uci()}: there {plans.there(g, b2, BLACK, WHITE, memo)}, in one_move {g in plans.one_move(b2, BLACK, WHITE, memo)}")
