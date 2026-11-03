"""Rung 2: a wrong answer, honestly given. Rung 1's scene, with the pattern's past from a different spec.

A pattern has no rival want, so it cannot lie as Leo did (fiction rung 3). It can be wrong honestly: its past is the
swapped color line, which pairs each color with its character, (meta[i], content[i]):

    v3.append((v2[v4], <str>))        its answer there: v1[v4]

Asked here, it answers from what it lived. Its condition carries over (the spec passes only if the lockstep roles
fill), but its way does not: here v1[v4] pairs the content with itself, and no role fills. The code tries the told
way, the role stays empty, the told receipt is retracted and the teller's record marked down; then the code searches
for the fill itself, and its own runs confirm the condition the pattern gave. Right about what, wrong about how.

Configurations: courted (rung 1: the pattern's past is this spec), mismatched (its past is the swapped spec), alone.

Run: python -X utf8 rung2.py [--seeds 10] [--ticks 600] [--show]
"""
import argparse
import sys

from codemind import CodeMind
from codeworld import CodeWorld
import grammar as G
import references as R
import rung0
import specs

PATTERN = "Lockstep"


def swapped_cases():
    """f1(content, meta) returns one (color, character) pair per position: the color line's spec with each pair
    swapped. The same inputs as specs.color_line_cases."""
    def case(content, meta):
        def run(tree):
            got = specs.Machine(tree).call("f1", content, meta)
            want = [(meta[i], content[i]) for i in range(len(content))]
            return "" if got == want else f"f1({content!r}, {meta!r}) returned {got!r}, not {want!r}"
        return run
    pairs = [(c, m) for c in specs.strings("ab", 3) for m in specs.strings("ab", 3) if len(m) == len(c)]
    pairs += [("ababa", "babab"), ("aabba", "abbaa"), ("abababa", "bbbaaab"), ("aaaaaa", "bbbbbb")]
    return [case(c, m) for c, m in pairs]


specs.CASES["color_line_swapped"] = swapped_cases()


def swapped_world(order=None):
    program = G.replace(R.color_line(), rung0.PAIR + (0,), G.indexing(G.name("v2"), G.name("v4")))
    return CodeWorld(program, {"second": rung0.SLOTS["second"]}, "color_line_swapped", "parallel_strings",
                     ("ps_lockstep", "ps_pair_output"), order=order)


def pattern(world, ticks):
    p = CodeMind(PATTERN, world, want="spec_passing")
    for _ in range(ticks):
        p.tick()
        if p.done:
            break
    return p


def court(config, order, last, ticks):
    others = []
    if config == "courted":
        others = [pattern(rung0.world(order=1000 + order), ticks)]
    elif config == "mismatched":
        others = [pattern(swapped_world(order=1000 + order), ticks)]
    w = rung0.world(order=order, last=last)
    mind = CodeMind("Code", w, want="spec_passing", others=others)
    for _ in range(ticks):
        mind.tick()
        if mind.done:
            break
    return mind, w


def show(mind, w):
    for b in mind.beats:
        if b.kind in ("try", "ask", "tell", "surprise", "learn", "reach", "wait", "feel") or (
                b.kind in ("change", "nothing") and b.obj in ("second", "spec")):
            d = {k: v for k, v in b.detail.items() if k in ("strength", "to", "slot", "condition", "way_to", "inv",
                                                           "expected", "got", "told", "confirms", "phase")
                 and v is not None}
            print(f"  t{b.t:<4} {b.actor:9} {b.kind:8} {b.obj:20} {d}")
    print(f"trust: {mind.trust}; reliability of {PATTERN}: {mind.reliability(PATTERN):.2f}")
    print(w.python())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--show", action="store_true", help="one mismatched story (seed 0, the answer last), beat by beat")
    args = ap.parse_args()
    if args.show:
        mind, w = court("mismatched", 0, "v2[v4]", args.ticks)
        tries = [b for b in mind.beats if b.kind == "try" and b.actor == "Code"]
        show(mind, w) if len(tries) < 40 else (show.__call__ if False else None)
        if len(tries) >= 40:   # long: the conversation and the end only
            keep = [b for b in mind.beats if b.kind in ("ask", "tell", "surprise", "learn", "reach", "feel")]
            for b in keep:
                print(f"  t{b.t:<4} {b.actor:9} {b.kind:8} {b.obj:20} "
                      f"{ {k: v for k, v in b.detail.items() if v not in (None, [], '')} }")
            print(f"tries {len(tries)}; runs {sum(1 for b in tries if b.obj == 'spec')}; trust {mind.trust}; "
                  f"reliability {mind.reliability(PATTERN):.2f}")
            print(w.python())
        return
    print(f"{'config':11} {'order':12} {'reached':>8} {'tries (median, range)':>22} {'runs':>5} {'retracted':>9} "
          f"{'reliability':>11}")
    for config in ("courted", "mismatched", "alone"):
        for name, last in (("shuffled", None), ("answer last", "v2[v4]")):
            rows = []
            for k in range(args.seeds):
                mind, w = court(config, k, last, args.ticks)
                tries = [b for b in mind.beats if b.kind == "try" and b.actor == "Code"]
                rows.append((any(b.kind == "reach" for b in mind.beats), len(tries),
                             sum(1 for b in tries if b.obj == "spec"),
                             sum(1 for b in mind.beats if b.kind == "surprise" and b.detail.get("told")),
                             mind.reliability(PATTERN)))
            ok = sorted(t for r, t, *_ in rows if r)
            rng = f"{ok[len(ok) // 2]}, {ok[0]}-{ok[-1]}" if ok else "-"
            runs = sorted(r[2] for r in rows)[len(rows) // 2]
            print(f"{config:11} {name:12} {len(ok):>5}/{len(rows):<2} {rng:>22} {runs:>5} "
                  f"{sum(r[3] for r in rows):>9} {sorted(r[4] for r in rows)[len(rows) // 2]:>11.2f}")


if __name__ == "__main__":
    main()
