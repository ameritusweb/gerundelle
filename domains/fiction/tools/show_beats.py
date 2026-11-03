"""Print an arm's beats for a rung (a development readout).

Run: python tools/show_beats.py [--rung 1] [--config lean] [--ticks 200] [--all]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_ladder import RUNGS, run_arm  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", type=int, default=1)
    ap.add_argument("--config", default="lean")
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--all", action="store_true", help="include see and change beats")
    args = ap.parse_args()
    beats, world = run_arm(args.config, RUNGS[args.rung], args.ticks)
    print(f"{len(beats)} beats, world tick {world.t}")
    for i, b in enumerate(beats):
        if args.all or b.kind not in ("see", "change"):
            detail = {k: v for k, v in b.detail.items() if k != "unexpected"}
            print(f"  {i:3d} t{b.t:<4d} {b.actor:5} {b.kind:9} {b.obj:8} {b.hole:28} {detail} pull {b.pull:.2f} refs {b.refs}")


if __name__ == "__main__":
    main()
