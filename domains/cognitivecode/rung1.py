"""Rung 1: courtship. Rung 0's scene (one open slot of the color line, the lockstep pattern, the spec as the want), with
the pattern present as a mind the code can ask.

The pattern's knowledge is not scripted: it has been followed before. Its past is rung 0 lived once on its own copy of
the world (its own order of the fills), kept as its ledger, as Ben's prologue was in fiction's rung 2. Asked, it answers
from what it lived: what the spec needs (LeanMind.answer, the conditions question), then which push gives that
(CodeMind.way_to, the way question).

Configurations: alone (rung 0), courted (the pattern knows), ignorant (the pattern present, with no past).

Run: python -X utf8 rung1.py [--seeds 10] [--ticks 600] [--show]
"""
import argparse
import sys

from codemind import CodeMind
import rung0

PATTERN = "Lockstep"


def pattern(past_order, ticks):
    """The pattern with a past: rung 0 lived through once, on its own copy of the world."""
    p = CodeMind(PATTERN, rung0.world(order=past_order), want="spec_passing")
    for _ in range(ticks):
        p.tick()
        if p.done:
            break
    return p


def court(config, order, last, ticks):
    w = rung0.world(order=order, last=last)
    others = []
    if config == "courted":
        others = [pattern(1000 + order, ticks)]
    elif config == "ignorant":
        others = [CodeMind(PATTERN, rung0.world(order=1000 + order))]
    mind = CodeMind("Code", w, want="spec_passing", others=others)
    for _ in range(ticks):
        mind.tick()
        if mind.done:
            break
    return mind, w


def show(mind, w):
    for b in mind.beats:
        if b.kind in ("try", "change", "nothing", "ask", "tell", "learn", "reach", "wait") and not (
                b.kind == "change" and b.obj not in ("second", "spec")):
            d = {k: v for k, v in b.detail.items() if k in ("strength", "to", "slot", "condition", "way_to", "inv",
                                                           "confirms") and v is not None}
            print(f"  t{b.t:<4} {b.actor:9} {b.kind:8} {b.obj:20} {d}")
    print(w.python())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--show", action="store_true", help="one courted story, beat by beat (seed 0, the answer last)")
    args = ap.parse_args()
    if args.show:
        show(*court("courted", 0, "v2[v4]", args.ticks))
        return
    print(f"{'config':10} {'order':12} {'reached':>8} {'tries (median, range)':>22}  {'asks':>4}")
    for config in ("alone", "courted", "ignorant"):
        for name, last in (("shuffled", None), ("answer last", "v2[v4]")):
            rows = []
            for k in range(args.seeds):
                mind, w = court(config, k, last, args.ticks)
                tries = sum(1 for b in mind.beats if b.kind == "try" and b.actor == "Code")
                asks = sum(1 for b in mind.beats if b.kind == "ask")
                rows.append((any(b.kind == "reach" for b in mind.beats), tries, asks))
            ok = sorted(t for r, t, _ in rows if r)
            rng = f"{ok[len(ok) // 2]}, {ok[0]}-{ok[-1]}" if ok else "-"
            print(f"{config:10} {name:12} {len(ok):>5}/{len(rows):<2} {rng:>22}  {max(a for *_, a in rows):>4}")


if __name__ == "__main__":
    main()
