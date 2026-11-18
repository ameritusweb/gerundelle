"""Its own pieces' bearings as territory (the user, 2026-11-17: "the gerund changing to 'hanging' should be a loss of territory"; from
the play app: 1. e4 e5 2. c4 Bc5 3. b4, the pawn left hanging). Checks, White to move after 1. e4 e5 2. c4 Bc5:
  B1  every White piece's bearing region is held (none hanging now)
  B2  b2b4 is predicted to leave the b-pawn hanging (white_pawn_b2_bearing_hanging, relative bearing+0_hanging, theirs pressing)
  B3  a move that keeps every piece guarded (d2d3) predicts no piece hanging
  B4  stood for the move made, the b4 prediction is a loss (the region held, the effect another state of it)
  B5  after b4 and Bxb4... no: after b4 the world shows the pawn hanging and the region is lost
python -X utf8 check_bearing.py"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import chess

import rung4p
from chessduel import configure
from plansworld import give

bad = 0


def check(name, ok, detail):
    global bad
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {name}: {detail}")


b = chess.Board()
for san in ("e4", "e5", "c4", "Bc5"):
    b.push_san(san)
w, a = rung4p.build(0, b.fen(), dreams=True, half_moves=10)
configure(a)
w.shown = w.read()
give(a, w)
rows = a.mind.territory.rows
mine = [o for o in w.shown if o.startswith("white_") and o.endswith("_bearing")]
check("B1 held", mine and all(rows.get(o, {}).get("holder") == "mine" for o in mine),
      f"{len(mine)} bearing regions, holders {sorted({rows.get(o, {}).get('holder') for o in mine})}")
preds = w.push_predictions()
b4 = [p for p in preds if "b2b4" in p[4][0] and "_bearing_" in p[0]]
check("B2 b4 predicted hanging", any(p[0] == "white_pawn_b2_bearing_hanging" and p[3] == "bearing+0_hanging" and ("theirs", "bearing+piece:square") in p[2]
                                     for p in b4), f"{[(p[0], p[3], sorted(p[2])) for p in b4]}")
d3 = [p for p in preds if "d2d3" in p[4][0] and p[0].endswith("_bearing_hanging")]
check("B3 d3 predicts no piece hanging", not d3, f"{[p[0] for p in d3]}")
# B4: the register's verdict on the b4 prediction, stood as stand_prediction stands it
row = rows.get("white_pawn_b2_bearing", {})
check("B4 a loss", row.get("holder") == "mine", f"white_pawn_b2_bearing held ({row.get('holder')}): its going hanging is a predicted loss")
# B5: play b4; the world shows the pawn hanging; the region is lost
move = next(m for m in w.board.legal_moves if m.uci() == "b2b4")
w.act((w.label(move), w.ids_at(move.from_square), "present"))
w.act(None)   # (the mind's next slice: what the move did besides the piece moved reaches it then, the prediction's 2 slices)
give(a, w)
check("B5 lost once hanging", w.read().get("white_pawn_b2_bearing") == "hanging" and rows.get("white_pawn_b2_bearing", {}).get("holder") == "lost",
      f"world reads {w.read().get('white_pawn_b2_bearing')}, shown {w.shown.get('white_pawn_b2_bearing')}, holder {rows.get('white_pawn_b2_bearing', {}).get('holder')}")
print("ALL OK" if not bad else f"{bad} BAD")
