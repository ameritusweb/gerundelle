"""Rung 7's tree: how many stories, which endings, the all-'on' story per cast."""
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung7  # noqa: E402

t0 = time.time()
leaves = rung7.forest()
print(len(leaves), "stories in", round(time.time() - t0, 2), "s")
c = Counter()
for w, s in leaves:
    c[s.ending()] += w
print("prior over endings:", {k: round(v, 3) for k, v in c.most_common()})
print("count by ending:", Counter(s.ending() for _, s in leaves))
for w, s in leaves:
    if not s.moves:
        print("cast", s.cast, "->", s.ending(), "rounds", s.round, "beats", len(s.beats))
for e in rung7.ENDINGS:
    ex = [s for _, s in leaves if s.ending() == e]
    if ex:
        s = ex[len(ex) // 2]
        print(e, "e.g. cast", s.cast, "moves", s.moves, "rounds", s.round)
