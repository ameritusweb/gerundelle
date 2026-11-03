# Civilization

A civilizational world model. Populations of SOV minds live in worlds whose physics is a parameter, and the civilization is whatever they produce there. The design comes from `../SOV_CIVILIZATIONS.md`. This folder is where it gets built.

**Status (2026-10-30): rungs P0-P14 built and run on Gerundelle** (`potential_world.py`, `moon_world.py`, `lock_world.py`, `p0.py`-`p14.py`; sub-wants, grievance and the planner fix in Gerundelle itself; results in [LADDER.md](LADDER.md)).

## Why this track

It answers what-if questions that had no principled answer before. What if warp travel worked? What if there were no sunlight? What if colonies were easy to found but communication was slow? Science fiction imagines these worlds, economists model pieces of them, and historians reason by analogy from Earth. Nobody has run minds in such a world and watched what they did.

The same setup as the other tracks: the mind and the algebra stay fixed, and only the world changes. A what-if is a pair of runs that differ only in physics. Every institution, conflict or technology that appears can be traced through provenance back to the constraint that produced it, so "why does this colony govern itself this way?" has an answer: a chain of funded receipts, not a designer's choice.

## Lessons inherited from the other tracks

These were each learned, often by failing first. Each is listed with what it means at civilization scale. Implications marked *(proposed)* are my reading and still need testing.

### From fiction (`../fiction/LADDER.md`)

1. **A slot nothing can answer captures the mind** (rung 0). The lean mind pulled on an unanswerable flag forever until a rule for unfillable slots was added. *(proposed)* At civilization scale this is belief nobody can test: the design doc's "religion" row. It needs the same rule, or the population ruminates.
2. **Emotions come from ownership, not from effect holes** (rung 0). Phases anchored on territory slots supplied curiosity, frustration and joy. History's emotional texture (revolutions where claims fail, golden ages where they take) should be read off territory, not written as rules.
3. **Motive comes from structure** (rung 3). Leo lied exactly when the asker wanted what he wanted and a true answer would hand the region over. No "liar" rule was needed. *(proposed)* Politics, deception and alliances should come out of wants and asymmetric knowledge in the same way, with no designed roles.
4. **Endings aren't authored** (rungs 4, 7). Who outlasts whom falls out of reserves and pulls, and doubling one reserve flipped an ending. Temperament is range, not bugs: different parameters make different people.
5. **Ownership stakes didn't change behavior** (rung 4). The territory register earned its place as perception (held, contested, lost), not as something that pays attention. *(proposed)* Re-test this at scale. A civilization may be where ownership finally has to pay, or the minimality result holds there too.
6. **History pays** (rung 5). Grief scales with what was held. Memory has reach. A grudge closes when the lost thing is held again, and that closing is what forgiveness is. Time cools what isn't refreshed, and storage needs the right clock. *(proposed)* This becomes generational memory: grudges between peoples, and heritage that cools.
7. **Transfer happens by shape** (rung 6). A recalled condition maps onto a new object by structure, is held at half, and is then confirmed by the mind's own tries. That's civilization rung 4: a technology carried to a new environment.
8. **Being told only matters where it saves search** (rung 2). In Gerundelle, told structure reached understanding but not action until it was given a path to experiments.

### From cognitivecode (`../cognitivecode/LADDER.md`, `INCOMPLETE.md`)

9. **Scarcity drives variety** (rung 8). Without scarcity no code varied anything. Variety came from pressure, not from a novelty bonus. This is civilization rung 0's prediction: specialization under scarcity.
10. **Output depends on history** (rung 9). A different telling order produced a different set of held programs. Civilizations will be path-dependent, so every what-if is reported as a range over orders and seeds, never as a single run.
11. **Contest needs a narrowed want** (rung 6). Contest after the frontier closed never fired, because codes wanting *any* passing program kept searching instead of fighting. Conflict (civilization rung 3) needs attachment: wanting *this* region, not just any.
12. **Run both arms from the start.** The code ladder ran on the lean mind alone, and its central claim is still untested because of that. Also: name every authored choice. Gerundelle is about 6× slower than the lean mind, which is a real cost at population scale.

### From the relation work (`../relations/`)

13. **The social relation forms belong here.** Six of the 15 forms (possession transfer, exchange, status transfer, communication, opposition, competition) had no real home in the force scenes. A village is made of them, so this track is where they get lived receipts.
14. **Store primitive and field, not flat labels.** A form discovered here (perhaps kinship, obligation or rule) should fit into the primitive × field table instead of being bolted on.

## How a what-if is run *(proposed)*

- **Paired runs.** Same population, same temperaments, same seeds; only the physics differs.
- **Ranges, not single runs** (lesson 10): many telling orders and seeds per arm.
- **The answer is the difference, with provenance.** Which institutions, technologies and conflicts appear in one world and not the other, each traced to the constraint behind it.
- **Discovered, not predicted.** Write predictions down before the run so a surprise counts as a surprise.

## The ladder (from `SOV_CIVILIZATIONS.md`, with the lessons each rung leans on)

**Updated 2026-10-29:** the physics comes first, generous before scarce. [PHYSICS.md](PHYSICS.md) adds rungs P0–P4 (forming, learning its condition, told blueprints, reaching space, and a population with no scarcity as the baseline). The rungs below follow once the scarcity knobs are turned.

| Rung | Question | World | Leans on |
|---|---|---|---|
| 0 | Does a population specialize under scarcity? | one village, several resources, exclusive claims | 9, 2, 13 |
| 1 | Does taught knowledge pass between generations? | two generations; the second starts with told receipts | 6, 8, 1 |
| 2 | Does trade emerge between populations with different funded conditions? | two villages, different resources | 13, 3 |
| 3 | Does conflict emerge over contested territory? | two villages, one scarce resource between them | 11, 4, 5 |
| 4 | Does a technology transfer to a new environment? | a village that moves, carrying conditions that may not hold | 7, 6 |
| 5 | Does culture diverge when communication is slow? | two villages, delayed communication, same start | 10, 6 |
| 6 | Does the civilization write fiction about itself? | the fiction pipeline on the civilization's history | 4, the printer |

Then the what-ifs themselves: Earth-like as the control, then warp speed, no solar radiation, easy colonization with slow communication, and hostile physics.

## Open decisions (not yet made)

- **Which mind.** Lean, Gerundelle, or both (lesson 12). Gerundelle's speed matters at population scale.
- **The world.** Extend fiction's `ScenicWorld` / ForceWorld interface, or build a new world with resources, geography and travel time.
- **Generations.** How minds are born, die and teach, and what a child inherits (told receipts, temperament, territory).
- **How physics is parameterized,** so that "no sunlight" is a change to the world's constraints, not a script.
- **Measures at civilization scale.** Specialization, trade volume, conflict, how knowledge lasts across generations, divergence between populations.
- **Which copy of Gerundelle.** `E:/vscode/analogy/molecules` (what fiction and cognitivecode use) or `embodied/gerundelle/molecules`. The two have diverged.

## Note on the design doc

The "What exists" section of `../SOV_CIVILIZATIONS.md` is out of date as of 2026-10-29. Fiction has gone well past 7 rungs (results through rung 24, the Gerundelle arm, temperament, social worlds). Cognitivecode has 10 rungs plus the Gerundelle arm at rung 0.
