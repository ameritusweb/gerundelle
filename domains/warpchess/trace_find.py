"""Trace (LADDER.md, rung 1g, every switch): seeds that found the crossing with the switches off and never with them on. Per 200 slices: how
moves were chosen, how many distinct moves were tried; and every slice where a move that would take the knight was on offer: what was chosen
instead, and how. Run: python -X utf8 trace_find.py SEED [on|off] [pieces]"""
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld

sys.stdout.reconfigure(encoding="utf-8")
SEED, ON, PIECES = int(sys.argv[1]), sys.argv[2] == "on", len(sys.argv) > 3 and sys.argv[3] == "pieces"
w = WarpWorld(RUNG1_TWO, seed=SEED, moves=2, forces=True)
a = OfferedMainMind(w, pieces=PIECES, forces=True)
for ag in [a] + list(a.pieces.values()):
    ag.mind.p.imagined_tournament = ag.mind.p.want_site = ag.mind.p.setup_support = ON
m = a.mind
how = {"v": None}
planned, winner, did = a.planned, a.winner, m.inquiry.did
def p(invs):
    s = planned(invs)
    if s is not None: how["v"] = "plan"
    return s
def wn(rec, invs):
    s = winner(rec, invs)
    if s is not None: how["v"] = "attention"
    return s
def d(eid):
    how["v"] = "experiment"
    return did(eid)
a.planned, a.winner, m.inquiry.did = p, wn, d
per = collections.defaultdict(collections.Counter)
tried = collections.defaultdict(set)
chances = []
for t in range(1000):
    if a.goal is None:
        a.goal = WANT
    caps = [lab for lab, mv in w.offers().items() if w.board.pieces[mv.final_square] or w.board.pieces[mv.to_square]] if w.board.turn else []
    knight = [lab for lab in caps if "Rd4" in lab]
    n = len([x for x in w.log if x[2]])
    how["v"] = None
    out = a.tick()
    moved = len([x for x in w.log if x[2]]) > n
    per[t // 200][how["v"] if moved else ("watching" if a.watching and not moved else "no move")] += 1
    if moved:
        tried[t // 200].add(w.log[-1][1])
    if knight and a.watching is None or (knight and moved):
        chances.append((t, knight[:2], w.log[-1][1] if moved else None, how["v"]))
print(f"seed {SEED} switches {'on' if ON else 'off'} {'pieces' if PIECES else 'alone'}: wants met {len(a.reached)}, first {a.reached[0][0] if a.reached else None}")
for k in sorted(per):
    print(f"  {k*200}-{k*200+199}: {dict(per[k])}; distinct moves tried {len(tried[k])}")
print(f"  slices with a knight capture on offer: {len(chances)}")
for c in chances[:10]:
    print("   ", c)
