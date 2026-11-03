"""Rung 1c, seed 8, converge with the extended cost, the clean want: the records under Rd8's split on material_down."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

w = ChessWorld(RUNG1C, order=8, seed=8, reply="answer", moves=2,
               relations=RUNG1C_RELATIONS + ("reply", "game"), clean=True)
m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
for k, v in rung1c.ARMS["converge_cost"].items():
    setattr(m.agent.mind.p, k, v)
m.run(400)
meta = m.agent.mind.meta
for x, sp in meta.splits.items():
    if "Rd8" in x and sp["tag"] == "material_down":
        print("split", x, "\n  tag", sp["tag"], "yes", sp["yes"], "no", sp["no"])
        for half in ("yes", "no"):
            for h in meta.modes.get(sp[half], [])[:4]:
                ctx = sorted(f for f in h[1] if f.startswith(("material", "game", "reply", "e8", "d8", "white_rook")))
                print(f"   {half}: outcome {sorted(h[2])[:4]}  situation {ctx}")
