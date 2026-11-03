"""Statement slots (rung 7): the color line's loop header and the statement that grows its result, as two slots.

    v3 = []
    <header>:                  for v4 in range(len(v1)) | for v4, v5 in zip(v1, v2) | for v4, v5 in enumerate(v1)
        <growth>               v3.append((v1[v4], v2[v4])) | v3 += [(...)] | ...
    return v3

Fills are not the seeds' programs. They are ways: a seed's header or growth statement with its names stripped
(CodeWorld.shape: a name read as ext, a parameter, or loc, the function's own), wired again with the names in scope at
the slot (POC3's existential wiring: every name of the right type and origin). A growth statement from one seed set
under another seed's header is wired to that header's names. Replacing the header keeps the body.

A code can only push fills whose shape it knows (`known`): given at its start, told by a pattern, or recalled. The
world offers what the code can name, not every expansion of the grammar (an unguided statement slot is intractable:
78 statement options at the loop, 20,000 complete loops at depth 6, none passing: LADDER.md rung 6).
"""
import itertools

from codeworld import CodeWorld
import grammar as G  # noqa: E402
import references as R  # noqa: E402
from printer import op  # noqa: E402

LOOP = (1, 0, 1, 1)
FACETS = ("ps_lockstep", "ps_pair_output", "ps_position_from_loop", "ps_collect")
SEEDS = {"positions": R.color_line, "zip": R.color_line_zip, "enumerate": R.color_line_enumerate,
         "accumulate": R.color_line_accumulating}


def stmt_text(n):
    lines = []
    op(n, 0, lines)
    return lines[0] if n.kind not in G.LOOPS else lines[0]


def typed_names(tree, node):
    """{id(name leaf): (type, origin)} for the name leaves read under node in tree (binding targets and loop names
    excluded: they stay fixed)."""
    params = {p.value for p in tree.kids[1].kids[0].kids[0].kids}
    ids = {id(x) for x in G.walk(node)}
    out = {}
    for v in G.visit(tree):
        n = v.node
        if id(n) in ids and n.kind == "name" and v.expect not in ("new", "target"):
            out[id(n)] = (v.scope.vars.get(n.value), "ext" if n.value in params else "loc")
    return out


def ways():
    """The seeds' ways: {'header': [(seed, loop node with an empty body)], 'growth': [(seed, statement)]}, each with
    the types and origins of its name leaves (as read in its seed)."""
    out = {"header": [], "growth": []}
    for seed, make in SEEDS.items():
        t = make()
        loop = G.find(t, LOOP).node
        body = loop.kids[-1].kids[0]
        out["header"].append((seed, loop, typed_names(t, loop.kids[:-1] and G.Node("x", loop.kids[:-1]))))
        out["growth"].append((seed, body, typed_names(t, body)))
    return out


def way_parts(seed):
    """A seed's growth statement read from one tree: (statement, {id(name leaf): (type, origin)}, {id(value
    operation): type}), the types as poc2's grammar infers them in the seed. One tree, so the ids agree."""
    t = SEEDS[seed]()
    body = G.find(t, LOOP).node.kids[-1].kids[0]
    ids = {id(x) for x in G.walk(body)}
    parts = {id(v.node): G.infer(v.node, v.scope) for v in G.visit(t)
             if id(v.node) in ids and v.node.kind in G.VALUE_OPS and v.scope is not None}
    return body, typed_names(t, body), parts


def recombinations(host, donor, donor_varied=False):
    """The host way with one of its value operations replaced by a value operation of the same type from the donor way
    (rung 9; typed: untyped splicing would be noise; names are left to the wiring, so only operations are exchanged).
    [(statement, names for the wiring)]."""
    hbody, hnames, hparts = way_parts(host)
    dbody, dnames, dparts = way_parts(donor)
    out = []
    donors = [dbody] + ([swapped(dbody)] if donor_varied else [])   # the donor as held: varied too, if it was
    for h in G.walk(hbody):
        if hparts.get(id(h)) is None:
            continue
        for d in (x for body in donors for x in G.walk(body)):
            if d.kind == "pairing" and id(d) not in dparts:   # a swapped pair: typed as the pair it was made from
                orig = next((o for o in G.walk(dbody) if o.kind == "pairing" and
                             [id(k) for k in o.kids] == [id(k) for k in reversed(d.kids)]), None)
                if orig is not None:
                    dparts[id(d)] = dparts.get(id(orig))
            if dparts.get(id(d)) != hparts[id(h)] or id(d) not in dparts:
                continue

            def sub(n, h=h, d=d):
                return d if n is h else G.Node(n.kind, [sub(k) for k in n.kids], n.value, n.type)
            out.append((sub(hbody), {**hnames, **dnames}))
    return out


def rewire(node, names, scope, params):
    """Every way of filling node's name leaves with names in scope of the same type and origin. names: {id: (type,
    origin)} from the node's seed; scope: {name: type} at the slot."""
    leaves = [x for x in G.walk(node) if id(x) in names]
    options = []
    for x in leaves:
        t, origin = names[id(x)]
        options.append([n for n, ty in sorted(scope.items()) if ty == t and ((n in params) == (origin == "ext"))])
    out = []
    for pick in itertools.product(*options):
        m = dict(zip(map(id, leaves), pick))

        def go(n):
            if id(n) in m:
                return G.name(m[id(n)])
            return G.Node(n.kind, [go(k) for k in n.kids], n.value, n.type)
        out.append(go(node))
    return out


def swapped(node):
    """The way with the two parts of its pair swapped (POC3's reorder, on a held way): the same leaves, so the names
    read from the seed (by node id) still apply to the variant."""
    if node.kind == "pairing" and len(node.kids) == 2:
        return G.Node(node.kind, [node.kids[1], node.kids[0]], node.value, node.type)
    return G.Node(node.kind, [swapped(k) for k in node.kids], node.value, node.type)


class StmtWorld(CodeWorld):
    def __init__(self, header_seed, known=(), spec="spec", order=0, registry=None, code=None):
        self.ways, self.order = ways(), order
        self.known = set(known)   # (slot, seed): the ways this code can use
        self.registry, self.code = registry, code
        program = SEEDS[header_seed]()
        loop = G.find(program, LOOP).node
        program = G.replace(program, LOOP, G.Node(loop.kind, loop.kids[:-1] + [G.block(G.hole("stmt"))]))
        self.known.add(("header", header_seed))
        super().__init__(program, {}, "color_line", "parallel_strings", FACETS, spec=spec)
        self.slots = {"header": LOOP, "growth": self.growth_path()}
        self.objs.update({"header": None, "growth": None})
        self._fills = {}
        self.refill()

    def growth_path(self):
        loop = G.find(self.program, LOOP).node
        return LOOP + (len(loop.kids) - 1, 0)

    def refill(self):
        """The fills on offer, from the known ways, wired in the scope they would sit in."""
        params = {"v1", "v2"}
        self._fills = {"header": {}, "growth": {}}
        body = G.find(self.program, LOOP).node.kids[-1]
        for seed, loop, names in self.ways["header"]:
            if ("header", seed) not in self.known:
                continue
            scope = {"v1": G.STR, "v2": G.STR}
            heads = rewire(G.Node("x", loop.kids[:-1]), names, scope, params)
            for h in heads:
                node = G.Node(loop.kind, h.kids + [body])
                self._fills["header"][f"{seed}:{stmt_text(G.Node(loop.kind, h.kids + [G.block()]))}"] = node
        self.slots["growth"] = self.growth_path()
        scope = G.find(G.replace(self.program, self.slots["growth"], G.hole("stmt")), self.slots["growth"]).scope.vars
        for seed, stmt, names in self.ways["growth"]:
            if ("growth", seed) not in self.known:
                continue
            for s in rewire(stmt, names, scope, params):
                self._fills["growth"][f"{seed}:{stmt_text(s)}"] = s
            if ("growth", seed) in getattr(self, "varied", set()):   # the way varied: its pair's parts swapped
                for s in rewire(swapped(stmt), names, scope, params):
                    self._fills["growth"][f"{seed}~swap:{stmt_text(s)}"] = s
        for host, donor in sorted(getattr(self, "recombined", set())):   # parts of two held ways, recombined
            if ("growth", host) in self.known and ("growth", donor) in self.known:
                for stmt, names in recombinations(host, donor, ("growth", donor) in getattr(self, "varied", set())):
                    for s in rewire(stmt, names, scope, params):
                        self._fills["growth"].setdefault(f"{host}+{donor}:{stmt_text(s)}", s)
        import lean   # each fill is its own push strength, of size 1 (as CodeWorld registers its fills)
        for fills in self._fills.values():
            for label in fills:
                lean.AMOUNTS.setdefault(label, 1.0)

    def _type(self, path):
        return None

    def _complete_fills(self, path):
        return {}

    def evaluate(self):
        if any(n.kind == "hole" for n in G.walk(self.program.kids[1])):
            return False, {s: "unreached" for s in self.slots}
        try:
            return super().evaluate()
        except Exception:
            return False, {s: "unreached" for s in self.slots}

    def _read(self):
        out = super()._read()
        for s in self.slots:   # a statement slot's state: its roles (statements have no value of their own)
            out[s] = out[s].split("=")[0]
        return out

    def invitations(self, tree=None):
        out = [(label, s, "slot") for s in ("header", "growth") for label in sorted(self._fills.get(s, {}))]
        # (a slot invites its fills whatever fills it now: CodeWorld.invitations)
        return out + [("run", self.spec, "passing" if self.passing else "failing")]

    def act(self, inv=None, hold=False):
        if inv is not None and inv[1] in ("header", "growth"):
            node = self._fills[inv[1]][inv[0]]
            if inv[1] == "header":   # the body comes along
                body = G.find(self.program, LOOP).node.kids[-1]
                node = G.Node(node.kind, node.kids[:-1] + [body])
            before = self.states()
            self.program = G.replace(self.program, self.slots[inv[1]] if inv[1] == "growth" else LOOP, node)
            self.version += 1
            self.passing = False
            self.refill()
            after = self.states()
            governed = set(self.slots) | set(self.roles)   # a fill reports what it governs (CodeWorld.act)
            self.diffs = [f"{o}: {before[o]} -> {after[o]}" for o in after if o in before
                          and (after[o] != before[o] or o in governed) and o != self.spec]
            self.t += 1
            return self.diffs
        return super().act(inv, hold)

    def learn_way(self, slot, seed):
        self.known.add((slot, seed))
        self.refill()

    def recombine(self, host, donor):
        """Two held growth ways recombined (rung 9): the host's value operations replaced by the donor's of the same
        type, offered wired in scope like any way."""
        self.recombined = getattr(self, "recombined", set()) | {(host, donor)}
        self.refill()

    def vary(self, slot, seed):
        """A held way varied (rung 8): its pair's parts swapped, offered wired in scope like any way."""
        self.varied = getattr(self, "varied", set()) | {(slot, seed)}
        self.refill()
