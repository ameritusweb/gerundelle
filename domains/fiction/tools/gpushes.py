"""Gerundelle's pushes on a rung: facts at the push and what it did (debug)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_ladder  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
rung, ticks = int(sys.argv[1]), int(sys.argv[2])
spec = run_ladder.RUNGS[rung]
m = GerundelleMind(spec["actor"], spec["world"](), want=spec["want"], want_count=spec.get("want_count", 1))
m.run(ticks)
for inv, facts, mode in m.agent.pushed:
    print(inv[:2], sorted(f for f in facts if not f.startswith(("ground", "agent"))), sorted(mode))
print("splits", {x: s["tag"] for x, s in m.agent.mind.meta.splits.items()})
print("not:", {c: [o for (r, o) in rel if r == "conditioned_by"] for c, rel in m.agent.mind.understanding.rel.items() if "_push:" in c})
terr = m.agent.mind.territory
print("relation_of:", terr.relation_of())
for r in ("flag",):
    for x in ("crate",):
        print(r, x, terr.responsive(r, x), "outside share", terr._outside, "expected out", round(terr._expected_out, 2),
              "span", m.agent.mind.t, "fails", len(terr.rows[x].get("fail_times", [])))
