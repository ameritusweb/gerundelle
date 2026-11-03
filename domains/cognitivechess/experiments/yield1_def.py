"""Rung 1 (reply perceived), one seed: the defended configuration's episodes, their first two moves and outcome, for an
arm; and the sub-want log's kinds."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402

seed, arm = int(sys.argv[1]), sys.argv[2]
w, m, log = rung1.run(seed, arm, 800, relations=("reply",))
eps, cfg, won = collections.defaultdict(list), {}, set()
for ep, c, mv, ev in log:
    cfg[ep] = c
    if mv:
        eps[ep].append(mv)
    if "material: even -> up" in ev:
        won.add(ep)
d = collections.Counter((tuple(v[:2]), ep in won) for ep, v in eps.items() if cfg[ep] == 0)
print(arm, "defended episodes", sum(d.values()), "won", sum(n for (mv, w_), n in d.items() if w_))
for k, n in d.most_common(8):
    print("  ", n, k)
print("  sub-wants:", collections.Counter((g, k) for _, g, k in m.agent.sub_log).most_common(5))
