# Reference implementation, versioned

- **`v1/`**: Gerundelle as of 2026-11-03. The fiction, code, chess and civilization domains run on it (their paths point here, or set `GERUNDELLE`).
- **`v2/`**: `molecules.py` and `sov_agent.py` with the switches added since, by the Warp chess work and the mystery maze (`domains/mysterymaze/LESSONS_LEARNED.md`, section 2). Every switch is off by default; with them off, `v2`'s suite matches `v1`'s (72/80, 2 pending). The mystery maze runs on it.
- **`v3/`**: Gerundelle as of 2026-11-14, with what the tetris, Go and Warp chess work added. The tetris, Go and Warp chess domains run on it (`domains/<name>/paths.py`, or set `GERUNDELLE`).
  - **Switches**, every one off by default (each domain turns on its own): `force_predictions`, `anti_wants`, `decision_paths`, `meta_targets`, `dormancy`, `commit`, `concept_abstracts`, `held_evidence`, `affords_relation`, `reach_relations`, `transfer_tells`, `reach_claims`, `predicted_losses`, `commit_told`, `situational_told`, `no_loss_means`, `held_state_wants`, `tool_use`, `commit_waits_turn`, `dream_when_stuck`. One new temperament parameter, `aversion` (how strongly an anti-want pushes down what threatens it; 1.0). A world can also declare regions held only by reading (`read_held`) and regions no one can claim (`unclaimable`).
  - **Exact speed-ups**, no switch, each checked to give identical results: Abstract's core cut and caches, the planner's step, and the tournament's candidates.
  - **Optional Rust kernels** (`rust/gerundelle_fast/`): the same results, faster, when built and installed (`maturin build` in that folder); without them, or with `GERUNDELLE_PURE=1`, the Python runs.
  - With every switch off, `v3`'s suite matches `v1`'s and `v2`'s (72/80, 2 pending).

Each version runs its own suite: `cd v1 && python -X utf8 test_molecules.py` (likewise in `v2` and `v3`), with `PYTHONHASHSEED=0`.
