"""Why no two-move line is committed to (rung4p_lines_s0.log: 9 plan questions answered, lines stood, 0 line commits). Follows each line
from the tool's answer to the tournament: per slice of the mind's, after each tool answer, the lines standing in the tool (MindTool
.predicted, two pushes), those in the mind's predicted sequences (SovAgent.sequence_predicted), the line commits on offer (commit pushes
naming two pushes), their bids at the top level against the best move's, and whether one won; also, when lines stood but none was in the
sequences, whether the line's first push was on offer under the same name.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_line_commits.py [slices]"""
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
slices = 0
steps = lambda c: c.count("_push:") - 1


def look(t):
    tool_lines = [item for k, item in a.tool.predicted if len(item[4]) == 2]
    seq_lines = [x for x in a.__dict__.get("sequence_predicted", []) if len(x[4]) == 2]
    offers = [i for i in (a.mind.inquiry.actions if a.mind.inquiry else ()) if i.startswith("commit_push:") and steps(i) == 2]
    rec = a.last_rec
    lv = rec["levels"][-1] if rec and rec.get("levels") else {"bids": {}, "winners": []}
    line_bids = sorted((round(v, 2) for i, v in lv["bids"].items() if i.split("|")[0] in offers), reverse=True)[:3]
    move_bids = sorted((round(v, 2) for i, v in lv["bids"].items() if "_push:" in i and not i.startswith(("commit", "ask"))), reverse=True)[:3]
    won = [i[:90] for i in lv["winners"] if i.split("|")[0] in offers]
    if offers and rec:   # where the line commits stand: their best bid at each level, and the pool's molecule for one
        per_level = [(L, round(max((v for i, v in l_["bids"].items() if i.split("|")[0] in offers), default=-1), 2), len(l_["bids"]))
                     for L, l_ in enumerate(rec.get("levels", []))]
        mol = a.mind.pool.get(offers[0])
        print(f"    line commits by level (level, best bid or -1 if absent, competitors): {per_level}; in the pool: {mol is not None}"
              f"{'' if mol is None else f', act {mol.act:.2f}, tags {sorted(mol.tags)[:4]}'}; one-move commits bid "
              f"{sorted((round(v, 2) for i, v in lv['bids'].items() if i.startswith('commit_push:') and steps(i.split('|')[0]) == 1), reverse=True)[:2]}")
    if tool_lines or seq_lines or offers:
        offered = {f"{i[0]}_push:{i[1]}_{i[2]}" for i in w.invitations()}
        first_on_offer = sum(1 for item in tool_lines if item[4][0] in offered)
        print(f"slice {t}: lines in the tool {len(tool_lines)} (first push on offer under its name: {first_on_offer}); in the mind's "
              f"sequences {len(seq_lines)}; line commits on offer {len(offers)}; their top bids {line_bids} vs moves {move_bids}; won {won}",
              flush=True)
        if tool_lines and not first_on_offer:
            print("    e.g. tool line", tool_lines[0][4], "| offered e.g.", sorted(offered)[:2])


while slices < N:
    if w.board.turn == 1 and not w.over():
        w.actor = "White"
        n = len([x for x in w.log if x[2]])
        for _ in range(TURN_STEPS):
            a.tick()
            give(a, w)
            slices += 1
            look(slices)
            if len([x for x in w.log if x[2]]) > n or slices >= N:
                break
    elif not w.over():
        black.tick()
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
        look(slices)
    else:
        w.actor = "White"
        a.tick()
        give(a, w)
        slices += 1
print("tool calls:", [(t, c[:50], s) for t, c, _, s in a.__dict__.get("tool_log", [])])
print("commits:", [(x[0], x[2], steps(x[1])) for x in a.__dict__.get("commit_log", [])])
