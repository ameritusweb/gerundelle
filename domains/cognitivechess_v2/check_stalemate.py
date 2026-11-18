"""Checks the opponent's stalemate plan (plansworld: STALEMATE, stalemate_doing, stalemate_effect, give). On positions with White to
move: the moves predicted to make the plan (`plan_stalemate_made`) are exactly the moves after which python-chess says Black is
stalemated; the plan's doing (none / stoppable / unstoppable) matches the count of such moves; a stalemate board reads `made`; and the
register holds the region at none, contests it at stoppable, loses it at made. python -X utf8 check_stalemate.py"""
import random
import sys

import chess

import rung0  # noqa: F401
import plansworld
from plansgame import PlansGame

sys.stdout.reconfigure(encoding="utf-8")


def predicted(fen):
    w = PlansGame(fen=fen, half_moves=10 ** 6)
    w.actor = "White"
    got = {chain[0].split("_push:")[0].split(" ", 1)[1]: sorted(forces)
           for effect, n, forces, rel, chain in w.push_predictions() if effect == f"{plansworld.STALEMATE}_made"}
    return got, w.shown.get(plansworld.STALEMATE)


def truth(fen):
    b = chess.Board(fen)
    out = set()
    for m in b.legal_moves:
        b.push(m)
        if b.is_stalemate():
            out.add(m.uci())
        b.pop()
    n = b.legal_moves.count()
    doing = "none" if not out else ("unstoppable" if len(out) == n else "stoppable")
    return out, doing


bad = 0
named = [("queen can stalemate (Qg6 with Black's king on h8)", "7k/8/5K2/8/8/8/8/6Q1 w - - 0 1"),
         ("the start", chess.STARTING_FEN)]
for label, fen in named:
    (got, shown), (want, doing) = predicted(fen), truth(fen)
    ok = set(got) == want and shown == doing
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {label}: predicted {got}, reading {shown}; python-chess {sorted(want)}, {doing}")
w = PlansGame(fen="7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", half_moves=10 ** 6)
ok = w.shown.get(plansworld.STALEMATE) == "made"
bad += not ok
print(f"{'ok ' if ok else 'BAD'} a stalemate board reads {w.shown.get(plansworld.STALEMATE)!r} (wanted 'made')")
rng = random.Random(4)
found = checked = tries = 0
while found < 25 and tries < 40000:   # random games, kept where White to move can stalemate Black (and a few where it can't)
    tries += 1
    b = chess.Board()
    for _ in range(rng.randrange(20, 160)):
        ms = list(b.legal_moves)
        if not ms:
            break
        b.push(rng.choice(ms))
    if b.turn != chess.WHITE or b.is_game_over():
        continue
    want, doing = truth(b.fen())
    if not want and checked - found >= 15:
        continue
    got, shown = predicted(b.fen())
    checked += 1
    found += bool(want)
    if set(got) != want or shown != doing:
        bad += 1
        print(f"BAD {b.fen()}: predicted {sorted(got)} {shown}; python-chess {sorted(want)} {doing}")
print(f"random positions {checked} ({found} where White can stalemate; {tries} games)")
import rung4p  # noqa: E402
w2, a = rung4p.build(0, None, dreams=True, half_moves=10 ** 6)
held = []
for doing in ("none", "stoppable", "made"):
    w2.shown[plansworld.STALEMATE] = doing
    plansworld.give(a, w2)
    row = a.mind.territory.rows[plansworld.STALEMATE]
    held.append((doing, row.get("holder")))
ok = [h for _, h in held] == ["mine", "contested", "lost"]
bad += not ok
print(f"{'ok ' if ok else 'BAD'} the register: {held}")
print("ALL OK" if not bad else f"{bad} BAD")
