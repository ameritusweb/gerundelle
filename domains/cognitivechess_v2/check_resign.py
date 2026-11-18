"""Checks Black's resignation after the 7th new forced mate (gameworld.RESIGN_AFTER_NEW_MATES): a world where the count reaches it on
White's move is over, shows White outcome_white playing -> won, and records "1-0 (Black resigned ...)"; the next game starts unresigned
with the count at 0. python -X utf8 check_resign.py"""
import sys

import rung0  # noqa: F401
from gameworld import GameWorld

sys.stdout.reconfigure(encoding="utf-8")
bad = 0
w = GameWorld(half_moves=10 ** 6)
w.actor = "White"
w.has_moved.add("White")
w.new_mates_game = 6
# the 7th new forced mate, counted inside White's move as play() counts it (the reading stubbed: this move reaches a new one)
w.qualifies = lambda before, move, after: True
w.read_mate = lambda board: ("new", ("a new position",), 3)
m = next(iter(w.board.legal_moves))
w.act((w.label(m), w.ids_at(m.from_square), "present"))
checks = [("over", w.over(), True), ("outcome", w.outcome, "won"), ("shown to White", w.pend["White"].get("outcome_white"), ("playing", "won"))]
w.reset()
checks += [("recorded", w.games[-1][0], "1-0 (Black resigned after 7 new forced mates)"),
           ("next game: resigned", w.resigned, None), ("next game: count", w.new_mates_game, 0), ("next game: over", w.over(), False)]
for label, got, want in checks:
    ok = got == want
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {label}: {got!r} (wanted {want!r})")
print("ALL OK" if not bad else f"{bad} BAD")
