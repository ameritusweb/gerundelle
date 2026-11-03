"""Rung P10: the mark. A lock that shows whose hand shut it.

P9 found enclosure without grievance: a mind locked out of its jar 63 times by the same mind felt frustration, not anger,
because a stopped push changes nothing and nothing it perceived linked the lock to a hand. Here LockWorld's `marks`: a
shut lid's state names its keeper (`lid1: shut by Ben`). So "a lid shut by Ben" and "a lid shut by me" are different
pushes, a failed dip can be conditioned on `lid1_shut_by_Ben`, and Ben's act shows on the lid. P9's populations run with
marks, against P9 (no marks), sub-wants off (they did not engage in a crowd at P7-P9).

PREDICTION, written before the first run: attribution enters knowledge (minds learn conditions that name another's
lock: "the jar fills only when lid1 is not shut by Ben"); anger still does not come (Gerundelle's anger needs a region the
mind held undone by another, and a locked-out mind rarely held the lid); behaviour barely changes: the mark is perception,
not a norm, so minds still shut others' lids, and wants met stay near P9's.

Measures: P9's (wants met, locks shut own/others', lockouts, lids shut at the end, anger), and attribution: per mind, the
learned conditions (splits) whose tag names a keeper, another mind or itself; and pushes on lids shut by others against
lids shut by itself, in the first and second halves of the run (does a mind stop pushing locks that never open for it?).

Run: python -X utf8 p10.py [--ticks 2000] [--tempers steady,steady,steady,steady]
Writes results/p10_<tempers>.json.
"""
import argparse
import dataclasses
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import p4  # noqa: E402
import p7  # noqa: E402
import p9  # noqa: E402
from lock_world import LockWorld  # noqa: E402


def marked(n):
    return LockWorld(n, marks=True)


def attribution(world, minds):
    out = {}
    half = world.t / 2
    for m in minds:
        tags = [sp["tag"] for sp in m.agent.mind.meta.splits.values()]
        naming = [t for t in tags if "_shut_by_" in t]
        others = [t for t in naming if not t.endswith("_by_" + m.name)]
        lid_pushes = [(t, inv) for t, inv, _ in m.agent.tried if inv[1].startswith("lid") and inv[2].startswith("shut by")]
        theirs = lambda early: sum(1 for t, inv in lid_pushes if not inv[2].endswith(m.name) and (t < half) == early)
        out[m.name] = dict(conditions_naming=naming, naming_others=len(others),
                           pushes_on_others_locks=(theirs(True), theirs(False)),
                           pushes_on_own_locks=sum(1 for _, inv in lid_pushes if inv[2].endswith(m.name)))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    world, minds, shared = p4.run(tempers, args.ticks, subwants=False, kind=p7.Planning, world_cls=marked)
    rows, _, conserved = p4.measure(world, minds, shared)
    locks, end = p9.lock_measures(world, minds)
    attr = attribution(world, minds)
    met = sum(r["reached"] for r in rows)
    anger = sum(r["phases"].get("anger", 0) for r in rows)
    print(f"== marked locks: population {tempers}; wants met {met} of {len(rows)}; anger {anger}; slices {world.t}; "
          f"conservation {'HOLDS' if conserved else 'BROKEN'}")
    print(f"{'mind':5} {'temper':9} {'reached':>8} {'pushes':>6} {'shut own/others':>15} {'locked out':>10}  "
          f"{'pushes on others locks (1st/2nd half)':>38} {'own':>4}  conditions naming a keeper")
    for r in rows:
        k, a = locks[r["name"]], attr[r["name"]]
        print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} {r['pushes']:6d} "
              f"{k['shut_own']:>7}/{k['shut_others']:<7} {k['blocked_by_others']:>10}  "
              f"{str(a['pushes_on_others_locks']):>38} {a['pushes_on_own_locks']:>4}  {a['conditions_naming']}")
    for r in rows:
        print(f"   {r['name']}: phases {r['phases']}; locked out by {locks[r['name']]['locked_out_by']}")
    print(f"   lids shut at the end (lid: keyholder): {end}")
    print(f"   reached: {[(b.t, b.actor, b.obj) for b in shared if b.kind == 'reach']}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"p10_{'-'.join(tempers)}.json"), "w", encoding="utf-8") as f:
        json.dump(dict(tempers=tempers, slices=world.t, conservation=conserved, minds=rows, locks=locks,
                       attribution=attr, shut_at_end=end, beats=[dataclasses.asdict(b) for b in shared]),
                  f, indent=1, default=str)


if __name__ == "__main__":
    main()
