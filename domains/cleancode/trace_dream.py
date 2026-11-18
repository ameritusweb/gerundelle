"""What the in-problem dreams did on rung 0, seed 0, problem 2 (start adding_1, correct subtracting_1; never settled, with or without
dreams, 2026-11-14). For each dream in the problem: when, about what, which wheel settings its trials stood on, and whether any trial
showed every test passing; then, at the end of the problem: the imagined `causes test_*_passing` links the mind holds and from which
pushes, the stucks that ran no dream and why, and the wants set in the problem.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_dream.py [last slice]"""
import collections
import sys

import graph as g
import run

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 335
a, w = run.build("0", 0, dream=True)
und = a.mind.understanding
dreamed_at = 0
for t in range(N):
    a.mind.potentials = w.potentials()
    n_dreamed = len(a.dreamed)
    a.tick()
    run.give(a, w)
    if w.problems != 2:
        dreamed_at = len(a.dreamed)
        continue
    if len(a.dreamed) > n_dreamed:
        new = a.dreamed[n_dreamed:]
        settings = collections.Counter(next((f.split("conn_0_", 1)[1] for f in facts if f.startswith("conn_0_")), "?") for _, facts, _ in new)
        passing = [(inv[0], next((f for f in facts if f.startswith("conn_0_")), "?")) for inv, facts, names in new
                   if sum(1 for n in names if n.startswith("test_") and n.endswith("_passing")) == len(w.p.tests)]
        about = a.dreams_done[-1][1] if a.__dict__.get("dreams_done") else "?"
        print(f"slice {t + 1} at {w.p.shape.doing(0, w.pos[0])}: dream about {about[:70]}: {len(new)} trials on {dict(settings)}; "
              f"all tests passing after {passing[:4]}")
print("imagined links to a test passing:")
for c, rels in und.__dict__.get("imagined", {}).items():
    for (k, o), n in rels.items():
        if k == "causes" and o.startswith("test_") and o.endswith("passing"):
            print("   ", c, "->", o, n)
print("stucks with no dream run:", collections.Counter(why for _, _, why in a.__dict__.get("dreams_not_run", [])))
print("  e.g.", [c[:60] for _, c, _ in a.__dict__.get("dreams_not_run", [])[:4]])
print("wants set in the run:", collections.Counter(x for tt, x, k in a.sub_log if k == "set").most_common(8))
