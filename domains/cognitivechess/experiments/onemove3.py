"""Stress-test trace: why games still end after one move with the imagination lane on (seed 1, winner_acts, lane).

Every Black tick at its turn is recorded by game; the report covers games that ended after one half-move: the path the
tick took, Black's want and planner, what won its top level (by kind), whether a move on offer won a thought slot, and
the best bid among moves on offer against the bid needed for a thought slot at level 0.

Run: PYTHONHASHSEED=0 python -X utf8 experiments/onemove3.py [--seed 1] [--steps 4000]
"""
import argparse, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "fiction"))
import chess  # noqa: E402
from rung3 import make, play  # noqa: E402
from force_world import inv_id  # noqa: E402
from molecules import is_meta, is_sov, is_exp, is_own, is_phase  # noqa: E402


def kind(i):
    if i.startswith("own:"): return "ownership"
    if is_phase(i): return "phase"
    if is_meta(i): return "meta"
    if is_sov(i): return "SOV / question"
    if is_exp(i): return "experiment"
    if "_push:" in i: return "push"
    return "percept / fact"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--steps", type=int, default=4000)
    a = ap.parse_args()
    w, minds = make(a.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN, half_moves=120)
    for x in minds:
        x.agent.mind.p.winner_acts = True
        x.agent.mind.p.imagined_lane = True
    B = minds[1].agent; m = B.mind
    st = dict(game=1, half=0); ended = {}; ticks = defaultdict(list); flag = {}
    reset, act = w.reset, w.act

    def counted():
        ended[st["game"]] = st["half"]; st["game"] += 1; st["half"] = 0; reset()
    w.reset = counted

    def logged(inv=None, hold=False):
        if inv is not None and inv[0] != "pass" and w.playable(inv):
            st["half"] += 1
        return act(inv, hold)
    w.act = logged
    fore = B.foreseen

    def traced_fore(steps, invs):
        out = fore(steps, invs); flag["foreseen"] = out is not None; return out
    B.foreseen = traced_fore
    planned = B.planned

    def traced_plan(invs):
        flag["plan"] = planned(invs); return flag["plan"]
    B.planned = traced_plan
    tick = B.tick

    def ticked(force=None):
        flag.clear()
        mine = w.actor == "Black" and w.board.turn == chess.BLACK
        offered = {inv_id(i) for i in w.invitations()} if mine else set()
        goal = B.goal
        choice, rec = tick(force)
        if not mine:
            return choice, rec
        exps = rec.get("experiments") or []
        if choice is not None: path = "moved"
        elif B.watching: path = "watching its last move"
        elif flag.get("foreseen"): path = "experiment foreseen"
        elif exps:
            steps = m.inquiry.plans[exps[0]][2]
            path = "waiting experiment" if not steps or steps[0] == "wait" else "experiment, no move"
        else:
            path = "no experiment; no playable winner"
        top = rec["levels"][-1]["winners"]
        lv0 = rec["levels"][0]
        base = sorted((b for i, b in lv0["bids"].items() if not (is_meta(i) or is_sov(i) or is_exp(i) or is_own(i))
                       and i not in m.imagined(lv0["bids"])), reverse=True)
        k = m.p.slots[0]
        cut = base[k - 1] if len(base) >= k else 0.0
        best = max((b for i, b in lv0["bids"].items() if i.split("|")[0] in offered), default=None)
        ticks[st["game"]].append(dict(path=path, want=goal is not None, planned=flag.get("plan") is not None,
                                      top=Counter(kind(i) for i in top),
                                      offered_top=any(i.split("|")[0] in offered for i in top),
                                      best=best, cut=cut, n_offered=len(offered),
                                      offered_in_pool=sum(1 for i in m.pool if i.split("|")[0] in offered)))
        return choice, rec
    B.tick = ticked
    play(w, minds, a.steps // 2, "turns")
    w.close()
    one = [g for g, h in ended.items() if h <= 1]
    rows = [r for g in one for r in ticks[g]]
    print(f"games {len(ended)}; one-move games {len(one)}: {one}")
    print(f"Black's ticks at its turn in them: {len(rows)}")
    print("  path:", dict(Counter(r['path'] for r in rows).most_common()))
    print("  want active:", dict(Counter(r['want'] for r in rows)), "| planner found a way:", dict(Counter(r['planned'] for r in rows)))
    print("  a move on offer at the top level:", dict(Counter(r['offered_top'] for r in rows)))
    tk = Counter()
    for r in rows: tk.update(r["top"])
    print("  top level, by kind:", dict(tk.most_common()))
    print("  moves on offer:", Counter(r['n_offered'] for r in rows).most_common(3), "| of them in the pool:", Counter(r['offered_in_pool'] for r in rows).most_common(3))
    print("  level 0, best bid on offer >= the thought-slot cut:", dict(Counter((r['best'] is not None and r['best'] >= r['cut']) for r in rows)))
    ex = [r for r in rows if r['best'] is not None][:4]
    for r in ex: print(f"    e.g. best on offer {r['best']:.2f}, cut {r['cut']:.2f}")


if __name__ == "__main__":
    main()
