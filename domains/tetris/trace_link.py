"""Trace why the SOV does or doesn't link "aligning" to the rows coming apart (run.py's setup, luck 0.7, held_evidence and
concept_abstracts on): at each row coming apart, the held evidence for aligning causing it and whether either SOV molecule was in the
pool; over the run, how often each SOV molecule reached a slot; at the end, what the SOV holds. Run: python -X utf8 trace_link.py [slices]"""
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
A = "piece_alignment_aligning"
w = TetrisWorld(seed=0, luck=0.7)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
und, shown, t0 = a.mind.understanding, 0, time.time()
reached = collections.Counter()
f = lambda e: round(e[0] + e[2] + 0.5 * e[1], 2)
for t in range(N):
    a.mind.potentials = w.potentials()
    before = {y for y in range(w.height) if w.shown.get(f"row_{y}") == "coming_apart"}
    c, rec = a.tick()
    for i in rec["reached"]:
        if i.startswith("sov:") and (A in i or "coming_apart" in i):
            reached[i] += 1
    for y in range(w.height):
        r = f"row_{y}_coming_apart"
        if w.shown.get(f"row_{y}") == "coming_apart" and y not in before:
            late = und.__dict__.get("late", {}).get(A, {}).get(r, 0)
            print(f"slice {t}: {r}; times it came while aligning held {late}, arrivals {und.arrivals.get(r, 0)}; evidence {und.evidence(A, r)}; "
                  f"in the pool: sov:aligning {('sov:' + A) in a.mind.pool}, sov:{r} {('sov:' + r) in a.mind.pool}", flush=True)
    while shown < len(w.games):
        shown += 1
        print(f"game {shown}: {w.games[shown - 1][0]} pieces, {w.games[shown - 1][1]} rows; slice {t} ({time.time() - t0:.0f}s)", flush=True)
print("SOV molecules reaching a slot:", dict(reached))
print("aligning:", {k: f(v) for k, v in und.rel.get(A, {}).items() if k[0] in ("causes", "caused_by", "conditioned_by")})
for c in sorted(k for k in und.rel if k.startswith("row_") and k.endswith("_coming_apart")):
    print(c, {k: f(v) for k, v in und.rel[c].items() if k[0] in ("causes", "caused_by", "conditioned_by")})
for c in sorted(k for k in und.rel if k.endswith("_push:piece_falling")):
    print(c.split("_push")[0], "->", {k: f(v) for k, v in und.rel[c].items() if "alignment" in k[1] or "coming_apart" in k[1]})
ca = und.__dict__.get("concept_abstracts", [])
print("concept abstracts:", len(ca), "| with rows:", [(x["id"], [m[x["center"]] for m in x["members"]]) for x in ca if any(m[x["center"]].startswith("row_") for m in x["members"])])
