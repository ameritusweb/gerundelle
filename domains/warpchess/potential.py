"""Potential forces (LADDER.md, rung 1e; the user's idea). A move on offer is an open force slot, and it carries the force it would exert, read from the position before it's tried.

Gerundelle is unchanged: ForceMind is a Mind whose invitations enter the tournament with that force as their activation, where every invitation otherwise enters at 1.0.
"""
from molecules import Mind
from sov_agent import inv_id

HANGING, PRESSED, QUIET = 3.0, 2.0, 1.0   # the force a move would put on what it reaches (my scale, not piece values)


def potential(world):
    """push id -> the force that move would exert: onto an enemy piece with no reserve against it, onto one held by a defender, or none."""
    out = {}
    states = world.states()
    for inv in world.invitations():
        move = world.offers().get(inv[0])
        force = QUIET
        if move is not None:
            target = move.final_square
            taken = next((o for o, sq in world.where.items() if sq == target and world.board.colors[target] != world.board.colors[move.from_square]), None)
            if taken is not None:
                force = HANGING if states.get(f"{taken}_bearing") == "hanging" else PRESSED
        out[inv_id(inv)] = force
    return out


class ForceMind(Mind):
    """A Mind whose invitations enter with their potential force as activation."""

    potentials = {}

    def present(self, m, act=1.0):
        return super().present(m, act=max(act, self.potentials.get(m.id, act)))


def feel(agent, world):
    """Before the agent perceives: the potential forces of what's on offer now."""
    agent.mind.potentials = potential(world)
