"""The author's search (rung 6): how the setup is told (not at all, in passing, emphasized) x how long until
the payoff scene (the gap), each configuration run end to end and scored by the reader mind. The first
choice the ladder searches at the level of the story rather than of a mind's push.

Run: python tools/author_search.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_ladder import CONFIGS, RUNGS, compose  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    spec = RUNGS[6]
    rows = []
    for plant in ("none", "passing", "emphasized"):
        for gap in (10, 40, 120):
            name = f"search-{plant}-{gap}"
            CONFIGS[name] = ("lean", {"_plant": plant, "_gap": gap})
            _, scene, sentences, m = compose(name, spec, 200)
            r = m["reader"]
            rows.append((plant, gap, len(sentences), m["round_trip"], r["memorability"], r["satisfaction"], r["deus"],
                         r["debt"], any(p.kind == "recall" for p in scene.plans)))
    print(f"{'plant':11} {'gap':>4} {'sents':>5} {'trip':>5} {'recall':>6} {'memor':>6} {'satis':>6}  deus  debt")
    for plant, gap, n, trip, mem, sat, deus, debt, rec in rows:
        print(f"{plant:11} {gap:4d} {n:5d} {trip:5.2f} {str(rec):>6} {mem:6.3f} {sat:6.3f}  {str(deus):5} {debt}")
    ok = [r for r in rows if r[3] == 1.0 and not r[6]]
    best = max(ok, key=lambda r: (r[5], -r[2]))
    print(f"\nchosen: plant {best[0]}, gap {best[1]} (satisfaction {best[5]:.3f})")


if __name__ == "__main__":
    main()
