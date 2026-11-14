"""Trace (LADDER.md, rung 1g, both switches): seed 0, main mind alone met the want 10 times in its first 200 slices and 12 in 1000. Why does it
stop? At every slice where a move that brought the want is on offer: the want in the pool and its open site, the move's funded `causes` toward
the want, its box (settled?), whether it was in the pool and needed, its bid and highest level, and whether a plan came of it."""
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from molecules import concept_of
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld

sys.stdout.reconfigure(encoding="utf-8")
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
PIECES = len(sys.argv) > 2 and sys.argv[2] == "pieces"
w = WarpWorld(RUNG1_TWO, seed=SEED, moves=2, forces=True)
a = OfferedMainMind(w, pieces=PIECES, forces=True)
for ag in [a] + list(a.pieces.values()):
    ag.mind.p.imagined_tournament = True
    ag.mind.p.want_site = True
m, und = a.mind, a.mind.understanding
plan = {"step": None}
real = a.plan_step
def plan_step(invs, budget=60, horizon=3):
    plan["step"] = real(invs, budget, horizon)
    return plan["step"]
a.plan_step = plan_step
rows, met_at = [], []
for t in range(1000):
    if a.goal is None:
        a.goal = WANT
    plan["step"] = None
    n_met = len(a.reached)
    a.tick()
    if len(a.reached) > n_met:
        met_at.append(t)
    rec = a.last_rec
    ways = {inv_id(i) for i, _, names in a.pushed if WANT in names}
    for c in ways & {inv_id(i) for i in w.invitations()}:
        f = und.rel.get(c, {}).get(("causes", WANT), [0, 0, 0])
        goal = [x for x in m.pool.values() if "goal" in x.tags]
        in_pool = [i for i in m.pool if (concept_of(i) or i) == c]
        halves = [i[len(c):] for i in in_pool]
        bids0 = rec["levels"][0]["bids"]
        reach = max([L for L, lv in enumerate(rec["levels"]) for i in lv["winners"] if (concept_of(i) or i) == c], default=-1)
        hist = m.meta.modes.get(m.meta.reading_in(c, a.facts_now()), [])
        rows.append(dict(t=t, c=c[:30], funded=round(f[0] + f[2] + m.p.credulity * f[1], 2), want_in_pool=bool(goal), want_site=goal[0].sites if goal else None,
                         settled=bool(m.boxes.get(c, {}).get("settled")), in_pool=bool(in_pool), bid=round(max((bids0[i] for i in in_pool if i in bids0), default=-1), 2),
                         reach=reach, plan=plan["step"] is not None, watching=a.watching is not None, refuted=(c, "causes", WANT) in und.refuted,
                         reading_rate=f"{sum(WANT in h[2] for h in hist)}/{len(hist)}", reading=m.meta.reading_in(c, a.facts_now())[len(c):], halves=halves, top=[i[:38] for i in rec['levels'][-1]['winners'][:4]]))
print("wants met at slices:", met_at)
for lo in range(0, 1000, 200):
    rs = [r for r in rows if lo <= r["t"] < lo + 200]
    if not rs:
        print(f"{lo}-{lo+199}: the capture never on offer"); continue
    print(f"{lo}-{lo+199}: on offer {len(rs)}; in pool {sum(r['in_pool'] for r in rs)}; reached top {sum(r['reach'] == 2 for r in rs)}; plan {sum(r['plan'] for r in rs)}; "
          f"want in pool {sum(r['want_in_pool'] for r in rs)}; settled {sum(r['settled'] for r in rs)}; refuted {sum(r['refuted'] for r in rs)}")
print()
for r in rows[:4] + rows[len(rows)//2:len(rows)//2+4] + rows[-6:]:
    print(r)
