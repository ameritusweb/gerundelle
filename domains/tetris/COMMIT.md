# Commit: committing to a sequence saved in the prediction SOV

`Params.commit` in `analogy/molecules/sov_agent.py` (the comments are at lines 478-507, the code at 509-623). Built 2026-11-12. In tetris it is
on by default as of clean5 (`run.SWITCHES`, `commit=True`). Elsewhere it is off unless a domain turns it on.

## Why it exists

A tetris mind at luck 0 would line a piece up, own the prediction that it would clear, and then push it off again: since slice 12,000, 38 of
44 predictions were rejected (`spot_predictions.py`). I proposed having the world label each push by whether it kept the piece aligning. The
user turned that down:

- "no, that's cheating, it needs to learn when to trust its own predictions"
- "there would be a new action called 'commit'. It would be forced to 'watch' until the potential effect is expected. Where it either does or
  does not occur."
- "maybe it should instead save the sequence of actions at every tick leading up to the potential effect. That way, it works for Go and tetris
  generally, and isn't limited to these wait and see games"
- "it commits to the sequence, which gets saved in the prediction SOV"
- In a two-player game, "if the opponent does something unexpected, the commitment dissolves"
- "in tetris, the commitment can't dissolve because there is no opponent"

The world never tells the mind whether a push is good. The mind learns which commits to trust from its own record: what came after it
committed.

## Where the sequences come from

Each slice, before it perceives, `force_predict` (around line 1246) reads `world.push_predictions()`. That returns
`(effect, n, forces, rel, chain)` for each chain of pushes the world's forces say leads to a potential effect from here, such as a clear or a
piece bearing on the floor. In each tuple:

- `effect` is the effect as the world shows it.
- `n` is the number of slices until it is due.
- `forces` is the force structure, which names its prediction SOV.
- `rel` is the effect relative to the piece, so the same structure recurs in different places.
- `chain` is the pushes, in order.

These are kept as `self.sequence_predicted`. The first push of each chain is told (self-talk) that it causes `potential:<rel>`.

## 1. On offer: `commit_offers`

`SovAgent.perceive` adds the commits to the invitations (line 151). Nothing is on offer while the mind is already committed, or when the world
offers no push, because committing has to give something up. Two kinds are offered:

| Commit push | When it is offered | Its sequence |
|---|---|---|
| `commit_push:potential_<effect>_standing` | for each prediction of the mind's that stands unbroken and unanswered | nothing pushed: watch until it is due |
| `commit_push:potential_<rel>_<push+push+...>` | for each chain in `sequence_predicted` | those pushes in order, then watch |

A commit is a push of the mind's own on the prediction's region (`und.owners[c] = "potential_<rel>"`). Because it is named relatively, the
same commit recurs across situations and builds up a record. No rule chooses it: it competes in the tournament like any other push.

## 2. Made: `commit_to`

When the winner is a commit (line 397):

- **standing**: it takes the open prediction with that effect that is due soonest.
- **sequence**: it finds the matching chain, then reuses the open prediction for `(effect, now + n)` or stands a new one through
  `stand_prediction`. That writes the SOV's forces where Abstract can see them, keeps the instance open until it is due, owns
  `potential:<rel>` while it stands, and meets a want for it.
- If nothing is left to commit to (the prediction was answered, or the forces moved on, this slice), the mind idles and the commit comes to
  nothing.
- Otherwise it marks the prediction `committed`, sets `self.committed` (`inv`, `ins`, the facts, `since`, `left` = the chain, `steps` = []),
  logs `made` in `commit_log`, records the decision path, and makes the first step **in the same slice**. A standing commit's first step is a
  watched slice.

## 3. Followed: `commit_step`

While it is committed (lines 329-338):

- the scene is not set back (`world.renew` is skipped, as it is during an experiment);
- a slice spent watching a push it made is recorded as `"watching"`;
- otherwise the next push in `left` is made. A push the world doesn't offer when its turn comes is recorded as `"not on offer: <push>"` and
  skipped, and the rest of the chain is still followed;
- once the chain runs out, each slice is `"wait"`: the mind holds and pushes nothing.

A committed prediction is not called broken on the way (`force_predict`, line 1187). The pushes of its own sequence lead toward the effect, so
they can't break it. The world answers it when it is due.

## 4. Dissolved: `commit_on_track`, `commit_dissolved`

Both conditions must hold:

1. **another has moved something since the commit**: the world says who through `world.others`, which tetris doesn't have; and
2. **the forces no longer predict the effect along what is left**: the remaining chain is no longer in `sequence_predicted`, or with nothing
   left, the effect is no longer in `predicted_now`.

Then the commit is over and the mind is free again. The sequence as far as it went is saved in the prediction SOV's `sequences` as
`dissolved`, no receipt is written because it wasn't seen through, and the prediction becomes an ordinary one again. **In tetris a commit never
dissolves.**

## 5. Answered: `commit_answered`

When the prediction has its outcome, or `due + world.horizon` has passed:

- **The sequence goes into the prediction SOV.** `sov["sequences"]` gets `{commit, made, due, steps, outcome: came | did not come}`. `steps` is
  what the mind did at every tick from the commit to the answer.
- **If it came:** `commit_push:... causes potential:<rel>` (and `caused_by`) is written *seen* at weight 1.0, because the mind watched the
  whole way. The territory claim on `potential_<rel>` takes, so the mind owns what it committed to.
- **If it didn't come:** `commit_push:... causes no_change`, seen.
- **Either way:** the commit is `caused_by` the agent, meta-cognition observes its outcome (`observe_mode`), an experiment whose last step was
  the commit reports what it found, the commit goes into `tried` and `pushed` like a push, and `commit_log` gets `came` or `did not come` with
  the number of slices it was watched.

The usual prediction answer runs too (`force_predict`): confirmed means the told receipts stand, rejected means they are taken back. A
committed prediction has no `broken_by`, so a rejected one blames no push.

## What makes a commit worth choosing again

Nothing in the world scores it. A commit that came carries a seen `causes potential:<rel>` at full weight, and the mind owns that region. In
the next situation with the same relative effect, the same commit is on offer, and the tournament funds it from that record. One that didn't
come carries `causes no_change`. That is how the mind learns when to trust its own predictions.

## My readings (the user's to change)

- A commit is on offer only while the world offers a push too.
- Each sequence is its own push, and the tournament chooses among them.
- A push in the sequence that the world doesn't offer when its turn comes is left out; the rest are followed.
- A committed prediction is answered when it is due and isn't called broken on the way.

## Tried

`trace_commit.py`, 400 slices from `clean3_13000`:

| | Predictions confirmed | Predictions rejected | Pieces cleared |
|---|---|---|---|
| commit off | 10 | 20 | 6 |
| commit on (sequence) | 11 | 1 | 10 |

With commit on, 5 commits were made and all 5 came.

- `run_commit.py <checkpoint> <to> [name]` continues from a checkpoint with commit on (`--no-commit` turns it off, `--no-ground` turns off
  ground-piece holding) and reports commits made, came, did not come and dissolved.
- `clean5` (`trace_decisions.py`, from 0, commit and ground both on) reached luck 0 at slice 6,400. clean3 got there at 12,200.

## Noted, not built: chess

The user, 2026-11-12: "that should work good in chess, because you should theoretically be able to commit to a certain potential effect if it
is forced and the opponent's reply is expected". In chess a forced reply (the other side has only one legal reply) is known from the forces
alone, as gravity is in tetris. A sequence through forced replies could be committed to and owned; a reply that is expected but not forced is
where a commitment can dissolve. This would need the Warp chess world to follow forces through a reply and say whether it is the only legal
one, and a commitment to wait for its turn between its pushes.
