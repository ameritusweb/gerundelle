# Clean code

A new domain (the user, 2026-11-14). The code is a small language of our own, and its structure is a force structure with gerunds.
The mind's territory is code that is right and clean: tests passing, validity holding, no lint, the simplest setting.

Nothing here is built yet. This file holds what is decided and what is still open. Each item says who decided it.

## Decided

### The language: a feed-forward graph

- A program is a feed-forward graph. It starts with N inputs and goes from left to right, generally. Paths can connect, and they
  always end at one output path, with one output (the user).
- Each connection is an operation: on a single path, like "add 2" or "subtract 2"; where paths come together, like "multiply"
  (the user).
- Values are integers (proposed, the user agreed). A negative value is a compile error (the user, 2026-11-14).
- One gerund per compile error (the user, 2026-11-14): each range-validity gerund, each loop's overflow gerund, and a gerund for a
  negative value at each place a value can go negative (each connection, on every test input; picked, below).

### Moves: wheels

- Each operation has a potential force that changes what it does. The force can go forward or backward (the user).
- Think of a wheel: each place on its circumference is an operation. A force changes the operation to the one directly in front or
  directly behind, along the circumference (the user). So a move is one push, one step, on one connection's wheel. The mind never
  writes code: it turns wheels.
- The wheels wrap around (proposed, the user agreed).
- There are two kinds of wheel (the user):
  - **Single-path wheel:** `... multiply by 3, multiply by 2, add 2, add 1, identity, subtract 1, subtract 2, negate, halve ...`.
    It is smooth in the middle and surprising at the edges, so small turns are predictable, but the mind can get stranded far from
    the answer if it overshoots into negate or halve.
  - **Join wheel:** `... max, add, multiply, subtract, min, mod ...`. It has fewer operations, but each changes how the two paths
    interact: multiply next to add next to subtract means one step can flip credit assignment completely.
- `halve` rounds down, on integers (proposed, the user agreed); that gives plateaus, where a push can change nothing on the tests.
- `mod` by zero makes the value invalid (proposed, the user agreed).

### The corpus

- A corpus of coding problems. Each problem instance has one fixed graph shape (the user): the mind can't change the shape, only
  turn the wheels.
- How far off the operations start is random: luck (the user). Each problem comes from a correct setting, scrambled.
- Something always satisfies the problem: there is a setting that passes every test and keeps every validity gerund passing (the
  user: anything else "would be too hard"). The correct setting is one.

### Range validity

- Range-validity gerunds (the user): a gerund switches between "passing" and "failing" validity based on a hidden range constraint.
  The mind sees the gerund's reading, never the range; where the range's edges lie, it learns from its own record of which pushes
  flipped it.
- The problem defines the gerunds: where they are, and each one's range (the user).
- A gerund passes when the value at its place stays in range for every test input (the user).
- This is the compiler-error side of the territory: a failing validity gerund is an invalid program, read from the structure itself.

### Tests

- The mind perceives pass or fail for each test, plus the output value, only when it fails (the user). A pass tells it the test is
  held territory; a failure and the actual output tell it the gap between what it produced and what was wanted, a force the mind can
  feel. Pure pass/fail is too opaque; every output value on every test is too generous (the user).

### Lint

- Lint is detectable local waste (the user). The user: lint the mind can see in the structure without running the tests; lint that
  depends on values is read by the world from the test inputs (below, picked).
- `add N` followed by `subtract N` on a path is lint (the user).
- Identity in the middle of a path is not lint (decided 2026-11-14). The shape is fixed, so identity is the emptiest a connection can
  be, and clean code prefers it. The user first listed it as lint; dropped because it would conflict with clean code.

### Clean code

- Clean code is the simplest setting that still satisfies everything: the fewest non-identity operations (the user). The mind
  doesn't just solve, it settles (the user).

### Territory

What the mind owns (the user): lint rules off, compiler errors off, clean code, tests passing. In this world:

| Territory | Read from |
|---|---|
| Tests passing | each test's pass or fail |
| Compiler errors off | each range-validity gerund passing, each loop's overflow gerund contained (`CONTROL_FLOW.md`), no negative value, no `mod` by zero; one gerund per compile error |
| Lint rules off | each lint rule not firing where it could |
| Clean code | the fewest non-identity operations among the settings that satisfy everything |

### Control flow

Loops and branches: `CONTROL_FLOW.md` (the user, 2026-11-14). Each has a condition, a stack of unit potential forces fixed per
problem, with no wheel; the force arriving from the graph, based on the inputs, overwhelms it when it outnumbers the units. Each loop
has an overflow gerund. No nested loops (the user).

### Picked by Claude (the user, 2026-11-14: "for the rest, pick'em")

- **Negative values:** one gerund at each connection, failing if the value there goes negative on any test input.
- **`mod` by zero:** a compile error, so its own gerund, one at each join, failing if the join takes a `mod` by zero on any test
  input.
- **Lint that depends on values** (the user's "dominated by the other path"; dead loops and dead paths, `CONTROL_FLOW.md`): read by
  the world from the test inputs, as the validity gerunds are. Each is its own lint gerund: a join input is dominated when it never
  changes the join's result on any test input; a loop is dead when it goes round zero times on every test input; a branch path is
  dead when no test input's value takes it. The mind still never sees the values, only the lint gerunds.
- **"Fewest range-validity gerunds under pressure":** dropped from clean code. The problem fixes the gerunds, so their number can't
  change; clean code is the fewest non-identity operations.
- **The order of a join's inputs:** fixed per problem, part of the shape: each join has a first and a second input; `subtract` is
  first minus second, `mod` is first mod second.

## Open

1. **The force world:** how a graph, its values and its wheels sit on `force_world.py` (every world is built on it first). Not yet
   designed. (2026-11-17: it was never designed; `world.py` was built straight on `graph.py`, so the mind perceives operations and
   values as names, `adding_2`, `giving_7`, `wanting_9`, never as forces, and the SOV, which subsumes algebraic equations (the user,
   balance/PLAN.md), has no terms to build the program's equation from. Fifteen rung-2 variants patched the mind around this; the
   world was never grounded. Proposed below, for the user's rulings.)

### The force world, proposed (2026-11-17, Claude, for the user to rule on; nothing built)

Grounded the way the balance world is (balance/PLAN.md), the one domain where the SOV demonstrably builds equations from what it
perceives (rung 4: x solved on a scale; rung 3: count-conditioned knowledge carried across identities, p ~ 0.02):

- **A value is a stack of unit forces.** Each place on the graph (each input, each connection's output, the join, the output) is an
  object bearing, per test, the units of the value there. Perceived as balance perceives a load: an identity-free count per place
  and test, `bearing_<n>` (balance found the count must be identity-free to transfer: the load sensor, rung 3), never as a name
  like `giving_7`. A number is not a territory: these are unclaimable, as balance's load is.
- **An operation is a unit transformation, lived.** The wheel keeps its operation (what is turned), but what it does is perceived
  as the change between the counts on either side of it: three units in, five out. `adding_2` becomes what it does: two units
  joining. The equation's terms are then in the percepts: in, out, and the relation between them.
- **A change arrives as a pulse.** When a wheel turns, each place whose count changes shows the change as its own transient object
  (`rising_<n>`, `falling_<n>`), beside the standing count, as balance's pulse does (its third cut: the change and the count both
  perceived, neither hiding the other).
- **A test is a balance.** The output's units press one side, the wanted units the other: `holding` when they are equal,
  `giving_way` toward the side that outnumbers (falling short or overshooting). This is balance's scale (rung 4), with the
  wanted known rather than screened. Pass and fail stay as they are; the balance is how the gap is felt.
- **What stays hidden:** the range-validity reserves, as balance's reserves are (the mind learns their edges from flips).
- **Small numbers first:** test values in the subitizing range for the first rungs (balance: reserves 1-4), so counts are few and
  each can be lived.
- **Territory unchanged:** tests passing, compile errors off, lint off, clean, time.

**Decided (the user, 2026-11-17):**
1. **A stack per test**: every place shows its count for each of the three tests at once (the coupling between tests perceivable).
   This replaces the 2026-11-14 restraint under Tests ("the output value only when it fails"; "every output value on every test
   is too generous"): the user, asked, 2026-11-17: "Every place, every test".
2. **The identity-free count**: each place reads `bearing_<n>` per test, with a pulse when it changes; no per-unit identities.
3. **Balance's way**: its own world built to the force world's percepts (forces, sensors, pulses, potentials), not poc nodes.
4. **Rebuild from rung 0**, expectations written before each run.
2. **Rungs:** the first, smallest rooms (a few inputs, one join, one gerund) and what is expected of each. Not yet designed.
3. **Later challenges discussed, not decided** (2026-11-14): hidden tests (does the mind understand the program or only fit it);
   fan-out (one path feeding several); bigger graphs and further scrambles; a move budget; an opponent that turns wheels too.
