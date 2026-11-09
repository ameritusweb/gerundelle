"""The dream planner in the mystery maze (warpchess/dream.py, the user's design, LADDER.md rung 4 points 1-6; the user, 2026-11-08: the
confound between the cheese and what came with it breaks "through the dream planner").

Between trips, the mind dreams over the configurations the trip went through (where it pushed: the body's position, the controller's
heading, the walls as they stood). Manipulation, one force at a time: the body moved to a neighbouring position, or the controller's
heading changed; every configuration is valid in this world (the body can stand on any position, face any way), and the world itself
says what follows. In each configuration the mind's own push from that moment is tried again (the same push: walk onto what is in
front, the same button, the same word), and what follows is read as the mind perceives it. How well the mind understands it is
warpchess/dream.py's understanding_of, unchanged (a copy of the mind takes a real tick with the dream as its percepts; the concepts it
attends to whose structure is still open are the edge); at the edge the dream manipulates one force further. What it shows stays as
imagined structure (Understanding.add_imagined) and in the imagination register (SovAgent.dreamed), funding nothing (the firewall); a
state dreamed on one of the mind's regions is offered to that region's slot as a candidate want (dreams shape wants). With Params.dreams,
the planner and the sub-wants read dreamed ways where nothing was lived; acted on, a dreamed way becomes lived.

My choices (stated, as dream.py's): the dream starts from the trip's own configurations, most recent first (the way to the cheese is
where the trip ended); the forces manipulated are the body's position, the heading, and the walls beside the body; DREAM_TRIALS is a compute budget.
"""
import copy

from gerundelle_path import understanding_of  # (warpchess/dream.py's, copied there)
from maze import CELLS, HEADINGS, pos, wall_id

DREAM_TRIALS = 200
KEEP = ("pos", "heading", "got", "open_now", "dist", "shown", "pending", "since_walk", "slices", "t", "diffs", "seen_only")


class RemembersTrips:
    """A mixin for the maze: the configurations where the mind pushed this trip (position, heading, the walls open, the push's name)."""

    def act(self, inv=None, hold=False):
        if inv is not None and not self.__dict__.get("dreaming"):
            self.__dict__.setdefault("trip", []).append((self.pos, self.heading, frozenset(self.open_now), inv[0]))
        return super().act(inv, hold)

    def reset(self):
        self.__dict__["last_trip"] = self.__dict__.get("trip", [])
        self.__dict__["trip"] = []
        super().reset()


def configure(world, at, heading, open_now):
    world.pos, world.heading, world.open_now = at, heading, set(open_now)
    world.got = False
    world.dist = world.distance(at)
    world.shown = {"controller_heading": f"pointing_{heading}", "controller_distance": "holding", "cheese": "resting",
                   "controller": "resting", "voice": "resting"}
    world.shown.update(world.view())
    world.pending, world.since_walk, world.diffs = {}, 0, []


def manipulations(world, at, heading, open_now):
    """One force away: the body on a neighbouring position, the heading turned, or a wall beside the body opened or closed (a wall is
    a force too: first only the body and the heading were manipulated, and where the cheese's second way lay behind a wall the dream
    reached it from one side only, and nothing was promoted; seed 3). -> [(position, heading, walls open, the force, as a fact)]"""
    out = []
    for dx, dy in HEADINGS.values():
        n = (at[0] + dx, at[1] + dy)
        if n in CELLS:
            out.append((n, heading, open_now, f"{pos(n)}_bearing"))
            e = frozenset((at, n))
            if e in world.walls:
                wall = wall_id(e, world.walls[e])
                if e in open_now:
                    out.append((at, heading, open_now - {e}, f"{wall}_blocking"))
                else:
                    out.append((at, heading, open_now | {e}, f"{wall}_yielding"))
    for h in HEADINGS:
        if h != heading:
            out.append((at, h, open_now, f"controller_heading_pointing_{h}"))
    return out


def promote(agent, dreamt):
    """The co-occurrence promoted to an imagined cause (the user, 2026-11-08: "it should promote the co-occurrence to an imagined cause to
    a sub-want"): for each want the mind has had, the dreamed trials it came in; if they came with different company (the confound
    broke: reached from different sides), what came with it in every one of them is imagined to cause it (marked imagined, funding
    nothing). Under Params.dreams the sub-wants read it (Mind.support_subwants), believed at credulity."""
    und = agent.mind.understanding
    for g in sorted({w for _, w in agent.reached}):
        came = [frozenset(n) - {g} for _, _, n in dreamt if g in n]
        if len(set(came)) < 2:
            continue
        for x in sorted(frozenset.intersection(*came)):
            und.add_imagined(x, "causes", g)
            und.add_imagined(g, "caused_by", x)
            agent.__dict__.setdefault("promoted", []).append((agent.mind.t, x, g))


def chosen(agent, items):
    """Which manipulations the dream follows (the user, 2026-11-08: "the tournament"): each one, as the fact it would make (a position
    stood on, a wall open or closed, a heading), enters the mind's own tournament with what the mind holds now (Mind.imagined_levels,
    as the opponent's reply is read in its shoes; nothing is kept: the firewall). The ones that win the top level are followed, in
    the order they won; if none wins a slot anywhere, the one the tournament carried furthest. First every manipulation was followed in
    the order I listed them, and with nearly every dreamed configuration at the edge, that order, not the mind, chose (seed 3: 517 of
    600 trials among the walls near one corridor)."""
    from molecules import clause
    if not items:
        return []
    mind = agent.mind
    by = {}
    for it in items:
        by.setdefault(it[4], it)
    pool = dict(mind.pool)
    for f in by:
        x = clause(f, tags=("manipulation",))
        x.act = 1.0
        pool[f] = x
    levels = mind.imagined_levels(pool, set(by))
    for L in range(len(levels) - 1, -1, -1):
        won = [i for i in levels[L]["winners"] if i in by]
        if won:
            return [by[i] for i in won] if L == len(levels) - 1 else [by[won[0]]]
    bids = levels[0]["bids"] if levels else {}
    return [by[min(by, key=lambda i: (-bids.get(i, 0.0), i))]]


def dream(agent):
    """Dream over the last trip; -> (trials, trials at the edge)."""
    world = agent.world
    trip = world.__dict__.get("last_trip", [])
    if not trip:
        return 0, 0
    saved = {k: copy.deepcopy(world.__dict__[k]) for k in KEEP if k in world.__dict__}
    log_len, episodes = len(world.log), list(world.episodes)
    und, terr = agent.mind.understanding, agent.mind.territory
    trials = edges = 0
    world.__dict__["dreaming"] = True
    try:
        tried, frontier = set(), []   # configurations already dreamed (first none were kept, and the dream went back and forth
        # between two positions for 197 of its 200 trials; trace_dream.py)
        for at, heading, open_now, name in reversed(trip):   # most recent first: the trip ended at the cheese
            frontier.append((at, heading, open_now, name, None, None))
        while frontier and trials < DREAM_TRIALS:
            at, heading, open_now, name, force, base = frontier.pop(0)
            if (at, heading, open_now, name) in tried:
                continue
            tried.add((at, heading, open_now, name))
            configure(world, at, heading, open_now)
            inv = next((i for i in world.invitations() if i[0] == name), None)
            if inv is None:   # the same push isn't possible here (the world says so): nothing new is learned, so the reason to go on
                # is the configuration it came from, which was at the edge (or the trip's own); one force further (first it stopped
                # here, and a configuration two forces away, standing west of the cheese and facing it, was never reached)
                frontier[:0] = chosen(agent, [(a2, h2, o2, name, f2, base) for a2, h2, o2, f2 in manipulations(world, at, heading, open_now)])
                continue
            before = dict(world.shown)
            facts = frozenset(f"{o}_{st}" for o, st in before.items())
            mid_diffs = world.act(inv)
            mid = dict(world.shown)
            world.act(None)   # what follows lands
            after = dict(world.shown)
            names = frozenset(f"{o}_{st}" for o, st in after.items() if st != before.get(o)) | \
                frozenset(f"{o}_unseen" for o in before if o not in after)
            agent.dreamed.append((inv, facts, names))
            trials += 1
            push = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
            for e in names:
                und.add_imagined(push, "causes", e)
                und.add_imagined(e, "caused_by", push)
            for e in {f"{o}_{st}" for o, st in mid.items() if st != before.get(o)}:
                und.add_imagined(push, "co_occurs", e)
            if force is not None and base is not None and names != base:   # one force changed what follows: it conditions the push
                und.add_imagined(force, "conditions", push)
                und.add_imagined(push, "conditioned_by", force)
            nxt = chosen(agent, [(a2, h2, o2, name, f2, names if force is None else base) for a2, h2, o2, f2 in manipulations(world, at, heading, open_now)])
            if force is None:   # the configuration as it was: one force away is tried next
                frontier[:0] = nxt
            edge = understanding_of(agent, inv, names, after)
            agent.__dict__.setdefault("dream_edges", []).append((inv, facts, names, edge))
            if edge:   # at the edge of its understanding: manipulate further there; understood: leave it
                edges += 1
                if force is not None:
                    frontier[:0] = nxt
            for o, st in after.items():   # dreams shape wants
                if st != before.get(o) and o in terr.rows:
                    terr.rows[o].setdefault("dreamed_states", set()).add(f"{o}_{st}")
        promote(agent, agent.dreamed[len(agent.dreamed) - trials:])
    finally:
        world.__dict__["dreaming"] = False
        world.__dict__.update(saved)
        del world.log[log_len:]
        world.episodes[:] = episodes
    return trials, edges
