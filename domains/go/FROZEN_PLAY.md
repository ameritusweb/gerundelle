# Frozen play

A design, not built. Written 2026-11-13 during the first temperament league (`league.py`). Its companion is `STUDY_MODE.md`.

## The user's idea

> "a 'frozen learning mode', where it plays moves on auto-pilot without updating its SOV; it then 'queues' up dreams based on what it wants to explore or experiment with further; so it enacts the dreams between league matches; then goes back into frozen learning mode for the next league game"

What prompted it: league games grew from about 2 minutes each to about 18 as the minds learned. A Gerundelle mind's cost per slice grows with what it holds, and a mind that learns while it plays carries that cost into every move.

## Decided (the user)

- In a league game the mind plays without updating its SOV.
- While it plays it queues what it wants to explore or experiment with further.
- Between games it works through that queue (`STUDY_MODE.md`), then plays the next game frozen again.
- Studying on a real board is lived, not dreamed: "it would be like, if I took out a Go board and 'replayed' key events from the game, so it would technically be lived".

## What freezes and what stays live (proposed, my reading)

A slice's work splits into acting and learning. The mind can't play without the acting half: its wants come from the territory register, so the register is its motivation, not its learning.

| Stays live: acting | Frozen: learning, queued instead |
|---|---|
| perceiving (`self_noticed`), the world's predictions of kills and losses | writing relations into the SOV (`Understanding.add`): receipts, lived or told |
| the territory register: what is held, lost, contested (`run.give`, `track_region`) | Abstract (`analogize`, `analogize_concepts`) and its transfers |
| wants from ownership slots, sub-wants from known ways, the want stack | posing questions (`q:`), running experiments (`exp:`, inquiry plans) |
| anti-wants and their aversion | the meta layer's records (decision paths, `meta:` targets) |
| the tournament and the choice (commit steps, plans, the winner) | a prediction's answer turned into funding (confirmed or rejected) |
| commits made and followed | `dormancy`'s storing (nothing new to store while frozen) |

So "auto-pilot" means acting from the SOV as it stood at the game's start, with the register and its wants live.

## What gets queued (proposed)

The events the mind would have learned from in the moment, each with the board as it stood (`dream_go.RemembersGames` already records every board the mind pushed on):

- a loss: a region going lost, an anti-want set;
- a prediction that didn't come, or a loss that came unpredicted;
- a surprise: a change no push of the mind's predicted;
- an open question it would have posed, an experiment it would have run;
- a commit and its answer.

Each entry is the event, the board, the push the mind made, and what came.

## Open, for the user

- **Exactly what freezes.** The table above is my reading. In particular:
  - whether the meta layer freezes;
  - whether a prediction's answer is queued or applied (the register uses it at once for owned predictions).
- **Whether wants and anti-wants should be fixed for the game,** or only formed from what is already held and lost. They aren't "learning" in the SOV's sense, but they change during play.
- **How long a queue may grow,** and whether temperament sets it: a curious mind queues more.
- **Whether the league runs frozen for every profile,** or frozen play is itself a profile.

## What it would change in the league (expected, not measured)

- **Faster games:** none of the learning half runs during play. How much of a slice is learning hasn't been measured.
- **Settled minds:** each game is played by the mind as it was at the game's start, so a result compares settled minds, not minds changing mid-game. That is closer to what an Elo is meant to measure.
- **Learning moves between games:** every lesson a game teaches is learned in study, so a game's lessons arrive in the next game, not later in the same one.

## Where it would live

The acting/learning split is in Gerundelle (`molecules.py`, `sov_agent.py`), behind a switch, off by default, as every other Gerundelle change is (`analogy/DRIFT.md`). The queue would be the agent's. The league's runner would put a mind into frozen play for a game and into study between games.
