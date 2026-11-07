"""Trace (LADDER.md, rung 1g): why doesn't a capture the mind has lived win the top level? Seed 0, main mind alone, rung 1f's mind with
Params.imagined_tournament. At every slice where a move that has brought the want before is on offer: what won the top level and with what bids,
the capture's own bid and the highest level it reached, and whether a plan came of it. Run: python -X utf8 trace_tops.py [--seed 0] [--ticks 400]"""
import argparse
import collections
import sys

from rung0 import WANT  # (puts Gerundelle on the path)
from molecules import concept_of
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--off", action="store_true", help="the switch off, to compare")
    ap.add_argument("--want-site", action="store_true")
    args = ap.parse_args()
    w = WarpWorld(RUNG1_TWO, seed=args.seed, moves=2, forces=True)
    a = OfferedMainMind(w, pieces=False, forces=True)
    a.mind.p.imagined_tournament = not args.off
    a.mind.p.want_site = args.want_site
    planned = {"step": None}
    real = a.plan_step

    def plan_step(invs, budget=60, horizon=3):
        planned["step"] = real(invs, budget, horizon)
        return planned["step"]
    a.plan_step = plan_step

    rows = []
    for t in range(args.ticks):
        if a.goal is None:
            a.goal = WANT
        planned["step"] = None
        a.tick()
        rec = a.last_rec
        ways = {inv_id(i) for i, _, names in a.pushed if WANT in names}   # moves that have brought the want
        offered = {inv_id(i) for i in w.invitations()}
        on_offer = ways & offered
        if not on_offer or rec is None:
            continue
        levels = rec["levels"]
        top = levels[-1]["winners"]
        reach = {}
        for L, lv in enumerate(levels):
            for i in lv["winners"]:
                reach[concept_of(i) or i] = L
        for c in on_offer:
            bids0 = levels[0]["bids"]
            mine = [i for i in bids0 if (concept_of(i) or i) == c]
            bid = max((bids0[i] for i in mine), default=None)
            rank0 = sorted(bids0, key=lambda i: -bids0[i])
            rows.append(dict(t=t, c=c, bid=bid, rank0=min((rank0.index(i) for i in mine), default=None), n0=len(bids0),
                             reach=reach.get(c, -1), top=[(i, round(levels[-1]["bids"].get(i, 0), 2)) for i in top],
                             plan=planned["step"] is not None, watching=a.watching is not None))
    print(f"switch {'off' if args.off else 'on'}; slices with a lived capture on offer: {len(rows)}; wants met {len(a.reached)}")
    print("highest level the capture reached (-1 none):", dict(collections.Counter(r["reach"] for r in rows)))
    print("a plan came of it:", sum(r["plan"] for r in rows), "of", len(rows), "; slices spent watching:", sum(r["watching"] for r in rows))
    kinds = collections.Counter(i.split(":")[0] if ":" in i and not "_push:" in i else ("move" if "_push:" in i else "fact/other") for r in rows for i, _ in r["top"])
    print("what held the top level on those slices:", dict(kinds))
    print()
    for r in rows[:12]:
        print(f"t{r['t']} {r['c'][:40]}: bid {r['bid']}, rank at level 0 {r['rank0']} of {r['n0']}, reached level {r['reach']}, plan {r['plan']}")
        print("     top:", r["top"])


if __name__ == "__main__":
    main()
