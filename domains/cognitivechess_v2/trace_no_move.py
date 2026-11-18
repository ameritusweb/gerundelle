"""Why a mind makes no move in check (the play app: 1. d4 d5 2. Na3 e6 3. Qd3 Bb4+, White to move, no move in 400 slices). A fresh mind
with the app's settings (the league's configure, accepting_patient, coverage on) in the position; each slice: the moves on offer, the
pushes at the top of its tournament with their bids and defense, the plan pull, experiments, the route and the choice."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import chess

import mate_oracle
import rung4p
from chessduel import configure
from league import PROFILES
from plansworld import give, read_mate_passed

b0 = chess.Board()
for san in ("d4", "d5", "Na3", "e6", "Qd3", "Bb4+"):
    b0.push_san(san)
w, a = rung4p.build(0, b0.fen(), dreams=True, half_moves=300)
configure(a, PROFILES["accepting_patient"])
w.covers_read = True
w.shown = w.read()
give(a, w)
uci = lambda c: c.split("_push")[0].split(" ", 1)[-1]
print("legal:", [m.uci() for m in w.board.legal_moves], "| offered:", [i[0] for i in w.invitations()])
for t in range(30):
    n0 = w.moved
    a._route = None
    choice, rec = a.tick()
    read_mate_passed(a, choice)
    give(a, w)
    d = a.mind.__dict__.get("anti_defense") or {}
    top = rec["levels"][-1]
    pushes = [x for x in top["winners"] if "_push:" in x and x[:3].isdigit()]
    others = sorted([x for x in top["winners"] if x not in pushes], key=lambda x: -top["bids"].get(x, 0))[:3]
    print(f"s{t}: chose {None if choice is None else choice[0]}; route {a.__dict__.get('_route')}; quiet {a.quiet}; goal {a.goal}; "
          f"pull {a.mind.__dict__.get('plan_pull')}; exp {(rec.get('experiments') or [None])[0]}; queue {a.queue}; watching {bool(a.watching)}; "
          f"asking {bool(a.__dict__.get('asking'))}; committed {bool(a.__dict__.get('committed'))}")
    print(f"     top pushes {[(uci(x), round(top['bids'].get(x, 0), 2), d.get(x.split('|')[0])) for x in pushes]}; other top "
          f"{[(x[:50], round(top['bids'].get(x, 0), 2)) for x in others]}")
    if w.moved > n0:
        print("MOVED")
        break
mate_oracle.close()
