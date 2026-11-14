"""The dream planner in the Go world (mysterymaze/dream_maze.py and warpchess/dream.py, the user's design, warpchess/LADDER.md rung 4
points 1-6; the user, 2026-11-11: "yes, build it on those terms").

The terms (the user's): the dream starts from the positions of the game just played, most recent first; it manipulates one stone at a
time, one of either colour added to a free point or one taken away, only where the result is a valid board; where it leans is chosen
by the tournament, at the edge of what the mind understands, not by a list of mine.

Between games, the mind dreams over the boards it placed on (or passed on) in the game just ended. In each, its own push from that
moment is tried again (the same point, or the pass), and what follows is read as the mind would perceive it through its watch: its
stone's slice, the loads read, what came apart leaving, then the other's stone as the world itself places it and what that takes
(world.horizon slices; the world's reply is the world's own, so where the other has one place left to go, the dream shows it going
there). How well the mind understands what it saw is warpchess/dream.py's understanding_of, unchanged; which manipulations are
followed is mysterymaze/dream_maze.py's chosen, unchanged (the mind's own tournament). At the edge the dream manipulates one stone
further. What it shows stays as imagined structure (Understanding.add_imagined) and in the imagination register (SovAgent.dreamed),
funding nothing (the firewall); a doing dreamed on one of the mind's regions is offered to that region's slot as a candidate want
(dreams shape wants). With Params.dreams the planner and the sub-wants read dreamed ways where nothing was lived; acted on, a dreamed
way becomes lived.

A manipulation is the world's own physics: a stone added is a stone landing (what it takes leaves), so the board that results is one
the world could show; a stone taken away leaves a board that is always valid. As a fact: the added stone doing what it does, or the
point it left as it then reads.

My choices (stated, as the other dreams'): a dreamed stone is named by its colour and point (white_at_3_3: the same names every dream,
none of them a stone of a real game); the doings offered to a region's slot are those the dream showed during the watch, not only
those standing at its end (a group's breath hangs and comes apart within the watch); DREAM_TRIALS is a compute budget, lower than the
maze's 200 because each trial copies the mind.
"""
import copy
import sys

sys.path.insert(0, __import__("paths").domain('warpchess'))
from dream import understanding_of  # noqa: E402

sys.path.append(__import__("paths").domain('mysterymaze'))   # (last: only dream_maze's chosen and promote are taken)
from dream_maze import chosen, promote  # noqa: E402

from world import BLACK, REST, WHITE, GoWorld, point  # noqa: E402

DREAM_TRIALS = 60
NO_BOARD = object()   # no board to be put back to: a manipulation isn't a reply
KEEP = ("at", "colour", "objs", "coming_apart", "unread", "turn", "last", "last_point", "since_stone", "waited", "passes", "placed",
        "black_placed", "took", "captures", "before_last", "lucky_reply", "full", "shown", "set_back", "kept", "taken", "next", "t",
        "diffs", "others", "lucky", "earned", "luck", "luck_log", "rng", "luck_rng", "game_start")
LASTING = ("hand", "black_breath", "white_breath")


class RemembersGames:
    """A mixin for the Go world: the boards on which the mind pushed this game (the stones as they stood, the board before the last
    stone, the push's name and what it was on)."""

    def act(self, inv=None, hold=False):
        if inv is not None and not self.__dict__.get("dreaming") and inv in self.invitations():
            self.__dict__.setdefault("game_positions", []).append((dict(self.at), dict(self.colour), self.before_last, inv[0], inv[1]))
        return super().act(inv, hold)

    def reset(self):
        self.__dict__["last_game"] = self.__dict__.get("game_positions", [])
        self.__dict__["game_positions"] = []
        super().reset()


class DreamingGo(RemembersGames, GoWorld):
    """The Go world that remembers its games, for the dream."""


def configure(world, at, colour, before_last):
    """The board as it stood, the mind to place, the board at rest."""
    for o in [o for o in world.objs if not o.startswith(("point_", "opportunity_")) and o not in LASTING]:
        del world.objs[o]
    world.at, world.colour = dict(at), dict(colour)
    for s in colour:
        for o in world.stone_objs(s):
            world.objs[o] = None
    world.coming_apart, world.unread, world.set_back = set(), False, set()
    world.turn, world.last, world.before_last = BLACK, WHITE, before_last
    world.since_stone, world.waited, world.passes, world.placed, world.full = REST, 0, 0, len(at), False
    world.lucky_reply, world.diffs, world.others = False, [], set()
    world.shown = world.read()


def manipulations(world, at, colour):
    """One stone away: a stone of either colour landing on a free point (what it takes leaves), or a stone taken away.
    -> [(the stones, their colours, the force as a fact)]"""
    board = {c: colour[s] for c, s in at.items()}
    out = []
    for x in range(world.size):
        for y in range(world.size):
            c = (x, y)
            if c in board:
                at2 = {k: v for k, v in at.items() if k != c}
                col2 = {s: v for s, v in colour.items() if s != at[c]}
                after = {k: v for k, v in board.items() if k != c}
                out.append((at2, col2, f"{point(c)}_{world.point_doing(c, after, NO_BOARD)}"))
                continue
            for col in (BLACK, WHITE):
                landed = world.landing(c, col, board, before=NO_BOARD)
                if landed is None:
                    continue
                after, taken = landed
                name = f"{col}_at_{x}_{y}"
                at2 = {k: v for k, v in at.items() if k not in taken}
                at2[c] = name
                col2 = {s: colour[s] for s in at2.values() if s != name}
                col2[name] = col
                out.append((at2, col2, f"{name}_{world.doing(after, c, BLACK)}"))
    return out


def dream(agent):
    """Dream over the last game; -> (trials, trials at the edge)."""
    world = agent.world
    positions = world.__dict__.get("last_game", [])
    if not positions:
        return 0, 0
    saved = {k: copy.deepcopy(world.__dict__[k]) for k in KEEP if k in world.__dict__}
    log_len, games = len(world.log), list(world.games)
    und, terr = agent.mind.understanding, agent.mind.territory
    trials = edges = 0
    world.__dict__["dreaming"] = True
    try:
        tried, frontier = set(), []
        for at, colour, before_last, name, target in reversed(positions):   # most recent first: the game ended where it was decided
            frontier.append((at, colour, before_last, (name, target), None, None))
        while frontier and trials < DREAM_TRIALS:
            at, colour, before_last, (name, target), force, base = frontier.pop(0)
            key = (frozenset((c, colour[s]) for c, s in at.items()), name, target)
            if key in tried:
                continue
            tried.add(key)
            configure(world, at, colour, before_last)
            one_away = lambda base_: [(a2, c2, before_last, (name, target), f2, base_) for a2, c2, f2 in manipulations(world, at, colour)]
            inv = next((i for i in world.invitations() if i[0] == name and i[1] == target), None)
            if inv is None:   # the same push isn't possible here (the world says so): one stone further (as the maze's dream)
                frontier[:0] = chosen(agent, one_away(base))
                continue
            before = dict(world.shown)
            facts = frozenset(f"{o}_{st}" for o, st in before.items())
            seen, names = dict(before), set()
            mid = None
            for k in range(world.horizon):   # the mind's watch: its stone's slice, then what follows, the other's stone and what that takes
                world.act(inv if k == 0 else None)
                now = dict(world.shown)
                names |= {f"{o}_{st}" for o, st in now.items() if o in seen and seen[o] != st}   # (as the mind notices: a change to what
                seen.update(now)                                                                  # it has seen; coming into view isn't one)
                if k == 0:
                    mid = set(names)
            after = dict(world.shown)
            names = frozenset(names)
            agent.dreamed.append((inv, facts, names))
            trials += 1
            push = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
            for e in names:
                und.add_imagined(push, "causes", e)
                und.add_imagined(e, "caused_by", push)
            for e in mid:
                und.add_imagined(push, "co_occurs", e)
            if force is not None and base is not None and names != base:   # one stone changed what follows: it conditions the push
                und.add_imagined(force, "conditions", push)
                und.add_imagined(push, "conditioned_by", force)
            nxt = chosen(agent, one_away(names if force is None else base))
            if force is None:   # the board as it was: one stone away is tried next
                frontier[:0] = nxt
            edge = understanding_of(agent, inv, names, after)
            agent.__dict__.setdefault("dream_edges", []).append((inv, facts, names, edge))
            if edge:   # at the edge of its understanding: manipulate further there; understood: leave it
                edges += 1
                if force is not None:
                    frontier[:0] = nxt
            for e in names:   # dreams shape wants
                o = agent.owner_of(e)
                if o in terr.rows:
                    terr.rows[o].setdefault("dreamed_states", set()).add(e)
        promote(agent, agent.dreamed[len(agent.dreamed) - trials:])
    finally:
        world.__dict__["dreaming"] = False
        world.__dict__.update(saved)
        del world.log[log_len:]
        world.games[:] = games
    return trials, edges
