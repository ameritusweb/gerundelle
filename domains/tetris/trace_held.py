"""Trace Params.held_evidence in the tetris mind (run.py's setup, luck 0.7): each game, then what the SOV holds linking the pushes, the
alignment gerund and the rows coming apart. Run: python -X utf8 trace_held.py [slices]"""
import collections
import sys
import time

import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
w = TetrisWorld(seed=0, luck=0.7)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
cleared, shown, t0 = collections.Counter(), 0, time.time()
for t in range(N):
    a.mind.potentials = w.potentials()
    before = {y for y in range(w.height) if w.shown.get(f"row_{y}") == "coming_apart"}
    a.tick()
    for y in range(w.height):
        if w.shown.get(f"row_{y}") == "coming_apart" and y not in before:
            cleared[f"row_{y}"] += 1
    while shown < len(w.games):
        shown += 1
        print(f"game {shown}: {w.games[shown - 1][0]} pieces, {w.games[shown - 1][1]} rows; slice {t} ({time.time() - t0:.0f}s)", flush=True)
und = a.mind.understanding
f = lambda e: round(e[0] + e[2] + 0.5 * e[1], 2)
print("rows cleared, each:", dict(sorted(cleared.items())))
late = und.__dict__.get("late", {})
print("came later while aligning held (times):", sorted(((n, y) for y, n in late.get("piece_alignment_aligning", {}).items()), reverse=True)[:12])
print("aligning:", {k: f(v) for k, v in und.rel.get("piece_alignment_aligning", {}).items() if k[0] != "enables"})
for c in sorted(k for k in und.rel if k.endswith("_coming_apart") and k.startswith("row_")):
    print(c, {k: f(v) for k, v in und.rel[c].items()})
for c in sorted(k for k in und.rel if k.endswith("_push:piece_falling")):
    print(c.split("_push")[0], "->", {k: f(v) for k, v in und.rel[c].items() if "alignment" in k[1] or "coming_apart" in k[1]})
print("territory rows:", collections.Counter(row["holder"] for r, row in a.mind.territory.rows.items() if r.startswith("row_")))
ca = und.__dict__.get("concept_abstracts", [])
print("concept abstracts:", len(ca))
for x in ca:
    c = x["center"]
    cs = [m[c] for m in x["members"]]
    if any(k.startswith("row_") for k in cs) or len(cs) >= 4:
        print(" ", x["id"], sorted(x["pattern"]), "| members:", cs[:10], "| shared:", {r: v for r, v in x["members"][0].items() if r != c})
