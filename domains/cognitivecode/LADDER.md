# The cognitive code ladder

The same setup as `fiction/LADDER.md`, in the world of coding possibilities (`README.md`). The mind is fiction's lean
mind (`fiction/lean.py`), extended as `CodeMind` (`codemind.py`) with the additions each rung needed; the world is
poc2's operation language behind ForceWorld's interface (`codeworld.py`). Each rung is written up after it runs.

**The ladder is not complete.** Every rung ran on the lean arm only, never on Gerundelle; the additions to the mind are
unchecked against the architecture; its planning, meta-cognition, tournament and wants-from-ownership were not used;
several tables were measured by earlier versions of the mind; and the comparison with POC3 is asymmetric. See
**`INCOMPLETE.md`** for what is missing and the order in which to finish.

**Key result so far (rung 7):** codes composing statement fills from ways told and recalled, starting from POC3's four
seeds alone, found two valid color-line programs that POC3's search did not (an enumerate header with an index-read
growth; an enumerate header with an accumulating growth: in none of its 52 skeletons). Beyond POC3, not only close to
it, and with no conjunction learner: wiring each way in the slot's scope did the joining.

**Scarcity drives variety (rung 8).** Varying a held way is what reached flow 8, and it activates only under pressure:
without scarcity no code varies anything; each is satisfied by a way it already knows. Only a code turned away from
every flow it can compose turns inward to vary what it holds. Not a side effect: the design's prediction (README:
scarcity, not a novelty bonus, as the source of variety), now measured.

**What a scarce population holds depends on the order of telling (rung 9's check).** With a fifth seed the patterns
told their ways in another order, codes spent their patience on other things, and flows the same population held at
rung 8 (5 and 8) were not held. The population's output depends on its courtship history: the code world's analogue
of temperament giving different valid endings in fiction. Comparisons are run over several telling orders, and the
range reported.

## Rung 0: one open slot, one pattern, no talk (`rung0.py`)

The color line with the second part of the pair left open: `v3.append((v1[v4], <str>))`. The want: the spec passing
(`specs.CASES["color_line"]`, 89 cases). The pattern: lockstep (`ps_lockstep`, `ps_pair_output`: six roles). The
states: each role filled or empty, the slot's state the roles its value plays (or none), the spec passing or failing.
A push on the slot fills it with one of 159 complete values of its type; running the cases is the push on the spec.
The known answer: `v2[v4]`.

| order of the 159 fills | reached | tries (median, range) | distinct fills tried |
| --- | --- | --- | --- |
| alphabetical (the mind's tie-break) | yes | 3 | 1 |
| shuffled, 10 seeds | 10/10 | 178, 60-449 | 20-150 |
| the answer last, 10 seeds | 10/10 | 478 | 159 |

Plain enumeration (each fill once, then one run) would take about 80 tries on average and at most 160. The mind does
worse: about three tries per fill in the worst case.

### Findings

1. **A slot's state is what the world makes of it, not its text.** First the slot's state was its value printed: an
   edit always changes the text, so every edit "took", the slot was held at once (uniqueness pull, decaying below the
   curiosity floor), while running was paid by the want's control slot and rose toward 2, doubled on the wanted object:
   4 edits, then 396 runs. Read as the roles its value plays, an edit that plays no role leaves the slot as it was, as a
   push that does not cross the latch's grip leaves it seated.
2. **No partial credit, no gradient: the mind scans.** One fill in 159 plays any role, and all six roles fill at once
   (`ps_pair_output` counts a pairing only once a lockstep pair exists). Nothing is partly right, so no mind alone can do
   better than scanning. This is the baseline: what the next rung gains must come from the pattern's guidance, not
   from a smarter scanner.
3. **Inquiry assumes a moving world.** About half the edits re-try fills that already did nothing: the inquiry term
   ("try it at another moment", `LeanMind.value`) pays for a push again while its conditions slot is open. In fiction
   the moment mattered (the wind); in a code world nothing changes between tries unless the mind acts, so a repeat
   under the same facts teaches nothing. Inventory note: inquiry should be gated on whether the world can change
   between tries without the mind's action. Not changed yet (the mind is fiction's, unchanged).
4. **With both parts of the pair open** the roles can fill only jointly: the lamp's AND (fiction rung 9), which
   neither fiction mind learned. It is a later rung, not this one.
5. As in fiction (rung 6), the tie-break among equal pushes is alphabetical: the answer comes first by its name. The
   fair test shuffles the fills' order by seed (`CodeWorld(order=...)`), and puts the answer last (`last=...`).

## Rung 1: courtship (`rung1.py`, `codemind.py`)

Rung 0's scene, with the pattern present as a mind the code can ask. The pattern's knowledge is not scripted: it has
been followed before. Its past is rung 0 lived once on its own copy of the world (its own order of the fills), kept as
its ledger, as Ben's prologue was in fiction's rung 2. One capability added to the mind (`CodeMind`, `lean.py`
unchanged): **asking the way to a condition**. Stuck on a condition it cannot bring about by any push it has tried, the
mind asks which push gives it; the teller answers from its lived tries, in shared words (the value, `v2[v4]`, not its
own ordering of the fills); the answer enters told, funded at half.

The courted story (the answer last in the code's order): the code runs, and the spec fails. "What keeps the spec
failing?" The pattern: its left read filled. "What fills that?" The pattern: `v2[v4]`. The code fills the slot, runs,
the spec passes, and the condition it learns from its own two runs confirms the pattern.

| config | order | reached | tries (median, range) | asks |
| --- | --- | --- | --- | --- |
| alone | shuffled | 10/10 | 178, 60-449 | 0 |
| alone | answer last | 10/10 | 478 | 0 |
| courted | shuffled | 10/10 | **3** | 2 |
| courted | answer last | 10/10 | **3** | 2 |
| ignorant | shuffled | 10/10 | 178, 60-449 | 1 |
| ignorant | answer last | 10/10 | 478 | 1 |

### Findings

1. **The gain is the pattern's knowledge, not its presence.** Courted, 3 tries in every order; with the pattern present
   and no past (ignorant), exactly the alone numbers: it says it does not know, and the code scans. Rung 0's scan is
   replaced by guidance, not by a better scanner.
2. **Two questions, not one.** The answer to "what keeps the spec failing?" was a condition on a role, and a role is not
   something the code can push: fiction's subgoal acts on the condition's own object, and with no push there the mind
   would wait in a world that never moves. The second question ("which push gives it?") joins the pattern's terms to the
   code's.
3. **The search was paid once, by someone.** The pattern's past cost a full rung-0 scan; courtship hands its result on.
   What transfers is told knowledge in shared words, funded at half until the code's own runs confirm it (the learn beat
   cites the teller), not a section of code (POC3's library, which transferred nothing).
4. **The told condition is a conflation, made harmless by the way question.** The six roles fill together, so the
   pattern's condition learner cannot tell them apart and names the first alphabetically ("left read"), though the code's
   slot is the right part. The way it was told is right, because it was what the pattern did, not what it called it.
5. Not tested here: exclusivity and territory (one code, one pattern), and a teller whose way is wrong (fiction's rung 3:
   a told way the world contradicts is retracted; here `CodeMind.subgoal` would offer it again, unretracted).

## Rung 2: a wrong answer, honestly given (`rung2.py`)

A pattern has no rival want, so it cannot lie as Leo did. It can be wrong honestly: here its past is the swapped color
line (`(meta[i], content[i])`: `v3.append((v2[v4], <str>))`, its answer there `v1[v4]`). Asked, it answers from what it
lived. Its condition carries over (the lockstep roles must fill); its way does not (`v1[v4]` here pairs the content with
itself, and no role fills).

Three things the mind needed first, found by checking before writing:
- **Retraction did not cover the way question.** `LeanMind.act` retracts only a rival's counterfeit way to the want,
  tested by the want arriving. `CodeMind` now retracts a told way when the push it named does not give the condition
  promised: a retract receipt, the teller's record marked, a surprise, anger at the teller. Borne out, it confirms him.
- **The surprise is at the fill, not the run.** `predict` has nothing for an untried push with no belief, so no surprise
  fired; and after the wrong fill the role is visibly empty, so the code never runs. "The spec still fails" never
  happens; "the role did not fill" does.
- **Waiting in a still world never ends.** With the told way retracted, fiction's subgoal finds no push on the role and
  waits for it, as for the wind's flag. `CodeWorld.still`: in a world where nothing changes unless the mind acts, a
  condition the mind cannot push on directly is searched for, watching for it.

The mismatched story (the answer last in the code's order): "What keeps the spec failing?" Its left read filled (right).
"What fills that?" `v1[v4]` (wrong here). The code fills it, the role stays empty: surprise, the told way retracted,
anger at the pattern. It searches, finds `v2[v4]`, runs, and its own runs confirm the condition the pattern gave.

| config | order | reached | tries (median, range) | runs (median) | told ways retracted | reliability |
| --- | --- | --- | --- | --- | --- | --- |
| courted | shuffled | 10/10 | 3 | 2 | 0 | 0.75 |
| courted | answer last | 10/10 | 3 | 2 | 0 | 0.75 |
| mismatched | shuffled | 10/10 | 172, 53-443 | 2 | 10 | 0.50 |
| mismatched | answer last | 10/10 | 472 | 2 | 10 | 0.50 |
| alone | shuffled | 10/10 | 178, 60-449 | 12 | 0 | (none told) |
| alone | answer last | 10/10 | 478 | 12 | 0 | (none told) |

### Findings

1. **Retraction is sound before the multi-agent rung.** Every mismatched run retracts the wrong way once and goes on; no
   loop. Reliability ends at 0.50 against 0.75 for the right pattern: the record a second exchange would discount by.
2. **A right condition saves the runs, not the search.** Mismatched, the code runs twice (median) against twelve alone:
   it knows what it is looking for and does not run until it sees it. But it does not know where, so the search is
   rung 0's (172 against 178; 472 against 478 worst). What a pattern says is worth what it says: a condition tells what,
   a way tells where.
3. **Trust records what held, not why.** The pattern was right about what and wrong about how, and its record says so
   (one confirmed of two told). The anger at it is the same phase Leo's lie formed: the phase is read off the blocked
   want and the word that failed, and does not know the teller's motive. Whether an honest mismatch should anger is
   open (Gerundelle's anger is blame grounded on the failing word, whatever the motive).
4. **The second instance of the moving-world assumption** (rung 0's inquiry was the first): waiting. Both are fiction
   mechanisms for a world with drivers of its own; a code world has none. `CodeWorld.still` gates the second; the first
   is still ungated (the search's waste is in all three rows).
5. Phases on the slot read oddly as a story: joy when the wrong fill "took" (the slot changed from empty to playing no
   role, a claim on its region), then anxiety and sadness as later fills fail there. Honest to the ownership register,
   which reads change, not usefulness; to revisit when the courtship is printed.
6. Not tested: asking again (one teller gives the same answer; a second teller is the multi-agent rung), and trust
   exercised (a later told receipt discounted by 0.50).

## Rerun of rungs 0-2: the slot's abstract value, and credit to slots

Rung 3 found that roles alone could not tell junk from the answer (below), and two changes followed. Both change what
every rung perceives, so rungs 0-2 were rerun (logs in `logs/`); the tables above are the roles-only runs, kept.

- **The slot's state carries its abstract values** over the spec's cases: the set of what it came to (`=value`,
  `=empty`, `=fault`, joined: `=value/fault`), POC.md 3h's domain. Every case, not one probe: a probe can read empty for
  a fill that is non-empty elsewhere, and "non-empty in any case" read `v5[v4]` (non-empty at the first position, a
  fault after) as `v1[v4]`. Rung 0's 159 fills now fall into 6 perceived states, not 2.
- **Credit to slots** (`OWNERSHIP_SOV.md` sec. 5, integration step 4), in `CodeMind`. With nearly every fill changing
  the slot, the plain lean mind held the slot at its first fill and ran the failing spec hundreds of times (rung 0's
  first failure again). In code a claim on a slot is made for the want, and the run is its test: a fill's claim is
  pending until a run; the fill just before a run takes if the run passes and fails if not (a lived "the spec still
  failed" on its hole); fills replaced before any run were never tested, and are neither. A run on a program unchanged
  since the last run is not offered (a still world: it can only repeat itself). Rung 0 now uses `CodeMind`.

| rung | config | order | reached | tries (median, range) | runs | before (roles only) |
| --- | --- | --- | --- | --- | --- | --- |
| 0, 1, 2 | alone | shuffled | 10/10 | 357, 110-807 | 111 | 178 |
| 0, 1, 2 | alone | answer last | 10/10 | 871, 836-888 | 190 | 478 |
| 1, 2 | courted | both | 10/10 | 4 | 2 | 3 |
| 1 | ignorant | both | 10/10 | as alone | | as alone |
| 2 | mismatched | shuffled | 10/10 | 243, 72-624 | 2 | 172 |
| 2 | mismatched | answer last | 10/10 | 676, 660-701 | 2 | 472 |

Retraction: 10/10 mismatched runs retract the wrong way; reliability 0.50 against 0.75 courted.

### Findings

1. **Finer perception costs the lone scanner** (median 178 -> 357, worst 478 -> 871): every fill that changes the slot's
   perceived state is a new situation worth a run. The guidance's share of the gain grows with it: courted stays at 4.
   Rung 1 and 2's findings hold (the knowledge, not the presence; a condition saves the runs, not the search).
2. **A claim takes when it is tested, not when it is made.** The first cut of credit took back only the fill before a
   failed run: untested fills piled up as held, credit brought the slot's strength to the base rate, and the slot read
   as lost, pulling at 1 + all it had held (9, 11, 13, rising). The mind grieved the slot, searching it for what took
   it, and never ran the answer it had put there (two of ten patterns' pasts never reached; their codes, told "I don't
   know", scanned). Fiction's grief mechanism, misfiring where held means "changed", not "worked".
3. **Runs are gated; edits are not yet.** The repeated-run gate is the inquiry note from rung 0 applied to runs; re-trying
   a fill under the same facts is still paid by inquiry (the waste is in every "alone" row).

## Rung 3: scarcity, two styles in one slot (`rung3.py`)

Fiction's rung 4 in code: two minds, one shared program, in turns. The color line in the enumerate style, the first
part of the pair open: `for v4, v5 in enumerate(v1): v3.append((<str>, v2[v4]))`. The slot admits two fills that both
pass the spec and keep every lockstep role filled: the index read `v1[v4]` and the loop's item `v5`. They differ in what
the slot plays (the index read: the left read, the position, the pair's left part, the position's use; the item: the
pair's left part only, the loop doing the reading), so the slot's state shows whose style holds it, and a replacement is
seen as an undo. Two keepers with pasts: Index made the spec pass once in the index-style color line (`v1[v4]`), Item
once in this scene. Each keeps the slot's state its passing fill gave it, by the fill in place when its past was
reached (`CodeMind.held_way`); each undo seen drains its resolve by 1 / the pull of its slot; at zero it gives up.

| resolve (Index, Item) | pushes (Index, Item) | resigned | the slot ends in | anger |
| --- | --- | --- | --- | --- |
| (2, 2) | 4, 4 | Index | Item's style | both ways |
| (4, 2) | 5, 4 | Item | Index's (`v1[v4]`) | both ways |
| (2, 4) | 4, 4 | Index | Item's style | both ways |
| (1, 1) | 2, 2 | Index | Item's style | Index at Item |
| (8, 2) | 5, 4 | Item | Index's (`v1[v4]`) | both ways |

"[Index] gave up, resigned": "...for v4, v5 in enumerate(v1): v3.append((v5[:3], v2[v4]))".

### Findings

1. **The ending is read off the minds, and resolve flips it.** At equal resolve Index gives up; doubling Index's
   resolve flips the ending to the index read; doubling Item's changes nothing (it already outlasts). As in fiction,
   who holds the slot falls out of two reserves draining, not out of which style is better: both pass the spec.
2. **What is scarce is the slot, not correctness.** The spec never enters the contest; attribution of one slot does
   (REORG.md sec. 5: exclusive roles are scarce, information is not). Anger forms both ways, from the purposeful-other
   rule: each keeps leaving the slot in the same state.
3. **Junk can satisfy a pattern's recognizer.** The first contest was between junk: each keeper's past was "make the
   slot hold my style's state", and the first fills to do it were `v5[v4]` and `v5[v4:v4]` (the facets resolve a loop's
   item to its sequence), which the spec fails. A keeper's knowledge must come from a past that reached the want that
   matters (fiction: Leo's keeper past taught him the latch), and roles alone could not see the difference: hence the
   abstract value (above). The facets (`poc2/rules.py`) were not changed: the world's physics stays, the perception is
   fixed.
4. **A keeper's way is what held when its want was reached**, not the latest push that brought the state about
   (`LeanMind.way`): two fills can give one state, and only one of them passed.
5. **The run judges behavior, not the gate.** Item's way is `v5[:3]`: it passes the spec (a one-character string
   sliced to three is itself), so its state is the item's, but POC's semantic gate (`specs.admit`) would reject it as a
   slice that does not matter. Decided (the user, 2026-10-27): the spec judges. `admit` is a search heuristic (it kept
   POC's mutation from churning on no-ops); the mind is not a search, and a fill that passes the spec is a valid claim,
   however inelegant. The gate stays in poc2, out of the mind's perception.

## Inquiry gated in a still world (rungs 0-3 rerun)

Rung 0's inventory note, done: `CodeMind.value` takes inquiry away from a push already tried under the facts as they
stand, in a still world ("try it at another moment" cannot differ when nothing moves unless the mind acts); the work
term stays. Rerun (logs in `logs/`):

| config | shuffled (median, range) | answer last | runs | before the gate |
| --- | --- | --- | --- | --- |
| alone | 66, 26-157 | 166 | 7 | 357 / 871 |
| courted | 4 | 4 | 2 | 4 / 4 |
| ignorant | as alone | as alone | | as alone |
| mismatched | 61, 23-152 | 161 | 2 | 243 / 676 |

Rung 3 is unchanged (the same endings for every resolve). All 10/10.

### Findings

1. **The lone mind is now enumeration without repeats, and better than "each fill then a run":** every fill once
   (159 in the worst case) and 7 runs in all, against plain enumeration's run after each fill (up to 318). It runs
   only when a fill gives the slot a state it has not tested. Rung 0's two moving-world assumptions are both gated now
   (waiting in rung 2, inquiry here).
2. **Every finding stands, against a sound baseline.** Courtship still turns a scan into 4 tries; an ignorant pattern
   is still no help; a right condition still saves the runs (2 against 7) and not the search (61 against 66, 161
   against 166); the scarcity contest is untouched (it never repeated a fill).

## Rung 4: regression and loss (`rung4.py`; fiction's rung 5)

Rung 0's scene, after the code has found `v2[v4]`; from then on it keeps the spec passing. Authored events (named as
fiction's take and give): **uses**, the program run on new inputs and passing, each a claim on the slot that takes
with the fill in place (the code's Mara playing with the toy); then **the spec changes** (each character now paired
with the rest of the meta-line from its position, `(content[i], meta[i:])`), its new cases in place first; then a
**use on the new inputs**, which the held fill fails. The new answer, `v2[v4:]`, is among the 159 fills. Two readings
of the loss (the user, 2026-10-27): **A**, the change takes the slot (Territory `taken_by`, as fiction's take: lost at
once; no one to be angry at); **B**, the register alone (failures lower the holding strength; contested above the
base rate, lost at it).

| reading | uses | held | grief (pull) | grief formed | the slot read | recovered (tries) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1 | 3 | sadness, **4.0** | 3 ticks after | lost | yes (35) |
| A | 3 | 5 | sadness, **6.0** | 3 ticks after | lost | yes (35) |
| A | 5 | 7 | sadness, **8.0** | 3 ticks after | lost | yes (35) |
| B | 1, 3, 5 | 3, 5, 7 | none | | nobody (s 0.03-0.07, base 0.14-0.16) | yes (35) |

### Findings

1. **Taken, grief scales with what was held**: pull 1 + held, 4, 6, 8, as fiction's toy (one play sadness, four
   heartbreak). It forms at once, and the recovery does not depend on it (35 tries in every row).
2. **By the register alone, a slot found by search is never held.** Holding strength is per region, (held + KAPPA b) /
   (tried + KAPPA), and every fill tried in the search is a claim on the slot's region: some sixty failed fills dilute
   the few confirmed ones (s 0.03-0.07 against a base rate of 0.14-0.16, five uses later). The slot never reads mine,
   so it can be neither contested nor lost: no doubt, no grief. The estimate that B would grieve after two or three
   failures assumed a strength near 1 when the loss came; a code slot starts far below the base rate. The register was
   built for regions with a few pushes (the toy, the latch); a slot has as many as its type has values. Open: strength
   per claim (the fill in place), or search fills read as a different kind of try.
3. **A learned condition can outlive its spec (Reopen).** After the change the code put `v2[v4:]` in the slot and never
   ran it: its condition, "the spec passes only if the lockstep roles are filled", forbade a run without them, and a
   slice fills none. `CodeMind.contradicts`: a run (own, or a use seen) that fails with its learned condition met
   retracts the condition, logged, with a surprise (`SOV_ALGEBRA.md`, Reopen). The authored use is seen whole (a Try
   in the code's `observed`). Fiction never needed it: nothing there contradicted a learned condition.
4. **Grief is ownership's, not memory's, in code.** With `carry_on` (a memory), `LeanMind.act` leaves a lost slot's
   sadness to the memory, which forms it only for a thing gone from view (the toy carried off). A slot never leaves
   view: no grief formed. The scene runs without a memory.
5. **A slot is never held until a run confirms a fill**, its `ever` flag included: Territory set `ever` on a pending
   take, and the slot read as lost while the code searched and grieved before anything was held; a phase forms once,
   so the regression's grief could not form after it.
6. Not tested: a rival code claiming the slot while it is open, and storage (time passing before recovery).

### Rung 4, reading B again: only runs claim (the user, 2026-10-27)

A fill that is never run makes no claim on the ownership register: a slot is not tried until a run tests it, as it is
not held until a run confirms it (`CodeMind.unclaim`: the register as it stood is put back after a fill; `credit`
records the try at the run). The register was built for objects with two or three pushes; a slot has 159.

| reading | uses | held | grief (pull) | grief formed | doubt | recovered (tries) |
| --- | --- | --- | --- | --- | --- | --- |
| A | 1, 3, 5 | 3, 5, 7 | 4.0, 6.0, 8.0 | 3 ticks after | | yes (35) |
| B | 1 | 3 | 4.0 | 3 ticks after | anxiety, a tick later | yes (35) |
| B | 3 | 5 | 6.0 | 3 ticks after | anxiety, a tick later | yes (35) |
| B | 5 | 7 | none | | anxiety | yes (35) |

Rung 0 is unchanged (seed 0: 80 tries).

7. **Theft and erosion.** Taken (A), grief is immediate and scales with held. By the register (B), the slot resists in
   proportion to what was confirmed: held a little, its strength sits near the base rate and the one failure tips it
   into loss at once (grief as in A); held five times, the failure leaves it contested, doubt forms, and the code finds
   `v2[v4:]` before the slot erodes to lost: no grief. The failed runs of the first search still count against the
   slot (they were runs), so the strength after the find is low (0.17 against a base rate of 0.20) and uses raise it.
8. Extension, not run: a rival code claiming the slot while it is open (doubt or grief with someone to blame).

## Rung 5: recall by shape across scenes (`rung5.py`; fiction's rung 6)

Scene A is rung 0: the code finds `v2[v4]` and learns what the run needs (the lockstep roles filled). At the scene's
end it keeps an episode (`CodeMind.keep_episode`): that condition, and the shape of the fill that brought it about
without its names, `indexing(ext, loc)` (`CodeWorld.shape`: a name read as where it comes from, a parameter or the
function's own, as POC3's skeletons keep it). Time passes. Scene B is the swapped color line, its second part open: the
answer there is `v1[v4]`. B's slot and spec are named apart (`part`, `spec_b`), so nothing carries over by identity.
Stuck on B's run with nothing held, the code recalls a warm episode (memory's h_site 20 and cold 0.1, as fiction's):
the condition, held as recalled (funded at half: a hypothesis), and the way's shape; it tries the values of that shape
here, untried first, and runs when the condition is met.

The recall story: B's run fails; the code recalls (warmth 0.68) "the lockstep roles filled; by `indexing(ext, loc)`";
it tries `v2[v4]` (the shape, wired wrong here: the pair would read one sequence twice), then `v1[v4]`; the roles fill;
it runs; the spec passes.

| config | reached | tries in scene B (median, range) | recalled |
| --- | --- | --- | --- |
| recall (a gap of 10) | 10/10 | **5, 4-5** | 10/10 |
| cold (a gap of 120) | 10/10 | 72, 13-134 | 0/10 |
| fresh (no scene A) | 10/10 | 72, 13-134 | 0/10 |

### Findings

1. **What transfers is a condition and a shape, not code.** (Corrected by rung 5b: as first built, the condition
   carried over by the pattern's role names, which the two scenes share by construction: a naming shortcut. It now
   carries over by structure; see 5b.) The way carries over by its shape without names. POC3's library offered 180-265 sections
   across domains and none made a valid skeleton; here the past turns a scan of 72 into 5.
2. **One shape stands for several wirings, and the run tells them apart.** `indexing(ext, loc)` fits `v1[v4]` and
   `v2[v4]` here (POC3's existential wiring: a skeleton is all its readings). Four or five tries is whether the right
   reading came first.
3. **A cold episode is as if never lived.** After 120 ticks the episode is below cold, nothing is recalled, and the
   code scans exactly as a fresh one does (the same 72): fiction's months, where Mara searched instead of remembering.
4. Caveats: the two scenes share a skeleton (only which part of the pair is open, and the spec, differ); a harder
   test is another domain of the theory (the editor's splice) or of another theory, where the roles do not carry over by
   name. In the recall story one edit outside the shape (`v1[0:0]`) came first, chosen in the same turn as the recall,
   before the recalled way could guide.

## Rung 5b: transfer across theories (`rung5b.py`, `mask.py`)

The user, 2026-10-27: rung 5's scenes share a skeleton, so the role names carry over by construction; the claim is that
conditions transfer by shape, not by name. Scene B is now another theory: the mask (select the characters of `v2`
where `v1` has `'a'`: `if v1[v4] == 'a': v3 += <str>`), perceived through its own facet (`mask_select`: test, selected,
accumulator; written in `mask.py`, registered in `rules.FACETS` at run time, poc2 unchanged), 260 fills, the answer
`v2[v4]`: the same shape, `indexing(ext, loc)`, under other role names.

**Carried by name, recall failed.** The code recalled the episode, tried the shape, put `v2[v4]` in place (its slot read
the mask's `selected`), and never ran it: it held "the lockstep left read filled", which nothing in the mask world can
be. 300 tries, not reached.

**Redesigned: carried by structure** (fiction's rung 6 mapped the latch's condition onto whatever object was now in the
latch's gerund). The episode keeps the way's shape and what the condition was structurally: that the fill made its
slot play a part in the pattern (its state names roles). In the new scene the code tries values of the shape; one
that makes its slot play a part, in whatever pattern this scene is perceived through, gives the condition in this
scene's terms (that slot's state), held as recalled, and the code runs (`CodeMind.recall`, `follow_recall`). The
condition then learned from its own runs is in the mask's vocabulary (`mask_select.accumulator_filled`).

| scenes | config | reached | tries in B (median, range) | recalled |
| --- | --- | --- | --- | --- |
| rung 5, one theory | recall | 10/10 | **4, 3-4** (was 5, 4-5) | 10/10 |
| rung 5, one theory | cold / fresh | 10/10 | 72, 13-134 | 0/10 |
| rung 5b, two theories | recall | 10/10 | **3, 3-4** | 10/10 |
| rung 5b, two theories | fresh | 10/10 | 156, 77-255 | 0/10 |

### Findings

1. **The first recall was a naming shortcut, and the harder test caught it.** Under another theory's pattern a
   condition carried by name can never be met, and the code holds the answer without running it.
2. **Carried by structure, a past in one theory helps in another:** 156 tries to 3. What crosses is a shape and a
   structural fact ("this made my slot play a part"), mapped onto the new pattern's names when seen; the new names
   are then learned from the code's own runs.
3. **The stray edit is gone** (rung 5: 5 -> 4 tries). A run whose condition was unmet looked stale after the failed
   run, plan gave nothing, and an unguided edit came first; a run with its condition unmet is never made (act turns
   to the condition), so it is not stale.
4. Caveat: "plays a part" is read off the perceived pattern, so transfer needs the new scene's pattern to recognize
   the answer at all; a pattern that cannot see the answer's structure gives the mapping nothing to see.

## Rung 6: a population and scarcity: distribution, not discovery (`rung6.py`)

**What is tested.** Scarcity spreads a population over a given space, while the same codes without exclusivity
converge on what they value most. **What is not tested:** scarcity producing variety the population discovers itself.
The space is given: POC3's color-line results (52 valid skeletons, 113 complete programs, 12 load-bearing data flows),
found by POC3's search with its novelty bonus. Every program in it passes the spec, so no code searches for
correctness here; what is measured is who ends up holding what. Discovery is rung 7's (below).

The scene: 20 codes, each a program of its own (`PopWorld`, a `CodeMind`), filling its function with one of the 113
programs and running it. The exclusive unit is the flow: one code at a time across the population. A code perceives
its slot's roles, `match` (the flow of the program in place: free, its own, or another's: seen, as one sees that
someone is married), and the spec (passing only if the cases pass and the flow is free or its own; `taken`
otherwise, a failure credited to the fill). A run on a flow another holds is a contest: the holder's reserve (2)
drains by 1, and at zero it resigns (rung 4: the want given up) and the flow is freed. Preferences (my choice): a style
is the loop kind and how the result grows; a code tries its preferred style first. **Varied** codes: half prefer the
commonest style, the rest one each of the others, each with its own order among equal fills. **Identical** codes: one
preference, one order (any spread then comes from scarcity alone). Codes test a fill in place before swapping it
(`CodeMind.test_pending`, below).

| codes | scarcity | matched | flows held (of 12) | most codes on one flow | contests | holders resigned | tries (median) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| varied | yes | 12/20 | **12, 12, 12** | 1 | 7-11 | 3 | 3-5 |
| varied | no | 20/20 | 11, 9, 6 | 6-10 | 0 | 0 | 3 |
| identical | yes | 12/20 | **12, 12, 12** | 1 | 13 | 6 | 66-72 |
| identical | no | 20/20 | **1, 1, 1** | **20** | 0 | 0 | 3 |

Three seeds each. Contests after every flow was held: **0 of 7-13** in every run.

### Findings

1. **Scarcity spreads the population over the whole space; without it, identical codes converge on one program.** With
   scarcity both populations cover all 12 flows in every seed, one code to a flow; identical codes without it all hold
   the same one. Varied codes without scarcity spread partly (6-11 flows) by their own random order among equal fills,
   which does here what POC3's novelty bonus did, and still pile up (6-10 on one flow).
2. **Spreading identical codes costs search, not luck**: a median of about 70 tries against 3-5 for varied ones. Each
   reaches for the same programs first and is turned away (it sees `taken`) before it moves on.
3. **Contest after saturation did not fire.** The README's prediction (alphas re-emerge when no unclaimed slot is left)
   was checkable here for the first time: every contest came during the scramble, while flows were still free (a code
   ran a fill whose flow another took between its fill and its run, or chose to run on a taken one), and none after all
   12 were held. The 2-5 codes still wanting at the end swap programs indefinitely and never contest: nothing in the
   mind values pushing against a held possibility when no free one is left. Contest in fiction's rung 4 came from a
   want on one contested region (the latch); here a code's want is any passing program it can hold, so it keeps looking.
   Open: whether a closed frontier should change what pays (the ownership doc's frontier tradeoff), or whether this
   population's wants are too broad to contest.
4. **Two corrections on the way.** A holder whose reserve ran out was freed from its flow but not told: it watched a
   program it no longer held; resignation now gives the want up, as in rung 4. And `test_pending`: in this space every
   program passes and every fill changes the body's roles, so each fill looked like work and the run, which only
   tests, was outbid (the codes swapped programs and almost never ran one); a fill in place and not yet tested is now
   run before another fill (a claim takes when tested, rung 4), but not when the code sees its flow is another's: forced
   then, identical codes fought over one flow until 19 of 20 had resigned. On for this rung only; rungs 0-5 were
   measured without it. A candidate for the general mind.
5. Unmatched at the end: 8 of 20 (there are 12 flows), of them 3-6 holders who lost a contest and resigned.

### For rung 7: what discovery needs (the composition machinery)

Discovery means codes build the programs, not choose among given ones, and the comparison is then with POC3 on the same
target (52 skeletons, 12 flows at its budget). What the code world lacks:

1. **Statement slots.** Every slot so far is a value. The color line's variety is in statements: the loop header
   (positions, together, with positions) and how the result grows (append, accumulate, insert). Unguided, a statement
   slot is intractable: the loop position offers 78 statement options, and a depth-first enumeration of complete loops
   reached 20,000 at depth 6, all junk, none passing the spec.
2. **Fills composed from known ways, not enumerated.** A code's ways (lived, told by a pattern, recalled by shape) are
   gerund subtrees with their names stripped (`CodeWorld.shape`). A statement fill is a known way's shape set into the
   slot and wired with names in scope: POC3's existential wiring, a finite check per skeleton. The fills on offer at a
   slot are the ways the code holds for that slot's role, not every expansion of the grammar.
3. **Sources of ways.** The patterns' instances (POC3's four hand-written seeds: positions, zip, enumerate,
   accumulate), told in courtship (rung 1); recall by shape across scenes and theories (rungs 5, 5b); and recombination:
   a way from one seed set into another seed's slot (an enumerate header with an accumulating body), which is where
   variety beyond the seeds would come from.
4. **Coordinated slots.** Changing the loop header changes what the body may read (a zip loop's items against an index
   loop's reads): two slots whose roles fill only jointly. That is the lamp's AND (fiction rung 9) and rung 0's finding
   4, which neither fiction mind learned; discovery at statement level needs a conjunction learner, or ways that carry
   the header and the body together (a way's shape spanning both slots).
5. **The measure.** Distinct valid programs and load-bearing flows found by a population of codes from the four seeds
   alone, against POC3's 52 skeletons and 12 flows, at a comparable budget of tries; scarcity on (one code per flow) and
   off.

## Rung 7: composition at statement level, from POC3's four seeds (`stmtworld.py`, `rung7.py`)

**The known ceiling, stated before running.** The four seeds (positions + append, zip + append, enumerate + append,
positions + accumulate) and their wirings reach 5 of POC3's 12 flows (1, 4, 5, 6, 7). Inserting is in no seed (flows
9-11); four flows are variants inside a seed's style (0, 2, 3, 8) that passing a way on as it is cannot reach.

**What counts as composition** (the user, 2026-10-27): not being handed a seed. No seed program is a fill. The world
has two statement slots, the loop header and the statement that grows the result (`StmtWorld`); a fill is a way, a
seed's header or growth with its names stripped and wired again with the names in scope at the slot, and replacing
the header keeps the body. A code can only push fills whose way it knows. Each starts from a partial program, its
header from one seed and its growth open, knowing only its header's way; ways arrive by courtship (it asks the growth
pattern, then the header pattern, for a way it lacks, one per ask, in the seeds' order) or by recall (it starts with a
growth way from a past scene). A flow is **composed** when it is held with a header and a growth from different seeds.
Twelve codes: the three headers, each courting or recalling one of three growths. Scarcity as rung 6.

| | scarcity | no scarcity |
| --- | --- | --- |
| flows held, of POC3's 12 | 4 (1, 4, 6, 7) | 4 (1, 4, 6, 7) |
| of them composed | 1 (flow 1: positions header + accumulate growth) | 1 |
| new valid programs, not among POC3's 12 | 2 (enumerate + index-read growth; enumerate + accumulate), both composed | 2 |
| codes holding nothing at the end | 6 of 12 | 0 |

The composed programs:
- `for v4 in range(len(v1)): v3 += [(v1[v4], v2[v4])]` (flow 1: the positions header told, the accumulate growth
  recalled; it is also the accumulate seed's own program, reached without being handed it)
- `for v4, v5 in enumerate(v1): v3.append((v1[v4], v2[v4]))` (new)
- `for v4, v5 in enumerate(v1): v3 += [(v1[v4], v2[v4])]` (new)

### Findings

1. **Composition reaches 4 of the 5 the seeds allow, and two programs POC3's search never found.** An enumerate header
   with an index-read or an accumulating growth passes the spec and is in none of POC3's 52 skeletons. Flow 5 (zip over
   the content then the meta, appending `(v4, v5)`) was within reach and not held: the zip codes that came after the
   first one's flow 6 asked the header pattern for other loops instead.
2. **Scope decides what composes.** A growth way can be set under a header only where its names can be wired: the
   index-read growths need an integer position, which a zip loop does not bind, so under zip only zip's own growth
   fits. Enumerate binds both a position and an item, so every growth fits under it, and that is where the new programs
   are. No conjunction learning was needed here: wiring each way in the slot's scope did the joining.
3. **Strictly, one of POC3's flows was composed.** Flows 4, 6 and 7 were held with a header and a growth from the same
   seed: the seed reassembled from its own told parts, not handed over, but not combined either. By the user's criterion
   (a loop style from one source, a growth from another) composition reached flow 1 and the two new programs.
4. **Four corrections on the way:** the statement fills had to be registered as push strengths as they arrive; a fill
   tried is tried whatever its slot's state was then (by the whole push, changing the header made every fill look new
   and the zip codes never asked); no test is forced while a slot is still empty (an unfilled program cannot pass, and
   the forced runs spent the zip codes' patience before they were told the way they lacked); and a way told or
   recalled and not yet tried is tried before any fill already tried (fiction's `LeanMind.plan` acts on an untested told
   way first; without it the zip codes, told the zip growth, cycled the header's four wirings, each flipping several
   roles and so valued as more work).
5. Six of twelve codes hold nothing under scarcity: the space of composable programs is small (6 flows), and they
   keep asking until the patterns have told everything.

### For rung 8

The variants inside a style (flows 0, 2, 3, 8) and inserting (9-11) are out of reach of ways passed on as they are.
What rung 8 needs, as the user scoped it: the header and growth interacting beyond wiring (a conjunction learner), and a
source of ways the seeds lack. Composition already found what POC3's search did not; the comparison with POC3's 52
skeletons and 12 flows is fair once codes can vary a way, not only combine whole ones.

## Rung 8: varying a held way (`rung8.py`)

Flows 0, 2 and 3 are **churn POC3's rules passed, not targets**: each wraps the pair in a list and pops it straight
back out (`v5 = [v7]; v3.append(v5.pop())`), the pattern POC3's audit rounds tried to rule out. Rung 9's comparison is
counted twice: against all 12 of POC3's flows, and against the 9 that are not churn (1, 4-11).

**The known answer: flow 8.** With its temporaries inlined (flows are counted modulo temporaries, so the extract move
is not needed) it is `for v4, v5 in enumerate(v2): v3.append((v1[v4], v5))`. Its header is offered by wiring
(rung 7 already offered `enumerate(v2)`); its growth is not: the enumerate seed pairs (item, index-read), and flow 8
needs (index-read, item). Wiring re-chooses names and keeps a way's structure.

**The capability (named: new in the mind).** Not natural from the existing value logic: a reordered pair is never an
offered fill, and the mind only values what is offered. A code that has tried everything it knows, with nothing left
for the patterns to tell, varies a way it holds: its pair's two parts swapped (POC3's reorder, applied to a held way),
offered by the world wired in scope like any way (`StmtWorld.vary`). The trigger (the user's): something of the way's
shape works but no wiring of it passes here; so the ways seen to work are varied first. A way is seen to work when its
program passes the spec, run or not: a flow reading `taken` is read only for a passing program.

| scarcity, patience | flows held, of POC3's 12 | of the 9 not churn | new | flow 8 | codes that varied a way |
| --- | --- | --- | --- | --- | --- |
| yes, 12 | 4 (1, 4, 6, 7) | 4 | 2 | no | 3 |
| yes, **24** | **6 (1, 4, 5, 6, 7, 8)** | **6** | 2 | **yes** | 6 |
| no, 12 | 4 (1, 4, 6, 7) | 4 | 2 | no | 0 |

Flow 8 was found by `enu-court` (an enumerate header, courting): after its told ways and the patterns were exhausted, it
varied the positions way (nothing new: two index reads reversed), then the enumerate way, set `enumerate(v2)`, and filled
`v3.append((v1[v4], v5))`.

### Findings

1. **Varying a held way reaches what combining whole ways cannot**: flow 8, the known answer, one swap from the
   enumerate seed's way. With it, a patient population holds all six of POC3's flows that are neither churn nor
   inserting, and the two new programs of rung 7.
2. **Variation comes from pressure, not from a search.** Without scarcity no code varies anything: each is satisfied by
   a way it knows. Under scarcity, codes turned away from every flow they can compose turn inward to the ways they hold.
3. **Patience decides who gets there.** At patience 12 the code that would have found flow 8 gave up one step short (its
   twelfth failed run came right after it set the header, with the needed fill already on offer); at 24 it found it, and
   another found flow 5. Fiction's temperament finding in code: the dogged reach what the impatient do not.
4. **What to vary is read off what worked.** Varied in the order known, codes spent their patience on variants of ways
   that never worked (the positions way swapped only reverses two reads). A way seen to work, its own wiring blocked
   (taken), is the one whose variant is worth trying: the trigger the user gave, read as "something of this shape
   works".
5. Two corrections on the way: a fill in place is recognized by its text (the world rebuilds its fills after every
   push), and a program seen to pass counts as working without a run (codes never run a program they can see is another's,
   so counting runs only recorded nothing).

## Rung 9: recombination within a statement, and the comparison with POC3 (`rung9.py`)

**The check first** (the user's): with a fifth seed (POC3's flow 9, `for v4 in range(len(v1)): v3.insert(v4, (v1[v4],
v2[v4]))`) and no new capability, does wiring alone reach the inserting flows? Flow 9, yes: under a positions loop `v4`
is an integer, and insert-at-`v4` wires as it is. Scope did the conjunction again; no conjunction learner was needed,
and none has been earned in code yet. Flows 10 and 11, no: they are the insert verb with the enumerate seed's pair,
`v3.insert(v4, (v5, v2[v4]))` and `v3.insert(v4, (v1[v4], v5))`, parts of two ways in one statement.

**The capability (named: new in the mind).** Recombining two held ways: a value operation of one (the host) replaced by
a value operation of the same type from another (the donor, as held: its varied form too, if it was varied), wired in
scope like any way (`StmtWorld.recombine`; typed by poc2's grammar in the seeds, so a pair is exchanged only for a
pair; names are left to the wiring). The trigger (the user's): only after every whole way and every variation is
exhausted. In the world directly, it reaches both known answers: flow 10 under `enumerate(v1)` (insert + the enumerate
pair) and flow 11 under `enumerate(v2)` (insert + the varied enumerate pair), and a new program besides (an enumerate
header with the insert way's own pair).

**The population.** Rung 8's twelve codes with the fifth seed, under scarcity, over six orders in which the patterns
tell their ways, at patience 24 and 48; one control without scarcity.

| | of POC3's 12 flows | of the 9 not churn | new programs (not among POC3's 12) |
| --- | --- | --- | --- |
| patience 24, per order | 4-5 | 4-5 | 3 |
| patience 24, union over the six orders | 6 (1, 4, 5, 6, 7, 9) | 6 | |
| patience 48, per order | 4-7 | 4-7 | 3-4 |
| patience 48, union over the six orders | **7 (1, 4, 5, 6, 7, 8, 9)** | **7** | |
| no scarcity, patience 24, one order | 4 (1, 4, 6, 7) | 4 | 2 |

### Findings

1. **Flows 10 and 11 were not held by any population**, though recombination reaches both. The codes that recombine
   are the ones under pressure: those whose headers (positions, zip) left them without a free flow. They recombine
   pairs in order of the ways seen to work, then the seeds' order, and gave up or settled before reaching (insert,
   enumerate) (one of 20 ordered pairs of five ways). The codes with an enumerate header, which flows 10 and 11 need,
   are satisfied early by the new programs composition gives them (enumerate with a positions, accumulating or
   inserting growth) and are never pressed to recombine. The mechanism reaches the answer; the population, as
   tempered, does not.
2. **Patience and the order of telling decide what is held.** At patience 24 the population holds 4-5 of POC3's flows,
   at 48 up to 7; the same patience gives 4 or 7 under different orders. Over all orders at patience 48: 7 of the 12,
   7 of the 9 that are not churn. The no-scarcity control holds 4: without pressure no code varies or recombines.
3. **Beyond POC3: 3-4 new valid programs in every scarce run**, the enumerate header with a positions, accumulating
   or inserting growth: programs POC3's search with its novelty bonus did not find, found here from its own four seeds
   and one more.

### The comparison with POC3, as it stands

POC3's search (seeded mutation with a novelty bonus, rules and a semantic gate, eight audit rounds) found 52 skeletons in
12 flows on the color line, three of them churn. From POC3's four hand-written seeds alone, a scarce population of
twelve code minds, composing and varying ways told and recalled, holds up to **6 of the 12** (6 of the 9 not churn:
rung 8). Rung 9's 7 counts flow 9, but its fifth seed is POC3's own flow-9 program, a program POC3's search discovered
(INCOMPLETE.md 6.3): flow 9 held is not a discovery, and the honest count from the hand-written seeds is rung 8's. With
that fifth seed, 7 of the 12 (7 of the 9) over six telling orders. Either way, 3-4 valid programs POC3 did not find
(not yet audited by POC3's rules and gate). Not reached: flows 10 and 11
(reachable by the mechanism, not reached by the population as tempered), and the churn flows 0, 2, 3 (not targets). The
two are not the same kind of search: POC3 explored a grammar under rules; the codes court, recall and vary what they
hold, under scarcity, and never enumerate. What reaches the codes is bounded by what they hold, and what moves them past
it is pressure.
