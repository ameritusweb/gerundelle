"""Checks plansworld.PlansWorld.push_predictions with no mind (PLAN.md step 3): the world played by random moves from the ladder's
rooms; for each move made, every plan change predicted for it shows in the slice predicted, and every plan whose doing changed after the
move was predicted (what the relevance shortcut, re-checking stoppability only for plans a move touches, would miss). Also the time.
Run: python -u -X utf8 check_plans_effects.py [moves per room]"""
import random
import sys
import time

import rung0  # noqa: F401
from plansworld import PlansWorld
from warpworld import RUNG1_TWO, RUNG2B

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
rng = random.Random(3)
checked, missed, unpredicted, times = 0, [], [], []
for fen in (RUNG1_TWO, RUNG2B):
    w = PlansWorld(fen, seed=0, moves=1000)
    made = 0
    while made < N:
        invs = w.invitations()
        if not invs:
            w.act(None)
            continue
        t0 = time.perf_counter()
        preds = w.push_predictions()
        times.append(time.perf_counter() - t0)
        inv = rng.choice(invs)
        pid = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
        mine = {(e, n) for e, n, f, rel, ch in preds if ch == (pid,)}
        before = {o: v for o, v in w.shown.items() if o.startswith("plan_")}
        w.act(inv)
        w.act(None)   # the slice the move's consequences land in
        after = {o: v for o, v in w.shown.items() if o.startswith("plan_")}
        for e, n in mine:
            checked += 1
            o, v = e.rsplit("_", 1)
            if after.get(o) != v:
                missed.append((fen[:10], inv[0], e, after.get(o)))
        predicted = {e for e, n in mine}
        for o in after:
            if after[o] != before.get(o) and f"{o}_{after[o]}" not in predicted:
                unpredicted.append((fen[:10], inv[0], o, before.get(o), after[o]))
        made += 1
        print(f"{fen[:12]} move {made} {inv[0]}: {len(mine)} changes predicted, read in {times[-1]:.1f}s", flush=True)
print(f"predicted changes checked {checked}; not shown {len(missed)}; changed unpredicted {len(unpredicted)}; "
      f"push_predictions {sum(times) / len(times):.1f}s a slice on average, {max(times):.1f}s at most")
for x in missed[:5]:
    print("  missed:", x)
for x in unpredicted[:8]:
    print("  unpredicted:", x)
import collections
kinds = collections.Counter((x[3], x[4]) for x in unpredicted)
print("unpredicted by change (before -> after):", dict(kinds))
print("unpredicted plans ended or created (must be 0):", sum(n for (a, b), n in kinds.items() if "none" in (a, b)))
