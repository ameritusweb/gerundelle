"""Probe the link (carry.py): carried relations written into the main SOV in a full game, and what they say."""
import collections
import sys

import gameworld
import rung4
from carry import Carries
from imagine import Imagines

sys.stdout.reconfigure(encoding="utf-8")


class Game(Imagines, gameworld.GameWorld):
    pass


class Player(Carries, rung4.Player):
    def perceive(self):
        inputs, invs = super().perceive()
        self.carry_links(invs)
        return inputs, invs


mind = rung4.learned(1, 1000, True)
w = Game(seed=1)
w.owned = True
w.actor = "White"
a = Player(w, "game", mind=mind)
rung4.switch(a.mind, True)
for k in ("own_wants", "subwants", "sub_yield", "imagine"):
    setattr(a.mind.p, k, True)
terr = a.mind.territory
terr.given = w.white_pieces()
for r in terr.given:
    terr.row(r)
terr.update(terr.given)
black = gameworld.RandomSide(w, 1)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
for r in range(ROUNDS):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            n = len([x for x in w.log if x[2]])
            a.tick()
            if len([x for x in w.log if x[2]]) > n:
                break
    else:
        black.tick()
        w.actor = "White"
        a.tick()
carried = a.carried or set()
print("lived pairs:", len(getattr(a, "_pairs", {})), "| carried relations:", len(carried))
print("what they say (state carried):", collections.Counter(k[2].split("_")[-1] if not k[2].startswith(("material", "standing")) else k[2] for k in carried).most_common(10))
for k in sorted(carried)[:8]:
    print("  ", k[0][:34], "causes", k[2], "| from", a.liens[k][:34])
print("games:", [g[:2] for g in w.games])
