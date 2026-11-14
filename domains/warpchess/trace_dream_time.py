"""Where a dream's time goes, part by part (the user, 2026-11-13: "trace it"). Replays rung 4p's room game with dreams (seed 0,
PYTHONHASHSEED=0) into its slice-7 dreams, with timers on each step of a dream trial (dream.py): the mind's copy (dreaming_mind:
unpickling, and giving it the imagined register), the copy's tick (Mind.tick, split into think's levels, and within them resolve and
candidates), the board (play: the move and Black's reply in their shoes), reading the world (read: forces and plans), the
manipulations, and the rest. Prints totals and shares per part, and the copy's pool size (how many compete at level 0).
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_dream_time.py [slices, default 7]"""
import collections
import sys
import time

import rung0  # noqa: F401
import dream
import molecules
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

N = int(sys.argv[1]) if len(sys.argv) > 1 else 7
T = collections.Counter()
calls = collections.Counter()
inside = {"dream": False}
pool_sizes = []


def timed(owner, name, label, only_in_dream=True):
    orig = getattr(owner, name)

    def wrap(*args, **kw):
        if only_in_dream and not inside["dream"]:
            return orig(*args, **kw)
        t0 = time.perf_counter()
        try:
            return orig(*args, **kw)
        finally:
            T[label] += time.perf_counter() - t0
            calls[label] += 1
    setattr(owner, name, wrap)


orig_dream = dream.dream


def dream_timed(agent, rng=None, focus=None):
    inside["dream"] = True
    t0 = time.perf_counter()
    try:
        return orig_dream(agent, rng, focus)
    finally:
        T["dream, total"] += time.perf_counter() - t0
        calls["dream, total"] += 1
        inside["dream"] = False


dream.dream = dream_timed
timed(dream, "dreaming_mind", "copy of the mind (unpickle + imagined)")
timed(dream, "understanding_of", "understanding_of (copy + its tick + reading attention)")
timed(dream, "manipulations", "manipulations")
timed(molecules.Mind, "tick", "copy's tick (Mind.tick)")
timed(molecules.Mind, "levels_of", "  levels_of")
timed(molecules.Mind, "resolve", "    resolve")
timed(molecules.Mind, "candidates", "      candidates")
timed(molecules.Mind, "support", "    support")
timed(molecules.Understanding, "observe", "  Understanding.observe")
w, a = rung4p.build(0, RUNG1_TWO, dreams=True)
timed(type(w), "play", "board: play (move, reply)")
timed(type(w), "read", "world: read (forces, plans)")
orig_think = molecules.Mind.think


def think(self, *args, **kw):
    if inside["dream"]:
        pool_sizes.append(len(self.pool))
    return orig_think(self, *args, **kw)


molecules.Mind.think = think
black = RandomSide(w, 0)
slices = 0
while slices < N:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            a.tick()
            give(a, w)
            slices += 1
            if len([x for x in w.log if x[2]]) > n or slices >= N:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
total = T["dream, total"]
print(f"dreams {calls['dream, total']}, {total:.1f}s; trials {calls['understanding_of (copy + its tick + reading attention)']}")
for label, sec in sorted(T.items(), key=lambda kv: -kv[1]):
    print(f"  {100 * sec / total:5.1f}%  {sec:7.1f}s  {calls[label]:6d} calls  {label}")
if pool_sizes:
    print(f"the copy's pool when it thinks: {min(pool_sizes)}-{max(pool_sizes)} molecules (mean {sum(pool_sizes) / len(pool_sizes):.0f})")
