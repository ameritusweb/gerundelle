"""Rung P11: grievance. A seal that is a state of the jar itself.

P10 found that a mark on a separate lid teaches futility but not grievance: Gerundelle's anger is about a region the
mind holds, undone by another, and the jar a mind held never changed when another locked its lid. SealWorld (lock_world.py)
makes the lock a state of the jar: another's `seal` push changes the jar (`charged sealed by Ben`), a change by another to
a region the mind may hold (its first claim: its dips into the jar took). P9's populations run in it, sub-wants off.

PREDICTION, written before the first run: grievance appears: anger at the sealer, anchored on the jar, in minds that held
the jar it sealed; enclosure goes on as in P9 and P10 (curiosity seals others' jars as readily as lids), and wants met stay
near P9/P10's (1 of 4 steady, 0 of 4 mixed).

Measures: P9's (wants met, seals own/others', lockouts, jars sealed at the end and by whom), and grievance: per mind its
phases, the anger phases with what they are anchored on, and for each seal another set on a jar this mind had claimed
before (its dips took), whether anger followed within 40 ticks.

Run: python -X utf8 p11.py [--ticks 2000] [--tempers steady,steady,steady,steady]
Writes results/p11_<tempers>.json.
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
from lock_world import SealWorld  # noqa: E402


class Grieving(p7.Planning):
    """The mover is visible (my choice, named; fiction rung 5's authored "Leo took it" is the precedent): fiction's look()
    already finds who moved each object in another mind's slice (`movers`) but never writes it into the territory; so
    Gerundelle's anger at "the one who took it" (`taken_by` on a lost region, molecules.Phases) could never form between
    Gerundelle minds. Here, when another mind's move changes a region this mind has held (its claims took: `ever`), the
    mover is written as `taken_by`; whether the region is lost, and whether anger forms, is Gerundelle's own reading."""

    def look(self):
        movers = super().look()
        terr = self.agent.mind.territory
        for o, actor in movers.items():
            row = terr.rows.get(o)
            if row and row.get("ever") and actor != self.name:
                row["taken_by"] = actor
        return movers


def grievance(world, minds, shared):
    out = {}
    for m in minds:
        angers = sorted(p for p in m.phases_seen if ":anger:" in p)
        anger_t = [b.t for b in shared if b.kind == "feel" and b.actor == m.name and b.detail.get("phase") == "anger"]
        claimed = {}   # jar -> first tick this mind's dip into it took
        for t, inv, names in m.agent.tried:
            if inv[1].startswith("jar") and inv[0] != "seal" and any(n.startswith(inv[1] + "_") for n in names):
                claimed.setdefault(inv[1], t)
        sealed_mine = [(t, a, j) for t, a, j in world.shuts if a != m.name and j in claimed and claimed[j] < t]
        followed = sum(1 for t, _, _ in sealed_mine if any(t <= a < t + 40 for a in anger_t))
        out[m.name] = dict(anger=angers, claimed=sorted(claimed), sealed_mine=len(sealed_mine),
                           anger_followed=followed, sealed_mine_by=sorted({a for _, a, _ in sealed_mine}))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--tempers", default="steady,steady,steady,steady")
    ap.add_argument("--blind", action="store_true", help="the mover not written (P11's first runs)")
    args = ap.parse_args()
    tempers = args.tempers.split(",")
    kind = p7.Planning if args.blind else Grieving
    world, minds, shared = p4.run(tempers, args.ticks, subwants=False, kind=kind, world_cls=SealWorld)
    rows, _, conserved = p4.measure(world, minds, shared)
    locks, end = p9.lock_measures(world, minds)
    grief = grievance(world, minds, shared)
    met = sum(r["reached"] for r in rows)
    anger = sum(r["phases"].get("anger", 0) for r in rows)
    print(f"== seals ({'mover not seen' if args.blind else 'mover seen'}): population {tempers}; wants met {met} of {len(rows)}; anger {anger}; slices {world.t}; "
          f"conservation {'HOLDS' if conserved else 'BROKEN'}")
    print(f"{'mind':5} {'temper':9} {'reached':>8} {'pushes':>6} {'sealed own/others':>17} {'locked out':>10}  "
          f"{'claimed jars':>14} {'sealed by others (anger within 40t)':>36}")
    for r in rows:
        k, g = locks[r["name"]], grief[r["name"]]
        print(f"{r['name']:5} {r['temper']:9} {str(r['reached_at']) if r['reached'] else 'no':>8} {r['pushes']:6d} "
              f"{k['shut_own']:>8}/{k['shut_others']:<8} {k['blocked_by_others']:>10}  {','.join(g['claimed']) or '-':>14} "
              f"{g['sealed_mine']:>28} ({g['anger_followed']})")
    for r in rows:
        g = grief[r["name"]]
        print(f"   {r['name']}: phases {r['phases']}; anger {g['anger'] or 'none'}; her claimed jars sealed by "
              f"{g['sealed_mine_by'] or 'nobody'}; locked out by {locks[r['name']]['locked_out_by']}")
    print(f"   jars sealed at the end (jar: keyholder): {end}")
    print(f"   reached: {[(b.t, b.actor, b.obj) for b in shared if b.kind == 'reach']}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"p11_{'-'.join(tempers)}{'_blind' if args.blind else ''}.json"), "w",
              encoding="utf-8") as f:
        json.dump(dict(tempers=tempers, slices=world.t, conservation=conserved, minds=rows, locks=locks, grievance=grief,
                       sealed_at_end=end, shuts=world.shuts, beats=[dataclasses.asdict(b) for b in shared]),
                  f, indent=1, default=str)


if __name__ == "__main__":
    main()
