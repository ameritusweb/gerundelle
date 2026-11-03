"""Can rung 4's scene be copied mid-story (deepcopy of world + minds + beats) and how fast does a turn run?"""
import copy
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lean import LeanMind  # noqa: E402
from beats import effect_parts  # noqa: E402
import worlds  # noqa: E402

world = worlds.jack_in_the_box()
shared = []
leo = LeanMind("Leo", worlds.jack_latch_undone(), want="latch_connecting")
for _ in range(300):
    leo.tick()
    if leo.done:
        break
leo.world, leo.beats, leo.keep, leo.resolve = world, shared, True, 2.0
leo.want.closed, leo.done, leo.last_facts, leo.recent = None, False, None, set()
leo.terr.wants[effect_parts("latch_connecting", world.objs)[0]] = "latch_connecting"
mara = LeanMind("Mara", world, want="lid_releasing", beats=shared, resolve=2.0, others=[leo])
leo.others = [mara]
leo.contesting.add("lid_releasing")
t0 = time.time()
for k in range(6):
    mara.tick()
    leo.tick()
print("6 rounds", round(time.time() - t0, 3), "s;", len(shared), "beats")
t0 = time.time()
st = copy.deepcopy((world, mara, leo, shared))
print("deepcopy", round(time.time() - t0, 4), "s")
w2, m2, l2, s2 = st
assert m2.world is w2 and l2.world is w2 and m2.beats is s2 and l2.others[0] is m2
for k in range(100):
    if m2.done:
        break
    m2.tick()
    l2.tick()
for k in range(100):
    if mara.done:
        break
    mara.tick()
    leo.tick()
print("copy and original agree:", [b.kind for b in s2] == [b.kind for b in shared], len(shared))
print("mara done", mara.want.closed, "resolve", mara.resolve, "leo resolve", leo.resolve)
