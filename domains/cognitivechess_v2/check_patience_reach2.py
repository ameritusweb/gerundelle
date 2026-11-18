"""Params.patience_reach, exercised directly: the game-12 mind (patience 6) is handed the league's stuck want,
potential:plan_outpost+1_none, as its held want at the start of a game against random Black; each slice: whether a move on offer leads to
it, and whether it steps aside. Switch off and on. Expectations written before the run:
  Q1 (on): the want steps aside within 7 slices of its first slice out of reach (6 in a row, read off the last slice's readings).
  Q2 (off): it is still held after 20 slices unless met.
python -X utf8 check_patience_reach2.py"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from chessduel import configure, fresh_seat
from gameworld import RandomSide
from plansworld import give, read_mate_passed
from rung4p import load_run

WANT = "potential:plan_outpost+1_none"
for on in (False, True):
    a, w0, _, _ = load_run("checkpoints/rung4p_full_s0_g12.pkl")
    w = fresh_seat(a, True, old=w0, half_moves=300)
    configure(a, dict(patience=6))
    a.mind.p.patience_reach = on
    a.goal, a.stack, a.sub_since = WANT, [], a.mind.t
    black = RandomSide(w, 5)
    trace, first_out, gone = [], None, None
    for s in range(30):
        if not w.board.turn:
            black.tick()
        w.actor = "White"
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        reach = a.within_reach(WANT)
        if not reach and first_out is None:
            first_out = s
        trace.append(("R" if reach else ".") + ("" if a.goal == WANT else "s"))
        if WANT not in (a.goal, *a.stack) and gone is None:
            gone = (s, next((k for t, g, k in reversed(a.sub_log) if g == WANT), "?"))
            break
    print(f"patience_reach {'on ' if on else 'off'}: reach per slice {''.join(trace)}; first out of reach at slice {first_out}; "
          f"the want left at {gone}")
mate_oracle.close()
