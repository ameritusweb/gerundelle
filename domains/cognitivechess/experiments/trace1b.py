"""Trace one rung 1b run: the moves of each defended episode that lost the exchange, and what the planner chose."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402

seed, src = int(sys.argv[1]), sys.argv[2]
w, m, log = rung1.run(seed, "both", 800, src)
eps, cfg, lost = collections.defaultdict(list), {}, set()
for ep, c, mv, ev in log:
    cfg[ep] = c
    if mv:
        eps[ep].append(mv)
    if any(e.startswith("material:") and e.endswith("-> down") for e in ev):
        lost.add(ep)
print("lost in episodes:", sorted(lost)[:15], "...")
print("their moves:", collections.Counter(tuple(eps[e]) for e in lost).most_common(5))
print("configs of lost:", collections.Counter(cfg[e] for e in lost))
print("splits on Rxd5:", {x.split(" ", 1)[-1][:45]: s["tag"] for x, s in m.agent.mind.meta.splits.items() if "Rxd5" in x})
print("sub_log:", collections.Counter((g, k) for _, g, k in m.agent.sub_log).most_common(5))
