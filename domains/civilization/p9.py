"""Rung P9: a lock. Possession as physics, and what a population does with it.

P8 found that a mind defends its state only by remaking it, and that defending as distinct from remaking needs a way to
stop another's push. LockWorld (lock_world.py) gives each station's jar a lid that, shut, opens only to the hand that
shut it, and keeps every hand out of the jar meanwhile. P4's populations run in it, sub-wants off (P4's minds) and on
(P7's), against their numbers in StationsWorld.

PREDICTION, written before the first run: nothing tells a mind which lid is its own, and curiosity pushes everything, so
minds shut lids at random, others' as often as their own. A mind finds its own jar locked by another and cannot fill it:
blocked pushes, frustration, anger at the one who locked it. Possession without norms is enclosure: wants met fall
below P4/P7 (1-2 of 4), and interference (changes on others' stations) falls too, as locked jars cannot be emptied.

Measures: P4's (wants met, own-station share, changes on others' stations, phases incl. anger, give-ups); and the locks:
lids each mind shut (its own station's, others'), pushes the locks stopped (by whom, whose lock), and lids still shut at
the end and whose.

Run: python -X utf8 p9.py [--ticks 2000] [--tempers steady,steady,steady,steady] [--only off,on]
Writes results/p9_<tempers>_<off|on>.json.
"""
import argparse
import dataclasses
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import p4  # noqa: E402
import p7  # noqa: E402
from lock_world import LockWorld  # noqa: E402


def lock_measures(world, minds):
    out = {}
    for m in minds:
        mine = f"lid{m.station}"
        shut = [lid for _, a, lid in world.shuts if a == m.name]
        stopped = [(o, k) for _, a, o, k in world.blocked if a == m.name]
        out[m.name] = dict(shut_own=sum(1 for l in shut if l == mine), shut_others=sum(1 for l in shut if l != mine),
                           blocked=len(stopped), blocked_by_others=sum(1 for _, k in stopped if k != m.name),
                           blocked_by_self=sum(1 for _, k in stopped if k == m.name),
                           locked_out_by=dict(Counter(k for _, k in stopped if k != m.name)))
    end = {lid: world.keyholder.get(lid) for lid, g in world.gerund.items() if lid.startswith("lid") and g.startswith("shut")}
    if hasattr(world, "seal"):   # P11's seals are on the jars themselves
        end = dict(world.seal)
    return out, end


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--only", default="off,on")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for mode in args.only.split(","):
        on = mode == "on"
        world, minds, shared = p4.run(tempers, args.ticks, subwants=on, kind=p7.Planning, world_cls=LockWorld)
        rows, shared_regions, conserved = p4.measure(world, minds, shared)
        locks, end = lock_measures(world, minds)
        met = sum(r["reached"] for r in rows)
        anger = sum(r["phases"].get("anger", 0) for r in rows)
        print(f"== locks, sub-wants {mode}: population {tempers}; wants met {met} of {len(rows)}; anger {anger}; "
              f"slices {world.t}; conservation {'HOLDS' if conserved else 'BROKEN'}")
        print(f"{'mind':5} {'temper':9} {'reached':>8} {'gave up':>7} {'pushes':>6} {'own':>5} {'changed':>7}  "
              f"{'shut own/others':>15} {'blocked (by others/self)':>24}  phases")
        for r in rows:
            k = locks[r["name"]]
            print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} "
                  f"{'yes' if r['gave_up'] else 'no':>7} {r['pushes']:6d} {r['own_share']:5.2f} {r['changed_others']:7d}  "
                  f"{k['shut_own']:>7}/{k['shut_others']:<7} {k['blocked']:>10} ({k['blocked_by_others']}/{k['blocked_by_self']})"
                  f"{'':8}  {r['phases']}")
        for name, k in locks.items():
            if k["locked_out_by"]:
                print(f"   {name} was locked out by {k['locked_out_by']}")
        print(f"   lids shut at the end (lid: keyholder): {end}")
        print(f"   reached: {[(b.t, b.actor, b.obj, b.detail.get('by', 'own push')) for b in shared if b.kind == 'reach']}")
        with open(os.path.join(HERE, "results", f"p9_{'-'.join(tempers)}_{mode}.json"), "w", encoding="utf-8") as f:
            json.dump(dict(tempers=tempers, subwants=on, slices=world.t, conservation=conserved, minds=rows, locks=locks,
                           shut_at_end=end, shuts=world.shuts, blocked=world.blocked,
                           beats=[dataclasses.asdict(b) for b in shared]), f, indent=1, default=str)
        print()


if __name__ == "__main__":
    main()
