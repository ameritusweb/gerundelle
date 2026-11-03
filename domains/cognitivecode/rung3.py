"""Rung 3: scarcity. Two codes, one slot, two styles; one shared program, in turns (fiction's rung 4).

The world: the color line in the enumerate style with the first part of the pair open:

    for v4, v5 in enumerate(v1):
        v3.append((<str>, v2[v4]))

The slot admits two fills that both pass the spec and both keep every lockstep role filled: the index read v1[v4],
and the loop's item v5. They differ in what the slot itself plays (the index read: the left read, the position, the
pair's left part, the position's use; the item: only the pair's left part, the loop doing the reading), so the slot's
state shows which style holds it, and a replacement is seen as an undo.

Two code minds, each a keeper with a past: Index made the spec pass once in the index-style color line (v1[v4]);
Item made it pass once here (v5). Set in one program, each keeps its state, reopening whenever the other undoes it. Each undo seen
drains the keeper's resolve by 1 / the pull of its slot there (fiction rung 4); at zero it gives up (resignation).
Endings are read off the minds. The known answer: doubling one keeper's resolve flips which style the program ends in.

Run: python -X utf8 rung3.py [--show]
"""
import argparse
import sys

from codemind import CodeMind
from codeworld import CodeWorld
from beats import effect_parts  # noqa: E402  (fiction's, on the path codeworld set)
import references as R  # noqa: E402

FIRST = (1, 0, 1, 1, 3, 0, 1, 0)
FACETS = ("ps_lockstep", "ps_pair_output", "ps_position_from_loop")


def world():
    return CodeWorld(R.color_line_enumerate(), {"first": FIRST}, "color_line", "parallel_strings", FACETS)


def state_of(fill):
    """The slot's state when it holds fill (read off the world, not written by hand)."""
    w = world()
    w.act((fill, "first", None))
    return w.states()["first"]


def index_world():
    """The color line in the index style (for v4 in range(len(v1))), its first part open: Index's past."""
    return CodeWorld(R.color_line(), {"first": (1, 0, 1, 1, 2, 0, 1, 0)}, "color_line", "parallel_strings", FACETS)


def keeper(name, past_world, shared, beats, resolve, ticks=600):
    """A keeper's past: the spec made to pass once, on its own world (Index: the index-style color line; Item: this
    scene); what it keeps is the slot's state its passing fill gave it, and its way is the push that gave it (fiction's
    keeper: Leo's past taught him the latch). First the past was "make the slot hold my style's state", and the first
    fill to do that was junk the spec fails (v5[v4], v5[v4:v4]: the facets resolve the loop's item to its sequence)."""
    m = CodeMind(name, past_world, want="spec_passing")
    for _ in range(ticks):
        m.tick()
        if m.done:
            break
    state = past_world.states()["first"]
    from printer import value
    m.held_way = (value(past_world.program and __import__("grammar").find(past_world.program, past_world.slots["first"]).node),
                  "first")
    m.world, m.beats, m.keep, m.resolve, m.resolve0 = shared, beats, True, resolve, resolve
    m.done, m.last_facts, m.recent = False, None, set()
    m.open_want(f"first_{state}")
    return m


def contest(r_index, r_item, ticks=200):
    shared, beats = world(), []
    a = keeper("Index", index_world(), shared, beats, r_index)
    b = keeper("Item", world(), shared, beats, r_item)
    a.others, b.others = [b], [a]
    for _ in range(ticks):
        for m in (a, b):
            if not m.done:
                m.tick()
        if a.done or b.done:
            break
    for m in (a, b):   # what each sees of the end
        m.perceive()
    return a, b, shared, beats


def summary(a, b, shared, beats):
    resigned = [x.actor for x in beats if x.kind == "feel" and x.detail.get("phase") == "resignation"]
    angry = sorted({(x.actor, x.obj) for x in beats if x.kind == "feel" and x.detail.get("phase") == "anger"})
    pushes = {m.name: sum(1 for x in beats if x.kind == "try" and x.actor == m.name) for m in (a, b)}
    holds = "v1[v4] (Index)" if shared.states()["first"] == state_of("v1[v4]") else \
        "v5 (Item)" if shared.states()["first"] == state_of("v5") else shared.states()["first"]
    return resigned, angry, pushes, holds


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="the equal contest, beat by beat")
    args = ap.parse_args()
    if args.show:
        a, b, shared, beats = contest(2.0, 2.0)
        for x in beats:
            if x.kind in ("try", "change", "feel") and (x.kind != "change" or x.obj == "first"):
                d = {k: v for k, v in x.detail.items() if k in ("strength", "to", "phase")}
                print(f"  t{x.t:<4} {x.actor:6} {x.kind:7} {x.obj:6} {d}")
        print(shared.python())
        return
    print(f"{'resolve (Index, Item)':22} {'pushes':>22}  {'resigned':10} {'the slot holds':16} anger")
    for ri, rt in ((2.0, 2.0), (4.0, 2.0), (2.0, 4.0), (1.0, 1.0), (8.0, 2.0)):
        resigned, angry, pushes, holds = summary(*contest(ri, rt))
        print(f"{f'({ri:g}, {rt:g})':22} {str(pushes):>22}  {','.join(resigned) or '-':10} {holds:16} "
              f"{', '.join(f'{x}->{y}' for x, y in angry) or '-'}")


if __name__ == "__main__":
    main()
