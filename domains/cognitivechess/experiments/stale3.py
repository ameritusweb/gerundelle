"""Stress-test trace: why a push the world keeps rejecting keeps being tried (Black, seed 1, winner_acts, pushback).

For every rejected try, the molecule that won (the push or a split half of it), as it stood in the tick that chose it:
its activation, its bid at the top level and the parts of that bid, its surprise and expected-surprise term, its top
wins and half-life, whether it has open sites, the meta molecules about it, and the mind's record of 'no change' for it.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/stale3.py [--seed 1] [--steps 8000]
"""
import argparse, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
import chess  # noqa: E402
from rung3 import make, play  # noqa: E402
from force_world import inv_id  # noqa: E402
from molecules import is_meta  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--steps", type=int, default=8000)
    a = ap.parse_args()
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=120)
    for x in minds:
        x.agent.mind.p.winner_acts = True
    B = minds[1].agent; m = B.mind
    rows = defaultdict(list)
    st = {}
    winner = B.winner

    def traced_winner(rec, invs):
        out = winner(rec, invs)
        st["won"] = None
        if out is not None:
            c = inv_id(out)
            st["won"] = next((x for x in rec["levels"][-1]["winners"] if x.split("|")[0] == c), c)
            st["rec"] = rec
        return out
    B.winner = traced_winner
    tick = B.tick

    def ticked(force=None):
        st["won"] = None
        choice, rec = tick(force)
        if w.actor == "Black" and choice is not None and st.get("won") and w.board.turn == chess.BLACK:
            c = inv_id(choice)
            if c not in {inv_id(i) for i in w.invitations()}:   # tried, and the world pushed back
                x = st["won"]; mol = m.pool.get(x)
                top = rec["levels"][-1]; lv0 = rec["levels"][0]
                b = lv0["res"].get(x); s = lv0["scores"].get(x)
                rows[c].append(dict(
                    winner_id=x[len(c):] or "(the push itself)", act=round(mol.act, 2) if mol else None,
                    bid_top=round(top["bids"].get(x, 0.0), 2), act_x_binding=round(mol.act * (1 + max(s or 0, 0)), 2) if mol else None,
                    tension=round(m.tension(mol, b), 2) if mol and b else None, forward=round(m.p.w_pred * m.forward(x), 3),
                    S=round(m.S.get(x, 0.0), 3), top_wins=m.top_wins.get(x, 0),
                    half_life=round(m.half_life(mol, 0.0), 1) if mol else None, open_sites=list(mol.sites) if mol else None,
                    metas=sorted({i.split(":")[1] for i in m.pool if is_meta(i) and c in i}),
                    no_change=round(m.understanding.rel.get(x, {}).get(("causes", "no_change"), [0, 0, 0])[0]
                                    + m.understanding.rel.get(c, {}).get(("causes", "no_change"), [0, 0, 0])[0], 1),
                    rivals=sorted(((round(top["bids"].get(i, 0), 2), i[:40]) for i in top["winners"] if "_push:" in i and i != x), reverse=True)[:2]))
        return choice, rec
    B.tick = ticked
    play(w, minds, a.steps // 2, "turns")
    w.close()
    worst = sorted(rows, key=lambda c: -len(rows[c]))[:2]
    for c in worst:
        print(f"=== {c}: tried and rejected {len(rows[c])} times")
        for k, r in enumerate(rows[c]):
            if k < 4 or k % 5 == 0 or k == len(rows[c]) - 1:
                print(f"  try {k + 1}: {r}")
    bored = sum(1 for _, d, _ in m.meta.log if d == "op:novelty doubled")
    print(f"Black's 'bored' operations over the run: {bored}; rejected tries in all: {sum(len(v) for v in rows.values())}")


if __name__ == "__main__":
    main()
