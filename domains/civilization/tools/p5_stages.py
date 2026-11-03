"""P5's curriculum across temperaments, fresh and carried: each stage reached or not, and how long it took."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))
import p5  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for carried in (False, True):
    for temper in sys.argv[1].split(","):
        world, m, log = p5.run_stages(int(sys.argv[2]) if len(sys.argv) > 2 else 800, temper, carried)
        totals = {round(r["total"], 9) for r in world.history}
        stages = "  ".join(f"{w}: {'yes' if ok else 'NO'} ({t}{f', {c} plan crashes' if c else ''})" for w, ok, t, c in log)
        print(f"{'carried' if carried else 'fresh':7} {temper:9} {stages}  conservation {'HOLDS' if len(totals) == 1 else 'BROKEN'}")
