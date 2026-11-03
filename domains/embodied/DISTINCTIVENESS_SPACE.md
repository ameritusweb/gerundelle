# Distinctiveness space

A novel representation for object identity, orientation, recognition, and reality judgment
in the SOV architecture. Distinctiveness space is where the unique marks on each object
live — not as features to be averaged across a category, but as molecules in the tournament
whose quality tells the mind whether what it sees was made by a world it understands.

## The problem it solves

The gerund field tells you what things are doing. The tournament tells you what to attend
to. The ownership register tells you why you care. But none of them answers:

- **Which thing is which?** Two cups, both "resting." Which is the one you drank from?
- **Which way is it facing?** A cup rotated. The gerund didn't change. How do you know?
- **Is it real?** A CGI cup has every gerund a real cup has. How do you tell the difference?

These were open slots in the embodied cognition architecture. Distinctiveness space fills
all three.

## What distinctiveness is

Every real object has marks that make it unlike every other object: a chip on the rim, a
scratch on the surface, a worn patch where hands grip, an asymmetric curve in the handle,
a crack in the glaze. These are not general features shared by all cups. They are what
makes THIS cup this cup.

Each distinctive mark is a **molecule** in the tournament. It competes, bonds, funds, and
carries information the same way every other molecule in the architecture does.

```
molecule = {
  id: unique across the scene,
  object: which object it belongs to,
  position_on_object: where on the object (local),
  position_in_field: where in the gerund field (world),
  gerund_context: the gerund of the region it sits in,
  quality: {
    roughness,        // how rough the edges are
    depth,            // how deep the mark goes
    edge_profile,     // sharp, worn, chipped, cracked
    correlation,      // does it follow use, grain, stress, growth?
  },
  bonds: [],
  receipts: [],
}
```

## The four jobs of a distinctiveness molecule

Each molecule does four things through the same tournament, not through four separate
systems:

### 1. Identity

The chip molecule bonds with the worn-patch molecule and the crack molecule on the same
object. The bonded set IS this cup. No other bonded set matches. Recognition of this
specific cup is the bonded set winning in the tournament.

Seeing one marker triggers resonance for the rest: the chip appears, and the worn patch
fires from storage before the mind even sees it. The bond pulls the set into attention.
This is how you recognize your cup in a row of cups — one mark, and the rest follow.

### 2. Orientation

The chip is to the left of the handle in the gerund field. That spatial relationship
between distinctiveness molecules is the cup's facing. Rotate the cup: the chip moves to
the right of the handle. The molecules are the same. Their arrangement in the field
changed.

The mind reads orientation from where the distinctiveness molecules sit relative to each
other — not from an angle measurement but from the tournament's perception of their
spatial bonds in the gerund field.

### 3. Gerund tracking

The chip sits in a "resting" region of the gerund field. The cup slides: the chip is now
in a "sliding" region. The chip didn't change. Its context did. The mind tracks the
object's gerund through its distinctiveness — the marks are the anchors that carry identity
through state changes.

### 4. Category recognition

The chip's quality — rough edges, impact-consistent depth, at the rim where cups get
knocked — lands in a **funded region** of distinctiveness space. The worn patch's quality —
friction-consistent, where hands grip — lands in another funded region. Each marker
individually makes sense as real distinctiveness on a cup.

Recognition is not feature matching. It is: do the distinctive marks on this object,
which I have never seen before, land in funded regions of distinctiveness space? Are they
the KIND of distinctiveness that cups have? If yes, it is a cup — even though every
specific mark is novel.

## Distinctiveness space has structure and density

Not all distinctiveness is equal. The space has regions, and the mind's funded conditions
determine which regions make sense. But funding is not binary. Funded regions carry
**density**: how commonly marks of this kind occur in the mind's experience. Density is
what makes the space work as a compression mechanism, not just a recognition mechanism.

### Funded regions with density

Areas of distinctiveness space where the mind has lived experience of how the real world
produces marks. Each region has a density — how many marks of this kind the mind has
encountered:

- **Wear from use:** appears where hands grip, where things rub, where contact repeats.
  Funded by a lifetime of touching and observing real objects. **High density** — nearly
  every handled object shows it. Common. Low discriminative value per mark.
- **Impact damage:** chips at edges, cracks along grain, rough fractured surfaces. Funded
  by pushing things and watching them break. **Medium density** — many objects show damage,
  each in its own way.
- **Growth asymmetry:** no face is symmetric, no tree is regular, no handmade object is
  uniform. Funded by observing living and handmade things. **High density for small
  asymmetries**, low density for large ones — a slightly crooked nose is common, a very
  crooked one is rare and highly distinctive.
- **Age and patina:** surfaces darken where exposed, lighten where protected, wear smooth
  where touched. Funded by observing things over time. **Density varies by age** — slight
  patina is common, deep oxidation less so.

The dense core of a funded region is where common marks cluster. The sparse periphery is
where rare marks sit. This distinction does double duty:

- **The dense core drives category recognition and resolution release.** Marks in the
  dense core are common. Everyone has eyebrows roughly there. Every cup has a handle on
  the side. These marks don't discriminate between individuals, so the mind doesn't need
  high resolution on them. The norm absorbs them.
- **The sparse periphery drives individual identity and demands resolution.** Marks in the
  sparse periphery are rare. This specific scar, this particular asymmetry, this unusual
  wear pattern. These marks discriminate. Resolution pools here.

### Unfunded regions

Areas where the mind has no lived experience of real physics producing such marks:

- **Too regular:** pores evenly spaced, scratches uniformly distributed, wear patterns
  that don't follow contact. Procedurally generated, not caused. Not just unfunded — marks
  with **impossible statistics**, a density profile no real population produces.
- **Too clean:** edges too sharp for a chip, surfaces too smooth between features,
  transitions too crisp. Rendered, not broken.
- **Uncorrelated with forces:** marks that don't follow grain, wear that doesn't follow
  use, asymmetry that doesn't follow growth. Generated by a noise function, not by physics.

### The boundary

Real distinctiveness and fake distinctiveness sit in different regions. They do not blend.
The mind doesn't need a "real vs fake" label. It has funded regions and unfunded regions,
and funded regions with density profiles that real populations produce. A CGI face's
too-regular pores aren't just in an unfunded region — they're marks with a density
profile no real face produces. The fakeness is in the statistics, not just the quality.

## Expected novelty

The deepest property of distinctiveness space: the mind EXPECTS objects to have novel
distinctiveness.

You see a cup you've never seen before. It has a chip you've never seen, a handle shape
you've never seen, a glaze pattern you've never seen. None of those match anything in
memory. But you expected a cup to have its own chip, its own handle shape, its own glaze.
The specific marks are new. The fact that it has its own marks is not.

This is not "I expect cups to have handles" (a general feature). It is: "I expect any
real cup to have distinctive marks of its own, and those marks should be the kind of marks
real physics produces on cups." The novelty of the marks is itself expected. A cup with
NO distinctive marks — perfectly uniform, featureless — would be surprising, because real
objects are not featureless. A cup with distinctive marks whose quality makes sense is
recognized instantly, even though every mark is novel.

### The uncanny valley

A CGI face fills every distinctiveness slot. It has eyes, pores, wrinkles, asymmetry.
Each feature is novel — this specific face was generated, never seen. But the pores are
too regular. The wrinkles don't follow muscle lines. The skin is too smooth between
features.

The distinctiveness slots are filled. But the fillers land in unfunded regions of
distinctiveness space. The mind's funded conditions — how real skin ages, how real pores
distribute, how real wrinkles follow expression — are contradicted. The result is the
valley: close enough to funded that most bonds form, far enough that the conditions are
violated. The conflation detector (Chapter 6) fires: some bonds say real, some say not.
The mind hasn't split yet. It knows something is wrong before it knows what.

The uncanny valley is not about similarity to humans. It is about the funded conditions
on distinctiveness being contradicted. The discomfort is the bimodal signal in the
tournament — a conflation the mind has not yet resolved.

## Distinctiveness and rotation

Distinctiveness space doesn't just track identity. It tracks spatial structure:

**Rotation** is the distinctive markers moving relative to each other and to the body in
the gerund field. The cup turns: the chip moves from left to right. The gerund didn't
change. The distinctiveness pattern changed. Same object, different orientation.

**Alignment** is distinctive features of two objects in a consistent spatial relationship.
A key in a lock: the teeth's distinctiveness must align with the pins' distinctiveness.
The alignment is a condition: "the key works only when these markers line up with those
markers."

**Relative rotation** is a conditions slot. The key at this angle: it turns. At that
angle: it doesn't. The distinctive features of the key and the lock have a relative
orientation that the conditions slot learns by contrast.

## The objective: minimize resolution, not maximize discrimination

The optimization is not "find the most discriminative marks." It is: **what is the minimum
resolution that still tells this object apart from every other object the mind has
encountered?**

This is a compression objective. More experience makes profiles cheaper, not richer. The
more faces you see, the more you learn which marks are common (high density in
distinctiveness space, low discriminative value) and which are rare (sparse periphery,
high discriminative value). Common marks stop winning tournaments — they're no longer
surprising against the population. Resolution drops on them. Rare marks keep winning.
Resolution stays on them.

The trajectory:

- **Few objects seen.** The mind doesn't know what's common. It allocates resolution
  broadly. Every mark might be distinctive because the population is too small to know
  otherwise. Expensive.
- **Many objects seen.** Most marks are known to be common. Resolution drops on common
  regions. The nose, the general eye shape, the handle shape — all coarse. Only the actually
  distinctive marks get high resolution. The profile is sparser and cheaper.
- **Thousands of objects seen.** The mind knows the full distribution. Resolution is
  surgical — a handful of marks that are genuinely rare, everything else at minimum. The
  profile is maximally compressed. Recognition is FASTER because the mind processes LESS.

**Expertise is compression, not enrichment.** The expert doesn't see more than the novice.
The expert needs to see less. A bird watcher identifying a warbler concentrates resolution
on two or three marks that separate this species from every other warbler in their funded
space. Everything else is coarse. They appear more perceptive because they know exactly
where to look and ignore everything that isn't distinctive.

### The norm

The typicality model — the "average face," the "typical cup" — is not a stored template.
It is the **aggregate density of funded distinctiveness space**, falling out for free. The
dense core of the funded region IS the norm. Common marks cluster there. Resolution
releases there. An individual's profile is the **residual**: what this object has that the
norm doesn't predict.

Eyebrows roughly there, nose roughly this shape — the norm carries it. The individual
doesn't have to. The profile shrinks to what the norm can't account for: the scar, the
unusual spacing, the chip in an unexpected place. Valentine's face space — faces coded as
deviations from a norm — is what this looks like from the outside. The caricature effect
falls straight out: exaggerate the residual (the marks that deviate most from the dense
core) and recognition is faster, because the bonds that matter are sharper.

### The tournament finds the optimum without computing it

Every term in the compression objective maps to a mechanism the architecture already has:

- **Surprise is marginal information.** A mark gets noticed when it's surprising — when
  the existing profile failed to predict it. "Surprising given what the profile already
  predicts" is the greedy selection rule for maximizing marginal discriminability. The
  baby's finger catching on the chip isn't a precursor to optimization. It IS the
  optimization step.
- **Receipts are the persistence term.** Each re-encounter where the mark recurs adds a
  receipt. A mark that vanishes stops accumulating. Weighting by receipt depth just is
  weighting by persistence — measured, not assumed.
- **The tournament is the cost term.** Molecules compete for slots. A mark that never does
  discriminative work stops winning, stops being attended, and decays out of the profile.
  The budget isn't enforced by a regularizer. It's enforced by the scarcity of attention.
- **The contrast set is sampled, not specified.** The population term is the history of
  what the mind actually had to tell apart. The other-race effect: profiles optimized
  against the wrong population. The prediction: move somewhere new, discrimination
  improves as the contrast set resamples — which is empirically what happens.

The mind runs a greedy, online, anytime approximation. Each encounter makes one local
move — add a surprising mark, deepen a receipt, let an idle molecule decay — and the
profile drifts toward the optimum without any process ever representing it. The formula
is the mathematician's summary of where the drift goes, the way "minimize free energy"
summarizes what a soap bubble does. The bubble doesn't calculate.

### Escalation on collision

The profile is normally the cheap pass — minimum resolution, the residual against the
norm. Sometimes the minimum fails: twins, or the friend who shaved. The system doesn't
crash. It **escalates locally** — spends resolution it normally skips, hunting for a finer
residual that separates the two colliding profiles.

The mother discriminating twins doesn't see them at high resolution all the time. She's
learned WHERE to drill: the mole on the left twin's chin, the slightly different hairline.
Those are marks that sit below the normal profile's resolution threshold but above it
when the cheap pass fails and the tournament re-escalates.

Recognition is progressive refinement:
1. **Coarsest sufficient pass first.** The residual against the norm. Usually enough.
2. **Collision detected.** Two profiles resonate on the same set of marks. The tournament
   can't settle.
3. **Escalate.** The tournament allocates resolution to marks it normally skips. Finer
   details enter the pool.
4. **Discriminate.** The finer residual separates the colliding profiles. The mole wins
   the tournament.
5. **The escalation point is remembered.** Next time, the mind knows WHERE to drill for
   this pair. The escalation becomes part of the funded profile.

### The profile is never finished

Identity is homeostatic, continuously re-funded. The face you haven't seen in twenty
years is hard to recognize not because memory faded — the marks are in storage. It's hard
because the object drifted (aged, changed) while the profile went stale. The stored
residual was computed against a norm and a face that no longer match. Show the person a
photo of the friend as they looked twenty years ago and recognition is instant. The
profile isn't degraded. It's aimed at where the face used to be.

Greedy convergence can lodge in local optima: a profile built around a mark that later
proves unstable (the friend's beard). When the dominant molecule disappears, the remaining
profile may be too sparse to resonate. The system predicts recognition failure at exactly
those points — and recovery through contradiction and rebuilding.

### Sleep as profile reorganization

The waking mind funds one profile at a time: greedy, local, one encounter one update.
Sleep replays the stored profiles against the current density of distinctiveness space and
strips marks whose commonness has changed. A mark that was discriminative when you knew
three cups is no longer discriminative now that you know twelve. The dream strips it. The
profile sharpens.

This is not recalculating the norm. The norm is the density, and the density shifts as
profiles fund. Sleep re-residualizes every profile against the current shape of the space.
Profiles that were optimal against the old population adjust to the new one. Marks that
were rare and are now common lose resolution. Marks that were common and are now rare
gain it.

Perceptual narrowing in infants is the first large-scale instance: the six-month-old
discriminating monkey faces has resolution allocated to monkey-face distinctiveness. By
nine months, those dimensions have never paid in the baby's actual population. Sleep
reallocates the budget. The capacity wasn't lost. The resolution was withdrawn because
monkey-face distinctiveness never won tournaments against human-face distinctiveness.
The compressor did its job.

## Resolution follows distinctiveness

With the density model, resolution allocation is precise:

- **Dense core (common marks): minimum resolution.** The norm absorbs them. Eyebrows,
  general nose shape, handle placement. Coarse. Cheap.
- **Sparse periphery (rare marks): high resolution.** The individual's residual. The scar,
  the unusual spacing, the chip in the unexpected place. This is where the identity lives.
- **Unfunded regions: alert.** Marks here trigger the conflation detector. Not recognized,
  not ignored — flagged.
- **Everything else: no resolution.** The smooth, featureless middle of a gerund region.
  Skip it.

The tournament allocates resolution by density. A mark in the dense core stops winning
tournaments — it's expected, it's common, it doesn't discriminate. A mark in the sparse
periphery keeps winning — it's rare, it's surprising, it carries identity. Resolution
follows surprise, which follows density, which follows the funded population.

## Face recognition as the most heavily funded province

Faces are not a special case requiring special machinery. They are the most densely funded
region of distinctiveness space, and every face-recognition finding falls out of the
density model:

**The inversion effect.** Faces are catastrophically harder to recognize upside down.
Under the configural hypothesis, this is a holistic module switching off. Under minimum
resolution, it's simpler: a lifetime of face interaction funded the profile in upright
orientation at enormous density. Invert the face and the spatial bonds between
distinctiveness molecules no longer land where the funding is. No module needed — just
the most heavily funded region in the whole space, orientation-locked because that's how
it was funded.

**The other-race effect.** Not missing machinery. Not even miscalibrated contrast sets.
**Over-compression.** The typicality model confidently releases resolution from marks that
happen to be the discriminative ones in another population. The failure is the compressor
doing its job on the wrong statistics. Less interaction with faces of another race means
sparser funding in that region. The profiles are compressed against a norm that doesn't
fit.

**The Greeble experiments.** People trained to expertise on novel objects show face-like
inversion effects. Impossible if face recognition is modular. Inevitable if face
recognition is what happens when any category gets funded densely enough. Direct evidence
that there is no face-specific mechanism — just the density of funding.

**Valentine's face space.** The dominant formal model codes each face as a deviation from
a norm. The caricature effect: exaggerate the deviations and recognition is faster than
for the real face. Distinctiveness is literally the recognition signal. Valentine backed
into the architecture decades ago without a causal story. Distinctiveness space supplies
the story: the deviations are molecules, their quality is funded by growth-asymmetry
experience, and the profile is the bonded residual against the dense core.

**Relational marks as molecules.** The spacing between the eyes being unusually wide is
itself a distinctive mark — a molecule whose position is relational rather than local. A
scratch deviates from a smooth surface; a wide-set gaze deviates from the funded typical
geometry. Both are deviations landing in funded regions of how growth produces variation.
The first-order/second-order distinction in the face literature collapses: "configural"
effects are distinctiveness molecules of a relational kind. What psychologists call
configural structure is the bonded set including its spatial bonds, taken as the unit that
resonates from storage.

**Expert fixation patterns.** Experienced face viewers recognize from a couple of fixations
near the eyes-nose center. Novices and children scan more widely and longer. Exactly what
minimum resolution predicts. The expert has compressed the profile to a sparse residual
and needs only a glance at where the distinctive marks cluster. The novice hasn't
compressed yet and allocates resolution broadly.

**Identical twins.** Near-identical distinctiveness profiles. The profiles almost collide.
Mothers lean on the one local mark that separates them — a mole, a scar, a slightly
different hairline. The escalation mechanism: the cheap pass fails, the tournament
re-escalates, resolution pools on the single molecule that discriminates. The twins prove
that when the profile collides, the system degrades to individual molecules — exactly as
the architecture predicts.

**Testable commitment.** There should be nothing faces do that a sufficiently funded
category of anything else can't do. And face recognition should degrade exactly where
distinctiveness profiles degrade: identical twins, the other-race effect, inverted faces,
faces encountered only briefly (sparse funding).

## How it funds

Distinctiveness space is not pre-built. It funds through interaction, the same way every
other SOV structure funds:

1. **A baby sees the gerund field from birth.** Objects are doing things. But distinctiveness
   is unfunded — the baby doesn't know which marks matter, what quality means, or how to
   track identity through change.

2. **Interaction funds the marks.** The baby grasps a cup. The chip catches its finger. A
   surprise — the chip is noticed. A molecule forms. The baby grasps again. The chip is
   there again. A receipt. The chip becomes a funded distinctive marker on this cup.

3. **Quality funds over many objects.** After interacting with many chipped things, the
   mind has funded conditions on what chips are like: rough edges, impact-consistent depth,
   at edges and rims. The region of distinctiveness space for "chip" is funded. A new chip
   on a new object lands in the funded region and is instantly recognized as a chip, even
   though this specific chip is novel.

4. **The fake stands out.** After funding distinctiveness space from real objects, a
   procedurally generated object lands in an unfunded region. Its marks don't follow the
   funded conditions. The mind doesn't need a "fake" label. It has an unfunded region and
   the conflation detector.

## Produced distinctiveness: constraints collapse a space of solutions

Everything above is distinctiveness **discovered**: a mark relationally unique among the things
in a context. Distinctiveness can also be **produced**. Constraints don't select from existing
distinctive things. They generate distinctiveness by collapsing a space of equivalent solutions
down to one. The solution is distinctive not because it differs from other things in the world,
but because it is the only thing that survives the constraint intersection.

The definition does not change: distinctive is relationally unique in context. What changes is
where the context comes from. In recognition the world hands it over (these mugs, this genre).
In action the mind builds it, out of constraints.

### Reaching and grasping

There are many ways to grasp a mug: by the handle, around the body, by the rim, from above. All
of them work and they are interchangeable, so none is distinctive. Apply constraints (the mug is
full of hot coffee, I'm going to drink from it, the rim is chipped, the bottle is in the way on
the left, my hand has this span) and perhaps one grasp survives: the handle, from the right,
fingers through, thumb on top. It is distinctive because it is the solution that satisfies the
constraints.

### Constraint search, not solution search

This is not constraint satisfaction, and it is not solution search. The mind does not compute a
grasp in advance. It attempts, and most attempts fail. Among the failures, one attempt stands
out: the one where the constraints converge. It is **noticed** as distinctive among the failures,
the way a chip on a rim is noticed, not computed. What is stored is its signature, the convergent
constraints that singled it out; the next time those constraints are present, the signature
resonates and the solution comes back.

What is searched is constraints, not solutions. That is why it is tractable: the solution space
(every grasp, every word, every design) is enormous, practically unbounded; the constraints that
matter are few (hot, chipped, the bottle on the left, the hand's span, going to drink). The mind
never works through the space of solutions. It looks for which constraints matter, and resolution
goes only to what they touch: the handle's gap, the chip, the bottle's edge, the level of the
coffee. A mapping need not end in exactly one solution. It ends in one (distinctive), several
(under-constrained: style), or none (over-constrained: negotiation), and in every case it was
reached without enumerating the space.

Gerundelle already does constraint search under another name: a failed claim opens a control slot,
"what blocks it?", which pays for a conditions question, and Inquiry suggests experiments to answer
it. Each step searches for a constraint, never a solution.

### Failures are constraint revelations

In the paradigm Gerundelle departs from (deep learning at scale, transformers, and reinforcement
learning on top of them, roughly 2017 on), failure is always a negative signal: a loss to
minimize, a negative reward, a dispreferred sample. The system learns by reducing failure.

In Gerundelle, failures are **constraint revelations**. Each is informative not because it says
what not to do, but because it exposes a constraint not yet found. The spill reveals the tilt
constraint. The knocked bottle reveals the spatial constraint. The slip reveals the surface
constraint. Failures are not the opposite of success; they are the raw material that makes
success recognizable. Enough of them are needed to triangulate the convergence.

So the aim is not to minimize failures but to extract constraints from them efficiently. A failure
that reveals a new constraint is worth more than a success that confirms what was already known.
The most informative failure is a **near miss**: one that differs from the success in a single
respect, isolating one constraint cleanly, where a flail tangles several together. Experts fail
informatively: their failures are near misses, almost deliberate, probing one constraint at a
time. Boundary-testing. The measure for the build: constraints revealed per failure (a novice,
many failures with little each; an expert, few failures, each a near miss).

Failed attempts are territorial probes. The force world pushes back, and that resistance is a
constraint being revealed. The agent is not being defeated; it is reading the shape of the
territory through what blocks it. The whole system is built not for avoiding resistance but for
extracting the most constraint information from it. That is a fundamentally different
relationship to difficulty than any learning framework of that paradigm has.

Lineage, as contrast: Winston's arch learner (1970) refined a concept from near misses, and
Mitchell's version spaces (1982) tightened a hypothesis with negative examples. Both learn from
negatives a teacher supplies; neither has an agent whose own failed attempts are the world's
resistance, nor success noticed as where revealed constraints converge.

### It unifies

- **Design.** A good design is not distinctive because it looks different. It is the solution
  that survives the most constraints at once. The more constraints, the more distinctive and
  inevitable it feels.
- **Theory.** A scientific theory becomes distinctive not by being unlike other theories but by
  being the only thing that satisfies the evidential constraints.
- **Words.** A word in a sentence is chosen not by comparison with other words but by what
  meaning, syntax, rhythm and register jointly permit.

Creativity in Gerundelle is then not search or recombination. It is constraint accumulation until
distinctiveness emerges. Expertise is knowing which constraints to apply first.

In the architecture's terms, a constraint is a **conditions** slot. A conflation split adds a
boundary condition; "what blocks it?" asks for the conditions on a claim. Constraint
accumulation is filling conditions slots: while the constraints found do not yet converge, the
question stays open and pulls; when they converge on a distinctive solution, it closes.

### Over-constraint: the dropped constraint is the confession

When nothing survives the intersection (the mug is hot, the handle is chipped, the bottle blocks
the other side) the system doesn't fail. It negotiates. Territory decides which constraint to
drop, so the negotiation is not arbitrary: the agent drops the constraint protecting the least
held ground first. Not spilling on the book outranks not using the chipped handle.

Over-constraint therefore reveals value structure. You cannot see what an agent truly holds until
something has to give. The dropped constraint is the confession. Expertise is knowing which
constraints to apply first, and also which to let go.

It reaches the social layer. Two agents over-constrained together must negotiate whose
territorial claims outrank whose. Not spilling on the book beats not using the chipped handle, but
whose book? That matters enormously.

### Under-constraint: style

Constraints rarely collapse to exactly one solution. Usually a small set of equivalent solutions
remains, and something has to break the tie. Style in most frameworks is mysterious, an
ineffable quality that resists analysis. Here it has a precise definition: **style is the
distinctiveness signature of tie-breaking, across a lifetime of under-constrained solutions.**
Same constraints, same surviving solution space, but this mind always reaches through the handle,
this writer always chooses the shorter word, this architect always lets go the constraint that
touches light rather than structure.

Style is more revealing than the constrained choices, because those were forced. The
tie-breaking is where the agent's particular graph shows through most purely. Different
temperaments (different SOV parameters) are different characters, and style is where they show.

For fiction generation this is exact. A transformer picks the high-probability word. Gerundelle
picks the word that survives the constraints, and in the remaining tie-space the agent's
character decides. That is the difference between competent writing and a voice.

## What it replaces

| Current paradigm | Distinctiveness space |
| --- | --- |
| Feature vectors (shared properties of a category) | Molecules (unique marks on an individual) |
| Feature matching (does this match the template?) | Funded quality (does this distinctiveness make sense?) |
| Object classification (what category?) | Distinctiveness landing in a funded region (what kind of marks?) |
| Instance recognition (match to a known individual) | Bonded marker set resonating from storage |
| Orientation estimation (compute an angle) | Marker arrangement in the gerund field |
| Anomaly detection (trained on normal, flags outliers) | Unfunded region of distinctiveness space |
| The uncanny valley (unexplained discomfort) | Conflation: funded conditions contradicted by fake statistics |
| The face inversion effect (holistic module) | The most heavily funded region, orientation-locked |
| The other-race effect (miscalibration) | Over-compression against the wrong population's statistics |
| Configural vs featural processing (a debate) | One representation: relational and local molecules in one space |
| Valentine's face space (deviations from a norm) | Residuals against the dense core of funded distinctiveness |
| The caricature effect (exaggeration aids recognition) | Exaggerated residuals resonate the profile harder |
| Expert recognition (more detail seen) | Minimum resolution: the expert needs to see less, not more |
| Perceptual narrowing in infants (capacity lost) | Compression succeeding: budget reallocated from unfunded dimensions |

## Why it's novel

Distinctiveness space has no analogue in the current paradigm:

- Neural networks treat distinctiveness as noise to be averaged out
- Feature spaces compress it away in service of category boundaries
- Embeddings project it into a shared space where individuals are indistinguishable
- Templates match against stored examples, not against funded conditions on quality
- No existing system has a representation where novel, never-before-seen marks are the
  primary signal, and where the mind's judgment of "this makes sense" comes from funded
  conditions on how real physics produces marks

It is a novel space for a novel learning system. Each novel space in this project filled
an open slot the previous ones created:

- The gerund field filled the perception slot (what things are doing)
- The tournament filled the attention slot (what to attend to)
- The SOV algebra filled the understanding slot (what you know and don't know)
- The ownership register filled the motivation slot (why you care)
- Distinctiveness space fills the identity, orientation, and reality slot (which thing,
  which way, and is it real)

Each one could only be conceived after the previous ones existed, because each one's
open slot was only visible from the vantage point of what had already been built.
