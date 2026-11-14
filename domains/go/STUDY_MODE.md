# Study mode

A design, not built. Written 2026-11-13. Its companion is `FROZEN_PLAY.md`: the mind plays a league game frozen, queuing what it would have learned from, and studies the queue between games.

## The user's idea

> "it then 'queues' up dreams based on what it wants to explore or experiment with further; so it enacts the dreams between league matches"

and, on whether that learning counts:

> "it would be like, if I took out a Go board and 'replayed' key events from the game, so it would technically be lived"

## Decided (the user)

- **Between league games the mind works through what it queued during the game.**
- **It does so on a real board, so what it learns is lived.** This follows Gerundelle's own rule: lived means the world answered, not the mind's model. A position set up on a real board and played out under the board's physics is experience, even after the game.

So this is **study, not dreaming.** The dream (`Params.dreams`, `dream_go.py`) imagines boards, and what a dream shows is written as imagined and funds nothing (the firewall). Study sets up real positions, and the world answers.

## How it would work (proposed)

1. **Set up the board.** For each queued event, the mind's seat (a real `GoWorld`) is set to the board as it stood. `dream_go.configure` already does this set-up for the dream: stones, the board before the last stone, the mind to place, the board at rest.
2. **Replay what happened.** The mind makes the push it made in the game. The physics answers again (captures, breath, which opportunities die or live), and the receipts the game deferred are written, lived.
3. **Try what it wanted to try.** If the event carried an open question or an experiment, the mind makes the other placement it would have tried. The board answers, and that is lived too.
4. **Then frozen play again** for the next game, with the SOV as study left it.

What study writes is what a lived slice writes: relations with their receipts, Abstract over the new structure, answered questions and experiments, meta records. It is the learning half of a slice, moved from the game to the study.

## The other side's stones (open, for the user)

A study board has no opponent. It answers the physics of the mind's own stones, but no one plays the other side's reply.

- **Replaying what happened:** the other side's stones are what it actually played. That is memory of a lived game, so it stays lived.
- **Trying an alternative:** the other side's reply to a placement it never saw isn't known. The options:
  - **(a) Only what the board alone answers.** The push's own consequences before any reply: captures, the loads read, which opportunities die. Lived, but shallow.
  - **(b) The reply filled in by the mind's own expectation,** marked as such: a told link, not lived. Deeper, but weaker provenance.
  - **(c) The other side's actual reply from the game, where it still applies.** Lived where it fits.

## What gets studied first (open)

- The order: the most recent first, the losses first, or the tournament choosing among the queue as it chooses any thought (the dream lets the tournament choose: `dream_maze.chosen`).
- How much: a fixed number of events, all of them, or as much as the mind's energy allows (`mental_energy`, `rest`).
- Whether temperament sets either. A curious mind might study more; a patient one longer per event; an accepting one let unanswered events go sooner (`acceptance`).

## Related pieces already built

- `dream_go.RemembersGames`: the boards of every push in the game just played.
- `dream_go.configure`: a board set up as it stood, the mind to place.
- `dream_go.dream`: the between-games loop with trials; study would follow its shape.
- Inquiry's experiments and plans (`exp:`, `inquiry.plans`): what the mind would try. In frozen play they'd be queued instead of run.

## Not decided

Whether study replaces the dream, or the dream stays for what can't be set up on a real board (imagined variations, marked imagined, as now).
