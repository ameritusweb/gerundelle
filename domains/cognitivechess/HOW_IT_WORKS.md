# How cognitive chess works

A map of the code. What each rung found is in `LADDER.md`, and the decisions are in `README.md`. Written 2026-10-31 from
`chessworld.py`, `rung1.py`, `rung3.py`, `../fiction/gerundelle_arm.py`, and `E:/vscode/analogy/molecules/`
(`sov_agent.py`, `molecules.py`). Every mechanism described here was checked against its code on that date. Where a
comment or docstring in Gerundelle disagrees with the code, this file follows the code and says so. Not covered:
`Mind.learn`, `contradict`, closure, parking and boxes, the analogy/abstraction machinery in `Understanding`, and
`mcts` itself.

## The stack

```
rungN.py                 builds a world, a mind (or two), sets the arm's Params, runs, measures from a log of slices
  └─ GerundelleMind      ../fiction/gerundelle_arm.py: wraps a SovAgent, writes "beats" (see, want, try, learn, feel, ...),
       │                 sees other minds' slices (rung 3), passes told knowledge between minds (consult/answer)
       └─ SovAgent       molecules/sov_agent.py: perceive, the mind's tick, choose a push, watch it, record what came of it
            └─ Mind      molecules/molecules.py: the molecule competition, meta layer, understanding register (SOV),
                         territory register, inquiry (experiments), emotional phases
ChessWorld / DuelWorld   chessworld.py: python-chess behind the interface SovAgent reads
```

Every rung script puts `../fiction` on `sys.path` and imports `GerundelleMind`. Importing it (through fiction's
`worlds.py`) puts `E:/vscode/analogy/molecules` on the path. **The live Gerundelle is shared** with fiction,
cognitivecode and civilization, and that is why every change to it is opt-in and checked against its suite.

## The world (`chessworld.py`)

`ChessWorld` gives Gerundelle the same interface as its force worlds:

| Member | In chess |
|---|---|
| `objs` | every piece by identity (`black_knight_d5`: colour, kind and starting square), each piece's `<piece>_safety`, `material`, and any perceived relations |
| `states()` | object → gerund. A piece is `present`, `captured` or `absent`; its safety is `safe`, `attacked` (attacked and defended) or `hanging` (attacked, undefended), and a king's is `safe`, `checked` or `mated`; `material` is `even`, `up` or `down` against the episode's start |
| `invitations()` | the legal moves as `(label, piece, piece's state)`. The label is an order rank plus SAN without `+`/`#`, e.g. `'042 Rxd5'` |
| `act(inv, hold)` | makes the move and the world's reply, and returns diffs `'<obj>: <from> -> <to>'` |
| `renew()` | an episode ends after `moves` White moves, a mate, or `IDLE` (6) slices with no move; then the position is set back. SovAgent never renews in the middle of an experiment |
| `still = True`, `horizon = 2`, `gamma = 0.7` | nothing moves unless the mind acts; a push is watched for 2 slices; later effects are discounted |

Perception choices, each named in the module docstring and learned from a rung:
- **Principle 0:** in a move's own slice, only the moved piece changes. Everything else (the captured piece, material,
  other pieces' safety) lands one slice later, through `pending`. Otherwise Gerundelle would read the consequences as
  part of the situation the move met.
- **A piece and its safety are separate objects** (`safety=True`, rung 1). A move's configuration (its piece is
  present) stays a stable fact, and safety is a relation that is perceived.
- **Relations as objects** (rung 1c, `relations=`): a square (`d8`: `held`, `guarded` or `open`), `flight` (whether
  the black king has an escape square off its rank), `game` (`on`, `mate`, or with `clean`, `costly_mate`), and `reply`
  (Black's last answer). `reply` is listed in `events`, so SovAgent treats it as an outcome, not a condition (rung 2).
- **Move order:** `order` seeds a rank for each move, so ties between equal moves aren't broken by the move's name, and
  a move keeps its rank in every position where it's legal. Moves in `last` get rank 999.

Black's reply is authored, a rule of the world like the wind in the force worlds: `None` (Black passes; rung 0),
`"recapture"` (take back on the square just taken with the least valuable piece, else pass), or `"answer"` (meet a
check by capturing, stepping away or interposing; otherwise recapture).

Two more world services:
- `imagine(line)` (rung 1b): plays a line on a copy, by the rules, with Black's replies from Stockfish
  (`imagine="stockfish"`, at depth 6) or none (`"rules"`).
- `relations_of(inv)` (rung 1e, `converge`): what a move would meet, read before it's made: `check`, `landing`,
  `guard`, `backed`, `flight`, `interpose`, plus non-causes (`piece`, `captures`, `lands`).

The positions are `RUNG0`, `RUNG1` (the knight on d5 defended or hanging), and `RUNG1C` (eight back-rank configurations).
Rungs 1d and 2b generate theirs.

### `DuelWorld` (rung 3)

A subclass, so earlier rungs are unchanged. Each round, every mind takes one step, with `world.actor` naming whose step
it is (civilization P4's pattern).
- Only the side to move gets invitations, and there's no authored reply. A scripted Black acts through `("pass", ...)`
  or a real move.
- What a move does reaches its maker in the maker's next slice (`pend[side]`); other minds just see the board.
- `standing_white` / `standing_black` is the material balance from that side's view, read when its turn comes round
  again, so a capture is judged after the reply. The want is `standing_<side>_up`.
- `horizon = 3` (a watch spans the other side's answer). An episode is `half_moves` (4) moves.
- `relations_of` is read from the side to move. It has no event objects yet.
- `holding=True` (opt-in) adds `holding_white` / `holding_black`: `kept` while that side's standing is even or up,
  `lost` while down. Black wanting `holding_black_kept` (`rung3.py --black-want kept`) is a defender: the want is met
  by winning back what was taken.
- **Who steps when** is set in `rung3.py` (`play`, shared by the trace scripts), not the world: `--schedule rounds` (every mind once per round, P4's) or
  `turns` (the side to move steps until it moves, at most `TURN_STEPS` = 5, then the other side one slice). Use `turns`:
  under `rounds`, a thinking opponent's answer came after the mover's watch two times in three, and the mover's wins
  credited no push (LADDER.md rung 3; `experiments/delivery3.py`). A side's pending standing is delivered only in a
  slice where it doesn't move; a slice where it moves drops it.

## A tick of `SovAgent` (`sov_agent.py:156`)

1. **Housekeeping.** Drop a sub-want that has outlived `sub_budget`. With `patience`, give up a want (or drop its
   sub-want) once failures on its region reach the limit. The want sets a control slot on its region.
2. **Perceive** (`perceive`). Facts are `<obj>_<gerund>` for every object except events. The news is the diffs.
   Invitations become concepts like `'<label>_push:<piece>...'`. The territory register gets a row per object, with the
   pushes on it.
3. **`mind.tick(inputs)`** (`molecules.py:1035`): perceive, `contradict` (what the world shows checked against what
   is held), present the inputs, `think`, `learn`. It returns `rec`, including the experiments and phases that won.
   `think` (`molecules.py:495`) is the competition:
   - **Levels** `slots=(7,5,4)`. At each level every molecule resolves its best binding (`resolve`): a partner, by the
     partner's activation × the force between them, or acting as an edge between two others (a bond).
   - **Then the bids:** activation × (1 + binding score) + tension (open sites) + `w_pred` × expected surprise
     reduction going forward + constraint support (`Params.support`).
   - **Separate tracks** with their own slots: thoughts (`k` per level), meta molecules (`meta_slots`, operable kinds
     first), SOV molecules and questions (`sov_slots`), phases, experiments (`exp_slots`), and ownership instances
     (`own_slots`). Exact ties go to more expected surprise, then the one that has waited longest, then the id. The
     winners at one level are the competitors at the next; **the last level is the conscious one** (`mind.top(rec)`).
   - **After:** composites form from bound winners, open sites are filled, molecules that won nothing decay by their
     half-life, the top winners are fed back as next tick's percepts (`self_feed`), and the meta layer, understanding
     and phases observe the record.
4. **Choose**, in this order:
   1. if a push is still being watched, keep watching (`world.act(None, hold=True)`);
   2. if there's a want and `planned(invs)` (`sov_agent.py:589`) returns a push, take it. Its order:
      - (`sub_yield`) a sub-want that already holds is met. If the planner now finds a way to the root want, the
        sub-wants are dropped and that way is taken;
      - `plan_step`: MCTS (budget 60, horizon 3) over the agent's own `Model`, with the first push taken from the moves
        on offer and the top winners' pushes as the prior. A push is returned only if its value is above 0;
      - (`converge`) a **direct** way (the push itself expected to bring the want) that would meet all of some
        constraint from earlier failures (`runs_into`) is vetoed. With `bridge` and `subwants`, the fact that would let
        it clear (`clearing`) is set as a sub-want;
      - (`subwants`, stack < 4) `subwant`: a nearer want from a known way's missing configuration or condition, or a
        situation never tried, to be made one fact at a time;
      - (`converge`, no sub-want) **last**, `notice`: the untried push the constraints converge on.

      The `Params.converge` comment says "before sub-wants", but the code puts the noticing after them; the comment at
      `sov_agent.py:638` records that it was moved after rung 1;
   3. otherwise the next step of the experiment under way, or the experiment that won. In a still world, an experiment
      whose outcome is already known is reported rather than re-run (`foreseen`, rung 0);
   4. otherwise idle, which is still watching: anything that moves meanwhile is credited to something else
      (`territory.moved`).
5. **Watch** the push for `world.horizon` slices. When the watch closes (`watch`):
   - seen `causes` / `caused_by` receipts, discounted by `gamma ** delay`, or `causes no_change`;
   - changes on other objects that weren't predicted go to `territory.unexplained`;
   - the territory claim is recorded (`territory.claimed`);
   - `meta.observe_mode(push, outcome, situation)`, which is how conditions get learned (next section);
   - logs: `tried`, `pushed`, `left` (what the push left behind), `just` (for `told_effects`), and `converge`'s `trials`;
   - sub-want bookkeeping. A want met closes its control slot (joy); a sub-want met hands control back to its parent.

## What the mind learns, and from what

- **Conditions by contrast** (`molecules.Meta`, `molecules.py:1392–1509`):
  - `observe_mode(push, outcome, situation)` files the outcome under the push's current **reading**: the push read
    through any splits it already has (`reading_in`).
  - When some change comes in at least 2 outcomes and is missing from at least 2, the rarer side being at least a
    quarter (`opposed`), a `meta:conflated:<push>` molecule is emitted.
  - It must **win the top level** of the competition (`Meta.observe`, then `operate`); only then does `differentiate`
    run. Meta molecules with an operation take the meta slots first.
  - `differentiate` splits on the situation fact that best separates the change's presence from its absence
    (`mode_boundary`: at least 2 outcomes on each side, one side at least 75% one way, the two rates at least 0.5
    apart). The result is two molecules, `<push>|<tag>` and `<push>|not_<tag>`, with the outcomes divided between
    them, and `conditioned_by <tag>` written as a worked receipt. A half that is still mixed is conflated again at
    once, which gives nested splits.
  - With no boundary, the concept goes into `meta.unexplained` (a hidden cause; "what is left to vary is the moment")
    and is retried after 4 more outcomes. `Territory.relation_of` reads `unexplained` to look for another agent who
    answers.
  - Each tick, `reread` swaps in whichever half of each split the present situation selects.
- **Prediction** (`SovAgent.predict`): the most common outcome of the push's reading in this situation, from the meta
  register's records; `None` if that reading was never tried.
- **The understanding register** (`molecules.Understanding`, `molecules.py:1570`):
  - `rel[concept][(relation, other)] = [seen, told, worked]`. Relations written include `causes`, `caused_by`,
    `co_occurs`, `role`, `conditions`, `conditioned_by` (including `not:<prep>` from a ruled-out preparation), and with
    `polarity`, `enables` / `prevents`; with `told_effects`, also `after`.
  - `funding(c, rel)` = seen + worked + `credulity` × told; the `conditions` slot also counts `conditioned_by`.
  - **A slot is open while its funding is below 1.0.** `level(c)` is the mean over the five slots (`causes`,
    `caused_by`, `co_occurs`, `role`, `conditions`) of funding / `sov_m0` (2.0), each capped at 1. The planner imagines
    a push while its `conditions` funding is below 1.0.
  - Receipts are written from the pool's own work (split boundaries, fillers' roles, composites' parts) and from a
    winning `sov:<concept>` molecule. It "works out" relations with what is at hand, from the raw records:
    `co_occurs` from co-wins, and `causes` when the other is perceived on the next tick in at least 60% of the
    concept's arrivals and at least 2 times, at twice or more its base rate. Two pushes are never each other's cause.
  - **Refutation** (in `SovAgent.watch`): a told way to the want that the world contradicts has its told receipt
    zeroed, goes into `refuted` (never written again), and the teller goes into `belied` (which phases read as anger).
    With `told_effects`, a told effect that doesn't come is refuted the same way. A told step tried out of its `after`
    order is not refuted.
- **Experiments** (`molecules.Inquiry`, `molecules.py:3146`): each tick, every standing question and ownership question
  suggests experiment molecules `exp:<slot>:<concept>[:<first>]`. Their activation is how open the slot is, × what its
  ownership slot pays, × `persistence / (persistence + times done)`; below `floor` (0.05) they aren't offered. They
  compete in their own track, and the top one is `rec["experiments"]`.
  - `causes?` a push: do it.
  - `conditions?` a push: a preparation, then the push. Preparations are pushes seen to change something, plus untried
    ones, minus ones ruled out. First choice goes to preparations that make a situation the push was never tried in;
    a told condition's preparation goes first, unless `credulity < 0.5` (a skeptic tests the alternatives too). In a
    still world with no lead, untried preparations come first.
  - `caused_by?` a change: an untried push (or, in a moving world, waiting).
  - **Unexplained pushes** (moving worlds only): the push after waiting 1 or 2 ticks.
  - **Ownership questions:** `probe` (uniqueness or contested: try a claim again), `await` (a want whose way needs a
    condition the agent can't make: wait; moving worlds only), `causes` for an unclaimed region's untried claims, and
    `summon` for a relation (the claim twice: does the other come?).
  - `result`: a conditions experiment whose push came out as usual rules the preparation out
    (`conditioned_by not:<prep>`, worth 1/n of the 1.0 that closes the slot, where n is the number of preparations).
    The question closes once all are ruled out.
- **Sub-wants** (`SovAgent.subwant`, `needs`; `sov_agent.py:794–876`):
  1. **A way known** (a push that has brought the want before, most often first): `needs` returns the push's
     configuration (`<piece>_present`), plus, walking its splits, the tag of each half whose outcomes brought the want.
     With `sub_tested`, a tag is skipped if the other half has no records. With `polarity`, it writes `enables`, or for
     a `not_` half `prevents`, and wants the object as it most often stood when the want came. The first need not
     holding now that some known push has made becomes the sub-want; with `sub_cost`, not if that push moved the root
     want's object or undid something the way needs and has now (`serving`).
  2. **No way known:** the objects named by the splits on pushes on the wanted object. If the current combination of
     their states was never tried with a push on the wanted object, that push is tried now. Otherwise the untried
     combination needing the fewest facts made is chosen, and its first fact is the sub-want.

  At most 4 deep. A sub-want is dropped (and not set again) after `sub_budget` (80) ticks, or when its failures reach
  `patience`.
- **Convergence** (`converge`; `constraints_from`, `notice`; `sov_agent.py:26–64, 737`):
  - Each root-want push records `(what relations_of said it would meet, what came of it)`. A failure's kind is the
    world's event objects after it (in chess, `reply_<what Black did>`), or else the changes.
  - `constraints_from` takes, for each failure kind, the smallest combination of what its failures met that no other
    attempt carried in full (`distinguishing`, from grasp.py), merging pairs while the shared part still tells them
    apart.
  - `notice` scores each push not yet tried in this exact situation with a fresh one-level `Mind(support="candidates")`.
    Each constraint is a molecule weighted `1 − 0.5^n` (n = its receipts), whose open site is filled by each attempt
    that clears it. The top bidder is returned only if it clears at least one constraint and bids above the
    lowest-ranked option; otherwise `None`.
- **The planner's model** (`Model.recorded`, `sov_agent.py:978`) predicts a push from the agent's own records in the
  current reading. Its reward is the share of past outcomes that met the want. Opt-in additions: told ways and told
  effects at credulity, the told `after` condition and `made:` markers (`told_effects`), imagination through
  `world.imagine` for pushes not yet understood (`imagine`: it scores plans and writes nothing to the register, which
  is the firewall), and `sub_cost` (`Model.costly`): while a sub-want is served, a push whose usual outcome moves the
  root want's object, or changes something the served way needs, has reward 0 there.
- **The territory register** (`molecules.Territory`, `molecules.py:2572`):
  - A row per object: claims `{push: [tried, took]}`, and moves by something else (`other`, `other_to`,
    `other_times`).
  - `claimed` (a watch ended): every region the push touches or was ever followed by gets a try. It **took** if the
    region changed and the changes predicted there came.
  - `moved`: changes with no push of the agent's in flight are something else's. In rung 3 they come from
    `GerundelleMind.look`, which reports the other mind's slices.
  - Holder, from strength `(took + κ·b)/(tried + κ)` against the base rate b across all regions:
    - `mine` when strength is above b, or every try took;
    - `contested` while another's last move is still warm, or after a held region's claim fails; also as hysteresis:
      a held region below b stays contested for `h0` ticks;
    - then `lost` (or `another` if something else moved it, unless `grievance`);
    - `another` if only others moved it; `nobody` if tried and never held; `unknown` otherwise.
  - Each holder opens a slot with a question and a pull: unclaimed "what happens if I push here?" (pull
    `curiosity·κ/(κ + other)`), control "what blocks it?" and contested "what else moves it?" (between 1 and 2),
    lost "what took it?" (1 + held), mine "is it mine alone?" (`κ/(κ + tried)`), and relation "will they be there?"
    (`relation_of`, `molecules.py:3031`).
  - Open slots **fund** the concepts they serve (`serve`), which is what pays questions and experiments. Slots nothing
    could fill now are **parked**.
- **Phases (feelings)** (`molecules.Phases.graph`, `molecules.py:2358`). In an acting mind, they are read off the
  ownership graph, each anchored on its instance `own:<kind>:<region>`:
  - **frustration:** a control slot (or one contested by its own failure) whose claims failed twice running;
  - **anxiety:** a contested-by-failure slot after one failure;
  - **sadness:** a lost slot;
  - **anger** at `other:<who>`: whoever took a lost thing; a purposeful other who keeps the state a frustrated slot's
    condition names; or a teller whose word the world contradicted last tick;
  - **joy:** an instance closed because a claim took on its region;
  - **gratitude:** a want met by another's act (`helped_now`);
  - **resignation:** a want given up (`patience`);
  - **curiosity:** an unclaimed slot winning the ownership track;
  - **calm:** no live instance for 5 ticks.

  Phases fade with `phase_h` (4) unless refreshed. Frustration, anxiety and sadness close when their instance closes by
  a claim; grounded anger closes when its goal does. A closable phase that fades with its sites open is stored and
  **re-opens** when its anchor comes back. The dominant phase steers which slot the questions ask (`STEER`).
  `GerundelleMind` turns `rec["phases"]` into `feel` beats, and rung 3 counts them. The `graph` docstring still says
  anger is "left open" until Stage 6; the code under it forms anger in the three ways above.

## The `Params` switches this track added (all off by default)

`GerundelleMind` builds `Mind(Params(inquiry=True, phases=True, ...temperament))`. A rung's arm then sets switches on
`m.agent.mind.p`.

| Switch | Rung | What it does |
|---|---|---|
| `polarity` | 1 | a split's condition **enables** or **prevents** a push; a want needs a prevented condition undone |
| `subwants` (`sub_budget`) | 1 | a want with no way found sets a nearer want on a stack (civilization P6) |
| `imagine` | 1b | the planner imagines open pushes through `world.imagine` |
| `support`, `w_support` | 1d | candidate-support bidding from constraint molecules |
| `sub_cost` | 1c | a means that undoes the root want is no means |
| `converge` | 1e | direct ways that run into a constraint from failures are vetoed; when nothing else is found, the untried push the constraints converge on is noticed (after sub-wants, in the code) |
| `sub_yield` | 1e | sub-wants yield when the planner finds the root want's own way |
| `sub_tested` | 1e | a condition never seen absent is not wanted |
| `bridge` | 2 | from constraints to sub-wants |
| `told_effects` | 2b | told effects, the told `after`, `made:` markers, and quiet moves still count as made |

Older switches the rungs also lean on: `inquiry`, `phases`, `meta`, `sov`, `patience`, `credulity`, `curiosity`,
`persistence`, `keep_subs`, `grievance`.

## A rung script

The pattern, taken from `rung1.py`:

```python
w = ChessWorld(RUNG1, order=seed, seed=seed, reply="recapture", moves=2)
m = GerundelleMind("White", w, want="material_up", want_count=10**6)   # want it again and again
for k, v in ARMS[arm].items(): setattr(m.agent.mind.p, k, v)
w.act = logged(w.act)                       # every slice: (episode, configuration, move, diffs)
m.run(ticks)                                # GerundelleMind.step -> SovAgent.tick, ticks times
measure(w, m, log)                          # wins/losses per configuration from the diffs, splits, polarity, sub_log
```

- A **seed** draws the episodes and orders the moves. Results are always reported over seeds (default 10), never
  from one run.
- **Arms** are named dicts of `Params` switches (`ARMS` in each script). The same seeds run under each arm.
- Measures come from the world's slice log (e.g. `material: even -> up` in a defended configuration) and from the
  mind's own records (`meta.splits`, `understanding.rel`, `sub_log`, `phases`).
- Rung 3 instead loops `for each round: for each mind: w.actor = name; mind.step()`. Black is a `GerundelleMind`
  wanting `standing_black_up`, or `ScriptedBlack`, which applies rung 1's recapture rule as a player.

Run with `python -X utf8 rungN.py --seeds 10 ...`, writing to `logs/`. Each script's docstring gives its flags.
**Results depend slightly on `PYTHONHASHSEED`** (set iteration order inside the minds); set it to a fixed value for
runs that must be exactly reproducible. Logs up to 2026-10-31 were run without it.

## Discipline (from the README)

Before any change to Gerundelle, back up `molecules/` to `backup/molecules_<date>[b|c]/` (with `SHA1SUMS`), then run
its suite. It must match the reference, 72/80 with 2 pending (`../cognitivecode/backup/fails_after_honest_repair.txt`);
logs go in `backup/tests_after_<change>.log` and `fails_after_<change>.txt`. Every new mechanism is a `Params` switch,
off by default. Every authored choice is named in a comment, usually with the failure that forced it ("first ...;
rung N").

## Fixed 2026-10-31: the overflow in a duel

`Territory.relation_of` overflowed once another mind moved a region every turn (`GerundelleMind.look` reports each of
its moves as `territory.moved`). It now checks `n >= 5 and _outside <= 0.1` first and computes the Poisson tail in log
space (`molecules.poisson_cdf`). Backup `backup/molecules_2026-10-31d/`; the suite matched the reference.
