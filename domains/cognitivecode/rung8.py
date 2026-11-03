"""Rung 8: varying a held way. Rung 7's population, with one capability added to the code's mind.

The known answer: flow 8, `for v4, v5 in enumerate(v2): v3.append((v1[v4], v5))` (temporaries inlined: flows are
counted modulo temporaries, so POC3's extract move is not needed). Its header is offered by wiring (enumerate over the
meta: rung 7 already offered enumerate(v2)); its growth is not: the enumerate seed pairs (item, index-read), and flow 8
needs (index-read, item). Wiring re-chooses names and keeps a way's structure, so no wiring of a known way gives it.

The capability (my choice of trigger, the user's, 2026-10-27): a code that has tried everything it knows, with nothing
left for the patterns to tell, varies a way it holds: the two parts of its pair swapped (POC3's reorder, applied to a
held way rather than to a program). The world offers the variant, wired in scope like any way (StmtWorld.vary). It
comes after asking: courtship first, then the inward variation, the last thing before giving up. Each held growth way
is varied once, in the order the code came to know them.

Flows 0, 2, 3 (a pair wrapped in a list and popped straight back out) are churn POC3's rules let through, not targets.

Run: python -X utf8 rung8.py [--ticks 400]
"""
import argparse
import sys
from collections import Counter

import rung7
import rung6
import stmtworld as S
from beats import Beat  # noqa: E402


class VaryMind(rung7.ComposeMind):
    def choose(self):
        w = self.world
        done = {(x.inv[0], x.inv[1]) for x in self.tries}
        untried = [i for i in w.invitations() if i[1] != self.wanted() and (i[0], i[1]) not in done]
        run = next(i for i in w.invitations() if i[1] == self.wanted())
        told_out = all(p.tell(w.known) is None for p in self.patterns)
        if not untried and told_out and self.stale(run) and w.spec_state != "passing":
            worked = getattr(self, "worked", set())   # ways whose fill was in place when a run passed the spec
            held = [seed for slot, seed in sorted(w.known, key=lambda k: (k[1] not in worked,
                                                                         list(S.SEEDS).index(k[1])))
                    if slot == "growth" and (slot, seed) not in getattr(w, "varied", set())]
            # the ways seen to work first (the trigger, the user's: something of this shape works, no wiring of it
            # passes here); first in the order known, and the codes spent their patience on variants of ways that
            # never worked (the positions way swapped only reverses two index reads)
            if held:   # everything known tried, nothing left to be told: vary a way it holds
                w.vary("growth", held[0])
                self.beat("wonder", obj="growth", detail={"vary": held[0], "move": "swap the pair's parts"})
        return super().choose()

    def act(self, max_watch=12):
        out = super().act(max_watch)
        w = self.world
        st = w.states()
        if self.tries and (st.get("match") in ("taken", "mine") or w.spec_state in ("passing", "taken")):
            # seen to work: a program whose flow reads taken passes the spec ('match' is read only for a passing
            # program), so the way works, run or not (first only runs counted, and a code never runs a program it can
            # see is another's: nothing was ever recorded)
            g = rung7.G.find(w.program, w.growth_path()).node
            text = S.stmt_text(g)   # by text: the fills are rebuilt after every push, so not by identity
            seed = next((lab.split(":")[0].split("~")[0] for lab in w._fills["growth"]
                         if lab.split(":", 1)[1] == text), None)
            if seed:
                self.worked = getattr(self, "worked", set()) | {seed}
        return out


def population(scarce, ticks, patience=12):
    reg = rung6.Registry(scarce)
    patterns = (rung7.Pattern("Growth", "growth"), rung7.Pattern("Header", "header"))
    codes = []
    for header in ("positions", "zip", "enumerate"):
        for recalled in (None, "positions", "accumulate", "enumerate"):
            c = rung7.Code(f"{header[:3]}-{recalled or 'court'}", header, recalled, reg, patterns)
            c.mind.__class__ = VaryMind
            c.mind.patience = patience   # temperament: failed runs before the want is given up
            codes.append(c)
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
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=400)
    args = ap.parse_args()
    rung7.NAMES = rung7.flow_names()
    for scarce, patience in ((True, 12), (True, 24), (False, 12)):
        reg, codes = population(scarce, args.ticks, patience)
        print(f"== scarcity {scarce}, patience {patience}")
        held = Counter()
        for c in codes:
            f = c.holds() if scarce else (c.world.flow() if c.world.spec_state == "passing" else None)
            varied = [b.detail["vary"] for b in c.mind.beats if b.kind == "wonder" and "vary" in b.detail]
            g = S.stmt_text(rung7.G.find(c.world.program, c.world.growth_path()).node)
            if f:
                held[f] += 1
            print(f"  {c.name:16} holds {str(f):9} varied {varied} | "
                  f"{' / '.join(x.strip() for x in c.world.python().splitlines()[3:5])}")
        ours = {f for f in held if f.startswith("flow")}
        print(f"  flows held: {sorted(held)}; of POC3's 12: {len(ours)}; new: {len(held) - len(ours)}; "
              f"flow 8: {'flow08' in held}")


if __name__ == "__main__":
    main()
