"""The pool of fork rooms for the lifelong coverage test (PLAN.md, coverage, L1-L3): positions from seeded random games, White to move,
not in check, no uncovered set now, and at least one move on offer that would uncover one (the covers-on world's own reading). Each
room: its FEN, its walk-in moves (uci), its number of moves on offer. -> cover_rooms.json
python -X utf8 cover_rooms.py [rooms]"""
import json
import random
import sys

import chess

import rung0  # noqa: F401
from plansgame import PlansGame
from plansworld import COVER

n_rooms = int(sys.argv[1]) if len(sys.argv) > 1 else 40
rng = random.Random(17)
rooms, tries = [], 0
while len(rooms) < n_rooms and tries < 5000:
    tries += 1
    b = chess.Board()
    for _ in range(rng.randrange(8, 60)):
        if b.is_game_over():
            break
        b.push(rng.choice(list(b.legal_moves)))
    if b.is_game_over() or not b.turn or b.is_check():
        continue
    w = PlansGame(seed=0, fen=b.fen())
    w.covers_read = True
    r = w.read()
    if any(s == "uncovered" for o, s in r.items() if o.startswith(COVER)):
        continue
    w.shown = r
    walk = sorted({p[4][0].split("_push")[0].split(" ", 1)[1] for p in w.push_predictions()
                   if p[0].startswith(COVER) and p[0].endswith("_uncovered")})
    if not walk:
        continue
    rooms.append(dict(fen=b.fen(), walk=walk, moves=b.legal_moves.count()))
    print(f"room {len(rooms)} (try {tries}): {len(walk)} walk-ins of {b.legal_moves.count()} moves: {b.fen()}", flush=True)
json.dump(rooms, open("cover_rooms.json", "w"), indent=1)
base = sum(len(r["walk"]) / r["moves"] for r in rooms) / len(rooms)
print(f"{len(rooms)} rooms; a random move walks in {base:.1%} of the time")
