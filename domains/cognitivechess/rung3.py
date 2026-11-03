"""Rung 3 (chess-sov-plan.md): two minds, contested territory.

Rung 1's defender family (the knight on d5 defended by the bishop on b7, or hanging, drawn per episode), now with Black a
Gerundelle mind of its own instead of the authored reply. Both play on one `DuelWorld` (civilization P4's way: each round
every mind steps once). White wants its standing up (`standing_white_up`: the material balance when its turn comes round
again, after Black's answer); Black wants its own (`standing_black_up`). An episode is four half-moves.

Opponents for the same White mind: Black a mind, or Black scripted (rung 1's rule: take back on the square just taken if
it can, else pass), so White's results against a rule and against a mind can be set side by side.

Schedules (a named choice, 2026-10-31): `rounds`, each round every mind steps once (P4's, as first run); `turns`, the
side to move steps until it moves (at most TURN_STEPS slices), then the other side takes one slice to see the answer. In
`rounds` a thinking Black took one or two of White's slices to answer, and White's new standing landed inside the watch
of White's own move only a third of the time: arriving after it, or dropped when White moved in the slice that would
have shown it, it credited no push (experiments/delivery3.py). The scripted Black answered at once, so it never showed.
In `turns` the other side's thinking takes none of the mover's time, as at a chess board. Both schedules spend 2 x rounds
mind-steps.

Measured: each side's wants met (its standing delivered as up); every episode's end (White's balance just before the
board is set back: what happened, whether or not it reached a mind); White's wins in the defended configuration (the
combination); the feelings each side forms; what each side learns (its splits).

Black's want (`--black-want`): `up` (its standing up, as White's; the first runs) or `kept` (`holding_black_kept`: met
when what was taken is won back, a defender's want; DuelWorld's opt-in holding facts).

Run: python -X utf8 rung3.py [--seeds 10] [--rounds 800] [--black mind,scripted] [--arm base] [--schedule rounds|turns]
     [--black-want up|kept] [--given]
"""
import argparse
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import chess  # noqa: E402
from chessworld import RUNG1, DuelWorld, VALUE  # noqa: E402
from gerundelle_arm import GerundelleMind  # noqa: E402

ARMS = {"base": dict(polarity=True, subwants=True, sub_yield=True, sub_tested=True),
        "full": dict(polarity=True, subwants=True, converge=True, sub_cost=True, sub_yield=True, sub_tested=True,
                     bridge=True)}


TURN_STEPS = 5   # a side's slices to make its move under the turns schedule: under the world's IDLE (6), so a mind
                 # thinking does not end the episode


class ScriptedBlack:
    """Rung 1's authored reply, as a player: take back on the square just taken with the least valuable piece that can,
    else pass."""
    name, done, pending = "Black", False, None

    def __init__(self, world):
        self.world = world

    def step(self, seen):
        w = self.world
        if w.board.turn != chess.BLACK or w.mated or w.board.is_game_over():
            w.act(None)
            return seen
        last = w.board.peek() if w.board.move_stack else None
        took = last is not None and w.board.piece_at(last.to_square) is not None and len(w.board.move_stack) and \
            w.board.move_stack[-1] is not None
        legal = [m for m in w.board.legal_moves if last is not None and m.to_square == last.to_square]
        if legal and took:
            m = min(legal, key=lambda m: (VALUE[w.board.piece_at(m.from_square).piece_type] or 99, m.uci()))
            san = w.board.san(m).rstrip("+#")
            inv = next(i for i in w.invitations() if i[0].split(" ", 1)[-1] == san)
            w.act(inv)
        else:
            w.act(("pass", None, None))
        return seen


WANTS = {"up": "standing_black_up",      # Black wants to gain, as White does (rung 3's first runs)
         "kept": "holding_black_kept",   # Black wants back what was taken: a defender (DuelWorld holding)
         "keeper": "holding_black_kept"}  # the same state, kept (GerundelleMind keep): wanted only once undone, so no
                                          # sub-want to lose it first (rung 3, finding 15)


def make(seed, black, arm, black_want="up", given=False, fen=RUNG1, half_moves=4):
    """The world and its two players: White a Gerundelle mind wanting its standing up; Black a mind (wanting
    WANTS[black_want]) or scripted. given: each mind's pieces are its given territory (Territory.given), and a captured
    piece leaves view (DuelWorld owned), so a capture is a loss in the mind's own register."""
    w = DuelWorld(fen, order=seed, seed=seed, half_moves=half_moves, holding=black_want in ("kept", "keeper"), owned=given)
    minds = []
    for side in ("White", "Black"):
        if side == "Black" and black == "scripted":
            minds.append(ScriptedBlack(w))
            continue
        want = "standing_white_up" if side == "White" else WANTS[black_want]
        if side == "Black" and black_want == "keeper":   # a keeper: one want at a time, back when undone (the arm sets a
            m = GerundelleMind(side, w, want=want, want_count=1, keep=True, keep_wait=False)   # met want again below its
        else:                                                                                 # count, kept or not)
            m = GerundelleMind(side, w, want=want, want_count=10 ** 6)
        for k, v in ARMS[arm].items():
            setattr(m.agent.mind.p, k, v)
        if given:
            terr = m.agent.mind.territory
            terr.given = w.side_pieces(side)
            for r in terr.given:
                terr.row(r)
            terr.update(terr.given)
        minds.append(m)
    return w, minds


def play(w, minds, rounds, schedule="rounds"):
    """Step the players: `rounds`, every mind once per round; `turns`, the side to move until it moves (at most
    TURN_STEPS), then the other side one slice. Both spend 2 x rounds mind-steps."""
    seen = {m.name: 0 for m in minds}
    by = {m.name: m for m in minds}

    def step(name):
        w.actor = name
        seen[name] = by[name].step(seen[name])
    if schedule == "rounds":
        for _ in range(rounds):
            for m in minds:
                step(m.name)
        return
    spent = 0
    while spent < 2 * rounds:
        mover = "White" if w.board.turn == chess.WHITE else "Black"
        other = "Black" if mover == "White" else "White"
        before = (w.moved, len(w.episodes))
        for _ in range(TURN_STEPS):
            step(mover)
            spent += 1
            if (w.moved, len(w.episodes)) != before or spent >= 2 * rounds:
                break
        if spent < 2 * rounds:
            step(other)
            spent += 1


def run(seed, black, arm, rounds, schedule="rounds", black_want="up", given=False):
    w, minds = make(seed, black, arm, black_want, given)
    log, act = [], w.act

    def logged(inv=None, hold=False):
        ep, cfg, who = len(w.episodes), w.config, w.actor
        ev = act(inv, hold)
        log.append((ep, cfg, who, inv[0].split(" ", 1)[-1] if inv else None, ev))
        return ev
    w.act = logged
    ends, reset = {0: Counter(), 1: Counter()}, w.reset

    def counted_reset():   # every episode's end, read just before the board is set back
        ends[w.config][w.balance("White")] += 1
        reset()
    w.reset = counted_reset
    play(w, minds, rounds, schedule)
    w.close()
    wanted = {m.name: m.want.rsplit("_", 1) for m in minds if hasattr(m, "agent")}   # name -> (object, state)
    met = Counter(who for _, _, who, _, ev in log for e in ev
                  if who in wanted and e.startswith(wanted[who][0] + ":") and e.endswith("-> " + wanted[who][1]))
    defended = sum(1 for _, cfg, who, _, ev in log if who == "White" and cfg == 0 and "standing_white: even -> up" in ev)
    feel = {m.name: Counter(p.split(":")[1] for p in m.agent.mind.phases.info) for m in minds if hasattr(m, "agent")}
    splits = {m.name: sorted({sp["tag"] for sp in m.agent.mind.meta.splits.values()})[:6] for m in minds if hasattr(m, "agent")}
    moves = Counter(who for _, _, who, mv, _ in log if mv)
    subs = {m.name: Counter(g for _, g, k in m.agent.sub_log if k == "set") for m in minds if hasattr(m, "agent")}
    return dict(met=dict(met), defended=defended, episodes=len(w.episodes) - 1, feel=feel, splits=splits, moves=dict(moves),
                ends={c: dict(e) for c, e in ends.items()}, subs=subs)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--black", default="mind,scripted")
    ap.add_argument("--arm", default="base")
    ap.add_argument("--schedule", default="rounds", choices=("rounds", "turns"))
    ap.add_argument("--black-want", default="up", choices=tuple(WANTS))
    ap.add_argument("--given", action="store_true", help="each mind's pieces are its given territory (captures are losses)")
    args = ap.parse_args()
    for black in args.black.split(","):
        t0, rows = time.time(), []
        for k in range(args.seeds):
            r = run(k, black, args.arm, args.rounds, args.schedule, args.black_want, args.given)
            rows.append(r)
            print(f"  Black {black} seed {k}: wants met {r['met']}; White's defended wins {r['defended']}; episodes "
                  f"{r['episodes']}; ends {r['ends']}; moves {r['moves']}; feelings {r['feel']}; splits {r['splits']}", flush=True)
        tot = sum((Counter(r["met"]) for r in rows), Counter())
        feel = {s: sum((r["feel"].get(s, Counter()) for r in rows), Counter()) for s in ("White", "Black")}
        ends = {c: sum((Counter(r["ends"][c]) for r in rows), Counter()) for c in (0, 1)}
        up = {c: f"{ends[c]['up']}/{sum(ends[c].values())}" for c in (0, 1)}
        bsubs = sum((r["subs"].get("Black", Counter()) for r in rows), Counter())
        print(f"Black {black:8} wants met {dict(tot)}; White's defended wins {sum(r['defended'] for r in rows)}; "
              f"episodes {sum(r['episodes'] for r in rows)}; episodes ending White up: defended {up[0]}, hanging {up[1]} "
              f"({dict(ends[0])}, {dict(ends[1])}); Black's sub-wants set {bsubs.most_common(4)}; feelings {feel}  [{args.schedule}, Black wants {args.black_want}{', given' if args.given else ''}] {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
