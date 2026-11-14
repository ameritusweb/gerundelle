"""Trace (LADDER.md, rung 1g): seed 4, main mind alone, both switches. From slice 746 the want isn't met and from 800 the capture is never on
offer: the move that sets it up isn't played. At each episode's first move: the setup moves (those played just before a move that brought the
want) on offer, in the pool, how far they got, what the planner returned, and what was played and how."""
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from molecules import concept_of
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld

sys.stdout.reconfigure(encoding="utf-8")
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 4
w = WarpWorld(RUNG1_TWO, seed=SEED, moves=2, forces=True)
a = OfferedMainMind(w, pieces=False, forces=True)
a.mind.p.imagined_tournament = True
a.mind.p.want_site = True
a.mind.p.setup_support = len(sys.argv) > 2 and sys.argv[2] == "setup"
m = a.mind
how = {"v": None}
planned, winner, did = a.planned, a.winner, m.inquiry.did
def p(invs):
    s = planned(invs)
    if s is not None: how["v"] = ("plan", inv_id(s))
    return s
def wn(rec, invs):
    s = winner(rec, invs)
    if s is not None: how["v"] = ("attention", inv_id(s))
    return s
def d(eid):
    how["v"] = ("experiment", eid[:60])
    return did(eid)
a.planned, a.winner, m.inquiry.did = p, wn, d
rows = []
for t in range(1000):
    if a.goal is None:
        a.goal = WANT
    first = w.moved == 0 and a.watching is None
    preps = set()
    for k, (inv, facts, names) in enumerate(a.pushed):
        if WANT in names and k > 0:
            preps.add(inv_id(a.pushed[k - 1][0]))
    offered = {inv_id(i) for i in w.invitations()}
    how["v"] = None
    a.tick()
    if first and t >= 600:
        rec = a.last_rec
        reach = {}
        for L, lv in enumerate(rec["levels"]):
            for i in lv["winners"]:
                reach[concept_of(i) or i] = L
        on = sorted(preps & offered)
        rows.append(dict(t=t, preps_on_offer=[(c[:28], "pool" if any((concept_of(i) or i) == c for i in m.pool) else ("settled" if m.boxes.get(c, {}).get("settled") else "out"), reach.get(c, -1)) for c in on],
                         how=how["v"], top=[i[:30] for i in rec["levels"][-1]["winners"][:4]]))
print("wants met:", len(a.reached), "last at", a.reached[-1][0] if a.reached else None)
print("setup moves known:", len(preps), sorted(x[:28] for x in preps))
print("episode starts traced:", len(rows), "; how the first move was chosen:", dict(collections.Counter(r["how"][0] if r["how"] else None for r in rows)))
for r in rows[:6] + rows[len(rows) // 2: len(rows) // 2 + 4] + rows[-6:]:
    print(r)
