"""Rung 1c, converge with the extended cost, the clean want: each time the sub-want 'material_down' is set, the way it
came from (a push that has brought the want), that way's needs, and the split chain behind the need."""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1c  # noqa: E402
from chessworld import RUNG1C, RUNG1C_RELATIONS, ChessWorld  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402
from force_world import inv_id  # noqa: E402

seeds, shown = int(sys.argv[1]), collections.Counter()
for seed in range(seeds):
    w = ChessWorld(RUNG1C, order=seed, seed=seed, reply="answer", moves=2,
                   relations=RUNG1C_RELATIONS + ("reply", "game"), clean=True)
    m = GerundelleMind("White", w, want="game_mate", want_count=10 ** 6)
    for k, v in rung1c.ARMS["converge_cost"].items():
        setattr(m.agent.mind.p, k, v)
    a = m.agent
    orig = a.subwant

    def subwant(facts, invs=None):
        out = orig(facts, invs)
        if out == "material_down" and shown[seed] < 2:
            shown[seed] += 1
            for inv in a.makers(a.goal):
                needs = a.needs(inv, a.goal)
                if "material_down" in needs:
                    x, chain, meta = inv_id(inv), [], a.mind.meta
                    while x in meta.splits:
                        sp = meta.splits[x]
                        brought = lambda h: sum(1 for r in meta.modes.get(h, []) if a.goal in r[2])
                        chain.append((sp["tag"], f"yes brought {brought(sp['yes'])}/{len(meta.modes.get(sp['yes'], []))}",
                                      f"no brought {brought(sp['no'])}/{len(meta.modes.get(sp['no'], []))}"))
                        x = sp["yes"] if brought(sp["yes"]) else sp["no"]
                    print(f"seed {seed} t{a.mind.t}: way {inv[0]} (config {w.config}) needs {needs}\n   splits {chain}")
                    break
        return out
    a.subwant = subwant
    m.run(800)
