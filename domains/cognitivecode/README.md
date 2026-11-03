# Cognitive code

The idea (the user, 2026-10-26): generate code the way `fiction/` generates prose, cognitively, with SOVs, iterating
until an ending state. **It is the same setup as fiction.** The machinery stays fixed (the mind, its ledger, holes,
pulls, receipts, splits, phases, resolve, endings read off the mind); only the world changes.

## The code is a mind

The program is not something a mind outside it pushes on; the code is the mind. Its structure is an SOV graph:

| SOV (`SOV_ALGEBRA.md`) | code |
| --- | --- |
| a node with typed open slots, surrounded by known bonds | a skeleton of gerund operations with unnamed typed slots (POC3, `POC.md` 14c): valid if some filling works, standing for all its readings at once |
| Open | a typed hole, a parameter |
| Fund | a case run through a slot and coming out right (a lived receipt) |
| Close | a slot filled, funded past M0 |
| Pose | a hole's type: what fits here? |
| Split (bimodal outcomes divided on a boundary condition) | a branch: some cases pass, some fail, split on the fact that separates them (`if v1 == '': return []`). The learned condition written into the structure |
| Unify | two branches that behave the same, merged |
| Reopen | a regression |
| Park | a stub |
| provenance | code derived and tested (lived, worked) against code pasted or data taken on another's word (told, half) |

## The code mind acts on its world

As Mara acts on the box. The world is everything the program touches, and every contact is an interaction:

- **Pulling data is perception:** a file, an API, user input (the `see` beat).
- **Compilation and errors are the world pushing back:** a compile or type error is a push the world will not take
  ("the lid did not move"); a runtime exception is a surprise (a prediction contradicted); a run that comes out right is
  a receipt that funds the slot.

So the mechanisms the fiction ladder built have their code counterparts already (my reading; each to be tested by a
rung, not assumed):

| ladder | code |
| --- | --- |
| a condition learned by contrast (rungs 0-1) | error handling: "the call fails only if the input is empty", a guard or an except: a split |
| waiting for a hidden periodic driver (rung 1, the wind) | retry with backoff: the network is the wind |
| told receipts at half weight (rung 2) | external data: an API's answer is another's word |
| a lie; trust per teller (rung 3, `lean.reliability`) | bad data from a source; validation is testing a told receipt |
| two minds on one region; keeping (rung 4) | concurrency: two writers on one state; locks |
| storage, cooling, resonance (rung 5) | caching and invalidation |
| resolve, patience (rung 4, `temperament.py`) | timeouts, retry limits, giving up |
| recall by shape (rung 6) | a known pattern applied to a new problem |

**Development** is the mind learning: its graph changes through compile and test interactions, slots fund, splits
become branches. **Running** is the mind acting on what it learned (`lean.plan`: exploit the way before inquiring). A
deployed program is a mind with its slots closed, acting on its ways; when the world surprises it in production a slot
reopens, and development resumes.

**Endings** are closures read off the mind, as in fiction: reached (it works: the spec met), resigned (patience or
resolve spent: a timeout, a failure given up), unresolved. A reached ending can be earned (the conditions slot closed)
or lucky (it passes with the conditions slot open, as Gerundelle opened the cupboard because the bolt sorted first).

**Fiction and code from one run:** fiction is the mind's trace (what was tried, failed, realized, felt, in order); code
is the state it closes into (what was understood, as structure). "Mara realized that the latch had kept the lid shut"
and an `if` guarding the lid are the same receipt: the story of learning it, and the knowledge itself.

## Territory: agents for patterns and styles, claiming what is unclaimed

The user, 2026-10-26: territorial ownership is not abandoned. There are SOV agents for different coding patterns and
different coding styles, and they attempt to gain territory that is not already claimed.

This is `OWNERSHIP_SOV.md` applied to code: territorial ownership (or the perception of it) is the foundational
motivation, and a world reports what happened, never what it is worth (`DRIFT.md` rule 10). No designer reward drives
the program's growth; agents extending their territory drives it. In the force world "mine" means "my push fills it and
I know what follows" (`OWNERSHIP_SOV.md` sec. 2). In code, as proposed here (not yet decided):

- **A region** is a slot of the program (a typed hole of the skeleton) with the behavior that runs through it (the spec
  cases it carries).
- **A claim** is an agent filling the slot with its pattern. It **takes** when the cases through the slot come out as
  the agent predicted. Holding strength is `ownership.Territory`'s, (took + κ·b) / (tried + κ).
- **The agents** are SOV minds, each with its own ledger, holes, temperament and ownership SOV. A pattern agent does
  one kind of thing: iterate over positions, read in lockstep, accumulate a result, guard a boundary, splice, register
  and notify (POC3's theory facets are candidates). A style agent is a way of doing it (my examples: index loop vs zip
  vs enumerate, append vs accumulate, early return vs nested branch).

The slot kinds (`TERRITORIAL_MAPPINGS.md` sec. 1), read in code (proposed):

| slot | in code | question |
| --- | --- | --- |
| unclaimed | a hole no agent has filled; a behavior the spec asks for that nothing produces | what happens if I fill it? |
| control | an agent's filling that does not take (the cases through it still fail) | what blocks it? |
| contested | a region one agent holds and another also fills (an index loop and a zip loop over the same sequences) | what else moves it? |
| lost | a region that was held and stopped taking (a regression) | what took it? |
| uniqueness | a doing of one agent that no other agent covers | does anyone else hold this? |
| relation | another agent's doing that this one depends on (the loop the accumulator lives inside) | will it be there? |

What follows from the ownership doc, as predictions for code (to be tested):

- **Growth is expansion into unclaimed territory.** Agents fill holes because unclaimed regions pull
  (κ / (κ + other moves)), not because a search proposes edits. A program is finished when no unclaimed behavior is
  left and every claim takes: the frontier is closed.
- **Contest begins when the frontier closes** (`OWNERSHIP_SOV.md` sec. 8: alphas re-emerge when no unclaimed slots are
  left). While unclaimed regions remain, pattern agents do not fight; afterwards they contest each other's regions, and
  resolve decides who outlasts whom (rung 4). That would be refactoring, and conflict between styles, emerging from
  structure.
- **Nested territory.** An architectural pattern holds a region that contains other agents' claims (pub/sub's registry
  contains the loop that notifies); the alpha, in sec. 8's terms, is the agent holding the most slots that others live
  inside.
- **Phases are readings of the territory graph, not rules:** frustration on a control slot whose fillings keep failing,
  anger at an agent whose filling blocks this one's, sadness at a regression, joy when a claim takes.
- **Variety from the population.** Which agents are present, and their temperaments, decide which program the
  society closes into. Different populations, different programs, each a valid ending.

### Scarcity

Ownership means something only where territory is scarce. Substance learned this first: in `src/share_economy.py`
cash never constrained anything, every bidder could afford every property, and "auctions reduced to 'best prediction
EMA wins'"; prices were made a share of the money supply so that holding costs and must be earned (rent on good
predictions). `REORG.md` sec. 5 places scarcity at Stage 6: "attention, attribution and exclusive roles are limited;
information is not", so a region is held by one agent at a time for attribution and by many for knowledge. The fiction
ladder runs on it too: one box, two wants (rung 4), and a lie only where a true answer would hand the region over (rung
3).

In code (proposed):
- **The spec fixes how much territory exists:** the behaviors it asks for. A slot is filled by one agent's code at a
  time (an exclusive role); what an agent knows (a learned condition such as lockstep) is not scarce and can be held by
  many.
- **Holding must keep earning** (rent): an agent keeps a region only while the cases through it take. A regression is
  a lost slot.
- **Junk holds nothing.** POC3's audit rounds fought no-ops, churn and decoration, and novelty search manufactured
  broken-but-novel programs (`POC.md` 3f-3h), because novelty is unlimited. Under scarcity, code that makes no case
  take claims no territory, so the load-bearing pressure of principle 3 would come from the economy rather than from a
  rule per exploit (to be tested).
- **Specialization.** Overlapping costs contest, so agents differentiate toward uniqueness: modular code as a division
  of labor.
- **Contest when the frontier closes**, as above: once every behavior is held, the only territory left is another
  agent's. Measured at rung 6 (LADDER.md): it did not fire, because a code wanting any passing program keeps searching
  rather than fight. Contest needs a narrowed want (fiction's was fixed on one region, the latch): a code whose courtship
  or recall history keeps returning to one pattern or shape should come to want that one, an attachment rather than an
  open preference (the user, 2026-10-27): temperament meeting courtship history. Rung 7's codes should carry it.

## Pushes are bounded, as in fiction

In the force world a push is an invitation read off the structure: `ForceWorld.invitations()` offers `(strength,
object, gerund)` for every node whose gerund watches the push channel against a finite reserve, never off names. The
mind does not search; `LeanMind.value` scores each invitation (work x gap x the hole's pull, plus inquiry) and takes
the highest. In code the invitations are likewise read off the structure: each typed hole's expansions that fit it, and
the move set POC3 already has (replace, rewrite, insert, delete, reorder, extract, inline, add_else, insert_lib).

## What exists

In `E:/vscode/analogy`:
- **The world's structure:** the operation vocabulary (`VOCABULARY.md`, 37 gerunds), the grammar and printer (`poc2/`),
  skeletons with existential wiring (`poc3/skeleton.py`).
- **The world's physics:** the interpreter for the construct language and the specs (`poc2/interp.py`, `specs.py`);
  the rules, which define what is admitted (`POC.md` principle 1: "the search decides what gets tried, never what gets
  kept").
- **What chooses today:** a blind search (MCTS, seeded mutation with Metropolis acceptance, `poc3/skelsearch.py`).

In `fiction/`: the mind (`lean.py`; Gerundelle's `sov_agent.py` in `analogy/molecules`), temperament, beats, the story
layer and the printer.

What POC3's search could not do, which the setup predicts the mind can (to be measured):
- **Cross invalid intermediates.** "Items with a counter" (three coordinated inserts) was never found; the editor's
  "insert through temporaries" needed two extractions no move made. Blind mutation cannot carry a plan across steps
  that each score worse. A learned condition can ("this works only if that node is in state S"): a subgoal, held
  across the failing steps (`LeanMind.subgoal`; rung 4's latch before the lid).
- **Transfer.** The cross-domain library offered 180-265 sections and none made a valid skeleton. Recall by shape
  carries a learned condition keyed by gerunds, not a section. "A read at a position works only if its partner is read
  at the same position" is lockstep, the parallel-strings theory, learned as a condition instead of written by hand as
  `ps_lockstep`.
- **Variety without a novelty bonus.** Novelty search manufactured broken-but-novel programs (`POC.md` 3h). Here
  different temperaments reach different valid endings (index loop, zip, enumerate), as rung 7's four endings did.

## The ladder

Each rung a new world, testing whether the mechanisms are general. Rung 0: the jack-in-the-box in code: one want, one
hidden condition, the world pushing back with errors.

## Open

- Which nodes invite a push. My guess: the load-bearing slice (`POC.md` 3g): a node that cannot reach an output invites
  nothing, as a push that cannot cross a reserve is not invited.
- What a fact is, for conditions: gerunds alone, or gerunds plus abstract values per case ({empty, non-empty},
  `POC.md` 3h). Contrast learns only from facts that differ between tries.
- Phases: in a mind, frustration and curiosity redirect search; in the code mind, whether they do the same work.
- One mind or many: is the program one mind whose territory nests the pattern agents' claims, or the shared world the
  agents claim regions of? (Substance's population level: "a universe's doings are for owning properties and paying
  rent".)
- Which agents exist: one per POC3 theory facet, per vocabulary gerund, or per learned pattern (a section from the
  library becoming an agent of its own once it holds territory).
