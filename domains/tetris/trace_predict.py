"""Trace Params.force_predictions in the tetris mind (run.py's setup, luck 0.7): the prediction SOVs made, confirmed and rejected, what
they were linked to, and what the SOV holds for the pushes and the potential effects. Run: python -X utf8 trace_predict.py [slices]"""
import collections
import sys
import time

import run
from molecules import Params
from potential import ForceMind
from sov_agent import SovAgent
from world import TetrisWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
w = TetrisWorld(seed=0, luck=0.7)
a = SovAgent(w, ForceMind(Params(**run.SWITCHES)))
a.mind.p.acceptance = 6
shown, t0 = 0, time.time()
for t in range(N):
    a.mind.potentials = w.potentials()
    a.tick()
    run.earn_luck(a, w)
    run.own_open_rows(a, w)
    if (t + 1) % 100 == 0:   # progress (first only at a game's end, and with luck the well rarely filled: nothing for 75 minutes)
        now_ = time.time()
        print(f"slice {t + 1}: {now_ - t0:.0f}s, {100 / (now_ - __import__('builtins').__dict__.setdefault('_last', t0)):.2f} slices/s; "
              f"luck {w.luck} ({w.earned} earned), pieces cleared {w.pieces_cleared}, rows {w.lines}, games {len(w.games)}; "
              f"prediction SOVs {len(a.mind.understanding.__dict__.get('prediction_sovs', {}))}, "
              f"answered {len(a.__dict__.get('prediction_answers', []))}, pushes so far {sum(1 for _, _, ok in w.log if ok)}", flush=True)
        __import__('builtins')._last = now_
    while shown < len(w.games):
        shown += 1
        print(f"game {shown}: {w.games[shown - 1][0]} pieces, {w.games[shown - 1][1]} rows; slice {t} ({time.time() - t0:.0f}s)", flush=True)
und = a.mind.understanding
log = a.__dict__.get("prediction_log", [])
print(f"{N} slices ({time.time() - t0:.0f}s); rows cleared {w.lines}; prediction SOVs {len(und.__dict__.get('prediction_sovs', {}))}")
print("answered:", collections.Counter((o, by.split('_push')[0]) for _, _, o, by in log))
sovs = und.prediction_sovs
print("prediction SOVs by how often they came up:", sorted((len(v["instances"]) for v in sovs.values()), reverse=True)[:10])
for t_, pid, o, by in log[:12]:
    print(f"  slice {t_}: {pid} ({len(sovs[pid]['forces'])} forces) {o}, linked to {by}")
f = lambda e: round(e[0] + e[2] + 0.5 * e[1], 2)
for c in sorted(k for k in und.rel if k.endswith("_push:piece_falling")) + ["wait"]:
    print(c.split("_push")[0], "->", {k: f(v) for k, v in und.rel.get(c, {}).items() if k[1].startswith("potential:")})
for c in sorted(k for k in und.rel if k.startswith("potential:")):
    print(c, {k: f(v) for k, v in und.rel[c].items() if not k[1].startswith("prediction:")}, "| from", sum(1 for k in und.rel[c] if k[1].startswith("prediction:")), "prediction SOVs")
abs_ = [x for x in und.abstracts if any("prediction:" in v for m in x["members"] for v in m.values())]
print("rows cleared", w.lines, "| pieces cleared", w.pieces_cleared, "| luck", w.luck, "earned", w.earned, w.luck_log[:8])
print("abstracts over prediction SOVs:", len(abs_))
for x in abs_[:6]:
    m0 = x["members"][0]
    print(" ", x["id"], "members", len(x["members"]), "| pattern:", sorted((r, und.kind(m0[a]), und.kind(m0[b])) for r, a, b in x["pattern"]))
print("belied (self-told ways the world refuted):", len(und.belied), [b for b in und.belied if b[1] == "self"][:6])
print("told links to potential effects now:", {(c.split("_push")[0], o): round(e[1], 2) for c in und.rel for (r, o), e in und.rel[c].items() if r == "causes" and o.startswith("potential:") and not c.startswith("prediction:")})
terr = a.mind.territory
for r, row in sorted(terr.rows.items()):
    if r.startswith("potential_"):
        print("owned prediction", r, "| now", row["holder"], "| history", row["history"][:12])
print("lost slots on predictions:", sorted((k, r) for k, r in terr.open_slots() if r.startswith("potential:")))
print("pushes per 1000 slices:", [sum(1 for tt, _, ok in w.log if ok and b <= tt < b + 1000) for b in range(0, N, 1000)])
print("luck by 1000 slices:", [min([l for tt, l in w.luck_log if tt < b + 1000] or [0.7]) for b in range(0, N, 1000)], "| made clears at", w.__dict__.get("made_log", [])[:20])
print("anti-wants:", a.__dict__.get("anti_log", []), "| held now:", a.__dict__.get("anti"))
