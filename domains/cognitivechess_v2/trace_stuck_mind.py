"""The play app's stuck mind (play_stuck_*.pkl: no move in 400 slices): a few slices replayed; at each level of its tournament, how
many pushes are bid, the best push's bid, the lowest winner's bid (the bar), and whether any push wins; and the top level's winners.
python -X utf8 trace_stuck_mind.py play_stuck_<time>.pkl"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from plansworld import give, read_mate_passed
from rung4p import load_run

a, w, _, st = load_run(sys.argv[1])
print("FEN", w.board.to_fen(), "| goal", a.goal, "| winner_acts", a.mind.p.winner_acts, "| patience", a.mind.p.patience)
is_push = lambda x: "_push:" in x and x[:3].isdigit()
for t in range(3):
    w.actor = w.me_name
    choice, rec = a.tick()
    read_mate_passed(a, choice)
    give(a, w)
    print(f"slice {t}: chose {None if choice is None else choice[0]}")
    for L, lv in enumerate(rec["levels"]):
        bids, win = lv["bids"], lv["winners"]
        pushes = sorted([x for x in bids if is_push(x)], key=lambda x: -bids[x])
        bar = min((bids.get(x, 0) for x in win), default=None)
        print(f"   level {L}: {len(bids)} bid, {len(win)} win (lowest winning bid {bar if bar is None else round(bar, 2)}); pushes bid {len(pushes)}, "
              f"best {[(p.split('_push')[0], round(bids[p], 2)) for p in pushes[:3]]}; pushes winning {sum(1 for x in win if is_push(x))}")
    top = rec["levels"][-1]
    print("   top winners:", [(x[:45], round(top["bids"].get(x, 0), 2)) for x in sorted(top["winners"], key=lambda x: -top["bids"].get(x, 0))])
mate_oracle.close()
