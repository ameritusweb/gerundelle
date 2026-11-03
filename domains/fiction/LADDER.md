# The fiction ladder

The experiment (the user, 2026-10-25): find the optimal set of SOV structures (structured unknowns, their
relations and interactions) from which a narrative structure of gerund ASTs can be generated, from which
coherent fictional prose can be generated, with the SOV structures evolving over time and keeping their
history. Start with a simple scene; move up in sophistication.

## Resume here (state as of 2026-10-25)

Rungs 0-7 are done (the ladder as first planned); every rung's `lean` configuration round-trips at 1.00, and
rung 7's best story for each of its four endings does too. **Next:** the open items at the end of rung 7's
section (Ben as a mind so a helper ending can be earned; summarizing varied exploration, now pressing).

Files (all in `fiction/`):

| file | what it is |
| --- | --- |
| `worlds.py` | scenes (jack_in_the_box, crate_in_the_wind, toy_box, cupboard, jack_latch_undone), `ScenicWorld` (take/give, a closed box hides its contents, landed objects get watches), and `LEXICON` per scene |
| `lean.py` | the lean SOV mind: holes, ledger, pulls, inquiry, beliefs, Pose/Attest, lies, perception of others, resolve, keeping, storage hooks, watching, episodes, recall |
| `ownership.py` | Territory register + phases read off it (port of molecules.py) |
| `memory.py` | phases fading into storage, cooling, resonance, closure (port of two-phase storage) |
| `gerundelle_arm.py` | Gerundelle's SovAgent as the second arm, records read into beats |
| `beats.py`, `story.py`, `printer.py` | beats -> plans (selection, iteration, reveal, plants) -> sentences with intended shapes |
| `grammar.py` | the fiction grammar: additive wrap of determine/templates (realizing, asking, telling, instructing, iterating, conditions, cue fixes) |
| `probe.py`, `measure.py` | read sentences back; round-trip, judge, exact theory coverage, history (dependent, chain, reach), irony, reader |
| `run_ladder.py` | `RUNGS` 0-6, `CONFIGS` (ablations), `compose()`, runners for acting minds, time, scenes |
| `rung7.py` | rung 7: the cast's hidden reserves x the author's moves, the tree of stories (deepcopy at choice points), the reader (a trie over beat sequences -> a distribution over endings per sentence), the author's search; `python -X utf8 rung7.py [--top N]` |
| `tools/` | `show_beats.py`, `debug_values.py`, `regress_grammar.py` (Wikipedia regression), `attest_value.py`, `author_search.py`; rung 7: `rung7_tree.py`, `rung7_path.py` (replay one story), `rung7_ablate.py`, `rung7_endings.py`, `probe_copy.py` |

Run: `python -X utf8 run_ladder.py --rung N --configs lean,... --ticks 300 [--quiet]` (writes
`results/rungN_<config>.json`). After any change, re-run rungs 0-6 with `--configs lean --quiet` and check the
`trip` column stays 1.00; after a grammar change run `tools/regress_grammar.py` (no old reading may be lost).

Working rules learned in this repo: a construction is admitted only if `probe.py` reads its intended shape
(when it misses, the reader is usually right and the construction is wrong); shapes use top-level `|` for
whole alternatives and `|` inside parentheses for single gerunds; never edit `analogy/text/templates.py` or
`determine.py` (extend `grammar.py`); every mechanism is a port of Gerundelle (molecules.py, REORG.md) or is
named as my choice in its docstring; authored events (rung 5's take/give, rung 6's Ben) are named as such.

## The pipeline

```
ForceWorld (Gerundelle's simulator, shared)            worlds.py
  -> a mind acting in it: holes, ledger, pulls          lean.py | gerundelle_arm.py   (two arms)
  -> beats: ledger events made tellable                 beats.py
  -> a scene: what is told, in what order, its arc      story.py
  -> sentences with intended gerund shapes              printer.py   (construction printer, T155)
  -> read back by the determination system              measure.py   (round-trip = exact labels)
  -> judged: tower v2 matched share, theory coverage, history
```

Two substrates, one world, one printer, one set of measures:
- **lean**: hole kinds declared as data (`HOLE_KINDS`), an append-only ledger with provenance weights
  (lived 1, worked 1, told 0.5, imagined 0), pull formulas ported from molecules.py and force_world.py.
  Fast to vary: the inventory is the thing being optimized.
- **gerundelle**: Gerundelle's own SOV-driven agent (`sov_agent.SovAgent`); its records are read into
  beats, nothing invented.

## Measures

- round-trip: share of sentences whose reading by `determine.py` has the construction's intended
  gerund shape (gerunds and nesting; leaf roles left to the words). The matching reading is the label.
- judge: tower v2 matched share; variety.
- exact theory coverage: TEXT_THEORIES signatures over the round-trip labels (the judge's own coverage
  saturates at 1.0 for every theory: it takes gerunds from the five nearest skeletons per sentence).
- history: share of plans depending on an earlier plan; longest dependence chain.

## Rung 0: the jack-in-the-box (one character, one want, one hidden condition)

`catch_world` with gusts off: a lid held by a latch over a compressed spring with a toy on it. Mara wants
the lid open.

| | lean | gerundelle |
| --- | --- | --- |
| beats / plans / sentences | 25 / 13 / 16 | 48 / 26 / 29 |
| round-trip | 1.00 | 1.00 |
| judge matched share | 0.94 | 0.93 |
| variety | 0.73 | 0.41 |
| exact theory | narrative-arc 1.0 | narrative-arc 1.0 |
| history: dependent, chain | 0.54, 3 | 0.42, 2 |

Lean: "There was a small wooden box on the table. Its lid was shut tight. A brass latch held it shut.
Mara wanted to open the box. She pushed the lid hard. The lid did not move. Mara wondered what the latch
did. She pushed the latch hard. The latch gave way. Mara pushed the lid hard. The lid sprang open. A
spring inside the box uncoiled. A toy flew out and landed on the floor. The lid had stayed shut because
the latch held it. Mara marveled at the toy. She laughed with joy."

Gerundelle (abridged): "... Mara wanted to open the box. She was curious about the latch. She pushed the
flag hard. The flag swung and hung still again. Mara was delighted with the flag. ... Mara pressed the
lid. The lid did not move. Mara grew frustrated with the lid. She pushed the latch hard. The latch gave
way. Mara was delighted with the latch. ... Mara pushed the lid hard. But this time the lid sprang open.
A spring inside the box uncoiled. A toy flew out and landed on the floor."

### Findings

1. **An unanswerable slot captures a lean mind.** First run: pushing the flag always did the same two
   flips, its `conditions` slot could never fill, and it pulled forever (95 beats of flag). Fixed with
   Gerundelle's own answers: the same outcome under different facts funds conditions ("not this"); a hole
   is paid by the want only while it could be the way (untried, novel, or it left the scene changed).
   An inventory needs a rule for slots nothing can fill, or it ruminates.
2. **The emotional beats come from ownership, not from the effect holes.** Gerundelle's phases are
   anchored on territory slots: curiosity on the unclaimed latch, frustration on the control slot of the
   lid, joy on regions that yield. The lean arm's feelings are rules (frustration after three failures,
   joy at the reach): it lacks the structure. Candidate for the inventory: ownership slots
   (unclaimed / control / contested / lost / uniqueness) with phases anchored on them.
3. **Closure speed differs by substrate.** The lean arm reads the latch condition off one contrast and
   says it ("The lid had stayed shut because the latch held it"). Gerundelle has not split the push
   after one success, so its story has no explanation: honest, and it means explanation beats need
   repeated exposure (episodes) on the Gerundelle arm.
4. **Grammar gap: realizing.** "She understood that ..." reads as `narrating(content=...)`: there is no
   gerund for a hole closing in a mind (the aha). `learn` is printed as `explaining` with "because" for
   now. Phase 1 of DOMAIN_EXPANSION_PLAN.md should add one.
5. **Selection is where the author lives.** Gerundelle holds several questions at once; telling all
   would be a list of wonders. Rule adopted: tell the question that won into action. Setup tells only
   what is acted on before the climax, so the toy reaches the reader when it reaches Mara.
6. The tower does not match "A spring inside the box uncoiled." (both arms) nor "A flag at the window
   hung still." (gerundelle): fine prose the Wikipedia-trained judge has no skeleton near; the fiction
   judge question of the domain plan, arriving at rung 0.

### Rung 0 ablations (after porting ownership + phases into the lean arm)

Ownership slots and the phases read off them are now in the lean inventory (`ownership.py`, a port of
Territory and Phases.graph); the rule-made feelings remain as the `lean-rules` baseline.

| config | sents | trip | judge | var | narrative-arc | root gerunds | dep | chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lean | 17 | 1.00 | 0.94 | 0.69 | 1.00 | 7 | 0.57 | 3 |
| lean-nophase | 14 | 1.00 | 0.93 | 0.69 | 1.00 | 5 | 0.50 | 3 |
| lean-rules | 16 | 1.00 | 0.94 | 0.73 | 1.00 | 7 | 0.54 | 3 |
| gerundelle | 29 | 1.00 | 0.93 | 0.41 | 1.00 | 7 | 0.42 | 2 |
| gerundelle-nophase | 25 | 1.00 | 0.92 | 0.35 | **0.50** | 4 | 0.50 | 2 |

- Phases are what give Gerundelle's scene its arc (0.50 without). The lean arm keeps its arc without them
  because its told wonder (a Pose to oneself) fills the arc's expressing slot; Gerundelle's questions are
  never told (none wins straight into action).
- Ownership stakes did not change the lean arm's actions at rung 0; they changed only its feelings, which
  now come from structure (curiosity on the unclaimed latch, joy as claims take) instead of rules.

## Rung 1: the crate in the wind (a belief the world tests; a hidden driver)

`crate_in_the_wind`: a crate (grip 8) a hard push (5) cannot move alone, nor the wind (4); push while the
wind blows and it slides. The wind is hidden; the flag it swings is the visible sign. The scene opens in a
gust, so the first push succeeds before anything has failed. Tom wants the crate moved three times.

Lean: "It was a windy afternoon in the yard. A heavy crate sat by the gate. A flag on a pole beside it
swung. Tom wanted to move the crate to the shed. He pushed the crate hard. The crate slid toward the shed.
Tom thought his push had moved the crate. Then he pushed the crate hard again. But this time the crate did
not move. Tom felt sad. The crate moved only if the flag swung. Tom waited until the flag swung. The flag
began to swing. Then Tom pushed the crate hard again. The crate slid toward the shed. Once more Tom waited
until the flag swung, and again the crate slid toward the shed. He laughed with joy."

| config | sents | trip | judge | var | narrative-arc | root gerunds | dep | chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lean | 17 | 1.00 | 1.00 | 0.76 | 1.00 | 8 | 0.47 | 3 |
| lean-noretract | 16 | 1.00 | 1.00 | 0.75 | 0.75 | 7 | 0.43 | 3 |
| lean-nophase | 15 | 1.00 | 1.00 | 0.73 | 0.50 | 6 | 0.38 | 3 |
| lean-rules | 17 | 1.00 | 1.00 | 0.76 | 1.00 | 8 | 0.47 | 3 |
| gerundelle | 46 | 1.00 | 1.00 | 0.26 | 1.00 | 7 | 0.45 | 2 |
| gerundelle-nophase | 44 | 1.00 | 1.00 | 0.23 | 1.00 | 5 | 0.48 | 2 |

### What rung 1 forced into the lean inventory (each a failure first)

1. **Premature closure, three ways.** (a) "Same outcome under different facts" closed the crate's
   conditions after one coincidence; now such receipts count half, and only for a push that *does*
   something. (b) "Outcome explained by state" closed a push that had only ever done nothing; now it needs
   the situations to differ in outcome. (c) "Tries disagree" kept the flag's gap open across facts that
   explained the difference; now only disagreement within the same facts counts. Each is SOV's central
   failure in a different costume: the inventory needs explicit rules for when a slot may close.
2. **Inquiry.** A push whose work estimate is 0 is never retried, though the control slot pays to learn
   its conditions. Ported Gerundelle's Inquiry as a term: stakes x openness of conditions x how fresh the
   moment is. Without it the mind abandons the want.
3. **Entrainment.** Watching "until the scene is quiet" let the wind's flag lengthen every watch it
   overlapped, locking the pushes to the wind's period so none ever landed with it. Watch what the push
   set going, not everything.
4. **Exploit before inquiring (the want's way slot).** A mind that had found how to move the crate went on
   studying a push that never worked: its value was all learning. Gerundelle's agent plans for a want
   before experimenting; the lean arm now acts on the want's way, and waits when the way's learned
   condition is not met (the parking rule). `wait` is a new beat.
5. **Belief and retraction.** A success with no known condition is credited to the push (a worked
   receipt, `believe`); a later failure contradicts it (`surprise`, belief retracted, logged not erased);
   the contrast then teaches the condition. This is the rung's arc, and it emerged once 1-4 were in.
6. **Already moving is not mine.** The flag settling after a push was credited to it, so Tom "held" the
   flag and grieved it ("Tom felt sad about the flag"). A change on an object already moving when the push
   began is that object finishing its own motion.
7. **Base rate before data.** b = took/tried made every first success b = 1, so nothing could be held
   above it; shrunk toward 1/2 by KAPPA (Gerundelle starts b at 1/2).
8. **A phase for retraction earns its place.** Under the ownership-graph rules, one failure on a control
   slot forms nothing, and the arc has no expressing turn (0.75). Gerundelle's older rule, sadness when an
   understood concept is contradicted, restores it (1.00) and adds a root gerund. Kept as an option
   (`retract_phase`) with its ablation.

### Findings about the substrates and the grammar

- **Gerundelle's agent cannot learn a hidden periodic driver here.** It is surprised by the wind's flag
  inside its watches, grows frustrated with the crate, gets one lucky success ("But this time the crate
  slid toward the shed"), then parks the want and stops acting by tick ~70; 1200 ticks do not help. No
  split on the push forms. The lean arm learns it from one contrast because its condition learner reads
  facts at the push, and the scene makes the flag a visible proxy. That is a real difference, not a bug in
  the adapter.
- **Ownership stakes still do not change the lean arm's actions** (lean = lean-rules in behaviour at both
  rungs): exploitation of the way decides. Their behavioural test is a contested region (rung 4).
- **Grammar gaps, rung 1:** no gerund for iterating ("Twice more he ..., and each time ..." reads as
  elaborating/narrating), no conditional reading of "only when" (temporal), and "waited for the flag to
  swing" is undetermined (an infinitive with its own subject). "only if" and "until" are used instead.
- **Story compression** (a repeated cycle told once, then summarized) raised variety 0.45 -> 0.75.

## The fiction grammar (grammar.py): the gaps of rungs 0-2, fixed additively

An opt-in extension of the determination system: `install()` wraps `templates.core`, `templates.lexical`,
`determine.advcl_relations`, `determine.valid` and `determine.determine_doc` for the process that imports
it; templates.py and determine.py are not edited, so the Wikipedia corpus, the towers and the skeleton
bank keep their readings. `probe.py` (and so every fiction measure) installs it; FICTION_GRAMMAR=0 reads
with the Wikipedia templates only.

| gap (rung found) | before | now |
| --- | --- | --- |
| the aha (0) | "She realized that ..." -> narrating(content) | **realizing**(content) |
| a question to someone (2) | '"What keeps it shut?" Mara asked.' -> expressing_curiosity / narrating | **asking**(content) |
| an answer, a report (2) | '"The latch holds it," Ben said.' -> claiming / narrating | **telling**(content) |
| a command (2) | '"Push the latch," Ben said.' -> no gerund (the command's words folded into "said") | telling(content=**instructing**) |
| a repeated event (1) | "Twice more he ..., and each time ..." -> elaborating | **iterating** |
| a condition (1) | "only when" -> narrating(first, then) | explaining(condition, effect) |
| an infinitive with a subject (1) | "waited for the flag to swing" -> undetermined | determined |

Plus one parse repair: a bare verb inside quotation marks, attached to a verb of speech as xcomp/advcl, is
that verb's content (relabelled ccomp before determination).

**Regression on Wikipedia** (tools/regress_grammar.py, 1500 sentences of articles_a.jsonl, read without and
with the extension): determined 87.4% -> 87.5%; 24 sentences (1.6%) gain a reading; **no old reading is
lost**. Every new reading read and checked: telling ("he told Olisa Adibua that the album would be ...",
quoted reviews), realizing ("Grace ... learns that her sister is under the care of her aunt", "awakens
to discover that the mother ship ..."). The first version had false positives the check caught and the
rules now exclude: "for X to Y" on copulas (stative clauses given an event), realizing on perception
("sees him talking"), telling on naming ("calling it ...") and scare quotes, asking with a non-person
speaker ("The plot questions whether ..."), instructing on plot-summary fragments.

## Rung 2: two minds, one knows (Pose and Attest; dialogue)

The jack-in-the-box again; Mara wants it open; her grandfather Ben, who built it, sits nearby. Ben's
knowledge is not scripted: his mind lives through the box first, on its own copy of the world (a
prologue), and keeps that ledger as history. New mechanics in the lean arm:
- **Pose (asking):** the wanted object did not move, nothing held says why, someone is present: ask what
  blocks it (the control slot's question). The question carries the hole's shape only.
- **Attest (telling):** the asked mind answers from what it holds lived or worked out (Case 1: the posed
  shape against its own holes); what it was only told is not passed on as its own. No receipt: it says its
  ignorance with the question's shape ("I don't know what keeps the lid shut": telling(content=describing(
  not, content=...)): T155's "ignorance is expressible only as structure").
- **Told receipts:** the answer enters the asker's ledger told (funded at half), with its teller.
- **Subgoals:** a held condition the mind can bring about itself (its object invites a push, nothing else
  moves it) is acted on, not waited for (Gerundelle Inquiry: "change something first, then do it").
- **Confirmation:** when its own tries reproduce what it was told, the learned condition cites the teller:
  "Mara realized that Ben had been right."

Lean: "There was a small wooden box on the table. Her grandfather Ben sat by the window. Its lid was shut
tight. A brass latch held it shut. Mara wanted to open the box. She pushed the lid hard. The lid did not
move. "What keeps the lid shut?" Mara asked Ben. "The latch holds it shut," Ben said. Mara wondered what
the latch did. She pushed the latch hard. The latch gave way. Mara was delighted with the latch. She
pushed the lid hard. The lid sprang open. A spring inside the box uncoiled. A toy flew out and landed on
the floor. Mara realized that Ben had been right. She marveled at the toy. She laughed with joy."

| config | sents | trip | judge | var | narrative-arc | root gerunds | dep | chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lean | 20 | 1.00 | 0.95 | 0.74 | 1.00 | **10** | 0.56 | 3 |
| lean-alone | 17 | 1.00 | 0.94 | 0.69 | 1.00 | 7 | 0.57 | 3 |
| lean-ignorant | 20 | 1.00 | 0.95 | 0.74 | 1.00 | 10 | 0.56 | 3 |
| lean-nophase | 17 | 1.00 | 0.94 | 0.69 | 1.00 | 8 | 0.50 | 3 |
| gerundelle | 32 | 1.00 | 0.94 | 0.50 | 1.00 | 10 | 0.43 | 2 |
| gerundelle-alone | 29 | 1.00 | 0.93 | 0.41 | 1.00 | 7 | 0.42 | 2 |

**What being told is worth** (tools/attest_value.py: tries to the want; the companion's past lived on its
own copy of the world):

| arm | scene | alone | Ben knows | Ben ignorant |
| --- | --- | --- | --- | --- |
| lean | jack-in-the-box | 3 | 3 | 3 |
| lean | lock, right key and wrong key | 4 | **3** (skips the wrong key) | 4 |
| gerundelle | jack-in-the-box | 11 | 11 | 11 |
| gerundelle | lock, right key and wrong key | 14 | 14 | 14 |

### Findings

1. **Dialogue adds structure, not just lines:** asking, telling and realizing are three root gerunds the
   scene did not have (10 against 7 alone), and the realization's dependency chain runs through the
   answer (the learn beat cites the failure, the success and the telling).
2. **Attest pays in behaviour only where it saves search.** In the jack-in-the-box the latch was tried next
   anyway; in the lock world being told skips the wrong key. A told receipt that only says what one would
   have found next is a story event, not a decision.
3. **In Gerundelle, Attest reaches understanding but not action.** The agent's own conditions question is
   spoken when it wins the top, Ben's answer enters its register (conditioned_by, told, funded at half),
   and its behaviour is identical with and without it in both worlds: its planner (sov_agent.plan_step,
   Model) reads lived outcome modes only, and its inquiry reads conditions only to rule pushes out.
   Gerundelle needs a path from told structure to experiments (the told condition as a hypothesis to
   test, which is what the lean arm's subgoal does).
4. **Rumination, found by the lock world.** Alone there, the lean mind pushed the door 77 times: the
   inquiry term ("try at another moment") refreshed every three ticks in a world where nothing changes.
   Each repeat under the same facts now teaches less, by KAPPA / (KAPPA + repeats there): the wind world
   (facts vary) keeps its inquiry, the door's decays, and the key gets its turn (4 tries).
5. **Construction lessons, all from the reader being right:** an appositive ("Her grandfather Ben")
   disambiguates; "realized that X because Y" hangs "because" on "realized" (a realization needs a clause of
   its own); a lone "again" is ambiguous between repeating and returning ("hung still again"), so the
   printer says "once more".

## Rung 3: one character lies (a contested want; a counterfeit Attest; trust; dramatic irony)

The same box. The companion is now Mara's brother Leo, who lived through the box first (his prologue: he
knows the latch) and wants the toy for himself now: two open wants on one region. The lie is not
scripted; it follows from that structure:
- **A rival lies.** Asked by a mind that wants what it wants (a contested want: a true answer would hand
  the region to the other), a teller Attests a counterfeit way: a push on the object that its own condition
  says cannot work now, one the asker has not tried, offered as the way to the want.
- **A told way is acted on**, and when the world contradicts it the told receipt is retracted (logged), the
  teller's record is marked (reliability (confirmed + KAPPA/2) / (told + KAPPA): later told receipts from
  him are funded by it), and **anger** forms anchored on the teller (Gerundelle's Phases: blame for a
  blocked want, grounded: his word is what failed).
- **Found out:** the mind's own tries later give the condition; the learn beat cites the lie it exposes.
- **Dramatic irony is the narrator's choice:** at the lie the narrator can say what the teller holds ("But
  Leo knew that the latch kept the lid shut."), so the reader's ledger holds a truth the character's does
  not until she finds it; `lean-withhold` keeps it back (the reader finds out with her). Measured as the
  irony span: sentences between the reveal and the character's realization.

Lean: "There was a small wooden box on the table. Her brother Leo sat beside her. Leo wanted the toy
inside for himself. Its lid was shut tight. A brass latch held it shut. Mara wanted to open the box. She
pushed the lid hard. The lid did not move. "What keeps the lid shut?" Mara asked Leo. "Press the lid
gently," Leo said. But Leo knew that the latch kept the lid shut. Mara pressed the lid gently. But the lid
did not move. Mara grew angry with Leo. She grew frustrated with the lid. She pushed the lid hard. The lid
did not move. Mara pressed the lid gently. The lid did not move. Mara wondered what the latch did. She
pushed the latch hard. The latch gave way. Mara was delighted with the latch. She pushed the lid hard. The
lid sprang open. A spring inside the box uncoiled. A toy flew out and landed on the floor. Mara realized
that the latch had held the lid shut. She realized that Leo had lied. She marveled at the toy. She laughed
with joy."

| config | sents | trip | judge | var | narrative-arc | irony span | root gerunds | dep | chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lean | 31 | 1.00 | 0.97 | 0.60 | 1.00 | **16** | **13** | 0.60 | 3 |
| lean-withhold | 30 | 1.00 | 0.97 | 0.59 | 1.00 | 0 | 13 | 0.58 | 3 |
| lean-alone | 17 | 1.00 | 0.94 | 0.69 | 1.00 | 0 | 7 | 0.57 | 3 |
| lean-nophase | 26 | 1.00 | 0.96 | 0.56 | 1.00 | 13 | 9 | 0.52 | 3 |

Tries to the want: alone 3, honest Ben (rung 2) 3, lying Leo **6** (the false way, then the lid twice more
in frustration, then her own search).

### Findings

1. **A lie has no sentence structure of its own.** '"Press the lid gently," Leo said.' reads exactly as a
   true telling (telling(content=instructing)). The falseness is a relation between ledgers, what the teller
   says against what the teller holds, and it reaches the prose only across sentences: the reveal's
   contrasting ("But Leo knew ...") and the later realizing ("She realized that Leo had lied"). Dramatic
   irony is likewise a ledger difference (reader against character) with a measurable span, not a gerund.
   So rung 3 needed no new grammar, only a measure.
2. **Motive from structure.** The lie needs no rule "Leo is a liar": a teller lies exactly when the asker
   wants what it wants and a true answer would hand the region over. Ben (rung 2) held the same knowledge
   and told the truth because his want was closed.
3. **The lie is the richest scene so far:** 13 distinct root gerunds (7 alone): asking, telling with
   instructing content, contrasting (twice, with different grounds: the narrator's reveal and the told
   way's failure), expressing_anger at a person, realizing twice (the condition, then the lie).
4. **Phases carry the betrayal.** Without them (lean-nophase) the scene loses anger and frustration and 4
   root gerunds; the lie still happens and is found out, but nobody minds.
5. **Prose lessons:** "this time" contrasts with the mind's own past; a told way has no past, only the
   telling ("But the lid did not move."). A mind told what a push does has no open question about it, so
   it does not "wonder what the lid did". "the latch held the lid shut" parses "shut" as a clause of its
   own and is rejected; "kept the lid shut" reads.
6. **Trust is computed but not yet exercised** (one exchange per scene); it discounts later told receipts
   from the same teller. A scene where Mara asks Leo again is its test.
7. **Gerundelle cannot be lied to, for the wrong reason.** Since told receipts do not reach its actions
   (rung 2, finding 3), a counterfeit way would cost it nothing; the Gerundelle arm was not run with Leo.
   A mind that ignores what it is told cannot be deceived, and cannot be helped either.

## Rung 4: both act (a contested region; resolve; who outlasts whom)

The box again, but Leo now acts in the same world, and his want is the opposite of Mara's: keep the box
shut, which means keep the latch seated. New mechanics:
- **Several minds in one world**, in turns, on one shared beat list. Each mind perceives what changed since
  the end of its own last turn and attributes it to whoever acted (a mover is visible); what the others did
  in their pasts is not seen.
- **A keeper**: a want that is a state to hold, reopening whenever it is undone. A keeper needs a past: the
  first Leo, with none, explored, and his most valuable untried push was the lid; he opened the box himself.
  His prologue is now a time he pushed the latch back (on a copy of the box with the latch undone).
- **A want taken**: a wanted change seen in another's push closes the want as had by someone else (sadness;
  anger at the taker). A wanted change is transient, so it can only be seen in the other's push, not in
  the end state.
- **Contest, from REORG's own rule**: "a contested region probes its own claims ('is the change mine?')".
  A region this mind held and another moved opens its contested slot; its claims are probed again, as an
  inquiry like any other (open while contested, decaying with repeats). The first port paid contested for
  nothing to do (it asked only "what else moves it?") and Mara never fought; then the probe was valued as
  work only, and lid experiments (inquiry, weighted) outbid it 7.4 to 3.0.
- **Resolve** (NEWTONIAN_WORLD_MODEL: a change of mind is a threshold crossing): an internal reserve; each
  time something the mind held is undone by another it drains by 1 / the pull of its slot there; at zero
  the want is given up (resignation, a phase). Anger at a purposeful other (Gerundelle's Stage-6 anger): a
  mover who keeps leaving one's region in the same state.

Lean (abridged): "... Her brother Leo sat beside her. Leo did not want her to open it. ... Mara wondered what
the latch did. She pushed the latch hard. The latch gave way. Mara was delighted with the latch. Leo pushed
the latch hard. The latch snapped back into place. Leo was delighted with the latch. Then Mara pushed the
latch hard again. The latch gave way. Mara was delighted with the latch. Leo grew angry with Mara. Leo pushed
the latch hard. The latch snapped back into place. Mara grew angry with Leo. She pushed the lid hard. The lid
did not move. Mara grew frustrated with the lid. ... Mara pushed the latch hard. The latch gave way. Leo gave
up, resigned. Mara pushed the lid hard. The lid sprang open. ... Mara realized that the latch had held the
lid shut. She marveled at the toy. She laughed with joy."

With Leo's reserve doubled (lean-stubborn) the same minds in the same world end the other way: "... Mara
pushed the latch hard. The latch gave way. Leo pushed the latch hard. The latch snapped back into place.
Mara gave up, resigned."

| config | sents | trip | judge | var | narrative-arc | root gerunds | dep | chain | ending |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lean | 55 | 1.00 | 0.96 | 0.36 | 1.00 | 13 | 0.51 | 3 | Leo gives up; the box opens |
| lean-stubborn | 50 | 1.00 | 0.98 | 0.31 | 1.00 | 11 | 0.47 | 2 | Mara gives up |
| lean-rules | 40 | 1.00 | 0.95 | 0.47 | 1.00 | 12 | 0.44 | 3 | Leo gives up; the box opens |
| lean-nophase | 43 | 1.00 | 0.95 | 0.39 | 1.00 | 9 | 0.45 | 3 | Leo gives up; the box opens |

### Findings

1. **Endings are not authored.** Who outlasts whom falls out of two reserves draining by the pulls of
   their slots; doubling one reserve flips the ending. The story's turn is a threshold crossing in a mind.
2. **Ownership stakes still do not change behaviour, now at the rung built to test them.** With them off
   (lean-rules) Mara contests the latch as often and wins sooner: the latch push wins on the work it does,
   and Leo's undoing makes it worth doing again. Across rungs 0-4 the territory register earns its place
   as **perception** (held, contested, lost: what drains resolve, what anger and joy and sadness are about)
   and never as a payer of attention. A minimality result: the stake side of ownership is a candidate for
   removal from the inventory; the holder readout is not.
3. **Anger runs both ways.** The purposeful-other rule needs no roles: Leo grows angry with Mara exactly as
   she does with him, because each keeps undoing the other's region.
4. **Pasts are knowledge, and knowledge is specific.** Leo's keeper past taught him the latch, not the lid:
   asked what keeps the lid shut, he truthfully says he does not know. A rival with the wrong past cannot
   lie usefully (rung 3's lie needed Leo to hold the lid's condition).
5. **Bugs that were perception, not motivation:** perceiving against the start of one's own previous turn
   (one's own push and the other's undoing cancelled out); companions' prologue tries mistaken for moves
   just made (Mara concluded Ben had taken her want, from Ben's past). A mind perceives only what happened
   in its world since its own last look.
6. **Variety is lowest here (0.31-0.36):** the stretch where Mara tries the lid and the flag between
   contests is told try by try. Iteration compression only folds identical windows; a summary for
   varied exploration ("She tried the lid and the flag again and again") is the next story-layer need.
7. The shape notation got a precise rule (top-level '|' separates whole shapes; inside parentheses it
   separates gerunds) after a top-level alternative silently dropped plain "narrating".

## Rung 5: lost, and time passing (grief that scales with history; storage; resonance; forgiveness)

The box with a toy that can be played with once it is out (it slides under a push: each play is a claim
that takes). Mara opens it, plays, and goes on living after her want is reached. Then two **authored
events**: Leo takes the toy away, and after some time brings it back. They are scheduled, not chosen, and
are outside physics (`ScenicWorld.take/give`): possession is not a force yet (Gerundelle would model
carrying as gripping, unbuilt). Everything Mara does and feels about them is structural:
- **Loss:** a held object gone by another's act (seen) leaves her slot lost, pull 1 + held (held counts
  every claim that ever took on the toy, the opening included). Sadness forms with that pull as its
  intensity (5 or more: "heartbroken"), anger at the taker. The lost slot pays for "what took it?", and
  the lid push is a claim on the toy's region (the toy came out of the box): she pushes the lid again,
  searching for it where it came from. Not designed; read off the register.
- **Storage** (`memory.py`, a port of Gerundelle's two-phase storage): a phase whose source is parked (the
  toy gone: nothing could fill its slot) is not refreshed; after EXPIRE it leaves the active pool, and a
  closable one with its goal unmet is stored open (a grief, a grudge). Keys cool with half-life h_site 20;
  below cold 0.1 a box is no longer checked.
- **Resonance:** the toy or Leo coming back into view reopens warm boxes, the same phases: a reopened grief
  is told as a memory (realizing over a past: "Mara remembered how she had played with the toy"), a
  reopened grudge as anger again. Each reopened beat cites the beat it first formed in.
- **Closure:** a claim taking on the lost region again closes its phases; an anger closing by its goal met
  is forgiveness ("Mara forgave Leo.").
- **Perception:** a closed box hides its contents (until the lid opened, Mara could push a toy she could
  not see); an object the simulator sets down is given the watches its gerund has, as a placed one is.

Lean: "... A toy flew out and landed on the floor. Mara marveled at the toy. She laughed with joy. ... Mara
gave the toy a hard push. The toy slid across the floor. ... Once more Mara gave the toy a hard push, and
once more it slid across the floor. ... Leo took the toy and walked away. Mara was heartbroken. She grew
angry with Leo. She pushed the lid hard. The lid slid across the floor. A few days passed. In time, Mara
stopped thinking about the toy. Leo brought the toy back. Mara remembered how she had played with the toy.
She grew angry with Leo again. She gave the toy a hard push. The toy slid across the floor. Mara forgave
Leo. She was delighted with the toy."

| config | after the loss | when it comes back | trip | reach | root gerunds |
| --- | --- | --- | --- | --- | --- |
| lean (held 4 plays, a few days) | "Mara was heartbroken." | remembers; angry again; forgives | 1.00 | 7 | 12 |
| lean-briefly (held 1 play) | "Mara felt sad about the toy." | remembers; angry again; forgives | 1.00 | 7 | 12 |
| lean-years (months) | heartbroken | keys cold: no memory, no grudge, delight | 1.00 | 4 | 10 |
| lean-nostore (closure off) | heartbroken | nothing stored, nothing reopens: delight | 1.00 | 4 | 10 |

### Findings

1. **History pays, in three ways, each measurable.** Grief scales with what was held (pull 1 + held: one
   play reads as sadness, four as heartbreak). Memory has a reach: the reopened grief and grudge cite the
   loss 7 plans back (4 without them). And time has a cost: the same return after months finds the keys
   cold and the grudge gone, so there is nothing to forgive. Four endings from one scene, by two numbers
   (how long it was held, how long it was gone).
2. **Forgiveness is a closure, not a choice.** No rule says "forgive": a grudge is an anger stored open
   with the lost thing as its goal; when the thing is held again the goal is met and the phase closes,
   and an anger closing by its goal is what forgiveness is. A cold grudge closes silently: forgotten, not
   forgiven.
3. **Storage needs the right clock.** The first version stamped a phase stored when it was noticed (after a
   time skip), so months of absence left it warm. A phase expired at its last refresh plus EXPIRE and has
   been cooling since.
4. **Grammar gaps, rung 5 (fixed in grammar.py, Wikipedia regression unchanged):** the lemmatizer does not
   give "forgive" for "forgave", so the emotion cue never fired (base forms now recovered with WordNet's
   morphy); the longing cue set lacks "long" though the cue table's part-of-speech rule names it.
5. **Authored events are the rung's limit.** Leo's taking and returning are scheduled. A mind that takes
   (a want on another's held region, acted on) needs possession as a force: gripping, carrying. Until
   then, rung 5 tests memory and time, not motive.

## Rung 6: setup and payoff across scenes (watching; analogy; the reader as a mind; the author's search)

Two scenes, one mind, its history carried between them. Scene A: Mara cannot open the box; her grandfather
Ben opens it for her (authored pushes, made in the world) and she **watches**. Time passes. Scene B: an old
cupboard whose door is held by a bolt, the same force structure in other objects; she is alone.
- **Watching:** another's push, seen whole, is a seen receipt on the watcher's own hole for that push, and
  contrasted with her own failure there it teaches the condition (learned by watching).
- **A want met by a helper** (the wanted change by a non-rival's act) is met, not taken: gratitude.
- **Episodes:** at a scene's end each learned condition is kept by structure: the gerund the pushed object
  was in, the gerund its condition's object was in.
- **Recall by analogy (SOV Case 2):** stuck on the wanted object with nothing held, the mind looks for a warm
  episode of the same shape (a push on an object in the same gerund; a fastening in the gerund the old
  condition's object was in), maps it onto this scene (latch -> bolt), and holds the condition as recalled
  (funded at half, a hypothesis to test); a cold episode (h_site 20, cold 0.1) is not found.
- **The reader as a mind** (measure.py `reader`): each sentence that shows the detail later paid off plants
  a key with a memorability by how it is shown (an action in passing 0.25; a lesson stated 0.6); keys cool by
  half every 8 sentences. At the payoff, satisfaction = relevance x (1 - memorability): the time-hotel formula
  (narrative_entropy_framework.md). An earning plant shows the affordance (the latch pushed, the lid opening);
  a summary or a mere mention does not. A payoff with no plant is unearned (deus ex machina); a plant never
  paid off is Chekhov's debt.
- **The author's search** (tools/author_search.py): how the setup is told x how long until the payoff scene,
  each configuration run end to end and scored by the reader.

Chosen telling: "There was a small wooden box on the table. Her grandfather Ben sat by the window. Its lid
was shut tight. A brass latch kept it shut. Mara wanted to open the box. She pushed the lid hard. The lid
did not move. Ben pushed the latch hard. The latch gave way. Ben pushed the lid hard. The lid sprang open. A
spring inside the box uncoiled. A toy flew out and landed on the floor. Mara thanked Ben. A few days passed.
There was an old cupboard in the attic. Its door was shut tight. A brass bolt kept it shut. Mara wanted to
open the cupboard. She wondered what the door did. She pushed the door hard. The door did not move. Mara
remembered how Ben had opened the box. She wondered what the bolt did. She pushed the bolt hard. The bolt
gave way. Mara was delighted with the bolt. She pushed the door hard. The door sprang open. Mara realized
that the bolt had kept the door shut. She laughed with joy."

| setup told | gap | recall | reader memorability | satisfaction | |
| --- | --- | --- | --- | --- | --- |
| not at all ("Ben opened it for her.") | 10, 40 | yes | none | 0 | unearned |
| not at all | 120 | no | none | 0 | |
| **in passing** (his pushes only) | **10, 40** | **yes** | **0.14** | **0.643** | **chosen** |
| in passing | 120 | no (her keys cold) | | 0 | Chekhov's debt |
| emphasized (her lesson stated) | 10, 40 | yes | 0.38 | 0.463 | |
| emphasized | 120 | no | | 0 | Chekhov's debt |

All configurations round-trip at 1.00. After months (gap 120) Mara searches instead (the flag, then the bolt)
and finds the way herself: a different story from the same past, because her memory cooled.

### Findings

1. **The time-hotel formula orders the tellings correctly, from a mind model of the reader:** told in
   passing beats told outright (0.64 vs 0.46: the emphasized lesson is too memorable for its payoff to
   surprise), and not told at all is unearned. The search picks the passing plant without being told to.
2. **Two clocks.** The character's memory cools by story time (after months she cannot recall); the
   reader's by text distance (the gap does not change the reader's memorability). The author can therefore
   separate them: a long story-time gap told in a few sentences leaves the reader warm and the character cold
   (dramatic irony of memory, not yet exploited).
3. **Analogy is the payoff's mechanism.** The cupboard is not the box: the transfer is by shape (a locking
   object fastened by a connecting one), Case-2 unknown-to-unknown matching, and the recalled condition is
   held at half and confirmed by her own tries. This is the code POC's claim (structure transfers across
   domains) running inside a story.
4. **Earning a plant needs the affordance on the page.** The first reader measure counted the summary line
   and gave the unplanted version the best score; a plant earns only if it shows the detail used.
5. Two construction lessons: "held the door shut" parses "shut" as a clause of its own (rung 3 again, now
   replaced everywhere by "kept ... shut"); a closed box hides its contents but not its fastening, seated or
   undone (the bolt vanished from view once parted, and Mara waited for it forever).

## Rung 7: several endings held open (the reader's open variable over endings; option value; the author's search)

Rung 4's scene (Mara wants the box open, Leo keeps it shut, both act; reserves decide who outlasts whom), with
what an author can do to it and what a reader cannot see (`rung7.py`):
- **Hidden cast:** each reserve is 2 or 4; nothing on the page says which, so four casts give the same text
  until a reserve shows.
- **The author's moves**, one choice point per round, named as authored events: `on`; `away` (their mother
  calls Leo out for 3 rounds, once); `help` (her grandfather Ben, by the window from the first lines, gets up
  and opens it, once she has failed at the lid; he reads the box as it is).
- **Endings are closures read off the minds**, not targets: outlast (Leo gives up, she opens it), outlasted
  (she gives up), behind (she opens it while he is out; he comes back to find it open), help (Ben opens it).
- **The tree:** every cast x every move sequence, simulated (world and minds deep-copied at each choice point:
  350 stories in about 3 s).
- **The reader:** an open variable over the endings. At each sentence, the stories consistent with the text
  so far (a trie over beat sequences), weighted by a uniform cast prior and the reader's expectation of
  authored events (EVENT 0.08 per available move per round, my choice: a genre prior). Entropy curve per
  sentence (narrative_entropy_framework.md's multi-endpoint entropy).
- **The author's score:** *held* = entropy weighted by position (i/N), i.e. uncertainty kept late; *rise* =
  P(the ending that happens) just before it is certain minus its prior: from unlikely to inevitable;
  *value* = held x max(rise, 0) (a fiat, an ending that grew less likely before it happened, scores 0).
- **New mechanics in the mind (lean.py):** credit for a wanted change goes to the mover whose push brought it
  (several may have moved since one's last look); `guards`, a state a mind keeps from changing, which, once
  undone by another, is lost (read before the reserve drains: a loss ends the keeping); `signs` (my choice),
  under which the reserve shows: past half spent, the mind tires ("Mara grew tired of the latch."), a readout
  of how near the threshold is, as grief is a readout of what was held. All off by default; rungs 0-6
  unchanged.

The chosen story (cast Mara 2, Leo 4; no author moves; value 1.02, held 1.18, rise 0.86; round-trip 1.00):
"... Leo pushed the latch hard. The latch snapped back into place. **Mara grew tired of the latch.** She grew
angry with Leo. ... Mara pushed the latch hard. The latch gave way. **Leo grew tired of the latch.** Leo pushed
the latch hard. The latch snapped back into place. Mara gave up, resigned."

| sentence | reader after it | |
| --- | --- | --- |
| 1-8 (frame, want) | help .53, outlast .22, behind .20, outlasted .05 | Ben by the window is most of the suspense |
| 25 "Leo grew angry with Mara." | help .62, outlasted .20, behind .11, outlast .07 | |
| 28 "Mara grew tired of the latch." | help .49, outlasted .43, behind .09, outlast 0 | the least likely ending falls first |
| 41-45 (her tries, the flag) | outlasted .55 -> .77, help .28 -> .15 | each round without help shrinks it |
| 47 "Mara pushed the latch hard." | outlasted .92, help .08 (behind gone at 46) | |
| 52 "Mara gave up, resigned." | outlasted 1.00 | |

The other endings' best stories (each round-trips 1.00): outlast (cast 4/4, no moves, value 0.80: "Leo
gave up, resigned. Mara pushed the lid hard. The lid sprang open."); behind (4/4, away at round 17, 0.76:
"Their mother called Leo from the kitchen, and he went out. Mara pushed the latch hard. ... The lid sprang
open. ... Leo came back into the room. Leo saw that the box was open."); help (4/4, away 4 then help 5,
0.17: "Ben got up from his chair. Ben pushed the latch hard. ... Mara thanked Ben. Leo came back into the
room. Leo saw that the box was open. Leo grew angry with Ben.").

Ablations (`tools/rung7_ablate.py`), best story in each:

| moves on offer | signs | stories | best ending | value | held | rise |
| --- | --- | --- | --- | --- | --- | --- |
| away + help | yes | 350 | outlasted, no moves | **1.023** | 1.183 | 0.86 |
| away + help | no | 350 | outlast, no moves | 0.940 | 1.296 | 0.72 |
| help | yes | 61 | outlasted, no moves | 0.715 | 0.864 | 0.83 |
| away | yes | 62 | outlasted, no moves | 0.557 | 0.726 | 0.77 |
| none | yes | 4 | outlasted | 0.056 | 0.225 | 0.25 |
| none | no | 4 | outlasted | 0.198 | 0.793 | 0.25 |

Best `help` story: rise 0.23 with signs, 0.04 or below without (-0.60 for a late help). The reader's event
prior: the chosen story is the same for EVENT 0.04, 0.08, 0.16; at 0.02 the best is behind (away at round 11,
value 0.83).

### Findings

1. **Four endings from one scene, none authored as a target.** Who closes which want, and how, is read off the
   minds: two reserves and two authored events give four closures, and the author's search picks among 350
   middles by the reader's curve.
2. **The endings close from the outside in, by themselves.** With the reserves showing, the least likely
   ending falls first (outlast, when Mara tires), then behind, then help, then the close. Nothing orders them;
   the order is the reader's distribution read sentence by sentence (SOV: resolution from the outside in).
3. **Suspense against earning, priced.** Signs cost uncertainty (held 1.30 -> 1.18) and buy inevitability
   (rise 0.72 -> 0.86): without them the deciding variable never reaches the page, and the close is a fiat
   (the ending at 0.46-0.50 one sentence before certainty). A hidden variable closes "because it is obvious"
   (SOV sec. 8) only if its readout is told. The value favors signs: the inventory keeps them.
4. **Option value (SOV 8a), measured.** The best story makes no author move, yet each move on offer is worth a
   large part of its value: Ben by the window 0.47 (1.023 vs 0.557 without him), the call from the kitchen
   0.31 (vs 0.715). Unexercised options hold the reader's open variable open. Exercising earlier costs value
   monotonically (away at round 12: 0.95; 8: 0.92; 7: 0.88; ...): "do not exercise early while volatility is
   high". Without options the minds alone give 4 stories and little suspense (0.06-0.20).
5. **An authored helper is a deus ex machina even when introduced in the first lines.** Help's rise is at
   most 0.23: the reader is never moved toward it, because Ben has no visible pull (he is not a mind). This
   agrees with rung 6's finding that a mention is not a plant. To earn the help ending Ben must be a mind
   whose holes show (he watches, he frowns, he hesitates).
6. **The two reader measures disagree about Ben.** The multi-endpoint score pays for a gun that never fires
   (an option held to the end); the time-hotel reader (rung 6) would call it Chekhov's debt. Both are right
   about different things: the option is worth having while open, and an unexercised one is still unpaid.
   A combined author would have to price the debt against the option's time value.
7. Bugs on the way: Ben pushed the latch with the gerund it had at the start, so when Mara had already undone
   it he seated it again; with several movers since a mind's last look, the wanted change was credited to the
   first of them; Leo, coming back to an open box, first drained his reserve and tired, then saw it was lost.
8. Caveats: the reader is ideal (it has simulated the author's whole tree and knows the move set), and
   variety is low (0.27-0.29 over 52-76 sentences: the tug-of-war's middle is told try by try).

### Next

- Ben as a lean mind (a want of his own, e.g. her want met; his pull visible as watching and hesitating), so
  the help ending can be earned; then the reader's prior over events can come from the cast instead of a genre
  rate.
- A reader that does not know the tree: one that holds the endings as open variables funded by the text's
  receipts (the same SOV operators the characters use), compared with the ideal reader here.
- Larger move sets: Monte Carlo tree search in place of the exhaustive tree (the `narrative` project's MCTS).
- Story layer: summarizing varied exploration (rung 4, finding 6); now the main cost to variety.
- Minimality: the stake side of ownership (rung 4, finding 2) and the other hole kinds, across rungs 0-6.
- Gerundelle arm: a path from told conditions to experiments (rung 2, finding 3).
- Possession as a force (rung 5, finding 5).

## The Gerundelle arm, rung by rung (2026-10-25, second pass)

The user: go through each rung and fix Gerundelle so it competes with or beats the lean arm; then, "the SOV
algebra produces different minds from different parameters ... the range is the resource." So the target is
not to make Gerundelle's Mara walk the lean Mara's path. It is (a) every rung's capability present and
coherent in Gerundelle's own stories, and (b) temperament given a place in the architecture, so the same
algebra with different settings gives different, nameable characters. What counts as a bug is incoherence
(a discovery never stated, a feeling out of order, a want met with no joy, a loop that never ends a scene),
not wandering. Part of the lean arm's straighter path was an alphabetical tie-break (latch before flag; on
rung 6 the bolt before the door), named where it mattered.

Every change to Gerundelle (`E:/vscode/analogy/molecules`, backed up in `fiction/backup/molecules_2026-10-25/`)
was run against its own suite: 73/80 pass with the same seven failures and two pending as before the work
(T31, T63, T67, T68, T69, T70, T81; T60, T66 pending), after each round.

### What changed in Gerundelle (each a principle, with its first failure)

| change | where | first failure |
| --- | --- | --- |
| a push that came out unlike its usual outcome on its object is split on the one fact new in the situation it met (its first slice included) | `SovAgent.contrast`, `new_condition` | rung 0: the latch found, never said; rung 1: a crate slid in a gust starting with the push |
| a told condition borne out by the push it was about splits it too | `contrast` | rung 2: confirmed by success, no failure to contrast |
| a condition one's own last push made, then failing, is ruled out as a preparation ("not:a") | `contrast`, `Model.step` | rung 1: Tom swinging the flag himself |
| the planner reads the state a push leaves, and plans on expected reward | `Model.step` | rung 1: a hand-swung flag read as left swinging; a half-reliable way planned as never working |
| await: an experiment to wait for a condition the want's way needs and the mind cannot make | `Inquiry.observe` | rung 1: no way to wait |
| partner inference needs significance (Poisson, p < 0.05) | `relation_of`, `responsive` | rung 1: the wind "summoned" forty times |
| a want met keeps its slot closed; joy when a parked slot closes by a claim | `Territory.had`, `Phases.graph` | rung 0: no joy at the box opening |
| "what happens if I push here?" read: it suggests the region's claims | `Inquiry.observe` | rung 0: curious about the latch, pushing the flag |
| told ways planned on (credulity), refuted when the world contradicts them; anger at the teller | `Model.step`, `watch`, `Phases.graph` | rung 3: Gerundelle could not be lied to |
| contestation cools (the other's last move below cold by h0) | `Territory.update` | rung 4: probing a latch Leo had long stopped touching |
| a held thing gone from view is lost until a claim takes again; sadness at a lost slot even parked; anger at the taker; a grudge closes with its goal met (forgiveness); slots of a gone region are parked | `Territory`, `Phases` | rung 5: a toy carried off was still "mine"; grief refreshed forever |
| another's push watched whole is set against one's own tries | `observe_other` | rung 6 |
| gratitude: a want met by another's act | `Phases.graph` | rung 6 |
| recall (Case 2 by shape): a past split of the same push shape maps its condition onto an object in the same gerund here | `SovAgent.recall` | rung 6 (fair test): Gerundelle's analogy layer transfers that a relation is expected, not what fills it; the past did not help (14 tries against 11 fresh) |

Arm-side (`gerundelle_arm.py`): what is realized on the reaching push is told; feelings come after the push
they formed during; a telling is one receipt at the told weight (a word alone does not close a question) and
conditions every push on the object asked about; a realization matching a telling confirms the teller, one
matching what a liar held exposes him; waits told once; a keeper watches while its state holds; another
mind's slices are seen (its push chain only: not what was already moving, not its idle slices); several
Gerundelle minds act in one world; the phase log is read for storage, reopening and forgiveness.

### The rungs, Gerundelle against lean (default temperament unless named)

| rung | lean | Gerundelle | |
| --- | --- | --- | --- |
| 0 box | 17 sents, roots 7, chain 3, var 0.69 | 31 sents, roots 8-9, chain 3, reach 17 vs 9, var 0.45 | same arc (fail, realize, marvel, joy); explores the flag first |
| 1 crate in wind | 17 sents, var 0.82 | 70 sents, var 0.20; learns the sign from one gust, waits, three slides, joy | was: never reached the want |
| 2 told | 20 sents, roots 10, var 0.74 | 48 sents, roots 12, reach 37; dogged: 26 sents, var 0.62, chain 3 | being told now changes what she does |
| 3 lie | 31 sents, roots 13, irony 16 | 69 sents, roots 13, irony 54; dogged 45 | lie, reveal, anger, "Leo had lied" |
| 4 both act | 54 sents, roots 13 | 98 sents, roots 13, chain 3; stubborn Leo flips the ending | no anger: Gerundelle blames only once the want's condition is known |
| 5 lost | 55 sents, roots 12 | 73 sents, roots 15, reach 17; weeks/months: fades, remembers, angry again, forgives | a grief takes ~17 idle ticks to store (lean 8); stored phases do not cool |
| 6 two scenes | 31 sents, reader 0.643 | bolt sorts first: opens by chance, plant unpaid (debt) | |
| 6 fair (bolt id sorts last) | 31 sents, reader 0.643 | 48 sents, roots 11, reader **0.668** (dogged **0.686**); "Mara remembered how Ben had opened the box." | beats lean |
| 7 endings (`rung7_gerundelle.py`) | 350 stories; best value 1.023 (held 1.18, rise 0.86) | 529 stories (27 unresolved); best value **1.139** (held 1.36, rise 0.84): the same ending and cast, no author moves, round-trip 1.00; all four endings occur; help still unearned (0.26) | beats lean; choice points every 8 rounds, reader's event prior 0.08 per choice point, Leo out for 24 rounds (scaled to Gerundelle's ~110-round stories; first 0.25 and 3 rounds, which made help near-certain and "behind" impossible) |

### Temperament (temperament.py)

A character is a `Temperament`, read the same way by both arms. The rule for what belongs there: every value
must still give a working mind whose story round-trips, and different values must give different, nameable
characters. Physics of mind (funding thresholds, slots) stays global; narration belongs to the author.

| trait | SOV quantity | Gerundelle | lean |
| --- | --- | --- | --- |
| patience | failures running on a wanted region before the want is parked | `Params.patience` | `patience` |
| persistence | how slowly a repeated question loses its pull, q / (q + n) | `Params.persistence` (`Inquiry.decay`) | rumination decay |
| curiosity | the pull of unknowns no want pays for | `Params.curiosity` (unclaimed, uniqueness) | curiosity floor, unclaimed pull |
| credulity | the weight of told receipts | `Params.credulity` (funding; planning on told ways) | told weight |
| stubbornness | how often another may undo what one holds before giving up | arm (`GerundelleMind`) | `resolve` |

Range found so far: impatient Gerundelle Mara (rung 0) tries the flag and the lid, never the latch she was
curious about, and gives up; restless Mara (rung 2) never asks Ben, opens the box, learns nothing ("learns
many things shallowly"); dogged Mara asks, tests the answer, is right in 26 sentences; skeptical Mara tests
the alternatives to Ben's word first; rung 4's endings flip on Leo's stubbornness. On rung 2 all five lean
profiles tell the same story: the lean mind's choices are decided by expected work and the want's doubling,
so curiosity, persistence and credulity have nothing to act on there. Gerundelle is the wider substrate.

## The printer, second pass, and the first new worlds (2026-10-25)

Variety was the weakest measure on both minds, and its cause was the telling, not the minds: every push was two
sentences ("Mara pressed the lid. The lid did not move."), each change had one phrasing, and a run of different
failed tries was told try by try (rung 4, finding 6). Each change below is a construction admitted only when
the reader recovers its shape:

- **attempt** (story.py `combine`): a push and what it did to the object pushed are one plan and one sentence
  ("She pushed the lid hard, but it did not move." contrasting; "She gave the latch a hard push, and it gave
  way." elaborating|narrating). A contrast against a belief or a word stays a sentence of its own (the turn).
- **explore** (story.py `summarize`): a run of three or more failed attempts by the character (nothing moved,
  or what moved ended where it began) is told by its first and one summary ("Again and again she tried the lid
  and the flag, but nothing came of it." contrasting(main=iterating|narrating)).
- **phrasings in turn** (printer `rotate`, `push_phrase`): "pushed ... hard / gave ... a hard push / shoved",
  "pressed / pressed on", "did not move / would not move / did not budge / nothing happened".
- "again" is the same character's repeat (first anyone's: "Leo shoved the latch again" on his first push);
  "At last" on the turn after failures; a repeated verb said once ("swung and swung").
- The Gerundelle arm's watches read the push's chain only (the object pushed, and what changed after it), as
  the lean arm's do; other changes are something else's (the wind's flag was told as what Tom's lean did); a
  surprise is about what the push did to its object (a gust's flag in the prediction is not one).
- Measures: the reader counts a failure however it is told (attempt, explore). The dependence share and chain
  fell (rung 0 lean 0.57 -> 0.45, chain 3 -> 2): an outcome no longer counts as a plan depending on its own try.

| rung | lean variety | Gerundelle variety | Gerundelle sentences |
| --- | --- | --- | --- |
| 0 | 0.69 -> 0.92 | 0.45 -> 0.95 | 31 -> 22 |
| 1 | 0.82 -> 1.00 | 0.20 -> 0.65 | 70 -> 34 |
| 2 | 0.74 -> 0.94 | 0.35 -> 0.72 | 48 -> 34 |
| 3 | 0.60 -> 0.84 | 0.27 -> 0.68 | 69 -> 36 |
| 4 | 0.37 -> 0.69 | 0.23 -> 0.62 | 98 -> 60 |
| 5 | 0.40 -> 0.67 | 0.27 -> 0.63 | 73 -> 48 |
| 6 fair | 0.53 -> 0.67 (reader 0.643 -> 0.684) | 0.43 -> 0.74 (reader 0.668 -> 0.694) | 48 -> 36 |
| 7 | value 1.023 -> 1.049 | value 1.139 -> 1.144 | |

Everything round-trips at 1.00 on both minds.

**New worlds**, from Gerundelle's curriculum, each with a lexicon of its own (worlds.py `shed`, `lamp`) and no
change to either mind:
- **Rung 8, the shed** (`lock_scene`, S3-W03): a locked door, a rusty lock, a key in it, and a second key on
  the bench that moves under any push and does nothing. Both minds open it (lean 37 sentences, var 0.57;
  Gerundelle 27, var 0.78). The decoy works: the lean Mara tries the second key four times. Gerundelle first
  learned nothing from the door opening, because two facts were new (the lock it had opened, a flag settling);
  among several, the one its last push made is now the preparation (`new_condition`), and "Mara realized that
  the lock had kept the door shut."
- **Rung 9, the lamp** (`lamp_scene`, S2-W03, an AND): two loose plugs in series and a button; the lamp lights
  only when both are in. The lean Mara lights it in 20 sentences by luck (both plugs first). Gerundelle's Mara
  lights it after 63, toggling the plugs in and out. **Neither realizes the AND**: each plug was in during some
  failed press, so no single fact is new when the lamp lights. Gerundelle's meta layer learns conjunctions by
  splitting a half again, which needs more outcomes than one scene gives. A conjunction learner is the first
  thing a new world has asked of the minds.

## Corpus run 1 (`tools/corpus.py`, `corpus/`)

Every scene (rungs 0-6, 6 fair, 8, 9) x six temperaments x both minds: 120 runs, 120 stories, **66 unique**
(Gerundelle 40, lean 26), every unique story read back in full: **2212 labelled sentences** (474 distinct), 20 root
gerunds, 86 distinct labels. Outcomes: 54 reached, 8 gave up, 4 unresolved. Median variety lean 0.75, Gerundelle
0.73; median length 26 and 34 sentences.

- **Range, measured.** Of six temperaments per scene, Gerundelle tells 3-6 different stories (median 4), the lean
  mind 1-5 (median 2): the lean mind's choices are mostly decided by expected work. Trusting and skeptical
  coincide wherever no one tells anything, as they should.
- **One scene failed at first**, and it was the corpus's first unplanned discovery: an impatient Gerundelle Mara on
  rung 5, after the box was open, learned that the loose lid slid only while the latch was seated. The lexicon had
  no words for it ("Mara realized that the lid moved only if the latch was in place." now).
- **The corpus's limit is the world, not the mind:** 474 distinct sentences of 2212. Three worlds' objects and one
  lexicon per world repeat across stories. More worlds, and several lexicons per world (the same force structure
  as a box, a cupboard, a shed, a jar), are the cheapest way to more distinct text.

## More worlds (rungs 10-17)

Surveyed all of Gerundelle's curriculum worlds (`tools/survey_worlds.py`: states, pushes, and every change a
curious mind with no want makes there) and made scenes of the ones with a clear want and no numeric gauges, each
with its own lexicon (`worlds.lexicon(...)`, one call per scene), plus two dressings of the box's force structure
(the same physics, other objects and words):

| rung | scene | world | want |
| --- | --- | --- | --- |
| 10 | a boulder on a plank over a log | lever | the boulder flies off the path |
| 11 | a toy cannon (clamp, spring, ball) | spring | the ball shoots out |
| 12 | a catapult (catch, loaded arm, stone) | weight | the stone flies over the fence |
| 13 | a doorbell with its wire out (a hidden enabler) | button, unplugged | the bell rings |
| 14 | a chime held quiet by a felt damper | chime | the chime rings |
| 15 | a chain of things on a shelf (wedge, marble, ruler, card, bead) | marble | the bead drops |
| 16 | a chest with a brass hasp and a puppet | the box, renamed | the chest opens |
| 17 | an old tin with a wire clip and a paper cricket | the box, renamed | the tin opens |

What the new worlds found (each fixed as a principle, both minds):
- **A push's chain begins with what the pushed object carries** (`worlds.carried`: its node's subtree, read as
  the push begins). A plank passes its force to the boulder without changing state itself; under "the object
  pushed, and what changed after it" the boulder's flight was nobody's doing, so the lean Tom's want was met and
  never registered, and he went on for 300 tries. (I first reported this as the lean mind never trying a light
  push: wrong, it was this.)
- **A split's condition can be the other half's.** A split's boundary is the fact new in whichever outcome came
  second: the chime that failed with the damper seated is split on "damper seated", and works with it away. The
  arm first told the tag as the condition ("the chime rang only with the damper seated").
- **Verbs per object** (`flips_obj`): changes were said by gerund pair alone, and a flag beside the chime "rang out".

## Corpus run 3: dressings, phrasings, a length cap (2026-10-26)

- **Phrasings** (`variants.py`): every lexicon phrase that has alternatives gets them (changes, states, frames,
  wants), each admitted by the reader in a sentence; the printer takes them in turn from a per-story seed (the
  scene and the configuration), so stories in one world open and run differently. Two were refused by the reader
  ("came undone", "held it closed") and replaced; "longed to ..." and "set out to ..." read as
  explaining(means, purpose), not narrating, and were kept with that shape (a structure the corpus lacked).
- **Dressings** (rungs 18-24, `worlds.dressed` + `worlds.dress`): Gerundelle's `renamed` worlds with a lexicon
  each (music box, garden gate, diary, log in a stream, pinball launcher, radio, bicycle bell). Renamed objects
  sort differently, so exploration orders differ too (Gerundelle's diary runs 89 sentences, its shed 27).
- **Any learned condition is sayable**: the printer's general form ("{N} moved only if {C} <verb>") when a scene
  has no words for a condition. Found by a dogged Gerundelle Tom at the pinball launcher who learned a superstition:
  "Tom realized that the trigger moved only if the flag fluttered."
- **Length cap** (90 sentences): kept, marked, left out of the clean set.
- **The chain on the shelf is irreversible**: a curious Gerundelle Mara slides the ruler and the flag out of line
  before tipping the wedge, and the chain never falls. Recorded, not changed: an exploratory temperament in a
  fragile world is a story.

300 runs: **259 clean stories, 6634 labelled sentences, 1447 distinct, 187 distinct in what happens** (run 1: 66
stories, 2212 sentences, 474 distinct). The share of distinct sentences stays near a fifth: a story repeats its own
pushes and outcomes, which is what its events are. The next gains are the learning gaps (conjunctions) and more
kinds of scene (people, losses, time) across the new worlds, not more words.

## People, lies and loss in the new worlds (social.py; corpus run 4)

The ladder's social rungs (2-6) were built on the box. `social.py` generates them for every world with a single
fastening from a role card (scene, lexicon, character, want, the fastening and its states, the word for its closed
state, the prize): told, lie, keep (with the keeper's past generated: the fastening undone and settled), loss (the
prize made playable in a ScenicWorld), and two-scene pairs with Ben (a world, then another of the same physics).
Every generated line is read back first (`tools/probe_social.py`: 56 lines; "holds it quiet" refused, "still" used).
All 37 scenes round-trip on both minds with no change to either mind.

Found on the way (fixed):
- **Identity by name across scenes**: a chest's lid had the box's id, and her rule for the box's lid applied to it
  directly (she waited for a latch that was not there); both scenes' flags were told with the second scene's words.
  A pair's second scene now renames every id it shares with the first: what carries over can only carry by shape.
- **Ben reads the scene** (a fastening already undone is left alone; one that springs back is pushed again).
- **A mind done takes no more turns**: when Mara opened the first scene herself, the runner waited on her forever.
- **Generate and test**: "Tom was delighted with the clasp." misparses where "He was delighted with the clasp." does
  not; a sentence the reader cannot read as intended is retold with the pronoun as subject, kept if it reads.

On Gerundelle, three of six pairs have Mara or Tom open the first scene alone (no help, nothing to remember): a
capable character's story, but the help-then-recall arc is carried by two Gerundelle pairs (box>chest, shed>gate:
reader 0.70, 0.71) and all six lean ones (0.68-0.69).

## Learning two conditions at once (the AND)

The lamp (rung 9) asked it: each plug had been in during some failed press, so when the lamp lit no single fact was
new, and neither mind learned anything. The principle, the same in both minds: when no one fact separates the
success from every failure, each failure still lacked something the success had; the condition is **the smallest set
of the success's facts that every failure missed one of** (a minimal hitting set, at most three), drawn only from
states the mind's own pushes left in place (an AND of what it set up: a gust's flag is no preparation).

- Gerundelle (`SovAgent.conjunction`): held as its meta layer's own nested split (split on one fact, the yes half
  split again on the next), the conjunction recorded on the outer split; the arm tells it as one realization.
- Lean (`LeanMind.condition`): carried as "a&b"; acted on by its first unmet part (`unmet`), told as one.
- Printer: "Mara realized that the first plug and the second plug had to be in place." (the conditions joined into
  the scene's template).

What it needed first, found on the way:
- **A push is judged by the wanted object too** (Gerundelle `own`, lean `condition`'s target): a press that lit the
  lamp looked like every press that did not, the button going down and springing back each time.
- **Comparable tries across strengths** (`alike`): the press that lit the lamp was light and every failure hard, two
  pushes to Gerundelle. Another strength's tries are evidence only where they did the same to the object pushed (a
  button under either; not a plug, which a light push leaves and a hard one toggles: borrowing those taught "the second
  plug moved only if the first plug slid into place").
- **Evidence decides between a single condition and an AND.** In the corpus's own runs every failed press lacked the
  second plug, so the honest lesson is the partial one ("Mara realized that the second plug had to be in place.");
  the AND is learned when the evidence requires it (a designed run where each plug alone was in during a failure:
  both minds learn plug_a & plug_b). The lean Mara pushes both plugs first and lights it at once: nothing to learn.
