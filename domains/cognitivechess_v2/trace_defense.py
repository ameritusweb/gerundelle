"""Why a fresh mind with the felt loss on (defense_still, computed before the tournament) chooses a move that leaves a piece hanging
(check_plan_pull.py, plan_as_pull on: Ne2 or Ke2, 10 of 10). One mind, seed 0, the g5 position, the outpost want: each slice, the
defense of the moves at the top, their bids, the plan pull, and what was chosen and by which route."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import chess

import mate_oracle
import rung4p
from chessduel import configure
from league import PROFILES
from plansworld import give, read_mate_passed

from sov_agent import SovAgent
_yields = SovAgent.yields


def yields_traced(self, step, invs):
    st = self.stakes(invs) or {}
    out = _yields(self, step, invs)
    import re
    m_ = re.search(r"(\d+ [^_]+_push:.*)$", step)
    under = m_.group(1) if m_ else None
    print(f"   [gate] step {step[:60]}… -> {under}; in stakes {under in st}; its stakes {st.get(under)}; best {max(st.values(), default=None)}; "
          f"stakes keys like {list(st)[:2]}; yields {out}")
    return out


SovAgent.yields = yields_traced
b0 = chess.Board()
for san in ("c4", "e5", "e4", "Bc5", "g4", "d6"):
    b0.push_san(san)
w, a = rung4p.build(0, b0.fen(), dreams=True, half_moves=4)
configure(a, PROFILES["accepting_patient"])
w.shown = w.read()
give(a, w)
a.goal, a.stack, a.sub_since = "potential:plan_outpost+2_none", [], a.mind.t
uci = lambda c: c.split("_push")[0].split(" ", 1)[-1]
for t in range(12):
    n0 = w.moved
    a._route = None
    choice, rec = a.tick()
    read_mate_passed(a, choice)
    give(a, w)
    d = a.mind.__dict__.get("anti_defense") or {}
    top = rec["levels"][-1]
    pushes = sorted([x for x in top["winners"] if "_push:" in x and x[:3].isdigit()], key=lambda x: -top["bids"].get(x, 0))
    print(f"slice {t}: goal {a.goal}; plan_pull {a.mind.__dict__.get('plan_pull')}; defense nonzero for {sum(1 for v in d.values() if v)} moves "
          f"(min {min(d.values(), default=0)}); experiments {rec.get('experiments')[:1]}")
    print("   top pushes (bid, defense):", [(uci(x), round(top["bids"].get(x, 0), 2), d.get(x.split("|")[0])) for x in pushes[:6]])
    exps = rec.get("experiments") or []
    if exps:
        steps = (a.mind.inquiry.plans.get(exps[0]) or (None, None, []))[2]
        invs_ = {f"{i[0]}_push:{i[1]}_{i[2]}": i for i in w.invitations()}
        st = a.stakes(invs_) or {}
        print("   experiment", exps[0][:90], "steps", [s_[:70] for s_ in steps], "| experimentation", a.mind.p.experimentation,
              "| stakes best", max(st.values(), default=None), "| step in stakes", steps and steps[0] in st,
              "| yields", steps and a.yields(steps[0], invs_), "| yields log", a.__dict__.get("experiment_yields"))
    print("   chose", None if choice is None else (choice[0] if choice[0] in ("commit", "ask") else uci(f"{choice[0]}_push")),
          "route", a.__dict__.get("_route"), "queue", a.__dict__.get("queue"), "running", a.__dict__.get("running"))
    if w.moved > n0:
        break
mate_oracle.close()
