"""A mind for each piece (LADDER.md, rung 1d; the user's idea). Gerundelle is unchanged: each piece's mind is a SovAgent that thinks and learns, and the main mind decides.

Each tick, every piece's mind perceives the board, offered only its own moves, and thinks. Its top-level winners among its moves, and the move its planner holds,
enter the main mind's pool as molecules with their activation there. The main tournament bids on them fresh (binding, support, tension, forward), and the main
mind acts. When a piece's move is played, that piece lives the outcome through observe_other.
"""
from molecules import Mind, Params, clause
from potential import ForceMind, feel
from offers import RemembersOffers
from sov_agent import SovAgent, inv_id


class PieceView:
    """What one piece's mind sees: the whole board, and only its own moves on offer. It never acts on the world."""

    def __init__(self, world, piece):
        self.world, self.piece = world, piece
        self.still, self.gamma, self.horizon = world.still, world.gamma, world.horizon
        self.objs, self.tree = world.objs, world.tree

    @property
    def diffs(self):
        return self.world.diffs

    def states(self, tree=None):
        return self.world.states()

    def invitations(self, tree=None):
        return [i for i in self.world.invitations() if i[1] == self.piece]

    def renew(self):
        pass

    def act(self, inv=None, hold=False):
        return []


class PieceMind(SovAgent):
    """A piece's mind: it wants to own something, which it does for good once it captures it (the user); pressing something alone is the way there."""

    def __init__(self, world, piece, budget=500, forces=False):
        mind = ForceMind(Params(inquiry=True, phases=True)) if forces else Mind(Params(inquiry=True, phases=True))
        super().__init__(PieceView(world, piece), mind)
        self.real, self.forces = world, forces
        self.piece, self.budget = piece, budget
        self.goal = f"{piece}_unique_owns"

    def think(self):
        """Perceive and think, without acting: (its moves that won the top level with their activation, the move its planner holds)."""
        if self.goal is None:
            self.goal = f"{self.piece}_unique_owns"
        if self.forces:
            self.mind.potentials = {c: f for c, f in __import__("potential").potential(self.real).items() if f"_push:{self.piece}_" in c}
        inputs, invs = self.perceive()
        rec = self.mind.tick(inputs, seen=self.news)
        self.last_rec = rec
        top = [i for i in rec["levels"][-1]["winners"] if i.split("|")[0] in invs]
        step = super().plan_step(invs, self.budget, 3) if self.goal and invs else None
        return [(i.split("|")[0], self.mind.pool[i].act if i in self.mind.pool else 1.0) for i in top], step

    def lived(self, inv, facts, names):
        """Its move was played: it lives what came of it."""
        effects = {e: 0 for e in names if e != "no_change"}
        self.observe_other(inv, facts, effects)
        if self.goal in names:
            self.reached.append((self.mind.t, self.goal))


class MainMind(SovAgent):
    """The main mind: the pieces' winning thoughts enter its pool, and its own tournament decides."""

    def __init__(self, world, pieces=True, budget=500, forces=False):
        params = Params(inquiry=True, phases=True, winner_acts=True)
        super().__init__(world, ForceMind(params) if forces else Mind(params))
        self.budget, self.forces = budget, forces
        whites = sorted(o for o in world.ids.values() if o.startswith("white"))
        self.pieces = {p: PieceMind(world, p, budget, forces) for p in whites} if pieces else {}
        self.offered = []   # (tick, piece, push): what the pieces put forward
        self.seen_pushes = 0

    def plan_step(self, invs, budget=60, horizon=3):
        return super().plan_step(invs, self.budget, horizon)

    def tick(self, force=None):
        if self.forces:
            feel(self, self.world)
        if not self.watching:
            for p, pm in self.pieces.items():
                top, step = pm.think()
                ideas = dict(top)
                if step is not None:
                    ideas[inv_id(step)] = max(ideas.get(inv_id(step), 0.0), 1.0)
                for c, act in ideas.items():
                    self.mind.present(clause(c, tags=("invitation", p, f"from:{p}")), act=act)
                    self.offered.append((self.mind.t, p, c))
        out = super().tick(force)
        if len(self.pushed) > self.seen_pushes:   # a move's watch ended: the piece that moved lives it
            for inv, facts, names in self.pushed[self.seen_pushes:]:
                pm = self.pieces.get(inv[1])
                if pm is not None:
                    pm.lived(inv, facts, names)
            self.seen_pushes = len(self.pushed)
        return out


class OfferedPieceMind(RemembersOffers, PieceMind):
    situational = False   # rung 2: its want comes from where it stands, safety while it bears a force, otherwise to own

    def think(self):
        if self.situational:
            bearing = self.real.states().get(f"{self.piece}_bearing")
            self.goal = f"{self.piece}_bearing_free" if bearing in ("pressed", "hanging") else f"{self.piece}_unique_owns"
        if self.goal is None:
            self.goal = f"{self.piece}_unique_owns"
        if self.forces:
            self.mind.potentials = {c: f for c, f in __import__("potential").potential(self.real).items() if f"_push:{self.piece}_" in c}
        inputs, invs = self.perceive()
        rec = self.mind.tick(inputs, seen=self.news)
        self.last_rec = rec
        top = [i for i in rec["levels"][-1]["winners"] if i.split("|")[0] in invs]
        step = self.plan_step(invs, self.budget, 3) if self.goal and invs else None
        return [(i.split("|")[0], self.mind.pool[i].act if i in self.mind.pool else 1.0) for i in top], step


class OfferedMainMind(RemembersOffers, MainMind):
    """The main mind, and its pieces' minds, planning over what each saw on offer."""

    def __init__(self, world, pieces=True, budget=500, forces=False, side="white", situational=False):
        super().__init__(world, pieces=False, budget=budget, forces=forces)
        mine = sorted(o for o in world.ids.values() if o.startswith(side))
        self.pieces = {p: OfferedPieceMind(world, p, budget, forces) for p in mine} if pieces else {}
        for pm in self.pieces.values():
            pm.situational = situational
