# Cognitive chess

A chess player built from the SOV algebra, on Gerundelle: the same mind as fiction, cognitivecode and civilization, in
the world of a chess board. The design is `../chess-sov-plan.md`; this folder is where it gets built.

**Decided by the user (2026-10-30):**
- **Gerundelle only** (`E:/vscode/analogy/molecules`, the copy fiction, cognitivecode and civilization use). No lean arm.
- **Sub-wants** (civilization P6, `Params.subwants`): the plan's combinations ("remove the defender, then take") are what
  a mind's own sub-wants are for.
- **The 15 relation forms** (`../relations/RELATION_TYPES.md`) enter Gerundelle **opt-in, one per rung**: a `Params`
  switch, off by default, so Gerundelle's suite and every other track run as before. Gerundelle already has two of them
  as a condition's polarity (`enables`, `prevents`).

**Discipline, inherited from the other tracks:** every change to Gerundelle is backed up first and run against its
suite (reference: `../cognitivecode/backup/fails_after_honest_repair.txt`, 72/80, 2 pending); results are reported over
seeded orders, never one run; every authored choice is named.

| File | What it is |
|---|---|
| `chessworld.py` | python-chess behind the interface Gerundelle reads; rung 0's puzzle (`RUNG0`) |
| `rung0.py` | rung 0: Gerundelle against plain enumeration and a random mover |
| `rung1.py` | rung 1: the defender; polarity and sub-wants, off and on |
| `rung1b.py` | rung 1b: lookahead; imagination from the rules or Stockfish |
| `rung1c.py` | rung 1c: a back rank, relations as objects; today's mind as the baseline |
| `rung1d.py` | rung 1d: constraints converging on a move never tried (`Params.support`) |
| `rung1e.py` | rung 1e: convergence in the agent's own choice (`Params.converge`) |
| `rung2.py` | rung 2: told knowledge, Stockfish as a coach; the bridge from constraints to sub-wants |
| `rung2b.py` | rung 2b: a world where being told pays (`Params.told_effects`) |
| `rung3.py` | rung 3: two minds on one board (`DuelWorld`; schedules `rounds` and `turns`) |
| `play.py` | play the mind in a tkinter window, with a live view of its thinking (`python -X utf8 play.py`; N self-play games first is a setting) |
| `experiments/` | checks behind the findings (traces, the code world's planner, what imagining minds learn, withdrawal) |
| `LADDER.md` | each rung, written up after it runs |
| `MAKING_RUNGS.md` | how the next rung is made (from the last rung's residue, against the track's question; stress tests) |
| `KNOWNS_AND_UNKNOWNS.md` | Gerundelle's principle (unknowns pull, knowns support), where the code departs from it, and the change that follows |
| `STRESS_TESTS.md` | full games played with the mind as it stands: what fails, sorted, as candidate residue (from 2026-11-01) |
| `HOW_IT_WORKS.md` | how the code fits together: world, agent tick, what the mind learns, the Params switches, a rung script |
| `backup/` | Gerundelle before this track's changes, and the suite logs after each |
