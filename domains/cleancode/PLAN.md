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
- Values are integers (proposed, the user agreed).

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

- Lint is detectable local waste, which the mind can see in the structure without running the tests (the user).
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
| Compiler errors off | each range-validity gerund passing |
| Lint rules off | each lint rule not firing where it could |
| Clean code | the fewest non-identity operations among the settings that satisfy everything |

## Open

1. **"A path that feeds a join but whose value is always dominated by the other path"** (the user's lint rule). Whether a join's
   input is always beaten (say, in a `max`) depends on the values on the test inputs, so it isn't structural, and the mind never
   sees values inside the graph. Options: the world reads it from the tests; drop it from lint; or keep it, with the mind
   discovering it from its own record.
2. **"Fewest range-validity gerunds under pressure"** (the user, under clean code). The problem defines the gerunds, so their number
   can't change. Perhaps: the fewest near the edge of their range, a cleaner program keeping values comfortably inside? To be
   settled.
3. **Which input of a join is the left one**, for `subtract` and `mod`, where the order matters.
4. **The force world:** how a graph, its values and its wheels sit on `force_world.py` (every world is built on it first). Not yet
   designed.
5. **Rungs:** the first, smallest rooms (a few inputs, one join, one gerund) and what is expected of each. Not yet designed.
6. **Later challenges discussed, not decided** (2026-11-14): hidden tests (does the mind understand the program or only fit it);
   fan-out (one path feeding several); bigger graphs and further scrambles; a move budget; an opponent that turns wheels too.
