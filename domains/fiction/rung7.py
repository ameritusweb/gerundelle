"""Rung 7: several endings held open.

The scene is rung 4's (Mara wants the box open; Leo keeps it shut; both act, and their reserves decide who
outlasts whom), with what an author can do to it and what a reader cannot see:

- **the cast's hidden reserves** (resolve 2 or 4 each): nothing on the page says how long either will hold
  out until one gives up; four casts, the same text until a reserve runs out;
- **the author's moves**, at each round (a choice point), named as authored events: `on` (nothing happens);
  `away` (their mother calls Leo out of the room for AWAY rounds, once); `help` (her grandfather Ben, who
  sits by the window from the first line, gets up and opens the box for her, once she has failed at it).

**Endings are closures**, read off the minds at the end (not authored as targets): how Mara's want closed
(reached by her, met by Ben, given up) and how Leo's did (given up, lost, kept):
  outlast    she outlasts him (he gives up; she opens it)
  outlasted  he outlasts her (she gives up)
  behind     she opens it while he is out (he comes back to find it open: lost)
  help       Ben opens it for her (gratitude; Leo's box lost to Ben)

**The tree of stories**: every cast x every sequence of moves, simulated (world and minds deep-copied at each
choice point). **The reader** holds an open variable over the endings: at each sentence, the stories still
consistent with the text so far (the same beats), weighted by the cast prior (uniform) and the reader's
expectation of authored events (EVENT per available move per round; my choice: a genre prior, the rate at
which a reader expects something to happen to a scene). Its distribution over endings gives the entropy
curve (narrative_entropy_framework.md, multi-endpoint entropy) and its closure.
"""
import copy
import math
from collections import defaultdict

from beats import Beat, effect_parts
from lean import LeanMind
import worlds

AWAY = 3          # rounds Leo is out of the room
EVENT = 0.08      # the reader's expectation that a given authored event happens at a given round
ROUNDS = 80       # a story's longest run, in rounds
RESOLVES = (2.0, 4.0)
ENDINGS = ("outlast", "outlasted", "behind", "help", "unresolved")
SHORT = {"outlast": "win", "outlasted": "lose", "behind": "bhnd", "help": "help", "unresolved": "none"}
MOVES = ("away", "help")   # the author's moves on offer (the ablations take them away)
SIGNS = True               # the reserves show (weariness): False keeps them wholly hidden


class Ben:
    """Her grandfather by the window: when the author moves him, his pushes are made in the world and watched
    (rung 6's helper, an authored actor: he is not a mind)."""
    helps = True

    def __init__(self):
        self.name, self.tries = "Ben", []

    def push(self, world, inv, beats, watch=6):
        from run_ladder import Helper
        Helper.push(self, world, inv, beats, watch)


class State:
    def __init__(self, mara_resolve, leo_resolve, ticks=300):
        self.world = worlds.jack_in_the_box()
        self.beats = []
        leo = LeanMind("Leo", worlds.jack_latch_undone(), want="latch_connecting")
        for _ in range(ticks):   # his past: the time he pushed the latch back (rung 4's keeper)
            leo.tick()
            if leo.done:
                break
        leo.world, leo.beats, leo.keep, leo.resolve = self.world, self.beats, True, leo_resolve
        leo.want.closed, leo.done, leo.last_facts, leo.recent = None, False, None, set()
        leo.terr.wants[effect_parts("latch_connecting", self.world.objs)[0]] = "latch_connecting"
        leo.guards = {"lid_locking"}   # what he keeps: the box shut
        leo.resolve0 = leo_resolve
        self.ben = Ben()
        self.mara = LeanMind("Mara", self.world, want="lid_releasing", beats=self.beats, resolve=mara_resolve,
                             others=[leo, self.ben])
        leo.others = [self.mara, self.ben]
        self.mara.signs = leo.signs = SIGNS
        leo.contesting.add("lid_releasing")
        self.leo = leo
        self.cast = (mara_resolve, leo_resolve)
        self.away = None    # rounds left out of the room
        self.used = set()   # moves made (each at most once)
        self.moves = []     # (round, move)
        self.round = 0

    def over(self):
        return self.mara.done or self.round >= ROUNDS

    def available(self):
        out = ["on"]
        if self.over():
            return out
        if "away" in MOVES and "away" not in self.used and self.away is None and not self.leo.done:
            out.append("away")
        failed = any(not x.effects for x in self.mara.tries if x.inv[1] == "lid")
        if "help" in MOVES and "help" not in self.used and failed:
            out.append("help")
        return out

    def beat(self, kind, actor, **kw):
        self.beats.append(Beat(self.world.t, kind, actor, **kw))

    def apply(self, move):
        if move != "on":
            self.used.add(move)
            self.moves.append((self.round, move))
        if move == "away":
            self.beat("leave", "Leo", detail={"called_by": "mother"})
            self.away = AWAY
        elif move == "help":
            self.beat("rise", "Ben")
            # he unseats the latch if it is seated, then pushes the lid (what he does reads the box as it is)
            for obj in ("latch", "lid"):
                state = self.world.states()[obj]
                if obj == "latch" and state != "connecting":
                    continue
                self.ben.push(self.world, ("hard", obj, state), self.beats)

    def come_back(self):
        self.away = None
        self.beat("return", "Leo")

    def advance(self):
        """One round: Mara's turn, then Leo's (if he is in the room)."""
        self.round += 1
        self.mara.tick()
        if self.mara.done:
            self.finish()
            return
        if self.away is not None:
            self.away -= 1
            self.world.t += 1
            if self.away == 0:
                self.come_back()
            return
        self.leo.tick()

    def finish(self):
        """The want closed: Leo, out, comes back; in the room and still keeping it, he sees what happened."""
        if self.away is not None:
            self.come_back()
        if not self.leo.done:
            self.leo.tick()

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


def prior(move, avail):
    """The reader's expectation of a move at a choice point: each authored event EVENT, nothing the rest."""
    n = len(avail) - 1
    return EVENT if move != "on" else 1.0 - EVENT * n


def grow(state, weight=1.0, leaves=None):
    """Every story from this state: [(weight, final state)]. A state is copied at each choice point that
    offers more than one move; the 'on' branch continues in place."""
    leaves = [] if leaves is None else leaves
    while not state.over():
        avail = state.available()
        for m in avail[1:]:
            other = copy.deepcopy(state)
            other.apply(m)
            other.advance()
            grow(other, weight * prior(m, avail), leaves)
        weight *= prior("on", avail)
        state.advance()
    leaves.append((weight, state))
    return leaves


def forest():
    """All casts (uniform prior) x all move sequences."""
    out = []
    for mr in RESOLVES:
        for lr in RESOLVES:
            for w, s in grow(State(mr, lr)):
                out.append((w / len(RESOLVES) ** 2, s))
    return out


def sig(b):
    """What the reader sees of a beat (its time aside: the text does not say the tick)."""
    return (b.kind, b.actor, b.obj, b.hole, repr(sorted(b.detail.items())))


class Reader:
    """The reader's open variable over endings: a trie of the stories' beat sequences, each node holding the
    weight of every ending among the stories through it."""

    def __init__(self, leaves):
        self.root = {"kids": {}, "dist": defaultdict(float)}
        for w, s in leaves:
            node = self.root
            node["dist"][s.ending()] += w
            for b in s.beats:
                node = node["kids"].setdefault(sig(b), {"kids": {}, "dist": defaultdict(float)})
                node["dist"][s.ending()] += w

    def curve(self, beats):
        """The ending distribution after each beat of a story (normalized), from no beats to all."""
        node, out = self.root, [self.norm(self.root["dist"])]
        for b in beats:
            node = node["kids"][sig(b)]
            out.append(self.norm(node["dist"]))
        return out

    @staticmethod
    def norm(d):
        z = sum(d.values())
        return {k: v / z for k, v in d.items() if v > 0}


def entropy(d):
    return -sum(p * math.log2(p) for p in d.values() if p > 0)


def by_sentence(curve, scene, sentences):
    """The reader's distribution after each sentence: after the furthest beat told so far (the frame is
    the scene as first seen, so it counts as its own beats only)."""
    out, upto = [], 0
    for pi, _, _ in sentences:
        upto = max([upto] + [b + 1 for b in scene.plans[pi].beats])
        out.append(curve[upto])
    return out


def score(dists):
    """The multi-endpoint score: entropy held late. Each sentence's entropy (bits) weighted by how far into the
    story it is (i / N), normalized; and the curve's shape: where the endings fell away, one by one."""
    n = len(dists)
    w = [(i + 1) / n for i in range(n)]
    held = sum(wi * entropy(d) for wi, d in zip(w, dists)) / sum(w)
    viable = [len(d) for d in dists]
    drops = [(i, viable[i - 1] - viable[i]) for i in range(1, n) if viable[i] < viable[i - 1]]
    final = max(dists[-1], key=dists[-1].get)
    # the closing: the last sentence before the ending is certain, and how expected it was there (an ending
    # that was long the reader's favorite is predictable; one that was near zero is a fiat)
    certain = next((i for i, d in enumerate(dists) if d.get(final, 0) > 0.999), n - 1)
    before = dists[max(0, certain - 1)].get(final, 0.0)
    return {"held": round(held, 3), "peak": round(max(entropy(d) for d in dists), 3), "viable": viable,
            "drops": drops, "ending": final, "closed_at": round(certain / n, 2), "expected_before": round(before, 3),
            # foreshadowing: how far the text moved the reader toward the ending it closes on, from the prior
            "rise": round(before - dists[0].get(final, 0.0), 3)}


def told(state):
    """A story told and printed (no reading yet): (scene, sentences)."""
    from printer import Printer
    from story import tell
    people = ("Leo", "Ben") if "help" in MOVES else ("Leo",)   # Ben is in the room only if he can act
    scene = tell(state.beats, set(state.world.objs), "Mara", people=people, rivals=("Leo",))
    sentences = Printer(worlds.LEXICON["jack_open_endings"], "Mara", "she").print_scene(scene)
    return scene, sentences


def search(leaves, reader=None):
    """The author's search over middles: every story in the tree (cast x moves), told, and scored by the
    reader's curve over its sentences. Returns rows sorted best first."""
    reader = reader or Reader(leaves)
    rows = []
    for w, s in leaves:
        if s.ending() == "unresolved":
            continue
        scene, sentences = told(s)
        dists = by_sentence(reader.curve(s.beats), scene, sentences)
        rows.append(dict(score(dists), state=s, scene=scene, sentences=sentences, dists=dists, weight=w))
    for r in rows:   # suspense held late, times the ending earned (surprising, then inevitable): a fiat scores 0
        r["value"] = round(r["held"] * max(r["rise"], 0.0), 3)
    rows.sort(key=lambda r: (-r["value"], -r["held"]))
    return rows


def main():
    import argparse
    import json
    import os
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3, help="stories read back and printed in full")
    ap.add_argument("--event", type=float, default=EVENT)
    args = ap.parse_args()
    globals()["EVENT"] = args.event
    leaves = forest()
    rows = search(leaves)
    print(f"{len(leaves)} stories; {len(rows)} resolved")
    print(f"{'ending':10} {'cast':10} {'moves':28} {'sents':>5} {'value':>6} {'held':>6} {'peak':>5} {'closed':>6} {'exp':>5} {'rise':>5}  drops")
    seen = set()
    for r in rows:
        s = r["state"]
        print(f"{r['ending']:10} {str(s.cast):10} {str(s.moves):28} {len(r['sentences']):5d} {r['value']:6.3f} {r['held']:6.3f} "
              f"{r['peak']:5.2f} {r['closed_at']:6.2f} {r['expected_before']:5.2f} {r['rise']:5.2f}  {r['drops']}")
        if r is rows[min(len(rows) - 1, 15)]:
            break
    best_by = {}
    for r in rows:
        best_by.setdefault(r["ending"], r)
    print()
    print("best per ending:", {e: (r["value"], r["held"], r["rise"], str(r["state"].moves), r["state"].cast)
                               for e, r in best_by.items()})
    from measure import evaluate
    here = os.path.dirname(os.path.abspath(__file__))
    for k, r in enumerate(rows[:args.top]):
        m = evaluate(r["scene"], r["sentences"])
        s = r["state"]
        print()
        print(f"== #{k + 1}: {r['ending']}, cast {s.cast}, moves {s.moves}, value {r['value']}, held {r['held']}, "
              f"rise {r['rise']}, round-trip "
              f"{m['round_trip']:.2f}, judge {m['matched_share']:.2f}, variety {m['variety']:.2f}")
        for (pi, text, _), d, row in zip(r["sentences"], r["dists"], m["rows"]):
            dist = " ".join(f"{SHORT[e]}={p:.2f}" for e, p in sorted(d.items(), key=lambda kv: -kv[1]))
            print(f"  {'ok ' if row['ok'] else 'MISS'} {entropy(d):4.2f}  {text:70.70}  {dist}")
            if not row["ok"]:
                print(f"         intended {row['shape']}; read {row['readings'] or row['why']}")
        with open(os.path.join(here, "results", f"rung7_top{k + 1}.json"), "w", encoding="utf-8") as f:
            json.dump({"ending": r["ending"], "cast": s.cast, "moves": s.moves, "score": {x: r[x] for x in (
                "value", "held", "rise", "peak", "viable", "drops", "closed_at", "expected_before")},
                "sentences": [t for _, t, _ in r["sentences"]], "dists": r["dists"],
                "round_trip": m["round_trip"], "rows": m["rows"]}, f, indent=1, default=str)


if __name__ == "__main__":
    main()
