"""Rung 5b: the harder transfer test. Recall across theories, where the role names do not carry over.

Scene A is rung 0 (the color line, the lockstep pattern): the code learns "the run passes only if the lockstep roles
are filled", the way to it of shape indexing(ext, loc). Scene B is the mask (mask.py: another theory, perceived
through its own facet, roles test / selected / accumulator), its selected value open; the answer, v2[v4], has the same
shape. If recall carries the condition only by its name, nothing in B ever fills a lockstep role; if it carries it by
shape, the past should help as it did in rung 5.

Configurations: recall (a short gap), fresh (no scene A).

Run: python -X utf8 rung5b.py [--seeds 10] [--show]
"""
import argparse
import sys

from codemind import CodeMind
from codeworld import CodeWorld
import mask
import rung0


def scene_b(order):
    return CodeWorld(mask.program(), {"pick": mask.SLOT}, "mask", "mask", ("mask_select",), order=order,
                     spec="spec_b")


def story(config, k, gap=10, ticks=1500):
    wb = scene_b(500 + k)
    if config == "fresh":
        m, start = CodeMind("Code", wb, want="spec_b_passing"), 0
    else:
        wa = rung0.world(order=k)
        m = CodeMind("Code", wa, want="spec_passing")
        for _ in range(ticks):
            m.tick()
            if m.want.closed is not None:
                break
        m.keep_episode()
        m.pass_time(gap)
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
                              runs=sum(1 for b in tries if b.obj == "spec_b"),
                              recalled=any(b.kind == "recall" for b in after))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.show:
        m, wb, after, r = story("recall", 0, ticks=300)
        keys = ("strength", "to", "condition", "shape", "from", "warmth", "confirms")
        for b in after[:40]:
            if b.kind in ("try", "recall", "learn", "reach", "surprise", "wait") or (
                    b.kind == "change" and b.obj in ("pick", "spec_b")):
                print(f"  t{b.t:<4} {b.kind:8} {b.obj:8} { {k: v for k, v in b.detail.items() if k in keys} }")
        print(r)
        print(wb.python())
        return
    print(f"{'config':8} {'reached':>8} {'tries in B (median, range)':>28} {'runs':>5} {'recalled':>9}")
    for config in ("recall", "fresh"):
        rows = [story(config, k)[3] for k in range(args.seeds)]
        ok = sorted(r["tries"] for r in rows if r["reached"])
        rng = f"{ok[len(ok) // 2]}, {ok[0]}-{ok[-1]}" if ok else "-"
        runs = sorted(r["runs"] for r in rows)[len(rows) // 2]
        print(f"{config:8} {len(ok):>5}/{len(rows):<2} {rng:>28} {runs:>5} {sum(r['recalled'] for r in rows):>6}/{len(rows)}")


if __name__ == "__main__":
    main()
