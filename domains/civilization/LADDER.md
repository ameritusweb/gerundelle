# The civilization ladder

Each rung is written up after it runs, the same way as `../fiction/LADDER.md` and `../cognitivecode/LADDER.md`. The design is in [README.md](README.md) and [PHYSICS.md](PHYSICS.md).

## Rung P0: one mind draws, forms, breaks and launches (`potential_world.py`, `p0.py`), 2026-10-29

**Question.** Does one mind draw, form, break and launch in a generous world with potential, and does a story come out the other end?

**Built:**
- **`potential_world.py`**: a world of its own behind the interface Gerundelle reads (`states`, `invitations`, `act`, `diffs`, `renew`, `horizon`, `gamma`, `still`). Cognitivecode's `CodeWorld` set the precedent.
  - **Potential** lies in four places: the spring's field, the jar's store, objects (embodied), and flight (motion).
  - **The total is asserted after every slice.**
  - **Gerunds:** drawing (jar `empty → charged`), spilling (`charged → empty`), forming (hollow `shaping → cradling`, skiff appears `resting`), cleaving (boulder `resting → cleaving → gone`, pebbles appear `piling`), propelling (skiff `resting → propelling → flying → resting`, landing on the far hill, its motion returned to the field).
  - **The hidden condition:** every power spends the jar's store, so each one works only when the jar is charged.
- **`p0.py`**: Gerundelle (`E:/vscode/analogy/molecules`, unchanged) through fiction's `GerundelleMind`, then fiction's `story.tell`, `Printer` and `measure.evaluate` (unchanged). Only the world and its lexicon are new.

**My choices (named):**
- The world is self-contained instead of an extension of `forces/poc.py`. That kept the physics small and conservation checkable, but means P0 doesn't reuse poc's mechanics.
- The world is still: nothing moves unless a push set it going.
- Generous settings: field 1000, one draw of 20 covers forming (3), cleaving (2) and launching (5).

### Results (one run, Gerundelle, default temperament)

| Measure | Result |
|---|---|
| want reached (`skiff_flying`) | **yes**, at tick 26 (written at 34, after fiction's settling) |
| pushes | 10 (the jar 4, the boulder 2, the skiff 2, the hollow 1, plus pushes while settling) |
| conservation | **holds**: 35 slices, total 1006 at every one |
| powers used | all four: drew (twice), formed, cleaved, launched; also spilled |
| conditions learned | 1: `hard_push:skiff_resting` works under `jar_charged` |
| story | 24 sentences, **round-trip 1.00**, history: dependent 0.38, chain 2, reach 5 |

The story as printed:

> There was a spring of light at the foot of a hill. A clay jar stood empty beside it. A boat-shaped hollow lay open in the rock. A boulder sat on the slope. Ada wanted to fly. She pushed the boulder hard, but it did not move. She wondered what the jar did. She shook the jar, and it began to glow. She was delighted with the jar. She gave the hollow a hard push, and it held a new shape. A small skiff took shape in the hollow. Ada was delighted with the hollow. She pushed the boulder hard. But this time the boulder split apart. A heap of pebbles lay on the ground. Ada shook the jar, and it went dark. She shoved the skiff, but it would not move. She dipped the jar into the spring, and it began to glow. She pushed the skiff hard. The skiff rose into the air and came down on the far hill. The hollow lay empty again. Ada realized that the skiff flew only when the jar glowed. She felt sad about the skiff. She felt anxious about the hollow.

### Findings

1. **The whole pipeline runs on the new physics with no change to the mind or the story layer.** Gerundelle explored, met the hidden condition, learned it by contrast (the skiff failed with the jar dark and flew with it glowing), and reached the want. The printer told it, and the reader read every sentence back as written. P0's question is answered: yes.
2. **Conservation held at every slice**, through drawing, forming, cleaving, launching, landing and spilling. That's the property the Lean proof should eventually cover (PHYSICS.md).
3. **Making something is claiming it, so a creation that won't respond reads as loss.** This is the first new finding of the track. Forming was a push that took, so Gerundelle's territory register claimed the skiff (t11). When Ada pushed it with the jar dark (t20) and nothing happened, the region went to *contested* and then *lost* (t23). The launch that reached the want (t24) landed on a region already marked lost, so the closing feelings were sadness about the skiff and anxiety about the hollow, not joy. In the force world Mara never owned the lid before it opened, so this couldn't happen there. Only a world where minds make things can produce it. Not patched: it's Gerundelle's own reading. Whether it's coherent (grief over an object that merely needed its condition) is a question for Gerundelle under its backup-and-suite discipline (`../cognitivecode/GERUNDELLE_ARM.md`).
4. **Only one of the three conditions was learned.** Forming worked on its first try, because the jar happened to be charged, so it had no failure to contrast against. Cleaving failed once (jar dark, t5) and worked once (t14), and Gerundelle registered a surprise but made no split. The second try had several new facts at once: the jar charged, and the skiff and the hollow's new shape both present. `new_condition` needs a single new fact, and the AND learner needs two failures. Learning these conditions needs more tries, which a later rung (P1) is built to give.
5. **The wording needed two fixes, both mine.** "A hollow in the rock shaped like a boat lay open in the rock" and "lay scattered on the ground" didn't read back. The flight was also lost because the printer keeps the first and last of three changes ("surged forward ... came down"). Skipping `resting → propelling` lets "rose into the air" carry the flight.

### Not yet done

- One run only. A sweep over seeds and temperaments (README: ranges, not single runs) is the next measurement.
- "Ada wanted to fly", but the skiff flies, not Ada. A want phrased as making something fly would be truer.
- The lean arm hasn't run here. README lesson 12 says to run both arms from the start. `fiction/lean.py` reads the same interface, so it should be a short step.

## Rung P1: learning forming's hidden condition (`potential_world.PatternWorld`, `p1.py`), 2026-10-29

**Question.** Does a mind learn forming's hidden condition when it starts without the right pattern?

**The world** (`PatternWorld`, a subclass, so P0 still reproduces):
- **The hollow is blank** and forms the shape of whatever lies pressed in it.
- **A spiral shell lies on the slope.** It's a pattern in plain sight, but the wrong one: it forms a cup.
- **The right pattern is inside the boulder:** a little carved boat, found when the boulder is cleaved.
- **The jar starts charged** (store 40), so the condition that varies for forming is the pattern.
- **Pattern is a fact about another object** (`model_nesting`), so Gerundelle can learn it by contrast, as it learned the latch.
- **Chain to the want:** cleave → press the boat into the hollow → form → launch.

**Two physics fixes, each a failure first:**
1. **Forming takes a slice** (this answers one of PHYSICS.md's open questions). At first the shape appeared in the push's own slice and the hollow didn't change. Gerundelle reads other objects' changes in a push's first slice as part of the situation the push met; that rule exists so a coinciding gust is understood. So it learned that forming turns on `skiff_resting`, i.e. on its own effect. Fiction's beat writer also told the push as "nothing", with the cup appearing from elsewhere. Now the hollow works in the push's slice (`open → forming`, the potential held "in the making") and the shape comes out the next slice.
2. **Shaking an empty jar fills nothing; only dipping draws.** P0's world let any push draw, and the story said "She shook the jar again, and it began to glow." P0's world keeps its rule so its results reproduce.

### Results (Gerundelle, fiction's temperament profiles, 800 ticks)

| Temperament | Reached | Ticks | Pushes | Forming's condition learned | Round-trip |
|---|---|---|---|---|---|
| steady | yes | 46 | 14 | `model_nesting` (right) | 1.00 (35 sentences) |
| restless | yes | 63 | 19 | `model_nesting` (hard push) **and** `shell_nesting` (light push) | 1.00 (39) |
| dogged | **no** | 800 | 48 | `shell_nesting` only | 1.00 (79) |
| impatient, patient, trusting, skeptical | yes | 46 | 14 | `model_nesting` | 1.00 (35) |

Conservation held at every slice in every run.

The steady story:

> There was a spring of light at the foot of a hill. A clay jar glowed beside it. A smooth hollow lay open in the rock. A spiral shell lay on the slope. A boulder sat on the slope. Ada wanted to send a boat into the sky. She pushed the hollow hard, but it did not move. She moved the shell, and it settled into the hollow. She was delighted with the shell. She gave the boulder a hard push, and it split apart. A little carved boat lay among the pieces. A heap of pebbles lay on the ground. Ada wondered what the hollow needed. She felt sad about the boulder. She was delighted with the carved boat. She pushed the hollow hard. A shell-shaped cup took shape beside the hollow. Ada shook the jar, and it went dark. She was delighted with the jar. She wondered what the jar did. She shook the jar again, but it would not move. She felt anxious about the jar. She shoved the hollow, but it did not budge. She felt anxious about the cup. She felt sad about the jar. She moved the shell, and it came out of the hollow. She felt sad about the cup. She dipped the jar into the spring, and it began to glow. In time, she stopped thinking about the boulder. She moved the carved boat, and it settled into the hollow. She pushed the hollow hard. A small skiff took shape beside the hollow. Ada realized that the hollow made a boat only when the carved boat lay in it. She pushed the skiff hard, and it rose into the air and came down on the far hill. She laughed with joy.

### Findings

1. **Yes, the condition is learned by contrast**, in 6 of 7 temperaments: "the hollow made a boat only when the carved boat lay in it". The wrong pattern came first and made a cup, which isn't the want. The contrast that taught the condition was the skiff appearing (a change to the wanted object) against the hollow's failures.
2. **Restless learns the most.** It split the light push on the shell and the hard push on the boat: two patterns, two shapes. Moving on fast and exploring broadly is what lets a mind find more than one pattern, a first sign of the range README lesson 4 asks for.
3. **Dogged goes quiet with the answer two pushes away.** At t161 the carved boat lay in the hollow and the jar was dark. It then sat idle for 640 ticks (`meta:bored`, `meta:stuck` on the jar's conditions question). This is the open Gerundelle behavior `../cognitivecode/GERUNDELLE_ARM.md` lists under T80 ("a held, understood region stops being pushed"; "when a question should stop"), and low curiosity makes it come sooner. It isn't patched here; it belongs to Gerundelle's own repair discipline. It is also a character: a dogged mind that stops one step short.
4. **The P0 finding, from the other side.** P0 ended in sadness because Ada had pushed her newly made skiff while the jar was dark, and the mind read its unresponsive creation as lost. Here she never pushed the skiff before it could fly, and the story ends in joy. The same mind and physics give different feelings depending on the order of the tries, which supports reading P0's sadness as Gerundelle's ownership of creations rather than a defect of the world.
5. **Breaking something is losing it.** "She felt sad about the boulder" after cleaving it: the boulder region is gone, which the territory register reads as a loss. In a civilization, destruction will carry this cost on its own, without a rule saying so.
6. **Four temperaments don't differ here.** Patience, trust and skepticism only act on a want that keeps failing or on someone telling. A world with one mind and a reachable want doesn't exercise them. P2 (a told blueprint) is where trust and skepticism should first matter.

### Not yet done

- One run per temperament. Gerundelle is deterministic, so a range needs varied orders (cognitivecode's `order` seeds) or varied worlds.
- The lean arm hasn't run (README lesson 12).
- The hollow's own `open → forming` flip isn't said in the story (no wording); "She pushed the hollow hard. A ... took shape beside the hollow." reads well without it.

## Rung P2: a told blueprint (`p2.py`), 2026-10-29

**Question.** Does a told blueprint change what a mind can make?

**Setup:**
- **Two Gerundelle minds on P1's hillside** (`PatternWorld`).
- **Wen, the teller, has a past:** a P1 run on his own copy of the hillside, steady character. He learned one split, `hard_push:hollow_open` under `model_nesting`.
- **Ada is new.** When her own conditions question about a push wins her top, she asks Wen (Pose across minds). He answers from his own splits (Attest, `GerundelleMind.answer`), or says he doesn't know. The answer enters her register as `conditioned_by`, at the told weight.
- **Each temperament runs twice**, alone (P1) and with Wen, on the same world.

**My choices (named):**
- **`Asking`** (in `p2.py`, a subclass): fiction's `GerundelleMind` asks only about pushes on the wanted object. The blueprint is about the hollow, not the skiff, so `Asking` asks about any push whose conditions question wins, once per object. Fiction's code is unchanged.
- **Questions are subject questions** ("What belongs in the hollow?"). The printer embeds the question as it stands for "I don't know ...", and the first stories said "I don't know what does the boulder need".

### Results (800 ticks)

| Temperament | Alone | Told by Wen | Realized Wen was right |
|---|---|---|---|
| **dogged** | **not reached** (48 pushes, quiet from t161) | **reached**: 33 pushes, 117 ticks | yes |
| steady, impatient, patient | 14 pushes, 46 ticks | 16 pushes, 52 ticks | no (learned it, not told: finding 4) |
| restless | 19, 63 | 19, 63 | no |
| trusting | 14, 46 | **27, 88** | yes |
| skeptical | 14, 46 | **29, 94** | yes |

Conservation held in every run. All 14 stories round-trip at 1.00.

The dogged story, told:

> ... Ada wanted to send a boat into the sky. She pushed the hollow hard, but it did not move. She moved the shell, and it settled into the hollow. "What belongs in the hollow?" Ada asked Wen. "The carved boat belongs in the hollow," Wen said. ... "What breaks the boulder?" Ada asked Wen. "I don't know what breaks the boulder," Wen said. ... She pushed the boulder hard. But this time the boulder split apart. A little carved boat lay among the pieces. ... She moved the carved boat, and it settled into the hollow. ... Ada touched the hollow. A small skiff took shape beside the hollow. Ada realized that Wen had been right. "What lifts the skiff?" Ada asked Wen. "I don't know what lifts the skiff," Wen said. Ada pushed the skiff hard, and it rose into the air and came down on the far hill. ... Ada laughed with joy.

### Findings

1. **A told blueprint rescues the mind that would have gone quiet.** Alone, the dogged mind stopped at t161 with the answer two pushes away (P1 finding 3). Told, it reached the want, and its own try confirmed the telling ("Ada realized that Wen had been right"). The told condition is a hypothesis Gerundelle's Inquiry turns into experiments (`told_leads`), so a question stays alive that alone would have gone stuck and bored. This is the first sign of what culture is for in this world: it carries the minds that wouldn't have found it themselves.
2. **For minds that would have found it anyway, being told costs.** Trusting went from 14 to 27 pushes, skeptical from 14 to 29, steady from 14 to 16. Restless was unchanged. Testing the word takes tries. Fiction's rung 2 found that Attest pays only where it saves search; here it can also cost where it doesn't. That's a price of culture, and it falls on the able.
3. **Trusting and skeptical move the same way, and both away from steady.** Credulity sets the told weight in Gerundelle (`Understanding.funding`, and the planner's belief in a told way), so 0.9 and 0.1 should pull apart. They didn't: both doubled the pushes. The cause isn't traced yet. It's the first thing to look at before trust can be a what-if knob.
4. **Knowledge is specific (fiction rung 4, again).** Wen knows only what his past made him learn. His jar was charged when he launched, so he never learned the jar's condition, and "What lifts the skiff?" gets "I don't know". A blueprint holds exactly the contrasts its holder lived through.
5. **A blueprint can't say where its pattern is.** The told condition (`model_nesting`) names an object Ada can't push until she has cleaved the boulder. Until then Inquiry has no lead from it. The telling pays only once the pattern exists in her world. In a civilization this is the gap between knowing a recipe and having the ingredient: trade's opening (README ladder rung 2).
6. **Fiction's beat writer drops realizations in a world that makes things.** Steady and restless learned the condition (the split exists), but no "realized" sentence was written. `write_splits` skips a split when the pushed object moved in both halves, assuming the halves then differ only in what else changed (a gust's flag). Here the hollow works in both halves, and what differs is *what it makes* (a cup or a skiff). The fix belongs in fiction's shared code under its regression rule (rerun the ladder; round-trip must stay 1.00), so it isn't patched here.

### Not yet done

- Wen as a mind of another temperament, and Ada asking before or after her own first contrast (timing).
- The lean arm.
- Credulity's non-effect (finding 3) traced in Gerundelle.
- Fiction's `write_splits` fix for products (finding 6).

## Rung P3: reaching space (`potential_world.VoyageWorld`, `p3.py`), 2026-10-29

**Question.** Does a mind reach space?

**The world:**
- **P0's hillside with a world binding (15)** and a pale moon in the sky. The moon is a second place with its own field (500), so the ledger spans two places.
- **The jar has levels:** dipped once it's `charged` (10), dipped again `brimming` (20). Shaking spills it.
- **Launching releases all the jar holds as one push.**
  - Over the binding: `propelling → escaping → drifting → arriving → moored`, the skiff's motion going into the moon's field.
  - Under the binding: `flying` and back down on the far hill.
- **The hidden condition is `jar_brimming`.**
- **The watch is 6 slices long**, so the mind sees a voyage end.
- **The want, beyond the binding:** `skiff_arriving`.

**A law of this physics, learned the same way twice (P1, P3): in the slice a push lands, only the object pushed changes; consequences for anything else follow a slice later.** In the first P3 run the jar went dark in the launch's own slice. Gerundelle reads changes to other objects in a push's first slice as part of the situation the push met (the rule that lets it understand a coinciding gust), so it recorded every launch as made with the jar empty. No launch could be told apart from another, and nothing was learned. P1's forming was the same trap, with the product appearing in the push's slice. VoyageWorld now defers the jar's flip, the hollow's emptying, and the formed skiff to the next slice. (P0's world is unchanged, so its results reproduce.)

### Results (800 ticks)

| Temperament | Reached the moon | Pushes | Ticks | Launches (came back down) | Learned |
|---|---|---|---|---|---|
| steady, trusting, skeptical | **yes, earned** | 41 | 265 | 4 (2) | launch flies under `jar_charged`; in the other half, reaches the moon under `jar_brimming` (a nested split) |
| dogged | yes, **lucky** | 10 | 67 | 1 (0) | nothing: dipped twice before ever launching |
| impatient | **gave up** (t82) | 13 | 83 | 1 (0) | nothing |
| patient | **gave up** (t134) | 21 | 135 | 1 (0) | nothing |
| restless | no (quiet from t276) | 43 | 800 | 3 (2) | forming and flying under `jar_charged`, not the brim |

Conservation held at every slice in every run, across both places. The four stories printed (steady, dogged, impatient, restless) round-trip at 1.00.

The steady story, its end:

> ... She pushed the skiff hard. The skiff rose into the air and came down on the far hill. The jar went dark. The hollow lay empty again. Ada realized that the skiff flew only when the jar glowed. ... She gave the skiff a hard push, and it rose into the air and came down on the far hill. The jar went dark. Ada dipped the jar into the spring, and it began to glow. ... She dipped the jar into the spring, and it brimmed with light. She shoved the hollow, but it would not move. At last she pushed the skiff hard. The skiff climbed past the clouds and landed on the moon. The jar went dark. Ada realized that the skiff reached the moon only when the jar was full. She felt sad about the skiff.

### Findings

1. **Yes, a mind reaches space, and it can earn it.** The earned path is two realizations in order, the story's arc. First that the skiff flies at all (only when the jar glows), then, after flights that came back down, that it reaches the moon only when the jar is full. Gerundelle holds this as a nested split, a condition inside a condition: the first time the track has needed one.
2. **Reaching space by luck is possible, and the story knows the difference.** Dogged filled the jar twice before ever launching and arrived on its first try, learning nothing (21 sentences, no realization). cognitivecode's README distinction between earned and lucky endings appears here unprompted. In a civilization a lucky first voyage would be a technology nobody understands.
3. **Patience matters for the first time** (P1 finding 6 predicted it would need a want that keeps failing). Space is the first want here that fails repeatedly before it succeeds. Impatient (patience 2) gave up after two failed tries on the skiff, and patient (6) after six. Steady, with no limit, kept going and earned it. The what-if follows directly: a harder binding filters which temperaments reach space.
4. **Restless doesn't get there.** It learned that the jar's glow makes forming and flying work, then went quiet at t276 with a charged jar. It's the same Gerundelle quiet as dogged in P1, now in a different character: moving on fast left the brim untried after the flights came back down.
5. **The physics law above is a real constraint on world design, not a patch.** Any world built for these minds has to keep a push's own slice clean of other objects' changes, or the minds learn their own effects as their causes. Wind is different, because it's outside any push. Written into PHYSICS.md.
6. **The voyage still ends in sadness** for steady. P0's ownership effect again: her pushes on the skiff had failed while the jar was dark, and the region was marked lost before it arrived.

### Not yet done

- Varied orders for ranges (Gerundelle is deterministic; trusting and skeptical are identical to steady here, as no one tells).
- The lean arm.
- A told voyage (P2's Wen, who knows the brim) to see whether telling carries the impatient past their patience.

## Rung P4: a population with no scarcity (`potential_world.StationsWorld`, `p4.py`), 2026-10-29

**Question.** What does a population do with no scarcity? This is the baseline the scarcity rungs will be measured against.

**The world** (`StationsWorld`):
- **VoyageWorld's physics, one station per mind.** Each station is a jar, a hollow holding the boat's pattern, and the skiff it forms, which takes its push from the jar beside its hollow.
- **One spring with a field to spare (4000), and one moon.**
- **Mind k wants skiff k on the moon**, but nothing assigns a station to a mind. Any mind can push any object.

**The minds:** four Gerundelle minds take turns, one slice per mind per round (fiction's rung 4 way). They can ask each other (`p2.Asking`).

**The prediction, written in `p4.py` before the first run:** little specialization, little conflict, little exchange. Each mind works mostly its own station; pushes on others' are curiosity, not contest; anger is rare; asks are few.

**Two perception fixes for several minds, each a failure first:**
1. **The world is no longer still** (`still = False`). It inherited `still` from the one-mind rungs, which told every mind that nothing moves unless it acts, while three others were moving everything.
2. **A mind perceives the flight of what it threw.** A voyage takes five slices, and with four minds taking turns they fell in the others' turns. The launcher's watch never saw its skiff arrive, and fiction's `look()` credited the arrival to whoever's slice it landed in. In the first runs every one of four minds felt gratitude to another for its own launch: a perfect "ring of gifts" that was entirely misperception. Now the world keeps who set each motion going (`setter`) and delivers the continuation to that mind at its next turn (`inbox`). One-mind worlds are unaffected. Those first runs' numbers are discarded.

### Results (2000 rounds; Gerundelle, deterministic, one run per population)

| Population | Want met | How | Own-station share | Changed things on others' stations | Asks / answered | Anger | Gave up |
|---|---|---|---|---|---|---|---|
| steady ×4 | **1 of 4** (Dee) | own launch | 0.25–0.39 | 6–47 per mind | 27 / 2 | 0 | 0 |
| steady, restless, patient, dogged | **2 of 4** (Ada, Dee) | Dee's own launch; **Ada's skiff launched by Ben** (real gratitude) | 0.13–0.37 | 7–62 | 25 / 1 | **1** (Cal, at whoever moved jar1) | Cal (patient), t2019 |

Conservation held at every slice in both runs. In the mixed run the moon also took a skiff nobody wanted: Ada launched Cal's after Cal had given up.

What happened at the launches (steady ×4): 64 hard pushes on skiffs. Most did nothing, because the jar was empty when the push came, often spent or spilled by another mind. Most of the rest flew and came back down, because the jar was only charged. One reached the moon.

### Findings

1. **No specialization, as predicted, and more strongly than predicted.** The own-station share is around chance (0.25 with four stations), not above it. Wanting skiff k doesn't make a mind keep to station k. Curiosity spreads over everything, and every jar and skiff region is claimed by several minds.
2. **Conflict without scarcity, against the prediction.** Anger is rare (one, in the mixed population), but interference is heavy. Minds empty and spill each other's jars in the course of their own curiosity, and the owner's launch then does nothing. What is scarce isn't potential (the spring is nearly untouched) but **a stable state**: a jar that stays brimming long enough for its skiff's launch. A commons of tools is a coordination problem even with abundant matter. Only one or two of four minds reach a want that a mind alone reaches every time (P3, steady).
3. **Exchange fails because nobody's knowledge is clean.** Minds ask (25–27 asks) but almost nobody can answer (1–2). Each mind's conditions are confounded by the others' moves: Dee's hollow conditions came to include other stations' states. In a crowd, other minds are a gust. Telling needs a teller whose splits are clean (P2's Wen learned alone).
4. **Help happens, by accident.** Ben's curiosity launched Ada's skiff at a moment her jar was brimming, and Ada felt gratitude toward Ben. Ada launched Cal's skiff after Cal had given up, an arrival nobody wanted. Help and waste come from the same undirected curiosity.
5. **The mixed population did better (2 vs 1), on one run each.** Gerundelle is deterministic, so this can't be read as "variety helps" until there are ranges over orders.
6. **Two perception laws for worlds with several minds**, alongside PHYSICS.md principle 0: a world with others in it is never still, and a mind must perceive the continuation of what it set going, or it credits others with its own deeds.

### The baseline, for the scarcity rungs

Against this, scarcity rungs measure changes in: wants met (1–2 of 4), own-station share (about chance), interference (dozens of changes per mind on others' stations), anger (0–1), asks answered (1–2), and give-ups (0–1).

### Not yet done

- A story of the population. The printer needs a lexicon for numbered stations, and fiction's `story.tell` hasn't been tried with four actors.
- Ranges over turn orders and seeds.
- The lean arm.

## Rung P5: the rest of the physics, on the moon's own field (`moon_world.py`, `p5.py`), 2026-10-30

**Question.** Do unmaking, fusing and travel between two worlds work, with something made on the moon from the moon's own field, and can a mind use them to get home?

**The world** (`MoonWorld`): Ada is on the moon after P3's voyage, her skiff moored there. The moon is its own place with a sparse field: its pool is nearly dry (2). The last of PHYSICS.md's gerunds:
- **Unmaking:** an old husk pushed hard goes back whole into the moon's field (30). The pool glimmers again. This is the only way to potential here.
- **Drawing and forming:** a flask draws from the pool in levels (`charged` to 5, `brimming` above). A basin holds a lantern's pattern and forms the lantern from the flask: a thing made from the moon's own field.
- **Fusing:** the lantern pushed hard onto the skiff joins it (`skiff: moored → lit`). The lantern's potential and the joining's cost become the skiff's own (`skiff_fused`).
- **Travel home:** a launch releases the flask's store. The fused lantern lifts: the binding on a lit skiff is the moon's 12 less its fused 5. Over the binding: `escaping → drifting → returning → beached`, the motion going into the home world's field. Under it: `hopping` and back to the mooring.
- **The hidden condition is the track's first AND:** lit *and* a brimming flask.
- **The ledger spans the moon and home.**

**Two minds:** fresh, and **carried** (Ada's mind from P3's steady run: the hill, the jar, the brim, the voyage out).

**My choices (named):**
- **The curriculum** (`run_stages`): the same world and the same mind wanting in turn the pool glimmering, the skiff lit, the skiff home. These are authored sub-wants, as a person sets herself steps. Each stage is a `GerundelleMind` carrying the last one's Mind and beats, as fiction's rung 6 carried a mind between scenes.
- **No settling between stages.** The mind acts while a scene settles, and in the first curriculum it spent the lit skiff in the 8 ticks after lighting it.
- **The planner crash** (finding 5) is read as "no plan".

**A physics change, a failure first:** **the fused lantern lifts; it isn't burned.** At first a launch released the fused store along with the flask's, so a hop burned the lantern. The first launch any mind made in the last stage was lit with the flask spent by the fusing: it hopped and undid the whole preparation. In P3 a failed launch cost one jar fill; here it cost the lantern, the fusing and every draw behind them. Generous first (PHYSICS.md principle 4) means a wrong try shouldn't cost everything before it. The lantern now stays in the skiff and goes home with it. This also answers PHYSICS.md's open question on fusing: the parts' potential sums, and the whole has a property neither part had (lift).

### Results

**One want (sail home), 1500 ticks: nobody gets home, fresh or carried, in any of five temperaments.** Every new power was used. Steady, restless and dogged unmade the husk, formed lanterns, fused and hopped, but none put the seven steps together.

**The curriculum, 800 ticks per stage:**

| Mind | Temperament | Pool glimmering | Skiff lit | Home |
|---|---|---|---|---|
| fresh | steady | yes (89) | yes (85) | **yes (86)** |
| fresh | patient | yes (89) | yes (85) | **yes (86)** |
| fresh | restless | yes (157) | yes (30) | no |
| fresh | dogged | yes (179) | no | |
| fresh | impatient | yes (89) | gave up (47) | |
| carried | **dogged** | yes (**13**) | yes (144) | **yes (207)** |
| carried | steady | yes (13) | yes (215) | no |
| carried | restless | yes (13) | yes (250) | no |
| carried | impatient | yes (13) | gave up (70) | |
| carried | patient | yes (13) | no (150, gave up) | |

Conservation held at every slice of every run, across the moon and home. All three voyages home round-trip at 1.00 (88, 88 and 122 sentences).

The fresh steady story, its last stage:

> ... She pushed the lantern hard, and it melted into the skiff. The skiff began to shine. The basin lay empty again. The flask went dark. ... She dipped the flask into the pool, and it began to glow. ... She dipped the flask into the pool. But this time the flask brimmed with light. ... She pushed the skiff hard. The skiff climbed past the stars and came down on the hillside at home. The flask went dark. Ada realized that the skiff went home only when the flask was full. She marveled at the skiff. She was delighted with the skiff.

### Findings

1. **The physics set is complete, and every power is used by minds that weren't told it exists.** Drawing, spilling, forming, cleaving, unmaking, fusing, propelling, flying, escaping, drifting and arriving in both directions are all built, and potential is conserved across two places at every slice. Minds found unmaking (the husk "crumbled into light"), forming from another world's field, and fusing on their own, by contrast.
2. **A distant want with a seven-step chain is beyond Gerundelle; intermediate wants carry it.** With one want no mind got home. With three wants in order, three did. Gerundelle's experiments are two steps (a preparation and an action) and its planner looks three ahead. A mind needs steps between it and a far goal. In a civilization, that is what a culture's intermediate goals (apprenticeship, a curriculum) are for. It's also the clearest "what's missing" in the mind so far: making its own sub-wants.
3. **The past transfers, unevenly.** The carried mind (P3's) made the pool glimmer **in 13 ticks against 89–179 fresh**, in every temperament: its experience of draws and stores pays at once. Dogged couldn't light the skiff fresh, and carried it went all the way home. Steady and restless, carried, lit the skiff more slowly (215, 250 against 85, 30) and didn't get home. The hill's lessons (the jar's brim on a resting skiff) don't map onto the moon's (a flask, a moored or lit skiff), and a mind holding the old way may test the new one less. Experience helps where the shapes match and costs where they don't.
4. **The cost of a wrong try is a design knob, and generous worlds must keep it small** (the physics change above). The same AND condition is unlearnable when a failed try destroys the preparation, and learnable when it doesn't. A harsh world filters out minds that learn by trying. That's a what-if for later: a world where mistakes are expensive.
5. **Gerundelle's planner crashes** when a rollout reaches a state with no known action (`molecules.mcts`, `pick` returns `best[1]` with `best` None, `molecules.py:3716`). It happened 800 times in one carried run before the guard. The fix is one line in Gerundelle (stop the rollout when there is no action) but belongs to its backup-and-suite discipline.
6. **Patience still decides.** Impatient gave up on lighting the skiff in both minds, and patient gave up once carried.

### Not yet done

- Ranges over orders (deterministic runs).
- The lean arm.
- Minds making their own sub-wants (finding 2).
- The planner fix in Gerundelle (finding 5).
- A round trip in one run: P3's voyage out and P5's home as one curriculum.

## Rung P6: minds that set their own sub-wants, and Gerundelle's planner fixed (`p6.py`; Gerundelle `molecules.py`, `sov_agent.py`), 2026-10-30

**Question.** Can a mind set itself the intermediate wants that P5's curriculum authored for it, and so reach a far want on its own?

### Changes inside Gerundelle (`E:/vscode/analogy/molecules`), under its discipline

| Step | Result |
|---|---|
| backup before any change | `backup/molecules_2026-10-30/` (all `*.py`, `SHA1SUMS`: `molecules.py` 7b255edd…, `sov_agent.py` 1f142d75…) |
| suite on the unchanged code | 72/80, 2 pending: **identical to the reference** (`../cognitivecode/backup/fails_after_honest_repair.txt`); `backup/tests_baseline_2026-10-30.log` |
| the changes (below) | `molecules.py` 7272ae12…, `sov_agent.py` 2283c185… |
| suite after the changes | 72/80, 2 pending: **identical to the baseline** (`backup/tests_after_p6_2026-10-30.log`, `backup/fails_after_p6_2026-10-30.txt`) |

1. **The planner fix** (`molecules.mcts`): a rollout that reaches a state where the mind knows no action ends there with what it gathered, and a root with no action returns no plan. Before, `pick` returned `best[1]` with `best` None and crashed (P5 finding 5: 800 times in one carried run). Only paths that used to crash change. P5's guard in `p5.py` is now never needed.
2. **Sub-wants** (`Params.subwants`, `Params.sub_budget`; `SovAgent.planned`, `subwant`, `needs`, `makers`, `drop_sub`). **Off by default**, so every existing world, fiction's and cognitivecode's arms, and the suite run as before. When the planner finds no way to a want, the mind sets a nearer one, from its own records:
   - **a way known:** a push that has brought the want before. What it needs and doesn't have now (its configuration, and the condition of the split half whose outcomes brought the want) is the sub-want. This recurses.
   - **no way known:** Inquiry's "a situation it was never tried in", across steps. A combination of states of the wanted object and of the objects its pushes' conditions name, seen but never together at a push on it, is made one fact at a time. Each fact must be one some known push has brought about.
   - **Bookkeeping:** sub-wants are held on a stack (at most four deep). One that's met hands back to the want it served. One not met within `sub_budget` (80) ticks, or whose claims fail as often as the mind's patience, is dropped (not given up) and not set again. A sub-want met doesn't count as the want reached (`agent.reached` keeps root wants only); it's logged in `agent.sub_log`.

### Results (single wants, fresh minds, 1500 ticks; `results/p6_sweep.txt`)

| World | Temperament | Sub-wants off | Sub-wants on | The sub-want it set |
|---|---|---|---|---|
| moon (P5's way home) | steady | not reached | **home, 286 ticks** | fill the flask (`flask_charged`) |
| moon | restless | not reached | **home, 351** | fill the flask to the brim |
| moon | dogged | not reached | not reached | none |
| moon | impatient, patient | gave up (79, 203) | gave up (same) | none |
| voyage (P3's moon) | steady | arrived, 265 | **arrived, 225** | fill the jar to the brim |
| voyage | restless | not reached | **arrived, 307** | fill the jar to the brim |
| voyage | dogged | arrived, 67 (lucky) | same | none |
| voyage | impatient, patient | gave up | gave up | none |

Conservation held at every slice in every run. The sub-wants are told as beats of their own. Restless's story on the moon (91 sentences, round-trip 1.00), its end:

> She dipped the flask into the pool, and it brimmed with light. She dipped the flask into the pool again, but nothing happened. She shook the flask, and it went dark. She set out to fill the flask to the brim. ... She dipped the flask into the pool, and it began to glow. She dipped the flask into the pool again, and it brimmed with light. ... She pushed the lantern hard. But this time the lantern melted into the skiff. The skiff began to shine. ... She shoved the skiff, and it climbed past the stars and came down on the hillside at home. The flask went dark.

### Findings

1. **A mind that sets its own sub-wants reaches the far want that no temperament reached alone.** On the moon's single want, steady and restless now get home. On P3's, restless now arrives, and steady arrives sooner. Each set exactly one sub-want.
2. **The sub-want closes the last gap; it doesn't build the chain.** In every success the sub-want was the condition the minds had never combined with the rest: the flask or jar to the brim. Exploration had already found the pool, the lantern and the lit skiff, and what was missing was holding one more state *for* the want. P5's curriculum authored three wants; the minds needed to set themselves only the one they couldn't stumble into. That's the "untried situation" rule doing what Inquiry does for one step, across several.
3. **Where sub-wants don't help, the reason is visible.** Dogged set none: its pushes on the skiff carried no learned conditions, so there was nothing to combine. Impatient and patient gave the real want up before the planner ever ran dry, because patience counts failed claims on the wanted region, which come early. Sub-wants need something learned to reason from, and a mind that stays long enough to use them.
4. **The planner fix is invisible where nothing crashed**, which is what it should be. The suite and every earlier rung behave identically, and the carried-mind runs in P5 no longer need the guard.

### Not yet done

- The lean arm.
- Ranges over orders.
- Sub-wants in the population world (P4): does setting oneself "keep the jar brimming" turn interference into defending a state?
- A mind's own sub-wants for chess (`../chess-sov-plan.md`, "Per plan"): the same mechanism, against an opponent who moves between your steps.

## Rung P7: sub-wants in a population (`p7.py`; Gerundelle `sov_agent.py`), 2026-10-30

**Question.** In P4's commons, where curiosity emptied each other's jars and only 1–2 of 4 wants were met, does a mind that sets itself "my jar to the brim" defend that state, and does the population reach more?

**Setup.** P4's `StationsWorld` and runner (`p4.run` now takes `subwants` and the mind class), with Gerundelle's `Params.subwants` on for every mind. Each population runs off and on. With sub-wants off, P4 reproduces exactly (1 of 4, Dee at t4236, the same per-mind numbers).

**The prediction, written in `p7.py` before the first run:** more wants met, minds re-making states others undid (defending by remaking), more anger, and pushes on others' stations not falling much.

**A Gerundelle change, a failure first: try the push in the situation made for it.** In the first run one mind (Ada) set 58 sub-wants, all on her own jar, and met 57, but **55 were re-makes**: she cycled `jar1_charged`, `jar1_brimming`, even `jar1_empty`, and never launched. The "situation never tried" rule skipped a combination once it held and set the next one at once, so the push the combination was made for never came. In P6's single-mind worlds exploration happened to make the launch; in a crowd it didn't. Now, when the situation that holds is itself one never tried, `subwant` returns the push to try in it (`("try", invitation)`, logged as `tried`), and the means-ends loop closes: set, met, tried. The suite after the change: 72/80, 2 pending, **identical to the baseline** (`backup/tests_after_p7_2026-10-30.log`); `sov_agent.py` 1afe1fbd….

P6 rerun with the fix (`results/p6_sweep_after_p7.txt`): the same five runs succeed, with the loop visible in each (e.g. "set jar_brimming, met jar_brimming, tried hard_push:skiff_resting"). Ticks: moon steady 362, restless 384; voyage steady 213, restless 283 (P6's table above is from before the fix).

### Results (2000 rounds)

| Population | Measure | Sub-wants off (P4) | Sub-wants on |
|---|---|---|---|
| steady ×4 | wants met | 1 of 4 (Dee, t4236) | **2 of 4** (Dee t4236; **Ada t5047, own launch**) |
| | changes on others' stations (Ada / Ben / Cal / Dee) | 45 / 38 / 47 / 6 | **15** / 34 / 41 / 6 |
| | own-station share (Ada) | 0.39 | 0.35 |
| | sub-wants set / tried | — | Ada 0 / 1; others none |
| steady, restless, patient, dogged | wants met | 2 of 4 (Ada **by Ben's launch**, Dee t4258) | **1 of 4** (Dee, **t2575**) |
| | changes on others' stations (Ada / Ben / Dee) | 47 / 62 / 53 | **17 / 28 / 10** |
| | own-station share (Ada / Dee) | 0.31 / 0.37 | **0.44 / 0.51** |
| | sub-wants set / tried | — | Ada 0 / 1, Dee 0 / 1 |

Conservation held at every slice in all four runs. Anger: 0 and 1 (Cal, patient, mixed), unchanged by sub-wants.

### Findings

1. **No defending, against the prediction.** After the fix no mind re-made a state another undid. The 55 re-makes of the first run were the rule's own cycle, not defence. A mind with sub-wants in a crowd doesn't guard its jar. It acts sooner in the situation it wanted: one "try" per successful mind, launching the moment its skiff and jar first stood in the untried combination. Defending a state would need the mind to want the state to *last*, a keeper's want (fiction rung 4), which no sub-want is.
2. **Interference falls sharply, and minds keep closer to home.** In the mixed population, changes on others' stations dropped from 47/62/53 to 17/28/10 and own-station shares rose. Wanting something near (or trying the want as soon as it can) leaves less room for the curiosity that emptied others' jars in P4.
3. **Fewer accidents cuts both ways.** Steady ×4 went from 1 to 2 wants met. The mixed population went from 2 to 1: Dee arrived far sooner (t2575 against t4258), but Ada lost the arrival Ben's curiosity had given her with sub-wants off. In P4, help was an accident of undirected curiosity. Directing minds removes the harm and the help together. Deterministic, one run each: a direction, not a measured range.
4. **Sub-wants need something learned on the wanted object.** Ben and Cal never set a sub-want or tried one: in the crowd their pushes on their own skiffs carried no learned conditions to reason from (P6 finding 3 again). The crowd's noise, which kept minds' conditions from forming in P4, also keeps sub-wants from forming.

### Not yet done

- **A keeper's sub-want** (a state wanted to last, defended when undone) is what defending needs. Fiction rung 4 has keepers; Gerundelle's sub-wants don't.
- Ranges over turn orders.
- The lean arm.
- Stories of the population.

## Rung P8: a keeper's sub-want (`p8.py`; Gerundelle `molecules.py`, `sov_agent.py`), 2026-10-30

**Question.** P7 found no defending. Does a mind that keeps the state it made for its want restore it when something else undoes it, and does that change what a population reaches?

### The change inside Gerundelle

`Params.keep_subs`, **off by default**, needs `subwants`. `SovAgent.keep_watch` runs before the mind chooses:
- A sub-want met is **kept** for the want it serves.
- A kept fact that is gone is **used** if the mind's own last push changed its object away from it (a launch spends the jar it was filled for), or **restored** otherwise: set again as the current want, the current one held above it.
- A kept fact whose want is no longer held is **released**.

One fix along the way, a failure first: at first "the mind's own last push changed its object" included the push that *made* the kept fact (filling the jar changes the jar), so a theft right after filling read as use. Now only a push that changed it to something else counts.

Discipline: backup `backup/molecules_2026-10-30b/`. The suite after the change: 72/80, 2 pending, **identical to the baseline** (`backup/tests_after_p8_2026-10-30.log`). `molecules.py` c59b118d…, `sov_agent.py` 71c10870….

### Results

**Populations (P7's, with sub-wants on, keeping off against on, 2000 rounds):** steady ×4, steady ×2 and steady + restless are **identical with keeping on and off**, number for number. Keeping never engaged: no mind *set* a sub-want in any population (only P7's immediate "try"), so nothing was ever kept.

**The controlled test (`--thief`).** In P3's voyage, one mind with sub-wants on, and an authored thief (named; fiction's take and give are the precedent) who spills the jar right after each "jar brimming" sub-want is met, before the launch it was filled for, twice:

| Temperament | Keeping | Thefts | Reached | Ticks | What followed each theft |
|---|---|---|---|---|---|
| steady | off | 2 | yes | 239 | `set jar_brimming` again, met, and finally tried |
| steady | on | 2 | yes | 239 | `restored jar_brimming`, met, and finally tried |
| restless | off | 2 | yes | 309 | `set` again |
| restless | on | 2 | yes | 309 | `restored` |

Without the thief (P6 after P7's fix): steady 213, restless 283. Conservation held throughout.

### Findings

1. **Sub-wants already defend, by re-deriving.** After a theft, the want still needs the jar brimming, the planner still finds no way, and the sub-want rule sets the same condition again. Explicit keeping restores the same fact at the same moment: same outcome, same ticks. A mind that reasons from its want back to what the want needs restores whatever is undone without a separate rule. Keeping is redundant, and it stays off.
2. **Each theft costs the time to remake** (about 12 ticks of refilling here: steady 213 without the thief, 239 with two). Defending by remaking always loses that time to the thief. It recovers, but doesn't prevent.
3. **No anger at two thefts.** The mind felt frustration and anxiety over a contested jar, not anger at someone. Gerundelle's anger needs a purposeful other: a mover whose doings keep recurring (a significance test on its responsiveness). Two spills aren't a pattern.
4. **Defending a state, as distinct from remaking it, needs something the physics doesn't have: a way to stop another's push.** Every push here can be made by anyone. The force vocabulary already has the gerund for it (`locking`: holds against a push until released, `FORCE_VOCABULARY.md`). A lock its maker can open and others can't would let a mind *hold* a state rather than keep remaking it, which is possession in physical terms. That is the step toward the original ladder's conflict rung, where territory is held, contested and lost.

### Not yet done

- A physical lock (finding 4): possession as physics, and what a population does with it.
- Anger at a repeated thief: how many thefts make a purposeful other.
- Ranges, the lean arm, stories of the population.

## Rung P9: a lock (`lock_world.py`, `p9.py`), 2026-10-30

**Question.** Give the world possession as physics. What does a population do with it?

**The world** (`LockWorld`, StationsWorld with a lid per jar, after FORCE_VOCABULARY.md's `locking`):
- **A push on an open lid shuts it**, and the lid takes the hand that shut it.
- **Shut, it opens only to that hand.** Anyone else's push on it does nothing.
- **A shut jar can't be dipped or spilled by anyone**, its keeper included (the keeper opens it first). It still feeds its hollow and skiff, which are mechanisms, not hands.
- **My choice (named):** the lock is bound to the actor who set it (`world.actor`), as StationsWorld already keeps who set each motion going.
- Principle 0 and conservation hold; a lid holds no potential.

**The prediction, written in `p9.py` before the first run:** nothing tells a mind which lid is its own, so curiosity shuts lids at random, others' as often as its own. Minds are locked out of their own jars, with frustration and anger at whoever locked them. **Possession without norms is enclosure:** wants met fall below P4/P7, and interference falls (locked jars can't be emptied).

### Results (2000 rounds; sub-wants off and on gave identical runs, number for number)

| Population | Wants met (P4 → P9) | Lids shut, own / others' | Locked out of a jar or lid (by others / by own lock) | Lids shut at the end (lid: keyholder) | Anger |
|---|---|---|---|---|---|
| steady ×4 | 1 → **1** (Ada, **t657**; P4's Dee at t4236) | Ada 0/0, Ben 0/4, Cal 0/1, Dee 3/7 | Ben 67/1 (53 by Dee), Cal 16/2, Dee 17/**85** | Ada's jar: Cal; Ben's: Dee; Cal's: Dee | 0 |
| steady, restless, patient, dogged | 2 → **0** | Ada 0/0, **Ben (restless) 6/11**, Cal 0/0, Dee 1/4 | **Ada 66** (63 by Ben), Ben 15/26, Cal 21 (by Ben), Dee 40 (by Ben) | Ada's jar: Ben; Cal's: Dee; Dee's own: Dee | 0 |

Changes on others' stations fell (steady ×4: 2–15 per mind against P4's 6–47). Conservation held in every run.

### Findings

1. **Enclosure, as predicted.** Minds lock other minds' jars more than their own (Ben 0/4, Dee 3/7; in the mixed population restless Ben 6/11), because a lid is just another pushable thing to curiosity. At the end of both runs, most jars that were shut are held by someone other than their station's mind, and one mind holds two. Possession arrived before any sense of whose things are whose.
2. **Temperament decides who encloses.** In the mixed population the restless mind did most of the locking (11 of others' lids) and locked out every other mind, down to 0 wants met (P4: 2). The trait that explored most widely in P1 and P2 here takes the most.
3. **Locks protect as well as exclude.** In steady ×4, Ada reached her want at t657, far sooner than any mind in P4, because locked jars can't be emptied and interference fell. The same lock that shuts others out keeps a filled jar filled, when it falls on the right lid by chance.
4. **No anger, against the prediction, even at 63 lockouts by the same mind.** A push a lock stops changes nothing, so to the mind locked out it reads as "the jar won't move", a failed claim (frustration), not another undoing what it held. The lid was shut in the other's slice, but nothing links that to the mind's own failures. **Exclusion without perceived agency produces frustration, not grievance.** Anger at an encloser needs the mind to see the lock as someone's.
5. **No mind uses a lock to hold its own state.** Locks were shut by curiosity, not for a want. Locking one's own filled jar before launching would be possession for a purpose. It needs a want for the state to last plus knowing the lock protects it, which no mind here has learned. Sub-wants again never engaged in a crowd (the third rung running), so P8's keeping couldn't reach for the lid either.
6. **Dee locked herself out 85 times**, pushing on jars behind lids she had shut. A mind can enclose itself.

### Not yet done

- **Whose things are whose:** a perceived mark of ownership (the lock showing whose hand shut it, so a locked-out mind can see the lock as someone's), and whether that turns frustration into grievance (finding 4).
- **Locking for a purpose:** a mind that learns "shut lid keeps the jar full" and locks its own state before using it (finding 5).
- Ranges, the lean arm, stories of the population.

## Rung P10: the mark (`lock_world.py` `marks`, `p10.py`), 2026-10-30

**Question.** P9's locked-out minds felt frustration, not grievance: nothing they perceived linked a lock to a hand. If the lock shows whose hand shut it, does attribution enter what minds know, does grievance come, and does behaviour change?

**The world.** `LockWorld(marks=True)`: a shut lid's state names its keeper (`lid1: shut by Ben`). So pushing "a lid shut by Ben" and "a lid shut by me" are different actions; a failed dip can be conditioned on `lid1_shut_by_Ben`; and Ben's act shows on the lid. Otherwise P9's world. Sub-wants are off (they didn't engage in a crowd at P7–P9).

**The prediction, written in `p10.py` before the first run:** attribution enters knowledge (conditions that name another's lock); still no anger (Gerundelle's anger needs a held region undone, and a locked-out mind rarely held the lid); behaviour barely changes (the mark is perception, not a norm), and wants met stay near P9's.

### Results (2000 rounds)

| Population | Wants met (P9 → P10) | Anger | Learned conditions naming a keeper | Pushes on others' locks, 1st / 2nd half: **P9 (no marks)** | **P10 (marked)** |
|---|---|---|---|---|---|
| steady ×4 | 1 → 1 (Ada, t657) | 0 | **none** | Ben 16/13, Cal 8/0, Dee 5/4 | Ben **28/0**, Cal **14/0**, Dee **34/0** |
| steady, restless, patient, dogged | 0 → 0 | 0 | **none** | Ada 1/4, Ben (restless) 0/10, Dee 3/5 | Ada **3/0**, Ben **14/0**, Dee **13/0** |

The minds kept acting in the second half (steady ×4: Ben 124 pushes, Dee 163; mixed: Ada 56, Ben 84, Dee 44), so the drop to zero is a change of what they do, not quiet. Minds still shut others' lids (steady ×4: Ben 8, Cal 3, Dee 9 over the run; mixed: Ada 4, Ben 15, Dee 6), and lockouts continued (Ben locked out by Dee 46 times). Conservation held.

### Findings

1. **The mark teaches futility, not a norm.** With marks, every mind stopped pushing other minds' locks by the second half, while still acting. Without marks they kept trying to the end. "A lid shut by Dee" is an action of its own that never once worked for Ben, so its pull fell to nothing. Without the mark, "a shut lid" was one action that sometimes opened (one's own) and sometimes didn't, and there was no futility to learn. Others' property comes to be left alone because trying it never pays: respect by futility. Early on the marks drew *more* pushes (each new "shut by X" is an untried action to curiosity) before the drop.
2. **Attribution didn't enter learned conditions, against the prediction.** No mind learned a condition naming a keeper. What a mind learns about others' locks lives in the *action* ("pushing a lid shut by Dee does nothing"), not in a condition on its own jar ("my jar fills only when it isn't locked by Dee"). Conditions rarely form in a crowd at all (P4, P7).
3. **No anger, as predicted.** Seeing the hand on the lock isn't grievance. Gerundelle's anger is about a region the mind held, undone by another. The locked-out mind never held the lid, and the jar it wanted didn't change; it just wouldn't respond.
4. **Enclosure goes on.** Minds still shut others' lids, and wants met are unchanged. The mark stops minds trying others' locks; it doesn't stop them making the locks. Futility protects the encloser's hold, not the enclosed mind's access.

### Not yet done

- **Grievance:** what would make a locked-out mind angry at the hand on the lock. In Gerundelle terms, its jar would have to be a region it holds, so that the lock undoes its hold. A first claim (a mind's first dip into its station's jar) is the obvious candidate.
- **Locking for a purpose**, carried over from P9.
- Ranges, the lean arm, stories of the population.

## Rung P11: grievance (`lock_world.SealWorld`, `p11.py`), 2026-10-30

**Question.** P10's lid was a separate object, so a jar a mind held never changed when another locked it, and Gerundelle's anger is about a held region undone by another. If the lock is a state of the jar itself, and the mind sees who did it, does grievance come?

**The world** (`SealWorld`): a third push on a jar, `seal`, seals it and shows the hand (`jar1: charged sealed by Ben`). A sealed jar can't be dipped or spilled by anyone; only the sealing hand unseals it; it still feeds its hollow and skiff, its level showing through the seal. A seal by another is a change, by another, to a jar the mind may hold: its **first claim** is its own dips having taken (Gerundelle's territory: `ever`). Sub-wants are off.

**The mover made visible** (`Grieving`, a named choice; fiction rung 5's authored "Leo took it" is the precedent): fiction's `look()` already finds who moved each object in another's slice but never wrote it into the territory, so Gerundelle's anger at "the one who took it" (`taken_by`) could never form between Gerundelle minds. `Grieving` writes the mover onto any region the mind has held. Runs were made both ways (`--blind`: not written).

**The prediction, written in `p11.py` before the first run:** anger at the sealer, anchored on the jar, in minds that held the jar it sealed; enclosure as in P9/P10; wants met near P9/P10's.

**A bug on the way, mine:** inserting `SealWorld` into `lock_world.py` split `LockWorld`, so its lid `push` landed inside `SealWorld`. That was caught by the smoke test before any P11 run and put back. P9's and P10's results were made before the insertion.

### Results (2000 rounds; mover seen and not seen gave identical runs)

| Population | Wants met (P4 / P9 / P10 → P11) | Seals own / others' | Seals by others on jars the mind had claimed | Anger |
|---|---|---|---|---|
| steady ×4 | 1 / 1 / 1 → **0** | Ada 0/9, Ben 0/8, Cal 0/0, Dee 0/6 | 14, 15, 16, 10 | **0** |
| steady, restless, patient, dogged | 2 / 0 / 0 → **3** (Dee t2203, Ada t4825, Ben t5937) | Ada 0/14, Ben 0/10, Cal 0/0, Dee 0/22 | 28, 25, 28, 20 | **0** |

Conservation held. Anger didn't even form in Gerundelle's phase register (not just failing to win attention).

### Why there is no grievance: Gerundelle's theory of possession

`Territory.update` (`molecules.py:3007-3016`): a held region whose holding fades goes, after the mind's half-life, to **`another`** if anything else has moved it ("someone else holds it now"), and to **`lost`** only if nothing else moved it, or if it's **gone** from view (line 2988, fiction rung 5's toy carried off). Sadness and the anger at "the one who took it" form only on `lost`. The jar rows show it: Ben's and Cal's claimed jars went to `another`, and Ada's jar1 went `lost` once, from her own failing claims, before anyone's move was recorded on it.

So **in Gerundelle, a thing taken but still in sight becomes the taker's: concession, not grievance.** Grief needs the thing gone. Anger's other route (a frustrated claim conditioned on a state a purposeful other keeps, `molecules.py:2297`) needs a learned condition on the claim and a mover whose moves always leave the same state. Neither forms among curious minds in a crowd.

### Findings

1. **No grievance, against the prediction, and the reason is Gerundelle's model, not the world or the perception.** The seal changes the held jar, the mover is visible, and Gerundelle reads the result as the jar now being the sealer's. Whether that is right is a question about Gerundelle's theory of possession, not something to tune here: it decides whether a population of these minds can have grievance at all. Recorded as a decision for the user, below.
2. **Every seal is on someone else's jar.** Across both populations, 69 seals and **not one on a mind's own jar**. To curiosity, sealing is something to do to whatever is there, and a mind's own jar is rarely unsealed and in reach when the push comes.
3. **Seals cut both ways by population.** Steady ×4 met no wants (P9/P10: 1). The mixed population met 3, its best in the track (P4: 2; P9/P10: 0). A sealed jar can't be emptied but still feeds its skiff, so a seal by anyone protects a filled jar's launch. Whether that helps depends on whose jar is sealed when it's full. One deterministic run each: a direction, not a range.
4. **Seeing the mover changes nothing on its own.** Written or not, the runs are identical. Perception that no rule reads is inert.

### Decision for the user

Should Gerundelle read **a held region taken by another and still in view** as a loss to grieve, with anger at the taker, instead of as the taker's now? This would be an opt-in `Params` switch, off by default (the suite unchanged), as with sub-wants. It's the change that would let grievance, and from it the original ladder's conflict, arise in these populations.

### Not yet done

- The decision above, and a rerun of P11 with it.
- Locking for a purpose.
- Ranges, the lean arm, stories of the population.

## Rung P12: grievance, as a switch and as a trait (`p12.py`; Gerundelle `molecules.py`), 2026-10-30

**Question.** The user's decision on P11: both an opt-in switch and a trait. When a mind reads a held thing taken in view as a loss, does grievance come, at whom, and do grievers beside conceders differ?

### The change inside Gerundelle

**`Params.grievance`**, **off by default**, and set per mind, so it is a trait (`p4.run` now takes per-mind Params). In `Territory.update`, a held region whose holding fades past the mind's half-life after something else moved it is **`lost`** for a mind that grieves, and **`another`** (the taker's) for one that concedes. Gerundelle's existing phases then do the rest: sadness on the lost region, and anger at "the one who took it" when the mover was seen (`taken_by`, written by P11's `Grieving`).

Discipline: backup `backup/molecules_2026-10-30c/`. The suite after the change: 72/80, 2 pending, **identical to the baseline** (`backup/tests_after_p12_2026-10-30.log`); `molecules.py` 8a0e908c….

**The prediction, written in `p12.py` before the first run:** grievers feel sadness and anger at the sealers of jars they held, the sealer named, and conceders beside them don't. Anger changes little of what minds do (nothing in this world lets a mind act on a person, only on things), so grievance is felt, not acted on. Wants met stay near P11's.

### Results (P11's SealWorld, the mover seen, 2000 rounds; anger counted in Gerundelle's phase register)

| Population | Who grieves | Wants met | Sealed others' jars | Anger (at whom) | Sadness |
|---|---|---|---|---|---|
| steady ×4 | none (control) | 0 | Ada 9, Ben 8, Dee 6 | none | 2 (Ada, Dee) |
| steady ×4 | Ada, Cal | 1 (Cal t5327) | 9, 8, 0, 5 | **none** | grievers 1 each; conceders too (Dee 1) |
| steady ×4 | all | 1 (Dee t7347) | Ada 9, Cal 3, Dee 3 | **Ben at Ada; Dee at Ada and Cal** | all four |
| mixed | none (= P11) | 3 | Ada 14, Ben 10, Dee 22 | none | — |
| mixed | Ada, Cal | 1 (Dee t2203) | Ada 1, Ben 14, Dee 18 | **Ada at Cal and Ben; Cal at Ada;** conceders none | grievers 2 each, Ben 1 |
| mixed | all | 1 (Dee t2203) | Ada 1, Ben 11, Dee 8 | **Ada at Cal; Ben at Cal ×2; Cal at Ada; Dee at Cal ×2** | all four |

The control reproduces P11 exactly. Conservation held in every run. Anger reached the stories as feel beats (one or two per griever), and Cal's grudge closed: **forgiveness**, Gerundelle's closing of a grudge when the thing is held again.

### Findings

1. **The switch works, and the trait separates minds.** With grievance on, minds feel anger at named others. In the mixed half-and-half population the grievers (Ada, Cal) were angry and the conceders (Ben, Dee) weren't, beside each other in the same world and the same seals. Concession and grievance are now two kinds of character.
2. **Blame falls on whoever moved the held thing, not on the encloser.** In the mixed all-grieving population, patient Cal, who sealed nothing, drew 5 of the 7 angers, while restless Ben, who sealed 11 jars, drew 1. Gerundelle's anger is at "the one who took it", the last mind seen moving a region the mind held. Cal's few moves fell on things others held: dipping, spilling, forming at their stations. Ben's seals fell mostly on jars their station's minds hadn't held. Grievance tracks visible meddling with what one holds, not enclosure. The encloser who takes what nobody yet held goes unblamed.
3. **Grievance needs enough holding to lose.** In steady ×4 with half grieving, the grievers felt sadness but no anger: their held jars faded without a seen mover. Anger needs both a held thing and a seen hand, and a crowd of curious minds holds little for long.
4. **Wants met moved, but in both directions.** Mixed: 3 → 1 with grievers present. Steady: 0 → 1. Phases compete for attention in Gerundelle, so grief and anger do change what minds attend to. But with one deterministic run per population, this is a direction, not a measured effect.
5. **Felt, not acted on, as predicted.** No mind did anything *to* the one it was angry at: the world has no action on a person, and Gerundelle's anger sites ("blame?") ask, they don't push. Retaliation, and so conflict as the original ladder means it, needs a way to act on another mind's things *because of* that mind.

### Not yet done

- **Acting on grievance:** anger whose "blame?" site can be answered by an act on the taker's things (sealing the sealer's jar), which would be retaliation and the start of conflict.
- **Locking for a purpose.**
- Ranges (several orders per population, now that single runs disagree in direction), the lean arm, stories of the population.

## Rung P13: retaliation (`p13.py`), 2026-10-30

**Question.** P12's anger was felt, not acted on. If an angry mind answers its anger with an act, does conflict follow: feuds, retaliation both ways, fewer wants met?

**The mechanism** (`Avenging`, a civilization subclass of P11's `Grieving`; a named choice and a per-mind trait, `avenges`; Gerundelle is unchanged):
- **Trigger:** a live anger at another mind, answered once per anger.
- **The want:** undo something the blamed one did. Of the objects whose last change the avenger saw was that mind's move, and that it doesn't hold itself, it wants one in another state a push it knows can make.
- **How it's pursued:** held on the mind's want stack like a sub-want. Gerundelle's planner pursues it, the sub-want budget drops it if it stalls, and the mind's own want comes back after.
- **Why the arm and not Gerundelle:** who moved what is the arm's perception (fiction's `look()`, made visible at P11).
- **Setting:** P11's SealWorld, every mind grieving (P12), sub-wants off.

**The prediction, written in `p13.py` before the first run:** retaliation lands on the one blamed, often not the encloser; a grieving target is angered back; pairs fall into feuds; wants met fall below P12's.

### Results (2000 rounds; every mind grieves)

| Population, who avenges | Wants met (P12 → P13) | Retaliations (met / dropped) | Anger | Feuds |
|---|---|---|---|---|
| mixed (steady, restless, patient, dogged), all | 1 → **2** (Dee t2203, Ben t4093) | 4 (1 / 3): Ada→Dee, Ben→Cal, Cal→Dee, **Dee→Ada (met)** | Ada at Dee ×2, Ben at Cal ×2, Cal at Dee, Dee at Ada | **Ada–Dee: angry at each other and retaliated against each other** |
| mixed, Ada and Cal | 1 → 2 (Dee, Ada t3236) | 1 (0 / 1): Ada→Cal | Ada at Cal ×4 and Ben, Ben at Cal ×2, Cal at Ada, Dee at Cal | Ada–Cal angry at each other, no acts both ways |
| steady ×4, all | 1 → **0** | 2 (0 / 2): Cal→Ada, Dee→Cal | Cal at Ada, Dee at Cal ×2 | none: a chain (Dee → Cal → Ada), not a cycle |

What the retaliations wanted: Ada against Dee, `jar1_empty` (**her own station's jar**, which Dee had last moved); Ben against Cal, `hollow4_cradling`; Cal against Dee, `jar1_empty`; Dee against Ada, `jar2_brimming` (met); Cal against Ada, `jar2_charged`; Dee against Cal, `hollow3_cradling`. Conservation held in every run.

### Findings

1. **The first feud.** In the mixed population with everyone avenging, Ada and Dee were angry at each other and each retaliated against the other. Conflict in the original ladder's sense (grievance answered by an act, answered back) now arises from the minds and the physics, with no rule saying "feud".
2. **Most retaliation fails.** 6 of 7 retaliations stalled past the sub-want budget and were dropped. Undoing another's state needs a push the avenger knows and can make, and in SealWorld much of what others did is sealed, or is a state the avenger has never made. Wanting revenge is easy; doing it takes the same knowledge as doing anything else.
3. **Revenge is often undoing what was done to oneself.** The things the blamed mind last moved are often the avenger's own (that's what the anger was about), so Ada's retaliation against Dee was to want her own jar back in another state. In these minds, retaliation and restoration are hard to tell apart: what is "against Dee" is what Dee did, not something of Dee's.
4. **Grievance can run in chains instead of cycles.** In steady ×4, Dee blamed Cal, who blamed Ada, who blamed no one. Blame passes along whoever last touched what one held, and a feud needs it to come back.
5. **Wants met went in opposite directions again** (mixed 1 → 2, steady 1 → 0), as at P12. The single deterministic runs now disagree in direction from rung to rung, and the populations' results can't be read as effects until each is run over several turn orders. **This should come before the next mechanism.**

### Not yet done

- **Ranges:** each population over several turn orders (and, for the mixed one, several assignments of temperaments to stations), so that P9–P13's directions become measured effects or are shown to be noise.
- Retaliation aimed at the other's own things (what the other holds, not what it last touched), if finding 3 is to separate revenge from restoration.
- Locking for a purpose; the lean arm; stories of the population.

## Rung P14: ranges (`p14.py`), 2026-10-30

**Question.** Which of P4–P13's population results are effects, and which were one deterministic run?

**Setup.** No new mechanism. The seven population configurations (P4, P7, P9, P10, P11, P12, P13, each as its rung ran it) × the two populations × **four turn orders** (each mind first in turn; `p4.run(order=k)`), 56 runs of 2000 rounds, 14 in parallel. For the mixed population the temperaments are rotated across the stations with the order, so no temperament keeps one station. Order 0 reproduces each rung's single run (checked on P4: steady 1, mixed 2). Results in `results/p14_ranges.json` and `p14_ranges.txt`.

**The prediction, written in `p14.py` before the first run:** the single runs' directions don't all survive; wants met vary by at least one across orders in most configurations; what survives is structure: no specialization everywhere, enclosure wherever there are locks, anger only where minds grieve.

### Results (wants met per order, and the mean; means over the four orders for the rest)

| Config | Steady ×4 | Mixed | Own-station share (steady / mixed) | Locked own / others' | Anger | Feuds |
|---|---|---|---|---|---|---|
| P4 baseline | [1, 2, 3, 2] **2.00** | [2, 0, 0, 1] **0.75** | 0.31 / 0.32 | – | 0 / 0.2 | 0 |
| P7 sub-wants | [2, 3, 4, 3] **3.00** | [1, 1, 3, 2] **1.75** | 0.31 / 0.34 | – | 0 / 0.2 | 0 |
| P9 lids | [1, 2, 1, 0] 1.00 | [0, 1, 1, 0] 0.50 | 0.42 / 0.39 | 11.2/19.0, 7.2/18.5 | 0 | 0 |
| P10 marks | [1, 1, 1, 0] 0.75 | [0, 1, 1, 1] 0.75 | 0.40 / 0.39 | 12.2/20.8, 11.2/27.5 | 0 | 0 |
| P11 seals | [0, 2, 0, 2] 1.00 | [3, 1, 0, 0] 1.00 | 0.34 / 0.27 | **0/17.5, 0/31.8** | 0 | 0 |
| P12 grievance | [1, 2, 0, 1] 1.00 | [1, 2, 0, 1] 1.00 | 0.31 / 0.29 | 0/15.8, 0/24.5 | **5.2 / 5.0** | **1.00 / 0.75** |
| P13 retaliation | [0, 2, 1, 1] 1.00 | [2, 3, 0, 1] 1.50 | 0.33 / 0.28 | 0/15.5, 0/21.5 | **4.2 / 6.8** | 0.50 / 0.50 |

Conservation held in all 56 runs. Retaliations in P13: 2–4 per run, 0–1 met. In the mixed population the patient mind gives up in nearly every run.

### What survives, and what doesn't

| Earlier claim | Verdict |
|---|---|
| P7: sub-wants raise wants met | **Survives, strongly.** Steady goes up by exactly one in every order, matched order for order (1→2, 2→3, 3→4, 2→3); mixed up in 3 of 4 orders, mean 0.75 → 1.75. |
| P7: sub-wants cut interference | Survives in the mixed population (changes on others' stations 132 → 51); not in the steady (81 → 75). |
| P9/P10: locks enclose, others' more than one's own | **Revised.** Lids on others' stations are shut more often than one's own (19 vs 11), but there are three others' lids to every own one, so relative to chance minds shut their *own* lid *more* often. Lids aren't aimed at others. |
| P11–P13: seals are never on one's own jar | **Survives, without exception:** 0 own seals in all 24 seal runs. |
| P9–P11: locks lower wants met | **Survives for the steady population** (2.00 → 0.75–1.00, every lock configuration), not for the mixed (0.75 → 0.5–1.0, within its range). |
| P11: the mixed population's best result (3 of 4) | **Noise.** Order 0 met 3; the other orders met 1, 0, 0 (mean 1.00). |
| P12: grievance, and wants moving in opposite directions | Anger **survives** (about 5 per run, against 0 without grievance), and so do feuds (mutual anger in most grieving runs). Wants met don't move (P11 1.00 → P12 1.00 in both populations): the opposite directions were noise. |
| P13: retaliation, wants up in one population and down in the other | **Noise:** steady 1.00 → 1.00, mixed 1.00 → 1.50, within ranges of 0–3. Feuds aren't more common than with grievance alone (0.5 against 0.75–1.0). Retaliation rarely succeeds (0–1 of 2–4 per run). |
| No specialization | **Survives everywhere:** own-station share 0.27–0.42 against chance 0.25, a little above with locks. |

### Findings

1. **One mechanism reliably helps: sub-wants.** P7's improvement is the cleanest result in the population rungs: one more want met in every steady order, and more in three of four mixed orders. A mind that sets its own nearer wants does better in a crowd too, even though it seldom sets one (P7 finding 4). Its "try in the untried situation" is the part that acts.
2. **Locks cost a steady population about one want in two.** Every lock configuration (lids, marked lids, seals, with or without grievance) meets 0.75–1.0 wants on average against the baseline's 2.0. The mixed population starts too low (0.75) for locks to show a cost.
3. **Grievance changes feelings, not outcomes.** Anger and feuds are robust where minds grieve and absent where they don't, but wants met are unchanged, and retaliation adds nothing measurable. At this scale, conflict is felt and occasionally acted on, but it doesn't yet decide who gets what.
4. **Several single-run findings were noise,** and are corrected above: the mixed population's "best result" under seals, the opposite directions at P12 and P13, and the reading of lids as aimed at others. The structural findings held: no specialization, seals never on one's own jar, anger only with grievance.
5. **Ranges of 0–3 wants on four orders mean differences under about one want per population aren't readable** from four orders. Future population rungs should be run this way from the start.

### Not yet done

- More orders (and seeds of the world's own: e.g. the spring's starting field) for the configurations whose means are within one want of each other.
- The lean arm, now with a range to compare against.
- Stories of the population.
