"""Rung 1e: convergence in the agent's own choice (Gerundelle Params.converge).

Rung 1d's attempt loop noticed the mate a position's constraints converged on; here the same noticing is inside
SovAgent's choice: a want with no known way, in a world that says what a push would meet (`ChessWorld.relations_of`),
notices the untried push the constraints from its own failed pushes converge on, before sub-wants and experiments. The
mind is rung 1c's (polarity and sub-wants on), wanting the game mated, on rung 1d's positions (a sequence of new
positions, each mate-in-one, the next after a mate); Black's reply is perceived (`reply`), and is what a failure's kind
is read from.

Measured: pushes to the mate in each position, with Params.converge off and on.

Run: python -X utf8 rung1e.py [--seeds 10] [--positions 20] [--ticks 4000] [--arms base,converge]
"""
import argparse
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import rung1d  # noqa: E402
from chessworld import ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

WANT = "game_mate"
ARMS = {"base": dict(polarity=True, subwants=True), "converge": dict(polarity=True, subwants=True, converge=True),
        "full": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True),
        "bridge": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True, bridge=True)}


def run(seed, arm, n, ticks):
    fens = rung1d.positions(1000 + seed, n)
    w = ChessWorld(fens, order=seed, reply="answer", moves=1, relations=("reply", "game"), sequence=True)
    m = GerundelleMind("White", w, want=WANT, want_count=10 ** 6)
    for k, v in ARMS[arm].items():
        setattr(m.agent.mind.p, k, v)
    per, act = [0] * n, w.act

    def logged(inv=None, hold=False):
        if inv is not None and w.at < n:
            per[w.at] += 1
        return act(inv, hold)
    w.act = logged
    for _ in range(ticks):
        m.step(len(m.agent.tried))
        if w.at >= n - 1 and w.mated:
            break
    done = w.at + (1 if w.mated else 0)
    return per[:done], done, len(m.agent.noticed), m


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--positions", type=int, default=20)
    ap.add_argument("--ticks", type=int, default=4000)
    ap.add_argument("--arms", default="base,converge")
    args = ap.parse_args()
    half = args.positions // 2
    for arm in args.arms.split(","):
        t0, later, firsts, done_all = time.time(), [], 0, []
        for k in range(args.seeds):
            t1 = time.time()
            per, done, noticed, m = run(k, arm, args.positions, args.ticks)
            done_all.append(done)
            later += per[half:]
            firsts += sum(1 for x in per[half:] if x == 1)
            print(f"  {arm} seed {k}: positions mated {done}/{args.positions}; pushes per position {per}; noticed "
                  f"{noticed}  {time.time() - t1:.0f}s", flush=True)
        print(f"{arm:9} positions mated {sum(done_all)}/{args.seeds * args.positions}; second half pushes mean "
              f"{statistics.mean(later) if later else float('nan'):.2f} (median {statistics.median(later) if later else '-'}); "
              f"mated at the first push {firsts}/{len(later)}  {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
