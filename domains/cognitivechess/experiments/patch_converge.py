"""One-off patch: Params.converge and SovAgent.notice in Gerundelle (E:/vscode/analogy/molecules), rung 1e.
Backup first: cognitivechess/backup/molecules_2026-10-30c/. Run once; it asserts each anchor is found exactly once."""
import os

M = "E:/vscode/analogy/molecules"


def patch(path, reps):
    p = os.path.join(M, path)
    s = open(p, encoding="utf-8").read()
    for a, b in reps:
        assert s.count(a) == 1, (path, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


patch("molecules.py", [(
    """    sub_cost: bool = False
""",
    """    sub_cost: bool = False
    # convergence in the agent's own choice (2026-10-30, the cognitive chess ladder rung 1e; off by default): a want
    # with no known way, in a world that can say what a push would meet (world.relations_of), notices the untried push
    # the constraints from its failed pushes converge on (embodied/CONSTRAINT_DISCOVERY.md; SovAgent.notice), before
    # sub-wants and experiments
    converge: bool = False
""")])

FUNCS = '''

def distinguishing(tags, others):
    """The smallest combination of `tags` that no other attempt carried in full, the tags commonest among the others let
    go first; None if some other attempt carried all of them (embodied/body/grasp.py's)."""
    s = set(tags)
    if any(s <= o for o in others):
        return None
    common = {t: sum(t in o for o in others) for t in s}
    for t in sorted(s, key=lambda x: (-common[x], x)):
        if len(s) > 1 and not any((s - {t}) <= o for o in others):
            s.discard(t)
    return frozenset(s)


def constraints_from(trials):
    """Each kind of failure's constraints among trials (what was met, what came of it): what is distinctive of its
    failures among the attempts, merged into what two share while that still tells them apart (grasp.py's)."""
    out = {}
    for e in sorted({ev for _, ev in trials if ev != "want"}):
        others = [t for t, ev in trials if ev != e]
        conj = []
        for t in [t for t, ev in trials if ev == e]:
            d = distinguishing(t, others)
            if d is not None and d not in conj:
                conj.append(d)
        merged = True
        while merged and len(conj) > 1:
            merged = False
            for i in range(len(conj)):
                for j in range(i + 1, len(conj)):
                    d = distinguishing(conj[i] & conj[j], others) if conj[i] & conj[j] else None
                    if d is not None:
                        conj = [c for k, c in enumerate(conj) if k not in (i, j)] + [d]
                        merged = True
                        break
                if merged:
                    break
        if conj:
            out[e] = conj
    return out
'''

NOTICE = '''    # ---- convergence (Params.converge; the cognitive chess ladder rung 1e) ---------------------------------------
    #
    # embodied/CONSTRAINT_DISCOVERY.md, as embodied/body/grasp.py does it for the hand: each failed push reveals a
    # constraint, what is distinctive of its kind of failure among the pushes; an untried push is perceived before it
    # is made (world.relations_of) and clears a constraint unless it would meet all of it; the constraints stand as
    # molecules whose open site is clearing them, each combination weighing by its receipts (1 - 1/2^n); a tournament
    # with candidate support in superposition notices the push they converge on. Noticed only when one push alone
    # clears every constraint and wins the top: otherwise sub-wants and experiments go on as before.

    def kind(self, names):
        """A failure's kind: what the world's events did (world.events, e.g. its reply), else what changed."""
        ev = getattr(self.world, "events", ("reply",))
        out = sorted(e for e in names if self.owner_of(e) in ev)
        return "|".join(out) if out else "|".join(sorted(names))

    def notice(self, invs):
        """The untried push the constraints converge on (one alone clears them all and wins the top), or None."""
        cons = constraints_from(self.trials)
        if not cons:
            return None
        now = self.facts_now()
        options = [i for _, i in sorted(invs.items()) if not any(j == i and f == now for j, f, _ in self.pushed)]
        if not options:
            return None
        meet = {i: self.world.relations_of(i) for i in options}
        combos = [(f"{e}#{k}", h, sum(1 for t, ev in self.trials if ev == e and h <= t))
                  for e, hs in sorted(cons.items()) for k, h in enumerate(hs)]
        clears = {i: [c for c, h, _ in combos if not h <= meet[i]] for i in options}
        mind = Mind(Params(support="candidates", sov=False, meta=False, closure=False))
        mols = [clause(f"try:{inv_id(i)}", tags=("attempt",) + tuple(f"clears:{c}" for c in clears[i])) for i in options]
        for c, h, n in combos:
            mind.present(clause(f"constraint:{c}", tags=("constraint",), sites=(f"clears:{c}",)), 1 - 0.5 ** n)
        bids = mind.tick(mols)["levels"][0]["bids"]
        bid = lambda i: round(bids.get(f"try:{inv_id(i)}", 0.0), 9)
        ranked = sorted(options, key=lambda i: -bid(i))
        top = ranked[0]
        unique = len(ranked) == 1 or bid(top) > bid(ranked[1])
        return top if unique and len(clears[top]) == len(combos) else None

'''

patch("sov_agent.py", [
    ("from molecules import Mind, Params, clause, mcts\n", "from molecules import Mind, Params, clause, mcts\n" + FUNCS),
    ("""        self.sub_log = []      # (tick, want, 'set' | 'met' | 'dropped' | 'tried' | 'kept' | 'restored' | 'used' | 'released')""",
     """        self.sub_log = []      # (tick, want, 'set' | 'met' | 'dropped' | 'tried' | 'kept' | 'restored' | 'used' | 'released')
        self.trials = []       # Params.converge: (what a push met, as the world said before it was made; what came of it)
        self.meeting = None    # what the push under way met
        self.noticed = []      # (tick, invitation): pushes noticed where the constraints converged"""),
    ("""        self.watching = (choice, self.facts_now(), 0, {})""",
     """        if self.mind.p.converge and self.goal is not None and hasattr(world, "relations_of"):
            self.meeting = world.relations_of(choice)
        self.watching = (choice, self.facts_now(), 0, {})"""),
    ("""        step = self.plan_step(invs)
        if step is not None or not self.mind.p.subwants""",
     """        step = self.plan_step(invs)
        if step is None and self.mind.p.converge and not self.queue and not self.running:
            noticed = self.notice(invs)
            if noticed is not None:
                self.noticed.append((self.mind.t, noticed))
                return noticed
        if step is not None or not self.mind.p.subwants"""),
    ("""        self.tried.append((mind.t, inv, names))
        self.pushed.append((inv, facts, frozenset(names)))""",
     """        self.tried.append((mind.t, inv, names))
        self.pushed.append((inv, facts, frozenset(names)))
        if self.meeting is not None:   # Params.converge: what it met, and what came of it (the want, or a failure's kind)
            if self.goal is not None:
                self.trials.append((self.meeting, "want" if self.goal in names else self.kind(names)))
            self.meeting = None"""),
    ("""    def costly(self, inv, fact, root):""", NOTICE + """    def costly(self, inv, fact, root):"""),
])
print("patched")
