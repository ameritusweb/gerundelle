# clean5: why the aligning want went away, and the stuck run+2 want

Report of 2026-11-13, written while the last replays run. Each statement is marked **traced** (read from the run's checkpoints, or replayed and checked against the run's own record) or **pending**. Nothing here was predicted.

Run: `trace_decisions.py 30000 --prefix clean5`, started 2026-11-12 ~17:25, log `clean5_run.log`, checkpoints `checkpoints/clean5_<slice>.pkl`. Luck reached 0 at slice 6,400.

## 1. Why the aligning want went away (traced)

**Where the want comes from.** `piece_alignment_aligning` is never placed. It is offered by an ownership slot on the region `piece_alignment` (`SovAgent.own_candidates`), and the slot that offers it is a **contested** one: the region is the mind's, and something else moved it. The slot offers every state the region has been seen in except the one it is in now.

**What makes the region contested.** `Territory.update` (molecules.py:4263) marks a held region contested while `other_since` is warm (or a claim on it failed). `other_since` rises in only one path, `Territory.moved`, and the agent calls that from:

- `SovAgent.idle` (sov_agent.py:648): a slice with no push of the mind's in flight. Every change goes to `moved`.
- `SovAgent.watch` (sov_agent.py:662–667): during a push's watch, only changes the world attributes to another (`world.others`). Every other change is added to `watched_objs` and **claimed as the push's own** (line 665; `Territory.claimed`).

A change during a watch that the push didn't predict is also passed to `Territory.unexplained` (line 699). That records it in `other_to`, but it never raises `other_since`, so it cannot contest the region.

**What changed over the run.** The world kept flipping the alignment (a new piece forming aligned or straying, the stack changing under it) at a steady ~20 times per 1,000 slices. What changed is that the mind was nearly always mid-watch when it happened:

| Window (replayed, see §5) | Slices idle / watching | Alignment changes read while idle → `moved` | Read in a watch → claimed as the push's | Contested openings |
|---|---|---|---|---|
| 1,000→2,000 | 932 / 68 | 22 | 4 | 22 |
| 14,000→15,000 (today's code; matches the run through 14,541, see §5) | 495 / 505 | 2 | 18 | 2 |

From the slice-28,000 checkpoint (`piece_alignment`'s own row): moves by something else held at 10–25 per 1,000 slices all run, while contested openings fell from 15–22 per 1,000 (slices 0–3,000) to 0–2 from slice 6,000 on. From 14,000 to 28,000, 249 moves were recorded in `other_to` and 5 of them reached `moved`.

So the aligning want went away because **it can only arise while the mind is idle**, and as the mind acted more (≈40 decisions per 1,000 slices early, ≈110 by slice 10,000, ≈165 by 25,000) it was almost never idle when the alignment flipped. It was not given up: `failed_subs` never held it.

**A side effect: straying wants.** A contested slot offers whichever state the region isn't in now. When something else moves the piece *into* aligning, the slot offers `piece_alignment_straying`, and the mind took it: the mind wanting its piece not to line up. Both contests in 14,000→15,000 offered straying. Alignment wants set per game:

| Game | Slices | aligning set | straying set |
|---|---|---|---|
| 0 | 0–8,800 | 9 | (not tallied) |
| 1 | 8,800–14,000 | 7 (all met) | 2 |
| 2 | 14,000–24,000 | 2 | 5 |
| 3 | 24,000–26,800 | 0 | 3 |

This is the case the "never want your own loss" feedback names. `held_state_wants` (2026-11-13) would not stop it here: the register held `piece_alignment` in both states.

## 2. The stuck run+2 want (traced)

**What `run+2` is.** A potential effect: a *run* (4+ blocks side by side, two pieces each with 2+ blocks in it, `TetrisWorld.runs`) coming apart **two rows above the falling piece's lowest landed block** (world.py:327). In clean5, every run+2 prediction had exactly one block of the falling piece in the run (all 20). That needs the piece standing at least 3 rows tall, dropping into a pit at least two rows below the run's row, beside other pieces' pairs. Clear predictions over the whole run:

| Clear | Predictions stood | Falling piece's blocks in it |
|---|---|---|
| run+0 | 308 | 1 (269), 2 (39) |
| run+1 | 330 | 1 (294), 2 (36) |
| run+2 | 20 | 1 (20) |
| row+0 / row+1 / row+2 | 53 / 17 / 2 | 1–2 |

**How a want for it is set, and how it ends.** `own_candidates` offers `potential:run+2_coming_apart` while *any sequence* of pushes on offer leads to it (`situational`, from `world.push_predictions`, sov_agent.py:1278–1306), including long ones (`rotate+shift_right+shift_right+shift_right`). Once it wins the top with nothing else held, it is the **root** want, and:

1. `sub_budget` drops only sub-wants (sov_agent.py:313); a root want has no deadline.
2. Patience reads claim failures on the want's region (line 316); the region read for this want is `potential:run+2_coming`, which no claim ever touches.
3. No push's effects carry the relative name, so no push meets it (line 718).
4. It is met only when a prediction of that same effect **stands** (`stand_prediction`, line 1335). A prediction stands from the no-push forecast or from the single push just made (lines 1254–1265), never from a multi-push sequence.
5. Nothing withdraws it when the sequence that offered it is gone. It is re-presented to the pool every slice (sov_agent.py:219–233), raising it to the top again whether or not anything leads to it now.
6. The mind holds one root want (`self.goal`); every want that wins the top meanwhile can only become a sub-want under it, with a deadline, and lands in `failed_subs` when the deadline passes.

**What happened.** Of 34 potential wants in the run, 28 were met in the slice they were set (a prediction stood at once). Three run+2 wants stuck, each ended exactly by a run+2 prediction standing, with no run+2 standing anywhere inside the hold:

| Held | Slices | Ended by run+2 standing at | Game |
|---|---|---|---|
| 3,523 → 8,169 | 4,646 | 8,169 | 0 (second half) |
| 8,728 → 14,541 | 5,813 | 14,540 | 1 (all of it) |
| 24,385 → 25,733 | 1,348 | 25,733 | 3 (first half) |

The owned prediction row `potential_run+2_coming_apart` was lost at 8,199 and not re-tested until 14,541. The seven aligning wants of game 1 were sub-wants set beneath the stuck run+2 want.

## 3. Did either cost the mind clears or games? (partly traced, partly pending)

**Clears in reach were taken while the want was stuck (traced).** Replay 10,000→11,000 (inside the 5,813-slice hold, the root want run+2 for 995 of 1,000 slices): of 24 pieces, 11 had a clear in reach (run+0 or run+1, never run+2) and **all 11 made it**. The 13 with no clear in reach made none. The pushes carry their own predicted clears as tags (`situational`), which was enough without a matching want.

**The clear rate didn't change (traced, from the log).** Pieces cleared per 1,000 slices stayed between 16 and 26 for the whole run, held want or not: 22, 22, 24, 20 through the game-1 hold (10,000–14,000), 20–24 through game 2, 26 and 26 at 24,000–26,000.

**What did differ is how long a game lasted.** The mind places a piece every ~37–40 slices throughout, so a game's length is how many pieces it places before the stack tops out:

| Game | Pieces placed | Rows cleared (full rows) | Stuck run+2 want held |
|---|---|---|---|
| 0 | 236 | 14 | second half (luck still helping until 6,400) |
| 1 | 148 | 3 | all of it |
| 2 | 263 | 18 | none after 14,541 |
| 3 | 86 | 3 | first half |

The games under a stuck want were the short ones. That is four games, so it is a correlation; and the clear rate shows the stuck want did not lose clears. If it matters, it would be in **where the pieces with no clear in reach were put** (holes, stack height), which is what tops a game out.

**Pending (running now, on clean5's own code, §5):**

- Placement 10,000→11,000 as the run went, and the same window with the stuck want taken out at the start (a counterfactual on the same well and pieces): holes, stack height, pushes and waits per piece. At slice 10,400 both had placed the same 10 pieces with the same 4 clears.
- Placement 16,000→17,000 (game 2, no hold) as a baseline, and 24,000→25,000 (game 3, the hold starting at 24,385).
- Clear-wants 14,000→15,000 and 24,000→25,000, rerun (their first runs were on today's code, §5).

## 4. Proposed direction (the user, 2026-11-13; not built)

The user: *"ideally, there is no 'stuck' rare want; it stays a want, but due to rarity, it makes room for other more common wants."*

The mechanism agreed, through the tournament, with no rule about rarity:

1. **A held want is re-presented only while a push on offer leads to it**, the same reach condition `own_candidates` uses before offering a potential want (sov_agent.py:1706). Out of reach, it stays in the pool and in `wanted` but isn't refreshed, so it fades by the mind's half-life like any molecule that isn't perceived.
2. **A candidate that wins the top replaces a faded root want instead of stacking under it.** The old want is not dropped and doesn't go to `failed_subs`; `own_candidates` offers it again whenever a push leads to it.

Rarity then shows as how seldom the want is refreshed: run+2 is in reach a few slices in thousands, so it sits low and run+0/run+1 wants win the top in between; when the pit shape comes up it is refreshed and competes again.

The cost: a want held out of reach is also what drives setting up for it (`setup_for_wants`), so the mind would take a run+2 when one comes rather than build the pit for it.

It needs edits in `analogy/molecules/sov_agent.py`, behind a new switch, off by default. The go session edits the same files, so it waits until the user says to build it.

Related, not yet proposed: the aligning want's dependence on idleness (§1). Two directions were discussed: (a) count a change in a watch that the push didn't predict as another's move, so it can contest (general, but it raises straying wants too); (b) hold `piece_alignment` as territory only while it reads aligning (as `own_open_rows` holds a row while free), so straying is a loss and the slot only ever offers aligning back. Undecided.

## 5. How this was traced

**Replays.** A checkpoint holds the whole agent and world, so a window can be replayed slice by slice with wrappers on the loaded objects (never on the Gerundelle files), and the replay's records compared with the run's own (`sub_log`, the register's holder history).

**The code clean5 ran on.** clean5 loaded `analogy/molecules` on 11-12 at ~17:25; `molecules.py` and `sov_agent.py` have been edited since (the go session's 11-13 switches). Replays on today's code matched the run up to slice 14,541 and then diverged (the run set `piece_alignment_straying` at 14,707; today's code set `potential:row+0_coming_apart` at 14,680). Gerundelle backs each file up before an edit, so the first backups made after the run started are the code it loaded: `sov_agent.py.before_chain_ids` (11-12 20:26) and `molecules.py.before_anti_causes` (11-12 21:19), copied to `clean5_code/`. No other Gerundelle module, the Rust kernel or `warpchess/potential.py` changed after 17:20. `with_clean5_code.py` loads that copy ahead of the live folder. The replays in §1 and the 10,000→11,000 clear replay in §3 ran on today's code. 1,000→2,000 matched the run exactly, and 10,000→11,000's sub-want log matches the run's. 14,000→15,000 matched through 14,541 and its counts cover the whole window, so the last ~460 slices are today's code, not the run: its second contested opening came at 14,910 where the run had one at ~14,705. The run's own register agrees on the count (2 contested openings in 14,000–15,000). Everything pending runs on `clean5_code/`.

**A clear belongs to the piece before.** A piece's clear is decided in the slice it comes to rest (world.py:659–681) and its blocks leave in the next slice, by which time a counter has moved on to the next piece. `trace_clear_wants.py` marked each clear one piece late; `summarize_clear_wants.py` moves it back. `trace_placement.py` reads the clear in the resting slice.

**An unrelated freeze in meta-cognition.** From slice ~10,000, `meta:relevant` formed nothing new (formed 2,883, refuted 2,881 for the rest of the run). Before that it formed and refuted `meta:relevant:piece_alignment_aligning` every 5 slices (2,500 entries, 1,960–9,985). `target_unknowns` (molecules.py:1751) takes only the top-ranked concept with open slots from each list; from ~10,000 both picks were concepts whose `meta:relevant` already stood and was confirmed every slice. It does not gate wants. Not traced further.

### Files

| File | What it does |
|---|---|
| `trace_aligning.py` | reads a checkpoint: sub-want log, `failed_subs`, `piece_alignment`'s territory row, meta log |
| `summarize_aligning_log.py`, `summarize_other_moves.py`, `summarize_align_wants_by_game.py` | tables from `trace_aligning_<slice>.log` |
| `trace_alignment_path.py` | replay: which path read each alignment change, what opened each contested slot |
| `trace_potential_holds.py`, `trace_prediction_stands.py`, `trace_run_shapes.py` | every potential want's hold; predictions stood per effect; what each clear's structure held |
| `trace_clear_wants.py`, `summarize_clear_wants.py` | replay: per piece, clears in reach, wants held, cleared (re-attributed) |
| `trace_placement.py` | replay: per piece, holes, stack height, pushes and waits; `--drop-goal` for the counterfactual |
| `summarize_clear_rate.py`, `summarize_potential_holds.py` | from the run log and trace logs |
| `with_clean5_code.py`, `clean5_code/` | run any of these on the code clean5 loaded |
| `trace_*.log`, `c5_*.log` | outputs (`c5_` = on clean5's code); `*_livecode_partial.log` = stopped runs on today's code |
