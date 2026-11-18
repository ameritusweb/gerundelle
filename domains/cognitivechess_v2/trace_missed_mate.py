"""Why the mind played a stalemating move with a mate in one on the board (game 1 of the full run, its last White move). From the
game-1 checkpoint (nothing run): the position, its mating and stalemating moves; the decision records of the mind's last decisions (the
winning thought, its bonds, the SOV links); what the SOV holds about the mating move and the win effect; the commits; the wants held.
python -X utf8 trace_missed_mate.py checkpoints/rung4p_full_s0_g1.pkl"""
import collections
import sys

import chess

import rung4p

sys.stdout.reconfigure(encoding="utf-8")
a, w, b, s = rung4p.load_run(sys.argv[1])
und = a.mind.understanding
pos = w.__dict__.get("last_game", [])
board, where, label, mover = pos[-1]
cb = chess.Board(board.to_fen())
mates, stales = [], []
for m in cb.legal_moves:
    cb.push(m)
    if cb.is_checkmate():
        mates.append(m.uci())
    elif cb.is_stalemate():
        stales.append(m.uci())
    cb.pop()
print(f"last White position: {board.to_fen()}\n  played {label}; mating moves {mates}; stalemating moves {stales}")
tree = a.mind.__dict__.get("decision_tree", {})
recs = tree.get("records", [])
print(f"\nthe last decisions (decision, thought, bonds, SOV links):")
for t, dec, nodes in recs[-6:]:
    kinds = collections.defaultdict(list)
    for k, n in nodes:
        kinds[k].append(n)
    print(f"  t{t} {dec[:80]}")
    print(f"     thought {kinds.get('thought', [])[:2]}")
    print(f"     bonds {sorted(kinds.get('bond', []))[:8]}")
    print(f"     sov {sorted(kinds.get('sov', []))[:8]}")
for u in mates + [label.split(' ', 1)[1]]:
    cs = [c for c in und.rel if c.split("_push:")[0].endswith(u)][:2]
    for c in cs:
        rels = sorted(f"{r} {o} {tuple(round(x, 2) for x in e[:3])}" for (r, o), e in und.rel[c].items()
                      if "potential" in o or "outcome" in o or "stalemate" in o)
        print(f"\nSOV of {c[:70]}: {len(und.rel[c])} relations; about outcomes/stalemate/potential: {rels[:10]}")
    if not cs:
        print(f"\nno concept of {u} in the SOV")
print("\nprediction SOVs for the win or the stalemate plan:",
      {pid: (sv['effect'], len(sv['instances']), collections.Counter(i.get('outcome') for i in sv['instances']))
       for pid, sv in und.__dict__.get("prediction_sovs", {}).items() if "mate+" in sv["effect"] or "stalemate" in sv["effect"]})
print("territory rows potential_*:", [(r, row.get("holder"), row.get("prediction")) for r, row in a.mind.territory.rows.items()
                                      if r.startswith("potential_") and ("mate" in r or "stalemate" in r)])
print("commits (last 6):", a.__dict__.get("commit_log", [])[-6:])
print("wants: goal", a.goal, "| stack", a.stack, "| last sub-log", a.sub_log[-5:])
