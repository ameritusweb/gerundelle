"""Why the mind sits stuck on its questions about commits (trace_line_unknowns.log: meta:stuck:q:causes:commit_push:... among the
top-level winners every slice). Meta.check emits "stuck" for a pool molecule blocked 3 ticks running; operating on it parks the question
when nothing could answer it now (Meta.parkable). Replays rung 4p's room game (seed 0, PYTHONHASHSEED=0) and, at each slice in the window,
for each meta:stuck molecule in the pool: its subject (a question), the concept and slot the question is about, how long the question
has stood, its blocked count, whether it was parked or could be, whether the commit it asks about is on offer now, how many times that
commit has been made, the commit's "causes" funding (what would close the question: 1.0), and whether an experiment or an ask could
answer it; and the stuck molecule's activation and bid at the top level.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_stuck.py [from slice] [to slice]"""
import sys

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

LO = int(sys.argv[1]) if len(sys.argv) > 1 else 20
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 32
w, a = rung4p.build(0, RUNG1_TWO)
black = RandomSide(w, 0)
und, mind = a.mind.understanding, a.mind
meta = mind.meta
born = {}
slices = 0


def look(t):
    for q in und.questions:
        born.setdefault(q, t)
    if t < LO:
        return
    rec = a.last_rec
    lv = rec["levels"][-1] if rec and rec.get("levels") else {"bids": {}, "winners": []}
    offered = set(mind.inquiry.actions) if mind.inquiry else set()
    stucks = [i for i in mind.pool if i.startswith("meta:stuck:")]
    print(f"slice {t}: stuck molecules in the pool {len(stucks)}; at the top {[i[:60] for i in lv['winners'] if i.startswith('meta:stuck')]}", flush=True)
    for m in stucks[:3]:
        subj = m[len("meta:stuck:"):]
        c, r = und.questions.get(subj, (None, None))
        made = sum(1 for x in a.__dict__.get("commit_log", []) if x[1] == c and x[2] == "made")
        exps = [e for e, p in (mind.inquiry.plans.items() if mind.inquiry else ()) if c and c in str(p)]
        mol = mind.pool[m]
        print(f"    {m[:120]}\n      the question: concept {str(c)[:110]}, slot {r}; standing since slice {born.get(subj)}; in the pool "
              f"{subj in mind.pool}; blocked {meta.stuck.get(subj)}; parked {subj in mind.boxes and mind.boxes[subj].get('parked')}; "
              f"parkable now {meta.parkable(mind.pool[subj], (c,)) if subj in mind.pool and c else None}\n"
              f"      the commit on offer now {c in offered}; made {made} times; its causes funding {round(und.funding(c, 'causes'), 2) if c else None}; "
              f"experiments naming it {len(exps)}; the tool can answer it {a.tool.can_answer(c) if c else None}\n"
              f"      the stuck molecule: act {mol.act:.2f}, bid at the top {round(lv['bids'].get(m, -1), 2)}; watched {m in meta.watch}", flush=True)


while slices < HI:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            a.tick()
            give(a, w)
            slices += 1
            look(slices)
            if len([x for x in w.log if x[2]]) > n or slices >= HI:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
        look(slices)
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
