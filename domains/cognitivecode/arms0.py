"""Rung 0 on both arms, on the same world and the same orders of the fills: the lean code mind (CodeMind) and
Gerundelle (fiction's GerundelleMind, its SovAgent in a CodeWorld). Tries to the spec passing, per seed.

Run: python -X utf8 arms0.py [--seeds 10] [--ticks 1200]
"""
import argparse
import sys
import time

import rung0
from gerundelle_arm import GerundelleMind  # noqa: E402  (fiction's, on the path codeworld set)


def lean(order, where, ticks):
    w = rung0.world(order=order, **where)
    m = rung0.run(w, ticks)
    tries = [b for b in m.beats if b.kind == "try"]
    return any(b.kind == "reach" for b in m.beats), len(tries), sum(1 for b in tries if b.obj == "spec")


def gerundelle(order, where, ticks):
    w = rung0.world(order=order, **where)
    m = GerundelleMind("Code", w, want="spec_passing")
    m.run(ticks)
    t = m.agent.tried
    return bool(m.agent.reached), len(t), sum(1 for _, i, _ in t if i[1] == "spec")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=1200)
    ap.add_argument("--worst-only", action="store_true")
    args = ap.parse_args()
    cases = (("shuffled", {}), ("answer last for lean (rank 000)", {"last": "v2[v4]"}),
             ("answer last for Gerundelle (rank 158)", {"first": "v2[v4]"}))
    for name, where in cases[1:] if args.worst_only else cases:
        for arm, fn in (("lean", lean), ("gerundelle", gerundelle)):
            t0, rows = time.time(), []
            for k in range(args.seeds):
                rows.append(fn(k, where, args.ticks))
            ok = sorted(t for r, t, _ in rows if r)
            runs = sorted(n for _, _, n in rows)
            med = f"{ok[len(ok) // 2]}, {ok[0]}-{ok[-1]}" if ok else "-"
            print(f"{name:38} {arm:11} reached {len(ok)}/{len(rows)}  tries (median, range) {med:>14}  "
                  f"runs (median) {runs[len(runs) // 2]:>3}  {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
