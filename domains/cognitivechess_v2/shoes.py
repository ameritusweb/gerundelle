"""The mind in its opponent's shoes (LADDER.md, rung 4; the user, 2026-11-07: "the Gerundelle mind can put itself in the opponent's
shoes"). In an imagined line, the opponent's reply is the move the mind's own tournament picks from the opponent's side of the imagined
board: the opponent's moves enter the mind's pool as it stands, in place of the mind's own offers, each with the potential force it
would exert from that side (potential.py's reading: onto a hanging piece, a pressed one, or nothing), and the top-level winner among
them is the reply (Mind.imagined_winners: think()'s own levels; nothing kept, the firewall). README: recursive world-building, the
mind's own machinery run inside a world it imagines.
"""
import copy

from molecules import Territory, clause
from potential import HANGING, PRESSED, QUIET
from warpworld import BLACK, rehash


MINE_ONLY = ("own:", "subwant:", "phase:", "meta:", "exp:", "q:")   # the mind's own motivations and what they move


def their_wants(agent, states, side):
    """What the mind imagines the opponent wants (the user, 2026-11-07: empathy, part a): its own ownership machinery run from the
    other side. A copy of its territory register in which the opponent's pieces are the given territory (as its own are its own,
    like the body) and the mind's own doings on a region are another's; holders are read again by Territory.update, and the open
    slots that follow are the opponent's: own:<kind>:<region>, with the candidate wants own_candidates() offers for its own slots
    (every state the region was seen in but the one it is in now), each a site causes:<state> as a held want has (want_site), so a
    move the register says causes it binds to it. states: region -> fact on the imagined board; side: the opponent's colour word."""
    mind, mine = agent.mind, agent.mind.territory
    terr = Territory(mind)
    terr.given = {r for r in mine.rows if r.startswith(f"{side}_") and "_dream" not in r}
    for r, row in mine.rows.items():
        new = terr.row(r)
        new["seen_states"] = set(row.get("seen_states", ()))
        tried = sum(c[0] for c in row["claims"].values())   # the mind's own tries on it: another's, from that side
        new["other"] = tried
        new["other_since"] = tried
        new["other_last"] = row.get("other_last", mind.t)
        new["ever"] = r in terr.given
        new["gone"] = r in terr.given and r not in states
    terr.update(list(terr.rows))
    out = []
    for k, r in sorted(terr.open_slots()):
        out.append(clause(f"own:{k}:{r}", tags=("ownership", f"region:{r}"), sites=(f"{k}?{r}",)))
        if k not in ("lost", "control", "unclaimed", "contested"):
            continue
        for f in sorted(terr.rows[r].get("seen_states", set()) - {states.get(r)}):
            out.append(clause(f"subwant:{f}", tags=(f"{k}?{r}", "subwant", f"region:{r}"), sites=(f"causes:{f}",)))
    for x in out:
        x.act = 1.0
    return out


def in_their_shoes(agent):
    """A callable for Imagines.in_their_shoes: world -> the opponent's reply (a move) or None if it has none."""
    mind = agent.mind

    def reply(world):
        b = world.board
        side = b.turn
        rehash(b)
        moves = list(b.legal_moves)
        if not moves:
            return None
        states = world.read()
        und, told = mind.understanding, mind.p.credulity
        cands, by = {}, {}
        for m in moves:
            label = world.label(m)
            piece = world.ids_at(m.from_square)
            taken = next((o for o, sq in world.where.items() if sq == m.final_square and b.colors[m.final_square] != b.colors[m.from_square]), None)
            force = QUIET if taken is None else (HANGING if states.get(f"{taken}_bearing") == "hanging" else PRESSED)
            cid = f"{label}_push:{piece}_present"
            causes = tuple(sorted(f"causes:{e}" for (r, e), f in und.rel.get(cid, {}).items() if r == "causes" and f[0] + f[2] + told * f[1] > 0))
            cands[cid] = clause(cid, tags=("invitation", piece) + causes)   # (as perceive tags an offer under want_site)
            cands[cid].act = force
            by[cid] = m
        # the opponent's side: its moves, what the mind understands of the world (its SOVs, what it perceives), and what it imagines
        # the opponent wants (their_wants). The mind's own wants and what they move (its goal, sub-wants, ownership slots, phases,
        # meta, experiments, questions) are set aside. First they stayed, and its wants, slots and meta held every slot of the
        # opponent's tournament (trace_shoes.py, game 2: all 47 moves lost every slot 984 times)
        pool = {i: x for i, x in mind.pool.items()
                if "invitation" not in x.tags and "goal" not in x.tags and "subwant" not in x.tags and not i.startswith(MINE_ONLY)}
        pool.update({x.id: x for x in their_wants(agent, {o: f"{o}_{st}" for o, st in states.items()}, "black" if side == BLACK else "white")})
        pool.update(cands)
        levels = mind.imagined_levels(pool, set(cands))
        # the reply is a move: the one the tournament carried furthest (the highest level a move won, first among that level's
        # winners). First only the top level was read, and when other molecules held it (the mind's wants, phases, slots) the
        # opponent was imagined making no move at all, and dream trials with no reply kept nothing (game 3 on: 199 of 200)
        for L in range(len(levels) - 1, -1, -1):
            won = [i for i in levels[L]["winners"] if i in by]
            if won:
                if L < len(levels) - 1:
                    log = agent.__dict__.setdefault("shoes_below_top", [])
                    log.append((L, len(levels) - 1, [i for i in levels[-1]["winners"]][:6]))
                return by[won[0]]
        # no move won a slot at any level (the mind's own facts, wants and meta held them all; trace_shoes.py, game 2: 984 times all 47
        # moves lost every slot): the move the tournament bid highest, as every competitor is bid at the first level (ties by name)
        bids = levels[0]["bids"] if levels else {}
        agent.__dict__.setdefault("shoes_none", []).append((len(cands), len(pool), [l["winners"][:8] for l in levels]))   # for traces
        return by[min(by, key=lambda i: (-bids.get(i, 0.0), i))]
    return reply
