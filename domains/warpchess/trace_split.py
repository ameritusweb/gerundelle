"""Trace (LADDER.md, rung 2): the king's route that held the plan in seed 5 with piece minds. Was it seen as conflated, was it split, and what
value did the planner give it? Run: python -X utf8 trace_split.py [--seed 5] [--rounds 600]"""
import argparse
import collections
import sys

import rung0  # noqa: F401  (puts Gerundelle on the path)
import offers
import rung2
from duel import WarpDuel
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG2B

plans = []   # (round, the push the plan chose, the value it gave)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=600)
    ap.add_argument("--want-split", action="store_true")
    ap.add_argument("--white", default="pieces")
    args = ap.parse_args()
    real_mcts = offers.mcts
    state = {"r": 0, "who": None}

    def mcts(model, s, prior, **kw):
        a, v = real_mcts(model, s, prior, **kw)
        if model.agent is state["who"]:
            plans.append((state["r"], a, v))
        return a, v
    offers.mcts = mcts

    w = WarpDuel(RUNG2B, seed=args.seed)
    w.actor = "White"
    white = OfferedMainMind(w, pieces=args.white == "pieces", forces=True, side="white", situational=True)
    state["who"] = white
    w.actor = "Black"
    black = OfferedMainMind(w, pieces=True, forces=True, side="black", situational=True)
    for m in (white, black):
        for agent in [m] + list(m.pieces.values()):
            agent.mind.p.want_split = args.want_split
    minds = {"White": white, "Black": black}
    wants = {"White": "standing_white_up", "Black": "standing_black_up"}
    for r in range(args.rounds):
        state["r"] = r
        side = "White" if w.board.turn else "Black"
        w.actor = side
        a = minds[side]
        for _ in range(rung2.TURN_STEPS):
            if a.goal is None:
                a.goal = wants[side]
            n = len([x for x in w.log if x[2]])
            a.tick()
            if len([x for x in w.log if x[2]]) > n:
                break
        other = "Black" if side == "White" else "White"
        w.actor = other
        minds[other].tick()

    meta, goal = white.mind.meta, "standing_white_up"
    print("want_split", args.want_split)
    print("White's splits on the king:", {c: sp["tag"] for c, sp in meta.splits.items() if "white_king" in c})
    print(f"White's main mind: {len(white.pushed)} pushes lived, wants met {len(white.reached)}, splits {len(meta.splits)}")
    chosen = collections.Counter(a for _, a, v in plans if v > 0)
    print("\nThe planner's choices with a value above 0 (late half):", collections.Counter(a for r, a, v in plans if v > 0 and r >= args.rounds // 2).most_common(6))
    print("\nPushes the plan chose, and what the mind's records say of them:")
    for c, n in chosen.most_common(8):
        readings = [x for x in meta.modes if x == c or x.startswith(c + "|")]
        print(f"  {c}: chosen {n} times; split: {c in meta.splits}" + (f" on {meta.splits[c]['tag']}" if c in meta.splits else ""))
        for x in readings:
            hist = meta.modes[x]
            k = sum(goal in h[2] for h in hist)
            print(f"      reading {x[len(c):] or '(whole)'}: {len(hist)} tries, brought the want {k} ({k / max(1, len(hist)):.2f}); opposed changes: {meta.opposed(hist)[:4]}")
    print()
    print("Readings where the want came 2+ times and failed 2+ times, and what the split rule finds there:")
    for x, hist in sorted(meta.modes.items()):
        k = sum(goal in h[2] for h in hist)
        if k >= 2 and len(hist) - k >= 2:
            print(f"  {x}: {len(hist)} tries, want {k}; split: {x in meta.splits}" + (f" on {meta.splits[x]['tag']}" if x in meta.splits else "") + f"; want_opposed {meta.want_opposed(hist)}; mode_boundary -> {meta.mode_boundary(hist)}")
            if x not in meta.splits:
                tags = sorted(set().union(*(ctx for _, ctx, _ in hist)))
                best = []
                for c in tags:
                    yes = [goal in m for _, ctx, m in hist if c in ctx]
                    no = [goal in m for _, ctx, m in hist if c not in ctx]
                    if len(yes) >= 1 and len(no) >= 1:
                        best.append((abs(sum(yes) / len(yes) - sum(no) / len(no)), c, f"{sum(yes)}/{len(yes)} vs {sum(no)}/{len(no)}"))
                for b in sorted(best, reverse=True)[:4]:
                    print(f"      {b[1]}: want {b[2]}")
    print()
    print("Splits whose halves differ in the want:")
    for x, sp in meta.splits.items():
        a, b = meta.modes.get(sp["yes"], []), meta.modes.get(sp["no"], [])
        ka, kb = sum(goal in h[2] for h in a), sum(goal in h[2] for h in b)
        if ka or kb:
            print(f"  {x} on {sp['tag']} at t{sp['t']}: want {ka}/{len(a)} with, {kb}/{len(b)} without")
    vals = [v for r, a, v in plans if v > 0 and r >= args.rounds // 2]
    if vals:
        print(f"\nValues the planner gave its late choices: median {sorted(vals)[len(vals) // 2]:.3f}, max {max(vals):.3f}, n {len(vals)}")


if __name__ == "__main__":
    main()
