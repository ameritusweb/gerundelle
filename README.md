# Gerundelle

A formally verified architecture of mind. Twelve layers, from world physics to narrative,
machine-checked in Lean 4. Gerundelle minds learn though interaction with a world model, such that 
they exhibit recursive self-improvement without human intervention or a text corpus. Their 
understanding is structural and algebraic rather than locked away in high-dimensional vectors.

## What this is

**Gerundelle** is a twelve-layer architecture of mind whose promises are theorems. Its
layers run from a world that conserves its one physical quantity, through perception,
competition for attention, provenance of evidence, memory, understanding and self-awareness,
to ownership, affect, planning, social exchange and the selection of what is worth telling.

Each layer carries guarantees that a proof assistant (Lean 4) has checked for every possible
input, every possible sequence of operations, every possible interleaving. The development
comprises **24 files**, **301 theorems**, and **no unfinished proofs**.

### The twelve layers

| | Layer | Question it answers |
| --- | --- | --- |
| **The machine** | 1. World | A physics that conserves its one quantity |
| | 2. Perception | What the agent can distinguish |
| | 3. Competition | Scarce attention slots |
| | 4. Provenance | The difference between lived, told and imagined |
| **The cognition** | 5. Memory | Thoughts that settle and reopen |
| | 6. Understanding | Open questions with typed slots |
| | 7. Self-awareness | Detecting its own loops and confusion |
| **The will** | 8. Ownership | Territory: what the agent holds, contests and loses |
| | 9. Affect | Emotions read off the territory register |
| **The reach** | 10. Planning | Sub-wants, constraint convergence, the curriculum |
| | 11. Social | Attestation, trust, the discount |
| | 12. Selection | What is worth telling, and why |

The architecture is domain-independent: one mind and one algebra run in story, code, chess
and population worlds, with no domain-specific machinery. Only the world changes.

## Play it

[![Playing Nim against a Gerundelle mind, with what it wants, what it's attending to, and what it has lived through](images/play-nim.png)](https://gerundelle.com/play/)

**[Play Nim against a Gerundelle mind](https://gerundelle.com/play/)**, in your browser. It was never told the
rules or the strategy: it tried things, the game refused what its rules don't allow, and it found the rest by
playing. The page shows what it wants, what it's attending to, what it's wondering, and why it made each move,
all read from its own records.

## The five ideas

**The world is a tree of doings.** Objects are described by what they are doing (gerunds),
not by what they are made of. A jar is *charged*. A boulder is *resting*. Materials,
distances, and positions are inferred from the force structure, not given. Where a
configuration invites a force that has not been applied, the world has an *open force slot*:
the question "what would happen?" is itself a structure.

**Understanding is a graph with its own algebra.** Known and unknown concepts are nodes,
connected by typed relations — causes, caused by, co-occurs, role, conditions, etc. An unknown is a node
defined by its relations to what is already known.
Just like x in an equation is defined by its relations to the known numbers through
operators. The unknown's identity is its topology — how it relates to what surrounds it.
Unknowns are not gaps waiting to be eliminated; they are structural citizens that persist
and pull for attention. The graph has its own algebra of [seventeen operators](SOV.md) (Fit, Individuate, Constrain,
Retract, Compose, Differentiate, Unify, Exclude, Abstract, Posit, Pose, Attest, Bind,
Quote, Archaize, Anneal, Relabel) and its own theorems. Classical algebra — equations with knowns,
unknowns, and operators — is a special case.

This graph is called an **SOV** — Structured Open Variables. "Structured" because the
relations are typed. "Open" because the unknowns remain open, pulling, participating.
"Variables" because they are defined by their relations to what is known, the same way
variables in an equation are defined by the operators around them.

**Cognition is a thought molecule tournament.** A mind can only attend to a few things
at once. Hypotheses, patterns, meta-recognitions, and wants are thought molecules that
compete for those limited slots. Molecules bind with each other — each has binding sites,
and two molecules that bond form a composite that competes as one. A bond holds two
thoughts together. The winners of each level (7 → 5 → 4 slots) are the argmax of:

`activation × (1 + binding_score) + open_site_tension + w × forward + support`

where **activation** is how alive the thought is (decays when it doesn't win, boosted
when it does), **binding_score** is how well it fits with its current partner,
**open_site_tension** is the pull of an unfilled unknown, **w** is a weighting term, **forward** is how much the
mind would still learn by attending to it (expected information gain from its Dirichlet
prior), and **support** is how many conditions, each learned from a different experience, this
thought alone satisfies at once. The tournament runs in separate tracks — thoughts, meta-cognition,
understanding, emotions, experiments, and ownership — each with its own scarce slots, so
one faculty cannot drown the others. What the agent lived through counts in full, what it
was told counts at a discount, and what it imagined counts not at all.

**Ownership is the foundational motivation.** What the agent acts for is territory: unique
concepts it perceives as its own — and being a slot in someone else's understanding is
itself a form of territory. Emotions are what the mind feels about what it holds, what
it's losing, and what it doesn't yet have. Frustration is when the mind acts and nothing
moves. Curiosity is when the mind encounters something it doesn't understand yet. Joy is
when the mind acted on something and the result was what it wanted.

**Understanding, thinking, and behavior are three different things.** Behavior is what the
system does. Thinking is the competition in the tournament — molecules bidding, winning,
binding. Understanding is the funded (SOV, world) pairs the thinking operates on. You can
have behavior without thinking. You can have thinking without understanding. You need
understanding for the thinking to produce behavior that means something. The field
conflated all three for seventy years because there was no structural definition of
understanding that would separate them. The SOV provides one.

## Why it matters

### The problem

AI has spent decades on a representation problem. Symbolic AI gives you structure
you can reason about, but it's brittle, ungrounded, and can't learn from the world.
Statistical AI gives you learning from data, but it has no structure, no unknowns,
no explanation of what it knows or why. Each solves what the other can't, and decades
of trying to combine them have produced hybrids, not unity.

Gerundelle doesn't combine them. It operates at a level where the distinction doesn't
apply.

### The ontology: a world of doings

The world is described not by what things are made of, but by what they are doing.
A jar is *charged*: it holds potential drawn from a spring. A boulder is *resting*:
its weight balances the ground's support. No coordinates, no materials, no distances.
Each object is a gerund — a doing — and a doing is a balance of forces against reserves.
When a force crosses a reserve, the gerund flips. Where a force has not been applied,
the world has an *open force slot*: a question the world itself is asking.

This follows Whitehead (things are what they are doing), Talmy (doings are force
balances), and Gibson (an open force slot is an affordance). A small set of gerunds
covers every domain because doings, unlike materials, are universal: a stone arch and
a steel beam both *support*.

And because the force world has a small state space (gerunds, not raw pixels), clear
events (a force crosses a reserve, a gerund flips), and informative failures (each one
tells you something specific), experiential learning is tractable: a mind can learn from
a handful of interactions, because the world is structured at the right level of
abstraction for a mind to act in and learn from.

### The unknown as a structural citizen

The unknown is where the architecture departs from everything before it. In statistical
AI, an unknown is a probability — a spread over outcomes, waiting to be narrowed by data.
In symbolic AI, an unknown is an uninstantiated variable — a blank, waiting to be filled
by pattern matching. In both cases, the unknown is temporary: it exists to be eliminated.

In Gerundelle, an unknown is a permanent structural citizen. It has typed relation slots.
It has bonds to what is known around it. It pulls — a constant, non-decaying tension in
the competition for attention, every tick, until it is filled. It participates in the
algebra without being resolved. It shapes the graph by what it is reaching toward.

This is intentionality in Brentano's philosophical sense: directedness toward something
without containing it. Classical AI has never cracked intentionality. Statistical AI
sidesteps it. Symbolic AI simulates it poorly. Here, intentionality is structural.

### The algebra: how the SOV generalizes an equation

Classical algebra is a special case of the SOV algebra where three constraints are
artificially imposed: the domain is restricted to quantities and the relations to
arithmetic operators; every statement must already be closed around an equality sign
before you can manipulate it; and an unknown is a passive placeholder whose only role
is to be isolated and eliminated — once x = 5, the variable disappears and the algebra's
work is done.

The SOV lifts all three while keeping the core insight that makes algebra powerful:
defining an unknown by the topology of its relations to what is known.

- **From operators to typed relation slots.** Instead of numbers linked by +, ×, and =,
  an SOV is a graph of concepts linked by typed relations — causal triggers,
  preconditions, force-reserve thresholds, ownership claims, counterfactual boundaries.
  Classical equations are the subset where the nodes are scalars and the edges are
  arithmetic.

- **From passive blanks to active structural citizens.** In classical algebra, x does
  nothing on its own; an external mathematician rearranges the equation. In an SOV, an
  unfilled slot is an active causal agent in the mind. It exerts a constant, non-decaying
  pull in the attention tournament every tick. It shapes what experiments the agent runs
  and which thought molecules bond with it.

- **Productive persistence.** An unknown in Gerundelle does not exist merely to be
  eliminated. Even while a slot remains open, the SOV participates in bonds, forms
  higher-level composites, and constrains planning. You can manipulate, compose, and
  reason with structured ignorance as a first-class mathematical object.

- **Equations that grow by acting in the world.** In classical algebra, the equations are
  handed to you; if the system is underdetermined, you are stuck. An SOV with unfunded
  slots is an underdetermined system that goes out and generates its own new equations.
  Its open slots pull the agent to apply a force in the world; the world's failure or
  flip returns a new constraint (funded by lived provenance), which narrows the open slot
  until the constraints converge and the answer is simply noticed.

An algebraic equation is a static constraint on values. An SOV is a living constraint
graph over doings — where the unknowns themselves drive the search for the missing
constraints. It is to classical algebra what complex numbers were to real numbers: not
a rejection, but an extension that makes previously inexpressible things tractable.

### The SOV subsumes logical equations

Classical algebra is equations over quantities with arithmetic operators. Classical logic
is equations over propositions with connectives (AND, OR, NOT, IMPLIES) and quantifiers
(there exists, for all). Both are special cases of the SOV. Quantities and propositions
are kinds of nodes. Arithmetic operators, logical connectives, and quantifiers are kinds
of relations. Solving an equation and proving a theorem are kinds of closing a slot.

The SOV doesn't restrict what the nodes are, what the relations are, or what the unknowns
do. It subsumes both because it operates at the level where algebra and logic are the
same thing: a graph of knowns and unknowns connected by typed relations, where the
unknowns are defined by their topology and resolved when the constraints converge.

### The mind: a market under scarcity

A mind built on this algebra is a marketplace. Thought molecules — fragments of
understanding, each carrying its bonds, its open sites, its evidence — compete for
scarce working-memory slots (7 → 5 → 4, Miller's numbers). The competition is settled
by evidence from acting in the world, not by rules, not by gradients. What the mind
lived through funds at full weight. What it was told funds at half. What it imagined
funds at zero. No operation can promote told to lived — this is proved in Lean as a
type error in a graded writer monad. Provenance is conserved the way energy is
conserved: structurally, not by policy.

### Temperament: different minds from the same algebra

Each parameter enters a formula:

| Parameter | What it controls | Formula |
| --- | --- | --- |
| patience | how many failures before giving up on a want | give up after `patience` failed actions on the wanted state |
| persistence | how slowly a repeated question loses its pull | experiment value decays by `q / (q + times_done)` where q = persistence |
| curiosity | the pull of things no goal pays for | pull of unknowns multiplied by `curiosity` |
| credulity | how much weight given to what others say | told receipts fund at `credulity` (default 0.5: half weight) |
| stubbornness | how many times another can undo what you hold | resolve starts at `stubbornness`, drains by `1 / pull` per undoing |

An impatient mind and a dogged mind are both working minds — different people, not a
broken one and a fixed one.

### Ownership, emotion, and the will

What the mind acts for is territory: whatever it perceives as its own. Emotions are
how the territory reads. Frustration is a claim that keeps failing. Curiosity is an
unclaimed region. Joy is a claim that took. Grief scales with how much was invested.
Forgiveness is a grudge whose goal was met while it was still warm. None of these are
rules about feelings. They are phase transitions in a graph read off the ownership
register — the same mathematical structure as perception, factored through a different
view.

### Planning: what the mind does when the path is long

The motivation to plan comes from the same place all motivation comes from in the
architecture: territory. A want is a territorial claim on a state the mind doesn't
hold yet. It sits in the ownership register as an open slot. Open-site tension — the
constant, non-decaying pull — keeps it in the tournament every tick. The mind can't
ignore it; the slot keeps bidding.

A plan arises when there's a gap: the want is unmet and no single action achieves it.
The planner is invoked not because a "planning module" was triggered, but because the
want won the top, the mind tried to act on it, and there was no direct way. The planner
looks for a sequence of actions that reaches the wanted state, reading off what the mind
already knows about what leads to what.

When the planner finds no way either, sub-wants decompose the gap backward: what
conditions does the known way need? What facts must hold that don't hold now? Each
becomes a nearer want, held on a stack. Each sub-want is reachable. The chain is built
from what the mind already knows. Action on the nearest sub-want closes the gap one
step at a time.

Planning isn't a separate module. It's the pull of an unfilled territorial slot — the
same pull that drives curiosity, frustration, and grief — meeting a gap too wide for
one action.

### The atom of representation: the minimal (SOV, world) pair

From all of this, one atom emerges. A known concept is not a symbol, not a weight
vector, not a rule, not a distribution. It is the minimal pairing of a structured open
variable (the understanding, with its typed slots, its funded relations, its open
unknowns) and a force world (the physics that gives those relations their meaning). The
SOV without the world is imagination — structure with no grounding. The world without
the SOV is raw physics nobody understands. The pair is the concept.

This is uniform. A steam engine is a minimal force world where heat crosses a reserve
and pressure does work, paired with the SOV that captures the conditions. Lift is a
force world where airflow exceeds weight, paired with the SOV that knows what it depends
on. Reproducibility is a world where the same push under the same conditions gives the
same result, paired with the SOV that says why. Trust is a world where a teller's word
matches or fails to match the world's answer, paired with the reliability tracking.
Concrete and abstract, physical and social, scientific and moral — the same kind of
thing, the same machinery, the same atom.

### Recursive world-building: minds that create their own worlds

Because the atom of a concept is a (SOV, world) pair, any rule system the mind has
already funded — like the rules of chess — already contains a minimal force world.
Instantiating that inner world and dropping sub-minds into it turns mental simulation
and game play into recursive world-building, using the exact same machinery as the
base layer.

- **Rules become the physics of the sub-world.** To the parent mind, the rules of
  chess are a funded (SOV, world) structure. When the parent spins up a chess sub-world
  from that structure, those rules become Layer 1 physics — forces, reserves, and legal
  flips — for the sub-minds inside it.

- **Sub-minds do real experiential work.** Inside that constructed world, the sub-minds
  aren't doing brute-force tree search. They are full Gerundelle minds with their own
  attention tournaments, open slots, sub-wants, and territorial claims. When White and
  Black sub-minds play against each other, each failure reveals a constraint and each
  tactical surprise exposes a conflation boundary.

- **Recursive growth of understanding.** The parent mind doesn't just get a move
  evaluation back from the sub-minds; it harvests the SOVs and converged constraints
  the sub-minds discovered while contending with each other. A tactical motif (a fork,
  a pin) or an opponent's behavioral quirk emerges as a newly structured (SOV, world)
  atom that feeds back into the parent mind's understanding.

This also raises a question about provenance. When a parent mind constructs an internal
world from its own understanding and lets sub-minds act inside it, the sub-minds
experience their trials as lived relative to the sub-world's physics. To the parent,
those trials are lived in a world the parent imagined — which is where the firewall
theorem and the provenance grading meet recursive construction.

### Bootstrapping: starting from what others have confirmed

If a concept is a minimal (SOV, world) pair, then bootstrapping a mind is giving it a
set of pairs to start with. The mind receives them as told knowledge — funded at half
weight, each a structure it hasn't lived through. Its open slots pull for the evidence
that would make them its own.

A told pair at half weight, once tested and confirmed by the mind's own experience,
becomes a lived pair at full weight. From that point it's a foundation, not a hypothesis.
The mind builds on it — new constraints reference it, sub-wants use it, recall by shape
matches against it. And every pair confirmed becomes the ground the next pair is tested
on: confirm the basics, then the things built on the basics confirm faster because the
foundations are already funded, and each new layer of confirmation opens the next.

This works in two modes. **Organic harvest:** run a mind, let it fund its own pairs,
seal them, transfer them to the next mind. The fiction ladder does this across scenes;
the chess app does it with self-play games. **Crafted injection:** design the pairs by
hand — a minimal force world that exhibits the concept, an SOV with the right slots —
and inject them as told knowledge. The civilization ladder calls this the curriculum:
the sequence of experiences a society constructs to fund its members' understanding.

The constraint on ordering is real. The holonomy theorem says path matters: Relabel
steps make transport path-dependent, so you can't dump all pairs in at once. But the
geodesic property says every valid curriculum is a shortest path — each step adds
exactly one concept, in an order where each is testable given what's already been
confirmed. As long as you have the right epistemic order, you can start from a
bootstrapped state, and each new mind pushes further from the last generation's
confirmed stack.

### Why it's computationally cheap

The atom is small. A stored concept is not a running simulation. It is a handful of
typed relations and a handful of force balances, sealed in a box with cooling keys.
Thousands of concepts can be stored because each is a minimal pair, and none competes
for attention until something warms its keys. The mind's energy goes to the few molecules
active in the tournament right now. Everything else is sealed. The capacity for concepts
scales with how small the pairs are. The energy cost scales with how many are active at
once. A mind that understands ten thousand concepts and attends to four of them is cheap.

### Understanding makes search unnecessary

The cost of search is not the size of the problem. It is the mind's ignorance — the
number of unfunded slots. Each failure reveals a constraint. The constraints accumulate.
When enough of them converge on one candidate, the mind doesn't search for the answer.
It notices it. A mind that understands a domain doesn't search faster. It barely searches
at all. That is what understanding is for: making search unnecessary.

### The representation problem, solved

Not by choosing between symbolic and statistical. Not by choosing between physical and
abstract. By finding the atom that underlies all of them. The minimal (SOV, world) pair
is that atom. It is small enough to store, grounded enough to mean something, structured
enough to reason about, and uniform enough to cover steam engines and trust and
reproducibility with the same machinery.

## Origin story

It all began with a question: how do higher-level thoughts form?

I thought it must be some kind of feedback loop where lower-level thoughts build on
each other. If that were so, how would such a system work? I thought there would be a
recognition module that detected higher-level thoughts, that would then feed back into
more thinking. Though that doesn't explain how the higher-level thoughts actually form.

So I turned to graphs and algebra to figure it out. Usually, knowledge is represented
hierarchically. You have topics and subtopics and so on. But what you don't know is
always waiting in the wings until someone figures it out. That doesn't serve a mind when
you want to represent understanding. To represent understanding accurately, you need both
what you know and what you don't know. But the question is, how do you know what you
don't know? And maybe that's the wrong question to ask, because maybe you don't need to
know per se. You just need to know how it relates to what you do know, or what facts or
understandings point to what it might be. This means representing understanding can't
just be a hierarchy. It must be a graph.

But where does algebra fit in? Classically, algebra is made up of equations with knowns
and unknowns. You don't hide the unknowns or pretend they don't exist. You understand
the unknowns based on how you rearrange the equations and how they relate to the known
numbers through the operators. Therefore, a graph with both known and unknown concepts
with typed relations can become its own algebra and can be formalized as such.

This represents your understanding. It then becomes the source of higher-level thinking
because the concepts themselves can be at any level.

An unknown in the graph becomes a pull that potentially generates a higher-level thought.
Then the question becomes how do thoughts become conscious and get your attention. There
is only limited attention as to not be overwhelming. That's where I turned to chemistry.

If only a certain number of thoughts get your attention, that points to some kind of
tournament structure. But how do thoughts win? They need partners. What do partners do?
They bond. So thoughts might behave as molecules that bind with other molecules to help
them win the tournament and get conscious attention. So, in this theory, consciousness
isn't some mysticism, but is just related to thought molecules winning their tournament
and getting the attention they deserve.

## The answer

It turned out to be the wrong question. "How do higher-level thoughts form?" assumes
something builds them — some mechanism that takes lower-level pieces and assembles them
into a higher-level thing. Nothing forms them. Understanding is the substrate, not
thoughts. You build understanding from experience: each interaction with the world funds
a relation, fills a slot, reveals a condition. When enough funded (SOV, world) pairs are
active in the tournament at once, and their open slots point at each other, they bond.
The composite that emerges is the higher-level thought. It wasn't constructed. It was
noticed — because the conditions converged and only one thing satisfied all of them.

You don't build higher-level thoughts from lower-level ones by aggregation. You build
understanding from experience, and the higher-level thoughts emerge from that
understanding the way solutions emerge from a well-constrained algebra. Not searched for.
Noticed.

The question contained a hidden assumption — that thoughts are the primary thing and
understanding is derived from them. It's the other way around. Understanding is the
substrate. Thoughts are what surface when the substrate is rich enough.

## Artificial Understanding

Artificial Understanding would have asked different questions from the start. Not "how
do we get the system to produce the right output" but "how does a mind come to know what
it knows, and what does knowing actually consist of." Not behavior as the target but the
generative capacity behind behavior as the target.

And the field would have arrived at unknowns much sooner. Because understanding — real
understanding — is defined as much by what you don't know as what you do. A mind that
only represents what it knows isn't understanding anything. It's just storing. The
unknown node isn't a deficiency to be patched. It's the engine.

Turing asked "can machines think." That framed everything that followed around behavior
— the imitation game, the behavioral test. The question should have been "can machines
understand." That's a different question entirely. It points straight at structure,
grounding, provenance, the (SOV, world) pair.

Intelligence is a benchmark that can be gamed. Understanding cannot.

Gerundelle is the answer to the question the field forgot to ask.

### Grounded Semantic AI

Statistical AI: semantics as co-occurrence. The meaning is in the geometry of the vector
space. Ungrounded — no world, just text about the world.

Symbolic AI: semantics as formal relations between symbols. Structural but ungrounded.
The symbols point at each other, not at anything outside the system.

Grounded Semantic AI: semantics as the minimal (SOV, world) pair. The symbol points at a
force world where something actually happens. The grounding is real, checkable,
structural. The meaning isn't derived from other symbols or from co-occurrence. It's
anchored in a world that exhibits the phenomenon.

"Grounded" has a history in the field — the symbol grounding problem (Harnad, 1990).
Harnad asked how symbols get their meaning, argued that you can't ground symbols in other
symbols, and proposed sensorimotor grounding as the answer. He was pointing at the world
half without having the algebra to formalize it. Grounded Semantic AI is the answer to
Harnad's question. Not sensorimotor grounding — that's too biological, too narrow. Force
world grounding. The (SOV, world) pair as the atom.

### The two contributions

**The unknown as a first-class citizen.** Every prior architecture treats the unknown as
a temporary embarrassment — something to be eliminated as fast as possible. A gap in the
data, a missing variable, a probability waiting to collapse. In Gerundelle, the unknown
is permanent, structural, algebraically active. It has identity. It pulls. It
participates. It doesn't exist to be resolved — it exists to be productive while
unresolved. That's a fundamental shift in what a knowledge representation even is.

**Understanding as a first-class citizen, distinguished from both thinking and behavior.**
The entire field aimed at behavior because that was the only target they could see.
Thinking was the mechanism, behavior was the measure, and understanding was either
mystical or reducible to the other two. Gerundelle gives understanding its own structure.
The minimal (SOV, world) pair is not a description of behavior. It's not a description
of the tournament. It's the atom of what it means to know something. No prior cognitive
architecture has formalized understanding as a first-class object distinct from both
thinking and behavior.

The two contributions need each other. Understanding requires the unknown as a
first-class citizen — because real understanding is defined as much by structured
ignorance as by funded knowledge. A mind that only represents what it knows isn't
understanding anything. And the unknown only becomes productive when it's embedded in an
understanding structure — typed relations, funded neighbors, a world that gives it
grounding. One without the other is incomplete. Together they're the foundation.

### Aristotle's nous is now a Lean type

Aristotle said understanding was a real thing, distinct from behavior — nous, the direct
grasp of what something is and why. For 2,400 years it stayed philosophical. The
behaviorists dismissed it as mentalism. The AI field operationalized it away: if the
output looks right, the rest doesn't matter.

The (SOV, world) pair formalizes it. Understanding is a graph of funded relations
anchored in a force world, with typed unknowns that pull. It has 301 machine-checked
theorems. It is the least mystical thing anyone has said about understanding — because
it says exactly what understanding is, structurally, and proves properties about it for
every possible input.

Aristotle was right that understanding is real and distinct. He just didn't have Lean 4.

### Nous-Orexis-Entelechy Formalization

Aristotle didn't just say understanding grasps things. He connected it to orexis —
desire, striving, the pull toward completion. Things move toward their form the way an
unknown strains toward its resolution.

The architecture formalizes three connected Aristotelian ideas at once:

- **Nous** (understanding as direct grasp): the minimal (SOV, world) pair. An unknown
  defined by its relations to what is known. When the constraints converge and only one
  thing fits, the mind grasps it directly — not by searching, by noticing.
- **Orexis** (desire as structural pull toward completion): the open-site tension in the
  tournament formula. A constant, non-decaying pull, every tick, until the slot closes.
  The unknown literally pulls, in a way that can be measured and proved.
- **Entelechy** (the extinguishing of potential once realized): the moment the slot
  closes, the tension goes to zero. The unknown no longer bids. The yearning
  extinguishes itself by being fulfilled. The acorn doesn't strive once it's an oak.

### Next token prediction vs structural similarity: an example

I was thinking about the minimal (SOV, world) pair for representing the concept of an 
"anti-pattern." An anti-pattern is something that looks like it should work — it has 
the same surface structure as something that does work — but consistently fails 
because of a condition that isn't visible in the surface. In the architecture, it's 
one half of a split: the conflation detector fires when outcomes are bimodal, the 
boundary condition is found, and the pattern and the anti-pattern become two concepts 
where there was one.

At that point, I connected it to something from a completely different domain: using
statistical AI to achieve real understanding is itself an anti-pattern. It has the same
surface structure as understanding — it produces outputs that look like the outputs of
understanding — but the condition that makes the difference (grounded (SOV, world)
pairs, funded by lived experience, with genuine unknown nodes pulling) is missing. Same
skeleton. Missing condition. Wrong outcome.

A language model would not have produced the word "anti-pattern" there. It's not the
probable continuation after "statistical AI." The probable words are "limitation,"
"challenge," "shortcoming." "Anti-pattern" comes from software engineering. The
connection is structural, not statistical — it can only be reached by holding funded
pairs for both concepts and noticing the skeletons match.

That's the difference between next token prediction and structural similarity. A
language model predicts the next word from what came before. A mind with understanding
notices a shape across domains because the bones are the same. One clear example
understood structurally beats a million examples understood statistically.

And this example was not constructed to illustrate the point. It happened, in real time,
from the machinery working naturally. The theory predicted exactly this kind of
cross-domain connection — funded (SOV, world) pairs whose skeletons match, bonding in
the tournament and surfacing as a composite thought. Then the event happened, unrehearsed,
in the middle of exploring the theory.

## Repository structure

```
formalization/          Lean 4 proofs (24 files, 301 theorems)
  SOV/                  The SOV algebra and its layers
  lakefile.toml         Build configuration
  lean-toolchain        Lean version

paper/                  The academic paper
  gerundelle.tex        LaTeX source
  gerundelle.pdf        The paper
  refs.bib              Bibliography

book/                   The Museum of Gerundelle (the book)
  gerundelle.pdf        Print edition (262 pages)
  gerundelle.epub       EPUB edition

reference/              The reference implementation
  molecules.py          The thought-molecule tournament
  sov_agent.py          The SOV agent
  force_world.py        The force world
  curriculum_worlds.py  The curriculum

domains/                Domain-specific worlds and ladders
  fiction/              The fiction pipeline (rungs 0-7, both arms)
  cognitivecode/        The cognitive code ladder (rungs 0-8)
  cognitivechess/       The chess ladder (rungs 0-3)
  civilization/         The civilization track (rungs P0-P14)
  embodied/             Embodied cognition (distinctiveness, recognition, grasping)

puzzle-pieces/          How external concepts map onto the running system
```

## Quick start

### Check the proofs

```bash
cd formalization
lake build
```

If it compiles, every theorem holds.

### Read the book

The finished book is in `book/gerundelle.pdf` (print edition) and `book/gerundelle.epub`.

### Play the mind at chess

```bash
cd domains/cognitivechess
python -X utf8 play.py --games 10 --side white
```

A tkinter app where you play one side and a Gerundelle mind plays the other. The mind
knows nothing of chess values and does not perceive squares — it learns from contrast,
sets sub-wants, and notices where its constraints converge. While it thinks, the panel
shows what it's attending to (moves, experiments, questions, feelings), what it wants,
what it learned, and why it chose its move (planner, experiment, or the top-level winner
of its tournament). `--games N` lets it play N games against itself first, so it carries
that experience into your match. Configurable temperament: `--curiosity`, `--persistence`,
`--patience`.

### Run a domain

**Fiction** (rungs 0-7, plus 25 worlds): a mind acts in a force world, discovers how
things work by contrast, forms beliefs and retracts them, asks others for help, is lied
to and finds out, contests a rival, loses something and grieves, remembers across scenes
by structural analogy, and produces verified prose whose every sentence reads back to its
intended gerund shape. Six temperaments give different characters different stories from
the same algebra.

```bash
cd domains/fiction
python -X utf8 run_ladder.py --rung 0 --configs lean --ticks 300   # Mara and the box
python -X utf8 run_ladder.py --rung 3 --configs lean --ticks 300   # Leo lies
python -X utf8 run_ladder.py --rung 5 --configs lean --ticks 300   # loss, grief, forgiveness
python -X utf8 tools/corpus.py                                      # all 300 stories
```

**Code** (rungs 0-8): a mind produces programs through constraint discovery, not search.
Each failure reveals a constraint. By rung 7, composition combines a header from one seed
with a growth from another and produces programs search never found.

```bash
cd domains/cognitivecode
python -X utf8 rung0.py    # the color line: 66 tries blind, 3 with a recalled shape
python -X utf8 rung7.py    # composition: programs no search finds
```

**Chess** (rungs 0-3): a mind learns chess tactics from contrast, sets sub-wants to bring
about conditions it needs, notices the move where its constraints converge at the first
attempt in positions it has never seen, and plays against another Gerundelle mind that
adapts to it.

```bash
cd domains/cognitivechess
python -X utf8 rung0.py     # the hanging piece: finds the capture
python -X utf8 rung1e.py    # constraint convergence: 87 of 100 new positions at the first attempt
python -X utf8 rung3.py     # two minds on one board: White and Black adapt to each other
```

**Civilization** (rungs P0-P14): populations of minds in worlds with configurable physics.
Minds voyage between worlds, teach each other, lock resources, enclose each other's
property, feel grievance, retaliate, and feud.

```bash
cd domains/civilization
python -X utf8 p0.py     # the spring of light: one mind, one want
python -X utf8 p4.py     # a population of four: curiosity, interference, accidental help
python -X utf8 p13.py    # retaliation and the first feud
python -X utf8 p14.py    # ranges: which findings survive across turn orders
```

## The paper

**GERUNDELLE: A Formally Verified Architecture of Mind**
*Twelve Layers, from World Physics to Narrative, Machine-Checked in Lean 4*

Scott Seto. October 2026.

Three results:

1. **Every layer is verified.** From conservation of potential in the world to the
   well-foundedness of a told story.
2. **Six fields, one structure.** Information security, symmetry groups, fiber bundles,
   learning theory, graded monads, and provenance calculi — six areas of mathematics that
   rarely cite one another — describe the same architecture once stated about its operators.
3. **Seeing and feeling are one property.** Perception and affect are both factorization
   through a view. Same mathematical structure, two levels.

## The book

**The Museum of Gerundelle: A Cognitive Architecture of Competing Thought-Molecules,
Structured Ignorance, Territorial Ownership, Scarce Attention, and the Market Forces
That Drive a Mind to Learn, Explore, Grow, and Express Itself**

Scott D. Seto. 262 pages.

A computational laboratory manual, not a textbook. Each chapter follows the rhythm:
What If → Why → Possibility, with suggested experiments. Before each chapter, a dream
sequence takes the reader through one gallery of a museum where the chapter's concepts
exist as physical exhibits. The chapters name what the galleries showed.

## The domains

| Domain | What it tests | Rungs |
| --- | --- | --- |
| Fiction | A mind in a force world producing verified stories | 0-7, both arms, temperament |
| Code | A mind producing programs through constraint discovery | 0-8, composition, variation |
| Chess | A mind learning tactics from contrast and playing combinations | 0-1c, sub-wants, polarity, lookahead |
| Civilization | Populations of minds in worlds with configurable physics | P0-P5, voyages, told blueprints, populations |
| Embodied | Distinctiveness space, recognition, grasping | Recognition 28/30, constraint discovery |

## The formal guarantees

Seven theorems that prove the architecture's core promises:

1. **The imagination firewall** — nothing imagined reaches the funded web
2. **Imagined evidence is inert** — dropping imagined trials changes no owner
3. **Told evidence can't be promoted** — told-only evidence funds at most c₀ per trial
4. **Ownership is order-dependent, funding is order-free** — non-commutativity placed precisely
5. **Paradoxes are broke, not banned** — a self-citing entry is legal but unfundable
6. **Every valid curriculum is a geodesic** — each step adds exactly one concept
7. **The pull order** — lost > control > unclaimed, with the restless inversion proved

Seven lemmas that prove its boundaries:

8. **No outbound morphism exists** — funding can't be reconstructed from imagination
9. **The Lamarckian pairing is a grade error** — inherited knowledge can't be typed as lived
10. **Lived mass can't grow without a Fit** — only world interaction creates evidence
11. **Relabel is primitive** — no composite of meets produces it
12. **No global coordinates when holonomy is non-trivial** — structure is inherently local
13. **Accrual and eviction don't commute** — the precise boundary of confluence
14. **Perception is determined by invariance** — the Umwelt is the quotient by funded distinctions

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23837987.svg)](https://doi.org/10.5281/zenodo.23837987)

If you use Gerundelle in your research, please cite:

```bibtex
@software{seto2026gerundelle,
  author    = {Seto, Scott},
  title     = {Gerundelle: A Formally Verified Architecture of Mind},
  year      = {2026},
  doi       = {10.5281/zenodo.23837987},
  url       = {https://doi.org/10.5281/zenodo.23837987},
  license   = {LGPL-2.1}
}
```

## License

LGPL v2.1 (code, proofs, and reference implementation). See [LICENSE](LICENSE).

## Author

Scott Seto (ameritusweb@gmail.com)
