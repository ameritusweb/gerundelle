"""Where the maze finds Gerundelle: reference/v2 (the version with the switches the maze needs), or $GERUNDELLE.

Import this first; then `molecules` and `sov_agent` are importable, and the two pieces borrowed from the Warp chess work are here:
ForceMind (a push enters the tournament with the force it would exert; warpchess/potential.py) and understanding_of (how well the
mind understands a dreamed situation; warpchess/dream.py).
"""
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GERUNDELLE = os.environ.get("GERUNDELLE", os.path.join(REPO, "reference", "v2"))
if GERUNDELLE not in sys.path:
    sys.path.insert(0, GERUNDELLE)

from molecules import Mind, clause  # noqa: E402


class ForceMind(Mind):
    """A Mind whose invitations enter with their potential force as activation (warpchess/potential.py): the world reads each push's
    force from what it would reach (maze.Maze.potentials), and run.py sets it before each slice."""

    potentials = {}

    def present(self, m, act=1.0):
        return super().present(m, act=max(act, self.potentials.get(m.id, act)))


def dreaming_mind(mind):
    """A copy of the mind, to read its attention to a dream: a real tick would take the dream's percepts as lived (the firewall). The
    copy's own tick is thrown away. The register holds small functions pickle can't carry; they are set aside and put back
    (warpchess/dream.py)."""
    und = mind.understanding
    names = [k for k in ("kind", "owner", "lien_holds") if k in und.__dict__]
    held = {k: und.__dict__[k] for k in names}
    for k in names:
        und.__dict__[k] = None
    try:
        copy = pickle.loads(pickle.dumps(mind, protocol=4))
    finally:
        und.__dict__.update(held)
    copy.understanding.__dict__.update(held)
    return copy


def understanding_of(agent, inv, names, states):
    """How well the mind understands a dreamed situation (the user: "see how well you understand that position after manipulation, by
    looking at your thought molecules and SOV"; warpchess/dream.py). A copy of the mind takes a real tick with the dream as its
    percepts: the facts register is the dreamed scene, the news is each change that came, and the push is offered. -> the concepts the
    copy attended to whose structure in the mind's SOV is still open, counting what dreams have given it (the edge). Empty: understood."""
    copy = dreaming_mind(agent.mind)
    move = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
    copy.facts = {o: clause(f"{o}_{st.replace(' ', '_')}") for o, st in states.items()}
    news = [clause(e) for e in sorted(names)]
    offers = [clause(move, tags=("invitation", inv[1]))]
    rec = copy.tick(news + offers)
    concepts = set(names) | {move}
    attended = {c for c in concepts for w in rec["levels"][-1]["winners"] if c in w}
    und = agent.mind.understanding
    return sorted(c for c in attended if und.open_structure(c))
