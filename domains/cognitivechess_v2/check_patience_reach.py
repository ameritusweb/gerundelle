"""Params.patience_reach (the user, 2026-11-17: "let patience also count slices where no move on offer leads to the want"). The game-12
mind as patient (patience 6) against random Black, the switch off and on, the same seed: how long wants are held, and whether any
want is held out of reach for more than patience slices with it on. Expectations written before the run:
  P1 (on): no want is held more than 6 slices in a row out of reach.
  P2 (on): wants stepped aside come back (are set again) when a move leads to them, at least once in the run.
python -X utf8 check_patience_reach.py [slices]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from chessduel import configure, fresh_seat
from gameworld import RandomSide
from plansworld import give, read_mate_passed
from rung4p import load_run

slices = int(sys.argv[1]) if len(sys.argv) > 1 else 200
for on in (False, True):
    a, w0, _, _ = load_run("checkpoints/rung4p_full_s0_g12.pkl")
    w = fresh_seat(a, True, old=w0, half_moves=300)
    configure(a, dict(patience=6))
    a.mind.p.patience_reach = on
    black = RandomSide(w, 5)
    log0 = len(a.sub_log)
    longest, run, prev = 0, 0, None
    for _ in range(slices):
        if w.over():
            break
        if not w.board.turn:
            black.tick()
        w.actor = "White"
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        g = a.goal
        out = g is not None and not a.within_reach(g)
        run = run + 1 if (out and g == prev) else (1 if out else 0)
        prev = g
        longest = max(longest, run)
    ev = Counter(k for t, g, k in a.sub_log[log0:])
    stepped = [g for t, g, k in a.sub_log[log0:] if k == "stepped_aside"]
    back = sum(1 for g in set(stepped) if any(gg == g and k == "set" and t > min(tt for tt, g2, k2 in a.sub_log[log0:] if g2 == g and k2 == "stepped_aside")
                                              for t, gg, k in a.sub_log[log0:]))
    print(f"patience_reach {'on ' if on else 'off'}: half-moves {w.moved}; want events {dict(ev)}; longest run held out of reach {longest} "
          f"slices; stepped aside {len(stepped)}, of which set again later {back}")
print("P1: met if 'on' shows a longest run <= 6; P2: met if 'on' shows some set again later")
mate_oracle.close()
