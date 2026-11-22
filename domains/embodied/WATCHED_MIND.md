# A robot that watches a Gerundelle mind (future direction)

Status: an idea, not built. From a conversation on 2026-11-20, after the cognitivechess_v2 play app and the assumptions discussion.

## The idea

An embodied robot holds a Gerundelle mind in its mind's eye: while its body acts (often from fast, learned motor skill), it runs the
mind's world of the scene and watches what the mind wants, fears and would do, and the two feed back on each other.

- **Body to mind.** What actually happened comes back as lived experience: the mind's predictions are confirmed or belied by the real
  world, so its territory and its weights are grounded in physics rather than a simulation (the force world, with a real force world).
- **Mind to body.** The mind offers what learned skill lacks: wants, felt losses ("that leaves something exposed"), imagined
  alternatives, and an explanation for each decision (as cognitivechess_v2's why.py does for each move).

## Why it fits

1. **The body is the challenge tool.** The mind's assumptions ("I can't reach that", "this will fall") are tested by the body trying,
   as Stockfish or a minimax search tests a chess mind's "this loss is forced". Disagreement between the two is the signal that an
   assumption is wrong.
2. **The mind challenges the body's habits.** A learned skill is a heap of unmarked assumptions (as a language model's fillers are).
   The watching mind can hold them as *assumed*, a provenance beside lived, told and imagined, funded by their own record (how often
   that kind held or broke, under which conditions, how old), and challenge the ones whose funding falls low.
3. **It is the watching faculty.** In the territory theory (substance-structural-coherence/intrinsic-motivation), territory is
   observed from skilled play; a robot watching its own mind, or a mind watching a skilled body, is that faculty.
4. **Every act is inspectable.** The mind's explanations are a running "why" for what the robot does.

## Emotions in sync with the inner mind

The mind's phases are readings of its territory, not scripts: sadness a region lost, anxiety a claim failed once, frustration claims
failing repeatedly, joy a claim taking, curiosity an unclaimed region winning attention, calm nothing pulling. The robot expresses
them (posture, voice, face, movement) in sync with the phases, intensity from the phase's bid.

- Legible: people read when it is stuck, uncertain or exploring without a log.
- Social feedback: frustration draws help; help that works is something the mind has reason to value (care from importance).
- The rule: expression is never decoupled from the phase. No joy shown to please, no calm shown to reassure: a performed emotion is
  no longer a signal, and that is how people come to over-trust machines.

## Playing games: two force worlds

The robot could play chess, Go or any of the domains, guided by the mind, in two layers grounded differently:

1. **The game's force world is exact.** The rules are the physics: the mind's world is the board (cognitivechess_v2's plans, bearings,
   reach, territory), unchanged; nothing to calibrate.
2. **The physical force world is calibrated by reality.** Lifting a knight without toppling its neighbours, placing a stone in a crowded
   corner, reaching across the board: the robot's model of weights, friction and clearance starts as a guess, and each lived outcome
   confirms or belies a prediction; the model is corrected from its own record (as the grasp work learned constraints from failures).
   The world never tells the mind the answer; reality belies the wrong guesses.

One mind, many worlds. On a real board against people: watching the opponent is the watching faculty for real, its phases are visible
across the table, and the body challenges assumptions at both layers ("this capture is forced", tested by search; "I can reach that
piece without knocking the rook", tested by trying).

## The language centre

A language model as the language centre: it watches, in parallel, the world (what is in front of the robot), the force world (what is
possible; the robot's physical guesses) and the inner mind (wants, phases, explanations, assumptions), and speaks when appropriate.

1. **The mind decides whether to speak; the language model decides how.** Speaking is an act in the tournament (a want to be helped, a
   frustration voiced, an explanation asked for); when it wins, the language model renders the mind's actual state into words. It never
   decides on its own that there is something to say, so it can't talk past what the mind holds.
2. **Provenance becomes language.** Lived: "I saw the bishop take it". Told: "I was told this is forced". Imagined: "I could try Nf3".
   Assumed: "I'm assuming the rook can't get out". The hedges are read off the register, not style: what a language model alone lacks
   is knowing which of its sentences are fillers; the mind supplies it.
3. **Listening.** What people say is parsed into the mind's terms and enters as told, funded by credulity: "watch your knight" is a
   told prediction to test, not an order.
4. **Its own fillers stay out.** Anything the language model adds about the world beyond what the mind holds comes in as told, from
   the language centre, never as lived; else its hallucinations would become the mind's beliefs.

With three streams it can say what no single one supports: "I wanted to take the rook, but I'm not sure I can reach it without
knocking the bishop." It is the fiction generator turned around (minds' structure into prose about invented worlds; here a live mind's
structure into speech about the real one).

## Asking it what it thinks

While it plays, you can ask: what are your assumptions, what ideas are you experimenting with, what do you want, what are you afraid
of, why did you play that. The language model answers honestly by construction: it reports what the register holds, not what sounds
plausible.

- Assumptions: the beliefs held as assumed, with their funding and kind ("I'm assuming the rook on h1 is lost; that kind has held 7 of
  9 times. I'm assuming my queen is safe on d3; I haven't checked that one").
- Experiments: the running experiment and its queue ("testing whether Nf3 then Bg2 keeps their bishop out; two moves in").
- Wants and fears: the held want and its stack; the anti-want.
- Why that move: the route, the predictions, the tournament's top (what why.py already writes).

Unlike a language model asked about its own reasoning, which composes a plausible account afterwards (often unfaithful to what drove
the answer), here the account is the cause, read from the register, and every claim can be checked against the record.

The question is itself told input: "what are you assuming?" can prompt the mind to look at its least-funded assumptions and challenge
one, as a coach's question makes a player re-check. Talking to it could make it play better.

First prototype: cognitivechess_v2's play app. why.py already reads wants, anti-wants, experiments and the tournament; assumptions come
once the assumed provenance exists (the parallel session's POC). A chat box beside the Why panel: the question, the relevant register
state gathered, a language model phrasing the answer from it alone.

## Listening, and trusted voices

To be a good listener and not too distracted to listen (the lesson of cognitivechess_v2's stuck mind: anything that must compete with
the mind's own thoughts for the shared slots loses once the mind matures):

1. **Getting the words into attention.** A lane for what is heard (as the move lane, push_slots): an utterance always reaches the top
   at least briefly. Held until placed (linked to its concepts, answered or acted on), as a question is, so it cannot decay unread. Its
   own speaking yields when someone speaks; a running experiment yields to a speaker as it yields to stakes. A temperament,
   attentiveness, sets how much a heard sentence interrupts.
2. **Wanting to understand.** "What they said, understood" is territory: held when placed (its prediction of the meaning holds),
   contested when unsure (opening a clarifying question, rendered by the language centre), lost when misheard (lived, so it learns where
   it mishears).
3. **Trusted voices.** Told input funded dynamically by the speaker's record, not one credulity number: a voice whose claims held, or
   whose requests paid off, is believed more (care from importance, applied to listening).
4. **A request is not a claim.** "Examine your assumptions" (asked on move 2) becomes a want, the least-funded assumptions challenged,
   its bid funded by the speaker's record of requests that led somewhere (an assumption broken, a piece saved). Before a record, the
   lane still guarantees it is heard; it may not outbid an urgent move (a hanging queen first). The result is reported either way ("I
   checked the queen's defence of c3: Bd2 does it, the queen is free" / "I checked; they held"), so a request is never silently
   ignored.
5. **"Please stop and consider X": stop, consider, report, then act.** Two parts, working differently:
   - *Stop* halts acting at once and unconditionally: no move while the request stands (as the mind holds still while the tool answers,
     `asking`). A hard rule of the body, not weighed in the tournament: the one exception to "no rules", for safety, and independent
     of trust.
   - *Consider X* is weighed, with priority: a want, X examined (its beliefs found and challenged, the result placed), run before the
     mind acts again. It must end (minds froze for 400 slices this week): when X is placed, or when patience runs out, said so ("I
     couldn't settle whether the sacrifice works"). Then the language centre reports ("I considered Bxf7: it loses the bishop for a
     pawn, so Nf3") and the hold lifts. Trust sets how much X weighs in the conclusion, not whether it is considered.
6. **Measuring it.** Latency to attention; placement (understood vs dropped); clarifications asked; distraction (heard sentences
   decayed while absorbed); outcome (did "watch your knight" save it).

## The hurdle

Speed: a mind slice takes about 1-3 s now. The mind would run a slower loop (strategy, watching, challenging, feeling) over the body's
moment-to-moment control, roughly as deliberation sits over motor skill in people.

## Related

- Assumptions as a provenance, funded dynamically; assumption metrics (formation, challenge, break rates, precision, recall,
  calibration) against performance, with interventions for causality: the 2026-11-20 conversation; the assumption-challenging POC in
  the parallel session.
- CONSTRAINT_DISCOVERY.md (failures as constraint revelations), EMBODIED_COGNITION.md.
