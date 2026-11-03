"""Rung 0: one code mind, one pattern (lockstep), one want (the spec passing), no talk.

The world is the color line (poc2 references.color_line) with the second part of the pair it appends left open: one
want, one hidden condition, as the jack-in-the-box.

    def f1(v1: str, v2: str) -> list[tuple[str, str]]:
        v3 = []
        for v4 in range(len(v1)):
            v3.append((v1[v4], <str>))
        return v3

The known answer: v2[v4], the color line (POC3's positive control). With both parts open (--both) the roles can fill
only jointly: that is the lamp's AND (fiction LADDER.md, rung 9), a later rung, not this one.

Run: python -X utf8 rung0.py [--ticks 400] [--beats]
"""
import argparse
import sys
from collections import Counter

from codeworld import CodeWorld
import references as R  # noqa: E402  (poc2's, on the path codeworld set)
import lean  # noqa: E402

PAIR = (1, 0, 1, 1, 2, 0, 1)
SLOTS = {"first": PAIR + (0,), "second": PAIR + (1,)}


def world(both=False, order=None, last=None, first=None):
    slots = SLOTS if both else {"second": SLOTS["second"]}
    return CodeWorld(R.color_line(), slots, "color_line", "parallel_strings", ("ps_lockstep", "ps_pair_output"),
                     order=order, last=last, first=first)


def run(w, ticks):
    from codemind import CodeMind   # credit to slots: with the abstract value in the slot's state, the plain lean
    mind = CodeMind("Code", w, want="spec_passing")   # mind holds the slot at its first fill and runs forever
    for _ in range(ticks):
        mind.tick()
        if mind.done:
            break
    return mind


def sweep(seeds, ticks, last=None):
    """Rung 0 under shuffled orders of the fills: tries to the want, per seed."""
    rows = []
    for k in range(seeds):
        w = world(order=k, last=last)
        mind = run(w, ticks)
        tries = [b for b in mind.beats if b.kind == "try"]
        edits = [b for b in tries if b.obj != "spec"]
        rows.append((k, any(b.kind == "reach" for b in mind.beats), len(tries), len(edits),
                     len({b.detail["strength"] for b in edits}), w.states()["second"]))
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--both", action="store_true", help="both parts of the pair open (the AND)")
    ap.add_argument("--seeds", type=int, default=0, help="the fair test: this many shuffled orders of the fills")
    args = ap.parse_args()
    if args.seeds:
        for name, last in (("shuffled", None), ("answer last", "v2[v4]")):
            rows = sweep(args.seeds, args.ticks, last)
            ok = [r for r in rows if r[1]]
            tries = sorted(r[2] for r in ok)
            print(f"{name}: reached {len(ok)}/{len(rows)}; tries median {tries[len(tries) // 2] if tries else '-'}, "
                  f"range {tries[0] if tries else '-'}-{tries[-1] if tries else '-'}; distinct fills tried "
                  f"{sorted(r[4] for r in rows)}")
        return
    w = world(args.both)
    print(f"slots: {', '.join(f'{s} ({len(f)} fills)' for s, f in w._fills.items())}; roles: {w.roles}")
    print(w.python())
    mind = run(w, args.ticks)
    kinds = Counter(b.kind for b in mind.beats)
    tries = [b for b in mind.beats if b.kind == "try"]
    runs = [b for b in tries if b.obj == "spec"]
    print(f"ticks {w.t}; tries {len(tries)} ({len(runs)} runs, {len(tries) - len(runs)} edits); "
          f"reached {any(b.kind == 'reach' for b in mind.beats)}; beats {dict(kinds)}")
    for b in mind.beats:
        if b.kind in ("learn", "believe", "surprise", "reach", "wait") or (b.kind == "feel"):
            print(f"  t{b.t:<4} {b.kind:8} {b.obj:24} {b.detail}")
    if args.beats:
        for b in mind.beats:
            print(f"  t{b.t:<4} {b.kind:8} {b.obj:24} {b.detail}")
    print(w.python())


if __name__ == "__main__":
    main()
