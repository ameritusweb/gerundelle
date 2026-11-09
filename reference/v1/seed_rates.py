"""Each force-world test arm's pass rate over seeds (gust phases): python seed_rates.py [tests...]."""
import sys
import time

import test_molecules as T
from force_world import phase

FORCE = ["t57", "t59", "t60", "t61", "t62", "t63", "t66", "t67", "t68", "t69", "t71", "t72"]


def rates(name, seeds=range(5)):
    fn = getattr(T, name)
    got = {}
    for s in seeds:
        with phase(s):
            title, arms = fn()
        for arm, _, ok in arms:
            got.setdefault(arm, []).append(bool(ok))
    return title, got


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for name in sys.argv[1:] or FORCE:
        t = time.time()
        title, got = rates(name)
        print(f"{title} ({time.time() - t:.0f} s)", flush=True)
        for arm, oks in got.items():
            print(f"    {sum(oks)}/{len(oks)}  {arm}  {''.join('+' if o else '.' for o in oks)}", flush=True)
