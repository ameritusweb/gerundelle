"""Rung 7 ablations: the author's moves on offer x whether the reserves show. For each, the best story by
held entropy, and the best per ending."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung7  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
print(f"{'moves':14} {'signs':5} {'n':>4}  {'ending':9} {'value':>6} {'held':>6} {'peak':>5} {'exp':>5} {'rise':>6}  best story")
for moves in (("away", "help"), ("help",), ("away",), ()):
    for signs in (True, False):
        rung7.MOVES, rung7.SIGNS = moves, signs
        leaves = rung7.forest()
        rows = rung7.search(leaves)
        best = {}
        for r in rows:
            best.setdefault(r["ending"], r)
        for k, (e, r) in enumerate(sorted(best.items(), key=lambda kv: -kv[1]["value"])):
            s = r["state"]
            print(f"{'+'.join(moves) or 'none':14} {str(signs):5} {len(leaves) if k == 0 else '':>4}  {e:9} {r['value']:6.3f} {r['held']:6.3f} "
                  f"{r['peak']:5.2f} {r['expected_before']:5.2f} {r['rise']:6.2f}  cast {s.cast} moves {s.moves}")

print()
rung7.MOVES, rung7.SIGNS = ("away", "help"), True
for ev in (0.02, 0.04, 0.08, 0.16):
    rung7.EVENT = ev
    rows = rung7.search(rung7.forest())
    r = rows[0]
    print(f"EVENT {ev:4.2f}: best {r['ending']} cast {r['state'].cast} moves {r['state'].moves} value {r['value']} "
          f"held {r['held']} rise {r['rise']} drops {r['drops']}")
