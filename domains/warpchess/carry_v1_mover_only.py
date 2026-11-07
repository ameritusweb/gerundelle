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
            mover = inv[1]
            start = frozenset((entity(e.rsplit("_", 1)[0])[1], e.rsplit("_", 1)[1]) for e in got[1]
                              if e.rsplit("_", 1)[0].startswith(mover) and entity(e.rsplit("_", 1)[0])[0] == mover)
            if not start:
                continue
            for src, (lived_mover, first, rest) in self._pairs.items():
                if first != start:
                    continue
                for obj, reading in rest:   # carried under mover -> mover; shared objects are themselves
                    e, ch = entity(obj)
                    target = (mover + ch) if e == lived_mover else obj
                    key = (c, "causes", f"{target}_{reading}")
                    if key in self.carried:
                        continue
                    und.add(c, "causes", f"{target}_{reading}", "worked")
                    self.carried.add(key)
                    self.liens[key] = src

    def lived_pairs(self):
        """move -> (its mover, its first-slice changes on its mover's readings, its other changes on its mover and shared objects)."""
        out = {}
        for (c, conds, target, reading, lo, hi) in self.relations():
            if conds:
                continue
            obj = target.split(":", 1)[1]
            mover = c.split("_push:")[1].rsplit("_", 1)[0]
            e, ch = entity(obj)
            first, rest = out.setdefault(c, (mover, set(), set()))[1:]
            if e == mover and lo <= 1 and ch:
                first.add((ch, reading))
            elif (e == mover and lo >= 1) or obj in SHARED:
                rest.add((obj, reading))
        return {c: (m, frozenset(f), frozenset(r)) for c, (m, f, r) in out.items() if f and r}


def inv_id_of(inv):
    return f"{inv[0]}_push:{inv[1]}_{inv[2]}"
