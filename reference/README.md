# Reference implementation, versioned

- **`v1/`**: Gerundelle as of 2026-11-03. The fiction, code, chess and civilization domains run on it (their paths point here, or set `GERUNDELLE`).
- **`v2/`**: `molecules.py` and `sov_agent.py` with the switches added since, by the Warp chess work and the mystery maze (`domains/mysterymaze/LESSONS_LEARNED.md`, section 2). Every switch is off by default; with them off, `v2`'s suite matches `v1`'s (72/80, 2 pending). The mystery maze runs on it.

Each version runs its own suite: `cd v1 && python -X utf8 test_molecules.py` (likewise in `v2`), with `PYTHONHASHSEED=0`.
