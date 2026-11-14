"""Probe the dream planner (dream.py) in full games: what each dream tried and where the edge was, what waking gave the planner, and the
wants and sub-wants that followed. No want placed: wants arise from the ownership slots (and, with dreams, from what dreams show)."""
import collections
import sys

import dream
import gameworld
import rung4
import shoes
from carry import Carries
from imagine import Imagines

sys.stdout.reconfigure(encoding="utf-8")
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 600


class Game(dream.Remembers, Imagines, gameworld.GameWorld):
    pass


class Player(Carries, rung4.Player):
    def perceive(self):
        self.world.__dict__.pop("_imagined", None)
        inputs, invs = super().perceive()
        self.carry_links(invs)
        self.woken = dream.wake(self, invs)
        return inputs, invs


mind = rung4.learned(1, 1000, True)
w = Game(seed=1)
w.owned = True
w.actor = "White"
a = Player(w, "game", mind=mind)
rung4.switch(a.mind, True)
for k in ("own_wants", "subwants", "sub_yield", "imagine", "dreams"):
    setattr(a.mind.p, k, True)
w.in_their_shoes = shoes.in_their_shoes(a)
terr = a.mind.territory
terr.given = w.white_pieces()
for r in terr.given:
    terr.row(r)
terr.update(terr.given)
black = gameworld.RandomSide(w, 1)
games, subs, woken = 0, collections.Counter(), 0
for r in range(ROUNDS):
    if w.board.turn == 1:
        w.actor = "White"
        for _ in range(rung4.TURN_STEPS):
            n = len([x for x in w.log if x[2]])
            a.tick()
            woken += getattr(a, "woken", 0) or 0
            if len([x for x in w.log if x[2]]) > n:
                break
    else:
        black.tick()
        w.actor = "White"
        a.tick()
    if a.stack:
        subs[a.goal] += 0
    if len(w.games) > games:
        games = len(w.games)
        t, e = dream.dream(a)
        print(f"game {games} ended {w.games[-1][:2]}; dream: {t} trials, {e} at the edge, dream pairs {len(getattr(a, 'dream_pairs', []))}; "
              f"waking so far gave {woken} imagined trials; wants met {len(a.reached)} {[g for _, g in a.reached][-3:]}; goal {a.goal}, stack {a.stack}", flush=True)
        print(f"    dream counts so far: {getattr(a, 'dream_counts', {})}", flush=True)
        for inv, facts, names, edge in [x for x in getattr(a, "dream_edges", [])[-t:] if x[3]][:2]:
            print(f"    at the edge: {inv[0]} by {inv[1]} -> {[(c[:40], a.mind.understanding.open_structure(c)) for c in edge[:3]]}", flush=True)
print("wake counts:", {k: v for k, v in getattr(a, "wake_counts", {}).items() if k != "examples"})
for e in getattr(a, "wake_counts", {}).get("examples", []):
    print("   mapped", e[0], "| the dream's rest on", e[1])
print("reached:", collections.Counter(g for _, g in a.reached).most_common(8))
