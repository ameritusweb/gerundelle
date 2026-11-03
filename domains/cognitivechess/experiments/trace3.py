"""Rung 3 trace: what each side does, by kind of move, against a thinking Black and the scripted one.

For every move: who made it, in which configuration (0 defended, 1 hanging), and its kind:
  takes-back   a capture on the square the other side just moved to
  capture      any other capture
  knight-flees Black's knight leaves d5 uncaptured
  quiet        any other move
  pass         the scripted Black's pass
Slices with no move (a mind watching or idle) are counted per side as 'no move'.
Also: White's first moves per configuration; every episode's end (White's balance just before the board is set back);
and Black's next move after each White capture (takes-back, knight-flees, quiet, capture, pass).

Run: python -X utf8 experiments/trace3.py [--seeds 0,3] [--rounds 800] [--arm base] [--black mind] [--schedule rounds|turns]
     [--black-want up|kept]
"""
import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))

import chess  # noqa: E402
from rung3 import make, play  # noqa: E402


def run(seed, black, arm, rounds, schedule="rounds", black_want="up", given=False):
    w, minds = make(seed, black, arm, black_want, given)
    kinds = {"White": Counter(), "Black": Counter()}
    first = {0: Counter(), 1: Counter()}
    ends = {0: Counter(), 1: Counter()}   # every episode's end (the one under way at the last round is left out)
    act, reset = w.act, w.reset
    state = dict(ep=None, white_took=False)
    answers = {0: Counter(), 1: Counter()}   # Black's next move after a White capture, per configuration

    def counted_reset():   # every episode's end: White's balance just before the board is set back
        if hasattr(w, "standing"):
            ends[w.config][w.balance("White")] += 1
        state["white_took"] = False
        reset()
    w.reset = counted_reset

    def logged(inv=None, hold=False):
        who, cfg, ep = w.actor, w.config, len(w.episodes)
        if state["ep"] != ep:   # a new episode began: the last one's end, read from the board before it was reset
            state["ep"] = ep
        if inv is None:
            kinds[who]["no move"] += 1
            return act(inv, hold)
        if inv[0] == "pass":
            kinds[who]["pass"] += 1
            if who == "Black" and state["white_took"]:
                answers[cfg]["pass"] += 1
                state["white_took"] = False
            return act(inv, hold)
        b = w.board
        move = b.parse_san(inv[0].split(" ", 1)[-1])
        last = b.peek() if b.move_stack and b.peek() != chess.Move.null() else None
        piece = b.piece_at(move.from_square)
        if b.is_capture(move):
            k = "takes-back" if last is not None and move.to_square == last.to_square else "capture"
        elif who == "Black" and piece.piece_type == chess.KNIGHT and move.from_square == chess.D5:
            k = "knight-flees"
        else:
            k = "quiet"
        kinds[who][k] += 1
        if who == "Black" and state["white_took"]:
            answers[cfg][k] += 1
        state["white_took"] = who == "White" and b.is_capture(move)
        if who == "White" and w.moved == 0:
            first[cfg][b.san(move).rstrip("+#")] += 1
        return act(inv, hold)
    w.act = logged
    play(w, minds, rounds, schedule)
    w.close()
    return kinds, first, ends, answers, len(w.episodes) - 1


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1,2,3,4,5,6,7,8,9")
    ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--arm", default="base")
    ap.add_argument("--black", default="mind")
    ap.add_argument("--schedule", default="rounds", choices=("rounds", "turns"))
    ap.add_argument("--black-want", default="up", choices=("up", "kept", "keeper"))
    ap.add_argument("--given", action="store_true")
    args = ap.parse_args()
    for s in (int(x) for x in args.seeds.split(",")):
        kinds, first, ends, answers, eps = run(s, args.black, args.arm, args.rounds, args.schedule, args.black_want, args.given)
        print(f"seed {s} ({args.arm}, Black {args.black}, {args.schedule}, Black wants {args.black_want}{', given' if args.given else ''}): {eps} episodes")
        for side in ("White", "Black"):
            print(f"  {side:5} moves {dict(kinds[side].most_common())}")
        for cfg, name in ((0, "defended"), (1, "hanging")):
            print(f"  {name:8} White's first moves {first[cfg].most_common(5)}; episodes ending White {dict(ends[cfg])}; "
                  f"Black's answer to a White capture {dict(answers[cfg].most_common())}", flush=True)


if __name__ == "__main__":
    main()
