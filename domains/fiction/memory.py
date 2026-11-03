"""Phases over time: refreshed while their source is live, expiring open into storage, cooling, and
reopening by resonance. A port of Gerundelle's two-phase storage for the phases that can be resolved
(molecules.py Phases and Mind boxes; THOUGHT_MOLECULES.md sec. 5h; the book's chapter 5 and 8):

- a phase whose source is live is refreshed (a lost slot that could still be filled: its object is there);
  one whose source is parked (nothing could fill it now: the toy is gone) is not, and after EXPIRE ticks
  without refresh it leaves the active pool. A closable phase (sadness, anger) leaving with its goal unmet
  goes to storage **open**: a grief, a grudge (Gerundelle: "an emotion can fade without being resolved");
- a stored box has keys (the region and the person it is about) whose warmth halves every H_SITE ticks
  (Params.h_site, 20); below COLD (Params.cold, 0.1) it is no longer checked;
- resonance (Pandora): when a key comes back into perception (the toy, Leo) and the box is still warm, it
  reopens: the phase forms again, the same phase;
- closure: when the goal is met (the lost region held again), an open phase closes, stored or active. An
  anger closing by its goal met is forgiveness; one that is cold closes silently (nothing to forgive in
  mind any more).
"""
PHASE_H = 4.0     # Params.phase_h: half-life of a phase molecule not refreshed by what produced it
EXPIRE = 2 * PHASE_H
H_SITE = 20.0     # Params.h_site: half-life of a parked site's warmth
COLD = 0.1        # Params.cold: warmth below which a stored box is no longer checked
CLOSABLE = ("sadness", "anger")


class Memory:
    def __init__(self, store=True):
        """store: False is the ablation (Gerundelle with closure off): an expired phase ends into nothing
        instead of going to storage open, so nothing can reopen it."""
        self.store = store
        self.active = {}   # pid -> dict(kind, region, person, born, refreshed)
        self.stored = {}   # pid -> dict(kind, region, person, stored)
        self.log = []      # (t, event, pid)

    def form(self, kind, region, person, t):
        pid = f"phase:{kind}:{person or region}"
        if pid in self.active:
            self.active[pid]["refreshed"] = t
            return pid
        self.stored.pop(pid, None)
        self.active[pid] = dict(kind=kind, region=region, person=person, born=t, refreshed=t)
        self.log.append((t, "formed", pid))
        return pid

    def step(self, t, live):
        """live(phase) -> whether its source is live now. Returns the phases that expired open into storage."""
        faded = []
        for pid, p in list(self.active.items()):
            if live(p):
                p["refreshed"] = t
            elif t - p["refreshed"] >= EXPIRE:
                del self.active[pid]
                if p["kind"] in CLOSABLE and self.store:
                    # stored when it expired (its last refresh + EXPIRE), not when it is noticed: a phase that
                    # expired during a long absence has been cooling since
                    self.stored[pid] = dict(kind=p["kind"], region=p["region"], person=p["person"],
                                            stored=p["refreshed"] + EXPIRE)
                    self.log.append((t, "stored open", pid))
                    faded.append(pid)
        return faded

    def warmth(self, pid, t):
        b = self.stored[pid]
        return 0.5 ** ((t - b["stored"]) / H_SITE)

    def resonate(self, keys, t):
        """Boxes with a key among `keys` (regions and persons now perceived), warm enough: reopened."""
        out = []
        for pid, b in list(self.stored.items()):
            if {b["region"], b["person"]} & set(keys):
                if self.warmth(pid, t) >= COLD:
                    del self.stored[pid]
                    self.active[pid] = dict(kind=b["kind"], region=b["region"], person=b["person"], born=t,
                                            refreshed=t, reopened=True)
                    self.log.append((t, "reopened", pid))
                    out.append(pid)
                else:
                    self.log.append((t, "cold", pid))
        return out

    def close(self, region, t):
        """The goal of the phases about a region is met: they close. Returns [(pid, was active)]."""
        out = []
        for pool, active in ((self.active, True), (self.stored, False)):
            for pid, p in list(pool.items()):
                if p["region"] == region:
                    del pool[pid]
                    self.log.append((t, "closed" if active else "closed cold", pid))
                    out.append((pid, active, p))
        return out
