"""Checks the clean code language with no mind (graph.py): on problems made on every shape (chains of 1-4 connections, a join, a loop, a
branch), the correct setting satisfies everything (the user: "there has to be 'something' that satisfies it") and the start isn't it;
the objects a program reads as are the same whatever the wheels (a mind perceives one set of objects per problem); random wheel turns
never crash, every reading is one of its gerund's doings, and a turn forward then back gives the same reading again.
Run: python -X utf8 check_graph.py [problems per shape]"""
import random
import sys

import graph as g

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
SHAPES = {"chain1": lambda: g.chain_shape(1), "chain2": lambda: g.chain_shape(2), "chain4": lambda: g.chain_shape(4),
          "join": g.join_shape, "loop": g.loop_shape, "branch": g.branch_shape}
DOINGS = {"test_": {"passing", "failing"}, "range_": {"passing", "failing"}, "sign_": {"keeping_sign", "going_negative"},
          "divisor_": {"holding", "dividing_by_zero"}, "overflow_": {"contained", "overflowing"}, "lint_": {"quiet", "firing"},
          "clean_": {"empty", "needed", "spare", "unsettled"}, "path_": {"flowing", "blocked"}}
rng = random.Random(1)
problems, seen = [], {}
for name, make_shape in SHAPES.items():
    made = 0
    for k in range(N):
        s = make_shape()
        if name in ("chain2", "join", "loop"):   # (a range check on the middle: rung 2's kind of room)
            s.checks = {len(s.nodes) - 2: None}
        try:
            p = g.make(s, rng, name=f"{name}_{k}")
        except ValueError:
            continue
        made += 1
        if not g.satisfied(p, p.correct):
            problems.append((p.name, "correct setting not satisfying"))
        if p.start == p.correct:
            problems.append((p.name, "starts correct"))
        keys = set(p.reading(p.start))
        pos = list(p.start)
        for step in range(30):
            c = rng.randrange(len(pos))
            d = rng.choice((1, -1))
            before = p.reading(pos)
            pos[c] += d
            r = p.reading(pos)
            if set(r) != keys:
                problems.append((p.name, "objects changed", sorted(set(r) ^ keys)[:4]))
            for o, doing in r.items():
                kinds = [v for pre, v in DOINGS.items() if o.startswith(pre)]
                if kinds and doing not in kinds[0]:
                    problems.append((p.name, "unknown doing", o, doing))
            pos[c] -= d
            if p.reading(pos) != before:
                problems.append((p.name, "forward then back differs", c))
            pos[c] += d
    seen[name] = made
print("problems made per shape:", seen)
print("problems:", len(problems))
for x in problems[:10]:
    print("  ", x)
