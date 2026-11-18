"""Checks coverage (plansworld: cover_ regions; impossible_demands.md, the user's option A, 2026-11-17) on built positions, White to move:
  fork        Black's king boxed in by its rook and pawns (no White check), its knight on c2 forks White's rook a1 and queen e1, and no White piece can take it: each plan stoppable alone, the pair
              uncovered (one of them falls)
  fork taken  the same with a White bishop on d1, which takes the knight: the pair covered (one move ends both)
  one threat  only the rook attacked: no set
  (sets a move on offer would uncover are named as the board is read, none, held: so the walk-in's sets stand before it)
  walk in     the queen on d2 guards c2 (Qxc2 ends the threat to a1); Qd2-e1 walks into the fork: predicted cover_..._uncovered, with p0
              (the queen answered the a1 plan before the move); and the region is territory: lost when uncovered (give)
python -X utf8 check_covers.py"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import rung0  # noqa: F401  (Gerundelle on the path)
from plansgame import PlansGame
from plansworld import COVER

bad = 0


def world(fen):
    w = PlansGame(seed=0, fen=fen)
    w.covers_read = True
    w.shown = w.read()
    return w


def covers(w):
    return {o: s for o, s in w.read().items() if o.startswith(COVER)}


def check(name, ok, detail):
    global bad
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {name}: {detail}")


PAIR = "cover_plan_piece_a1_and_plan_piece_e1"
w = world("6rk/6pp/8/8/8/8/2n5/R3Q1K1 w - - 0 1")
c = covers(w)
plans_now = {o: s for o, s in w.read().items() if o.startswith("plan_piece") and s != "none"}
check("fork", c.get(PAIR) == "uncovered" and plans_now.get("plan_piece_a1") == "stoppable" and plans_now.get("plan_piece_e1") == "stoppable",
      f"covers {c}; plans {plans_now}")

w = world("6rk/6pp/8/8/8/8/2n5/R2BQ1K1 w - - 0 1")
c = covers(w)
check("fork taken", c.get(PAIR) == "covered" and "uncovered" not in c.values(), f"covers {c} (Bxc2 ends both: covered, named because a "
      f"move taking the bishop off c2 would uncover it)")

w = world("6rk/6pp/8/8/8/8/2n5/R5K1 w - - 0 1")
c = covers(w)
check("one threat", not c, f"covers {c}")

w = world("6rk/6pp/8/8/8/8/2nQ4/R5K1 w - - 0 1")
c = covers(w)
preds = [p for p in w.push_predictions() if p[0].startswith(COVER)]
walk = [p for p in preds if "d2e1" in p[4][0]]
check("walk in: the walk-in sets named before, none (held)", c and set(c.values()) == {"none"} and PAIR in c, f"covers {c}")
check("walk in: Qd2-e1 predicted to uncover a1 and e1",
      any(p[0] == f"{PAIR}_uncovered" and ("p0", "cover") in p[2] and p[3] == "cover+2_uncovered" for p in walk),
      f"{[(p[0], sorted(p[2]), p[3]) for p in walk]}")
others = sorted((p[4][0].split("_push")[0], p[0]) for p in preds if "d2e1" not in p[4][0])
print(f"    other moves predicted to change coverage: {others}")

# territory: the region lost while uncovered, contested while covered (give, on a fresh mind)
from rung4p import build
w2, a = build(0, "6rk/6pp/8/8/8/8/2n5/R3Q1K1 w - - 0 1")
w2.covers_read = True
w2.shown = w2.read()
from plansworld import give
give(a, w2)
row = a.mind.territory.rows.get(PAIR)
check("territory: uncovered is lost", row is not None and row.get("holder") == "lost", f"{PAIR}: {row and row.get('holder')}")
print("ALL OK" if not bad else f"{bad} BAD")
