"""Rung 1 (both), seed 6 after the label fix: why is the coincidental condition never contradicted?"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1  # noqa: E402

w, m, log = rung1.run(6, "both", 800)
a, und = m.agent, m.agent.mind.understanding
print("splits on Rxd5:")
for x, sp in a.mind.meta.splits.items():
    if "Rxd5" in x:
        yes = collections.Counter(tuple(sorted(h[2]))[:3] for h in a.mind.meta.modes.get(sp["yes"], []))
        no = collections.Counter(tuple(sorted(h[2]))[:3] for h in a.mind.meta.modes.get(sp["no"], []))
        print(" ", x.split(" ", 1)[-1], "tag", sp["tag"], "\n    yes", dict(yes), "\n    no ", dict(no))
print("sub-wants:", collections.Counter((g, k) for _, g, k in a.sub_log).most_common(6))
print("ruled out (not:) on Rxd5 concepts:", [(c.split(' ',1)[-1][:30], o) for c, rels in und.rel.items() if "Rxd5" in c
                                           for (r, o) in rels if r == "conditioned_by" and o.startswith("not:")])
print("makers of white_bishop_a6_hanging:", [i[0] for i in a.makers("white_bishop_a6_hanging")])
# defended episodes: the moves, and material/bishop changes
eps, cfg = collections.defaultdict(list), {}
for ep, c, mv, ev in log:
    cfg[ep] = c
    eps[ep].append((mv, [e for e in ev if "material" in e or "a6" in e or "knight" in e]))
shown = 0
for ep in sorted(eps):
    if cfg[ep] == 0 and ep > 20 and shown < 8:
        shown += 1
        print(f"ep{ep}:", [(mv, e) for mv, e in eps[ep] if mv or e])
