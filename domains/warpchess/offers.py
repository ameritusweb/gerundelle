"""The planner reads what was on offer (LADDER.md, rung 1f). Gerundelle is unchanged.

A mind perceives what's on offer each tick. Remembering it, situation by situation, is its own experience: the model then considers only the moves it saw
offered in a situation it has been in, instead of every move it knows wherever a piece is present.
"""
from molecules import mcts
from sov_agent import Model, imagined_lines


def clean(s):
    return frozenset(x for x in s if not x.startswith(("made:", "line:")))


class OfferedModel(Model):
    def candidates(self, s):
        """The moves that fit an imagined state: of those the model allows, the ones seen on offer in that situation, if it has been in it.
        (Before Params.imagined_tournament this filtered actions(); as candidates it reads the same with the switch off.)"""
        base = super().candidates(s)
        seen = self.agent.offered_in.get(clean(s))
        return [c for c in base if c in seen] if seen is not None else base


class RemembersOffers:
    """A mixin for a SovAgent: it remembers what was on offer in each situation, and plans over that."""

    def perceive(self):
        inputs, invs = super().perceive()
        if not hasattr(self, "offered_in"):
            self.offered_in = {}
        self.offered_in.setdefault(clean(self.facts_now()), set()).update(invs)
        return inputs, invs

    def plan_step(self, invs, budget=60, horizon=3):
        """SovAgent.plan_step, over the model that reads what was on offer."""
        if not hasattr(self, "offered_in"):
            self.offered_in = {}
        budget = getattr(self, "budget", budget)
        s = self.facts_now()
        model = OfferedModel(self, self.goal, root=(s, set(invs)))
        if not model.actions(s):
            return None
        if self.mind.p.imagined_tournament:   # the same train of thought as SovAgent.plan_step, over the model that reads what was on offer
            a, v = imagined_lines(model, s, self.top_moves(model.actions(s)), horizon)
            return invs.get(a) if v > 0 else None
        top = set(self.mind.top(self.last_rec)) if self.last_rec else set()
        prior = {a: 3.0 for a in model.actions(s) if a in top}
        a, v = mcts(model, s, prior, budget=budget, horizon=horizon, value=True)
        return invs.get(a) if v > 0 else None
