"""Rung 2 (chess-sov-plan.md, "Feedback: Stockfish as coach and opponent"): told knowledge, at half weight.

The mind is rung 1e's "full" one (polarity, sub-wants, converge, sub_cost, sub_yield, sub_tested). A coach is present.
When the mind holds its want, has no way to it (the planner finds none), and is neither serving a sub-want nor running an
experiment, it asks the coach, once per situation. The coach's answer is its best move, told as the way to the want: it
enters Gerundelle's register as a told receipt (`causes`, told, the teller named), the planner believes it as far as the
mind's credulity goes, and Gerundelle's own refutation takes it back when the world contradicts it (SovAgent.watch: "a
told way the world contradicts"). The mind's own records come first: a move tried here before is read off them.

A named choice: the asking lives in this arm, not in fiction's `consult` (which asks only about pushes on the wanted
object; here the wanted objects, `game` and `material`, are never pushed).

Coaches (the plan's configurations): none (alone); Stockfish 15.1 at depth 8; Stockfish at depth 1 (honestly wrong at
times); an ignorant coach (a legal move at random: that the gain is the knowledge, not being told).

Worlds: rung 1e's sequence of new positions (each mate-in-one); rung 1's defender (Black's reply perceived), where
Stockfish's best move in the defended position, Bxb7, is a means, not a way: told as the way to material, it is refuted
at once.

Withdrawal (the plan: "what survives when the coach is removed is the mind's own"): the coach leaves halfway.

Run: python -X utf8 rung2.py [--world 1e|1] [--seeds 10] [--coaches none,stockfish8,stockfish1,ignorant] [--withdraw]
"""
import argparse
import os
import random
import statistics
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import chess  # noqa: E402
import chess.engine  # noqa: E402
import rung1  # noqa: E402
import rung1d  # noqa: E402
import rung1e  # noqa: E402
from chessworld import RUNG1, ChessWorld, open_engine  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from force_world import inv_id  # noqa: E402

FULL = rung1e.ARMS["full"]


class Coach:
    """Answers "what should I play here?" with a move it chooses: Stockfish at a depth, or a legal move at random."""

    def __init__(self, kind, seed=0):
        self.kind, self.name, self.engine = kind, f"coach ({kind})", None
        self.rng = random.Random(seed)

    def best(self, world):
        offered = {i[0].split(" ", 1)[-1]: i for i in world.invitations()}
        if not offered:
            return None
        if self.kind == "ignorant":
            return offered[self.rng.choice(sorted(offered))]
        if self.engine is None:
            self.engine = open_engine()
        board = chess.Board(world.board.fen())   # the position only (its history holds the passes)
        depth = int(self.kind.replace("stockfish", ""))
        move = self.engine.play(board, chess.engine.Limit(depth=depth)).move
        return offered.get(board.san(move).rstrip("+#")) if move else None

    def close(self):
        if self.engine is not None:
            self.engine.quit()
            self.engine = None


def coached(m, coach, log):
    """Wrap the agent's choice: ask the coach when the mind has no way to its want (once per situation)."""
    a, asked, orig = m.agent, set(), m.agent.planned
    und = a.mind.understanding

    def planned(invs):
        if coach[0] is not None and a.goal is not None and not a.stack and not a.queue and not a.running:
            key = (a.goal, a.facts_now())
            if key not in asked and a.plan_step(invs) is None:
                asked.add(key)
                inv = coach[0].best(m.world)
                if inv is not None:
                    c = inv_id(inv)
                    und.add(c, "causes", a.goal, "told", 1.0)
                    und.tellers[(c, "causes", a.goal)] = coach[0].name
                    a.known.setdefault(c, inv)
                    log.append((a.mind.t, "told", inv[0].split(" ", 1)[-1]))
        return orig(invs)
    a.planned = planned


def world_for(kind, seed, n):
    if kind == "1e":
        return ChessWorld(rung1d.positions(1000 + seed, n), order=seed, reply="answer", moves=1,
                          relations=("reply", "game"), sequence=True), "game_mate"
    return ChessWorld(RUNG1, order=seed, seed=seed, reply="recapture", moves=2, relations=("reply",)), rung1.WANT


def run(kind, seed, coach_kind, ticks, n=20, withdraw=False, bridge=False):
    w, want = world_for(kind, seed, n)
    m = GerundelleMind("White", w, want=want, want_count=10 ** 6)
    for k, v in dict(FULL, bridge=bridge).items():
        setattr(m.agent.mind.p, k, v)
    coach = [Coach(coach_kind, seed) if coach_kind != "none" else None]
    told = []
    coached(m, coach, told)
    halves, start, act = [], 0, w.act
    wins = []   # (tick, configuration or position) of each want met

    def logged(inv=None, hold=False):
        ev = act(inv, hold)
        if any(e.startswith("game:") and e.endswith("-> mate") for e in ev) or "material: even -> up" in ev:
            wins.append((m.agent.mind.t, w.at if kind == "1e" else w.config))
        return ev
    w.act = logged
    try:
        for half in (0, 1):
            if half == 1 and withdraw and coach[0] is not None:
                coach[0].close()
                coach[0] = None
            for _ in range(ticks // 2):
                m.step(len(m.agent.tried))
                if kind == "1e" and w.at >= n - 1 and w.mated:
                    break
            halves.append(len(wins) - start)
            start = len(wins)
    finally:
        if coach[0] is not None:
            coach[0].close()
        w.close()
    und = m.agent.mind.understanding
    belied = Counter(name for _, name, _ in und.belied)
    return dict(halves=halves, wins=wins, told=len(told), belied=sum(belied.values()), pushes=len(m.agent.tried),
                positions=(w.at + (1 if w.mated else 0)) if kind == "1e" else None,
                defended=sum(1 for _, c in wins if c == 0) if kind == "1" else None)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="1e", choices=("1e", "1"))
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=None)
    ap.add_argument("--coaches", default="none,stockfish8,stockfish1,ignorant")
    ap.add_argument("--withdraw", action="store_true")
    ap.add_argument("--bridge", action="store_true", help="Gerundelle's Params.bridge: constraints to sub-wants")
    args = ap.parse_args()
    ticks = args.ticks or (3000 if args.world == "1e" else 800)
    for ck in args.coaches.split(","):
        t0, rows = time.time(), []
        for k in range(args.seeds):
            r = run(args.world, k, ck, ticks, withdraw=args.withdraw, bridge=args.bridge)
            rows.append(r)
            print(f"  {ck} seed {k}: wants met by half {r['halves']}; told {r['told']}, refuted {r['belied']}; pushes "
                  f"{r['pushes']}" + (f"; positions mated {r['positions']}" if r['positions'] is not None else "")
                  + (f"; defended wins {r['defended']}" if r['defended'] is not None else ""), flush=True)
        h0 = sum(r["halves"][0] for r in rows)
        h1 = sum(r["halves"][1] for r in rows)
        extra = (f"; positions mated {sum(r['positions'] for r in rows)}" if args.world == "1e"
                 else f"; defended wins {sum(r['defended'] for r in rows)}")
        print(f"{ck:11} wants met: first half {h0}, second half {h1}{' (coach gone)' if args.withdraw else ''}; told "
              f"{sum(r['told'] for r in rows)}, refuted {sum(r['belied'] for r in rows)}{extra}  {time.time() - t0:.0f}s",
              flush=True)


if __name__ == "__main__":
    main()
