"""The common trace: what a mind did and what happened to it, beat by beat, whatever the substrate.

Both arms write it: the lean SOV layer (lean.py) and Gerundelle's mind (gerundelle_arm.py), acting in
the same ForceWorld. The story layer (story.py) reads only this, so the two substrates are compared on
one printer and one set of measures.

A beat is one ledger event made tellable:
    see        a slice perceived (the scene as it stands)                      -> describing
    want       a control hole opened: a change wanted                          -> narrating (wanting)
    wonder     a hole won attention: its open slot posed to oneself (Pose)     -> expressing_curiosity
    try        a push (the generator: ledger -> world)                         -> narrating
    change     what followed, seen (Fit, lived)                                -> narrating
    nothing    a push followed by no change (Fit: "it does nothing here")     -> narrating, not
    other      a change the mind did not cause (a gust's): something else moved -> narrating
    believe    an explanation worked out (Constrain; may be wrong)            -> claiming
    surprise   a prediction contradicted (the world's testimony)              -> contrasting
    learn      a condition found: the push works only when ...               -> explaining
    reach      the wanted change arrived: the control hole closes             -> narrating, then a phase
    feel       an emotional phase (an agent's phase change)                    -> expressing_*
    wait       a push parked: its learned condition is not met now; watching   -> narrating
    ask        a hole's open slot posed to another mind (Pose: shape only)      -> asking
    tell       an answer given from the teller's funded receipts (Attest)       -> telling
    time       time passing with nothing done (a scene break)                     -> grounding
    recall     an episode remembered by structure (Case-2 analogy), its condition carried over -> realizing
    scene      a new scene: the mind in another world, its history kept          -> describing (a frame)

Each beat carries its hole (the SOV it is about), its provenance (lived, worked, told, imagined) and the
hole's pull at the time, so the story layer can choose what is worth telling and the measures can check
that later beats depend on earlier ones (history).
"""
from dataclasses import dataclass, field

KINDS = ("see", "want", "wonder", "try", "change", "nothing", "other", "believe", "surprise", "learn",
         "reach", "feel", "wait", "ask", "tell", "time", "recall", "scene",
         "leave", "return", "rise", "lost")   # rung 7: authored comings and goings; a kept state lost


@dataclass
class Beat:
    t: int                      # world tick
    kind: str                   # one of KINDS
    actor: str                  # the mind (a character's name) or "world"
    hole: str = ""              # the SOV the beat is about ('' for none)
    obj: str = ""               # the object acted on or changed
    detail: dict = field(default_factory=dict)   # kind-specific: strength, from/to gerund, cause, condition, phase
    prov: str = "lived"         # lived | worked | told | imagined
    pull: float = 0.0           # the hole's pull when the beat happened
    refs: tuple = ()            # earlier beats (indices) this one depends on: history made explicit

    def __post_init__(self):
        assert self.kind in KINDS, self.kind


def effect_parts(effect, objs=()):
    """'lid_releasing' -> ('lid', 'releasing'); 'wrong_key_sliding' -> ('wrong_key', 'sliding') given
    the scene's objects (the longest object name that prefixes the effect); 'register_filling_+2' ->
    ('register', 'filling')."""
    obj = max((o for o in objs if effect.startswith(o + "_")), key=len, default=effect.split("_", 1)[0])
    rest = effect[len(obj) + 1:]
    return obj, rest.split("_")[0] if rest else ""
