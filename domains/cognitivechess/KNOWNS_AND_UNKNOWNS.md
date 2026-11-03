# Knowns and unknowns: what competes for attention

Written 2026-11-01, from the full-game stress test (`STRESS_TESTS.md`) and the user's correction of my reading of it.

## The principle (Gerundelle's, not a choice of this track)

**Unknowns pull; knowns support.** A fact is established by what funds it in the SOV structure: its receipts in the
understanding register, its place in the facts register, what followed it in perception. It never has to win anything.
The tournament is for what is open: SOV molecules and their questions (open slots), experiments, ownership instances,
and the moves the world offers, whose outcomes are unknown. A fact takes part in that competition only by supporting
what is open: an SOV molecule binds to the knowns it has evidence with.

The code states the same for the understanding register: "the relation types with too little funding are its open
slots. **Read directly, without competing.**" And `Understanding.observe` counts what followed what from
`mind.perceived`, not from the tournament's winners: learning from facts does not need them to win.

## Where the code departs from it

1. **News enters the tournament as a competitor.** `SovAgent.perceive` sends each change the world reports into the pool
   as a percept molecule (`news = [clause(effect_id(e)) for e in world.diffs]`): `white_king_e1_safety_hanging` is the
   change "White's king became hanging". In the pool it bids like any thought.
2. **Anything active bids, known or not.** A molecule's bid is
   `activation x (1 + binding score) + tension + w_pred x forward + support` (`Mind.think`). Only tension (open sites)
   and forward (what attending would still teach) come from being unknown; the first term pays anything active.
3. **Winners never decay** ("half-life: only molecules that won no slot this tick decay"), and **a thought that has been
   conscious before comes back stronger** (`Mind.present`: activation x (1 + reentry x log(1 + top wins))). So news that
   won once keeps winning, long after it stopped being true.

## What it did (seed 1, both minds with `winner_acts` and the imagination lane; `experiments/facts3.py`)

In the 23 games that ended after one move, Black's moves on offer won thought slots at levels 0–1 and lost them at
level 2 (4 slots) on 89 of 138 ticks; on 26 they never won one. The four top thought slots went to news every tick:

| | winning news (mean) | best move on offer (mean) |
|---|---|---|
| level 0 bid | 2.02 = act 1.44 x (1 + binding 0.41) | 1.78 = act 0.90 x (1 + binding 0.60) + forward 0.12 |
| level 2 bid | 2.23 = act 1.55 x (1 + binding 0.44) | 1.94 = act 0.89 x (1 + binding 0.77) + forward 0.12 |
| tension (open sites) | 0.0 | 0.0 |

The news won with **no pull of its own** (tension 0, forward 0), on activation alone. Much of it was not even true: at a
starting position after one move, `white_king_e1_safety_hanging` (62 ticks) and `material_down` (53) cannot hold, and
`black_bishop_f8_safety_safe` (57) and `..._attacked` (42) cannot both. (Inferred from these impossibilities, not
checked against the board tick by tick.) The moves, the actual unknowns, carried the only expected surprise in the
comparison, and lost.

## A wrong fix, recorded so it isn't repeated

I first proposed: a closed known doesn't bid, its activation goes to what it binds to, and a known may fill an open site
without winning. The second part was a patch around this observation: in `Mind.think` an open site is filled only when
its filler also wins (`if m.sites and b[0] == "partner" and b[1] in win`), and composites need both ends to win. That
assumes facts must take part in the tournament to support, which is the departure itself. Facts support from the
structure.

## The change that follows

**News and facts go to the structure, not the competition.** They are still perceived: the facts register, the follows
and arrivals counts, the meta layer's situations and the receipts all receive them as now. But they do not enter the
tournament as bidders. What competes stays what is open.

**Built 2026-11-01:** `Params.news_in_structure` (off by default; backup `backup/molecules_2026-11-01d/`, suite matched the
reference). `Mind.tick(seen=...)`: molecules perceived but not presented; `SovAgent` sends the world's news there.
What needed checking, from the code: learning (`Understanding.observe`), surprise (`Mind.perceive`), contradiction, the
meta layer's reading of the situation (`here`) and Pandora's re-opening all read perception, not the pool; the facts
register's clauses were never in the pool.

**Measured** (`STRESS_TESTS.md`, the rerun): one-move games on seed 1 fell from 23 of 41 to none; over three seeds, 105
games with none frozen, 95 played to the cap, against 29 games and a freeze on every seed before.
