"""Trace the SOV of the tetris mind (run.py's setup) after N slices: the gerund's arrivals and relations, what the SOV holds for the rows,
the pushes and the wants set, and what questions it has open. Run: python -X utf8 trace_sov.py [slices]"""
import collections
import sys

import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
w = TetrisWorld(seed=0)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
align, fullest = collections.Counter(), 0
for t in range(N):
    a.mind.potentials = w.potentials()
    a.tick()
    align[w.shown["piece_alignment"]] += 1
    fullest = max(fullest, max(w.row_load(y) for y in range(w.height)))
und = a.mind.understanding


def show(c, k=12):
    rels = und.rel.get(c, {})
    out = sorted(((r, o, tuple(round(x, 2) for x in f)) for (r, o), f in rels.items()), key=lambda x: -sum(x[2]))
    return f"{c}: {len(rels)} relations, level {und.level(c):.2f}, open {und.open_slots(c)}\n      " + "\n      ".join(map(str, out[:k]))


print(f"slices {N}; piece_alignment read {dict(align)}; the fullest row held {fullest} of {w.width} blocks")
print("arrivals of the gerund:", {k: v for k, v in und.arrivals.items() if "alignment" in k})
for c in ("piece_alignment_aligning", "piece_alignment_straying"):
    print(" ", show(c, 6))
print("pushes:")
for c in sorted({k for k in und.rel if k.endswith("_push:piece_falling")}):
    print(" ", show(c, 8))
rows = sorted(k for k in und.rel if k.startswith("row_"))
print("row concepts in the SOV:", len(rows), rows[:12])
for c in [r for r in rows if "coming_apart" in r][:3]:
    print(" ", show(c, 6))
wants = collections.Counter(g for _, g, k in a.sub_log if k == "set")
print("wants set:", wants.most_common(5))
for g, _ in wants.most_common(2):
    print(" ", show(g, 8))
print("questions open:", collections.Counter(q.split(":")[1] + " " + q.split(":", 2)[2].split("_")[0] for q in und.questions).most_common(8))
print("splits:", {k: (sp.get("cands") and sorted(sp["cands"])) or sp["tag"] for k, sp in a.mind.meta.splits.items()})
