# The Gerundelle arm in the code world

The user, 2026-10-27: the Gerundelle arm, as fiction did it, where it needs to be competitive with or beat the lean arm.
Gerundelle is `analogy/molecules` (`SovAgent`, `Mind`, `Inquiry`, the meta layer, the territory register), read into
beats by fiction's `gerundelle_arm.GerundelleMind`, acting in the same `CodeWorld` as the lean code mind. Backup before
any change: `backup/molecules_2026-10-27/` (checksums in `SHA1SUMS`). Every change was run against Gerundelle's own
suite: baseline 73/80, 2 pending (`backup/baseline_tests.log`, the same as fiction's); reference after the honest repair
72/80 (`backup/fails_after_honest_repair.txt`); every later change matches that reference.

## What changed in Gerundelle (each a principle, with its first failure)

| change | where | scope | first failure |
| --- | --- | --- | --- |
| Inquiry knows whether its world moves only when the agent acts (`Inquiry.still`, set by the agent from the world) | `molecules.py` Inquiry, `sov_agent.py` perceive | all | — |
| No experiment made only of waiting: retrying a push after a tick or two ("what is left to vary is the moment"), waiting to watch, waiting for a condition | `Inquiry.suggest`, `Inquiry.observe` (await) | still worlds | rung 0: the same junk fill retried after a wait, four times in five tries |
| With no lead, untried preparations before the first four known changes (a known preparation only re-makes a known situation) | `Inquiry.suggest` | still worlds | rung 0: four known fills re-tried before every run, one 29 times; the answer never tried. Everywhere it cost T78 a seed (a moving world may meet a new moment) |
| A question is answered when **all** preparations are ruled out, as `Inquiry.result`'s docstring says: each part 1/n, not m0/n | `Inquiry.result` | all | rung 0: the run's question closed after 64 runs (half ruled out), the want's slot parked, the agent surveyed fills instead of testing. The half came from mixing units (understood at m0, answered at 1.0) against DRIFT.md's own fix; three tests had grown around it and were repaired (the honest repair, below) |
| ... counted among every preparation, those already ruled out too | `Inquiry.result` | still worlds | rung 0: counted among those left, later parts weighed more and the question closed at about two thirds. Everywhere, the null world's agent stopped experimenting before all were ruled out, its slots never closed, and it went quiet with its graph live: the reverse of T80. Open: when a question should stop, where the agent can stop asking |
| A known step is not done: an experiment's last step, an action in a situation it was already tried in, comes out as it did; the experiment reports as usual | `SovAgent.tick` (the experiment's queue) | still worlds | rung 0: every conditions experiment ran the spec after its preparation, in situations already tried: about 75 runs |
| A situation is new until tried **once** (leads) | `Inquiry.untried_for` | still worlds | rung 0: with twice (a moving world's rule, for outcomes that come and go), nearly every fill was a lead, and the answer's never-tried situation did not stand out |

### The honest repair (the user, 2026-10-28)

The half rule, everywhere, was found to be a slip (above), and fixed everywhere; three tests failed. Each was traced:
- **T79** (sadness on a lost slot) asserted the gate's grief, but the arm's push leaves the gate leaning: its grief came
  from the base rate drifting past its holding strength, as exploration happened to go (with the fix it formed with no
  push at all). Repaired: grief counted against a no-push control (runs are deterministic); the push's grief is on the
  bead (and the gate or the marble) under either rule.
- **T80** (the null world) shows the same collapse one window later: given 16 windows. Its ablation (one claimable stone)
  also goes quiet in time under either rule, which 12 windows had not reached: checked now as a comparison (still
  claiming while the null world collapses). Open, not a target: a held, understood region stops being pushed.
- **T71** (stage 4) fails on its runaway check in one more seed: decided by how often exploration presses the primer
  from the start (every such press bursts the tank; presses later in an episode, pooled in one reading until two
  outcomes each way allow a split, do not), and seed 0 had passed on an alphabetical tie (one burst, one not). Left
  failing rather than tuned.

### Later changes from other tracks

- **2026-10-30, the civilization ladder P6** (`../civilization/LADDER.md`): the planner's `mcts` ends a rollout at a state with no known action instead of crashing; and sub-wants (`Params.subwants`, `SovAgent.subwant`), **off by default**. Backup `../civilization/backup/molecules_2026-10-30/`. The suite before and after is 72/80, 2 pending, identical to the reference above.
- **2026-10-30, the civilization ladder P7:** with sub-wants on, a situation never tried that already holds is tried at once (`subwant` returns `("try", invitation)`) rather than another sub-want set. The suite is unchanged (72/80, 2 pending).
- **2026-10-30, the civilization ladder P8:** keeping (`Params.keep_subs`, off by default; `SovAgent.keep_watch`): a met sub-want is restored if another undoes it. It turned out redundant with sub-wants, which re-derive what is undone. Backup `../civilization/backup/molecules_2026-10-30b/`. The suite is unchanged.
- **2026-10-30, the civilization ladder P12:** grievance (`Params.grievance`, off by default, a per-mind trait). In `Territory.update`, a held region whose holding fades after something else moved it is `lost` (grieved) rather than `another` (conceded). Backup `../civilization/backup/molecules_2026-10-30c/`. The suite is unchanged.

## What changed in the code world (both arms)

- `gamma` and `renew()`, the two parts of ForceWorld's interface Gerundelle reads that a code world lacked.
- **A slot invites its fills whatever fills it now** (`CodeWorld.invitations`, `StmtWorld.invitations`). First the slot's
  state was the invitation's gerund, as a force world's: every change of state made every fill a new, untried action.
- **A fill reports what it governs**, the slots and roles, re-made or not (`CodeWorld.act`, `StmtWorld.act`). First only
  what differed: a fill that re-made the slot's state read as doing nothing, the same fill did something or nothing by what
  was there before, and Gerundelle studied the fills' "conditions" instead of running the spec.

The lean code mind's rung tables in LADDER.md were measured before these two changes: they need the rerun.

## Rung 0, both arms, the same world and orders (`arms0.py`)

| | lean | Gerundelle |
| --- | --- | --- |
| shuffled, 10 seeds: tries (median, range) | 120, 39-303 | **125, 46-157** |
| runs (median) | 7 | 6 |
| the answer last in the lean mind's order (rank 000), 3 seeds | 320 | 18 |
| the answer last in Gerundelle's order (rank 158), 3 seeds | 3 | 44, 42-185 |
| **each arm's own worst case** | **320** | **185** |
| time, 10 shuffled seeds | 75 s | 485 s |

Gerundelle at the start of the arm: 182 tries alphabetically, not reached in shuffled orders.

**Rung 0: competitive in the median, better in the worst case.** Its worst case is not a scan: Inquiry's leads (a
preparation that makes a situation the run was never tried in) single out the fill that fills the pattern's roles, the
only one that does; the lean mind has no counterpart, so its worst case is the full scan with its runs.

## Next

Rungs 1, 2, 4, 5b, 6, 7, 8, 9 on both arms (INCOMPLETE.md section 8, step 3); the lean rungs rerun on the current world
first. Gerundelle's time per run (about six times the lean mind's) is the cost to watch.
