"""
Distinctiveness space — pseudocode sketch, revision 3.

Revision 2 + six fixes: compress considers the contrast set, escalation is
defined and stores drill points per pair, sleep bonds produce imagined
receipts, decay feeds back into profile vulnerability, norm cooling is
per-dimension, and gerund context modulates candidacy.

Still no global objective anywhere. Every update is local, greedy, online.
"""

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 0. Receipts — provenance first, everything else second
# ---------------------------------------------------------------------------

PROVENANCE_WEIGHT = {
    "lived":    1.0,
    "told":     0.5,
    "imagined": 0.0,
}

@dataclass
class Receipt:
    provenance: str
    interaction_ref: str
    tick: int
    kind: str = "recurrence"    # recurrence | causal_story | gerund_held | sleep_bond

    def weight(self) -> float:
        return PROVENANCE_WEIGHT[self.provenance]


# ---------------------------------------------------------------------------
# 1. Quality — typed SOV slots, each with its own funding level
# ---------------------------------------------------------------------------

@dataclass
class Slot:
    value: object
    funding: float = 0.0

@dataclass
class Quality:
    roughness:    Slot
    depth:        Slot
    edge_profile: Slot
    correlation:  Slot

    def slots(self):
        return [self.roughness, self.depth, self.edge_profile, self.correlation]

    def funded_score(self) -> float:
        return sum(s.funding for s in self.slots()) / len(self.slots())


# ---------------------------------------------------------------------------
# 2. Molecules — tournament participants
# ---------------------------------------------------------------------------

TAU = 10.0
EPS = 1e-12

@dataclass
class Molecule:
    id: str
    object_id: str
    position_local: tuple | None
    quality: Quality
    receipts: list = field(default_factory=list)
    strata: int = 0
    gerund_context: str = ""
    half_life: float = 40.0
    heat: float = 1.0
    open_sites: list = field(default_factory=list)
    _last_won: int = 0

    def bid(self, norm, want_pull: float, gerund_urgency: float = 1.0) -> float:
        tension = 1.0 + 0.25 * len(self.open_sites)
        return (norm.surprise(self)
                * self.persistence()
                * want_pull
                * self.heat
                * tension
                * gerund_urgency)

    def persistence(self) -> float:
        weighted = sum(r.weight() for r in self.receipts) + 0.5 * self.strata
        return 1 - math.exp(-weighted / TAU)

    def decay(self, tick: int):
        idle = tick - self._last_won
        self.heat *= 0.5 ** (idle / self.half_life)

    def tick_gerund(self, gerund_field, tick: int):
        current = gerund_field.region_of(self)
        if current != self.gerund_context and self.gerund_context:
            self.receipts.append(Receipt(
                "lived", f"gerund:{self.gerund_context}->{current}",
                tick, kind="gerund_held"))
        self.gerund_context = current

    def last_won(self) -> int:
        return self._last_won

    def record_win(self, tick: int):
        self._last_won = tick


@dataclass
class RelationalMolecule(Molecule):
    relates: tuple = ()
    relation: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 3. Gerund urgency — context modulates candidacy
# ---------------------------------------------------------------------------

GERUND_URGENCY = {
    "falling": 2.0,     # identity tracking through imminent change
    "sliding": 1.5,
    "held":    1.3,      # you're holding it — track it well
    "resting": 1.0,
    "supporting": 0.8,
    "anchoring": 0.5,    # the floor doesn't need identity tracking
    "empty": 0.3,
}

def gerund_urgency(mol: Molecule) -> float:
    return GERUND_URGENCY.get(mol.gerund_context, 1.0)


# ---------------------------------------------------------------------------
# 4. The norm — population density that cools per dimension
# ---------------------------------------------------------------------------

LAMBDA = 0.001
FUNDING_FLOOR = 0.01
CAUSAL_FLOOR = 0.3
JOINT_FUNDING_FLOOR = 50
JOINT_FLOOR = 0.05
ABSTAIN = -1.0

class Norm:
    def __init__(self):
        self.density = AgingDensity(cooling_rate=LAMBDA)
        self.joint = AgingJointModel(cooling_rate=LAMBDA)

    def observe(self, mol: Molecule, tick: int):
        self.density.update(mol.quality, weight=1.0, tick=tick)

    def observe_population(self, marks: list, tick: int):
        self.joint.update(marks, tick=tick)

    def absorb_released(self, mol: Molecule, tick: int):
        self.density.update(mol.quality, weight=mol.persistence(), tick=tick)

    def cool(self, tick: int, observed_dimensions: set):
        """Cool only dimensions NOT observed this tick. The norm is stable
        over short absences and adaptive over long ones. A dimension you
        keep seeing stays warm; one you stopped seeing gradually releases
        its density back to the prior."""
        self.density.age_except(observed_dimensions, tick)
        self.joint.age(tick)

    def surprise(self, mol: Molecule) -> float:
        return -math.log(self.density.prob(mol.quality) + EPS)

    def funded(self, mol: Molecule) -> bool:
        in_support = self.density.prob(mol.quality) > FUNDING_FLOOR
        causal = mol.quality.correlation.value > CAUSAL_FLOOR
        return in_support and causal

    def statistics_possible(self, marks: list) -> float:
        if self.joint.funding() < JOINT_FUNDING_FLOOR:
            return ABSTAIN
        return self.joint.plausibility(marks)

    def discriminative_value(self, mol: Molecule, contrast_set: list) -> float:
        """How much this mark helps separate the owner from its actual
        contrast set — the objects the mind really encounters and must
        not confuse. A mark common across the contrast set has low value
        even if it's rare in the global population."""
        matches = sum(1 for other in contrast_set
                      if self.density.similar(mol.quality, other))
        return 1.0 / (1.0 + matches)


# ---------------------------------------------------------------------------
# 5. Profiles — residuals whose marks can emigrate
# ---------------------------------------------------------------------------

RELEASE_THRESHOLD = 1.0
CONTRAST_RELEASE = 0.3
ADMIT_THRESHOLD = 2.0

class Profile:
    def __init__(self, object_id: str):
        self.object_id = object_id
        self.marks: dict[str, Molecule] = {}
        self.vulnerable_pairs: dict[str, list] = {}   # other_id -> escalation points

    def resonance(self, observed, trace) -> float:
        hits = [m for m in observed if self.matches(m, trace)]
        bond_fit = self.relational_fit(hits, trace)
        for m in hits:
            trace.matched_marks.append(m)
        return sum(m.persistence() for m in hits) * bond_fit

    def absorb(self, mol, norm, receipt, territory, tick):
        if not norm.funded(mol):
            return
        if receipt is None:
            territory.open_contested_slot(
                owner=self.object_id, mark=mol,
                claim="mark appeared without a causal story", tick=tick)
            return
        mol.receipts.append(receipt)
        self.marks[mol.id] = mol

    def compress(self, norm, contrast_set, tick):
        """Release what the population now predicts OR what no longer
        discriminates against the actual contrast set. A mark that was
        rare globally but common across the cups in your cupboard is
        released — it doesn't help tell YOUR cups apart."""
        for mid, m in list(self.marks.items()):
            global_common = norm.surprise(m) < RELEASE_THRESHOLD
            contrast_common = norm.discriminative_value(m, contrast_set) < CONTRAST_RELEASE
            if global_common or contrast_common:
                norm.absorb_released(m, tick)
                del self.marks[mid]

    def note_decay(self, mol_id: str):
        """A molecule cooled past its half-life. The profile got cheaper.
        But if the faded mark was the discriminating one for a collision
        pair, the profile is now vulnerable there."""
        if mol_id in self.marks:
            del self.marks[mol_id]
            for other_id, points in self.vulnerable_pairs.items():
                if mol_id in points:
                    self.vulnerable_pairs[other_id].append(
                        ("faded_discriminator", mol_id))


# ---------------------------------------------------------------------------
# 6. Tournament — budget from density, gerund urgency on candidates
# ---------------------------------------------------------------------------

INITIAL_BUDGET = 20.0
BASE = 20.0

class Tournament:
    def __init__(self):
        self.budget = INITIAL_BUDGET
        self._escalation_memory: dict[tuple, list] = {}

    def rebalance(self, norm, region):
        self.budget = BASE / (1.0 + norm.density.mass_in(region))

    def allocate(self, scene, norm, want_pull, tick) -> list:
        candidates = scene.candidate_marks(resolution="coarse")
        for mol in candidates:
            mol.tick_gerund(scene.gerund_field, tick)
        ranked = sorted(
            candidates,
            key=lambda m: m.bid(norm, want_pull, gerund_urgency(m)),
            reverse=True)
        attended, spent = [], 0.0
        observed_dims = set()
        for mol in ranked:
            price = norm.surprise(mol)
            if spent + price > self.budget:
                break
            attended.append(refine(mol))
            spent += price
            mol.record_win(tick)
            mol.receipts.append(Receipt("lived", scene.ref, tick))
            for s in mol.quality.slots():
                observed_dims.add(id(s))
        for mol in candidates:
            if mol not in attended:
                mol.decay(tick)
        return attended, observed_dims

    def escalate(self, scene, norm, where, pair_key: tuple, tick) -> list:
        """Allocate resolution below the normal threshold, specifically in
        the disagreement region. Stores the escalation point so subsequent
        encounters with the same collision pair start here."""
        prior_points = self._escalation_memory.get(pair_key, [])
        candidates = scene.marks_in_region(where, resolution="fine")
        if prior_points:
            candidates = sorted(candidates,
                                key=lambda m: m.id in prior_points,
                                reverse=True)
        extra = []
        for mol in candidates:
            mol.tick_gerund(scene.gerund_field, tick)
            extra.append(refine(mol))
            mol.record_win(tick)
            mol.receipts.append(Receipt("lived", f"escalation:{scene.ref}", tick))
        self._escalation_memory.setdefault(pair_key, []).extend(
            m.id for m in extra)
        return extra

    def exhausted(self) -> bool:
        return self.budget <= 0


# ---------------------------------------------------------------------------
# 7. Recognition — returns the trace
# ---------------------------------------------------------------------------

@dataclass
class ResonanceTrace:
    matched_marks: list = field(default_factory=list)
    held_bonds: list = field(default_factory=list)
    failed_bonds: list = field(default_factory=list)
    escalations: list = field(default_factory=list)
    conflations: list = field(default_factory=list)
    winner: object = None
    confidence: float = 0.0


def recognize(scene, norm, profiles, tournament, want_pull, tick):
    trace = ResonanceTrace()
    observed, observed_dims = tournament.allocate(scene, norm, want_pull, tick)

    for m in observed:
        if not norm.funded(m):
            trace.conflations.append(("unfunded_quality", m.id))
    joint = norm.statistics_possible(observed)
    if joint is not ABSTAIN and joint < JOINT_FLOOR:
        trace.conflations.append(("impossible_population_statistics", scene.ref))

    scores = {p.object_id: p.resonance(observed, trace) for p in profiles}
    winner, runner_up = top_two(scores)

    while ambiguous(winner, runner_up):
        pair_key = (winner.object_id, runner_up.object_id)
        region = disagreement_region(winner, runner_up)
        extra = tournament.escalate(scene, norm, where=region,
                                    pair_key=pair_key, tick=tick)
        trace.escalations.append({"region": region, "pair": pair_key,
                                  "marks_found": [m.id for m in extra]})
        observed += extra
        scores = {p.object_id: p.resonance(observed, trace) for p in profiles}
        winner, runner_up = top_two(scores)
        if tournament.exhausted():
            trace.winner, trace.confidence = None, 0.0
            return trace, observed_dims

    trace.winner, trace.confidence = winner, margin(scores)
    return trace, observed_dims


# ---------------------------------------------------------------------------
# 8. Waking loop
# ---------------------------------------------------------------------------

def encounter(scene, norm, profiles, tournament, territory, want_pull, tick):
    tournament.rebalance(norm, scene.region)
    trace, observed_dims = recognize(
        scene, norm, profiles, tournament, want_pull, tick)

    for mol in trace.matched_marks:
        norm.observe(mol, tick)
    norm.observe_population(trace.matched_marks, tick)
    norm.cool(tick, observed_dims)

    for prof in profiles:
        for mid, m in list(prof.marks.items()):
            if m.heat < 0.01:
                prof.note_decay(mid)

    if trace.winner is not None:
        prof = trace.winner
        contrast_set = [p for p in profiles if p.object_id != prof.object_id]
        for mol in novel_marks(trace, prof):
            prof.absorb(mol, norm,
                        receipt=causal_receipt(scene, mol, tick),
                        territory=territory, tick=tick)
        prof.compress(norm, contrast_set, tick)

    return trace


def causal_receipt(scene, mol, tick):
    story = scene.history.explains(mol)
    if story is None:
        return None
    return Receipt(story.provenance, story.ref, tick, kind="causal_story")


# ---------------------------------------------------------------------------
# 9. Sleep — reorganization with provenance firewall
# ---------------------------------------------------------------------------

def reorganize(profiles, norm, tick):
    """Stored profiles replayed against current density. Marks whose
    commonness changed emigrate to the norm. Every profile re-residualizes.

    Perceptual narrowing: dimensions whose marks never earn their resolution
    stop being sampled. The monkey faces at nine months were reorganized out
    of the budget, not lost.

    Open-site bonds formed in sleep are IMAGINED, not lived. The provenance
    firewall applies. Sleep sharpens the question; waking confirms it."""
    for prof in profiles:
        for mid, m in list(prof.marks.items()):
            if norm.surprise(m) < RELEASE_THRESHOLD:
                norm.absorb_released(m, tick)
                del prof.marks[mid]

    norm.density.retire_unsampled_dimensions()

    for prof in profiles:
        for mid, m in prof.marks.items():
            for site in list(m.open_sites):
                partner = find_partner_in_storage(site, prof, norm)
                if partner is not None:
                    m.open_sites.remove(site)
                    m.receipts.append(Receipt(
                        "imagined",
                        f"sleep_bond:{site}->{partner.id}",
                        tick, kind="sleep_bond"))


# ---------------------------------------------------------------------------
# Stubs — these would be real implementations in a full system
# ---------------------------------------------------------------------------

class AgingDensity:
    def __init__(self, cooling_rate): pass
    def update(self, quality, weight, tick): pass
    def prob(self, quality): return 0.5
    def age_except(self, observed_dims, tick): pass
    def mass_in(self, region): return 1.0
    def similar(self, q1, q2): return False
    def retire_unsampled_dimensions(self): pass

class AgingJointModel:
    def __init__(self, cooling_rate): pass
    def update(self, marks, tick): pass
    def age(self, tick): pass
    def funding(self): return 0
    def plausibility(self, marks): return 1.0

def refine(mol): return mol
def top_two(scores): return None, None
def ambiguous(w, r): return False
def margin(scores): return 1.0
def disagreement_region(w, r): return None
def novel_marks(trace, prof): return []
def find_partner_in_storage(site, prof, norm): return None
