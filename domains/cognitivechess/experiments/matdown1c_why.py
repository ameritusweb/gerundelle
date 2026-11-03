"""When 'material_down' is set as a sub-want: the goal served, the way, and for each split on that way the records in
each half (situation: e8 and material; outcome), with 'brought' against the goal actually served."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from force_world import inv_id  # noqa: E402

w = ChessWorld(RUNG1C, order=8, seed=8, reply="answer", moves=2, relations=RUNG1C_RELATIONS + ("reply", "game"), clean=True)
m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
for k, v in rung1c.ARMS["converge_cost"].items():
    setattr(m.agent.mind.p, k, v)
a, orig, done = m.agent, m.agent.subwant, [False]


def subwant(facts, invs=None):
    out = orig(facts, invs)
    if out == "material_down" and not done[0]:
        done[0] = True
        goal, meta = a.goal, a.mind.meta
        print("serving", goal, "stack", a.stack)
        for inv in a.makers(goal):
            if "material_down" not in a.needs(inv, goal):
                continue
            x = inv_id(inv)
            while x in meta.splits:
                sp = meta.splits[x]
                print(" split", x.split(" ", 1)[-1], "tag", sp["tag"])
                for half in ("yes", "no"):
                    for h in meta.modes.get(sp[half], []):
                        ctx = sorted(f for f in h[1] if f.startswith(("material", "e8", "reply")))
                        print(f"   {half}: brought {goal in h[2]}  situation {ctx}  outcome {sorted(h[2])[:5]}")
                x = sp["yes"] if any(goal in h[2] for h in meta.modes.get(sp["yes"], [])) else sp["no"]
            # what made material_down in the situations of the yes half: the push just before
            break
    return out


a.subwant = subwant
m.run(800)
