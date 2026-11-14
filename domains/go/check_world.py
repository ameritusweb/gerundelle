"""Checks of the Go force world with no mind (world.py): known answers set up by landing stones directly, then random legal play.
Run: python -X utf8 check_world.py [slices]"""
import random
import sys

from world import BLACK, WHITE, GoWorld, point

sys.stdout.reconfigure(encoding="utf-8")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000


def settle(w, n=3):
    """Slices with no stone placed by either side (the other's turn is held off)."""
    out = []
    for _ in range(n):
        turn, w.turn = w.turn, None
        out.append(list(w.act(None)))
        w.turn = turn
    return out


def setup(stones, size=7):
    w = GoWorld(seed=0, size=size)
    for colour, c in stones:
        w.land(c, colour)
        settle(w)
    w.turn = BLACK
    return w


# 1. a corner stone with one breath left: the mind's stone takes it, a slice at a time (principle 0)
w = setup([(WHITE, (0, 0)), (BLACK, (1, 0))])
inv = ("place", point((0, 1)), "free_alone_taking_breathing")
assert inv in w.invitations(), w.invitations()
assert w.potentials()["place_push:point_0_1_free_alone_taking_breathing"] == 3.0, w.potentials()
stone = w.at[(0, 0)]
d0 = w.act(inv)
assert [d.split(":")[0] for d in d0 if "None ->" not in d] == ["point_0_1"], d0   # only the point changes; the stone comes into view
assert w.potential_effects() and w.potential_effects()[0][0] == f"{stone}_coming_apart", w.potential_effects()
print("  the structure predicted:", sorted(w.potential_effects()[0][2]), "->", w.potential_effects()[0][3])
turn, w.turn = w.turn, None
d1 = w.act(None)
assert any(d.startswith(f"{stone}: ") and d.endswith("-> coming_apart") for d in d1) and any(d.startswith("black_0_up") or d.startswith("black_0_left") for d in d1) is False, d1
d2 = w.act(None)
assert "point_0_0: bearing -> barring_white" in d2 and stone not in w.objs and stone in w.kept and stone in w.taken, d2
assert not w.others, w.others
print("1. capture in the corner: ok;", d0, "|", d1, "|", [d for d in d2 if "point" in d])

# 2. a stone that couldn't hold isn't on offer; one that takes what presses it is
w = setup([(WHITE, (1, 0)), (WHITE, (0, 1))])
assert not any(i[1] == point((0, 0)) for i in w.invitations())
w = setup([(WHITE, (1, 0)), (WHITE, (0, 1)), (BLACK, (2, 0)), (BLACK, (1, 1)), (BLACK, (0, 2))])
assert ("place", point((0, 0)), "free_alone_taking_breathing") in w.invitations() and w.potentials()["place_push:point_0_0_free_alone_taking_breathing"] == 3.0
print("2. no stone where it couldn't hold, unless it takes what presses it: ok")

# 3. no taking straight back
w = setup([(BLACK, (1, 0)), (BLACK, (0, 1)), (BLACK, (1, 2)), (WHITE, (2, 1)), (WHITE, (3, 0)), (WHITE, (3, 2)), (WHITE, (2, 2)), (BLACK, (2, 0))])
# white takes (2,0)? set a simple ko: black at (1,1) is taken by white at ... built directly below instead
w = setup([(BLACK, (1, 0)), (BLACK, (0, 1)), (BLACK, (1, 2)), (WHITE, (2, 0)), (WHITE, (3, 1)), (WHITE, (2, 2)), (WHITE, (1, 1))])
inv = next(i for i in w.invitations() if i[1] == point((2, 1)))   # black takes the white stone at (1,1)
assert w.potentials()[f"place_push:{inv[1]}_{inv[2]}"] == 3.0
w.act(inv)
w.turn = None
w.act(None), w.act(None)
assert (1, 1) not in w.at
w.turn = WHITE
assert (1, 1) not in w.legal(WHITE), "white may not take straight back"
print("3. no taking straight back: ok")

# 4. random legal play on both sides: games end, stones are taken, nothing breathless stays, principle 0 holds in every landing slice
for luck in (0.0, 0.7):
    w = GoWorld(seed=1, luck=luck)
    rng = random.Random(5)
    hanging = turns = 0
    for t in range(N):
        w.renew()
        invs = w.invitations()
        inv = rng.choice(invs) if invs else None
        if invs:
            turns += 1
            hanging += any(f == 3.0 for f in w.potentials().values())
        before = dict(w.shown)
        placed = w.placed
        w.act(inv)
        if w.placed != placed:   # a stone landed: nothing already in view changed but its point (and the hand, once its stone is placed)
            changed = [o for o, st in w.shown.items() if o in before and before[o] != st]
            new = set(w.stone_objs(w.at[w.last_point]))
            assert set(changed) - new == {point(w.last_point)}, (t, changed)
        if w.settled():
            assert not w.crossed(w.board(), BLACK) and not w.crossed(w.board(), WHITE), t
        assert len(w.at) == len(w.colour) == sum(1 for o in w.objs if o.count("_") == 1 and not o.startswith("point") and not o.endswith("_breath"))
    g = w.games
    print(f"4. luck {luck}: {len(g)} games in {N} slices; stones a game {min(x['stones'] for x in g)}-{max(x['stones'] for x in g)}; "
          f"taken over the run: by black {w.captures[BLACK]}, by white {w.captures[WHITE]}; lucky replies {w.lucky}; "
          f"mean area black {sum(x['black_area'] for x in g) / len(g):.1f}, white {sum(x['white_area'] for x in g) / len(g):.1f}; "
          f"objects ever named {len(w.kept | set(w.objs))}; turns with a group to take on offer {hanging} of {turns}")

# 5. the eye read as a force, and the breath gerund by whose turn it is: a black ring around (1,1) with breath outside
w = setup([(BLACK, (1, 0)), (BLACK, (0, 1)), (BLACK, (2, 1)), (BLACK, (1, 2)), (BLACK, (0, 0)), (BLACK, (2, 0)), (BLACK, (0, 2)), (BLACK, (2, 2))])
assert w.read()["point_1_1"] == "barring_white", w.read()["point_1_1"]      # white couldn't hold there: the group breathes outside
assert w.read()["black_breath"] == "breathing"
for c in [(3, 0), (3, 1), (3, 2), (0, 3), (1, 3), (2, 3)]:   # white takes every breath outside
    w.land(c, WHITE)
    settle(w)
w.turn = BLACK
r = w.read()
assert r["point_1_1"] == "barring_black_white_taking", r["point_1_1"]                     # its last breath: white could land there now and take it; black couldn't hold
assert r["black_breath"] == "straining", r["black_breath"]                   # one breath, the mind to place: it can still be answered
w.turn = WHITE
assert w.read()["black_breath"] == "hanging"                                 # one breath, the other to place
w.turn = BLACK
assert any(i[1] == point((1, 1)) for i in w.invitations()) is False          # the mind's own stone couldn't hold on its last breath
print("5. an eye bars white until it is the group's last breath, then bars black; straining on the mind's turn, hanging on the other's: ok")

# 6. potential forces on groups: what a placement would do, and what a white stone would do where it could land
w = setup([(BLACK, (2, 2)), (BLACK, (4, 2)), (WHITE, (3, 1)), (WHITE, (2, 3)), (WHITE, (1, 2)), (WHITE, (2, 1))])
names = {i[1]: i[2] for i in w.invitations() if i[0] == "place"}
r = w.read()
print("   black at (2,2) has one breath, (3,2); black at (4,2) beside it:", names["point_3_2"], "| the point reads", r["point_3_2"])
assert names["point_3_2"].split("_")[1] == "saving", names["point_3_2"]          # joining them, the stone at (2,2) breathes again
assert r["point_3_2"] == "free_white_taking", r["point_3_2"]                    # a white stone there would take the stone at (2,2)
assert names["point_5_2"].split("_")[1] == "extending" and names["point_6_6"] == "free_alone_quiet_breathing", (names["point_5_2"], names["point_6_6"])
assert names["point_3_0"].split("_")[2] == "pressing" and r["point_5_2"] == "free_white_pressing", (names["point_3_0"], r["point_5_2"])
w = setup([(WHITE, (1, 1)), (WHITE, (3, 1)), (BLACK, (1, 3)), (BLACK, (3, 3))])
names = {i[1]: i[2] for i in w.invitations() if i[0] == "place"}
assert names["point_2_1"] == "free_alone_cutting_breathing", names["point_2_1"]         # between two white stones a white stone would join
assert w.read()["point_2_3"] == "free_white_cutting", w.read()["point_2_3"]             # a white stone there lands between two black groups
assert names["point_2_3"] == "free_joining_quiet_breathing", names["point_2_3"]         # and a black one joins them
print("6. placements read by what they would do to groups, points by what a white stone would do there: ok;", names["point_2_1"], "|", names["point_2_3"])
