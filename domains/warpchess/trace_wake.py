"""Trace (dream.py): why waking gives no imagined trials. For each wake: untried moves looked at, how many had a start, and why the fit failed."""
import collections
import sys
import runpy

import carry
import dream

stats = collections.Counter()
real_fit = carry.fit
def fit(first, start, lived_mover, mover):
    by = lambda st: {p: frozenset((ch, s) for q, ch, s in st if q == p) for p in {q for q, _, _ in st}}
    a, b = by(first), by(start)
    if len(a) != len(b):
        stats["pieces changed differ in number"] += 1
    elif a.get(lived_mover) != b.get(mover):
        stats["the mover's changes differ"] += 1
    out = real_fit(first, start, lived_mover, mover)
    if out is None and len(a) == len(b) and a.get(lived_mover) == b.get(mover):
        stats["no same-colour piece with the same changes"] += 1
    if out is not None:
        stats["fitted"] += 1
    return out
dream.wake.__globals__  # (wake imports fit from carry at call time)
carry.fit = fit
real_wake = dream.wake
def wake(agent, invs):
    if agent.__dict__.get("dream_pairs"):
        tried = {carry.inv_id_of(i) for i, _, _ in agent.pushed}
        untried = [c for c in invs if c not in tried]
        stats["untried moves looked at"] += len(untried)
        stats["with a start"] += sum(1 for c in untried if agent.world.imagined_start([invs[c][0]]))
    return real_wake(agent, invs)
dream.wake = wake
sys.argv = ["probe_dream.py", "170"]
runpy.run_path("probe_dream.py", run_name="__main__")
print("WAKE TRACE:", dict(stats))
