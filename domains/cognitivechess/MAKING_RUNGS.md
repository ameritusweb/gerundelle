# Making a rung

How the next rung of this ladder gets made. Invented 2026-11-01 (the user: "the tradition is to invent it"), from what
this ladder and the other tracks actually did, and meant to be revised the way a rung's named choices are: when using
it shows it wrong.

A rung is not picked from the plan or from a list of unused mechanisms. It is **made**, from the last rung's residue,
against the track's question. `chess-sov-plan.md`'s table is a sketch of where the ladder might go, not the order it
goes in.

## The track's question

From `README.md` and the user's decisions: **a chess player built from the SOV algebra on Gerundelle, the same mind as
fiction, cognitivecode and civilization.** So every rung asks one thing: *what does chess demand of this mind that it
cannot yet do, and what SOV structure answers it?* The answer has to be the architecture's, not chess's: no piece
values, no engine, no authored reward. Where chess needs something, Gerundelle should already have it, or earn it.

Two of the user's standing rules shape every rung:
- **The 15 relation forms enter one per rung**, opt-in (`../relations/RELATION_TYPES.md`). A rung that needs a form not
  yet in Gerundelle brings that form, and only that one.
- **Every change to Gerundelle is a `Params` switch, off by default**, backed up first and run against the suite.

## The steps

1. **Read the residue.** The last rung's findings and its "Not yet done", and what its traces showed. The residue is
   what the mind visibly *could not do*, measured, not what would be nice. Prefer the residue several findings keep
   returning to.
2. **Name the missing structure in Gerundelle's own terms.** A hole kind, a relation form, an ownership kind, a want,
   a phase, a reading. If it can't be named in the architecture's vocabulary, it isn't understood yet: trace more.
3. **Check what Gerundelle already has** (as `cognitivecode/GERUNDELLE_MAP.md` did): *covered* (an existing mechanism
   does it: use it, don't build), *partial* (exists, and chess shows the gap), *none* (new to the architecture). Read
   the code, not the docstrings: comments here lag the code.
4. **Make the smallest chess world where today's mind fails for want of exactly that structure.** One new demand on
   the last rung's world, the rest held fixed, so a failure has one cause. The failure must be real and measured
   first, with the structure off, before anything is built.
5. **State the question, the arms and the measures before running.** The question in one sentence; the arms (the
   structure off and on; controls such as a scripted opponent, a wrong book, a random mover); measures fixed in
   advance, read from what happened on the board, not only from what reached the mind (rung 3: the "wants met" count
   hid two thirds of White's wins).
6. **Build it the narrow way.** World changes opt-in in `chessworld.py` (earlier rungs unchanged, and checked to
   reproduce exactly); Gerundelle changes as a `Params` switch, backup, suite. Every choice named, with the failure
   that forced it.
7. **Run over seeds, with a fixed `PYTHONHASHSEED`.** Ten seeds; report totals and the spread; trace any seed that
   stalls or carries the result (rung 3: one seed was most of a "doubling").
8. **Write it up** in `LADDER.md` in the shared format: question, world, change, results, findings, not yet done. The
   "Not yet done" is the next rung's residue.

A rung is finished when its question has an answer with numbers, not when the mind succeeds. "The structure didn't
help, and here is why" is a finished rung.

## Finding residue early: the stress test (the user, 2026-11-01)

A rung's residue only shows what its own small world could pose. **Full games, played early, stress-test the mind**
against everything chess demands at once, and show what the next rungs might be before the ladder gets there. A
stress test is not a rung: it has no question to answer and nothing is built to pass it. It is run as the mind stands,
watched, and its failures sorted:
- **by kind**, in Gerundelle's terms (step 2): a missing structure, a pathology already met (coincidental sub-wants,
  fragmentation, loops), a world or speed problem;
- **by how often and how early** they stop play;
- **each one traced** to the mechanism, as for a rung's findings.

The sorted failures are candidate residue. Each one that becomes a rung is still built small (step 4): the full game
shows *what* to isolate, not where to test it. Rerun the stress test after a few rungs, to see which failures are gone
and which new ones show.

## Lettered rungs and sections

- **A section of the same rung** when a finding needs a fix to answer the *same* question (rung 1e's "want as mate
  without losing material", rung 3's schedule fix).
- **A lettered rung** (1b, 2b) when the same world needs a *new* question (1d: a move never tried; 2b: a world where
  being told pays).
- **A new number** when the demand is a new kind of thing chess asks of the mind, and the world must change to pose
  it.

## Where the results go

This file holds the method only. What using it produces goes elsewhere:
- a rung's write-up, and the next rung it proposes: `LADDER.md`;
- stress tests (full games): `STRESS_TESTS.md`, one dated section per run.
