"""The first run, traced by game (run.py's setup): for each game, the stones each side took, and of the mind's turns with a group to
take on offer (a placement of potential force 3), how many it took one on; against a player placing a random legal stone in the same
world (the same seed and luck), the same counts. Run: python -u -X utf8 trace_first.py [slices] [--luck 0.7] [--seed 0]"""
import collections
import random
import sys
import time

import run
from world import BLACK, GoWorld

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1200
luck = float(sys.argv[sys.argv.index("--luck") + 1]) if "--luck" in sys.argv else 0.7
seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 0


def report(name, w, per_game):
    for k, g in enumerate(w.games):
        offered, took_one, turns = per_game.get(k, (0, 0, 0))
        print(f"  {name} game {k + 1}: took {g['black_took']}, lost {g['white_took']}; luck after {g['luck']}; area {g['black_area']} to {g['white_area']}; "
              f"a group on offer in {offered} of {turns} turns, taken in {took_one}", flush=True)


# the mind
a, w = run.build(seed, luck)
per_game, read, t0 = {}, 0, time.time()
for t in range(N):
    pots = w.potentials()
    a.mind.potentials = pots
    game = len(w.games)
    choice, rec = a.tick()
    read, _ = run.give(a, w, read)
    if choice is not None and pots:
        o, k, n = per_game.get(game, (0, 0, 0))
        hang = any(f == 3.0 for f in pots.values())
        per_game[game] = (o + hang, k + (pots.get(f"place_push:{choice[1]}_free") == 3.0), n + 1)
    if (t + 1) % 200 == 0:
        terr = a.mind.territory
        print(f"    slice {t + 1} ({time.time() - t0:.0f}s): luck {w.luck} ({w.earned} games kept better), regions {len(terr.rows)}, slots open {len(terr.open_slots())}, "
              f"goal {a.goal}", flush=True)
print(f"the mind, seed {seed}, luck from {luck}: {N} slices in {time.time() - t0:.0f}s")
report("mind", w, per_game)
terr = a.mind.territory
print("  slots open:", collections.Counter((k, run.kind(r)) for k, r in terr.open_slots()).most_common(8))
print("  wants set:", collections.Counter(g.rsplit("_", 1)[-1] + " on a " + run.kind(g.rsplit("_", 1)[0]) for _, g, k in a.sub_log if k == "set" and not g.startswith("all:")).most_common(8))
print("  anti-wants:", collections.Counter(k for _, _, k in a.__dict__.get("anti_log", [])).most_common())
answers = a.__dict__.get("prediction_answers", [])
print("  predictions answered:", collections.Counter((o, "own push" if by != "wait" else "wait") for _, _, o, by in answers).most_common())

# a random player in the same world, luck held where the mind's began
w2 = GoWorld(seed=seed, luck=luck)
w2.earn = lambda: None
rng, per2 = random.Random(1), {}
for t in range(N):
    w2.renew()
    invs = w2.invitations()
    pots = w2.potentials()
    inv = rng.choice(invs) if invs else None
    game = len(w2.games)
    w2.act(inv)
    if inv is not None:
        o, k, n = per2.get(game, (0, 0, 0))
        per2[game] = (o + any(f == 3.0 for f in pots.values()), k + (pots.get(f"place_push:{inv[1]}_free") == 3.0), n + 1)
print(f"a random player, the same world, luck held at {luck}:")
report("random", w2, per2)
