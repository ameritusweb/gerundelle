"""Dream trials' understanding, in worker processes (the user, 2026-11-13: "why not just do all trials in parallel?", then "Yes, waves").
Each worker loads the mind's snapshot once per dream (dream.snapshot: the mind pickled with its register's three functions set aside) and,
for each trial, makes a fresh copy, gives it the imagined register as it stood after that trial's own writes, reads which of the trial's
concepts still have open structure (on the copy before it ticks: the mind's own SOV at that trial), lets the copy tick with the dream as
its percepts, and returns the attended ones still open: dream.understanding_of's answer, the edge.

The register's functions, rebuilt here as they are in the mind (pickle can't carry closures): `kind` (SovAgent.__init__'s act/change, and
force_predict's role kinds from the world's role_of) and `owner` (Understanding.__init__'s, over the register's own owners)."""
import pickle

_SNAP = None
_ROLE_OF = None


def plain_kind(c):   # SovAgent.__init__: und.kind
    return "act" if c.split(":", 1)[0].endswith("_push") else "change"


class RoleKind:   # SovAgent.force_predict's kind (c, plain=plain), with the world's role_of
    def __init__(self, role_of):
        self.role_of = role_of

    def __call__(self, c):
        if "#" not in c:
            return plain_kind(c)
        r = c.split("#", 1)[1]
        return self.role_of(r)[0] if self.role_of else r


def init(snap, role_of):
    global _SNAP, _ROLE_OF
    import rung0  # noqa: F401  (Gerundelle on the path)
    _SNAP, _ROLE_OF = snap, role_of


def copy_of(writes):
    """A fresh copy of the mind from the snapshot, with the imagined writes since the dream began replayed on its register (as
    Understanding.add_imagined made them in the mind): the register as it stood at the trial."""
    copy = pickle.loads(_SNAP)
    und = copy.understanding
    und.kind = RoleKind(_ROLE_OF) if und.__dict__.get("_role_kinds") else plain_kind
    und.owner = lambda c: (c.split(":", 1)[1].rsplit("_", 1)[0] if "_push:" in c else und.owners.get(c))
    for c, rel, other in writes or ():
        und.add_imagined(c, rel, other)
    return copy


def understanding(task):
    """(the imagined writes since the dream began, up to the trial; the move (label, mover, state); the changes it came to; the dreamed
    states) -> the edge."""
    from molecules import clause
    writes, inv, names, states = task
    copy = copy_of(writes)
    move = f"{inv[0]}_push:{inv[1]}_{inv[2]}"
    concepts = set(names) | {move}
    open_ = {c for c in concepts if copy.understanding.open_structure(c)}   # (the mind's SOV at the trial: before the copy ticks)
    copy.facts = {o: clause(f"{o}_{st.replace(' ', '_')}") for o, st in states.items()}
    news = [clause(e) for e in sorted(names)]
    offers = [clause(move, tags=("invitation", inv[1]))]
    rec = copy.tick(news + offers)
    attended = {c for c in concepts for w in rec["levels"][-1]["winners"] if c in w}
    return sorted(c for c in attended if c in open_)
