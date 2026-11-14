"""Why a commit on offer is never tried while a question about it stands (trace_stuck / _probe_q: "what does committing to Rc3-Rc1
cause?" stood from slice 4 to 16 with the commit on offer, never made, went stuck, then stale). For each slice in the window: the question
(in the pool? its bid at each level; blocked count); inquiry's experiments for it (Mind.inquiry: suggest / plans naming the commit) and
whether one won; the commit itself (on offer, in the pool, its bid at each level); the top level's winners and what the mind did.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_untried_commit.py [target text] [to slice]"""
import sys

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

TARGET = sys.argv[1] if len(sys.argv) > 1 else "720 Rc3Rc1_push:white_king_Lc1_present"
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 17
w, a = rung4p.build(0, RUNG1_TWO)
black = RandomSide(w, 0)
und, mind = a.mind.understanding, a.mind
slices = 0


def bids(rec, pred):
    return [(L, round(max((v for i, v in l_["bids"].items() if pred(i)), default=-1), 2)) for L, l_ in enumerate(rec.get("levels", []))]


def look(t, choice):
    rec = a.last_rec
    if not rec:
        return
    commit = next((i for i in (mind.inquiry.actions if mind.inquiry else ()) if TARGET in i and i.startswith("commit_push")), None)
    q = next((q for q in und.questions if TARGET in q), None)
    inq = mind.inquiry
    exps = {e: p for e, p in (inq.plans.items() if inq else ()) if TARGET in str(p)}
    top = rec["levels"][-1]["winners"]
    did = None if choice is None else f"{choice[0]}:{str(choice[1])[:30]}"
    print(f"slice {t}: did {did}; goal {str(a.goal)[:50]}; top {[x[:45] for x in top][:6]}", flush=True)
    if q:
        print(f"    question in pool {q in mind.pool}, blocked {mind.meta.stuck.get(q)}, bids by level {bids(rec, lambda i: i.split('|')[0] == q)}; "
              f"slot {und.questions[q][1]}; inquiry suggests an experiment for it {bool(inq and inq.suggest(und.questions[q][1], und.questions[q][0]))}", flush=True)
    print(f"    experiments naming the commit: {list(exps)[:3]}; won {[e for e in exps if e in top]}; rec experiments {rec.get('experiments', [])[:2]}", flush=True)
    if commit:
        print(f"    the commit on offer; in the pool {commit in mind.pool}, bids by level {bids(rec, lambda i: i.split('|')[0] == commit)}", flush=True)
    else:
        print("    the commit not on offer", flush=True)


while slices < HI:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            choice, _ = a.tick()
            give(a, w)
            slices += 1
            look(slices, choice)
            if len([x for x in w.log if x[2]]) > n or slices >= HI:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        choice, _ = a.tick()
        give(a, w)
        slices += 1
        look(slices, choice)
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
