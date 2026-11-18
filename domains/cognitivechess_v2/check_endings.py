"""Checks the game world's endings by the rules (gameworld.GameWorld.over, draw_reason, reset's recorded result): insufficient material,
threefold repetition, checkmate, stalemate, and that the start is not over. python -X utf8 check_endings.py"""
import sys

import rung0  # noqa: F401  (Gerundelle on the path)
from gameworld import GameWorld

sys.stdout.reconfigure(encoding="utf-8")
bad = 0


def play(w, ucis):
    for u in ucis:
        m = next(m for m in w.board.legal_moves if m.uci() == u)
        w.play(m)
        w.moved += 1


def result_after_reset(w):
    w.reset()
    return w.games[-1][0]


def expect(label, got, want):
    global bad
    ok = got == want
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {label}: {got!r} (wanted {want!r})")


w = GameWorld(fen="8/8/8/4k3/8/8/8/4KN2 w - - 0 1", half_moves=10 ** 6)
expect("king and knight against king: draw reason", w.draw_reason(), "insufficient material")
expect("  over", w.over(), True)

w = GameWorld(half_moves=10 ** 6)
expect("the start: over", w.over(), False)
play(w, ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"])
expect("after the start's position twice: not yet", w.draw_reason(), None)
play(w, ["f6g8"])
expect("the start's position a third time: draw reason", w.draw_reason(), "threefold repetition")
expect("  recorded result", result_after_reset(w), "1/2-1/2 (threefold repetition)")

w = GameWorld(half_moves=10 ** 6)
play(w, ["f2f3", "e7e5", "g2g4", "d8h4"])
expect("fool's mate: over", w.over(), True)
expect("  recorded result", result_after_reset(w), "0-1")

w = GameWorld(fen="7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", half_moves=10 ** 6)
expect("stalemate (Black's king on h8, White's queen on f7): over", w.over(), True)
w.moved = 1
expect("  recorded result", result_after_reset(w), "1/2-1/2 (stalemate)")
print("ALL OK" if not bad else f"{bad} BAD")
