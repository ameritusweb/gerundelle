"""Rung 7 on the Gerundelle arm: the same scene, moves, endings, reader and author's search as rung7.py, with
Mara and Leo as Gerundelle minds (gerundelle_arm.GerundelleMind; run_ladder.run_acting_gerundelle's way of
putting two in one world).

- The cast's hidden reserves are their stubbornness (how often another may undo what they hold before they
  give the want up): 2 or 4 each, never said.
- signs: past half their stubbornness spent, a mind tires ("Mara grew tired of the latch.").
- Leo, out of the room or watching Ben, finds the box open when he looks again: the lost kept state (the
  lean rung 7's `guards` rule, applied by this runner as a fiction-side rule: Leo's Gerundelle mind never held
  the lid, so its territory has no slot to lose there).
- The tree is grown by replay, not by copying: a Gerundelle mind wraps the world it acts in, so a copy would
  step the original. Each story is simulated from the start with its moves (deterministic in one process);
  Leo's past is lived once and its Mind copied into each replay.

Run: python -X utf8 rung7_gerundelle.py [--top 1]
"""
import copy

from beats import Beat
import rung7
from rung7 import AWAY, ENDINGS, RESOLVES, Reader, by_sentence, entropy, score  # noqa: F401
import worlds

ROUNDS = 220
CHOICE = 8     # a choice point every CHOICE rounds (Gerundelle's stories run ~110 rounds against the lean arm's
               # 13-22; one per round would grow thousands of stories per cast)
EVENT = 0.08   # the reader's expectation of a given authored event per choice point: the lean rung's 0.08 per
               # round, there over ~13 rounds, here over ~13 choice points (first 0.25 "compounded per round", and
               # the reader was 95% sure of Ben's help from the first line)
AWAY_G = 24    # rounds Leo is out (the lean rung's 3 of ~15 rounds, scaled to Gerundelle's ~110: first 3, and no
               # Mara of Gerundelle's could open the box that fast, so "behind his back" never happened)
_PAST = {}


def past_mind():
    """Leo's past (the time he pushed the latch back), lived once."""
    from gerundelle_arm import GerundelleMind
    if "leo" not in _PAST:
        past = GerundelleMind("Leo", worlds.jack_latch_undone(), want="latch_connecting")
        past.run(300)
        _PAST["leo"] = past.agent.mind
    return copy.deepcopy(_PAST["leo"])


class GState:
    def __init__(self, mara_stub, leo_stub):
        from gerundelle_arm import GerundelleMind
        from run_ladder import Helper
        self.world = worlds.jack_in_the_box()
        self.beats = []
        self.leo = GerundelleMind("Leo", self.world, want="latch_connecting", mind=past_mind(), beats=self.beats,
                                  keep=True, see=False, stubbornness=leo_stub)
        self.mara = GerundelleMind("Mara", self.world, want="lid_releasing", beats=self.beats, others=[self.leo],
                                   stubbornness=mara_stub)
        self.leo.others = [self.mara]
        self.leo.contesting.add("lid_releasing")
        self.mara.signs = self.leo.signs = rung7.SIGNS
        self.ben = Helper("Ben")
        self.cast = (float(mara_stub), float(leo_stub))
        self.away, self.used, self.moves, self.round = None, set(), [], 0
        self.seen = {"Mara": 0, "Leo": 0}
        self.ended = False

    def over(self):
        return self.ended or self.round >= ROUNDS

    def available(self):
        out = ["on"]
        if self.over() or self.round % CHOICE:
            return out
        if "away" in rung7.MOVES and "away" not in self.used and self.away is None and not self.leo.done:
            out.append("away")
        failed = any(inv[1] == "lid" and not any(n.startswith("lid_") for n in names)
                     for _, inv, names in self.mara.agent.tried)
        if "help" in rung7.MOVES and "help" not in self.used and failed:
            out.append("help")
        return out

    def beat(self, kind, actor, **kw):
        self.beats.append(Beat(self.world.t, kind, actor, **kw))

    def apply(self, move):
        if move == "on":
            return
        self.used.add(move)
        self.moves.append((self.round, move))
        if move == "away":
            self.beat("leave", "Leo", detail={"called_by": "mother"})
            self.away = AWAY_G
        elif move == "help":
            self.beat("rise", "Ben")
            self.world.actor = "Ben"
            for obj in ("latch", "lid"):
                state = self.world.states()[obj]
                if obj == "latch" and state != "connecting":
                    continue
                self.ben.push(self.world, ("hard", obj, state), self.beats)

    def turn(self, m):
        self.world.actor = m.name
        self.seen[m.name] = m.step(self.seen[m.name])

    def advance(self, settle=8):
        self.round += 1
        self.turn(self.mara)
        reached = self.mara.pending is not None or any(b.kind == "reach" and b.actor == "Mara" for b in self.beats)
        if self.mara.pending:
            for _ in range(settle):
                self.turn(self.mara)
            self.mara.write_try(*self.mara.pending, reach=True)
        if reached or self.mara.done:
            self.finish()
            return
        if self.away is not None:
            self.away -= 1
            self.world.t += 1
            if self.away == 0:
                self.away = None
                self.beat("return", "Leo")
            return
        if not self.leo.done:
            self.turn(self.leo)

    def finish(self):
        """The want closed: Leo, out, comes back; in the room and still keeping it, he sees what happened."""
        self.ended = True
        if self.away is not None:
            self.away = None
            self.beat("return", "Leo")
        reach = next((b for b in self.beats if b.kind == "reach" and b.actor == "Mara"), None)
        if reach is not None and not self.leo.done:
            by = reach.detail.get("by") or "Mara"
            self.beat("lost", "Leo", obj="lid", hole="own:lost:lid", detail={"kept": "lid_locking", "by": by})
            self.beat("feel", "Leo", obj=by, hole=f"other:{by}", detail={"phase": "anger", "unexpected": []})
            self.leo.done = True

    def ending(self):
        reach = next((b for b in self.beats if b.kind == "reach" and b.actor == "Mara"), None)
        if reach is not None and reach.detail.get("by") == "Ben":
            return "help"
        if reach is not None:
            lost = any(b.kind == "lost" and b.actor == "Leo" for b in self.beats)
            return "behind" if lost else "outlast"
        if any(b.kind == "feel" and b.actor == "Mara" and b.detail["phase"] == "resignation" for b in self.beats):
            return "outlasted"
        return "unresolved"


def fork(s):
    """A copy of a story at a choice point: world, minds and beats copied together, the copy's world wrapped
    again for the copy's minds (the original's wrappers would step the original)."""
    c = copy.deepcopy(s)
    c.world.__dict__.pop("act", None)   # back to the world's own step
    for m in (c.mara, c.leo):           # the order they wrapped it in at first
        m.world = c.world
        m.wrap()
    return c


def grow_fork(state, weight=1.0, leaves=None):
    leaves = [] if leaves is None else leaves
    while not state.over():
        avail = state.available()
        for m in avail[1:]:
            other = fork(state)
            other.apply(m)
            other.advance()
            grow_fork(other, weight * rung7.prior(m, avail), leaves)
        weight *= rung7.prior("on", avail)
        state.advance()
    leaves.append((weight, state))
    return leaves


def replay(cast, moves):
    """A story with these moves (round -> move, 'on' included), run until the next choice point past them, or to
    its end. Returns (state, whether it stopped at a choice)."""
    s = GState(*cast)
    last = max(moves) if moves else -1
    while not s.over():
        if s.round in moves:
            s.apply(moves[s.round])
        elif s.round > last and len(s.available()) > 1:
            return s, True
        s.advance()
    return s, False


def grow(cast, moves=None, weight=1.0, leaves=None):
    leaves = [] if leaves is None else leaves
    moves = dict(moves or {})
    s, choice = replay(cast, moves)
    if not choice:
        leaves.append((weight, s))
        return leaves
    avail = s.available()
    for m in avail:
        grow(cast, dict(moves, **{s.round: m}), weight * rung7.prior(m, avail), leaves)
    return leaves


def forest():
    out = []
    for mr in RESOLVES:
        for lr in RESOLVES:
            for w, s in grow_fork(GState(int(mr), int(lr))):
                out.append((w / len(RESOLVES) ** 2, s))
    return out


def main():
    import argparse
    import sys
    import time
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=1)
    args = ap.parse_args()
    t0 = time.time()
    rung7.EVENT = EVENT
    leaves = forest()
    rows = rung7.search(leaves)
    print(f"{len(leaves)} stories in {time.time() - t0:.0f}s; {len(rows)} resolved")
    best = {}
    for r in rows:
        best.setdefault(r["ending"], r)
    from collections import Counter
    print("endings:", Counter(s.ending() for _, s in leaves))
    for e, r in best.items():
        print(f"best {e:10} cast {r['state'].cast} moves {r['state'].moves} value {r['value']} held {r['held']} "
              f"rise {r['rise']} drops {r['drops']} sentences {len(r['sentences'])}")
    from measure import evaluate
    for k, r in enumerate(rows[:args.top]):
        m = evaluate(r["scene"], r["sentences"])
        print(f"\n== #{k + 1} {r['ending']} cast {r['state'].cast} moves {r['state'].moves} value {r['value']} "
              f"round-trip {m['round_trip']:.2f}")
        for (pi, text, _), d in zip(r["sentences"], r["dists"]):
            dist = " ".join(f"{rung7.SHORT[e]}={p:.2f}" for e, p in sorted(d.items(), key=lambda kv: -kv[1]))
            print(f"  {entropy(d):4.2f}  {text:70.70}  {dist}")


if __name__ == "__main__":
    main()
