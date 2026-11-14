"""Trace rung 2: why does White's main mind alone win material more often than White with piece minds?
For every White turn: did it move within its slices, how the move was chosen (plan, experiment, winner of attention), whether
a capture was on offer, whether the move captured, and in the pieces arm whose idea the winner was.
Run: python -X utf8 trace_rung2_white.py --white pieces|alone [--seed 5] [--rounds 600]"""
import argparse
import collections
import sys

import rung2
from duel import WarpDuel
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import RUNG2B


def captures_on_offer(w):
    out = set()
    for label, m in w.offers().items():
        b = w.board.copy()
        before = sum(1 for s in range(len(b.pieces)) if b.pieces[s] and not b.colors[s])
        b.push(m)
        if sum(1 for s in range(len(b.pieces)) if b.pieces[s] and not b.colors[s]) < before:
            out.add(label)
    return out


def instrument(a):
    a.how = None
    planned, winner, did = a.planned, a.winner, a.mind.inquiry.did

    def p(invs):
        s = planned(invs)
        if s is not None:
            a.how = "plan"
        return s

    def wn(rec, invs):
        s = winner(rec, invs)
        if s is not None:
            a.how = "attention"
        return s

    def d(eid):
        a.how = "experiment"
        return did(eid)
    a.planned, a.winner, a.mind.inquiry.did = p, wn, d


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--white", default="pieces")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=600)
    ap.add_argument("--patience", type=int, default=None)
    args = ap.parse_args()
    w = WarpDuel(RUNG2B, seed=args.seed)
    w.actor = "White"
    white = OfferedMainMind(w, pieces=args.white == "pieces", forces=True, side="white", situational=True)
    white.mind.p.patience = args.patience
    w.actor = "Black"
    black = OfferedMainMind(w, pieces=True, forces=True, side="black", situational=True)
    minds = {"White": white, "Black": black}
    wants = {"White": "standing_white_up", "Black": "standing_black_up"}
    instrument(white)
    turns, offer_log = [], []
    for r in range(args.rounds):
        side = "White" if w.board.turn else "Black"
        w.actor = side
        a = minds[side]
        caps = captures_on_offer(w) if side == "White" else set()
        offered_now = sorted(w.offers()) if side == "White" else []
        k0 = len(white.offered)
        moved, how, slices, label, origin = False, None, 0, None, None
        for _ in range(rung2.TURN_STEPS + (min(args.patience, w.horizon) if args.patience else 0)):   # as rung2.py: both sides
            if a.goal is None:
                a.goal = wants[side]
            n = len([x for x in w.log if x[2]])
            white.how = None
            k = len(white.offered)
            a.tick()
            slices += 1
            if len([x for x in w.log if x[2]]) > n:
                moved, how, label = True, white.how, w.log[-1][1]
                if side == "White" and white.pieces and white.watching:
                    cid = inv_id(white.watching[0])
                    who = sorted({p for t, p, c in white.offered[k:] if c == cid})
                    origin = ",".join(x.split("_")[1] for x in who) if who else "none"
                break
        if side == "White":
            turns.append(dict(r=r, ep=len(w.episodes), moved=moved, how=how, slices=slices, caps=len(caps), took=label in caps if label else False, label=label, capl=sorted(caps), offered=offered_now, origin=origin, goal=white.goal, quiet_slices=slices if not moved else None, fails=white.mind.territory.rows.get(white.mind.understanding.owners.get('standing_white_up') or 'standing_white', {}).get('fails'), gave=len(white.gave_up), ideas=sorted({(pp.split('_')[1], c) for t, pp, c in white.offered[k0:]}), pgoals={pp: pm.goal for pp, pm in white.pieces.items()}))
        other = "Black" if side == "White" else "White"
        w.actor = other
        minds[other].tick()
    n = len(w.episodes)
    for half, sel in (("early", lambda t: t["ep"] < n // 2), ("late", lambda t: t["ep"] >= n // 2)):
        ts = [t for t in turns if sel(t)]
        moved = [t for t in ts if t["moved"]]
        print(f"{args.white} {half}: White turns {len(ts)}, moved {len(moved)} ({len(moved) / max(1, len(ts)):.2f}), slices per move {sum(t['slices'] for t in moved) / max(1, len(moved)):.2f}")
        print("   how:", dict(collections.Counter(t["how"] for t in moved)))
        if white.pieces:
            print("   origin:", dict(collections.Counter(t["origin"] for t in moved)))
        c = [t for t in ts if t["caps"]]
        print(f"   turns with a capture on offer {len(c)}, moved {sum(t['moved'] for t in c)}, took it {sum(t['took'] for t in c)}; by how:",
              dict(collections.Counter((t["how"], t["took"]) for t in c if t["moved"])))
    ups = [(i[0], sorted(names)) for i, f, names in white.pushed if any("standing_white" in x for x in names)]
    print("pushes the main mind lived:", len(white.pushed), "with a standing change:", len(ups))
    print("   which moves brought standing_white up:", dict(collections.Counter(i for i, names in ups if "standing_white_up" in names).most_common(6)))
    late = [t for t in turns if t["ep"] >= n // 2 and t["caps"] and t["how"] == "plan" and not t["took"]][:8]
    for t in late:
        print("   plan, capture on offer, not taken:", t["label"], "| captures:", t["capl"])
    import json; json.dump(dict(n=n, turns=turns, offers=offer_log, gave_up=white.gave_up), open(f"trace_white_{args.white}_p{args.patience}_s{args.seed}.json", "w"))
    print("episodes", n, "White up", sum(x > 0 for x in w.episodes), "down", sum(x < 0 for x in w.episodes))


if __name__ == "__main__":
    main()
