# The lean code mind's additions, mapped onto Gerundelle

Written 2026-10-27 (INCOMPLETE.md section 8, step 2), from reading `analogy/molecules/sov_agent.py` (`SovAgent`,
`Model`, `recall`, `contrast`, `conjunction`) and `molecules.py` (`Inquiry`, `Meta`, `Mind.contradict` and `reopen`,
`Territory`), as backed up in `backup/molecules_2026-10-27/`. Before the Gerundelle arm is made competitive: for each of
the fourteen mechanisms the lean code mind gained (INCOMPLETE.md section 2), what Gerundelle already has. **Covered**: an
existing mechanism does it (use that one). **Partial**: one exists, and the code world shows a gap in it. **None**: new
to the architecture. "Seen" marks what rung 0 on Gerundelle (first run, unchanged code) already showed.

Gerundelle's own vocabulary, for the table: a question is an SOV's open slot posed at the top of the tournament;
Inquiry turns it into **experiments** (molecules competing in their own track): `causes?c` do c; `conditions?c` change
something first, then do c (a two-step experiment, a preparation then c); `caused_by` do an untried action, or wait;
a push **unexplained** (conflated with no boundary) is retried after one or two ticks of waiting. The meta layer
**splits** a concept whose outcomes are bimodal on a boundary fact (the learned condition), **unifies** halves that
behave alike, and parks what is **stuck** or **looping**. The planner (`plan_step`) runs MCTS over the agent's own
`Model` once a want has a known way.

| # | Lean addition (rung) | In Gerundelle | Status | What the code arm needs |
| --- | --- | --- | --- | --- |
| 1 | Asking the way to a condition (1) | `consult` asks the conditions question once; a told condition becomes an experiment's preparation (`Inquiry.suggest`, `told_leads`): a push known to *cause* the told fact, else a push on the told fact's *object* | Partial | In code the told fact is a role, an object nothing pushes, and no fill is yet known to cause it: `told_leads` is empty and the preparations fall back to the first four changes. Gerundelle's own path closes it if the teller's Attest can carry a *causes* relation (fill causes role) as a told receipt; then `told_leads` finds it. No second question needed |
| 2 | Retracting a told way (2) | `SovAgent.watch`: a told way to the goal the world contradicts is refuted (`und.refuted`), the teller noted (`belied`; the phases read anger) | Covered (for a way to the goal) | Extend the same refutation to a told *causes* receipt for a condition, once 1 is in |
| 3 | Searching instead of waiting in a still world (2) | Conditions experiments are search: "change something first, then do c"; `await` is offered only when no push of the agent's makes the condition | Covered | — |
| 4 | Repeated runs not offered (rerun after 3) | Experiments decay with repeats (`q / (q + done)`); the meta layer parks stuck and looping *thoughts* (not experiments, not wants) | Partial | Seen: a fill and a run repeated in a row (two-step conditions experiments) |
| 5 | Inquiry gated in a still world (0) | `Inquiry.suggest`: a push *unexplained* is tried "after a wait of one or two ticks: what is left to vary is the moment" | Partial | The repeat-after-waiting experiment assumes the moment can differ. A still world (`CodeWorld.still`) should not suggest it: the same gap as the lean mind's, now in Inquiry itself |
| 6 | Credit to slots: claims pending until a run (3, 4) | `Territory.claimed`: a claim took if its region changed **and the predicted changes came** ("my push filled the slot and the predicted effect came"); with no prediction yet, a change is enough | Partial | The predicted-effect clause is the architecture's own version of "takes when tested", but a fill's first try has no prediction, so it takes on any change. Whether the run's outcome should be the prediction a fill is judged by (the want's region, as `SovAgent.own` already judges a push by the wanted object) is the question to settle in Gerundelle's terms |
| 7 | Reopen: a learned condition contradicted (4) | `Mind.contradict` reopens a closed box whose prediction failed (full surprise); the meta layer's `same` unifies a split whose halves behave alike; the planner reads expected reward per reading (modes), so a contradicted half stops being planned on | Covered, probably (by modes), unverified | Check on rung 4 whether a split condition contradicted by a spec change stops blocking the new answer |
| 8 | A keeper's way is what held at its reach (3) | The planner's `Model.step`: reward is the share of a reading's outcomes that brought the goal | Covered, probably | — |
| 9 | Episodes and recall by structure (5, 5b) | `SovAgent.recall` (Case 2 by shape): a past split's condition mapped onto the object now in the gerund the condition's object *left* (`was`); `Understanding.analogize` (shared sub-structures) | Partial | Gerundelle maps by state, not by name: closer to 5b's structural recall than the lean mind's first version. The code world gives it roles and slot states as its gerunds; whether that is enough is a rung 5b question |
| 10 | Test a pending fill first (6) | A conditions experiment is a preparation *and* the push it prepares (fill, then run) | Covered (structurally) | — |
| 11 | Told or recalled ways tried first (7) | `told_leads` come first among preparations (a skeptic tests alternatives beside the word: credulity); the planner believes a told way to the degree of credulity | Covered | — |
| 12 | Asking policy (7) | `consult` fires when the agent's own conditions question wins the top (the tournament decides when to ask) | Covered | Patterns as minds that answer (INCOMPLETE.md 3.6) |
| 13 | Varying a held way (8) | No counterpart: splits divide a concept by situation; nothing varies an action's structure | None | New in the architecture, if kept: a variation of an action as an experiment (Inquiry's track), not a list in `choose` |
| 14 | Recombining held ways (9) | `Understanding.analogize` maps shared sub-structures between concepts; nothing builds a new action from parts | None | As 13 |

Also present in Gerundelle and absent from the lean code mind:

- **A conjunction learner** (`SovAgent.conjunction`: a minimal hitting set of facts every failure lacked one of, held as
  nested splits). Rungs 7 and 9 never needed one (scope wiring joined the parts), but it exists, and fiction's lamp
  learned through it.
- **A planner** (`plan_step`, MCTS over `Model`): lookahead over the agent's own records, not over the world. INCOMPLETE.md
  3.1's "imagined runs" would be the interpreter as a forward model; Gerundelle's planner is the other kind (its own
  model of outcomes).
- **The meta layer** (stuck, looping, conflated, distinction, same, unexplained): what INCOMPLETE.md 3.2 says the lean mind
  replaced with gates.
- **Other minds' purpose** (`Territory.purpose`, `responsive` with a significance test, `relation_of`): perception of what
  another keeps doing, for rungs 3 and 6.

## What this says for the Gerundelle arm

Of fourteen additions, seven are covered by mechanisms Gerundelle already has (3, 8, 10, 11, 12, and probably 2 and 7),
five are partial (1, 4, 5, 6, 9), and two are new to the architecture (13, 14). The partial ones are where the code world
is likely to break Gerundelle first, in this order: **5** (waiting to vary the moment in a world with no moments: seen at
rung 0), **6** (what a claim on a slot is judged by), **4** (repeats), **1** (a told condition on a role), **9** (recall in
code's states). Each, as fiction's second pass did, would be fixed in Gerundelle's own terms and run against its suite.
