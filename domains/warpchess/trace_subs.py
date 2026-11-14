"""Trace (rung 4, own_wants + subwants, placed goal as probe v8): why are sub-wants not met? For each sub-want while it is the goal:
how the moves were chosen (plan, experiment, attention), whether the planner returned a way, and whether the wanted state ever held."""
import collections
import sys

import gameworld
import rung4

sys.stdout.reconfigure(encoding="utf-8")
mind = rung4.learned(1, 1000, True)
w = gameworld.GameWorld(seed=1)
w.owned = True
w.actor = "White"
a = rung4.Player(w, "game", mind=mind)
rung4.switch(a.mind, True)
a.mind.p.own_wants = True
a.mind.p.subwants = True
terr = a.mind.territory
terr.given = w.white_pieces()
for r in terr.given:
    terr.row(r)
terr.update(terr.given)
black = gameworld.RandomSide(w, 1)
how = {"v": None, "plan_tried": 0, "plan_found": 0}
planned, winner, did = a.planned, a.winner, a.mind.inquiry.did
real_plan = a.plan_step
def ps(invs, budget=60, horizon=3):
    s = real_plan(invs, budget, horizon)
    how["plan_tried"] += 1
    how["plan_found"] += s is not None
    return s
a.plan_step = ps
def p(invs):
    s = planned(invs)
    if s is not None: how["v"] = "plan"
    return s
def wn(rec, invs):
    s = winner(rec, invs)
    if s is not None: how["v"] = "attention"
    return s
def d(eid):
    how["v"] = "experiment"
    return did(eid)
a.planned, a.winner, a.mind.inquiry.did = p, wn, d
spans = []   # (sub-want, start slice, moves by how, plans tried, plans found, held at any point, end)
cur = None
for r in range(600):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            if a.goal is None:
                a.goal = rung4.GOAL
            n = len([x for x in w.log if x[2]])
            how["v"] = None
            a.tick()
            if len([x for x in w.log if x[2]]) > n:
                if cur: cur["how"][how["v"]] += 1
                break
    else:
        black.tick()
        w.actor = "White"
        a.tick()
    g = a.goal if a.stack else None
    if (cur and cur["want"]) != g:
        if cur: cur["end"] = a.mind.t; spans.append(cur)
        cur = dict(want=g, start=a.mind.t, how=collections.Counter(), p0=how["plan_tried"], f0=how["plan_found"], held=False) if g else None
    if cur:
        cur["held"] |= g in a.facts_now()
        cur["plans"] = (how["plan_tried"] - cur["p0"], how["plan_found"] - cur["f0"])
for s in spans + ([cur] if cur else []):
    print(f"{s['want']}: slices {s['start']}-{s.get('end')}, moves {dict(s['how'])}, plans tried/found {s.get('plans')}, state ever held {s['held']}")
