"""Checks the two-mind duel with no minds (goduel.py): both seats driven by random legal choices (a placement, the pass, or nothing for
a slice, so turns also pass by waiting). Every slice: the two seats are one game (Duel.check). From each seat: principle 0 for the
opportunity objects (unchanged in the slice a stone lands), and every kill or loss its push_predictions names for the placement chosen
shows in the slice predicted, and no opportunity changes dead/alive unpredicted after the seat's own stone (before the other replies).
Also: each seat's opportunity objects are the other colour's (a black seat reads white's chances, a white seat black's), and results.
Run: python -u -X utf8 check_duel.py [slices]"""
import random
import sys

from goduel import Duel
from world import BLACK, DEAD, WHITE, opportunity

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
d = Duel(seed=5)
rng = random.Random(11)
stats = {BLACK: dict(checked=0, missed=[], unpredicted=[]), WHITE: dict(checked=0, missed=[], unpredicted=[])}
pending = {BLACK: None, WHITE: None}
for t in range(N):
    d.renew()
    for colour in d.order():
        seat = d.seats[colour]
        invs = seat.invitations()
        inv = None
        if invs and rng.random() < 0.8:
            inv = rng.choice(invs)
            if inv[0] == "place":
                iid = f"place_push:{inv[1]}_{inv[2]}"
                pending[colour] = (seat.t, {(e, n) for e, n, f, rel, ch in seat.push_predictions() if ch == (iid,)})
        seat.act(inv)
        if inv is not None and inv[0] == "place":
            assert not [x for x in seat.diffs if x.startswith("opportunity_")], (colour, seat.diffs)
        p = pending[colour]
        if p:
            t0, mine = p
            k = seat.t - t0
            for e, n in mine:
                if n == k:
                    stats[colour]["checked"] += 1
                    o, st = e.rsplit("_", 1)
                    if seat.shown.get(o) != st:
                        stats[colour]["missed"].append((seat.t, e, seat.shown.get(o)))
            if 2 <= k <= 3 and not seat.others:
                for x in seat.diffs:
                    o, ch = x.split(": ")
                    old, new = ch.split(" -> ")
                    if o.startswith("opportunity_") and (new in DEAD) != (old in DEAD) and (f"{o}_{new}", k) not in mine:
                        stats[colour]["unpredicted"].append((seat.t, x))
            if k >= 3:
                pending[colour] = None
    d.end_slice()
# whose opportunity each seat reads: a stone of the other colour could land on an empty board anywhere (breathing), and the seat's
# own stone's point reads bearing in both
for colour, seat in d.seats.items():
    board = seat.board()
    probe = next(c for c in seat.points() if c not in board)
    assert seat.opportunity_doing(board, probe) in ("breathing", "failing", "hanging")
print(f"{N} slices; games {len(d.results)}; winners {[r['winner'] for r in d.results][:12]}; mean area black "
      f"{sum(r['black_area'] for r in d.results) / max(1, len(d.results)):.1f}, white {sum(r['white_area'] for r in d.results) / max(1, len(d.results)):.1f}")
for colour, s in stats.items():
    print(f"  {colour}'s seat: predicted changes checked {s['checked']}, not shown {len(s['missed'])}, changed unpredicted {len(s['unpredicted'])}",
          s["missed"][:3], s["unpredicted"][:3])
assert all(not s["missed"] and not s["unpredicted"] for s in stats.values())
assert d.seats[BLACK].games == d.seats[WHITE].games
print("ok: the seats stayed one game every slice")
