"""Does Gerundelle's planner matter in the code world? Rung 0 of cognitivecode on Gerundelle, with the invitation's
gerund the slot's state (so a fill's configuration is a fact and the planner has actions) against the recorded run with
the fixed 'slot' (cognitivecode/logs/arms0.log: tries median 125, 46-157). Nothing in cognitivecode is changed: the
world's invitations are patched here only.

Run: python -X utf8 code_planner.py [--seeds 10] [--fixed]
"""
import argparse
import os
import statistics
import sys
import time

CODE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cognitivecode")
sys.path.insert(0, CODE)
os.chdir(CODE)

import codeworld  # noqa: E402
import arms0  # noqa: E402


def stated(self, tree=None):
    st = self.states()
    out = [(label, s, st[s]) for s, fills in self._fills.items() for label in fills]
    return sorted(out) + [("run", self.spec, "passing" if self.passing else "failing")]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=1200)
    ap.add_argument("--fixed", action="store_true", help="the world as it is (the fixed 'slot'), under today's Gerundelle")
    args = ap.parse_args()
    if not args.fixed:
        codeworld.CodeWorld.invitations = stated
    t0, rows = time.time(), []
    for k in range(args.seeds):
        rows.append(arms0.gerundelle(k, {}, args.ticks))
        print(f"  seed {k}: reached {rows[-1][0]} tries {rows[-1][1]} runs {rows[-1][2]}", flush=True)
    ok = sorted(t for r, t, _ in rows if r)
    print(f"{'fixed slot' if args.fixed else 'slot state'} as gerund: reached {len(ok)}/{len(rows)}  tries median {statistics.median(ok) if ok else '-'}, "
          f"range {ok[0] if ok else '-'}-{ok[-1] if ok else '-'}  {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
