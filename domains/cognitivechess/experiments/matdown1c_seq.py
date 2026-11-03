"""Rung 1c, converge with the extended cost, the clean want, one seed: the episodes in which Rd8 brought the want with
material down when it was played; the moves and what the world said."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

seed = int(sys.argv[1])
w = ChessWorld(RUNG1C, order=seed, seed=seed, reply="answer", moves=2,
               relations=RUNG1C_RELATIONS + ("reply", "game"), clean=True)
m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
for k, v in rung1c.ARMS["converge_cost"].items():
    setattr(m.agent.mind.p, k, v)
a, act, eps = m.agent, w.act, {}


def logged(inv=None, hold=False):
    ep, cfg, before = len(w.episodes), w.config, a.facts_now()
    ev = act(inv, hold)
    e = eps.setdefault(ep, {"cfg": cfg, "rows": []})
    e["rows"].append((inv[0].split(" ", 1)[-1] if inv else "", "material_down" in before, w.board.fen().split()[0], ev))
    return ev


w.act = logged
m.run(800)
shown = 0
for ep, e in eps.items():
    moves = [r for r in e["rows"] if r[0]]
    if any(r[0] == "Rd8" and r[1] for r in moves) and any("game_mate" in x or "-> mate" in x for r in e["rows"] for x in r[3]):
        shown += 1
        print(f"episode {ep} config {e['cfg']}:")
        for mv, down, fen, ev in e["rows"]:
            print(f"   {mv:5} material down before: {down}  {fen}  {[x for x in ev if 'game' in x or 'material' in x or 'reply' in x or 'captured' in x]}")
        if shown >= 3:
            break
