"""What makes each fill (trace_opp_games_losses.log: with predicted losses the anti-want held_bearing holds and no fill reaches the top
level on most endgame turns, yet the mind fills every third slice, often committed). SovAgent.tick picks a push, in order, from: a
commitment's next step (commit_step), a held want with a way known (planned), an experiment under way (queue) or starting
(rec["experiments"]), the tournament's winner (winner). Replays seed 0 and tags each choice of the mind's in the window with the path that
made it, the want held, and for a planned step, what the plan rests on; for a commit, what it committed to.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_choice_source.py [from slice, to slice]"""
import collections
import sys

import run
import sov_agent
from world import opportunity

sys.stdout.reconfigure(encoding="utf-8")
LO, HI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (380, 492)
a, w = run.build(0, 0.7)
und, terr, mind = a.mind.understanding, a.mind.territory, a.mind
tag = {}
for name in ("planned", "winner", "commit_step", "commit_to"):
    orig = getattr(sov_agent.SovAgent, name)

    def wrap(self, *args, _orig=orig, _name=name, **kw):
        out = _orig(self, *args, **kw)
        if self is a and out is not None and out != "wait":
            tag.setdefault(_name, out)
        return out
    setattr(sov_agent.SovAgent, name, wrap)
read = 0
tally = collections.Counter()
for t in range(HI):
    a.mind.potentials = w.potentials()
    invs = w.invitations()
    tag.clear()
    queue_before, running_before = list(a.queue), a.running
    goal = a.goal
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if t < LO or choice is None or not invs:
        continue
    if choice[0] == "commit":
        src = "commit made (commit_to)"
    elif "commit_step" in tag and tag["commit_step"] == choice:
        src = "commitment's next step"
    elif "planned" in tag and tag["planned"] == choice:
        src = "a want's plan (planned)"
    elif queue_before or (rec.get("experiments") and not tag.get("winner")):
        src = "an experiment"
    elif "winner" in tag:
        src = "the tournament's winner"
    else:
        src = "?"
    kind = "pass"
    if choice[0] == "place":
        c = w.target(choice)
        kind = "fill" if terr.rows.get(opportunity(c), {}).get("holder") == "mine" else "other"
    elif choice[0] == "commit":
        kind = "commit on " + ("a loss" if "opportunity+0_bearing" in choice[1] or "_breathing" in choice[1] else "a gain")
    tally[(kind, src)] += 1
    extra = ""
    if src.startswith("a want"):
        iid = f"place_push:{choice[1]}_{choice[2]}"
        extra = f" | its links to the want: {[(r, o, [round(x, 2) for x in e]) for (r, o), e in und.rel.get(iid, {}).items() if o == goal][:3]}"
    print(f"slice {t}: {kind} {choice[1]} {str(choice[2])[:60]} by {src}; want {goal}; anti {a.__dict__.get('anti')}{extra}")
print("\nchoices in the window, by kind and source:", sorted(tally.items(), key=lambda x: -x[1]))
print("commits made in the window:", [(t, c) for t, c, k, *_ in a.__dict__.get("commit_log", []) if k == "made" and t >= LO])
print("commit outcomes:", collections.Counter(k for t, c, k, *_ in a.__dict__.get("commit_log", [])))
