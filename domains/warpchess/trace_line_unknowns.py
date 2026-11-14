"""Why a new, untried two-move line commit (an unknown) doesn't become a question or an experiment (trace_line_commits2.log: 11 line
commits on offer at slices 27-29, never past the first level, gone when the mind moved). For the slices around them, for the line
commits on offer: do they matter (Understanding.matters), are they served by an open ownership slot (and what pay), which slots are
open on them (open_slots, needed), is their SOV attended (sov:<c> in the pool), does a question about them stand, does inquiry offer
an experiment with them; and what the SOV cue went to each slice (2 a slice) and why the line commits weren't among them: did one win
the top level (cueing (c) needs it).
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_line_unknowns.py [from slice] [to slice]"""
import sys

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

LO = int(sys.argv[1]) if len(sys.argv) > 1 else 24
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 30
w, a = rung4p.build(0, RUNG1_TWO)
black = RandomSide(w, 0)
und, mind, terr = a.mind.understanding, a.mind, a.mind.territory
slices = 0
steps = lambda c: c.count("_push:") - 1


def look(t, sov_before):
    if t < LO:
        return
    offers = sorted(i for i in (mind.inquiry.actions if mind.inquiry else ()) if i.startswith("commit_push:") and steps(i) == 2)
    cued = sorted(i[4:][:70] for i in mind.pool if i.startswith("sov:") and i not in sov_before)
    rec = a.last_rec
    top = rec["levels"][-1]["winners"] if rec and rec.get("levels") else []
    print(f"slice {t}: line commits on offer {len(offers)}; SOVs cued this slice {cued}; top-level winners {[x[:50] for x in top][:6]}", flush=True)
    served = terr.served or {}
    plans_ = mind.inquiry.plans if mind.inquiry else {}
    for c in offers[:3]:
        qs = [q for q, (cc, r) in und.questions.items() if cc == c]
        exps = [e for e, p in plans_.items() if c in str(p)]
        print(f"    {c[:100]}\n        matters {c in und.matters}; served {served.get(c) and (round(served[c][0], 3), served[c][1])}; "
              f"open slots {sorted(und.open_slots(c))}; needed {und.needed(c)}; region {und.owners.get(c)} holder "
              f"{terr.rows.get(und.owners.get(c, ''), {}).get('holder')} claims {len(terr.rows.get(und.owners.get(c, ''), {}).get('claims', {}))}; "
              f"SOV attended {('sov:' + c) in mind.pool}; questions {qs[:2]}; experiments {exps[:2]}; in the pool {c in mind.pool}", flush=True)
    one = sorted(i for i in (mind.inquiry.actions if mind.inquiry else ()) if i.startswith("commit_push:") and steps(i) == 1)[:1]
    for c in one:
        print(f"    (a one-move commit, for comparison) matters {c in und.matters}; served {served.get(c) and round(served[c][0], 3)}; "
              f"open slots {sorted(und.open_slots(c))}; region {und.owners.get(c)}", flush=True)


while slices < HI:
    sov_before = {i for i in mind.pool if i.startswith("sov:")}
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            sov_before = {i for i in mind.pool if i.startswith("sov:")}
            a.tick()
            give(a, w)
            slices += 1
            look(slices, sov_before)
            if len([x for x in w.log if x[2]]) > n or slices >= HI:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
        look(slices, sov_before)
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
