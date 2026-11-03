"""Rung 4: regression and loss (fiction's rung 5). Rung 0's scene; the code has found v2[v4], and the spec passes.

Authored events (named as such, as fiction's take and give):
- uses: the program used on new inputs, passing. Each is a claim on the slot that takes, with the fill in place: the
  code analogue of Mara playing with the toy. Held (Territory.held) counts them, so grief's pull, 1 + held, can scale.
- the spec changes: each character is now paired with the rest of the meta-line from its position, (content[i],
  meta[i:]). The new cases are in the spec before anything runs on them.
- a use on the new inputs: the held fill v2[v4] fails. The code sees its want undone by nothing it did.

Two readings of the loss, as configurations (the user, 2026-10-27):
- A, taken: the spec change takes the slot (Territory taken_by, as fiction's take): lost at once, grief at 1 + held.
  No one to be angry at: no taker is a person.
- B, the register: no authoring of the loss. Failures of the held fill lower its holding strength, (took + KAPPA b) /
  (tried + KAPPA); the slot reads contested (doubt: anxiety) while the strength is above the base rate, lost when it
  falls to it.

Then the code, a keeper of the spec passing, searches; v2[v4:] passes the new spec (it is among the 159 fills).

Run: python -X utf8 rung4.py [--show A|B] [--uses N]
"""
import argparse
import sys

from codemind import CodeMind
from lean import Try  # noqa: E402
from beats import Beat  # noqa: E402  (fiction's, on the path codeworld set)
import rung0
import specs  # noqa: E402

SLOT = "second"


def suffix_cases():
    """f1(content, meta) returns (content[i], meta[i:]) per position: the same inputs as specs.color_line_cases."""
    def case(content, meta):
        def run(tree):
            got = specs.Machine(tree).call("f1", content, meta)
            want = [(content[i], meta[i:]) for i in range(len(content))]
            return "" if got == want else f"f1({content!r}, {meta!r}) returned {got!r}, not {want!r}"
        return run
    pairs = [(c, m) for c in specs.strings("ab", 3) for m in specs.strings("ab", 3) if len(m) == len(c)]
    pairs += [("ababa", "babab"), ("aabba", "abbaa"), ("abababa", "bbbaaab"), ("aaaaaa", "bbbbbb")]
    return [case(c, m) for c, m in pairs]


specs.CASES["color_line_suffix"] = suffix_cases()


class Scene:
    def __init__(self, reading, uses, order=0, ticks=1500):
        self.reading, self.uses = reading, uses
        self.w = rung0.world(order=order)
        # no carry_on: with a memory, lean.act leaves a lost slot's sadness to the memory, which forms it only for a
        # thing gone from view (fiction's toy); a slot never leaves view, so its grief never formed
        self.mind = CodeMind("Code", self.w, want="spec_passing")
        for _ in range(ticks):   # the code finds the fill
            self.mind.tick()
            if self.mind.want.closed is not None:
                break
        m = self.mind
        m.keep, m.want.closed, m.done = True, None, False   # from now on it keeps the spec passing
        self.fill = next(x.inv for x in reversed(m.tries) if x.inv[1] == SLOT)

    def event(self, what):
        self.mind.beats.append(Beat(self.w.t, "try", "World", obj="spec", detail={"strength": what, "gerund": ""}))

    def use(self):
        """Authored: the program used on new inputs, passing (or not, if the spec has changed). The fill in place is
        credited: a claim on the slot, tried, that took if the spec passes."""
        m, w = self.mind, self.w
        before = w.states()
        w.passing = w.run()
        self.event("use")
        row = m.terr.row(SLOT)
        c = row["claims"].setdefault(self.fill, [0, 0])
        c[0] += 1
        if w.passing:
            c[1] += 1
            row["fails"] = 0
        else:
            row["fails"] += 1
            if row["ever"]:
                row["failed"] = True
        m.terr.update()
        after = w.states()
        w.diffs = [f"{o}: {before[o]} -> {after[o]}" for o in after if after[o] != before[o]]
        # the use is a run the code sees whole (provenance seen): it can contradict what the code holds about runs
        run = next(i for i in w.invitations() if i[1] == "spec")
        facts = frozenset(f"{d}_{g}" for d, g in before.items())
        x = Try(w.t, run, facts, tuple(f"spec_{after['spec']}" for _ in [0] if after["spec"] != before["spec"]),
                frozenset(f"{d}_{g}" for d, g in after.items()))
        m.observed.append(x)
        m.contradicts(x)
        w.t += 1

    def regress(self):
        """Authored: the spec changes (its new cases in place first), then a use on the new inputs."""
        self.w.domain = "color_line_suffix"
        self.event("the spec changes")
        if self.reading == "A":   # the change takes the slot: lost at once (no person took it)
            self.mind.terr.row(SLOT)["taken_by"] = "spec"
            self.mind.terr.update()
        self.use()

    def run(self, ticks=1500):
        m = self.mind
        for _ in range(self.uses):
            self.use()
            m.tick()
        self.t_regress, self.n_beats = self.w.t, len(m.beats)
        self.regress()
        for _ in range(ticks):
            m.tick()
            if self.w.passing and self.w.domain == "color_line_suffix" and self.w.states()["spec"] == "passing":
                for _ in range(2):
                    m.tick()
                break
        return self

    def measure(self):
        after = self.mind.beats[self.n_beats:]
        feels = [b for b in after if b.kind == "feel" and b.actor == "Code"]
        grief = next((b for b in feels if b.detail.get("phase") == "sadness" and b.obj == SLOT), None)
        doubt = next((b for b in feels if b.detail.get("phase") in ("anxiety", "frustration") and b.obj == SLOT), None)
        tries = [b for b in after if b.kind == "try" and b.actor == "Code"]
        return dict(held=self.mind.terr.held(SLOT) if False else None,
                    grief_pull=round(grief.pull, 2) if grief else None,
                    grief_at=grief.t - self.t_regress if grief else None,
                    doubt=(doubt.detail["phase"], doubt.t - self.t_regress) if doubt else None,
                    recovered=self.w.states()["spec"] == "passing" and self.w.domain == "color_line_suffix",
                    tries=len(tries), program=self.w.python())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", choices=("A", "B"))
    ap.add_argument("--uses", type=int, default=3)
    args = ap.parse_args()
    if args.show:
        s = Scene(args.show, args.uses).run()
        for b in s.mind.beats[s.n_beats - 2 * args.uses - 2:]:
            if b.kind in ("try", "feel", "learn", "reach", "surprise") or (b.kind == "change" and b.obj in (SLOT, "spec")):
                print(f"  t{b.t:<4} {b.actor:5} {b.kind:8} {b.obj:24} pull {b.pull:<5.2f} "
                      f"{ {k: v for k, v in b.detail.items() if k in ('strength', 'to', 'phase')} }")
        print(s.measure()["program"])
        return
    print(f"{'reading':8} {'uses':>4} {'held':>4}  {'grief pull':>10} {'grief at':>8}  {'doubt first':16} "
          f"{'recovered':>9} {'tries':>5}")
    for reading in ("A", "B"):
        for uses in (1, 3, 5):
            s = Scene(reading, uses)
            pre = (s.mind.terr.strength(SLOT), s.mind.terr.base(), s.mind.terr.tried(SLOT))
            s.run()
            held = s.mind.terr.held(SLOT)
            row = s.mind.terr.rows[SLOT]
            m = s.measure()
            m["doubt"] = m["doubt"] or f"({row['holder']}, s={s.mind.terr.strength(SLOT):.2f}, b={s.mind.terr.base():.2f})"
            print(f"{reading:8} {uses:>4} {held:>4}  {str(m['grief_pull']):>10} {str(m['grief_at']):>8}  "
                  f"{str(m['doubt']):16} {str(m['recovered']):>9} {m['tries']:>5}")


if __name__ == "__main__":
    main()
