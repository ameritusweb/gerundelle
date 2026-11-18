"""Why a potential want stays held for a whole game (the league's explanations: patient held "potential:plan_outpost+1_none" from move 1
to 20; its 18... Qxa1+ was planned toward it and predicted it, and it stayed). The game-12 mind against random Black; each prediction
that stands for a held potential want's own kind is caught with the register's verdict (loss or not), the region's row and its showing,
and the want's life (set, met, dropped) is followed. python -X utf8 trace_stuck_want.py [slices]"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from chessduel import fresh_seat
from gameworld import RandomSide
from plansworld import give, read_mate_passed
from rung4p import load_run
from sov_agent import SovAgent

slices = int(sys.argv[1]) if len(sys.argv) > 1 else 300
caught = []
orig = SovAgent.stand_prediction


def stand(self, effect, n0, n, rel, pid, by_):
    goal = self.goal
    region = self.owner_of(effect)
    row = dict(self.mind.territory.rows.get(region, {}))
    shown = self.world.shown.get(region)
    ins = orig(self, effect, n0, n, rel, pid, by_)
    if goal == f"potential:{rel}":
        caught.append(dict(t=self.mind.t, effect=effect, loss=ins.get("loss"), holder=row.get("holder"),
                           held=sorted(row.get("held_states", ()) or ()), shown=shown, met=self.goal != goal, by=by_[:22]))
    return ins


SovAgent.stand_prediction = stand
a, w0, _, _ = load_run("checkpoints/rung4p_full_s0_g12.pkl")
w = fresh_seat(a, True, old=w0, half_moves=300)
black = RandomSide(w, 5)
log0 = len(a.sub_log)
print("goal at load:", a.goal, "| stack:", a.stack)
timeline = []   # (slice, goal, the moves on offer predicted to bring it, the move made or None, its route)
for _ in range(slices):
    if w.over():
        break
    if not w.board.turn:
        black.tick()
    w.actor = "White"
    a._route = None
    goal = a.goal
    choice, _ = a.tick()
    read_mate_passed(a, choice)
    give(a, w)
    leads = a.__dict__.get("push_leads", {}) or {}
    bring = sorted(c.split("_push")[0] for c, pots in leads.items() if goal in pots) if goal else []
    made = choice[0] if choice is not None and choice[0] not in ("commit", "ask") else None
    timeline.append((a.mind.t, goal, bring, made, (a.__dict__.get("_route") or (None,))[0]))
runs, cur = [], None
for t, g, bring, made, route in timeline:
    if cur is None or cur[0] != g:
        cur = [g, t, t, 0, 0, Counter()]
        runs.append(cur)
    cur[2] = t
    cur[3] += bool(bring)
    if made:
        cur[4] += 1
        cur[5][("toward it" if made.split("_push")[0] in bring else "not toward it", route)] += 1
print("the goal's runs (goal, first slice, last slice, slices with a move on offer predicted to bring it, moves made, the moves by kind):")
for g, t0, t1, nb, nm, kinds in runs:
    print(f"  {str(g)[:70]}: slices {t0}-{t1}, bringable in {nb}, moves {nm} {dict(kinds)}")
life = a.sub_log[log0:]
pots = Counter((g, k) for t, g, k in life if g.startswith("potential:"))
print(f"half-moves {w.moved}; potential wants' events: {dict(pots)}")
print(f"stood predictions of the held want's own kind: {len(caught)}; as losses {sum(1 for c in caught if c['loss'])}; "
      f"met {sum(1 for c in caught if c['met'])}")
print("by the region's holder at the time:", dict(Counter((c["holder"], c["loss"]) for c in caught)))
for c in caught[:10]:
    print(f"  t{c['t']} {c['effect']}: loss {c['loss']}, met {c['met']}; row {c['holder']} held {c['held']}; showing {c['shown']}; by {c['by']}")
mate_oracle.close()
