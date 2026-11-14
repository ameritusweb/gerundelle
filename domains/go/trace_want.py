"""Where game 6's want for a held point's opportunity to come alive comes from (trace_opp_games_told.log: from slice 1146 the mind held
"opportunity_0_0_breathing", then "opportunity_0_2_breathing", and made a committed fill every 12 slices). Candidate sub-wants come from
open ownership slots (SovAgent.own_candidates): every state the slot's region has been perceived in but its state now, the tournament
choosing among them (the user: no rules). Replays seed 0 and, for every want set on an opportunity region: the slot that offered it, the
region's holder and history, the states it has been seen in, every candidate state of that region at the top level with its bid and
support, and what the mind's relations connect the chosen state to. Then each choice while such a want is held, with its source, and
for a commit what it committed to.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_want.py [to slice, default 1240]"""
import collections
import sys

import run
import sov_agent
from world import opportunity

sys.stdout.reconfigure(encoding="utf-8")
HI = int(sys.argv[1]) if len(sys.argv) > 1 else 1240
a, w = run.build(0, 0.7)
und, terr, mind = a.mind.understanding, a.mind.territory, a.mind
tag = {}
for name in ("planned", "winner", "commit_step"):
    orig = getattr(sov_agent.SovAgent, name)

    def wrap(self, *args, _orig=orig, _name=name, **kw):
        out = _orig(self, *args, **kw)
        if self is a and out is not None and out != "wait":
            tag.setdefault(_name, out)
        return out
    setattr(sov_agent.SovAgent, name, wrap)
read = 0
told = mind.p.credulity
sets_seen = len(a.sub_log)
for t in range(HI):
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    tag.clear()
    commits_before = len(a.__dict__.get("commit_log", []))
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    lv = rec["levels"][-1] if rec.get("levels") else {"bids": {}, "winners": [], "res": {}}
    for tt, g, k in a.sub_log[sets_seen:]:
        if k == "set" and g.startswith("opportunity_"):
            r = a.owner_of(g)
            row = terr.rows.get(r, {})
            slots = [i for i in mind.pool if i.startswith("own:") and i.endswith(":" + r)]
            cands = {i: round(v, 2) for i, v in lv["bids"].items() if i.startswith(f"subwant:{r}_")}
            causes = [(o, [round(x, 2) for x in e]) for (rr, o), e in und.rel.get(g, {}).items() if rr == "causes"][:6]
            caused = [(c, [round(x, 2) for x in rels[("causes", g)]]) for c, rels in und.rel.items() if ("causes", g) in rels][:6]
            print(f"slice {t}: want SET {g}; serving (stack) {[x[:60] for x in a.stack]}; slots on its region {slots}; holder {row.get('holder')}; history {row.get('history', [])[-5:]}; "
                  f"now {w.shown.get(r)}; seen states {sorted(row.get('seen_states', ()))}")
            print(f"    candidates of that region at the top, bids: {cands}; winners {[i for i in lv['winners'] if i.startswith('subwant:')]}")
            print(f"    the state wanted causes: {causes}")
            print(f"    what causes the state wanted: {caused}")
        elif g.startswith("opportunity_"):
            print(f"slice {t}: want {k} {g}")
    sets_seen = len(a.sub_log)
    goal = a.goal
    if choice is not None and invs and goal and goal.startswith(("opportunity_", "all:opportunity_")):
        src = ("commit made" if choice[0] == "commit" else "commitment's step" if tag.get("commit_step") == choice else
               "a want's plan" if tag.get("planned") == choice else "the tournament" if "winner" in tag else "other")
        new_commits = a.__dict__.get("commit_log", [])[commits_before:]
        kind = ""
        if choice[0] == "place":
            kind = "fill" if terr.rows.get(opportunity(w.target(choice)), {}).get("holder") == "mine" else "other"
        print(f"slice {t}:   choice {kind} {choice[1]} {str(choice[2])[:40]} by {src}; want {goal[:70]}; anti {a.__dict__.get('anti')}; "
              f"commits {[(x[1][:90], x[2]) for x in new_commits]}")
