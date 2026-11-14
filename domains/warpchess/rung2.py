"""Rung 2 (LADDER.md): both sides have minds, on one Warp board. Run: python -X utf8 rung2.py [--seeds 6] [--rounds 600] [--white pieces|alone]"""
import argparse
import statistics
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from duel import WarpDuel
from pieceminds import OfferedMainMind
from warpworld import RUNG2B as RUNG2

TURN_STEPS = 5   # a side's slices to make its move, under the world's IDLE (6)


def play(seed, rounds, white_pieces, patience=None, want_split=False):
    w = WarpDuel(RUNG2, seed=seed)
    w.actor = "White"
    white = OfferedMainMind(w, pieces=white_pieces, forces=True, side="white", situational=True)
    w.actor = "Black"
    black = OfferedMainMind(w, pieces=True, forces=True, side="black", situational=True)
    white.mind.p.patience = patience   # White's main mind only (rung 2b): Black as before, to see what patience does on one side
    for m in (white, black):   # rung 2c: Params.want_split in every mind of the run, main and pieces
        for agent in [m] + list(m.pieces.values()):
            agent.mind.p.want_split = want_split
    minds = {"White": white, "Black": black}
    wants = {"White": "standing_white_up", "Black": "standing_black_up"}
    rescues, chances = [], []   # Black: when a Black piece hangs on its turn, was its move one that left that piece free?
    for _ in range(rounds):
        side = "White" if w.board.turn else "Black"
        w.actor = side
        a = minds[side]
        hanging_before = {o for o, st in w.read().items() if o.startswith("black") and o.endswith("_bearing") and st == "hanging"} if side == "Black" else set()
        moved = False
        for _ in range(TURN_STEPS + (min(patience, w.horizon) if patience else 0)):   # rung 2b: a patient mind's wait before acting on attention fits in its turn
            if a.goal is None:
                a.goal = wants[side]
            n = len([x for x in w.log if x[2]])
            a.tick()
            if len([x for x in w.log if x[2]]) > n:
                moved = True
                break
        if side == "Black" and hanging_before and moved:
            after = w.read()
            chances.append(len(rescues) + len(chances))
            rescues.append(sum(after.get(o) != "hanging" for o in hanging_before) / len(hanging_before))
        other = "Black" if side == "White" else "White"
        w.actor = other
        minds[other].tick()   # it sees the answer
    ep = w.episodes
    half = len(ep) // 2
    wins = lambda xs: sum(x > 0 for x in xs) / max(1, len(xs))
    losses = lambda xs: sum(x < 0 for x in xs) / max(1, len(xs))
    r_half = len(rescues) // 2
    return dict(episodes=len(ep), white_up_early=wins(ep[:half]), white_up_late=wins(ep[half:]), white_down_late=losses(ep[half:]),
                rescue_early=sum(rescues[:r_half]) / max(1, r_half), rescue_late=sum(rescues[r_half:]) / max(1, len(rescues) - r_half), rescue_n=len(rescues),
                white_met=len(white.reached), black_met=len(black.reached), gave_up=len(white.gave_up))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--rounds", type=int, default=600)
    ap.add_argument("--white", default="pieces")
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--want-split", action="store_true")
    args = ap.parse_args()
    rows = []
    for s in ([args.only] if args.only is not None else range(args.seeds)):
        r = play(s, args.rounds, args.white == "pieces", args.patience, args.want_split)
        rows.append(r)
        print(f"white {args.white} patience {args.patience} want_split {args.want_split} seed {s}: episodes {r['episodes']}, White up early {r['white_up_early']:.2f} late {r['white_up_late']:.2f}, White down late {r['white_down_late']:.2f}; "
              f"Black saved a hanging piece early {r['rescue_early']:.2f} late {r['rescue_late']:.2f} (of {r['rescue_n']}); wants met White {r['white_met']} Black {r['black_met']}; White gave its want up {r['gave_up']} times", flush=True)
    med = statistics.median
    print(f"white {args.white}: White up early {med(r['white_up_early'] for r in rows):.2f}, late {med(r['white_up_late'] for r in rows):.2f}; "
          f"Black's rescues early {med(r['rescue_early'] for r in rows):.2f}, late {med(r['rescue_late'] for r in rows):.2f}")


if __name__ == "__main__":
    main()
