"""Rung 7: composition at statement level, from POC3's four seeds alone (statement slots; courtship and recall).

The known ceiling (stated before running): the four seeds and their wirings reach 5 of POC3's 12 color-line flows
(flows 1, 4, 5, 6, 7). Inserting is in no seed (flows 9-11); four flows are variants within a seed's style (0, 2, 3,
8) that passing a way on as it is cannot reach. New combinations of the seeds' styles (enumerate with accumulate) are
not among POC3's 12 at all; if they pass they are counted apart, as new.

What counts as composition (the user, 2026-10-27): not being handed a seed. No seed program is a fill. Each code starts
from a partial program, its header from one seed and its growth open (stmtworld.StmtWorld), and knows only its header's
way. Ways arrive by courtship (it asks the growth pattern, which tells the ways it holds from the seeds, one per ask) or
by recall (it starts with a growth way remembered from a past scene). A flow is reached by composition when the code
holds it with a header and a growth from different seeds' ways.

Asking (my choice, the courtship of rung 1 at statement level): a code with nothing untried that it knows, its last
run failed, asks the growth pattern for a way it does not know; with none left, the header pattern.

Scarcity as rung 6: a flow is held by one code at a time; 'match' perceived; a run on a held flow is a contest.

Run: python -X utf8 rung7.py [--ticks 300] [--show]
"""
import argparse
import sys
from collections import Counter

from codemind import CodeMind, said  # noqa: F401  (puts poc2 and fiction on the path)
from beats import Beat  # noqa: E402
import grammar as G  # noqa: E402
import rung6
import stmtworld as S
from dataflow import signature, inline_temps  # noqa: E402
sys.path.insert(0, __import__("os").path.join(rung6.ANALOGY, "poc3"))


def flow_names():
    """POC3's flow ids by name (rung 6's space), to say which flow a composed program is."""
    import pickle, os
    from skeleton import wirings_decomposed
    d = pickle.load(open(os.path.join(S.R.__file__.rsplit("poc2", 1)[0], "poc3", "results",
                                      "skeletons_color_line.pkl"), "rb"))
    fids = sorted({fid(r) for skel in d.values() for r in wirings_decomposed(skel, "color_line")[0]})
    return {f: f"flow{k:02d}" for k, f in enumerate(fids)}


def fid(program):
    s = signature(inline_temps(program))
    return repr(sorted(map(repr, s)))


NAMES = None


class ComposeWorld(S.StmtWorld):
    """A statement world with rung 6's scarcity: 'match' and a spec that reads 'taken' on a flow another holds."""

    def __init__(self, header_seed, registry, code, known=()):
        super().__init__(header_seed, known=known, registry=registry, code=code)
        self.objs["match"] = None
        self.spec_state = "failing"

    def flow(self):
        if any(n.kind == "hole" for n in G.walk(self.program.kids[1])):
            return None
        f = fid(self.program)
        return NAMES.get(f, "new:" + str(abs(hash(f)) % 1000))

    def _read(self):
        out = super()._read()
        f = self.flow() if self.run() else None
        out["match"] = self.registry.status(f, self.code) if f else "none"
        out[self.spec] = self.spec_state
        return out

    def states(self, tree=None):
        return self._read()

    def act(self, inv=None, hold=False):
        if inv is not None and inv[1] == self.spec:
            before = self.states()
            passes = self.run()
            f = self.flow() if passes else None
            status = self.registry.status(f, self.code) if f else "none"
            if passes and status in ("free", "mine"):
                self.spec_state = "passing"
                self.registry.claim(f, self.code)
            elif passes:
                self.spec_state = "taken"
                self.registry.contest(f, self.code)
            else:
                self.spec_state = "failing"
            after = self.states()
            self.diffs = [f"{o}: {before[o]} -> {after[o]}" for o in after if after[o] != before[o]]
            self.t += 1
            return self.diffs
        if inv is not None:
            self.spec_state = "failing"
        return super().act(inv, hold)


class Pattern:
    """A pattern agent for one slot: the ways it holds from the seeds it has been followed in, told one per ask, in
    the order it lived them (POC3's seeds' order)."""

    def __init__(self, name, slot):
        self.name, self.slot, self.seeds = name, slot, list(S.SEEDS)

    def tell(self, known):
        return next((s for s in self.seeds if (self.slot, s) not in known), None)


class ComposeMind(CodeMind):
    patterns = ()

    def choose(self):
        w = self.world
        done = {(x.inv[0], x.inv[1]) for x in self.tries}   # a fill tried is tried whatever its slot read then
        untried = [i for i in w.invitations() if i[1] != self.wanted() and (i[0], i[1]) not in done]
        # (first by the whole push, its slot's state included: changing the header changed that state, every fill
        # looked untried again, and the zip codes never asked)
        run = next(i for i in w.invitations() if i[1] == self.wanted())
        if not untried and self.stale(run) and w.spec_state != "passing":
            for p in self.patterns:   # nothing known left to try: ask for a way
                seed = p.tell(w.known)
                if seed is not None:
                    ab = self.beat("ask", obj=p.slot, detail={"to": p.name, "slot": "way"})
                    w.learn_way(p.slot, seed)
                    self.beats.append(Beat(w.t, "tell", p.name, obj=p.slot, detail={"to": self.name, "way": seed},
                                           prov="told", refs=(ab,)))
                    break
        untried = [i for i in w.invitations() if i[1] != self.wanted() and (i[0], i[1]) not in done]
        if untried and not (self.test_pending and self.tries and self.tries[-1].inv[1] != self.wanted()
                            and not any(w.states().get(s) == "empty" for s in w.slots)
                            and w.states().get("match") != "taken" and not self.stale(run)):
            # a way told or recalled and not yet tried is tried before any fill already tried (LeanMind.plan acts on
            # a told way it has not tested first); first the zip codes, told the zip growth, kept cycling the header's
            # four wirings, each flipping several roles and so valued as more work than an untried growth
            return max(untried, key=lambda i: (round(self.value(i), 9), i))
        return super().choose()


class Code:
    def __init__(self, name, header, recalled, registry, patterns):
        self.name, self.resolve0, self.reserve, self.resigned = name, 2.0, 2.0, False
        known = {("growth", recalled)} if recalled else set()
        self.world = ComposeWorld(header, registry, name, known)
        self.mind = ComposeMind(name, self.world, want="spec_passing", patience=12)
        self.mind.test_pending, self.mind.patterns = True, patterns
        self.header, self.recalled = header, recalled
        registry.codes[name] = self

    def holds(self):
        return next((f for f, h in self.world.registry.holder.items() if h == self.name), None)

    def composed(self):
        """(header seed, growth seed) of the program in place."""
        h = next((lab.split(":")[0] for lab, n in self.world._fills["header"].items()
                  if G.find(self.world.program, S.LOOP).node.kind == n.kind), "?")
        g = G.find(self.world.program, self.world.growth_path()).node
        gs = next((lab.split(":")[0] for lab, n in self.world._fills["growth"].items() if n is g), None)
        if gs is None:
            text = S.stmt_text(g)
            gs = next((lab.split(":")[0] for lab in self.world._fills["growth"] if lab.split(":", 1)[1] == text), "?")
        return h, gs


def population(scarce, ticks):
    reg = rung6.Registry(scarce)
    patterns = (Pattern("Growth", "growth"), Pattern("Header", "header"))
    codes = []
    for header in ("positions", "zip", "enumerate"):
        for recalled in (None, "positions", "accumulate", "enumerate"):
            codes.append(Code(f"{header[:3]}-{recalled or 'court'}", header, recalled, reg, patterns))
    for _ in range(ticks):
        for c in codes:
            m = c.mind
            if c.resigned:
                continue
            if m.want and m.want.closed is not None and not m.done:
                m.keep, m.want.closed, m.done = True, None, False
            if not m.done:
                m.tick()
    return reg, codes


def main():
    global NAMES
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=300)
    args = ap.parse_args()
    NAMES = flow_names()
    for scarce in (True, False):
        reg, codes = population(scarce, args.ticks)
        print(f"== scarcity {scarce}")
        held = Counter()
        for c in codes:
            f = c.holds() if scarce else (c.world.flow() if c.world.spec_state == "passing" else None)
            h, g = c.composed()
            asks = sum(1 for b in c.mind.beats if b.kind == "ask")
            tries = sum(1 for b in c.mind.beats if b.kind == "try")
            if f:
                held[f] += 1
            print(f"  {c.name:16} holds {str(f):9} header {h:10} growth {g:10} "
                  f"{'composed' if f and h != g else '':9} asks {asks} tries {tries} "
                  f"{'resigned' if c.resigned else ''}")
            if f:
                print("      " + " / ".join(x.strip() for x in c.world.python().splitlines()[3:5]))
        ours = {f for f in held if f.startswith("flow")}
        print(f"  flows held: {sorted(held)}; of POC3's 12: {len(ours)}; new: {len(held) - len(ours)}")


if __name__ == "__main__":
    main()
