"""Checks plansgame.PlansGame with no mind: random White moves against random Black replies from the rulebook's start. Before each White
move, the world's predictions for every move on offer; then for the move made, the plans read right after it (Black to move, before its
answer) against what was predicted for it: every predicted change shows, and every plan ended or created was predicted (a change of
stoppability on a plan already there is the tool's, not predicted). Also the time per White turn.
Run: python -u -X utf8 check_plansgame.py [White moves] [seed]"""
import collections
import random
import sys
import time

import rung0  # noqa: F401
from gameworld import RandomSide
from plansgame import PlansGame

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0
w = PlansGame(seed=SEED)
black = RandomSide(w, SEED)
rng = random.Random(SEED)
checked, missed, unpredicted, tool_kind, times = 0, [], [], collections.Counter(), []
made = 0
while made < N and not w.over():
    if w.board.turn:   # White
        w.actor = "White"
        before = dict(w.read_plans())
        t0 = time.time()
        preds = w.push_predictions()
        times.append(time.time() - t0)
        invs = w.invitations()
        inv = rng.choice(invs)
        push = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
        mine = {e for e, n, f, rel, chain in preds if chain == (push,)}
        w.act(inv)
        made += 1
        after = w.read_plans()   # the board right after the move, Black to answer
        for e in mine:
            obj, doing = e.rsplit("_", 1)
            checked += 1
            if after.get(obj, "none") != doing:
                missed.append((made, inv[0], e, after.get(obj, "none")))
        for obj in set(before) | set(after):
            a, b = before.get(obj, "none"), after.get(obj, "none")
            if a == b:
                continue
            if a != "none" and b != "none":
                tool_kind[(a, b)] += 1   # stoppability of a plan already there: the tool's
            elif f"{obj}_{b}" not in mine:
                unpredicted.append((made, inv[0], obj, a, b))
        print(f"White move {made} {inv[0]}: {len(preds)} changes predicted over {len(invs)} moves in {times[-1]:.1f}s", flush=True)
    else:
        black.tick()
print(f"predicted changes checked {checked}; not shown {len(missed)}; plans ended or created unpredicted {len(unpredicted)}; "
      f"stoppability changes (the tool's) {dict(tool_kind)}; predictions {sum(times) / len(times):.1f}s a turn on average, {max(times):.1f}s at most")
for x in (missed + unpredicted)[:8]:
    print("  ", x)
