"""Checks White's opportunity forces and their push predictions with no mind (the user, 2026-11-12: territory is the opponent's dead
opportunity forces, go/go-design.md). Black places random legal stones; at each of its turns every predicted kill of each placement is
checked against the world's own play for the placement chosen: the effect must show in the slice predicted (n acts after the one the
stone lands in counts as 1), and only then. Also: principle 0 for the opportunity objects (unchanged in a landing slice), and that every
opportunity that dies in the slices after a black stone, before White replies, was predicted.
Run: python -u -X utf8 check_opportunity.py [slices]"""
import random
import sys

from world import BLACK, DEAD, GoWorld

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
w = GoWorld(seed=3, luck=0.0)
rng = random.Random(7)
checked, hit, missed, unpredicted, kinds = 0, 0, [], [], {}
pending = None   # (slice the stone landed in, {(effect, n)}, the opportunities before)
for t in range(N):
    w.renew()   # (as the agent does each slice: a game over is set back)
    invs = w.invitations()
    inv = None
    if invs:
        preds = w.push_predictions()
        inv = rng.choice(invs)
        if inv[0] == "place":
            iid = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
            mine = {(e, n) for e, n, f, rel, chain in preds if chain == (iid,)}
            before = {o: s for o, s in w.shown.items() if o.startswith("opportunity_")}
            pending = (w.t, mine, before)
            for e, n, f, rel, chain in preds:
                if chain == (iid,):
                    kinds[rel] = kinds.get(rel, 0) + 1
    landing_t = w.t
    w.act(inv)
    if pending and inv is not None and inv[0] == "place":   # principle 0: no opportunity changes in the landing slice
        assert not [d for d in w.diffs if d.startswith("opportunity_")], w.diffs
    if pending:
        t0, mine, before = pending
        k = w.t - t0   # acts since (the landing act is 1)
        for e, n in sorted(mine):
            if n == k:
                checked += 1
                (hit := hit + 1) if e[:e.rfind("_")] in w.shown and f"{e[:e.rfind('_')]}_{w.shown[e[:e.rfind('_')]]}" == e else missed.append((t, e, n, w.shown.get(e[:e.rfind('_')])))
        if 2 <= k <= 3 and not w.others:   # what died, not by the other's stone
            for d in w.diffs:
                o, ch = d.split(": ")
                old, new = ch.split(" -> ")
                if o.startswith("opportunity_") and (new in DEAD) != (old in DEAD) and (f"{o}_{new}", k) not in mine:
                    unpredicted.append((t, d))
        if k >= 3:
            pending = None
print(f"{N} slices, {len(w.games)} games: predicted kills checked {checked}, shown as predicted {hit}, not shown {len(missed)}; "
      f"died unpredicted {len(unpredicted)}")
print("relative effects predicted:", sorted(kinds.items(), key=lambda x: -x[1])[:12])
for m in missed[:5]:
    print("  missed:", m)
for u in unpredicted[:5]:
    print("  unpredicted:", u)
assert not missed and not unpredicted
print("ok")
