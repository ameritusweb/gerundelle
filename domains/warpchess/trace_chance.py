"""Rung 1b, two moves: at the moments a capture of the knight is on offer, why isn't it taken? Run: python -X utf8 trace_chance.py [seed]"""
import collections
import sys

from rung0 import Budgeted, WANT
from molecules import is_exp, is_meta, is_own, is_phase, is_sov
from sov_agent import inv_id
from warpworld import RUNG1_TWO, WarpWorld


def track(i):
    return "meta" if is_meta(i) else "sov" if is_sov(i) else "exp" if is_exp(i) else "own" if is_own(i) else "phase" if is_phase(i) else "thought"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    Budgeted.budget = 500
    w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = Budgeted(w)
    g = a.mind
    windows, current, shown = [], None, 0
    why_end = collections.Counter()
    for t in range(1000):
        if a.goal is None:
            a.goal = WANT
        target = w.where["black_knight_Rd4"]
        caps = {l: m for l, m in w.offers().items() if w.moved == 1 and target is not None and m.final_square == target}
        ids = {f"{l}_push:{w.ids_at(m.from_square)}_present": l for l, m in caps.items()}
        if caps and current is None:
            current = dict(start=t, ticks=0, events=[])
        state = (list(a.queue), a.running, bool(a.watching))
        moved_before = w.moved
        choice, rec = a.tick()
        if current is not None:
            current["ticks"] += 1
            c = next(iter(ids), None)
            lv0, top = rec["levels"][0], rec["levels"][-1]
            seen = dict(
                t=t, queue=state[0], running=state[1], watching=state[2],
                cap=c and c.split("_push")[0], in_pool=c in g.pool if c else None, settled=bool(g.boxes.get(c, {}).get("settled")) if c else None,
                bid0=round(lv0["bids"].get(c, 0), 2) if c else None, reached=rec["reached"].get(c) if c else None,
                causes_funded=round(g.understanding.funding(c, "causes"), 2) if c else None,
                sov=f"sov:{c}" in g.pool if c else None, question=[q for q, (cc, r) in g.understanding.questions.items() if cc == c][:2] if c else None,
                exps_for_it=[e for e in g.pool if is_exp(e) and c and c in e][:3],
                exps_top=rec["experiments"][:2], thoughts_top=[i[:44] for i in top["winners"] if track(i) == "thought"][:4],
                exps_pool=sum(is_exp(e) for e in g.pool), choice=choice and choice[0],
            )
            current["events"].append(seen)
            if w.moved != moved_before and w.moved == 2:
                why_end["the second move was made"] += 1
            if w.moved != 1:
                windows.append(current)
                if not w.moved:
                    why_end["position set back"] += 1
                current = None
    print(f"seed {seed}: windows with a capture on offer: {len(windows)}; how they ended: {dict(why_end)}; ticks per window: {[x['ticks'] for x in windows][:20]}")
    agg = collections.Counter()
    for x in windows:
        for e in x["events"]:
            agg["in pool" if e["in_pool"] else "settled" if e["settled"] else "not in pool"] += 1
            agg["reached a slot" if e["reached"] is not None else "won no slot"] += 1
            agg["has a sov or question" if (e["sov"] or e["question"]) else "no sov or question"] += 1
            agg["an experiment about it" if e["exps_for_it"] else "no experiment about it"] += 1
            agg["queue busy" if e["queue"] or e["running"] else "queue free"] += 1
    print(f"over every tick a capture was on offer: {dict(agg)}")
    for x in windows[:4]:
        print(f"\nwindow at tick {x['start']}, {x['ticks']} ticks:")
        for e in x["events"]:
            print(f"  t{e['t']}: queue {e['queue'][:1]} running {str(e['running'])[:50]} watching {e['watching']} | capture {e['cap']} in pool {e['in_pool']} settled {e['settled']} bid {e['bid0']} reached {e['reached']} causes {e['causes_funded']} sov {e['sov']} q {e['question']}")
            print(f"        experiments about it {e['exps_for_it']}; top experiments {[s[:60] for s in e['exps_top']]}; top thoughts {e['thoughts_top']}; chose {e['choice']}")


if __name__ == "__main__":
    main()
