"""A readable explanation of a move (the user, 2026-11-17: "Does the Gerundelle mind have an inspectable 'reason' for each move?";
"don't throw it away; show a readable explanation for the last N moves in the app"). Read off what the mind already keeps; nothing in
how it chooses changes:
- how it was chosen: the tournament's top pick among the moves on offer (SovAgent.winner), a step planned toward its held want
  (SovAgent.planned), the next step of a committed sequence (Params.commit), or an experiment's step; recorded by rung4p's player
- what it wanted (agent.goal, and the wants it served, agent.stack) and what it was avoiding (agent.anti)
- what the move was predicted to lead to (agent.push_leads, from the forces this slice), marked where the mind has lived such a
  loss before (loss_rels: a feared kind)
- the slice's tournament at its top level (agent.last_rec): the moves that won it with their bids, and the other thoughts there
explain(...) -> a dict with the fields and `text`, the readable lines."""
import re

KIND = {"piece": "a piece", "square": "a square", "outpost": "an outpost"}


def _dist(d):
    if d == "0":
        return "on the square the piece lands on"
    if d == "1":
        return "next to where it lands"
    if d == "x":
        return "elsewhere"
    return f"{d} squares from where it lands"


def effect_text(rel):
    """A potential effect (relative), in words."""
    rel = rel.split(":", 1)[1] if rel.startswith("potential:") else rel
    m = re.fullmatch(r"plan_(piece|square|outpost)\+(\w+?)_(none|stoppable|unstoppable|made)", rel)
    if m:
        kind, d, new = m.groups()
        where = _dist(d)
        return {"none": f"ends a plan of theirs to win {KIND[kind]} {where}",
                "stoppable": f"gives them a plan to win {KIND[kind]} {where} (one it could stop)",
                "unstoppable": f"gives them a plan to win {KIND[kind]} {where} that it couldn't stop",
                "made": f"lets them win {KIND[kind]} {where}"}[new]
    if rel.startswith("mate+"):
        return "checkmates"
    if rel.startswith("forced_mate+"):
        return "reaches a new forced mate (Stockfish)"
    if rel.startswith("plan_stalemate+"):
        return "stalemates them (a draw)"
    m = re.fullmatch(r"bearing\+(\d+)_(hanging|pressed|free)", rel)
    if m:
        d, new = m.groups()
        where = "the piece it moves" if d == "0" else f"its piece {d} squares from where it lands"
        return f"leaves {where} hanging" if new == "hanging" else f"stops {where} hanging ({new})"
    m = re.fullmatch(r"cover\+(\d)_(uncovered|covered|none)", rel)
    if m:
        n, new = m.groups()
        return {"uncovered": f"leaves {n} of its pieces under threats no one move can all answer (an overload)",
                "covered": f"makes {n} threats answerable by one move again",
                "none": f"ends an overload of {n} threats"}[new]
    return rel.replace("_", " ")


def region_text(r):
    """A want, an anti-want or a region, in words."""
    if r is None:
        return "nothing"
    if r.startswith("potential_"):   # (a territory row's name for a potential effect)
        r = "potential:" + r[len("potential_"):]
    if r.startswith("potential:"):
        return "a move that " + effect_text(r)
    if r.startswith("all:"):
        return " and ".join(region_text(x) for x in r[4:].split("&"))
    if r.startswith("anti:"):
        return region_text(r[5:])
    m = re.fullmatch(r"plan_(piece|square|outpost)_([a-h][1-8])_(none|stoppable|unstoppable|made)", r)
    if m:
        kind, sq, st = m.groups()
        return {"none": f"no plan of theirs to win the {kind} on {sq}",
                "stoppable": f"their plan to win the {kind} on {sq} stoppable",
                "unstoppable": f"their plan to win the {kind} on {sq} unstoppable",
                "made": f"their plan to win the {kind} on {sq} made"}[st]
    m = re.fullmatch(r"plan_(piece|square|outpost)_([a-h][1-8])", r)
    if m:
        return f"their plan to win the {m.group(1)} on {m.group(2)}"
    m = re.fullmatch(r"standing_(white|black)_(up|down|even)", r)
    if m:
        return f"{m.group(1).title()} {'ahead' if m.group(2) == 'up' else 'behind' if m.group(2) == 'down' else 'level'} in material"
    m = re.fullmatch(r"outcome_(white|black)_(\w+)", r)
    if m:
        return f"the game {m.group(2)} for {m.group(1).title()}"
    m = re.fullmatch(r"(white|black)_(\w+?)_([a-h][1-8])_(bearing|exerting|unique)_(\w+)", r)
    if m:
        side, piece, sq, what, st = m.groups()
        return f"{side.title()}'s {piece} from {sq} {st}"
    if r.startswith("cover_"):
        parts = re.findall(r"plan_piece_([a-h][1-8])", r)
        st = r.rsplit("_", 1)[1]
        return f"the pieces on {', '.join(parts)} {'overloaded' if st == 'uncovered' else 'answerable together' if st == 'covered' else 'not overloaded'}"
    m = re.fullmatch(r"file_([a-h])_(\w+)", r)
    if m:
        return f"the {m.group(1)}-file {m.group(2)}"
    if r.startswith("held_"):   # (an anti-want for a doing, anywhere: SovAgent.anti_update's held_<doing>)
        doing = r[5:].replace("_", " ")
        example = {"hanging": "one of its own pieces left hanging", "pressed": "one of its own pieces pressed",
                   "uncovered": "two of its pieces under threats one move can't all answer",
                   "covered": "threats on its pieces it must answer"}.get(doing, f"a plan of theirs becoming {doing}")
        return f"anything it holds becoming {doing} (e.g. {example})"
    return r.replace("_", " ")


def thought_text(i):
    """A thought in the tournament (a molecule's id), in words."""
    i = i.split("|")[0]
    m = re.fullmatch(r"\d{3} ([a-h][1-8][a-h][1-8][qrbn]?)_push:.*", i)
    if m:
        return f"the move {m.group(1)}"
    m = re.match(r"exp:(\w+):(.*)", i)
    if m:
        moves = re.findall(r"\d{3} ([a-h][1-8][a-h][1-8][qrbn]?)_push", m.group(2))
        return f"an experiment ({m.group(1)}): {' then '.join(moves) or m.group(2)}"
    m = re.match(r"own:(q:)?control:(.+)", i)
    if m:
        return f"{'a question about ' if m.group(1) else ''}a control slot for {region_text(m.group(2))}"
    m = re.search(r"commit_push[:_]potential[:_](.+?)[:_ ](\d{3} [a-h][1-8][a-h][1-8][qrbn]?)_push", i)
    if m:
        return f"a commitment: {m.group(2).split(' ')[1]}, a move that {effect_text(m.group(1))}"
    m = re.match(r"(?:sov:)?ask_push:(.+?)(?::|$)", i)
    if m:
        return f"asking the tool about {region_text(m.group(1))}"
    m = re.match(r"phase:(\w+):own:(\w+):(.+)", i)
    if m:
        return f"{m.group(1)} ({region_text(m.group(3))}: {m.group(2)})"
    m = re.match(r"own:q:unclaimed:(.+)", i)
    if m:
        return f"an unclaimed wish for {region_text(m.group(1))}"
    m = re.match(r"own:(mine|contested|lost):(.+)", i)
    if m:
        return f"{region_text(m.group(2))}: its territory, {'held' if m.group(1) == 'mine' else m.group(1)}"
    m = re.match(r"subwant:(.+)", i)
    if m:
        return f"a sub-want: {region_text(m.group(1))}"
    m = re.match(r"q:(\w+):(.+)", i)
    if m:
        return f"a question ({m.group(1)}) about {thought_text(m.group(2))}"
    m = re.match(r"sov:(.+)", i)
    if m:
        return region_text(m.group(1))
    return region_text(i)


def inv_id_of(inv):
    return f"{inv[0]}_push:{inv[1]}_{inv[2]}" if isinstance(inv, tuple) else str(inv)


def _uci(push_id):
    m = re.match(r"\d+ ([a-h][1-8][a-h][1-8][qrbn]?)_push", push_id)
    return m.group(1) if m else None


def explain(agent, world, choice, route, fen_before, side, half_move, profile=""):
    import chess
    from force_world import inv_id
    c = inv_id(choice)
    uci = choice[0].split(" ", 1)[1]
    try:
        san = chess.Board(fen_before).san(chess.Move.from_uci(uci))
    except ValueError:
        san = uci
    feared = {r for r in agent.mind.understanding.__dict__.get("loss_rels", set())}
    leads = agent.__dict__.get("push_leads", {}) or {}

    def lead_lines(push):
        out = []
        for pot in sorted(leads.get(push, ())):
            rel = pot.split(":", 1)[1]
            out.append(effect_text(rel) + ("  [feared: a loss it has lived]" if rel in feared else ""))
        return out

    rec = agent.__dict__.get("last_rec") or {}
    top = (rec.get("levels") or [{}])[-1]
    bids = top.get("bids", {})
    winners = top.get("winners", [])
    pushes = sorted({w.split("|")[0] for w in winners if _uci(w)}, key=lambda w: -bids.get(w, 0.0))
    others = sorted([w for w in winners if not _uci(w)], key=lambda w: -bids.get(w, 0.0))
    kind, goal_then = route or (None, None)
    if kind == "commit-winner":   # a commitment won the tournament: its first step is this move
        commit = goal_then
        what = re.search(r"potential[:_](.+?)[:_ ]\d{3} ", inv_id_of(commit)) if commit else None
        goal_then = None
        how_commit = ("the tournament's top pick was a commitment: this move, the first step of a sequence it committed to (predicted: "
                      + (effect_text(what.group(1)) if what else "an effect it wants") + ")")
    else:
        how_commit = None
    how = {"winner": "the tournament's top pick among the moves on offer", "commit-winner": how_commit,
           "planned": f"a step planned toward its want ({region_text(goal_then)})",
           "commit": "the next step of a sequence it had committed to",
           "experiment": "a step of an experiment it was running"}.get(kind, "chosen another way")
    pulled = agent.mind.__dict__.get("plan_pull") or {}
    if kind == "winner" and c in pulled:
        how = f"the tournament's top pick, pulled by its want's planned step ({region_text(agent.goal or goal_then)})"
    elif kind == "winner" and pulled:
        how = (f"the tournament's top pick, over its want's planned step "
               f"({next(iter(pulled)).split('_push')[0].split(' ', 1)[-1]}, losses felt against it)")
    number = f"{(half_move + 1) // 2}{'.' if side == 'White' else '...'}"
    lines = [f"{number} {san} ({side}{', ' + profile if profile else ''}) — {how}"]
    # an experiment that reached the top but yielded to what was at stake (Params.experimentation): said, with the stakes
    t_now = agent.mind.t
    st = agent.__dict__.get("_stakes")
    for t_, eid, step in agent.__dict__.get("experiment_yields", [])[-3:]:
        if t_ >= t_now - 1:
            m = re.search(r"(\d+ [^_]+_push:.*)$", step)
            under = m.group(1) if m else step
            stake = st[1].get(under) if st and st[0] == t_ else None
            best = max(st[1].values()) if st and st[0] == t_ and st[1] else None
            lines.append(f"   an experiment yielded: {thought_text(eid)[:80]} — its move {_uci(under) or under[:30]} at stake {stake}, the best move "
                         f"on offer {best} (its experimentation {agent.mind.p.experimentation}: the experiment waits when the best is better "
                         f"by more than that)")
    lines.append(f"   wanted: {region_text(agent.goal)}" + (f" (serving {', '.join(region_text(s) for s in agent.stack)})" if agent.stack else ""))
    lines.append(f"   avoiding: {region_text(agent.__dict__.get('anti'))}")
    # the move made, by its real squares: the one-move predictions it stood (push_predicted: absolute effect, its relative kind)
    absolute = [(eff, rel) for eff, n, rel, pid, cc in agent.__dict__.get("push_predicted", []) if cc == c]
    if absolute:
        ll = [("leaves " if eff.endswith("_hanging") else "stops hanging: ") + region_text(eff) if "_bearing_" in eff else
              region_text(eff).replace("no plan of theirs", "ends their plan") if eff.endswith("_none") else
              ("gives them " + region_text(eff).replace("their plan", "a plan").replace(" stoppable", " (one it can stop)")
               .replace(" unstoppable", " it can't stop")) if eff.startswith("plan_") else effect_text(rel)
              for eff, rel in sorted(absolute)]
        ll = [x + ("  [feared: a loss it has lived]" if rel in feared else "") for x, (eff, rel) in zip(ll, sorted(absolute))]
    else:
        ll = lead_lines(c)
    lines.append("   predicted to: " + ("; ".join(ll) if ll else "nothing it could foresee"))
    if pushes:
        lines.append("   top of the tournament: " + ", ".join(f"{_uci(p)} {bids.get(p, 0.0):.2f}" + (" (played)" if p == c else "")
                                                          for p in pushes[:5]))
        for p in pushes[:4]:
            if p != c and lead_lines(p):
                lines.append(f"      {_uci(p)} would: " + "; ".join(lead_lines(p)[:3]))
    if others:
        lines.append("   other thoughts at the top:")
        for o in others[:4]:
            lines.append(f"      {bids.get(o, 0.0):.2f}  {thought_text(o)[:110]}")
    return dict(side=side, half_move=half_move, uci=uci, san=san, how=kind, goal=agent.goal, stack=list(agent.stack),
                anti=agent.__dict__.get("anti"), leads=sorted(leads.get(c, ())), text="\n".join(lines))
