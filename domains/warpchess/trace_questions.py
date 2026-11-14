"""Why the mind never asks the tool "what follows this move?" (rung4p_s0.log: 12 tool calls in 137 slices, all about plans). The tool is
offered only for a question standing in the pool about a concept it can answer (SovAgent.perceive, Params.tool_use). Replays rung 4p's
room game (seed 0, PYTHONHASHSEED=0) and, each slice: the questions standing (und.questions), by what their concept is (a plan; a move
push on offer now; a move push not on offer; a commit; anything else) and by slot; which the tool could answer; the ask pushes on offer;
and, for move pushes, how often one had its SOV attended (sov:<push> in the pool) and what slots it had open.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_questions.py [slices]"""
import collections
import sys

import rung0  # noqa: F401
import rung4p
from gameworld import RandomSide
from plansworld import give
from rung4 import TURN_STEPS
from warpworld import RUNG1_TWO

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
w, a = rung4p.build(0, RUNG1_TWO)
black = RandomSide(w, 0)
und, mind = a.mind.understanding, a.mind
by_kind, by_slot, answerable, asks_offered = collections.Counter(), collections.Counter(), collections.Counter(), 0
sov_push, push_open = collections.Counter(), collections.Counter()
examples = collections.defaultdict(list)
slices = 0


def kind_of(c, offered):
    if c.startswith("plan_"):
        return "plan"
    if c.startswith("commit_push:"):
        return "commit"
    if "_push:" in c:
        return "move push on offer" if c in offered else "move push not on offer"
    return "other"


def look():
    offered = {f"{i[0]}_push:{i[1]}_{i[2]}" for i in w.invitations()}
    for q, (c, r) in und.questions.items():
        if q not in mind.pool:
            continue
        k = kind_of(c, offered)
        by_kind[k] += 1
        by_slot[(k, r)] += 1
        if a.tool.can_answer(c):
            answerable[k] += 1
        if len(examples[k]) < 4:
            examples[k].append(q[:110])
    for i in mind.pool:
        if i.startswith("sov:") and "_push:" in i and not i.startswith("sov:commit_push"):
            sov_push["attended"] += 1
    for c in offered:
        for r in und.open_slots(c):
            push_open[r] += 1


while slices < N:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            a.tick()
            give(a, w)
            look()
            asks_offered += sum(1 for i in a.mind.inquiry.actions if i.startswith("ask_push:")) if a.mind.inquiry else 0
            slices += 1
            if len([x for x in w.log if x[2]]) > n or slices >= N:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        a.tick()
        give(a, w)
        look()
        slices += 1
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
print(f"{N} slices: question-slices standing in the pool, by what they're about: {dict(by_kind)}")
print("by kind and slot:", sorted(by_slot.items(), key=lambda x: -x[1])[:12])
print("ones the tool could answer:", dict(answerable), "| ask pushes on offer (slice-pushes):", asks_offered)
print("move pushes' SOVs attended (slice-count):", dict(sov_push), "| open slots of the move pushes on offer (slice-pushes):", dict(push_open))
for k, xs in examples.items():
    print(f"  e.g. {k}: {xs}")
print("tool calls:", [(t, c[:60]) for t, c, *_ in a.__dict__.get("tool_log", [])][:12])
