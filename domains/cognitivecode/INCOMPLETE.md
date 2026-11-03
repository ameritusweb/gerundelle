# What is not complete in the cognitive code mind

Written 2026-10-27, after rung 9. The ten rungs in `LADDER.md` (0-9, with 5b) were built, run and written up, and
their findings stand as findings about one mind in one world. But the ladder's claim is the README's: **the same setup
as fiction**: the SOV architecture, whole, in the world of coding possibilities. That claim has not been tested. This
document lists what is missing, what was improvised in its place, what the measurements do not yet support, and the
order in which to finish.

Status in one paragraph: every rung ran on the **lean mind** (`fiction/lean.py`, extended as `CodeMind` and four
subclasses), never on Gerundelle, the reference mind. Fourteen mechanisms were added to it as "my choice" without
checking whether the architecture already has them. The architecture's planning, meta-cognition, tournament and
wants-from-ownership were not used. Several numbers in `LADDER.md` were measured by earlier versions of the mind and
have not been rerun with the current one. The comparison with POC3 is asymmetric in ways the write-up does not state
clearly enough.

---

## 1. One arm only

Fiction ran every rung on two minds sharing one world: the lean mind (data-declared, fast to ablate) and Gerundelle
(`E:/vscode/analogy/molecules`, the SOV agent `sov_agent.SovAgent`, read into beats by `fiction/gerundelle_arm.py`).
The comparison was the result: Gerundelle needed its own fixes, rung by rung; it turned out the wider substrate
(temperament expresses there, 3-6 stories per scene against lean's 1-5); it beat lean on rungs 6 and 7.

The code ladder ran only the lean arm. So:

- **Unknown:** whether Gerundelle in the code world needs the same additions (section 2), different ones, or none.
- **Unknown:** whether Gerundelle's planner, tournament and meta layer (section 3) do what the additions were written
  to do.
- **Unknown:** whether the findings (scarcity drives variety; structural transfer across theories; composition beyond
  POC3) hold on the reference mind.

**Needed:** a `gerundelle_arm` for the code world, the counterpart of `fiction/gerundelle_arm.py` (a `GerundelleMind`
whose agent acts in a `CodeWorld` or `StmtWorld`), and the key rungs rerun on it: 0, 1, 2, 4, 5b, 6, 7, 8, 9.

---

## 2. Additions to the mind, unchecked against the architecture

Every mechanism below was added because a rung failed without it, and each is named in its docstring as my choice or
as a port. None was checked against Gerundelle, which may already have it, have it differently, or contradict it.

| Addition | Where | Found at | What it does | Possible counterpart in the architecture (unverified) |
| --- | --- | --- | --- | --- |
| Asking the way to a condition | `CodeMind.ask_way`, `way_to` | rung 1 | after "what is needed?", asks "which push gives it?" | Pose and Attest (SOV_ALGEBRA.md); Gerundelle's told receipts and planning on told ways (fiction LADDER, second pass) |
| Retracting a told way to a condition | `CodeMind.act` | rung 2 | a told way the world contradicts: retract receipt, trust marked down, surprise, anger | Gerundelle: "told ways planned on, refuted when the world contradicts them; anger at the teller" |
| Searching instead of waiting in a still world | `CodeMind.subgoal` | rung 2 | an unmet condition with no push on its object: try the best push elsewhere | Gerundelle's Inquiry ("change something first"); its `await` experiment |
| Repeated runs not offered | `CodeMind.stale`, `plan`, `choose` | rerun after rung 3 | a test of an unchanged program is not offered | the meta layer's "stuck"; Inquiry's decay |
| Inquiry gated in a still world | `CodeMind.value` | rung 0 (note), done before rung 4 | no inquiry for a push already tried under the same facts | Inquiry's decay with repeats (persistence) |
| Credit to slots: claims pending until a run | `CodeMind.register`, `unclaim`, `credit` | rerun after rung 3, rung 4 | a fill makes no claim on the register; the run before it tests it | OWNERSHIP_SOV.md integration step 4 ("credit to slots"), planned for Gerundelle, status unknown |
| Reopen: a learned condition contradicted | `CodeMind.conditions`, `contradicts` | rung 4 | a run failing with its condition met retracts the condition | SOV_ALGEBRA.md's Reopen; Gerundelle's contradiction handling (premature closure, splits) |
| A keeper's way is what held at its reach | `CodeMind.way`, `held_way` | rung 3 | not the latest push that brought the state | Gerundelle's keeper (`keep=True`), its `Model` |
| Episodes and recall by structure | `CodeMind.keep_episode`, `recall`, `follow_recall` | rungs 5, 5b | condition + way's name-free shape; mapped onto the new scene's pattern when seen | Gerundelle's recall (`SovAgent.recall`, Case 2 by shape); fiction rung 6 found it transfers that a relation is expected, not what fills it |
| Test a pending fill first | `CodeMind.choose` (`test_pending`) | rung 6 | a fill not yet tested is run before another fill (off for rungs 0-5) | the planner (plan before experiments) |
| Told or recalled ways tried first | `ComposeMind.choose` (rung 7) | rung 7 | untried known ways before repeated fills | `LeanMind.plan` already does this for told ways to the want; Gerundelle's planner |
| Asking policy | `ComposeMind.choose` | rung 7 | nothing untried, last run failed: ask the growth pattern, then the header pattern | Pose in Gerundelle (which question wins the top) |
| Varying a held way (swap a pair) | `VaryMind`, `StmtWorld.vary` | rung 8 | after everything known and told is tried | Gerundelle's splits; POC3's moves (`skelsearch.MOVES`) |
| Recombining two held ways (typed) | `RecombineMind`, `StmtWorld.recombine` | rung 9 | a value operation replaced by one of the same type from another way | the tournament? not known; POC3's `insert_lib` |

Three of these are trigger rules ("after everything else is exhausted"), written as fixed orders in `choose`. In
Gerundelle the order of what wins attention is the tournament's, driven by pulls and modulators, not by a list.

---

## 3. Architecture not used

### 3.1 Planning and lookahead

Gerundelle has a planner (`sov_agent.plan_step`, `Model`; REORG.md lists "MCTS, the tournament and its modulators"
among what stays; OWNERSHIP_SOV.md: "MCTS is guided by the top-level winners"). The code minds never looked ahead: every
fill was tested by a real run. Imagining a fill against the spec before trying it (the interpreter is the forward model,
cheap and exact) was never considered, though it is the code counterpart of the chess plan's counterfactual lookahead.

**Needed:** lookahead in code: imagined runs (provenance imagined, funding nothing) chosen by the pulls, guiding which
fill to try; measured as runs imagined per lived try, against the current mind.

### 3.2 Meta-cognition

Gerundelle's meta layer (THOUGHT_MOLECULES.md 5f; REORG.md: conflation, splits, modes) notices "stuck" and "conflated".
The code mind's stopping rules are hand-written gates instead (section 2: stale runs, the inquiry gate, the
exhausted-everything triggers). Two findings in `LADDER.md` are conflations the meta layer exists to detect: rung 1's
told condition naming the alphabetically first of six roles that fill together, and rung 7's zip codes holding one of
ten separating facts (`collect.collected_filled`) in place of a joint condition.

**Needed:** the meta layer in the code world: detecting conflation in learned conditions, stuck search, and (for
lookahead) imagining that no longer pays.

### 3.3 The tournament

The ordering of what to do next (ask, vary, recombine, search) is a list in `choose`. In Gerundelle, molecules compete
in a tournament and the winner acts. The pattern agents' "bidding" in the README and in the chess plan is this
mechanism, not something to build anew.

### 3.4 Wants from ownership slots

OWNERSHIP_SOV.md: "Goals placed in the agent's head go"; wants are read off ownership slots. Every code was handed
`spec_passing` (or, for keepers, a slot state). So:

- where a code's wants come from is not in the architecture's own terms;
- **narrowed wants** (README, after rung 6: a code whose courtship or recall keeps returning to one pattern comes to
  want that one) were written down and never built;
- **contest after saturation** did not fire at rung 6, probably because the wants were broad; whether narrowed wants
  make it fire is untested.

### 3.5 Phases steering search

OWNERSHIP_SOV.md section 7: a phase steers attention (curiosity asks the most answerable question; frustration asks what
blocks the goal). In the code ladder phases are read off the register and recorded in beats, but nothing reads them:
they steer nothing.

### 3.6 Other minds

Fiction rungs 2-4 built perception of other minds: Pose and Attest, attribution of changes to whoever acted, trust per
teller, the purposeful-other rule, purpose inferred "from what keeps happening". In the code ladder:

- patterns were minds only at rungs 1-2 (`CodeMind`s with pasts); from rung 7 on they are a `Pattern` class that
  tells ways in a fixed order, not a mind with holes or territory;
- possibility agents (README: specs, functions, patterns, styles each an SOV agent, "thinking about" the code that
  follows them) were never built as agents; possibilities are entries in a `Registry`;
- codes in a population perceive each other only through `match` (free, mine, taken); a contest is a scene rule
  (`Registry.contest`: the holder's reserve drains by 1), not the mind's own perception and resolve as in fiction's
  rung 4 (and code rung 3, which did use them).

### 3.7 Storage and time

Rung 4 (loss) ran without a memory (`carry_on` off, because memory grieves only for things gone from view and a slot
never leaves view). Storage, cooling and resonance (fiction rung 5: a grief stored open, reopened when its anchor
returns; forgiveness as a grudge closing) were not tested in code, and the reason grief belongs to ownership rather
than memory in code was found, not designed.

### 3.8 The printer

The courtship, the retraction, the contest, the loss: all are beats, and none was printed as a story. The README's claim
("fiction is the mind's trace; code is the state it closes into; one run gives both") is untested: no code-world run has
been told and read back by the determination system.

---

## 4. World and perception: choices made, and patches

**Design choices** (each found by a failure, each changeable):

- A slot's state is the roles its value plays plus its abstract values over the spec's cases (`CodeWorld._read`). The
  abstract domain is POC.md 3h's; the set-of-outcomes reading was mine.
- A statement slot's state is its roles only (statements have no value of their own).
- `match` (free, mine, taken) as a perceived fact, and `taken` as a spec state (rungs 6-9).
- Fills: rung 0-5 value slots offer one operation with leaf inputs (`_complete_fills`); rung 7-9 statement slots offer
  only ways the code knows, wired in scope (`stmtworld.rewire`). The first is a bounded enumeration, the second is not
  enumeration at all; the two worlds are not the same kind.
- Still world (`CodeWorld.still`): true for every rung, including rungs 6-9 where other codes' claims change what a code
  perceives (`match`) between its pushes.

**Patches** (working, fragile, to be replaced by interfaces):

- `lean.AMOUNTS` is extended at run time with every fill label as a push strength of 1 (`CodeWorld.__init__`,
  `StmtWorld.refill`).
- `specs.Machine` is swapped for a watching subclass during evaluation (`CodeWorld.evaluate`).
- `rules.FACETS["mask"]` and `specs.CASES[...]` (swapped, suffix, mask) are registered at import time by scene files.
- Rung 4's authored uses write the code's territory register directly (`Scene.use`), and add a `Try` to its `observed`.
- Rung 3's keepers and rung 4's keeper are set up by resetting a past mind's fields by hand (as fiction's `run_arm`
  does).
- Scene-level subclassing by `mind.__class__ = ...` (rungs 8, 9).
- Runs launched with `2>/dev/null`: errors hidden. Several bugs were found late because of it.

---

## 5. Open results

| Item | Status |
| --- | --- |
| Flows 10 and 11 | reachable by recombination in the world directly; **not held by any population** (rung 9): the codes under pressure have the wrong headers and give up before reaching (insert, enumerate), and the codes with enumerate headers are satisfied early |
| Contest after saturation | **did not fire** (rung 6); narrowed wants not built (3.4) |
| A rival claiming a slot while it is open | rung 4's extension, **not run** |
| Conjunction learner | **never needed**: scope wiring joined every pair the scenes offered; the lamp's AND is still unlearned by any mind, fiction's or code's |
| Rung 4, reading B with long holds | grief never formed for held 7 within the recovery (doubt only); whether it forms with a slower recovery is untested |
| Rung 3's known answer | half met: doubling Index's resolve flips the ending; doubling Item's changes nothing (it already wins at equal resolve) |
| Rung 5's same-skeleton scenes | superseded by 5b for the transfer claim; rung 5's own numbers are a within-theory result only |
| The pending-claim rule's effect on courtship stories | measured only in counts; never read as a story |

---

## 6. Measurement: what the numbers do not yet support

### 6.1 Numbers from earlier minds

The mind changed after most rungs were measured, and not every rung was rerun:

| Rung | Last measured with | Changed since, not rerun |
| --- | --- | --- |
| 0-2 | the inquiry gate (before rung 4) | credit by `unclaim` (rung 4 B), Reopen, the stale-run fix (rung 5b), episodes; rung 0 spot-checked once (seed 0: 80 tries) |
| 3 | the inquiry gate | the same |
| 4 | `unclaim` | Reopen's outcome fix applied before; the stale-run fix after |
| 5, 5b | the stale-run fix | `test_pending`'s gates (rung 7), told-ways-first is scene-level (ComposeMind) |
| 6 | `test_pending` gated on `match` | the empty-slot gate (rung 7) |
| 7-9 | each its own version | — |

**Needed:** one command that reruns every rung with the current mind and regenerates every table, as fiction's
working rule required ("after any change, re-run rungs 0-6 and check the trip column stays 1.00").

### 6.2 Sample sizes

10 seeds (rungs 0-5b), 3 seeds per population (rung 6), one population run per configuration (rungs 7, 8), 6 telling
orders and 2 patience levels (rung 9), 5 resolve settings (rung 3, one run each). No variances or intervals are
reported. The orders and seeds are fixed (deterministic), so "10 seeds" is 10 orders of the fills, not 10 independent
samples of anything else.

### 6.3 The comparison with POC3

- **The fifth seed is POC3's own output.** Rung 9's insert seed is POC3's flow-9 program: a program POC3's search
  discovered, given to the codes as a seed. Flow 9 "held by the codes" is therefore not a discovery; the honest count of
  flows reached from POC3's four hand-written seeds alone is rung 8's (up to 6).
- **Rung 6's possibilities are POC3's programs** (distribution, not discovery), as its write-up says.
- **Budgets are not compared.** POC3's runs had their step budgets (3,000 steps per run, several seeds, eight audit
  rounds); the codes' tries are counted differently (every fill and run of every code). No common unit of effort.
- **Churn excluded by judgment.** Flows 0, 2, 3 were excluded as churn (agreed); the exclusion is a reading of POC3's
  audit history, not a rule POC3 states.
- **The new programs are not audited.** The 3-4 programs POC3 did not find pass the spec; they were not run through
  POC3's rules, its gate (`specs.admit`), or an audit by eye, as POC3's own programs were. (The decision that the spec
  judges, not `admit`, was for the mind's perception; the comparison with POC3 is a different question.)

### 6.4 What was authored

Known answers were chosen before running, but the scenes were built around them: the open slots, the seeds, the facets
perceived, the cases. Every rung's scene names its authored events (uses, regressions, the Pattern's telling order), and
the preferences in rung 6 are tie-break orders, not wants.

---

## 7. Engineering debt

- **Speed.** The lean mind rescans its ledger for every value estimate; the code world re-reads its state (facet
  matching, the interpreter over every case) on every read where not cached. A 10-seed sweep of a one-slot world took
  most of an hour; rung 9's 13 population runs took over an hour. Gerundelle is slower still (fiction). Lookahead and a
  second arm multiply this.
- **No regression tests.** Fiction has the round-trip column and a Wikipedia regression for the grammar; the code
  ladder has no test that a change to the mind leaves earlier rungs' known answers met.
- **A chain of scene subclasses** (`ComposeMind` -> `VaryMind` -> `RecombineMind`; `CodeWorld` -> `StmtWorld` ->
  `ComposeWorld`; `PopWorld`) holding mind logic that belongs in the mind.
- **Three cache bugs** were found only by their effects (an id reused after free; a clock that moved after the read; a
  key without the spec). The caches are keyed correctly now; they have no tests.
- **`codemind.py`'s module docstring** has accreted a history of fixes and reads as a log, not as a description.

---

## 8. To complete, in order

1. **Read what was skipped.** Gerundelle's `sov_agent` (`SovAgent`, `plan_step`, `Model` and its MCTS, `recall`,
   Inquiry), the tournament, and the meta layer (THOUGHT_MOLECULES.md 5f and its code). Everything below depends on it.
2. **Map section 2 onto the architecture.** For each addition: covered by an existing mechanism (then use that one), a
   port (then cite it), or new (then keep it, named). Remove what duplicates.
3. **A Gerundelle arm for the code world,** and the key rungs rerun on both arms, compared as fiction compared them.
4. **One rerun command** for every rung with the current mind(s), regenerating every table in `LADDER.md`; a
   known-answer test per rung.
5. **Wants from ownership slots**, including narrowed wants; rerun rung 6's contest-after-saturation measurement.
6. **Lookahead in code** (imagined runs, funding nothing, chosen by the pulls), with **meta-cognition** deciding when
   imagining stops paying; measured as imagined runs per lived try.
7. **Phases steering search**, and **other minds** as minds: patterns and possibilities as SOV agents with holes and
   territory, contest through perception and resolve rather than a registry rule.
8. **Close the open results** (section 5): flows 10 and 11 held by a population; a rival claiming an open slot; a scene
   that genuinely needs the conjunction learner; storage and time across a loss.
9. **Print the courtships as stories** and read them back (the README's "one run gives both").
10. **Restate the comparison with POC3** honestly: from the four hand-written seeds only (no POC3-discovered seed), in a
    common unit of effort, with the new programs audited by POC3's rules and gate, over enough orders and seeds to
    report ranges with variance.
11. **Engineering:** speed (cache the mind's estimates, not only the world's reads), interfaces in place of the patches
    in section 4, regression tests, and errors not hidden.
