"""Trace: do the planner, the prediction and the sub-wants read the imagination register, and does it change a choice?"""
import collections
import sys
import runpy

import rung0  # noqa: F401  (puts Gerundelle on the path)
import sov_agent

counts = collections.Counter()
real_dm = sov_agent.SovAgent.dreamed_modes
def dm(self, inv, facts):
    out = real_dm(self, inv, facts)
    counts["dreamed_modes asked"] += 1
    counts["dreamed_modes found something"] += bool(out)
    return out
sov_agent.SovAgent.dreamed_modes = dm
real_makers = sov_agent.SovAgent.makers
def makers(self, fact):
    out = real_makers(self, fact)
    lived = {i for i, _, names in self.pushed if fact in names}
    counts["makers asked"] += 1
    counts["makers: a dreamed way given"] += any(i not in lived for i in out)
    return out
sov_agent.SovAgent.makers = makers
real_plan = sov_agent.imagined_lines
def lines(model, s, roots, horizon=3, gamma=1.0):
    out = real_plan(model, s, roots, horizon, gamma)
    counts["plans"] += 1
    counts["plans worth > 0"] += out[1] > 0
    return out
sov_agent.imagined_lines = lines
import offers
offers.imagined_lines = lines
sys.argv = ["probe_dream.py", "300"]
g = runpy.run_path("probe_dream.py", run_name="__main__")
print("USE:", dict(counts), "| imagined trials in the register:", len(g["a"].dreamed))
