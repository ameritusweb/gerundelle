"""Where game 5's wants on the mind's own stones' sides come from (trace_opp_games_readheld.log: from slice 1218 the mind held
"black_155_left_free", then "all:black_155_down_pressed&black_155_left_pressed&...", and filled its eyes to the last). Replays seed 0 and,
in the window, prints every want set (any kind), with: how it was set (the tournament from an ownership slot's candidate: own_subwant; a
need of a known way: subwant, and which push's needs held it and what want that way serves; a part of a whole), the stack it serves, the
root want and the slot that offered the root.
Run: PYTHONHASHSEED=0 python -u -X utf8 trace_wants_all.py [from slice, to slice]"""
import sys

import run
import sov_agent

sys.stdout.reconfigure(encoding="utf-8")
LO, HI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1100, 1250)
a, w = run.build(0, 0.7)
mind, terr = a.mind, a.mind.territory
how = {}
needs_seen = []
orig_needs = sov_agent.SovAgent.needs


def needs(self, inv, want):
    out = orig_needs(self, inv, want)
    if self is a:
        needs_seen.append((inv, want, list(out)))
    return out


sov_agent.SovAgent.needs = needs
orig_sub = sov_agent.SovAgent.subwant


def subwant(self, facts, invs=None):
    needs_seen.clear()
    goal = self.goal
    out = orig_sub(self, facts, invs)
    if self is a and isinstance(out, str):
        src = next(((inv, want) for inv, want, ns in needs_seen if out in ns or (out.startswith("all:") and set(out[4:].split("&")) <= set(ns))), None)
        how[out] = ("a part of the whole " + goal[:80]) if goal and goal.startswith("all:") else \
            (f"a need of the way {src[0][0]}:{src[0][1]}:{str(src[0][2])[:40]} toward {str(src[1])[:70]}" if src else "a situation never tried")
    return out


sov_agent.SovAgent.subwant = subwant
orig_own = sov_agent.SovAgent.own_subwant


def own_subwant(self, rec):
    before = self.goal
    orig_own(self, rec)
    if self is a and self.goal != before and self.goal is not None:
        tags = next((m.tags for i, m in [(f"subwant:{self.goal}", None)] if False), None)
        how[self.goal] = "the tournament (own_subwant)"
        how[("tags", self.goal)] = last_tags.get(f"subwant:{self.goal}")


sov_agent.SovAgent.own_subwant = own_subwant
last_tags = {}
read = 0
seen = len(a.sub_log)
for t in range(HI):
    a.mind.potentials = w.potentials()
    last_tags = {i: sorted(x for x in m.tags if "?" in x) for i, m in mind.pool.items() if i.startswith("subwant:")}
    a.tick()
    read, _ = run.give(a, w, read)
    new = a.sub_log[seen:]
    seen = len(a.sub_log)
    if t < LO:
        continue
    for tt, g, k in new:
        if k != "set":
            print(f"slice {t}: want {k}: {g[:90]}")
            continue
        root = a.stack[0] if a.stack else g
        print(f"slice {t}: want SET {g[:110]}")
        print(f"    how: {how.get(g, '?')}; slot tags {how.get(('tags', g))}")
        if g.startswith("opportunity_"):
            r_ = a.owner_of(g)
            row_ = terr.rows.get(r_, {})
            print(f"    region {r_}: holder {row_.get('holder')}, given {r_ in terr.given}, held_states {sorted(row_.get('held_states', ()))}; "
                  f"held doings by kind {terr.__dict__.get('held_doings')}; read_held {terr.__dict__.get('read_held')}")
        print(f"    serves (stack, root first): {[x[:70] for x in a.stack]}; the root: {root[:90]}, set by {how.get(root, 'before the window')}"
              f" {how.get(('tags', root)) or ''}")
