"""Stress-test trace: why perceived facts take Black's top thought slots in the one-move games (seed 1, winner_acts,
imagined lane). At each level, the bid of each fact that won a thought slot and of the best move on offer, split into
activation x (1 + binding score), tension, w_pred x forward (expected surprise) and support, with what each binds to; and
the level where the best move on offer drops out.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/facts3.py [--seed 1] [--steps 4000]
"""
import argparse, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
import chess  # noqa: E402
from rung3 import make, play  # noqa: E402
from force_world import inv_id  # noqa: E402
from molecules import is_meta, is_sov, is_exp, is_own, is_phase  # noqa: E402


def thought(i):
    return not (is_meta(i) or is_sov(i) or is_exp(i) or is_own(i) or is_phase(i))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--steps", type=int, default=4000)
    a = ap.parse_args()
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=120)
    for x in minds:
        x.agent.mind.p.winner_acts = True
        x.agent.mind.p.imagined_lane = True
    B = minds[1].agent; m = B.mind
    st = dict(game=1, half=0); ended = {}; rows = defaultdict(list)
    reset, act = w.reset, w.act

    def counted():
        ended[st["game"]] = st["half"]; st["game"] += 1; st["half"] = 0; reset()
    w.reset = counted

    def logged(inv=None, hold=False):
        if inv is not None and inv[0] != "pass" and w.playable(inv):
            st["half"] += 1
        return act(inv, hold)
    w.act = logged
    think = m.think
    cap = {}

    def traced_think():
        rec = think()
        cap["acts"] = {i: mol.act for i, mol in m.pool.items()}   # (after decay: read before, below)
        return rec
    tick = B.tick

    def ticked(force=None):
        mine = w.actor == "Black" and w.board.turn == chess.BLACK and not B.watching
        offered = {inv_id(i) for i in w.invitations()} if mine else set()
        before = {i: mol.act for i, mol in m.pool.items()} if mine else {}
        choice, rec = tick(force)
        if not mine or choice is not None or len(rows[st["game"]]) >= 6:
            return choice, rec
        out = []
        for L, lv in enumerate(rec["levels"]):
            k = m.p.slots[L]
            imag = m.imagined(lv["bids"])
            ranked = sorted((i for i in lv["bids"] if thought(i) and i not in imag), key=lambda i: -lv["bids"][i])
            def parts(i):
                mol = m.pool.get(i); b = lv["res"].get(i); s = lv["scores"].get(i, 0.0)
                a0 = before.get(i, mol.act if mol else 0.0)
                return dict(id=i[:44], bid=round(lv["bids"][i], 2), act=round(a0, 2), bind=round(max(s, 0), 2),
                            partner=(b[1][:30] if b and b[0] == "partner" else b[0] if b else None),
                            tension=round(m.tension(mol, b), 2) if mol and b else None,
                            forward=round(m.p.w_pred * m.forward(i), 2), support=0.0)
            facts = [parts(i) for i in ranked[:k] if "_push:" not in i]
            pushes = [i for i in ranked if i.split("|")[0] in offered]
            best = parts(pushes[0]) if pushes else None
            rank = (ranked.index(pushes[0]) + 1) if pushes else None
            out.append(dict(L=L, k=k, facts=facts, best=best, best_rank=rank))
        rows[st["game"]].append(out)
        return choice, rec
    B.tick = ticked
    play(w, minds, a.steps // 2, "turns")
    w.close()
    one = [g for g, h in ended.items() if h <= 1]
    drop = Counter(); fact_names = Counter(); comps = defaultdict(list)
    for g in one:
        for out in rows[g]:
            last = max((o["L"] for o in out if o["best"] and o["best_rank"] <= o["k"]), default=-1)
            drop[last + 1] += 1
            for o in out:
                for f in o["facts"]:
                    fact_names[(o["L"], f["id"])] += 1
                    comps[("fact", o["L"])].append(f)
                if o["best"]:
                    comps[("move", o["L"])].append(o["best"])
    print(f"one-move games traced: {len(one)}; Black ticks: {sum(len(rows[g]) for g in one)}")
    print("level where the best move on offer loses its thought slot (0 = never wins one):", dict(sorted(drop.items())))
    for L in range(len(m.p.slots)):
        top = [(n, c) for (l, n), c in fact_names.most_common() if l == L][:5]
        print(f"level {L} ({m.p.slots[L]} thought slots): commonest winning facts {top}")
        for who in ("fact", "move"):
            xs = comps[(who, L)]
            if not xs:
                continue
            mean = lambda key: round(sum((x[key] or 0) for x in xs) / len(xs), 2)
            partners = Counter(x["partner"] for x in xs).most_common(2)
            print(f"   {who:4} mean: bid {mean('bid')} = act {mean('act')} x (1 + bind {mean('bind')}) + tension {mean('tension')} "
                  f"+ forward {mean('forward')}; binds to {partners}")


if __name__ == "__main__":
    main()
