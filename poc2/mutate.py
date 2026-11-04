"""Seeded mutation search (PoC step 3, rebuilt): find distinct correct programs by
editing correct ones.

The search moves through complete programs (the STOKE setting): start from a seed,
propose an edit, refill any hole it opens (search.Filler, depth-first with backtracking),
and score the result.

Edits:
- replace: a value becomes a hole of its type, or an operation an operation hole, and is
  refilled; the parts of what was removed are offered to the refill first, so a changed
  operation can keep its inputs (appending(x, p) can become x += [p]);
- rewrite: an operation is replaced by another built only from its inputs (and
  wrapping or pairing them), chosen among all such rewrites (search.Filler.rewrites);
- insert: a new operation hole at a random place in a block, refilled;
- delete: an operation is removed (its block keeps at least one);
- reorder: two operations of a block swap places.

Score: 0 if the program isn't well-typed; 1 if it's correct (every rule, every spec case,
and the gate's minimality checks); otherwise half the share of rules passed plus half the
share of spec cases passed (specs.spec_score). The behavior half gives the walk a
direction across programs that break rules: before it, the score was nearly flat away
from correct programs, and programs two coordinated changes away were never reached
(ASSUMPTIONS.md X15). Acceptance is Metropolis on the score. Novelty (load-bearing data-flow signature distance to the K
nearest kept programs) doesn't enter acceptance, where it froze the walk on valid
programs (ASSUMPTIONS.md X4); it steers restarts instead. After RESTART steps without
the chain improving, the walk jumps to a kept program, niche first (loop kinds,
operations per function, nesting), then weighted by novelty.

Seeds are the domain's reference plus its hand-written alternatives.

Usage: J:\\python310\\python.exe poc2/mutate.py --domain color_line --steps 10000 [--seed 0]
  -> poc2/results/mutate_<domain>.txt
"""
import argparse, difflib, math, os, random, time
from collections import Counter

from dataflow import distance, judge_complete, signature
from grammar import EXPR_KINDS, GROUPS, LOOPS, Node, T, check, hole, infer, replace, visit, walk
from references import seeds as domain_seeds
from rulesets import DOMAINS
from search import Filler, canonical
from specs import admit, spec_score

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = 3000
TEMP = 0.05
RESTART = 200   # restart after this many steps without the chain improving
NOVELTY = 1.0   # restart weight: 1 + NOVELTY x novelty (0 turns the steering off)
K = 3
WRONG = 0.95
MOVES = ("replace", "rewrite", "insert", "delete", "reorder")


def sites(tree):
    """Places an edit can touch, in function bodies: (kind, visit entry)."""
    out = []
    for v in visit(tree):
        if not v.path or v.path[0] != 1:
            continue
        if v.expect == "stmt":
            out.append(("op", v))
        elif isinstance(v.expect, T) or v.expect in GROUPS:
            if infer(v.node, v.scope) is not None:
                out.append(("value", v))
        if v.node.kind == "block":
            out.append(("block", v))
    return out


def niche(tree):
    """A structural descriptor: (loop kinds, operations per function, deepest nesting)."""
    loops = sorted({n.kind.replace("iterating_", "").replace("repeating_", "") for n in walk(tree) if n.kind in LOOPS})

    def depth(n):
        return (n.kind == "block") + max((depth(c) for c in n.kids), default=0)
    fs = tree.kids[1].kids
    return ("+".join(loops) or "none", tuple(len(f.kids[1].kids) for f in fs), max(depth(f.kids[1]) for f in fs))


def set_kids(tree, path, kids):
    node = next(v.node for v in visit(tree) if v.path == path)
    return replace(tree, path, Node(node.kind, kids, node.value, node.type))


def parts(n, include_self=False):
    """The value subtrees inside n, offered for reuse when n is replaced."""
    return [x for x in walk(n) if x.kind in EXPR_KINDS and (include_self or x is not n)]


def propose(tree, rng):
    """(move, edited tree with holes or None if the move doesn't apply, parts to reuse)."""
    move = rng.choice(MOVES)
    all_sites = sites(tree)
    if move == "rewrite":
        kind, v = rng.choice([s for s in all_sites if s[0] == "op"])
        return move, (replace(tree, v.path, hole("stmt")), v.path), parts(v.node, include_self=False)
    if move == "replace":
        kind, v = rng.choice([s for s in all_sites if s[0] in ("op", "value")])
        h = hole("stmt") if kind == "op" else hole("expr", infer(v.node, v.scope))
        return move, replace(tree, v.path, h), parts(v.node)
    blocks = [v for kind, v in all_sites if kind == "block"]
    b = rng.choice(blocks)
    kids = list(b.node.kids)
    if move == "insert":
        i = rng.randrange(len(kids) + 1)
        return move, set_kids(tree, b.path, kids[:i] + [hole("stmt")] + kids[i:]), []
    if len(kids) < 2:
        return move, None, []
    if move == "delete":
        i = rng.randrange(len(kids))
        return move, set_kids(tree, b.path, kids[:i] + kids[i + 1:]), []
    i, j = rng.sample(range(len(kids)), 2)
    kids[i], kids[j] = kids[j], kids[i]
    return move, set_kids(tree, b.path, kids), []


class Walk:
    def __init__(self, domain, seeds, seed=0, novelty_weight=NOVELTY, uniform_restarts=False):
        self.domain = domain
        self.filler = Filler(domain, seed)
        self.rules = self.filler.rules
        self.rng = random.Random(seed)
        self.seed_texts = [canonical(s) for s in seeds]
        self.valid = {t: s for t, s in zip(self.seed_texts, seeds)}
        self.sigs = {t: signature(s) for t, s in self.valid.items()}
        self.novelty_weight = novelty_weight
        self.uniform_restarts = uniform_restarts
        self.judged, self.behavior = {}, {}
        self.wrong_examples = []
        self.found_at = {}
        self.stats = Counter()

    def score(self, prog):
        """(score, canonical text). A correct program (every rule, the spec and the gate's
        minimality checks) scores 1. Otherwise the score is graded: half the share of rules
        passed, half the share of the spec's cases passed, so a half-built program on the
        way to a correct one beats junk (ASSUMPTIONS.md X15). Every well-typed program can
        run in the interpreter, even one that breaks rules. A program that passes every rule
        and every case but has a part that doesn't matter scores WRONG."""
        if check(prog):
            self.stats["type_error"] += 1
            return 0.0, None
        text = canonical(prog)
        if text not in self.judged:
            res = judge_complete(self.rules, prog)
            self.judged[text] = (sum(v is True for v in res.values()) / len(res), spec_score(self.domain, prog))
        rules_share, cases_share = self.judged[text]
        if rules_share == 1.0 and cases_share == 1.0:
            self.stats["structurally_valid"] += 1
            return (1.0 if self.gate(text, prog) else WRONG), text
        return 0.5 * rules_share + 0.5 * cases_share, text

    def gate(self, text, prog):
        if text not in self.behavior:
            ok, why = admit(self.domain, prog)
            self.behavior[text] = ok
            if not ok:
                self.stats["wrong_behavior"] += 1
                if len(self.wrong_examples) < 5:
                    self.wrong_examples.append((text, why))
        return self.behavior[text]

    def novelty(self, text):
        others = sorted(distance(self.sigs[text], s) for t, s in self.sigs.items() if t != text)
        return sum(others[:K]) / len(others[:K]) if others else 1.0

    def distance(self, text):
        return 1 - max(difflib.SequenceMatcher(None, text, s).ratio() for s in self.seed_texts)

    def restart(self):
        """A kept program: niche first, then weighted by novelty (or uniformly)."""
        if self.uniform_restarts:
            return self.rng.choice(list(self.valid.values()))
        niches = {}
        for t, p in self.valid.items():
            niches.setdefault(niche(p), []).append(t)
        group = niches[self.rng.choice(sorted(niches))]
        weights = [1.0 + self.novelty_weight * self.novelty(t) for t in group]
        return self.valid[self.rng.choices(group, weights)[0]]

    def run(self, steps=STEPS):
        t0 = time.perf_counter()
        cur, cur_score = self.restart(), 1.0
        best, stalled = 0.0, 0
        for step in range(1, steps + 1):
            # Restart only when the chain stops improving, so a rising chain can run long
            # (fixed restarts every 50 steps kept the walk near what it already had).
            stalled += 1
            if stalled >= RESTART:
                cur, cur_score = self.restart(), 1.0
                best, stalled = 0.0, 0
                self.stats["restarts"] += 1
            move, edited, reuse = propose(cur, self.rng)
            self.stats[f"proposed_{move}"] += 1
            if edited is None:
                continue
            if move == "rewrite":
                punched, path = edited
                options_ = self.filler.rewrites(punched, path, reuse)
                new = self.rng.choice(options_) if options_ else None
            elif move in ("replace", "insert"):
                new = self.filler.rollout(edited, reuse)
            else:
                new = edited
            if new is None:
                self.stats["refill_failed"] += 1
                continue
            new_score, text = self.score(new)
            if new_score == 1.0 and text not in self.valid:
                self.valid[text] = new
                self.sigs[text] = signature(new)
                self.found_at[text] = step
                self.stats[f"new_from_{move}"] += 1
            if new_score >= cur_score or self.rng.random() < math.exp((new_score - cur_score) / TEMP):
                self.stats["accepted"] += 1
                if new_score < 1.0:
                    self.stats["accepted_invalid"] += 1
                cur, cur_score = new, new_score
                if new_score > best or (new_score == 1.0 and text in self.found_at and self.found_at[text] == step):
                    best, stalled = new_score, 0
        self.stats["seconds"] = round(time.perf_counter() - t0, 1)
        return self


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="color_line", choices=list(DOMAINS))
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--novelty", type=float, default=NOVELTY, help="restart weight on novelty; 0 turns it off")
    args = ap.parse_args()

    seeds = domain_seeds(args.domain)
    w = Walk(args.domain, seeds, args.seed, args.novelty).run(args.steps)
    new = [t for t in w.valid if t not in w.seed_texts]
    dists = sorted(w.distance(t) for t in new)
    q = (lambda p: dists[int(p * (len(dists) - 1))]) if dists else (lambda p: float("nan"))
    seed_sigs = {w.sigs[t] for t in w.seed_texts}
    new_sigs = {w.sigs[t] for t in new} - seed_sigs
    loops = Counter(niche(w.valid[t])[0] for t in new)
    # Variety: distinct canonical texts are an upper bound (operations in another order count
    # separately even when nothing changes); distinct load-bearing data flows, which include
    # order, are the number to trust (ASSUMPTIONS.md X7).
    summary = (f"{args.domain}: {len(new)} new correct programs (canonical texts, an upper bound) from {len(seeds)} "
               f"seed(s) in {args.steps} steps "
               f"({w.stats['seconds']}s). Distance from seed (stand-in, 0-1): median {q(0.5):.2f}, max {q(1.0):.2f}.\n"
               f"Loops among new programs: {dict(loops)}; {len(new_sigs)} new load-bearing data flows "
               f"(seeds have {len(seed_sigs)})\nStats {dict(w.stats)}")
    print(summary)
    by_dist = sorted(new, key=w.distance)
    lines = [summary, ""] + [f"# distance {w.distance(t):.2f}, found at step {w.found_at[t]}\n{t}" for t in by_dist]
    lines += ["", "# Structurally valid but rejected by the semantic gate, first few:"]
    lines += [f"# {why}\n{t}" for t, why in w.wrong_examples]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"mutate_{args.domain}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
