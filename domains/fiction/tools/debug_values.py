"""Print each invitation's value terms at chosen ticks of a lean run (a development readout)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lean import LeanMind, M0  # noqa: E402
from run_ladder import RUNGS  # noqa: E402


def main(rung=1, at=(30, 40, 60)):
    spec = RUNGS[rung]
    w = spec["world"]()
    m = LeanMind(spec["actor"], w, want=spec["want"], want_count=spec.get("want_count", 1))
    while w.t < max(at) + 1:
        if any(abs(w.t - a) <= 2 for a in at):
            print(f"t{w.t} facts {sorted(m.facts())}")
            for inv in w.invitations():
                h = m.effect_hole(inv)
                print(f"   {inv}: value {m.value(inv):.3f} level {m.level(h):.2f} pull {m.pull(h):.2f} stakes "
                      f"{m.stakes(h):.2f} work {m.work_estimate(inv):.1f} causes {m.funding(h, 'causes'):.2f} "
                      f"conds {m.funding(h, 'conditions'):.2f} serve {m.terr.serve().get(inv)} tried {len(m.tried(inv))}")
        m.tick()
    print({r: row["holder"] for r, row in m.terr.rows.items()}, sorted(m.terr.open_slots()))


if __name__ == "__main__":
    main()
