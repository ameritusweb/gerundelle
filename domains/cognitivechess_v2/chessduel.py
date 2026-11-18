"""Two minds playing chess (cognitivechess_v2's league; the user, 2026-11-17: "set up a league like we did with Go? With different
temperaments", "Mind vs mind"). After go/goduel.py: each mind has its own seat, a full game world read for its colour (gameworld.me), and
the duel keeps the two seats one game.

- A turn: the mind to move gets slices in its seat until it moves (rung4p's TURN_STEPS at a time; no idle limit, as rung 4p). Its move is
  then played in the other seat as the other side's move (as gameworld.RandomSide plays Black's), and the two boards are checked equal.
  The other mind sees the move in its next slice.
- Endings: the rules (checkmate, stalemate, insufficient material, threefold repetition, the fifty-move rule), the half-move cap (a draw),
  and seventh-heaven chess for either side (the user, 2026-11-17: "Either side resigns"): each seat counts its own mind's new forced
  mates; at the 7th, its opponent resigns, in both seats.
- At a game's end both minds have slices to see the outcome, and both seats are set back together before the next game begins.
- Lifelong minds: a mind keeps its seat across games (its forced-mate record, its games), saved with it (rung4p.save_run).
"""
import time

import rung4p
from plansworld import give, read_mate_passed
from rung4 import TURN_STEPS
from sov_agent import inv_id as inv_id_

WHITE, BLACK = True, False
NAME = {WHITE: "White", BLACK: "Black"}


def configure(agent, profile=None):
    """v2's dreaming (rung4p --dreams: want-dreams on the quiet register) and a temperament profile's Params."""
    p = agent.mind.p
    p.dream_when_stuck = False
    agent.__dict__.pop("dreamer", None)
    p.dreams = False
    p.dream_for_want = True
    p.explained_needs = True   # every switch the user has decided on (2026-11-17): explained needs, patience counting reach
    p.patience_reach = True
    p.defense_still = True     # and a predicted loss of territory felt at once (the user, 2026-11-15's balance ruling; 2026-11-17:
    #                            "loss of territory is always felt"), read through the world's effects_after
    p.plan_as_pull = True      # a want's planned step pulls in the tournament, losses felt against it (the user, 2026-11-17, "do it")
    p.push_slots = (3, 2, 2)   # the moves on offer in a lane of their own, so the best of them always reach the top (the user, "do both")
    p.ask_once_here = True     # a tool question answered in this very position isn't asked again there (the stuck mind's loop)
    p.defense_gains = True     # the felt defense counts gains too: a lost region brought back (the user's balance ruling, both sides)
    p.region_weights = True    # and weighs each region as the world says: a piece's bearing by what it can reach (the user, 2026-11-17)
    p.experimentation = 0      # temperament: an experiment yields to anything at stake on the board (the user, 2026-11-17, "do it";
    #                            the "scientific" profile sets more)
    if getattr(agent, "world", None) is not None:   # and coverage, a reading of the world's
        agent.world.covers_read = True
    for k, v in (profile or {}).items():
        setattr(p, k, v)


def new_mind(colour, profile=None, seed=0, half_moves=300):
    """A fresh mind on its own seat, from the start."""
    w, a = rung4p.build(seed, None, dreams=True, half_moves=half_moves, me=colour)
    configure(a, profile)
    return a, w


LIFELONG = ("games", "episodes", "forced_mate_log", "forced_mate_seen")   # (the world's records a mind keeps across games: its won games
#   and forced mates are read into its territory by count, plansworld.give's _wins_read and _mates_read)
CARRIED = ("RESIGN_AFTER_NEW_MATES", "seed")   # (the league's settings on a seat)


def fresh_seat(agent, side, old=None, half_moves=None):
    """`agent` on a fresh seat for `side` at the start position: a new world seated for the colour, the mind's lifelong records carried
    over from its old world, the mind's perception and tool rewired to it. The mind keeps everything it learned. -> the new world"""
    old = old if old is not None else agent.world
    w, _ = rung4p.build(0, None, dreams=True, half_moves=half_moves or old.moves, me=side)
    for k in ("act", "_noticed_by"):   # (build's own agent wrapped the new world's act: unwrapped, then wrapped by this mind)
        w.__dict__.pop(k, None)
    for k in LIFELONG + CARRIED:
        if k in old.__dict__:
            w.__dict__[k] = old.__dict__[k]
    if side == old.__dict__.get("me", True):   # (the last game's positions feed want-dreams from the seat's own turns; only the same colour)
        w.__dict__["last_game"] = old.__dict__.get("last_game", [])
    w._stale_moves = old.moved
    w.actor = w.me_name
    agent.world = w
    agent.tool = rung4p.MindTool(w)
    if agent.mind.p.self_noticed:
        agent.noticing()
    if agent.mind.p.dreams:
        w.in_their_shoes = rung4p.shoes.in_their_shoes(agent)
    return w


class ChessDuel:
    def __init__(self, agents, worlds, log=print):
        self.agents, self.worlds, self.log = agents, worlds, log   # {WHITE: ..., BLACK: ...}
        self.clock = 0

    def step(self, colour, note=""):
        """One slice of `colour`'s mind in its seat, logged."""
        a, w = self.agents[colour], self.worlds[colour]
        w.actor = NAME[colour]
        wd0, subs0 = len(a.__dict__.get("want_dreams_done", [])), len(a.sub_log)
        a._route = None   # (why.py: which way a move is chosen, recorded by rung4p's player)
        committed_before = bool(a.__dict__.get("committed"))
        fen0, moves0 = w.board.to_fen(), self.moved_count(colour)
        ts = time.time()
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        self.clock += 1
        did = ("waited" if choice is None else "asked the tool" if choice[0] == "ask" else
               f"committed" if choice[0] == "commit" else f"moved {choice[0]}")
        extra = []
        reads = w.__dict__.get("forced_mate_reads", [])
        for state_, x_, side_, uci_ in reads[w.__dict__.get("_fm_logged", 0):]:
            extra.append(f"FORCED MATE in {x_} for {NAME[colour]} ({state_}, after {side_}'s {uci_})")
        w._fm_logged = len(reads)
        mat = w.material() - w.start_material
        prev = w.__dict__.get("_mat_logged", 0) if w.__dict__.get("_mat_game") == len(w.games) else 0
        if colour == WHITE and mat != prev:   # (White's balance, logged from White's seat)
            extra.append(f"material {mat:+d} ({mat - prev:+d})")
        w._mat_logged, w._mat_game = mat, len(w.games)
        if len(a.__dict__.get("want_dreams_done", [])) > wd0:
            extra.append(f"WANT-DREAMED ({a.want_dreams_done[-1][1][:50]})")
        sets = [g for _, g, k in a.sub_log[subs0:] if k == "set"]
        if sets:
            extra.append(f"want set {sets[0][:60]}")
        self.log(f"   s{self.clock} {NAME[colour]:5s} {time.time() - ts:5.1f}s: {note}{did}; half-moves {w.moved}"
                 + ("; " + "; ".join(extra) if extra else ""))
        if self.__dict__.get("why_path") and choice is not None and choice[0] not in ("commit", "ask") \
                and self.moved_count(colour) > moves0:   # the mind moved: its explanation, kept (why.py; the user, 2026-11-17)
            import json
            import why
            route = a.__dict__.get("_route") or (("commit", None) if committed_before or a.__dict__.get("committed") else
                                                 ("experiment", None) if a.__dict__.get("running") or a.__dict__.get("queue") else None)
            try:
                e = why.explain(a, w, choice, route, fen0, NAME[colour], w.moved, self.__dict__.get("profiles", {}).get(colour, ""))
                with open(self.why_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(e) + "\n")
            except Exception as x:   # (an explanation that fails never stops the game)
                self.log(f"   (why: {type(x).__name__}: {x})")
        return choice

    def moved_count(self, colour):
        return sum(1 for x in self.worlds[colour].log if x[2])

    def mirror(self, mover):
        """The move `mover` just made in its seat, played in the other seat as the other side's move."""
        src, dst = self.worlds[mover], self.worlds[not mover]
        label = next(x[1] for x in reversed(src.log) if x[2])
        uci = label.split(" ", 1)[1]
        move = next(m for m in dst.board.legal_moves if m.uci() == uci)
        dst.actor = NAME[mover]
        dst.pend[NAME[mover]] = {}   # (the mover has no mind in this seat: what its move came to isn't kept for it here, as RandomSide)
        dst.act((dst.label(move), dst.ids_at(move.from_square), "present"))
        dst.pend[NAME[mover]] = {}
        dst.actor = NAME[not mover]
        if src.board.to_fen().split()[:4] != dst.board.to_fen().split()[:4]:
            raise RuntimeError(f"the seats are no longer one game: {src.board.to_fen()} vs {dst.board.to_fen()}")

    def sync_end(self):
        """A resignation in one seat is the game's: both seats over, both told."""
        r = next((self.worlds[c].__dict__.get("resigned") for c in (WHITE, BLACK) if self.worlds[c].__dict__.get("resigned")), None)
        for c in (WHITE, BLACK):
            w = self.worlds[c]
            if r and not w.__dict__.get("resigned"):
                w.resigned = r
            w.conclude()

    def over(self):
        """The game's end in either seat: the rules, a resignation, or the half-move cap (first only the rules and resignations: at the
        cap White's seat was set back and moved in a new game while Black's seat still stood in the old one; check_chessduel)."""
        return any(self.worlds[c].over() or self.worlds[c].moved >= self.worlds[c].moves for c in (WHITE, BLACK))

    def play_game(self, cap_slices=20000):
        """One game to its end, both seats set back after it. -> the result string (White's seat's record)."""
        self.align()
        g0 = {c: len(self.worlds[c].games) for c in (WHITE, BLACK)}
        start = self.clock
        while not self.over() and self.clock - start < cap_slices:
            mover = self.worlds[WHITE].board.turn
            n = self.moved_count(mover)
            for _ in range(TURN_STEPS):
                self.step(mover)
                if self.moved_count(mover) > n:
                    self.mirror(mover)
                    self.sync_end()
                    break
        if not self.over():   # (the duel's own safety cap: never expected with the half-move cap)
            for c in (WHITE, BLACK):
                self.worlds[c].moved = self.worlds[c].moves
        while any(len(self.worlds[c].games) == g0[c] for c in (WHITE, BLACK)):   # both minds see the end; both seats set back
            for c in (WHITE, BLACK):
                if len(self.worlds[c].games) == g0[c]:
                    w = self.worlds[c]
                    w.actor = NAME[c]
                    w.pend[NAME[not c]] = {}
                    self.step(c, "game over; ")
            if self.clock - start > cap_slices + 200:
                raise RuntimeError("the seats were not set back")
        # (White's seat can be set back and White move in the same slice, as rung4p's game 10 -> 11, g2g4: that first move stays in
        # White's seat, and is played in the next game's Black seat when that game begins, align(). First it was played here in this
        # game's Black seat: in the league the next game is against another Black mind, and the seats began apart, waiting on each
        # other, 2026-11-17)
        return self.worlds[WHITE].games[-1]

    def align(self):
        """The two seats at one game's start: a Black seat holding moves (a White first move from an earlier pairing, played in it by
        the code before align) is set fresh at the start (fresh_seat); a first move White made as its seat was set back is played in
        Black's seat."""
        wb, ww = self.worlds[BLACK], self.worlds[WHITE]
        if wb.moved:
            self.worlds[BLACK] = wb = fresh_seat(self.agents[BLACK], BLACK)
            self.log(f"   (Black's seat held {wb.__dict__.get('_stale_moves', '?')} move(s) from an earlier pairing: set fresh at the start)")
        if ww.moved > 1:
            raise RuntimeError(f"White's seat is {ww.moved} half-moves into a game at the start")
        if ww.moved == 1:
            self.mirror(WHITE)
            label = next(x[1] for x in reversed(ww.log) if x[2])   # (logged as a move, so the game's log holds every move: watch_league)
            self.log(f"   carried White   0.0s: moved {label}; half-moves 1 (made as its seat was set back after its last game)")
        fw, fb = ww.board.to_fen().split()[:4], wb.board.to_fen().split()[:4]
        if fw != fb:
            raise RuntimeError(f"the seats begin the game apart: {fw} vs {fb}")
