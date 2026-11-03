"""Rung 1c: which sub-wants a seed set, and the splits behind them."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402

w, m, log = rung1c.run(int(sys.argv[1]), "baseline", 800)
a = m.agent
print("sub-wants:", collections.Counter((g, k) for _, g, k in a.sub_log).most_common(6))
for x, sp in a.mind.meta.splits.items():
    if any(f" {mv}_push" in x for mv in ("Rd8", "Re8", "Rd7")):
        print("  split", x.split(" ", 1)[-1][:60], "->", sp["tag"])
print("makers of the top sub-want:", [i[0] for i in a.makers(collections.Counter(g for _, g, k in a.sub_log if k == "set").most_common(1)[0][0])][:5] if a.sub_log else None)
