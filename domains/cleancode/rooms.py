"""The rungs' rooms (LADDER.md): each is room(rng) -> the next Problem. Small rooms first (cognitivechess/LADDER.md's lesson). Each room
keeps its shape and makes fresh tests and a fresh scramble for every problem (the user: one fixed shape per problem instance, "random
how 'off' the operations are, based on luck"). The shapes and sizes are mine."""
import graph as g


def rung0(rng):
    """One input, one connection, three tests."""
    return g.make(g.chain_shape(1), rng, name="one")


def rung1(rng):
    """One input, two connections one after the other."""
    return g.make(g.chain_shape(2), rng, name="two")


def rung2(rng):
    """Two inputs, each through a connection, joined."""
    return g.make(g.join_shape(), rng, name="join")


def rung3(rng):
    """Two connections with a range check between them (range validity, hidden)."""
    s = g.chain_shape(2)
    s.checks = {1: None}
    return g.make(s, rng, name="range")


def rung4(rng):
    """A loop (CONTROL_FLOW.md)."""
    return g.make(g.loop_shape(), rng, name="loop")


def rung5(rng):
    """A branch (CONTROL_FLOW.md)."""
    return g.make(g.branch_shape(), rng, name="branch")


ROOMS = {"0": rung0, "1": rung1, "2": rung2, "3": rung3, "4": rung4, "5": rung5}
