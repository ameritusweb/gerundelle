"""Why plans as read differ from the full search on a position (check_plans.py's four differences). For each differing gain: which side
has it, and for the first moves of theirs that would make it a two-move plan, what each of my replies leaves (the full search's
one_move gains against plans.there). python -X utf8 trace_plan_diff.py "<fen>" """
import sys

import plans
from check_plans import full_two, name
from rustboard import WarpBoard

WHITE, BLACK = True, False
sys.stdout.reconfigure(encoding="utf-8")
b = WarpBoard.from_fen(sys.argv[1])
memo, fmemo = {}, {}
read = plans.plans(b, BLACK, WHITE, memo)
full = full_two(b, BLACK, WHITE, fmemo) | set(plans.one_move(b, BLACK, WHITE, fmemo))
one = set(plans.one_move(b, BLACK, WHITE, {}))
for g in sorted(set(read) ^ full):
    side = "read only" if g in read else "full only"
    print(f"{name(g)}: {side} (read depth {read.get(g)}; in one-move {g in one})")
    bt, firsts = plans.moves(b, BLACK, {})
    for m1 in firsts:
        b1 = plans._after(bt, m1)
        m = {}
        if g not in plans.one_move(b1, BLACK, WHITE, m):
            continue
        rb, replies = plans.moves(b1, WHITE, m)
        full_ok = all(g in plans.one_move(plans._after(rb, r), BLACK, WHITE, m) for r in replies)
        there_ok = all(plans.there(g, plans._after(rb, r), BLACK, WHITE, m) for r in replies)
        if full_ok != there_ok:
            bad = [r.uci() for r in replies if (g in plans.one_move(plans._after(rb, r), BLACK, WHITE, m))
                   != plans.there(g, plans._after(rb, r), BLACK, WHITE, m)]
            print(f"   first {m1.uci()}: full {full_ok}, there {there_ok}; replies where they disagree: {bad[:5]}")
