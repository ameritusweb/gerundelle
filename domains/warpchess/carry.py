"""The link from concepts to the main SOV (LADDER.md, rung 4; the user, 2026-11-07): a lived move's (SOV, world) pair carried onto a move
the mind has never made, when the start of its structure matches.

The user's example: a piece on A has a potential force forward onto B, an enemy piece on C has a potential force diagonally onto B; a
forward force on the piece puts it under the enemy's potential force, the enemy applies it and captures the piece: material is lost.
That pair is a concept of its own. Where a new move's structure matches it, the move gets related in the main SOV to losing material.

As the SOV algebra has it: Abstract (the shared pattern, a lien on both structures) then Constrain (a transitive accrual), written as a
worked-out relation (Understanding.add(..., "worked")), the provenance the mind's own inference has; the lien records the lived pair it
rests on. Nothing is told and nothing imagined is funded: imagination only shows the new move's first step (Params.imagine's world),
which is what is matched.

- A lived move's pair: the relations its trials show (pairs3.PairMind.relations): move -> object -> reading, at slices lo..hi.
- A new move's start: what the imagined board shows changing on the moving piece's own readings.
- Fit: the lived pair's first-slice relations on its own mover (its readings) equal the new move's start, the mover mapped to the
  mover. Carried: the pair's other relations on the mover (later slices) and on the objects every room shares (material, standing,
  outcome), under that mapping.
"""
import collections

from pairs3 import entity

SHARED = ("material", "standing_white", "standing_black", "outcome_white")


class Carries:
    """A mixin for rung 4's Player (a PairMind, which keeps its timed trials) in a world that imagines (imagine.Imagines)."""

    carried = None

    def carry_links(self, invs):
        """For each move on offer the mind has never made: fit its imagined start against the lived pairs, carry what fits."""
        if self.carried is None:
            self.carried, self.liens, self._pairs_at = set(), {}, -1
        if self._pairs_at != len(self.timed):   # the lived pairs change only when a trial ends
            self._pairs = self.lived_pairs()
            self._pairs_at = len(self.timed)
        tried = {inv_id_of(i) for i, _, _ in self.timed}
        und = self.mind.understanding
        for c, inv in invs.items():
            if c in tried:
                continue
            got = self.world.imagine([inv[0]]) if hasattr(self.world, "imagine") else None
            if not got:
                continue
            start = start_of(got[1], inv[1])
            if not start:
                continue
            for src, (lived_mover, first, rest) in self._pairs.items():
                phi = fit(first, start, lived_mover, inv[1])
                if phi is None:
                    continue
                for obj, reading in rest:   # carried under the mapping; the objects every room shares are themselves
                    e, ch = entity(obj)
                    if obj in SHARED:
                        target = obj
                    elif e in phi:
                        target = phi[e] + ch
                    else:
                        continue   # a piece the start doesn't map: the structure says nothing about it here
                    key = (c, "causes", f"{target}_{reading}")
                    if key in self.carried:
                        continue
                    und.add(c, "causes", f"{target}_{reading}", "worked")
                    self.carried.add(key)
                    self.liens[key] = src

    def lived_pairs(self):
        """move -> (its mover, its start: the first-slice changes on every piece's readings, the rest: its later changes on pieces
        and the changes on the objects every room shares)."""
        out = {}
        for (c, conds, target, reading, lo, hi) in self.relations():
            if conds:
                continue
            obj = target.split(":", 1)[1]
            mover = c.split("_push:")[1].rsplit("_", 1)[0]
            e, ch = entity(obj)
            first, rest = out.setdefault(c, (mover, set(), set()))[1:]
            if obj in SHARED:
                rest.add((obj, reading))
            elif lo <= 1 and (ch or obj.startswith("file_")):   # a file's pressure is holding (the user): part of the structure
                first.add((e, ch or "file", reading))
            else:
                rest.add((obj, reading))
        return {c: (m, frozenset(f), frozenset(r)) for c, (m, f, r) in out.items() if f and r}


def start_of(changes, mover):
    """The imagined start of a move: the changes on every piece's readings (its bearing, exerting, unique), as (piece, reading, state)."""
    out = set()
    for e in changes:
        obj, state = e.rsplit("_", 1)
        piece, ch = entity(obj)
        if ch or obj.startswith("file_"):   # a file's pressure is holding (the user): part of the structure
            out.add((piece, ch or "file", state))
    return frozenset(out)


def fit(first, start, lived_mover, mover):
    """The one-to-one mapping of the lived start's pieces onto the new start's, the mover onto the mover, under which the two starts
    are the same structure; None if there is none. Pieces match by what changes on them (the readings and states), and a piece of
    one colour maps to a piece of the same colour, a file to a file (my choice, stated to the user: whose forces a piece bears is part
    of what it is doing, but colour is in its name, not in the structure)."""
    by = lambda st: {p: frozenset((ch, s) for q, ch, s in st if q == p) for p in {q for q, _, _ in st}}
    a, b = by(first), by(start)
    if len(a) != len(b) or a.get(lived_mover) != b.get(mover):
        return None
    phi, used = {lived_mover: mover}, {mover}
    for p in sorted(a):
        if p == lived_mover:
            continue
        q = next((q for q in sorted(b) if q not in used and b[q] == a[p] and q.split("_")[0] == p.split("_")[0]), None)
        if q is None:
            return None
        phi[p], used = q, used | {q}
    return phi


def inv_id_of(inv):
    return f"{inv[0]}_push:{inv[1]}_{inv[2]}"
