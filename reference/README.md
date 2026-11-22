# Reference implementation, versioned

- **`v1/`**: Gerundelle as of 2026-11-03. The fiction, code, chess and civilization domains run on it (their paths point here, or set `GERUNDELLE`).
- **`v2/`**: `molecules.py` and `sov_agent.py` with the switches added since, by the Warp chess work and the mystery maze (`domains/mysterymaze/LESSONS_LEARNED.md`, section 2). Every switch is off by default; with them off, `v2`'s suite matches `v1`'s (72/80, 2 pending). The mystery maze runs on it.
- **`v3/`**: Gerundelle as of 2026-11-14, with what the tetris, Go and Warp chess work added. The tetris, Go and Warp chess domains run on it (`domains/<name>/paths.py`, or set `GERUNDELLE`).
  - **Switches**, every one off by default (each domain turns on its own): `force_predictions`, `anti_wants`, `decision_paths`, `meta_targets`, `dormancy`, `commit`, `concept_abstracts`, `held_evidence`, `affords_relation`, `reach_relations`, `transfer_tells`, `reach_claims`, `predicted_losses`, `commit_told`, `situational_told`, `no_loss_means`, `held_state_wants`, `tool_use`, `commit_waits_turn`, `dream_when_stuck`. One new temperament parameter, `aversion` (how strongly an anti-want pushes down what threatens it; 1.0). A world can also declare regions held only by reading (`read_held`) and regions no one can claim (`unclaimable`).
  - **Exact speed-ups**, no switch, each checked to give identical results: Abstract's core cut and caches, the planner's step, and the tournament's candidates.
  - **Optional Rust kernels** (`rust/gerundelle_fast/`): the same results, faster, when built and installed (`maturin build` in that folder); without them, or with `GERUNDELLE_PURE=1`, the Python runs.
  - With every switch off, `v3`'s suite matches `v1`'s and `v2`'s (72/80, 2 pending).

- **`v4/`**: Gerundelle as of 2026-11-18, with what the clean code, balance and cognitive chess v2 work added. The clean code and
  cognitive chess v2 domains run on it (`domains/<name>/paths.py`, or set `GERUNDELLE`).
  - **Switches**, every one off by default (each domain turns on its own): `meta_territory`, `anti_unbinds`, `reset_clears_plan`,
    `reconsider`, `tenacity`, `dreamed_conditions`, `faithful_choice`, `counted_pull`, `held_edges`, `abstract_grows`, `undo_loops`,
    `condition_subwants`, `dream_reach`, `dream_for_want`, `plan_asks_world`, `loop_unbinds`, `defense_still`, `explained_needs`
    (a need is one the mind's own record explains, never a conflation of what held), `patience_reach` (patience also counts slices a
    want is out of reach), `plan_as_pull` (a want's planned step pulls in the tournament instead of overriding it), `push_slots` (the
    pushes on offer in a lane of their own), `ask_once_here`, `defense_gains` (the felt defense counts gains as well as losses),
    `region_weights` (regions summed by the world's weights). Two temperament parameters: `experimentation` (how much at stake the
    mind sets aside to go on experimenting; unset, experiments go first as before) and `tenacity`.
  - A world can now say what a push would do to its territory (`effects_after`, read by `defense_still`) and what a region weighs
    (`region_weight`, read with `region_weights`).
  - Unchanged from `v3`: `force_world.py`, `forces/`, the Rust kernels (`rust/gerundelle_fast/`), and the other modules.
  - With every switch off, `v4`'s suite matches `v1`'s, `v2`'s and `v3`'s (72/80, 2 pending).

- **`v5/`**: Gerundelle as of 2026-11-22, with what the evidence campaign, the zodiac, codecraft and cognitive chess v2 work added.
  - **Switches**, every one off by default (each domain turns on its own):
    - wants and slots: `slot_bound_wants`, `control_spares_want`, `experiment_spares_want`, `starved_experiments_go`, `no_loss_wants`
    - felt territory: `held_losses_by_state`, `held_state_no_loss`, `contested_losses`, `new_region_gains`, `open_loss_blame`,
      `lived_loss_lessons` (each held region lost in a slice is a lesson, nothing lived thrown away)
    - improvement as territory: `improvement_territory`, `improvement_options` (the mind creates options that would improve it),
      `improvement_contests`, `improvement_retested`, `imagined_regions`
    - assumptions: `challenge_assumptions` (a loss the mind's own reading takes as forced is challenged with a tool)
    - exploration: `side_forces`, `unknown_slots` (a location never in view is its own kind of ownership slot, which pulls),
      `force_support`, `force_walks`, `plan_discovery`, `stack_pushes`
    - the watch and the meta layer: `others_not_caused`, `commit_facts_now`, `mode_same`, `split_keeps_boundary`
  - **Temperament parameters**, unset by default: `open_mindedness` (how far "assumed" safety is trusted), `thoroughness` (a tool
    search's budget), `anneal_rate` (SOV's Anneal), `watchfulness` (the watch before acting, apart from patience).
  - **Operator ablations**, on by default so every domain is unchanged; an ablation arm sets one off: `differentiate`, `retract`,
    `territory`.
  - A world can now also say: which contested regions count as losses (`contested_loss_regions`), what is a gain
    (`is_gain`, `gain_prefixes`), what it shows the mind (`shown`), its forces and locations (`forces`, `locations`, read by the
    exploration switches) and what an unknown would be seen as (`unknown_state`), what is in view (`view_reach`), regions held once
    reached (`held_once_reached`), a loss's kind relative to the last move (`lived_rel`), and `kind_of`, `games`.
  - Unchanged from `v4`: `force_world.py`, `forces/`, the Rust kernels (`rust/gerundelle_fast/`), and the other modules.
  - With every switch off, `v5`'s suite matches `v1`'s through `v4`'s (72/80, 2 pending; the same eight fail).

Each version runs its own suite: `cd v1 && python -X utf8 test_molecules.py` (likewise in `v2` and `v3`), with `PYTHONHASHSEED=0`.
