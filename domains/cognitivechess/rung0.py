"""Rung 0 (chess-sov-plan.md): win the hanging piece. One want (material up), the world pushing back, no reply.

The mind is Gerundelle (E:/vscode/analogy/molecules, SovAgent, read into beats by fiction's GerundelleMind), unchanged.
Measured over seeded orders of the moves (the fair test: ties among equal pushes are not broken by a move's name), and
with both winning moves last in Gerundelle's order: tries to the want, against plain enumeration (each move once, in
the same order) and a random mover (a legal move uniformly at random, with repeats).

Run: python -X utf8 rung0.py [--seeds 10] [--ticks 400] [--beats SEED]
"""
import argparse
import os
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

from chessworld import RUNG0, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402  (fiction's; puts Gerundelle on the path)

WANT = "material_up"
WINS = ("Rxd5", "Bxf6")


def gerundelle(order, last=(), ticks=400):
    w = ChessWorld(RUNG0, order=order, last=last)
    m = GerundelleMind("White", w, want=WANT)
    m.run(ticks)
    tries, won = 0, None
    for _, inv, names in m.agent.tried:
        tries += 1
        if WANT in names:
            won = inv[0].split(" ", 1)[-1]
            break
    return dict(reached=bool(m.agent.reached), tries=tries, won=won, mind=m, world=w)


def enumeration(order, last=()):
    w = ChessWorld(RUNG0, order=order, last=last)
    labels = [i[0].split(" ", 1)[-1] for i in w.invitations()]
    return 1 + min(labels.index(s) for s in WINS)


def random_mover(order):
    w = ChessWorld(RUNG0)
    moves = [i[0] for i in w.invitations()]
    rng, n = random.Random(order), 0
    while True:
        n += 1
        if rng.choice(moves) in WINS:
            return n


def summary(xs):
    xs = sorted(xs)
    return f"median {statistics.median(xs):g}, range {xs[0]}-{xs[-1]}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--beats", type=int, default=None, help="print the beats of one seed's run")
    args = ap.parse_args()
    n = len(ChessWorld(RUNG0).invitations())
    print(f"legal moves {n}; winning {len(WINS)} ({', '.join(WINS)})")
    for case, last in (("shuffled", ()), ("winners last", WINS)):
        t0, rows = time.time(), [gerundelle(k, last, args.ticks) for k in range(args.seeds)]
        ok = [r["tries"] for r in rows if r["reached"]]
        print(f"\n{case}")
        print(f"  gerundelle    reached {len(ok)}/{len(rows)}  tries {summary(ok) if ok else '-'}  "
              f"won by {sorted(r['won'] for r in rows if r['won'])}  {time.time() - t0:.0f}s")
        print(f"  enumeration   tries {summary([enumeration(k, last) for k in range(args.seeds)])}")
        if not last:
            print(f"  random mover  tries {summary([random_mover(k) for k in range(args.seeds)])}")
        for k, r in enumerate(rows):
            sp = {x: s["tag"] for x, s in r["mind"].agent.mind.meta.splits.items()}
            print(f"    seed {k}: tries {r['tries']:3}  won {r['won']}  ticks {r['world'].t}  splits {sp}")
    if args.beats is not None:
        r = gerundelle(args.beats, (), args.ticks)
        for b in r["mind"].beats:
            print(f"  t{b.t:<4} {b.kind:8} {b.obj:22} {b.detail}")


if __name__ == "__main__":
    main()
