"""Checks the win condition's potential effect (plansworld.PlansWorld.push_predictions, win_effect): on positions with White to move,
the moves predicted to bring `outcome_white_won` are exactly the moves python-chess says checkmate, with their relative force structure;
and a won game becomes territory for good (plansworld.give). python -X utf8 check_win.py"""
import random
import sys

import chess

import rung0  # noqa: F401  (Gerundelle on the path)
from plansgame import PlansGame

sys.stdout.reconfigure(encoding="utf-8")


def fen_after(*sans):
    b = chess.Board()
    for s in sans:
        b.push_san(s)
    return b.fen()


def predicted_wins(fen):
    w = PlansGame(fen=fen, half_moves=10 ** 6)
    w.actor = "White"
    out = {}
    for effect, n, forces, rel, chain in w.push_predictions():
        if effect == "outcome_white_won":
            label = chain[0].split("_push:")[0]
            out[label.split(" ", 1)[1]] = (rel, n, sorted(forces))
    return out


def mates(fen):
    b = chess.Board(fen)
    out = set()
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.add(m.uci())
        b.pop()
    return out


bad = 0
named = [("scholar's mate available (Qxf7#)", fen_after("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6")),
         ("back rank (Ra8#)", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"),
         ("no mate (rook, bishop and knight against a sheltered king)", "6k1/5ppp/8/8/8/8/B7/R3N1K1 w - - 0 1"),
         ("the start: no mate", chess.STARTING_FEN)]
for label, fen in named:
    got, want = predicted_wins(fen), mates(fen)
    ok = set(got) == want
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {label}: predicted {got}; python-chess mates {sorted(want)}")
rng = random.Random(3)
checked = with_mate = 0
structures = {}
tries = 0
while with_mate < 40 and tries < 20000:   # random games, kept where White to move has a mate in one (and a few without)
    tries += 1
    b = chess.Board()
    for _ in range(rng.randrange(10, 120)):
        ms = list(b.legal_moves)
        if not ms:
            break
        b.push(rng.choice(ms))
    if b.turn != chess.WHITE or b.is_game_over():
        continue
    want = mates(b.fen())
    if not want and checked - with_mate >= 20:
        continue
    got = predicted_wins(b.fen())
    checked += 1
    with_mate += bool(want)
    for rel, n, forces in got.values():
        structures[tuple(f for f in forces)] = structures.get(tuple(f for f in forces), 0) + 1
    if set(got) != want:
        bad += 1
        print(f"BAD random {b.fen()}: predicted {sorted(got)}, mates {sorted(want)}")
print(f"random positions {checked} ({with_mate} with a mate in one; {tries} games): {'all agree' if not bad else 'see above'}; "
      f"force structures of the mates: {structures}")


class Stub:   # a minimal agent for give(): the register's track_region on a real mind
    pass


import rung4p  # noqa: E402
w, a = rung4p.build(0, None, dreams=True, half_moves=10 ** 6)
w.games.extend([("1-0", 9, 40), ("1/2-1/2 (stalemate)", 3, 60), ("1-0", 12, 33)])
import plansworld  # noqa: E402
plansworld.give(a, w)
rows = {r: (row.get("holder"), row.get("for_good")) for r, row in a.mind.territory.rows.items() if r.startswith("won_game_")}
ok = rows == {"won_game_1": ("mine", True), "won_game_3": ("mine", True)}
bad += not ok
print(f"{'ok ' if ok else 'BAD'} won games as territory for good: {rows}")
print("ALL OK" if not bad else f"{bad} BAD")
