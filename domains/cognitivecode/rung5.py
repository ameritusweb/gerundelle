"""Rung 5: recall by shape across scenes (fiction's rung 6).

Scene A: rung 0 (the color line, the second part of the pair open). The code finds v2[v4] and learns what the run
needs: the lockstep roles filled. At the scene's end the episode is kept: that condition, and the shape of the fill that
brought it about without its names, indexing(ext, loc) (CodeMind.keep_episode).

Time passes. Scene B: the swapped color line (each color paired with its character), its second part open; there the
answer is v1[v4]. B's slot and spec are named apart ('part', 'spec_b'), so nothing carries over by identity (fiction
rung 6: the chest's lid was the box's lid, and its condition applied directly). What can carry over: the condition, by
the pattern's role names (the facets are the theory's, not the scene's), and the way, by shape.

Configurations: recall (a short gap), cold (months: the episode below memory's cold), fresh (no scene A).

Run: python -X utf8 rung5.py [--seeds 10] [--show]
"""
import argparse
import sys

from codemind import CodeMind
from codeworld import CodeWorld
import grammar as G  # noqa: E402
import references as R  # noqa: E402
import rung0
import rung2  # noqa: F401  (registers the swapped spec's cases)

FACETS = ("ps_lockstep", "ps_pair_output")


def scene_b(order):
    program = G.replace(R.color_line(), rung0.PAIR + (0,), G.indexing(G.name("v2"), G.name("v4")))
    return CodeWorld(program, {"part": rung0.SLOTS["second"]}, "color_line_swapped", "parallel_strings", FACETS,
                     order=order, spec="spec_b")


def story(config, k, gap=10, ticks=1500):
    wb = scene_b(500 + k)
    if config == "fresh":
        m = CodeMind("Code", wb, want="spec_b_passing")
        start = 0
    else:
        wa = rung0.world(order=k)
        m = CodeMind("Code", wa, want="spec_passing")
        for _ in range(ticks):
            m.tick()
            if m.want.closed is not None:
                break
        m.keep_episode()
        m.pass_time(120 if config == "cold" else gap)
        wb.t = wa.t
        m.others, m.done = [], False
        m.enter(wb)
        m.open_want("spec_b_passing")
        start = len(m.beats)
    for _ in range(ticks):
        m.tick()
        if m.want.closed is not None:
            break
    after = m.beats[start:]
    tries = [b for b in after if b.kind == "try" and b.actor == "Code"]
    return m, wb, after, dict(reached=any(b.kind == "reach" for b in after), tries=len(tries),
                              recalled=any(b.kind == "recall" for b in after),
                              episodes=[(e["cond"], e["shape"]) for e in m.code_episodes])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.show:
        m, wb, after, r = story("recall", 0)
        print("episodes:", r["episodes"])
        keys = ("strength", "to", "condition", "shape", "from", "warmth", "confirms")
        for b in after:
            if b.kind in ("scene", "want", "try", "recall", "learn", "reach", "surprise") or (
                    b.kind == "change" and b.obj in ("part", "spec_b")):
                print(f"  t{b.t:<4} {b.kind:8} {b.obj:12} { {k: v for k, v in b.detail.items() if k in keys} }")
        print(wb.python())
        return
    print(f"{'config':8} {'reached':>8} {'tries in B (median, range)':>28} {'recalled':>9}")
    for config in ("recall", "cold", "fresh"):
        rows = [story(config, k)[3] for k in range(args.seeds)]
        ok = sorted(r["tries"] for r in rows if r["reached"])
        rng = f"{ok[len(ok) // 2]}, {ok[0]}-{ok[-1]}" if ok else "-"
        print(f"{config:8} {len(ok):>5}/{len(rows):<2} {rng:>28} {sum(r['recalled'] for r in rows):>6}/{len(rows)}")


if __name__ == "__main__":
    main()
