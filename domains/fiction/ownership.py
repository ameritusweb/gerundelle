"""Ownership slots and the phases read off them, for the lean arm: a port of Gerundelle's Territory
register and Phases.graph (molecules.py; REORG.md, OWNERSHIP_SOV.md), cut to what the ladder needs.

One row per region (an object): the claims on it (pushes that were ever followed by a change in it) and
their tries and takes; moves by something else. A claim takes if the region changed and what was
predicted there came. Holding strength: (took + KAPPA b) / (tried + KAPPA), b the base rate over all
regions. The holder read off it, as perceived:
    mine       strength above b, nothing else seen moving it since it was claimed
    contested  held, and something else moves it too (or its own claim just failed)
    lost       was mine, strength fell to b, nothing else moving it
    nobody     tried, never taking, nothing else moving it
    unknown    never tried

The ownership SOV's open slot instances, own:<kind>:<region>, and their pulls (times T):
    unclaimed   untried, perceived             KAPPA / (KAPPA + other moves)
    control     wanted, or tried and not taking 1 + tried / (tried + KAPPA)
    contested   held, something else moves it  1 + strength x KAPPA / (KAPPA + other moves)
    lost        was mine, fell                 1 + held
    uniqueness  mine                           KAPPA / (KAPPA + tried)
What each kind pays its region's claims to find out (Territory.NEEDS): unclaimed their causes, control
and lost their conditions.

Phases (Phases.graph), each anchored on its instance:
    frustration  a control (or contested-by-failure) slot whose claims failed twice running
    anxiety      a held region's claim failed once
    sadness      a lost slot
    joy          an instance closed because a claim took on its region
    curiosity    an unclaimed slot whose push won into action (Gerundelle: winning the ownership track)
"""
from beats import effect_parts

KAPPA = 2.0
# contested probes its own claims ("is the change mine?", REORG.md step notes on T57): it pays their causes
NEEDS = {"unclaimed": ("causes",), "control": ("conditions",), "contested": ("causes",), "lost": ("conditions",),
         "uniqueness": ("causes", "conditions")}


class Territory:
    def __init__(self, objs=()):
        self.objs = set(objs)
        self.rows = {}
        self.wants = {}          # region -> wanted change: a control slot opened by the mind itself
        self.took_now = set()
        self.prev_live = set()
        self.phases = {}         # phase id -> (kind, instance, formed at)

    def row(self, r):
        return self.rows.setdefault(r, dict(claims={}, other=0, other_since=0, ever=False, fails=0, failed=False,
                                             holder="unknown"))

    def perceived(self, regions):
        """region -> pushes on it: claims, untried."""
        for r, pushes in regions.items():
            for p in pushes:
                self.row(r)["claims"].setdefault(p, [0, 0])

    def base(self):
        """The base rate of claims taking, shrunk toward 1/2 by KAPPA (Gerundelle: 1/2 before any try; with
        a raw rate, every claim taking on the first try made b = 1 and nothing could be held above it)."""
        tried = sum(c[0] for row in self.rows.values() for c in row["claims"].values())
        took = sum(c[1] for row in self.rows.values() for c in row["claims"].values())
        return (took + KAPPA * 0.5) / (tried + KAPPA)

    def tried(self, r):
        return sum(c[0] for c in self.rows.get(r, {}).get("claims", {}).values())

    def held(self, r):
        return sum(c[1] for c in self.rows.get(r, {}).get("claims", {}).values())

    def strength(self, r):
        n = self.tried(r)
        return (self.held(r) + KAPPA * self.base()) / (n + KAPPA) if n else 0.0

    def claimed(self, push, pushed, effects, predicted=None):
        """A push's watch ended (effects: 'obj_gerund' names). Its claims are the region pushed, the regions
        it ever changed, and those changed now. Each is tried; it took if the region changed and the
        changes predicted there came (with no prediction yet, a change is enough)."""
        effects = set(effects)
        changed = {effect_parts(e, self.objs)[0] for e in effects}
        regions = {pushed} | changed | {r for r, row in self.rows.items() if push in row["claims"]}
        for r in regions:
            row = self.row(r)
            c = row["claims"].setdefault(push, [0, 0])
            want = {e for e in (predicted or ()) if e.startswith(r + "_")}
            took = r in changed and want <= effects
            c[0] += 1
            c[1] += took
            row["fails"] = 0 if took else row["fails"] + 1
            if took:
                self.took_now.add(r)
            if row["ever"]:
                row["failed"] = not took
        self.update()

    def moved(self, changed):
        for r in set(changed):
            row = self.row(r)
            row["other"] += 1
            if row["ever"]:
                row["other_since"] += 1
        self.update()

    def update(self):
        b = self.base()
        for r, row in self.rows.items():
            if row.get("taken_by"):   # taken by someone: lost until a claim on it takes again
                row["holder"] = "lost"
                continue
            s, n = self.strength(r), self.tried(r)
            if n and s > b and not row["other_since"] and not row["failed"]:
                row["holder"], row["ever"] = "mine", True
            elif row["ever"] and (row["other_since"] or row["failed"]) and s > b:
                row["holder"] = "contested"
            elif row["ever"] and s <= b and not row["other"]:
                row["holder"] = "lost"
            elif n and not self.held(r):
                row["holder"] = "nobody" if not row["other"] else "another"
            elif not n:
                row["holder"] = "unknown" if not row["other"] else "another"

    def open_slots(self):
        out = set()
        for r, row in self.rows.items():
            h = row["holder"]
            if r in self.wants and self.wants[r] not in row.get("had", ()):   # wanted, not yet had
                out.add(("control", r))
            elif r in self.wants and h in ("nobody", "another", "unknown"):   # had: the want's slot closed
                continue
            elif h in ("unknown", "another") and not self.tried(r) and row["claims"]:
                out.add(("unclaimed", r))
            elif h == "nobody":
                out.add(("control", r))
            elif h in ("contested", "lost"):
                out.add((h, r))
            elif h == "mine":
                out.add(("uniqueness", r))
        return out

    def reached(self, r, change):
        """The wanted change came: the want's control slot on its region closes."""
        self.row(r).setdefault("had", set()).add(change)
        self.took_now.add(r)

    def pull(self, kind, r):
        row = self.rows[r]
        n = self.tried(r)
        if kind == "unclaimed":
            return getattr(self, "curiosity", 1.0) * KAPPA / (KAPPA + row["other"])
        if kind == "control":
            return 1.0 + n / (n + KAPPA)
        if kind == "contested":
            return 1.0 + self.strength(r) * KAPPA / (KAPPA + row["other"])
        if kind == "lost":
            return 1.0 + self.held(r)
        if kind == "uniqueness":
            return KAPPA / (KAPPA + n)
        return 0.0

    def serve(self):
        """What the open instances pay for: push -> (pay, the relations its hole is paid to find out)."""
        out = {}
        for k, r in self.open_slots():
            pay = self.pull(k, r)
            for push in self.rows[r]["claims"]:
                p, needs = out.get(push, (0.0, ()))
                out[push] = (max(p, pay), tuple(sorted(set(needs) | set(NEEDS[k]))))
        return out

    def attend(self, r, t):
        """A push on region r won into action: if r's slot is unclaimed, curiosity forms on it (Gerundelle:
        an unclaimed slot winning the ownership track). Returns the phase formed, if any."""
        if ("unclaimed", r) in self.open_slots() and f"phase:curiosity:own:unclaimed:{r}" not in self.phases:
            self.phases[f"phase:curiosity:own:unclaimed:{r}"] = ("curiosity", f"own:unclaimed:{r}", t)
            return ("curiosity", f"own:unclaimed:{r}")
        return None

    def read_phases(self, t):
        """The phases formed this tick, as (kind, instance) (Phases.graph)."""
        formed = []
        live = self.open_slots()

        def form(kind, inst):
            pid = f"phase:{kind}:{inst}"
            if pid not in self.phases:
                self.phases[pid] = (kind, inst, t)
                formed.append((kind, inst))
        for k, r in sorted(live):
            row, inst = self.rows[r], f"own:{k}:{r}"
            failing = k == "control" or (k == "contested" and row["failed"] and not row["other_since"])
            if failing and row["fails"] >= 2:
                form("frustration", inst)
            elif k == "contested" and row["failed"] and not row["other_since"] and row["fails"] == 1:
                form("anxiety", inst)
            if k == "lost":
                form("sadness", inst)
        for k, r in sorted(self.prev_live - live):
            if r in self.took_now:
                form("joy", f"own:{k}:{r}")
        self.took_now = set()
        self.prev_live = live
        return formed
