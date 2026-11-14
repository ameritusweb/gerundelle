"""Does today's Gerundelle speed work (analogy/DRIFT.md, "Speed, and Abstract's input") make tetris faster? (the user, 2026-11-13: "should
that make tetris faster too?", "yes, run it"). Replays slices from a clean5 checkpoint (nothing saved) and records, per slice: the time,
Abstract's time (Understanding.analogize), and the mind's choice. The mode is set before Gerundelle is imported, so each mode runs in its
own process (bench_abstract_all.py runs them together):
  base         the code clean5 ran (clean5_code/, before today's changes; with_clean5_code.py's way)
  now_full     today's code, the full scans (GERUNDELLE_FULL_EDGES=1)
  now          today's code, the edge cache
  now_check    the edge cache checked against the full scans every call (GERUNDELLE_EDGE_CHECK=1)
  now_affords  the edge cache and Params.affords_relation (its affordances relabelled; polarity must be off)
Run: PYTHONHASHSEED=0 python -u -X utf8 bench_abstract.py <mode> <checkpoint> <slices> <out.json>"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
mode, ckpt, N, out_path = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
if mode == "now_full":
    os.environ["GERUNDELLE_FULL_EDGES"] = "1"
if mode == "now_check":
    os.environ["GERUNDELLE_EDGE_CHECK"] = "1"
if mode == "base":   # (with_clean5_code.py: clean5's molecules.py and sov_agent.py, cached first)
    sys.path.insert(0, __import__("paths").GERUNDELLE)
    sys.path.insert(0, os.path.join(HERE, "clean5_code"))
    import molecules  # noqa: E402
    import sov_agent  # noqa: E402,F401
    assert molecules.__file__.startswith(os.path.join(HERE, "clean5_code")), molecules.__file__
sys.path.insert(0, HERE)
import checkpoint  # noqa: E402
import run  # noqa: E402
import molecules  # noqa: E402
from force_world import inv_id  # noqa: E402

a, w, start = checkpoint.load(ckpt)
for k, v in run.SWITCHES.items():
    if hasattr(a.mind.p, k):
        setattr(a.mind.p, k, v)
moved = 0
if mode == "now_affords":
    assert not a.mind.p.polarity
    a.mind.p.affords_relation = True
    und = a.mind.understanding
    for store in (und.rel, und.__dict__.get("dormant_rel") or {}):
        for c, rels in store.items():
            for key in [k for k in rels if k[0] == "enables"]:
                rels[("affords", key[1])] = rels.pop(key)
                moved += 1
abstract_time = [0.0]
real = molecules.Understanding.analogize


def timed(self, rec):
    t0 = time.perf_counter()
    try:
        return real(self, rec)
    finally:
        abstract_time[0] += time.perf_counter() - t0


molecules.Understanding.analogize = timed
rows = []
for t in range(start, start + N):
    a.mind.potentials = w.potentials()
    abstract_time[0] = 0.0
    t0 = time.perf_counter()
    choice, rec = a.tick()
    dt = time.perf_counter() - t0
    run.after_tick(a, w)
    rows.append(dict(t=t, seconds=round(dt, 4), abstract=round(abstract_time[0], 4),
                     choice=inv_id(choice) if choice is not None and choice[0] != "commit" else (choice[1] if choice else None)))
links = len(a.mind.understanding.edges_full()) if hasattr(a.mind.understanding, "edges_full") else len(a.mind.understanding.edges())
json.dump(dict(mode=mode, start=start, rows=rows, relabelled=moved, links=links, pieces=w.placed, games=len(w.games)),
          open(out_path, "w", encoding="utf-8"))
tot, ab = sum(r["seconds"] for r in rows), sum(r["abstract"] for r in rows)
print(f"{mode}: {N} slices from {start}: {tot:.0f}s ({tot / N:.2f}s a slice); Abstract {ab:.0f}s ({100 * ab / max(tot, 1e-9):.0f}%); "
      f"links Abstract reads {links}; relabelled {moved}", flush=True)
