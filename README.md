# Gerundelle

A formally verified architecture of mind. Twelve layers, from world physics to narrative,
machine-checked in Lean 4.

## What this is

**Gerundelle** is a twelve-layer architecture of mind whose promises are theorems. Its
layers run from a world that conserves its one physical quantity, through perception,
competition for attention, provenance of evidence, memory, understanding and self-awareness,
to ownership, affect, planning, social exchange and the selection of what is worth telling.

Each layer carries guarantees that a proof assistant (Lean 4) has checked for every possible
input, every possible sequence of operations, every possible interleaving. The development
comprises **24 files**, **301 theorems**, and **no unfinished proofs**.

### The twelve layers

| | Layer | Question it answers |
| --- | --- | --- |
| **The machine** | 1. World | A physics that conserves its one quantity |
| | 2. Perception | What the agent can distinguish |
| | 3. Competition | Scarce attention slots |
| | 4. Provenance | The difference between lived, told and imagined |
| **The cognition** | 5. Memory | Thoughts that settle and reopen |
| | 6. Understanding | Open questions with typed slots |
| | 7. Self-awareness | Detecting its own loops and confusion |
| **The will** | 8. Ownership | Territory: what the agent holds, contests and loses |
| | 9. Affect | Emotions read off the territory register |
| **The reach** | 10. Planning | Sub-wants, constraint convergence, the curriculum |
| | 11. Social | Attestation, trust, the discount |
| | 12. Selection | What is worth telling, and why |

The architecture is domain-independent: one mind and one algebra run in story, code, chess
and population worlds, with no domain-specific machinery. Only the world changes.

## The three ideas

**The world is a tree of doings.** Objects are described by what they are doing (gerunds),
not by what they are made of. A jar is *charged*. A boulder is *resting*. The world has no
coordinates. Where a configuration invites a force that has not been applied, the world has
an *open force slot*: the question "what would happen?" is itself a structure.

**Cognition is a market.** A mind is a marketplace whose scarce resource is commitment.
Hypotheses, patterns and wants compete for slots, and the competition is settled by evidence
from acting in the world. What the agent lived through counts in full, what it was told
counts at a discount, and what it imagined counts not at all.

**Ownership is the foundational motivation.** What the agent acts for is territory: whatever
it perceives as its own. Emotions are how this territory reads. Frustration is a claim that
keeps failing. Curiosity is an unclaimed region. Joy is a claim that took.

## Repository structure

```
formalization/          Lean 4 proofs (24 files, 301 theorems)
  SOV/                  The SOV algebra and its layers
  lakefile.lean         Build configuration
  lean-toolchain        Lean version

paper/                  The academic paper
  gerundelle.tex        LaTeX source
  refs.bib              Bibliography

book/                   Building Gerundelle (the book)
  section_*.json        Chapter sources
  appendix_*.json       Appendix sources
  preface.json          Preface
  figures/              13 figures (SVG + PNG)
  build_book.py         Print typesetter (ReportLab)
  build_epub.py         EPUB builder

writing/                The museum galleries
  galleries/            12 dream sequences, one per chapter

reference/              The reference implementation
  molecules.py          The thought-molecule tournament (3,852 lines)
  sov_agent.py          The SOV agent
  force_world.py        The force world
  curriculum_worlds.py  The curriculum

domains/                Domain-specific worlds and ladders
  fiction/              The fiction pipeline (rungs 0-7, both arms)
  cognitivecode/        The cognitive code ladder (rungs 0-8)
  cognitivechess/       The chess ladder (rungs 0-1c)
  civilization/         The civilization track (rungs P0-P5)
  embodied/             Embodied cognition (distinctiveness, recognition, grasping)
```

## Quick start

### Check the proofs

```bash
cd formalization
lake build
```

If it compiles, every theorem holds.

### Build the book

```bash
pip install reportlab pyphen pypdf svglib pymupdf
cd book
python build_book.py --out gerundelle.pdf
python build_epub.py
```

### Run a domain

```bash
# Fiction: Mara and the box
cd domains/fiction
python -X utf8 run_ladder.py --rung 0 --configs lean --ticks 300

# Code: the color line
cd domains/cognitivecode
python -X utf8 rung0.py

# Chess: the hanging piece
cd domains/cognitivechess
python -X utf8 rung0.py

# Civilization: the spring of light
cd domains/civilization
python -X utf8 p0.py
```

## The paper

**GERUNDELLE: A Formally Verified Architecture of Mind**
*Twelve Layers, from World Physics to Narrative, Machine-Checked in Lean 4*

Scott Seto. October 2026.

Three results:

1. **Every layer is verified.** From conservation of potential in the world to the
   well-foundedness of a told story.
2. **Six fields, one structure.** Information security, symmetry groups, fiber bundles,
   learning theory, graded monads, and provenance calculi — six areas of mathematics that
   rarely cite one another — describe the same architecture once stated about its operators.
3. **Seeing and feeling are one property.** Perception and affect are both factorization
   through a view. Same mathematical structure, two levels.

## The book

**The Museum of Gerundelle: A Cognitive Architecture of Competing Thought-Molecules,
Structured Ignorance, Territorial Ownership, Scarce Attention, and the Market Forces
That Drive a Mind to Learn, Explore, Grow, and Express Itself**

Scott D. Seto. 262 pages.

A computational laboratory manual, not a textbook. Each chapter follows the rhythm:
What If → Why → Possibility, with suggested experiments. Before each chapter, a dream
sequence takes the reader through one gallery of a museum where the chapter's concepts
exist as physical exhibits. The chapters name what the galleries showed.

## The domains

| Domain | What it tests | Rungs |
| --- | --- | --- |
| Fiction | A mind in a force world producing verified stories | 0-7, both arms, temperament |
| Code | A mind producing programs through constraint discovery | 0-8, composition, variation |
| Chess | A mind learning tactics from contrast and playing combinations | 0-1c, sub-wants, polarity, lookahead |
| Civilization | Populations of minds in worlds with configurable physics | P0-P5, voyages, told blueprints, populations |
| Embodied | Distinctiveness space, recognition, grasping | Recognition 28/30, constraint discovery |

## The formal guarantees

Seven theorems that prove the architecture's core promises:

1. **The imagination firewall** — nothing imagined reaches the funded web
2. **Imagined evidence is inert** — dropping imagined trials changes no owner
3. **Told evidence can't be promoted** — told-only evidence funds at most c₀ per trial
4. **Ownership is order-dependent, funding is order-free** — non-commutativity placed precisely
5. **Paradoxes are broke, not banned** — a self-citing entry is legal but unfundable
6. **Every valid curriculum is a geodesic** — each step adds exactly one concept
7. **The pull order** — lost > control > unclaimed, with the restless inversion proved

Seven lemmas that prove its boundaries:

8. **No outbound morphism exists** — funding can't be reconstructed from imagination
9. **The Lamarckian pairing is a grade error** — inherited knowledge can't be typed as lived
10. **Lived mass can't grow without a Fit** — only world interaction creates evidence
11. **Relabel is primitive** — no composite of meets produces it
12. **No global coordinates when holonomy is non-trivial** — structure is inherently local
13. **Accrual and eviction don't commute** — the precise boundary of confluence
14. **Perception is determined by invariance** — the Umwelt is the quotient by funded distinctions

## License

LGPL v2.1 (code, proofs, and reference implementation). See [LICENSE](LICENSE).

## Author

Scott Seto (ameritusweb@gmail.com)
