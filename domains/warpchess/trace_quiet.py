"""Rung 1, two moves: why does the mind go quiet? Reads what it holds once it stops pushing. Run: python -X utf8 trace_quiet.py"""
import collections
import sys

from rung0 import Budgeted, WANT  # (puts Gerundelle on the path)
from molecules import is_exp, is_meta, is_own, is_phase, is_sov
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld


def track(i):
    return "meta" if is_meta(i) else "sov" if is_sov(i) else "exp" if is_exp(i) else "own" if is_own(i) else "phase" if is_phase(i) else "thought"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for seed in (1, 2, 3):
        Budgeted.budget = 500
        w = WarpWorld(RUNG1_TWO, seed=seed, moves=2)
        a = Budgeted(w)
        pushes, sources = [], collections.Counter()
        rec = None
        for t in range(1000):
            if a.goal is None:
                a.goal = WANT
            n = len(w.log)
            choice, rec = a.tick()
            if len(w.log) > n:
                pushes.append(t)
                sources["experiment" if rec["experiments"] or a.running else "other"] += 1
        g = a.mind
        print(f"\n===== seed {seed}: {len(pushes)} pushes, last at tick {pushes[-1]}, tick gaps {[pushes[i+1]-pushes[i] for i in range(len(pushes)-1)][-6:]}; sources {dict(sources)}")
        print(f"  now: goal {a.goal}, stack {a.stack}, queue {a.queue}, running {a.running}, watching {bool(a.watching)}, quiet {a.quiet}")
        print(f"  world: moved {w.moved} of {w.moves}, idle {w.idle}, pending {w.pending}; rook where {[(o, s) for o, s in w.where.items() if 'rook' in o]}; on offer {len(w.invitations())}")
        _, invs = a.perceive()
        print(f"  planner now: {a.plan_step(invs)}; experiments this tick {rec['experiments']}; winner(): {a.winner(rec, invs)}")
        print(f"  experiments in the pool {sum(is_exp(i) for i in g.pool)}; questions standing {len(g.understanding.questions)}; experiments done {len(g.inquiry.done)}")
        lv = rec["levels"][-1]
        print(f"  top level by track: {dict(collections.Counter(track(i) for i in lv['winners']))}")
        for i in sorted(lv["winners"], key=lambda i: -lv["bids"].get(i, 0))[:7]:
            print(f"    {lv['bids'].get(i, 0):8.2f} {track(i):7} {i[:74]}")
        offers = list(invs)
        inpool = [c for c in offers if c in g.pool]
        settled = [c for c in offers if g.boxes.get(c, {}).get("settled")]
        print(f"  offers: {len(offers)}; in the pool {len(inpool)}; settled in storage {len(settled)}; warm keys among those {sum(1 for c in settled if any(g.warm(g.boxes[c], k) for k in g.boxes[c]['keys']))}")
        thoughts = [i for i in rec["levels"][0]["winners"] if track(i) == "thought"]
        print(f"  thought slots at level 0, won by: {[i[:40] for i in thoughts][:7]}")
        tried_here = {inv_id(i) for i, _, _ in a.pushed}
        print(f"  pushes known {len(a.known)}, ever tried {len(tried_here)}, known but never tried {len(set(a.known) - tried_here)}")
        conds = [(c, r) for q, (c, r) in g.understanding.questions.items()]
        print(f"  open question kinds: {dict(collections.Counter(r for _, r in conds))}")
        terr = g.territory
        print(f"  territory: live {sorted(terr.live())[:6]}; served {len(terr.served or {})}; pulls {[round(terr.pull(f'own:{k}:{r}'), 1) for k, r in sorted(terr.live())[:6]]}")
        print(f"  the want's region: {g.understanding.owners.get(WANT)}; row {({k: v for k, v in terr.rows.get('material', {}).items() if k in ('holder', 'fails', 'ever', 'other')})}")


if __name__ == "__main__":
    main()
