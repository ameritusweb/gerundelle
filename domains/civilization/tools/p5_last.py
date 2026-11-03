"""What a mind did in the curriculum's last stage (sailing home), push by push."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
import p5  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
world, m, log = p5.run_stages(800, sys.argv[1], sys.argv[2] == "carried")
print(log)
for t, inv, names in m.agent.tried[:30]:
    print(t, inv, names[:4])
print("end", world.states(), "store", world.book.store, "fused", world.book.embodied.get("skiff_fused"), "pool", world.book.field)
print("top", m.agent.mind.top(m.agent.last_rec)[:5])
