"""The dream planner in the clean code world, in the problem, when the mind is stuck (the user, 2026-11-14: "in warpchess, we solved it
with in-game dreaming when it was stuck"; Params.dream_when_stuck, warpchess/rung4p.py's dreamer). Go's dream (go/dream_go.py) on this
world's terms, which are the user's design for the dream (warpchess/LADDER.md rung 4): it starts from where the mind pushed, most recent
first; it manipulates one force at a time, only where the world says the result is valid; where it leans is chosen by the mind's own
tournament (mysterymaze/dream_maze.py's chosen), at the edge of what it understands (warpchess/dream.py's understanding_of).

- Where it starts: the wheels as they stood when the mind pushed in this problem, most recent first; with a focus (the stuck concept's
  push, the dreamer below), the settings where that push was on offer, else where the mind stands now.
- One force away: one wheel turned one step, either way (the world's own move: every setting of the wheels is a program the world can
  run). As a fact: the connection doing what it then does (conn_<c>_<operation>).
- What follows: the push tried again, read through the mind's watch (world.horizon slices: the turn, then what it does to every gerund),
  as the mind notices it: a change to what it has seen.
- Kept as imagined structure (Understanding.add_imagined: push causes what followed, the manipulation conditions the push) and in the
  imagination register (SovAgent.dreamed), funding nothing (the firewall); a doing dreamed on one of the mind's regions is offered to
  that region's slot as a candidate want (dreams shape wants); the co-occurrences promoted (dream_maze.promote).
- The world is set back exactly as it was: nothing the dream did happened (no tick gained, no problem closed, nothing logged).
DREAM_TRIALS is a compute budget, as Go's (each trial copies the mind)."""
import copy
import re
import sys

sys.path.insert(0, __import__("paths").domain('warpchess'))
from dream import understanding_of  # noqa: E402

sys.path.append(__import__("paths").domain('mysterymaze'))   # (last: only dream_maze's chosen and promote are taken)
from dream_maze import chosen, promote  # noqa: E402

import graph as g  # noqa: E402
from world import TURNS, CodeWorld  # noqa: E402

DREAM_TRIALS = 60
KEEP = ("pos", "unread", "idle", "opened", "turned", "full", "closing", "shown", "objs", "set_back", "t", "diffs", "gained", "kept", "solved",
        "last_conn", "others")


class RemembersProblem:
    """A mixin for the clean code world: the wheels as they stood each time the mind pushed in this problem, and the push."""

    def act(self, inv=None, hold=False):
        if inv is not None and not self.__dict__.get("dreaming") and inv in self.invitations():
            self.__dict__.setdefault("problem_positions", []).append((tuple(self.pos), inv[0], inv[1]))
        return super().act(inv, hold)

    def open_problem(self):
        self.__dict__["problem_positions"] = []
        super().open_problem()


class DreamingCode(RemembersProblem, CodeWorld):
    """The clean code world that remembers its problem, for the dream."""


def configure(world, pos):
    """The wheels as they stood, read, the problem open."""
    world.pos = list(pos)
    world.unread, world.full, world.closing, world.idle = False, False, False, 0
    world.shown = {**world.read(world.pos), "hands": "holding"}
    world.objs = {o: None for o in world.shown}
    world.set_back, world.diffs = set(), []


def manipulations(world, pos):
    """One wheel one step either way: [(the wheels, the force as a fact)]."""
    out = []
    for c in range(len(pos)):
        for _, d in TURNS:
            p2 = list(pos)
            p2[c] += d
            out.append((tuple(p2), f"conn_{c}_{world.p.shape.doing(c, p2[c])}"))
    return out


def dream(agent, focus=None, budget=DREAM_TRIALS):
    """Dream in the problem; focus: (label, conn) of the push to try. -> (trials, trials at the edge)."""
    world = agent.world
    positions = list(world.__dict__.get("problem_positions", []))
    if focus is not None:
        starts = [(pos, focus[0], focus[1]) for pos, _, _ in reversed(positions)] or [(tuple(world.pos), *focus)]
    else:
        starts = list(reversed(positions))
    if not starts:
        return 0, 0
    saved = {k: copy.deepcopy(world.__dict__[k]) for k in KEEP if k in world.__dict__}
    log_len = len(world.log)
    und, terr = agent.mind.understanding, agent.mind.territory
    trials = edges = 0
    world.__dict__["dreaming"] = True
    try:
        tried, frontier = set(), []
        seen_starts = set()
        for pos, name, target in starts:
            if (pos, name, target) not in seen_starts:
                seen_starts.add((pos, name, target))
                frontier.append((pos, name, target, None, None, None))
        while frontier and trials < budget:
            pos, name, target, _, force, base = frontier.pop(0)   # (Go's layout: the force fact at [4], as chosen reads it)
            key = (tuple(x % len(g.wheel(k)) for x, k in zip(pos, world.p.shape.kinds)), name, target)
            if key in tried:
                continue
            tried.add(key)
            configure(world, pos)
            one_away = lambda base_: [(p2, name, target, None, f2, base_) for p2, f2 in manipulations(world, pos)]
            inv = next((i for i in world.invitations() if i[0] == name and i[1] == target), None)
            if inv is None:
                frontier[:0] = chosen(agent, one_away(base))
                continue
            before = dict(world.shown)
            facts = frozenset(f"{o}_{st}" for o, st in before.items())
            seen, names, mid = dict(before), set(), None
            for k in range(world.horizon):
                world.act(inv if k == 0 else None)
                now = dict(world.shown)
                names |= {f"{o}_{st}" for o, st in now.items() if o in seen and seen[o] != st}
                seen.update(now)
                if k == 0:
                    mid = set(names)
            after = dict(world.shown)
            names = frozenset(names)
            agent.dreamed.append((inv, facts, names))
            trials += 1
            push = world.push_id(inv)
            for e in names:
                und.add_imagined(push, "causes", e)
                und.add_imagined(e, "caused_by", push)
            for e in mid:
                und.add_imagined(push, "co_occurs", e)
            if force is not None and base is not None and names != base:   # one wheel changed what follows: it conditions the push
                und.add_imagined(force, "conditions", push)
                und.add_imagined(push, "conditioned_by", force)
            nxt = chosen(agent, one_away(names if force is None else base))
            if force is None:
                frontier[:0] = nxt
            edge = understanding_of(agent, inv, names, after)
            agent.__dict__.setdefault("dream_edges", []).append((inv, facts, names, edge))
            if edge:
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
    return trials, edges


PUSH = re.compile(r"(turning_forward|turning_back|resting)_push:(conn_\d+|hands)_")


def dreamer(agent, concept):
    """Params.dream_when_stuck's dreamer (as warpchess/rung4p.py's): the stuck concept's first push, dreamed from the settings of this
    problem where it was on offer (else from where the mind stands). The problem doesn't move while it runs (the mind's own slice)."""
    found = PUSH.findall(concept)
    if not found:
        agent.__dict__.setdefault("dreams_not_run", []).append((agent.mind.t, concept, "no push in it"))
        return 0
    trials, edges = dream(agent, focus=found[0])
    agent.__dict__.setdefault("dreams_done", []).append((agent.mind.t, concept, trials, edges))
    return trials
