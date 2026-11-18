# Control flow and loops via unit potential forces

Design notes for adding control flow and loops to the clean code domain. Nothing here is built yet.

(Corrected 2026-11-14, the user: loops and branches have no wheels. A condition is a fixed stack of unit potential forces, set per
problem, and the force arriving from the graph overwhelms it or not. The mind changes loops and branches only through the operation
wheels upstream.)

## The principle

Control flow and loops are not programming constructs. They are force balances. The mind doesn't learn "while" or "if/else": the
behaviour we call looping and branching falls out of the physics. The mind still only turns operation wheels; what the loops and
branches do follows from the values those wheels produce.

## Unit potential forces

A **unit potential force** is a single unit of resistance stacked against an external force. Multiple units can be stacked. When the
external force outnumbers the stacked units, it overwhelms them and the gerund flips.

This is the primitive for:
- **Counting and arithmetic:** numbers are stacked unit potential forces on zero
- **Loop termination:** a loop goes round until the force arriving at its condition outnumbers the condition's units
- **Control flow:** a branch goes one way or the other by whether the arriving force outnumbers its condition's units

## Conditions

Loops and branches both have a **condition**: a combination of unit potential forces that must be overwhelmed.

- The condition's units are **fixed per problem**: part of the problem's shape, set when the problem is made, never scrambled.
- The condition has **no wheel**. The mind can't change it.
- The **force against it** is the force arriving from earlier in the graph, which comes from the inputs. Different inputs, a
  different force.
- If the arriving force **outnumbers** the condition's units, the condition is overwhelmed; otherwise it holds.

## Loops

A loop is a connection in the feed-forward graph that feeds back into itself, guarded by a condition.

- Each time round, the value passes through the loop body, whose operations (on their wheels, like any others) change it.
- The changed value's force pushes against the condition.
- While the condition holds, the loop goes round again.
- When the force outnumbers the condition's units, the gerund flips from *iterating* to *done*, and the value flows onward.

So how many times a loop goes round depends on the inputs and on the operations: the same graph with different inputs loops a
different number of times. The mind changes a loop's behaviour by turning the operation wheels upstream of it or in its body, which
changes the values, which changes when the condition is overwhelmed.

### What the mind perceives

| Object | Doings |
|---|---|
| the loop connection | `iterating` (the condition holds), `done` (the force overwhelmed it) |
| the condition | its stacked units (perceived as a force magnitude, not a number) |

### Validity

A loop that goes round too many times may push values out of range: the range-validity gerund flips to failing. A loop that goes
round too few times may not produce the correct output: tests fail. The mind navigates between these by turning the operation
wheels that feed and make up the loop.

### Termination: the overflow gerund

With a fixed condition and a value-driven force, a loop ends only if the operations eventually make the force outnumber the
condition. A scrambled loop body that never does (say, `subtract 1` where `add 1` belongs) would go round forever.

Each loop has an **overflow gerund** (the user, 2026-11-14): it flips to *overflowing* if the loop's count of rounds gets above a
certain number. So the world never runs forever: a loop past its limit is stopped, and its overflow gerund shows it.

| Object | Doings |
|---|---|
| the loop's overflow gerund | `contained` (the rounds stay within the limit), `overflowing` (they went above it) |

As with range validity (confirmed by the user, 2026-11-14): the limit is set per problem and hidden from the mind; the gerund passes
only if the loop stays within its limit for every test input; and an overflowing loop is the compiler-error side of the territory,
as a failing range-validity gerund is.

## Control flow (branching)

A branch is a fork in the graph where two paths diverge, guarded by a condition.

- The force arriving at the fork, from earlier in the graph, pushes against the condition's units.
- If it outnumbers them, the value goes down one path; if the condition holds, the value goes down the other.
- The branch isn't a boolean condition: it's the force finding where it can go.

The mind changes which values take which path only by turning the operation wheels upstream, which changes the force arriving at
the fork.

### What the mind perceives

| Object | Doings |
|---|---|
| each branch path | `flowing` (the force takes this path), `blocked` (it doesn't) |
| the fork point | `selecting` (choosing which path the value takes) |

### Conditional behaviour

The mind doesn't learn "if x > 5 then path A else path B." It learns: "when the force from the value is strong enough to overwhelm
the condition, the value goes through A; otherwise it goes through B." The threshold is the condition's fixed units; what the mind
can change is the force that arrives.

## Interaction with existing mechanics

### Tests and territory

Tests still pass or fail. A loop that goes round the wrong number of times produces the wrong output: the test fails, the mind feels
the gap. A branch that routes values the wrong way produces the wrong output: same feedback.

### Range validity

Loops can push values outside valid ranges. Too many rounds of "add 2" on a value near the range ceiling, and the validity gerund
flips. The mind learns the relationship between what feeds the loop and the range constraint.

### Lint

Lint, read by the world from the test inputs, each its own lint gerund (picked; PLAN.md):
- A loop whose condition is overwhelmed at once for every test input never goes round: a dead loop.
- A branch whose condition is always overwhelmed (or always holds) makes the other path dead code.


### Clean code

The simplest setting is still the fewest non-identity operations, now including those in loop bodies and on branch paths.

## Connection to arithmetic

This is the same primitive the mind uses for understanding numbers:
- **Counting:** stacking units one at a time, perceiving each new balance
- **Addition:** stacking this many units onto that many
- **Subtraction:** removing units
- **Multiplication:** stacking a group of units, multiple times
- **Division:** how many times can you remove this group before the balance hits zero

A condition's units *are* a number, experienced as a force balance. The mind doesn't need separate concepts for "iteration count"
and "arithmetic": they're the same physics.

## Open questions

None left (2026-11-14). Picked by Claude (the user: "pick'em"):
- **Which branch path is which:** fixed per problem, part of the shape: the problem names the path an overwhelmed condition sends the
  value down.
- **Loops and branches together:** allowed both ways. A branch inside a loop's body reads its condition each time round; a loop on a
  branch path runs only for the values that take that path. Each is its own force balance on the value arriving at it. A loop never
  contains another loop, even through a branch (no nested loops).
- **Dead loops and dead paths as lint:** read by the world from the test inputs, each its own lint gerund (PLAN.md: a loop that goes
  round zero times on every test input; a branch path no test input's value takes).
- **The overflow gerund's readings:** `contained`, `overflowing`.

Answered (2026-11-14, the user): the force against a condition is the force arriving from the graph, based on the inputs; the
threshold is the condition's fixed units, and the arriving force is compared against it; conditions have no wheel; a loop that would
go round forever is caught by its overflow gerund, which flips when the count of rounds gets above a certain number. **Negative values
are compile errors** (so a force is never negative, and the question of how a negative value pushes doesn't arise). **No nested
loops**: a loop's body never contains another loop.
