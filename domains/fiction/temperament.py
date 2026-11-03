"""Temperament: where a character's hyperparameters live, and how a profile reaches each arm.

The user (2026-10-25): "A mind with a low parking threshold is impatient: it moves on fast, explores broadly,
learns many things shallowly. A mind with a high threshold is patient: it persists, goes deep, misses other
opportunities. Neither is broken. They're different characters." And: "The range is the resource." The same
algebra, different parameters: a fiction corpus needs the impatient and the patient, the reckless and the
cautious, minds that park early and minds that cannot let go.

The rule for what belongs here: a parameter is temperament if every value in its range still gives a working
mind that tells a coherent story (each setting must round-trip), and different values give different,
nameable characters. What makes a mind work at all (funding thresholds, working-memory slots, the force
world's physics) stays global; what the narrator chooses (selection, plants) belongs to the author.

Each trait is one SOV quantity, read the same way by both arms:
  patience     failed claims running on a wanted region before the want is parked (given up); None: never.
               The want's parking threshold. Gerundelle Params.patience; lean LeanMind(patience=).
  persistence  how slowly a question that keeps being asked stops being worth asking: an experiment's value
               after n repeats is q / (q + n) of its first (Gerundelle Inquiry.decay; lean's rumination
               decay, KAPPA q / (KAPPA q + n)). The question's parking threshold. 1: as built.
  curiosity    the pull of unknowns no want pays for (unclaimed regions, uniqueness), as a multiple of the
               territory's own (Gerundelle Territory.pull; lean's curiosity floor and unclaimed pull). 1: as
               built.
  credulity    the weight a told receipt funds at, lived ones at 1 (both arms' "told at half": 0.5).
  stubbornness how often another may undo what this mind holds before it gives the want up; None: the scene's
               own setting. Gerundelle arm GerundelleMind(stubbornness=); lean LeanMind(resolve=).
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Temperament:
    patience: int = None
    persistence: float = 1.0
    curiosity: float = 1.0
    credulity: float = 0.5
    stubbornness: int = None

    def lean(self):
        """Keyword arguments for LeanMind (stubbornness is its resolve, given only when set)."""
        out = asdict(self)
        stub = out.pop("stubbornness")
        if stub is not None:
            out["resolve"] = float(stub)
        return out

    def gerundelle(self):
        """Keyword arguments for GerundelleMind (passed on into Gerundelle's Params where it has them)."""
        out = asdict(self)
        if out["stubbornness"] is None:
            out.pop("stubbornness")
        return out


PROFILES = {
    "steady": Temperament(),                                    # the ladder's characters so far
    "impatient": Temperament(patience=2),                       # gives a want up after two failures running
    "patient": Temperament(patience=6),
    "restless": Temperament(persistence=0.25, curiosity=2.0),   # moves on fast, explores broadly
    "dogged": Temperament(persistence=4.0, curiosity=0.5),      # stays on one question, ignores the rest
    "trusting": Temperament(credulity=0.9),
    "skeptical": Temperament(credulity=0.1),
    "yielding": Temperament(stubbornness=1),
    "obstinate": Temperament(stubbornness=6),
}
