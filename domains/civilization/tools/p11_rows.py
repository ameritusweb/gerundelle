"""The territory rows of the jars, per mind, after a P11 run: holder history, taken_by, and how often others moved them."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
import p4  # noqa: E402
import p11  # noqa: E402
from lock_world import SealWorld  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
world, minds, shared = p4.run(["steady"] * 4, int(sys.argv[1]) if len(sys.argv) > 1 else 600, kind=p11.Grieving,
                              world_cls=SealWorld)
for m in minds:
    ph = m.agent.mind.phases
    formed = [(t, p) for t, what, p in ph.log if what == "formed" and ":anger:" in p]
    print(m.name, "anger formed (register):", formed[:6], "| won attention:", sorted(p for p in m.phases_seen if ":anger:" in p))
    terr = m.agent.mind.territory
    for j in sorted(r for r in terr.rows if r.startswith("jar")):
        row = terr.rows[j]
        print(m.name, j, "holder", row.get("holder"), "taken_by", row.get("taken_by"), "other", row.get("other"),
              "history", row.get("history", [])[-6:])
