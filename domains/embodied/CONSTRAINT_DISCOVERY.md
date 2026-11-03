# Constraint discovery for distinctiveness finding

How a Gerundelle mind finds a distinctive solution (a grasp, a word, a design) without searching
the space of solutions: it searches for constraints, mostly through its own failures, and notices
the solution as distinctive among the failures because it is where the constraints converge.
This extends distinctiveness space (DISTINCTIVENESS_SPACE.md) from recognition to action.

## The problem: many solutions, none distinctive

There are many ways to grasp a mug: by the handle, around the body, by the rim, from above, with
the fingers through or pinching. All of them can work, and they are interchangeable. Unconstrained,
none of them is distinctive.

Apply constraints and the space collapses:

- the mug is full of hot coffee, so the fingers must not wrap the body
- it is full, so it must not tilt
- the rim is chipped, so keep clear of it
- the bottle stands to the left, so come from the right
- the hand has a certain span, so the fingers must go through the handle

Under those, perhaps one grasp survives: the handle, from the right, fingers through. It is
distinctive because it is the solution that satisfies the constraints. It is relationally unique
in context, and here the context is the constraints.

## Discovered and produced distinctiveness

The definition does not change: **distinctive is relationally unique in context.** What changes is
where the context comes from.

| | Discovered | Produced |
| --- | --- | --- |
| What is distinctive | a mark, an object | a solution |
| The context | given by the world: these mugs, this genre | built by the mind: the constraints found |
| Unique among | the other things present | the other attempts, mostly failures |
| Example | the chipped diner mug among three diner mugs | the grasp through the handle from the right |

Recognition is the same map read backwards. An object's distinctiveness signature is the smallest
set of constraints that points to it and to nothing else among these objects ("the diner mug,
chipped, stained"). Minimum resolution that still tells it apart is the fewest constraints that
still single it out.

## Constraint search, not solution search

This is not constraint satisfaction and it is not solution search. The mind does not compute a
grasp in advance. It attempts, and most attempts fail. Among the failures, one attempt stands out:
the one where the constraints converge. It is **noticed** as distinctive among the failures, the
way a chip on a rim is noticed. It is not computed.

What is searched is constraints. That is why it is tractable:

- the solution space (every grasp, every word, every design) is enormous, practically unbounded
- the constraints that matter are few

The mind never works through the space of solutions. It looks for which constraints matter. A
search over constraints can end in one solution (distinctive), several (under-constrained) or none
(over-constrained), and in every case it got there without enumerating the solution space.

## Failures are constraint revelations

In the paradigm Gerundelle departs from (deep learning at scale, transformers, and reinforcement
learning on top of them, roughly 2017 on), failure is always a negative signal: a loss to minimize,
a negative reward, a dispreferred sample. The system learns by reducing failure.

In Gerundelle, failures are **constraint revelations**. Each one is informative not because it
says what not to do, but because it exposes a constraint not yet found:

| Failure | Constraint revealed |
| --- | --- |
| the burn when the fingers wrapped the body | the body is hot |
| the knocked bottle | the bottle stands to the left |
| the spill | it is full: it must not tilt |
| the cut lip | the rim is chipped |
| the pinch that slipped | the hand's span: the fingers must go through |

Failures are not the opposite of success. They are the raw material that makes success
recognizable, and enough of them are needed to triangulate the convergence. So the aim is not to
minimize failures but to extract constraints from them efficiently. A failure that reveals a new
constraint is worth more than a success that confirms what was already known.

**The most informative failure is a near miss**: one that differs from the success in a single
respect, which isolates one constraint cleanly. A flail tangles several constraints together.
Experts fail informatively. Their failures are near misses, almost deliberate, each probing one
constraint at a time: boundary-testing.

Failed attempts are **territorial probes**. The world pushes back, and that resistance is a
constraint being revealed. The agent is not being defeated; it is reading the shape of the
territory through what blocks it. The whole system is built not to avoid resistance but to extract
the most constraint information from it.

## Noticing: convergence as simultaneous binding

Mechanically, the convergence is a binding event. Each constraint is a molecule with a standing
open site: what meeting it looks like. Each attempt is a molecule carrying what it met. An attempt
that meets a constraint fills that constraint's site.

When enough constraints are found, one attempt fills all of their sites at once. Its support is
the number of constraints bound to it simultaneously, and that support enters its bid. It wins
not by being loud but by being **multiply supported**. Noticing is that attempt winning.

Two details matter, and both were found by trying them (see the experiment below).

- **Simultaneous binding is in superposition.** If each constraint first resolves to a single
  attempt by argmax, a constraint that several attempts satisfy picks one of them arbitrarily, and
  support scatters. The convergence then goes to the wrong grasp. Support has to count every
  constraint an attempt could fill, the candidate bindings, before each constraint settles on one.
- **A constraint stands.** In Gerundelle an open site closes once it is filled. A constraint must
  not: every attempt is held against it, so meeting it once does not close it.

Support is recomputed every tick from the constraints present and never accumulated, so it lasts
only as long as the constraints do. This guards against the lock-in of Gerundelle's first prototype
(chapter 4), where attraction fed on itself.

## Where constraints anchor, and where resolution goes

A constraint needs something distinctive to anchor on: the handle's gap, the chip, the bottle's
edge, the level of the coffee. These are **funded distinctive marks**: regions where the field has
resolution because interaction has funded them. A coarse, unfunded region cannot hold a constraint,
because there is nothing specific enough to attach it to.

This fixes the bootstrapping order. At first everything is coarse. A failure's surprise escalates
resolution where it happened, which gives the constraint its anchor. After that, resolution goes
only to what the constraints touch. Most of every attempt (the arm extending, the table, the light)
is the same in success and failure, and it stays coarse.

## Over-constraint: the dropped constraint is the confession

When nothing survives the intersection (the mug is hot, the handle is chipped, the bottle blocks
the other side), the system does not fail. It negotiates. Territory decides which constraint to
drop, so the negotiation is not arbitrary: the agent drops the constraint protecting the least
held ground first. Not spilling on the book outranks not using the chipped handle.

Over-constraint therefore reveals value structure. You cannot see what an agent truly holds until
something has to give: the dropped constraint is the confession. Two agents over-constrained
together must negotiate whose territorial claims outrank whose. Not spilling on the book beats not
using the chipped handle, but whose book?

## Under-constraint: style

Constraints rarely collapse to exactly one solution. Usually a small set of equivalent solutions
remains, and something has to break the tie. **Style is the distinctiveness signature of
tie-breaking, across a lifetime of under-constrained solutions.** This mind always reaches through
the handle; this writer always chooses the shorter word; this architect always lets go the
constraint that touches light rather than structure.

Style is more revealing than the constrained choices, because those were forced. The tie-breaking
is where the agent's particular graph shows through most purely, which is where temperament (the
SOV parameters) shows. For fiction: Gerundelle picks the word that survives the constraints, and in
the remaining tie-space the character decides. That is the difference between competent writing
and a voice.

## Two orderings

Expertise is knowing which constraints to apply first. There are two different orderings, and they
should not be merged.

- **Cut order**: which constraint to apply first to collapse the space cheaply. The one that rules
  out the most attempts goes first. It is learned from failures: how many failures each constraint
  explained. It decides how much work the search takes, not where it ends, as long as the
  constraints are consistent.
- **Stakes order**: which constraint to keep when over-constrained. Territory sets it: a
  constraint protecting held ground outranks one protecting nothing. Under over-constraint, it
  decides where the search ends.

The highest-stakes constraint is not always the one that cuts the most.

## Moving the hand: resonance warming and cooling

Once a success signature is stored, it guides the reach. As the hand moves, the current
configuration either resonates more with the stored signature or less: the signature warms or
cools. The action taken is the one that warmed it. Opening, closing, turning and approaching are
told apart by which one moves the configuration toward the convergence. There are no coordinates
and no measured distance.

Two things qualify this.

- It is not a gradient computed in advance. Each step is tried, and the warming or cooling that
  follows is the feedback.
- The very first reach has no stored signature to follow. It runs on the want's bond
  strengthening as the gerund regions between hand and object thin (EMBODIED_COGNITION.md). It is
  that first reach, and the failures it produces, that start the constraint search.

## In Gerundelle's terms

Almost all of this is machinery Gerundelle already has, applied to a new purpose.

| Here | In Gerundelle |
| --- | --- |
| a constraint | a **conditions** slot (a conflation split adds a boundary condition) |
| a failed attempt | a claim that did not take: a control slot opens, "what blocks it?" |
| searching for constraints | "what blocks it?" pays for a conditions question; Inquiry suggests experiments to answer it |
| an attempt meeting a constraint | the attempt filling the constraint's open site |
| noticing the convergence | the multiply supported attempt winning the top |
| the stored success signature | a box keyed by the convergent constraints |
| the next time | resonance: enough of its keys warm among the winners, and it reopens |
| what to drop when over-constrained | territory's pull order |
| breaking ties | temperament |

"What blocks it?" → conditions question → Inquiry is constraint search under another name. Every
step in that chain searches for a constraint, never for a solution. Distinctiveness says what the
chain is for: finding the convergence that singles out the distinctive solution.

## Built and proposed

The epistemic contract: what is built and measured is kept apart from what is proposed.

**Built** (on a copy of Gerundelle in `embodied/gerundelle/`; the original in `E:\vscode\analogy` is
untouched):

- `Mind.think` resolves every binding first and bids after, so support can be counted. Without
  constraint molecules this changes nothing. Checked: Gerundelle's suite on the unmodified copy and
  on the changed copy both give 72/80 with 2 pending, the same tests failing, and identical metrics
  except timing and one seed of T60 (pending). T60's first seed was then run alone on the original
  and on the changed copy under fixed hash seeds 0, 1 and 2: identical in each. It passes or fails
  with Python's hash randomization in Gerundelle itself (a nondeterminism that was already there),
  not with this change.
- `Mind.support`: constraint molecules (tagged `constraint`) bound to a molecule at once add to its
  bid, `w_support × T` apiece, in two modes: `resolved` (the bindings that resolved onto it) and
  `candidates` (every constraint it could fill, in superposition). `Params.support` is `None` by
  default: Gerundelle as it was.
- Constraint molecules keep their sites when filled.

**The experiment** (`embodied/grasp_convergence.py`): five lived attempts at the mug, each tagged
with the constraints it happened to clear; the five constraints revealed one at a time, as the
failures revealed them.

| constraints revealed | support off | resolved bindings | candidate bindings |
| --- | --- | --- | --- |
| 0 | all tied | all tied | all tied |
| 1 (hot) | four tied | arbitrary leader | four tied |
| 2 (+ bottle) | two tied | converged | two tied |
| 3 (+ spill) | all tied | wrong leader | **converged** |
| 4 (+ chip) | two tied | converged | **converged** |
| 5 (+ span) | all tied | wrong leader | **converged** |
| over-constrained (+ dry, which nothing clears) | | wrong leader | **converged** on the attempt clearing the most |

- With candidate support, from the third constraint on, the grasp they converge on (handle, from
  the right, fingers through) leads and stays ahead.
- With resolved support, the scattering is as predicted. At five constraints it leads with the
  grasp that burns the fingers.
- With no support, the attempts tie and nothing is noticed.

The first run found that constraint sites closed on the first tick and the constraints bound to
nothing after. That is why constraints now stand.

**Caveats, stated plainly**:

- The attempts are hand-tagged with what each cleared. In the real version each failure in the
  scene must reveal its constraint.
- The margin is small: the convergent grasp leads by exactly one constraint's worth of support.
  With four top slots it shares the top with other attempts. It leads; it does not yet stand alone.
- Over-constraint is resolved here by count (the attempt clearing the most), not yet by territory's
  stakes order.

**The hand in the scene** (`body/world.py`, `body/grasp.py`; 2026-10-28). The table scene with the oil bottle set
right beside the chipped mug, on the side away from its handle (`?layout=200`). The mug is full of hot coffee and the
mind wants to hold it. The hand reaches by the tournament: the want binds to a move, the move it binds to is made,
and the outcome (the regions between hand and goal thinned or thickened) is credited to that move's record with the
want. The hand's repertoire for a mug is a side to come from (left, right, near), a part to take (handle, rim,
body) and a grip (hook, pinch, wrap). Each failure reveals a constraint anchored on where it happened; the next
attempt is the untried one the constraints found so far support most (candidate support).

| attempt | what happened | constraint found |
| --- | --- | --- |
| 1. from the left, the body, hooked | the bottle knocked tipping (geometry: the hand ran into it coming down) | something in the way on the left |
| 2. from the near side, the body, hooked | burning | the body is hot |
| 3. from the near side, the handle, hooked | the fingers meet the handle edge-on | come from the handle's side |
| 4. from the near side, the rim, hooked | cutting on the chip | the chip is on the near side |
| 5. from the right, the handle, hooked | **held** | |

Four failures, four constraints: one per failure. The constraints converged before the rim's spill or a pinch's
slip were ever met, so those were never needed. A second episode, starting with the four constraints, held the mug
on its first attempt. Replays: `scene/?layout=200&replay=hand_ep1_05` (frames with `&frame=k`).

What it took, each a failure first:
- The moves are invitations perceived anew each tick (their site reopened). Kept as they were, the want filled
  them once and nothing bound after. Removed and presented again, Gerundelle's re-entry boost kept the first
  winners winning.
- The outcome is credited only to the move made. Credited to every winning move bound to the want, as `learn`
  does, nothing learned.
- The move made is the one the want binds to (its pull flows through that bond). Taking the first of the top
  winners, four moves tied at the top and broke by name.
- A move's identity includes how it lies to the mug as seen, toward or away (the force world's rule: the
  configuration is part of what invites), and a move toward invites by how much of the way lies along it.
  Without these, the hand went on past the mug on a good record, or rocked level with it and never tried the way
  still open.
- The regions between are half a centimetre (there is no air in the field, so this is close to distance in fine
  units). At 4 cm, half the steps changed nothing the hand could feel.

Plainly, the limits:
- The reach leans on seeing which way the mug lies. The learning does little there, beyond pushing down a move
  that stopped working.
- The grasp's rules, the loci of the events, and the mind's reading of its own action (which parts an attempt
  would touch: `involves`) are written by hand. The constraint for the chip comes from the world's event, not
  yet from the octree's chip mark under the fingers.
- Ties between equally supported attempts break by name. The first attempt (from the left, the body, hooked) was
  that order's luck. There is no style yet: no temperament breaks the ties.
- The constraints are about this mug where it stands. "Come from the handle's side" is stored as "from the right"
  and will not carry to a mug turned the other way. (Fixed since: see the next part.)

**Constraints that transfer** (`body/perceive.py`; 2026-10-28). A constraint is now anchored on what the mind
perceived doing it, a relation it reads again in each new scene from the octree's things and marks (never the
answer key), rather than on the side the body saw it from:

| failure | fixed anchor (first) | relational anchor |
| --- | --- | --- |
| a thing knocked tipping | not from the left | **keep clear of anything lying between the hand and where it reaches** (the field's regions between) |
| fingers against the handle edge-on | not the handle from the near side | **the handle only from the side it faces** |
| cut on the chip | not the rim from the near side | **not the rim on the side where a distinctive mark lay under the fingers** (the octree's chip mark) |
| burning, spilling, slipping | the body, the rim, two fingers on the handle | the same: relational already |

The mind's perception of each new mug (which way its handle points, where its rim's mark is, what lies in the way
to each side) matched the answer key in all three tasks, and its prediction of what lies in the way matched the
actual knocks on every side of every task (12 of 12). My first relational reading of a knock, "not from a side
where something stands close", was wrong: sent to the far side of the turned mug, the hand knocked a bottle that
stood on the right four times running. The bottle had not stood beside where it came from; it lay across the way
there.

The test: learn on task 200 (the chipped mug as it stands), then start two new tasks with what was learned: 201,
the same mug turned (handle and chip another way, the bottle beside it on the other side), and 202, the
"Lakeside Diner" mug (no chip, the bottle in front of it). Ties between equally supported attempts break by a
random order; 20 orders, stand-ins for 20 styles (first one order, by name, and its luck was taken for a result).

| attempts to the first hold | learning (200) | constraints learned | the same mug turned (201) | another mug (202) |
| --- | --- | --- | --- | --- |
| fixed constraints | 4.3 (worst 8) | 3.4 | 5.0 (worst 9) | 2.5 (worst 6) |
| relational constraints | 4.0 (worst 6) | 3.0 | **2.1 (worst 4)** | **1.8 (worst 5)** |

Fixed constraints mislead: "not from the left", learned where the bottle stood on the left, pointed the hand away
from the turned mug, whose handle now faced left. Relational ones are not always enough on their own: when
learning never met a failure (on task 200 a hand from the far side takes the handle, so "the handle only from the
side it faces" may never be learned), the new task has to find it, and does.

**Constraints from perception** (the user, 2026-10-28: have them come from what the mind perceives, not from
hand-written rules). Two things were still hand-written on the mind's side: which relation a failure becomes
(`anchor_of`), and which parts an attempt would involve (`involves`). Both are now perception (`grasp.py`:
`perceived`, `constraints_from`; `perceive.py`: `touch_tags`, `predict`):

- Every attempt is perceived as tags read from the octree: what the fingers met (the cells under them: where on
  the mug, which way they face, whether they stand out beyond the body, whether a distinctive mark is among
  them, and what the hand mostly holds), whether something lay in the way (the field's regions between), how
  the approach lay to what the mug shows (along the way its out-standing part faces, across, against; toward
  its mark or not), and the grip (the body knows its own hand).
- A failure's constraint is what is distinctive of it among the attempts: the smallest combination of its tags
  that no other attempt carried in full, the tags commonest elsewhere released first (a profile compressed).
  Failures of one kind are merged into what they share while that still tells them apart; where it cannot,
  the kind keeps more than one constraint (one label, two situations: the meta layer's conflation, split).
- Before acting, the mind predicts an untried attempt's tags from the mug as it sees it (where its fingers would
  go, what cells they would meet). An attempt runs into a constraint if it would carry all of it.

| attempts to the first hold (20 tie orders) | learning (200) | the same mug turned (201) | another mug (202) |
| --- | --- | --- | --- |
| hand-written, fixed sides | 4.0 | 4.9 (worst 9) | 2.4 (worst 6) |
| hand-written, relational | 4.0 | 2.1 (worst 4) | 1.8 (worst 5) |
| **from perception** | 10.1 (worst 29) | **1.8 (worst 4)** | **2.1 (worst 4)** |

What it found for itself, in one run: what knocks things over is `way:crosses` (something in the way); what
slips is `grip:pinch touch:stands-out` (a pinch on what stands out); what spills is holding the rim; what burns
is a wrap or holding the body (four combinations, one of them a coincidence: `came:with-mark`, the near body
pinch that burned happened to come toward the chip; more attempts would prune it). With these it held the turned
mug and the other mug on the first attempt.

Each step, a failure first:
- Tag by tag (keep what no other attempt had), the burn, whose contact with the body at mid height also occurred
  in rim grips that did not burn, was left as "the way is clear": nonsense. The smallest distinguishing
  combination fixed the slip.
- The burn still had none: a hook through the handle also brushes the body where the handle joins. What the hand
  mostly holds tells them apart.
- It still had none: the burn has two causes that share nothing (a hand wrapped round the handle; a hand on the
  body). Splitting it into more than one constraint fixed it.
- One body grip perceived nothing: I had put the fingers for it 1.8 cm off the body, in the world and in the
  mind's plan (my bug; now 8 mm).
- The world's cut was a 60-degree cone round the chip, broader than a hand; it is now geometric (the chip under
  the fingers' contact), with the same hand the mind perceives with.

Learning is slower (10.1 attempts, against 4.0), as it should be: it finds for itself what I had told it.
Still hand-written: the world's rules (its physics), and the vocabulary of what can be perceived (the tags).

**Tags minted by perception itself** (the user, 2026-10-28: let perception choose its own tags). The mind starts
with no tags but its grips (the body's own action). An attempt is perceived as raw quantities read off the octree,
no categories: of the cells under the fingers (area-weighted mean, extremes) their height on the mug and distance
from its axis as shares of the mug's, which way they face, lightness, texture spread, distinctiveness, how much was
touched; the approach's cosine to where the fingers went and to each of the mug's marks; how much of other things
lay in the way. When a failure cannot be told apart from an attempt that did not fail that way, the mind mints a
tag: the one quantity and cut-off that separates it from the most of those it collides with, keeps the most
failures of its kind with it, and cuts with the widest margin for that quantity (escalation on collision:
resolution only where two collide; the meta layer's split, applied to perception). Constraints are found over the
minted tags as before (`grasp.py`: `Vocabulary`, `episode_minted`; `perceive.py`: `raw`, `predict_raw`).

| attempts to the first hold (20 tie orders) | learning (200) | the same mug turned (201) | another mug (202) |
| --- | --- | --- | --- |
| hand-written, fixed sides | 4.0 | 4.9 (worst 9) | 2.4 (worst 6) |
| hand-written, relational | 4.0 | 2.1 (worst 4) | 1.8 (worst 5) |
| perceived, hand-written vocabulary | 10.1 | 1.8 (worst 4) | 2.1 (worst 4) |
| perceived, tags minted by need | 10.8 | 3.4 (worst 18) | 3.8 (worst 34) |

What it minted for itself, in good runs: `in_way > 9.6` for what knocks things over (a lot lies in the way);
for the burn, a wrap, or the outward-facing surface below 0.7 of the height (the body); in another run,
`distinct_max > 139` for the cut, a highly distinctive mark under the fingers (the chip, found through the
octree's distinctiveness, with no tag naming it). With these it held both new mugs on the first attempt.

Failures first: choosing the cut-off between the two closest values minted coincidences ("came straight at a mark"
for the knock; transfer 5.4 and 9.4); the widest margin for the quantity fixed most of it.

Where it stands, plainly. The averages are behind the hand-written vocabulary, and the worst cases are bad. Two
causes: a learning episode that succeeds early by luck mints nothing and leaves almost nothing to transfer, so the
new task is learning from scratch; and learning from scratch with minted tags is slow and noisy, minting
coincidences from few examples (both directions of a cut are sometimes minted; some constraints stay
over-specific). Candidates: trust a minted tag only once a second failure bears it out; mint on the nearest miss
(the most similar colliding attempt) so one quantity is isolated; let minted tags that never earn a receipt fade.

**The nearest miss, tried** (`Vocabulary(mode="nearmiss")`). The cut is minted against the colliding attempt
most like the failure in everything perceived (each quantity as a share of how much it varies), on the quantity
where the two differ most, half way between them. It did worse:

| tags minted by | learning (200) | the same mug turned (201) | another mug (202) |
| --- | --- | --- | --- |
| the widest margin (the default) | 10.8 | 3.4 (worst 18) | 3.8 (worst 34) |
| the nearest miss | 10.7 | 5.0 (worst 22) | 6.7 (worst 24) |

Why: a near miss has to be near. The attempts the mind chooses (by constraint support) change side, part and
grip at once, so the nearest colliding attempt is still far, and the quantity where they differ most is arbitrary
("low distinctiveness under the fingers" for what spills). Winston's near misses worked because a teacher built
them to differ in one respect. Here no one builds them. The principle stands; the mind has to **make** its near
misses: after a failure, try an attempt that changes one thing (the side, or the part, or the grip), the failure
made informative on purpose, as experts fail (and Gerundelle's Inquiry: change one thing first, then do it).

**Deliberate near misses** (`episode_probing`, `Vocabulary(mode="probe")`). After a failure the mind did not see
coming (the first of its kind, or one its constraints said the attempt would clear), its next attempts are
probes: the failed attempt with one thing changed (the side, or the part, or the grip), the one of those its
constraints support most. A probe that fails the same way says the thing changed was not the cause, and the next
probe changes another thing in the original, each at most once; a probe that does not fail that way is the near
miss. The near miss narrows the cause to the quantities that changed between the two; the widest margin over every
attempt chooses among them.

| tags minted by | learning (200) | the same mug turned (201) | another mug (202) |
| --- | --- | --- | --- |
| the widest margin | 10.8 (worst 28) | 3.4 (worst 18) | 3.8 (worst 34) |
| the nearest miss among attempts made | 10.7 (worst 32) | 5.0 (worst 22) | 6.7 (worst 24) |
| **deliberate near misses, the margin choosing** | **7.5** (worst 30) | **3.5 (worst 9)** | **4.0 (worst 16)** |

What it minted, in the run shown: what knocks things over, `in_way > 9.6` (a lot lies in the way); what spills,
`height_mean > 0.735` (holding high: the rim); what burns, `height_mean < 0.735` coming straight at what is touched
(the body), or a wrap; what slips, a pinch coming across what it touches. The real causes, each found through
quantities read off the octree, none named by me.

Each step a failure first:
- Each probe changed whatever its support favoured: after a knock from the left, the hand changed its grip three
  times running, knocking each time (transfer 4.7 and 8.4). Probes now work through the side, the part and the
  grip of the original failure, each once.
- The near miss alone chose the quantity that changed most between the failure and its probe: learning fell to
  7.8, but transfer was 6.0 and 7.2. One change in the action is not one change in what is perceived: moving the
  hand to another side changes at once what lies in the way, how it faces the chip's mark and how it faces what it
  touches, and "came straight at a mark" was minted for the knock (in the learning scene the left side happens to
  face a mark). The near miss isolates the action, not the cause. So the near miss narrows to what changed, and
  the other attempts, through the margin, tell those quantities apart.

Where it stands: the best of the perception-only ways to learn (7.5 attempts, against 4.0 for my hand-written
anchors), transferring about as well on average as the widest margin and with its worst cases halved; still
behind the hand-written vocabulary in transfer (1.8 and 2.1). Both directions of a cut are still minted (one is
idle), and a learning episode that holds early still leaves little to transfer.

**Where transfer loses attempts** (`body/diagnose_transfer.py`). In a new task a failure is either of a kind never
met in learning (unavoidable by what was learned) or of a learned kind the constraints did not foresee (a transfer
failure). Minted tags with probes, over 20 orders: 63 of the first, 47 of the second (burns 26, spills 12); the
hand-written vocabulary: 19 and 18. Probing learns fast partly by meeting fewer kinds. The missed burns were of two
opposite faults, constraints too broad ("anything pinched burns") and too narrow ("only a wrap burns").

Tried and reverted, with what each showed:
- Probes skipping variants already expected to fail another known way (kept: principled, though the difference
  is within noise).
- Minting on perception alone (the grip set aside when testing a collision) and releasing the grip first when
  compressing, so constraints are about the world: worse, 7.0 and 8.4 to transfer, and the hand-written
  vocabulary worse too. In this world a wrap burns wherever it grips: the grip is part of the cause. Forced to
  find a perceived one, the mind minted a coincidence ("a highly distinctive cell under the fingers"). My
  diagnosis was wrong; the real miss (a hooked hand on the body) is a second cause learning never met.

**Learning across more than one mug** (`body/leave_one_out.py`). Learn on two of the three tasks in turn, then
take the third, held out; each held out once; 20 orders.

| attempts to the first hold on the held-out mug | the chipped mug | it turned | the diner mug | all |
| --- | --- | --- | --- | --- |
| hand-written, relational | 1.1 | 1.6 | 1.4 | 1.33 |
| perceived, hand-written vocabulary | 2.1 | 1.4 | 2.1 | 1.88 |
| perceived, minted (widest margin) | 4.0 (worst 18) | 2.5 (worst 12) | 2.1 (worst 10) | 2.88 |
| perceived, minted (deliberate near misses) | 2.9 | 4.8 | 3.5 | 3.72 |
| **perceived, minted (widest margin), constraints weighed by receipts** | **2.5 (worst 11)** | **2.5 (worst 8)** | **1.8 (worst 5)** | **2.27** |

With more experience the widest margin overtakes the near misses (probes help a single mug, not more). The worst
cases came from a wrong constraint never tested: a coincidence forbids the attempts it covers, the mind avoids
them, and the coincidence is never caught even when it forbids the answer. So a constraint now weighs by its
receipts, the failures it accounts for (presented at 1 - 1/2^n; `Mind.support`, candidates mode, sums each
constraint's activation instead of counting it 1): a single coincidence weighs half what a cause met again and
again does. Within 0.4 of the hand-written vocabulary, worst cases a third of what they were. The price, on a
single mug from nothing: learning is slower (13.4 attempts with the widest margin, against 10.8), as a constraint
seen once is weak and the mind takes more risks early.

**New mugs, and what they exposed** (`body/new_mugs.py`; tasks 203 the new diner mug with its handle toward the near
side, 204 the stoneware mug (wider, thicker, uneven) toward the far side, 205 the blue mug toward the right; the
bottle beside each on the side away from its handle). Learn on the three first tasks, take each new mug.

| attempts to the first hold | new diner | stoneware | blue | all |
| --- | --- | --- | --- | --- |
| hand-written, relational | 1.2 | 1.0 | 1.2 | 1.15 |
| perceived, hand-written vocabulary | 1.4 | 1.1 | 1.4 | 1.30 |
| perceived, minted, as it was | 1.9 | 2.6 | **11.7 (worst 30)** | 5.37 |
| perceived, minted, margins on each quantity's own scale | 2.2 | 5.2 | 3.4 | 3.63 |
| perceived, minted (near misses), the same | 2.4 | 2.6 | 3.2 | 2.75 |

What each failure showed:
- My first three new mugs were turned by offsets and all happened to face left, the bottle on the right: one
  arrangement, not a test of others. Now they face three ways.
- On the blue mug the hand burned again and again: the burn had been minted as "outward-facing cells above
  0.985". Every mug learned on had straight diner walls; within the narrow spread their cells showed (0.98 to
  1.0), 0.985 looked like a wide margin. On a cosine's own scale it is nothing, and the flared blue mug fell under
  it. Margins are now measured on each quantity's own scale (`perceive.SCALE`: what the measurement can range
  over, an instrument's scale, not a category).
- On the stoneware mug the hand knocked the bottle seventeen times running: the mind predicted what lay in its way
  along a straight line, and its hand moves step by step along the longest part of the gap first. Now it imagines
  its reach as it moves (`imagined_path`) and measures what lay along the path its hand took; the imagined path
  foresees every knock, on every side of every task (24 of 24).
- "Cutting" was foreseen for every hook on the stoneware mug: its whole body is one distinctive mark among diner
  mugs, and the chip had been learned as "something highly distinctive under the fingers". Measured against the
  mug's own usual, or against a ring round the touch, the chip stopped standing out; the area of the mark under the
  fingers (a chip is a speck, the stoneware's body one mark) made the new mugs worse (4.35). All removed.
- Storing each cut once and tagging both its sides on every attempt (to end "idle" opposite cuts): worse, 3.88
  across held-out mugs against 2.27. The opposite side is minted only when a failure needs it; tagged always, it
  gave the constraints coincidences to compress onto. Reverted.

The lesson was not another quantity. Every mug learned on was a white diner mug (two of them the same mug), so
every cut was calibrated to white diner mugs, and nothing in that experience could refute it.

**Varied experience** (`body/leave_one_out.py 200 201 202 203 204 205`): learn on five of the six tasks, take the
sixth; each held out once; 20 orders.

| attempts to the first hold | chipped | turned | diner | new diner | stoneware | blue | all |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hand-written, relational | 1.0 | 1.1 | 1.0 | 1.1 | 1.0 | 1.0 | 1.02 |
| perceived, hand-written vocabulary | 1.8 | 1.2 | 1.1 | 1.1 | 1.1 | 1.2 | 1.24 |
| perceived, minted (widest margin) | 1.4 | 2.3 | 2.2 | 1.6 | 2.1 | 1.9 | 1.93 |
| perceived, minted (near misses) | 1.9 | 1.9 | 2.1 | 2.2 | 1.9 | 1.4 | 1.90 (worst 6) |

With mugs of different shapes and colours in its experience, a mind that mints its own tags from raw perception
takes about two attempts to hold a mug it has never handled: the stoneware and the blue mug, which cost 5 to 12
attempts when learning had seen only white diner mugs, now cost about 2. The hand-written vocabulary still takes
fewer (1.24), and my hand-written relational anchors fewest (1.02).

**Validation on mugs nothing was tuned on** (`body/validate.py`). Every threshold and design choice above was
settled on the seed-7 scene, so its numbers flatter. The seed-11 scene has the same kinds of mug as different
individuals (their own dimensions, ages, wear, stains and turns; the chip now at the back). Learn on all six seed-7
tasks, take the six seed-11 tasks, nothing changed. The mind's perception of every seed-11 task (handle, chip,
what stands close) matched the answer key.

| attempts to the first hold | chipped | turned | diner | new diner | stoneware | blue | all |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hand-written, relational | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.00 |
| perceived, hand-written vocabulary | 2.7 | 1.0 | 1.1 | 1.0 | 1.1 | 1.0 | 1.30 |
| perceived, minted (widest margin) | 1.1 | 1.0 | 2.2 | 1.2 | 1.1 | 4.8 (worst 28) | 1.92 |
| **perceived, minted (near misses)** | 1.7 | 1.2 | 1.6 | 1.4 | 1.3 | 1.9 | **1.53 (worst 5)** |

Out of sample, deliberate near misses are the more robust way to mint: within a quarter of an attempt of the
hand-written vocabulary, worst case 5. The widest margin keeps a bad tail (the blue mug, worst 28).

**Proposed** (not built):

- failures in the three.js scene revealing their constraints, anchored on funded distinctive marks
- each failure adding a constraint site to the grasp's open question
- grasp success fed in as a good outcome, so the convergent constraints are funded and the
  signature is stored as a box
- graded resonance (the share of a box's keys warm, which `reopen` already computes) read every
  tick to steer the hand
- the stakes order from territory under over-constraint, and the cut order from failures explained
- the measure: **constraints revealed per failure**. A novice should show many failures with
  little in each; an expert, few failures, each a near miss on one constraint.

## Lineage, as contrast

Winston's arch learner (1970) refined a concept from near misses, and Mitchell's version spaces
(1982) tightened a hypothesis with negative examples. Both learn from negatives a teacher supplies.
Neither has an agent whose own failed attempts are the world's resistance, nor success noticed as
the place where revealed constraints converge. They predate the paradigm Gerundelle departs from,
and they are its nearest neighbours, not a counterexample to the claim that this is a
fundamentally different relationship to difficulty.
