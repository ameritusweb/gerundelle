"""Known-answer tests for the Warp chess ladder (LADDER.md), as ../../analogy/molecules/test_molecules.py does them: each criterion is
fixed before running, and where a change can be switched off, an ablation arm shows it is what makes the difference.

Run: PYTHONHASHSEED=0 python -X utf8 -m pytest -q test_warpchess.py   (results depend on the hash seed, as every ladder run does)
"""
import os

import pytest

import rung0  # noqa: F401  (puts Gerundelle and the engine on the path)
from molecules import concept_of
from pieceminds import OfferedMainMind
from sov_agent import inv_id
from warpworld import BLACK, RUNG1_TWO, WHITE, WarpBoard, WarpWorld, rehash

WANT = "material_up"
SWITCHES = ("imagined_tournament", "want_site", "setup_support")

if os.environ.get("PYTHONHASHSEED") != "0":
    pytest.skip("run with PYTHONHASHSEED=0: the ladder's results depend on it", allow_module_level=True)


def mind(seed, on=True, pieces=False):
    """Rung 1f's main mind on rung 1's two-move room, with rung 1g's switches on or off."""
    w = WarpWorld(RUNG1_TWO, seed=seed, moves=2, forces=True)
    a = OfferedMainMind(w, pieces=pieces, forces=True)
    for ag in [a] + list(a.pieces.values()):
        for k in SWITCHES:
            setattr(ag.mind.p, k, on)
    return w, a


def live(a, ticks, each=None):
    for t in range(ticks):
        if a.goal is None:
            a.goal = WANT
        a.tick()
        if each:
            each(t)


def late_share(w):
    made = [x for x in w.log if x[2]]
    half = made[len(made) // 2:]
    return sum(x[3] == "up" for x in half) / max(1, len(half))


# ---- engine and world ------------------------------------------------------------------------------------------------

def test_turn_rehash():
    """A board turned to the other side is offered that side's moves (the engine caches legal moves by its hash)."""
    b = WarpBoard.starting_position()
    white = {m.uci() for m in b.legal_moves}
    b.turn = BLACK
    rehash(b)
    black = {m.uci() for m in b.legal_moves}
    assert white and black and not (white & black)


def test_king_jump_is_not_castling():
    """The user's engine fix: a king's 2-square jump from e1 with no castling rights moves no rook and takes no own piece."""
    b = WarpBoard.from_fen("4c3/8/1P1PP3/2P2P2/1Q4P1/P6P/RNB2BNR|||8/5p2/4n1K1/2p5/1p1c2p1/p2n1b1p/r2qkb1r b - - 23 18")
    b.push(next(m for m in b.legal_moves if m.uci() == "Re1Rg1"))
    assert b.to_fen().split("|||")[1].split()[0].split("/")[-1] == "r2q1bkr"


def test_rulebook_start_has_no_quick_mate():
    """From the rulebook's chevron start neither side has a one-move win (move.py's STARTING_FEN had both)."""
    b = WarpBoard.starting_position()
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        assert not c.is_game_over()
        for r in c.legal_moves:
            d = c.copy()
            d.push(r)
            assert not d.is_game_over()


# ---- territory (the user's decisions) ------------------------------------------------------------------------------------

def _given_mind(owned):
    import gameworld
    import rung4
    w = gameworld.GameWorld(seed=0, fen="8/8/8/8/3R4/5PPP/2K5|||8/8/8/3n4/8/8/4k3 w - - 0 1")
    w.owned = owned
    a = rung4.Player(w, "game")
    terr = a.mind.territory
    terr.given = w.white_pieces()
    for r in terr.given:
        terr.row(r)
    terr.update(terr.given)
    return w, a


def test_given_piece_captured_is_lost():
    """White's pieces are given territory, like the body; a captured one leaves view and reads as lost. Ablation: a world that
    keeps captured pieces in view (owned off) still reads it as the mind's."""
    for owned, want in ((True, "lost"), (False, "mine")):
        w, a = _given_mind(owned)
        a.tick()
        rook = "white_rook_Ld3"
        sq = w.where[rook]
        w.board.pieces[sq], w.board.colors[sq], w.where[rook] = 0, None, None   # taken off the board
        rehash(w.board)
        w.shown = w.read()
        for _ in range(3):
            a.tick()
        assert a.mind.territory.rows[rook]["holder"] == want, (owned, a.mind.territory.rows[rook]["holder"])


def test_taken_piece_stays_mine():
    """A Black piece White captures is White's for good (the user): its region is the mind's after the capture and stays so."""
    w, a = mind(0, on=True)
    seen = []
    live(a, 300, each=lambda t: seen.append(a.mind.territory.rows.get("black_knight_Rd4", {}).get("holder")))
    first = next(i for i, h in enumerate(seen) if h == "mine")
    assert all(h == "mine" for h in seen[first:]), seen[first:first + 20]


# ---- rung 1g's mechanisms -----------------------------------------------------------------------------------------------

def test_imagined_tournament_keeps_the_firewall():
    """An imagined tournament (Mind.imagined_winners, think()'s own levels) changes nothing in the mind: its pool and percepts
    are put back, and the same imagined pool gives the same winners twice. (No ablation: there is no switch for the firewall.)"""
    w, a = mind(2, on=True)
    live(a, 60)
    m = a.mind
    pool, perceived = dict(m.pool), set(m.perceived)
    first = m.imagined_winners(dict(pool), set(perceived))
    assert m.pool == pool and m.perceived == perceived
    assert m.imagined_winners(dict(pool), set(perceived)) == first
    assert first   # the levels ran


def test_held_want_does_not_settle():
    """A want the mind still holds is not a finished thought (the user): under want_site its box is never settled while it is
    the goal. (Main arm only: the fix is part of want_site; before it, seed 4's want settled at slice 273, LADDER.md.)"""
    w, a = mind(4, on=True)
    settled = []
    live(a, 400, each=lambda t: settled.append(t) if a.goal == WANT and a.mind.boxes.get(WANT, {}).get("settled") else None)
    assert not settled, settled[:5]


def test_untried_move_does_not_settle():
    """A move never tried isn't finished: what follows it is what isn't known (the user). Seed 3, main mind alone, switches on:
    no knight capture settles untried. (Main arm only: the fix is part of want_site; before it one did by slice 51, LADDER.md.)"""
    w, a = mind(3, on=True)
    bad = []

    def check(t):
        for c in [inv_id(i) for i in w.invitations() if "Rd4" in i[0]]:
            tried = any(inv_id(i) == c for i, _, _ in a.pushed)
            if a.mind.boxes.get(c, {}).get("settled") and not tried:
                bad.append((t, c))
    live(a, 300, each=check)
    assert not bad, bad[:3]


def test_move_not_on_offer_takes_no_slot():
    """A move not on offer supports the moves that set it up and takes no slot (the user). Ablation: off, moves not on offer
    held top-level slots."""
    for on in (True, False):
        w, a = mind(4, on=on)
        held = []

        def check(t):   # moves (molecules tagged invitation), against what that tournament perceived as on offer; thoughts about a
            # move (sov:, q:, exp:, meta:) aren't moves (first counted, and the test failed on them)
            perceived = {concept_of(i) or i for i in a.mind.perceived}
            top = a.last_rec["levels"][-1]["winners"]
            held.append(sum(1 for i in top if concept_of(i) and i in a.mind.pool and "invitation" in a.mind.pool[i].tags
                            and concept_of(i) not in perceived))
        live(a, 300, each=check)
        assert (sum(held) == 0) is on, (on, sum(held))


# ---- the ladder's findings --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [0, 3])
def test_crossing_found_and_settled(seed):
    """Rung 1g, every switch: the two-move crossing is found and settled on (late share 0.50 in both seeds). Ablation for seed 3:
    with the switches off it found the crossing at try 188 and won 0.05 of late episodes."""
    w, a = mind(seed, on=True)
    live(a, 1000)
    assert a.reached and late_share(w) >= 0.40, late_share(w)
    if seed == 3:
        w, a = mind(seed, on=False)
        live(a, 1000)
        assert late_share(w) < 0.20, late_share(w)


def test_wants_arise_from_slots():
    """With Params.own_wants and no want placed, the mind takes up a want of its own from its ownership slots within a game
    (REORG step 4; the user: humans map a game onto their own territorial motivations). Ablation: own_wants off, no want arises."""
    import gameworld
    import rung4
    for on in (True, False):
        w = gameworld.GameWorld(seed=1)
        w.owned = on
        w.actor = "White"
        a = rung4.Player(w, "game")
        rung4.switch(a.mind, True)
        a.mind.p.own_wants = on
        terr = a.mind.territory
        terr.given = w.white_pieces()
        for r in terr.given:
            terr.row(r)
        terr.update(terr.given)
        black = gameworld.RandomSide(w, 1)
        wanted = False
        for _ in range(150):
            if w.board.turn == 1:
                w.actor = "White"
                a.tick()
            else:
                black.tick()
                w.actor = "White"
                a.tick()
            wanted |= a.goal is not None
        assert wanted is on, on
