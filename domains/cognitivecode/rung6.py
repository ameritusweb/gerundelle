"""Rung 6: a population, and scarcity (distribution, not discovery).

What is tested: scarcity spreads a population over a given space, while the same codes without exclusivity converge on
the options they value most. Not tested here: scarcity producing variety the population itself discovers (rung 7; see
LADDER.md). The space is POC3's: its 52 valid color-line skeletons, 113 complete programs (their readings), 12
load-bearing data flows (poc3/results/skeletons_color_line.pkl, found by POC3's search with its novelty bonus).

Each code is a program of its own (a CodeMind in a PopWorld): it fills its function with one of the 113 programs and
runs it. The exclusive unit is the flow: a flow is held by one code at a time across the population (README: a
possibility is exclusive across the whole population, the user, 2026-10-26). What a code perceives:
- its program's slot (the roles it plays, as in every rung),
- 'match': whether the flow of the program in place is free, its own, or held by another code (seen, as one sees that
  someone is married),
- the spec: passing only if the cases pass and the flow is free or its own; 'taken' otherwise (a failure, credited to
  the fill: the code moves on).
A run on a flow another holds is a contest push: the holder's resolve drains by 1 (rung 4's reserve; my choice of 1
for the pull); at zero the holder resigns, the flow is freed, and the holder's want reopens. A challenger whose runs
keep failing gives up by its patience (temperament.py's trait: failed tries running on the wanted object).

Preferences (my choice): a style is the program's loop kind and how its result grows; a code tries its preferred style
first (the order of its fills: ties go to the preferred). Half the codes prefer the commonest style (positions, append),
the rest one each of the others, so that without scarcity there is something to pile on.

Run: python -X utf8 rung6.py [--codes 20] [--ticks 400]
"""
import argparse
import os
import pickle
import random
import sys
from collections import Counter

from codemind import CodeMind
from codeworld import CodeWorld, ANALOGY
import grammar as G  # noqa: E402

sys.path.insert(0, os.path.join(ANALOGY, "poc3"))
from skeleton import wirings_decomposed  # noqa: E402
from dataflow import signature, inline_temps  # noqa: E402

FUNC = (1, 0)
FACETS = ("ps_lockstep", "ps_pair_output", "ps_position_from_loop", "ps_collect")


def space():
    """POC3's color-line space: [(style, flow id, program)] for every reading of every saved skeleton."""
    d = pickle.load(open(os.path.join(ANALOGY, "poc3", "results", "skeletons_color_line.pkl"), "rb"))
    out = []
    for skel in d.values():
        reads, _ = wirings_decomposed(skel, "color_line")
        for r in reads:
            kinds = {n.kind for n in G.walk(r)}
            loop = next((x for x in sorted(kinds) if x in G.LOOPS), "none").replace("iterating_", "")
            grow = next((x for x in ("appending", "inserting", "accumulating") if x in kinds), "none")
            sig = signature(inline_temps(r))
            fid = repr(sorted(map(repr, sig))) if isinstance(sig, (set, frozenset, list, tuple)) else repr(sig)
            out.append((f"{loop}+{grow}", fid, r))
    flows = {fid: k for k, fid in enumerate(sorted({f for _, f, _ in out}))}
    return [(style, f"flow{flows[fid]:02d}", r) for style, fid, r in out]


class Registry:
    """The possibilities' side: which code holds which flow (None: free). scarce=False: no exclusivity (the
    control): every flow is free to everyone."""

    def __init__(self, scarce=True):
        self.scarce, self.holder, self.codes = scarce, {}, {}
        self.contests, self.resignations = Counter(), []

    def status(self, flow, code):
        h = self.holder.get(flow)
        return "free" if not self.scarce or h is None else "mine" if h == code else "taken"

    def claim(self, flow, code):
        for f, h in list(self.holder.items()):   # a code holds one flow: claiming another lets the first go
            if h == code and f != flow:
                del self.holder[f]
        if self.scarce:
            self.holder[flow] = code

    def contest(self, flow, challenger):
        """A run on a flow another holds: the holder's reserve drains; at zero it gives the flow up."""
        h = self.holder.get(flow)
        if h is None or not self.scarce:
            return
        self.contests[flow] += 1
        holder = self.codes[h]
        holder.reserve -= 1.0
        if holder.reserve <= 0:
            del self.holder[flow]
            self.resignations.append((h, flow, challenger))
            m = holder.mind
            m.beat("feel", hole=f"own:control:{m.wanted()}", obj=m.wanted(),
                   detail={"phase": "resignation", "unexpected": [], "to": challenger})
            # the want given up, as rung 4's (fiction's) resignation: the code stops, and its program no longer passes
            # as its own (first the freed holder still read passing and watched a program it no longer held)
            m.want.closed, m.done, m.keep, holder.resigned = holder.world.t, True, False, True
            holder.world.spec_state = "failing"


class PopWorld(CodeWorld):
    def __init__(self, program, programs, registry, code, order):
        self.registry, self.code, self.flow_of = registry, code, {}
        self._programs, self._order = programs, order
        super().__init__(program, {"body": FUNC}, "color_line", "parallel_strings", FACETS, spec="spec")
        self.objs["match"] = None
        self.spec_state = "failing"

    def _type(self, path):
        return None

    def _complete_fills(self, path):
        """The fills are given: POC3's programs, labelled by style; ordered by the code's preference (ties go to
        the largest label: the preferred style gets the highest ranks), the rest shuffled by the code's seed."""
        prefer, seed = self._order
        rows = list(self._programs)
        random.Random(seed).shuffle(rows)
        rows.sort(key=lambda r: r[0] == prefer)
        out = {}
        for k, (style, flow, prog) in enumerate(rows):
            label = f"{k:03d} {style}#{flow}"
            out[label] = prog.kids[1].kids[0]
            self.flow_of[label] = flow
        return out

    def evaluate(self):
        if G.find(self.program, FUNC).node.kind == "hole":   # no function yet: nothing runs
            return False, {"body": "unreached"}
        return super().evaluate()

    def current_flow(self):
        n = G.find(self.program, FUNC).node
        return next((f for lab, f in self.flow_of.items() if self._fills["body"][lab] is n), None)

    def _read(self):
        out = super()._read()
        flow = self.current_flow()
        out["match"] = self.registry.status(flow, self.code) if flow else "none"
        out[self.spec] = self.spec_state
        return out

    def states(self, tree=None):
        return self._read()   # not cached: another code's claim changes 'match' without this program changing

    def act(self, inv=None, hold=False):
        if inv is not None and inv[1] == self.spec:
            before = self.states()
            flow, passes = self.current_flow(), self.run()
            status = self.registry.status(flow, self.code) if flow else "none"
            if passes and status in ("free", "mine"):
                self.spec_state = "passing"
                self.registry.claim(flow, self.code)
            elif passes and status == "taken":
                self.spec_state = "taken"
                self.registry.contest(flow, self.code)
            else:
                self.spec_state = "failing"
            after = self.states()
            self.diffs = [f"{o}: {before[o]} -> {after[o]}" for o in after if after[o] != before[o]]
            self.t += 1
            return self.diffs
        if inv is not None:
            self.spec_state = "failing"
        return super().act(inv, hold)


class Code:
    def __init__(self, name, prefer, seed, programs, registry, resolve=2.0, patience=8):
        self.name, self.prefer, self.resolve0, self.reserve = name, prefer, resolve, resolve
        self.resigned = False
        self.world = PopWorld(programs[0][2], programs, registry, name, (prefer, seed))
        self.mind = CodeMind(name, self.world, want="spec_passing", patience=patience)
        self.mind.test_pending = True
        registry.codes[name] = self

    def holds(self):
        return next((f for f, h in self.world.registry.holder.items() if h == self.name), None)


def population(n, scarce, programs, ticks=400, seed=0, same=False):
    """same: identical codes (one preference, one order of the fills): any spread then comes from scarcity alone, not
    from each code's own random order among equal fills (which spread the varied population with or without it)."""
    reg = Registry(scarce)
    styles = [s for s, _ in Counter(p[0] for p in programs).most_common()]
    prefs = [styles[0] if same or k % 2 == 0 else styles[1 + (k // 2) % (len(styles) - 1)] for k in range(n)]
    codes = [Code(f"code{k:02d}", prefs[k], seed * 100 + (0 if same else k), programs, reg) for k in range(n)]
    for _ in range(ticks):
        for c in codes:
            m = c.mind
            if c.resigned:
                continue
            if m.want and m.want.closed is not None and not m.done:   # matched: it keeps what it holds
                m.keep, m.want.closed, m.done = True, None, False
            if not m.done:
                m.tick()
    return reg, codes


def report(reg, codes, scarce):
    if scarce:
        held = {c.name: c.holds() for c in codes}
    else:   # no exclusivity: what each code ended with, its spec passing
        held = {c.name: c.world.current_flow() if c.world.spec_state == "passing" else None for c in codes}
    flows = Counter(f for f in held.values() if f)
    gave_up = sum(1 for c in codes if not c.resigned and any(b.kind == "feel" and b.detail.get("phase") ==
                                                              "resignation" for b in c.mind.beats))
    tries = sorted(sum(1 for b in c.mind.beats if b.kind == "try") for c in codes)
    return dict(matched=sum(1 for f in held.values() if f), flows=len(flows), largest=max(flows.values(), default=0),
                contests=sum(reg.contests.values()), holders_resigned=len(reg.resignations), gave_up=gave_up,
                tries=tries[len(tries) // 2])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", type=int, default=20)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    programs = space()
    print(f"space: {len(programs)} programs, {len({f for _, f, _ in programs})} flows, styles "
          f"{dict(Counter(s for s, _, _ in programs).most_common())}")
    print(f"{'codes':9} {'scarcity':9} {'seed':>4} {'matched':>8} {'flows held':>10} {'most on one':>11} "
          f"{'contests':>8} {'holders resigned':>16} {'gave up':>7} {'tries':>5}")
    for same in (False, True):
        for scarce in (True, False):
            for s in range(args.seeds):
                reg, codes = population(args.codes, scarce, programs, args.ticks, s, same)
                r = report(reg, codes, scarce)
                print(f"{'identical' if same else 'varied':9} {str(scarce):9} {s:>4} {r['matched']:>5}/{len(codes):<2} "
                      f"{r['flows']:>10} {r['largest']:>11} {r['contests']:>8} {r['holders_resigned']:>16} "
                      f"{r['gave_up']:>7} {r['tries']:>5}", flush=True)


if __name__ == "__main__":
    main()
