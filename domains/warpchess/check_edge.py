"""How the dream's edges split: no expectation, or an expectation that differs from what followed, and by how much."""
import collections
import sys
import runpy

sys.argv = ["probe_dream.py", "140"]   # long enough for one game
import dream
real = dream.dream
stats = []
def traced(agent, rng=None):
    pred = agent.predict
    def p(inv, facts=None, tree=None):
        e = pred(inv, facts, tree)
        stats.append(e)
        return e
    agent.predict = p
    try:
        return real(agent, rng)
    finally:
        agent.predict = pred
dream.dream = traced
g = runpy.run_path("probe_dream.py", run_name="__main__")
a = g["a"]
trials = a.dreamed[-len(stats):] if stats else []
none = sum(1 for e in stats if e is None)
print(f"dream trials {len(stats)}: no expectation {none}, an expectation {len(stats) - none}")
diffs = []
for e, (_, _, names) in zip(stats, trials):
    if e is not None:
        diffs.append((len(e & names), len(e - names), len(names - e)))
print("for those with one: (shared, expected but didn't come, came but not expected), first 12:", diffs[:12])
if diffs:
    print("expected changes that came, on average:", round(sum(d[0] for d in diffs) / max(1, sum(d[0] + d[1] for d in diffs)), 2))
