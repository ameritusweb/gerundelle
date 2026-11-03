import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1e
from sov_agent import constraints_from
per, done, noticed, m = rung1e.run(0, "converge", 20, 600)
a, w = m.agent, m.world
cons = constraints_from(a.trials)
print("kinds:", {e: len([1 for _, ev in a.trials if ev == e]) for e in set(ev for _, ev in a.trials)})
print("constraints:", {e: [" ".join(sorted(h)) for h in hs] for e, hs in cons.items()})
invs = {__import__("force_world").inv_id(i): i for i in w.invitations()}
now = a.facts_now()
opts = [i for i in invs.values() if not any(j == i and f == now for j, f, _ in a.pushed)]
combos = [(e, h) for e, hs in cons.items() for h in hs]
clear_all = [i[0] for i in opts if all(not h <= w.relations_of(i) for _, h in combos)]
print("position", w.at, "options", len(opts), "clearing every constraint:", clear_all)
print("plan_step now:", a.plan_step(invs))
