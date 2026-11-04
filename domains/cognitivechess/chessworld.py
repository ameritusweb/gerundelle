"""The chess world: python-chess behind the interface Gerundelle's SovAgent reads (cognitivecode's CodeWorld and
civilization's PotentialWorld are the precedents: a world of its own, no change to the mind).

    objs           every piece by identity (its colour, kind and starting square: 'black_knight_d5'), and 'material'
    states()       object -> what the world makes of it: 'safe', 'attacked' (attacked and defended), 'hanging'
                   (attacked, undefended), 'captured'; material 'even', 'up', 'down' against the start
    invitations()  the legal moves: (move, the piece moved, its state)
    act(inv, hold) the move made, the world's reply (rung 0: none, Black passes), and the diffs '<object>: <from> -> <to>'
    renew()        an episode is one try: the position is set back before the next (never inside an experiment)
    t, horizon, gamma, diffs, still, tree

The plan is chess-sov-plan.md ("The chess world"). My choices (named, to be revised by what the rungs find):
- A piece's state is what the rules make of it, not its square (code rung 0: a state that changed with every push made
  every push "take"). A move that changes nothing a piece is read as reports nothing.
- Principle 0 (civilization PHYSICS.md): in the slice a move lands only the piece moved changes; what it does to
  anything else (the piece taken, material, other pieces now attacked or freed) is seen a slice later. Gerundelle reads
  another object's change in a push's own slice as part of the situation the push met, and would learn "the capture
  wins when the knight is captured".
- The invitation's third part is the piece's state as the mind perceives it, Gerundelle's configuration: its planner
  offers a push only where `<object>_<gerund>` is a fact (Model.actions). First it was fixed ('piece', after the code
  world's CodeWorld.invitations, where a slot's state made every change of state make every fill untried again): no
  configuration was ever a fact, the planner had no actions, and at rung 1 a mind that set and met the sub-want "knight
  hanging" never took the knight. Then it was the piece's safety, and a move was another action when its piece was
  safe or attacked: a mind wanting "Bc8 by a safe bishop" gave up the exchange to make its bishop safe (rung 1, seed 6,
  after the label fix). Now a piece is present or not, and its safety is an object of its own (`safety`): the move's
  configuration is a stable fact, and safety a relation, perceived (the user, 2026-10-30: relations as objects).
- An order seed ranks each move ('042 Rxd5') by a draw keyed on the seed and the move, so ties among equal pushes are not
  broken by the move's name, and a move keeps its rank in every position it is legal in (an experiment's second step
  finds its move again). `last`: moves given the largest rank, the last Gerundelle tries (its untried preparations are
  taken smallest first).
"""
import os
import random
import shutil
from types import SimpleNamespace

import chess
import chess.engine

STOCKFISH = os.environ.get("STOCKFISH") or shutil.which("stockfish")   # only the rungs that use an engine need it


def open_engine():
    if not STOCKFISH:
        raise RuntimeError("This run uses Stockfish: install it on your PATH, or set STOCKFISH to its executable.")
    return chess.engine.SimpleEngine.popen_uci(STOCKFISH)


IDLE = 6   # slices without a move of White's that end an episode begun (a still world: waiting brings nothing)
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen",
        chess.KING: "king"}


class ChessWorld:
    still = True    # nothing moves between the mind's pushes unless it acts (no wind): waiting brings nothing
    gamma = 0.7     # how a push's later effects are discounted (ForceWorld's; Gerundelle reads it)
    horizon = 2     # the move's slice, and the slice its consequences land in (principle 0)

    def __init__(self, fen, name="board", order=None, last=(), reply=None, moves=1, seed=0, imagine=None,
                 engine_depth=6, relations=(), safety=True, sequence=False, clean=False):
        """fen: the puzzle's position, White to move; or several (configurations), one drawn per episode by `seed`.
        reply: the world's answer to White's move: None (Black passes; rung 0), "recapture", or "answer" (a check
        answered, else a recapture). moves: White's moves in an episode. relations: relations perceived as objects of
        their own (rung 1c): a square ('d8': guarded by Black, or open) or 'flight' (the black king has a square to step
        to off its rank, or none); with any, a king's state is safe, checked or mated. safety: a piece is two objects,
        itself (present, captured, absent) and its safety ('<piece>_safety': safe, attacked, hanging; a king's safe,
        checked, mated; none off the board), so a move's configuration is the piece being there (False: one object
        whose state is its safety, as rungs 0-1c first ran). sequence: the positions are taken in order, the next
        after a mate, each naming its own pieces (a new scene names its own: fiction rung 6); otherwise one is drawn
        per episode. A relation 'reply' is what Black's last answer was (none, passed, took, stepped, interposed).
        clean: the relation 'game' reads 'mate' only for a mate with material not down, and 'costly_mate' for one bought
        with material (the user, 2026-10-30: the want as "mate without losing material"; a named choice: the outcome
        perceived whole, so the want stays one fact)."""
        self.fens = [fen] if isinstance(fen, str) else list(fen)
        self.relations, self.safety, self.sequence, self.at = tuple(relations), safety, sequence, 0
        self.clean = clean
        self.events = tuple(r for r in self.relations if r == "reply")   # outcomes, not conditions (SovAgent.facts_now)
        self.last_reply = "none"
        self.name, self.order, self.last, self.reply, self.moves = name, order, set(last), reply, moves
        self.rng = random.Random(seed)
        self.imagined_by, self.engine_depth, self.engine = imagine, engine_depth, None
        self.imagined = 0          # positions imagined (each move of a line not imagined before from that board)
        self._imagined = {}        # (board, line) -> (facts, effects): a line imagined once is remembered
        self.ids = self.named(self.fens[0])
        pieces = list(self.ids.values()) if not sequence else sorted({o for f in self.fens for o in self.named(f).values()})
        self.objs = {o: None for o in pieces + [f"{o}_safety" for o in pieces if safety] + ["material"]
                     + list(self.relations)}
        self.t, self.diffs, self.episodes = 0, [], []
        self.tree = SimpleNamespace(doer=None, kids=[])   # no force tree: nothing is carried (worlds.carried)
        self.reset()

    @staticmethod
    def named(fen):
        return {sq: f"{'white' if p.color else 'black'}_{NAME[p.piece_type]}_{chess.square_name(sq)}"
                for sq, p in chess.Board(fen).piece_map().items()}

    def placed(self, board):
        """Piece identity -> square, in a configuration: the first configuration's names, a piece on the same square
        keeping its name, the rest matched by colour and kind (a bishop elsewhere is the same bishop)."""
        first = chess.Board(self.fens[min(self.at, len(self.fens) - 1) if self.sequence else 0])
        where, left = {}, dict(board.piece_map())
        for sq, o in self.ids.items():
            if left.get(sq) == first.piece_at(sq):
                where[o] = sq
                del left[sq]
        for sq, o in self.ids.items():
            if o not in where:
                sq2 = next((s for s, p in sorted(left.items()) if p == first.piece_at(sq)), None)
                where[o] = sq2   # None: not on the board in this configuration (absent)
                if sq2 is not None:
                    del left[sq2]
        assert not left, f"a piece with no name in {board.fen()}"
        return where

    def reset(self):
        if self.sequence:
            if getattr(self, "mated", False):
                self.at += 1
            k = min(self.at, len(self.fens) - 1)
            self.ids = self.named(self.fens[k])
        else:
            k = 0 if len(self.fens) == 1 else self.rng.randrange(len(self.fens))
        self.config = k
        self.episodes.append(k)
        self.board = chess.Board(self.fens[k])
        self.where = self.placed(self.board)   # piece identity -> its square (None: captured, or absent)
        self.absent = {o for o, sq in self.where.items() if sq is None}
        self.mated, self.last_reply = False, "none"
        self.start_material = self.material()
        self.shown = self.read()   # what the mind perceives: the board read, a slice behind for what follows a move
        self.pending, self.moved, self.idle = {}, 0, 0

    def renew(self):
        """An episode is `moves` of White's moves (an experiment runs on: Gerundelle does not renew inside one): set
        back after them."""
        # or when White has stopped moving: IDLE slices in a row with no move (first an episode waited for White's
        # second move however long, and a mind with nothing worth doing made none: 450 ticks still; rung 1e, seed 4)
        if (self.moved >= self.moves or self.mated or (self.moved and self.idle >= IDLE)) and not self.pending:
            self.reset()
            self.diffs = []

    # ---- reading ----------------------------------------------------------------------------------------------

    def material(self):
        return sum(VALUE[p.piece_type] * (1 if p.color else -1) for p in self.board.piece_map().values())

    def read(self):
        out = {}
        for o, sq in self.where.items():
            if sq is None:
                out[o] = "absent" if o in self.absent else "captured"
                if self.safety:
                    out[f"{o}_safety"] = "none"
                continue
            colour = self.board.piece_at(sq).color
            if self.relations and self.board.piece_at(sq).piece_type == chess.KING:
                checked = bool(self.board.attackers(not colour, sq))
                st = "mated" if (self.mated and not colour) else ("checked" if checked else "safe")
            else:
                attacked = bool(self.board.attackers(not colour, sq))
                defended = bool(self.board.attackers(colour, sq))
                st = "safe" if not attacked else ("attacked" if defended else "hanging")
            if self.safety:
                out[o], out[f"{o}_safety"] = "present", st
            else:
                out[o] = st
        d = self.material() - self.start_material
        out["material"] = "even" if d == 0 else ("up" if d > 0 else "down")
        for r in self.relations:
            out[r] = self.relation(r)
        return out

    def relation(self, r):
        """A relation perceived as an object (rung 1c). A square: 'held' if a black piece stands on it, 'guarded' if a
        black piece attacks it, else 'open'.
        'flight': whether the black king has a square to step to off its own rank, empty and not attacked by White
        ('open'), or none ('none'): the back rank's escape, read by the rules."""
        if r == "reply":
            return self.last_reply
        if r == "game":   # the game, as one object whatever the king is named: on, or mate (clean: costly_mate)
            if not self.mated:
                return "on"
            return "costly_mate" if self.clean and self.material() < self.start_material else "mate"
        if r == "flight":
            k = self.board.king(chess.BLACK)
            if k is None:
                return "none"
            for sq in chess.SquareSet(chess.BB_KING_ATTACKS[k]):
                if chess.square_rank(sq) == chess.square_rank(k):
                    continue
                p = self.board.piece_at(sq)
                if (p is None or p.color == chess.WHITE) and not self.board.attackers(chess.WHITE, sq):
                    return "open"
            return "none"
        sq = chess.parse_square(r)
        p = self.board.piece_at(sq)
        if p is not None and p.color == chess.BLACK:
            return "held"   # a black piece stands on it (first read as 'open' when nothing attacked it: after Rd8
                            # Nxd8 the knight stood on d8, d8 read open, and the sacrifice met the sub-want "d8 open")
        return "guarded" if self.board.attackers(chess.BLACK, sq) else "open"

    def states(self, tree=None):
        return dict(self.shown)

    def label(self, move):
        # without '+' and '#': whether a move checks or mates is what it does, not its name (first the SAN as
        # printed, and at rung 1c Re8 was 'Re8#' where it mated and 'Re8+' where it did not: two actions, nothing
        # to learn about either)
        san = self.board.san(move).rstrip("+#")
        if self.order is None:
            return san
        rank = 999 if san in self.last else random.Random(f"{self.order}:{san}").randrange(999)
        return f"{rank:03d} {san}"

    def invitations(self, tree=None):
        if self.mated:   # the game is over: nothing is on offer, an experiment under way ends, and the episode is set
            return []    # back (first play went on after a mate, and "Re8 mates when the king is mated" was learned)
        out = []
        for m in self.board.legal_moves:
            taken = self.board.piece_at(m.to_square)
            if taken is not None and taken.piece_type == chess.KING:
                continue   # after a pass a king can stand attacked; taking it is not a move
            piece = self.ids_at(m.from_square)
            out.append((self.label(m), piece, self.shown[piece]))
        return sorted(out)

    def answer(self, move):
        """The authored reply to a check (rung 1c, a rule of this world): take the checking piece with the least valuable
        piece that can; else step the king out (the first such move); else interpose with the least valuable piece;
        mated, none. Not in check: the recapture rule."""
        if not self.board.is_check():
            return self.recapture(move)
        legal = list(self.board.legal_moves)
        if not legal:
            return None
        value = lambda m: (VALUE[self.board.piece_at(m.from_square).piece_type] or 99, m.uci())
        checker = move.to_square
        takes = [m for m in legal if m.to_square == checker]
        if takes:
            return min(takes, key=value)
        steps = sorted((m for m in legal if self.board.piece_at(m.from_square).piece_type == chess.KING),
                       key=lambda m: m.uci())
        if steps:
            return steps[0]
        return min(legal, key=value)

    def relations_of(self, inv, fine=True):
        """What a move would meet, read off the board by the rules before it is made (rung 1d's perception, asked for by
        the agent: Params.converge): whether it checks, whether where it lands is guarded (and by a piece or the king
        only, and whether White backs it), whether the black king would have a flight, whether Black could interpose;
        and what is not a cause: its piece's kind, whether it captures, whether it lands on the back rank."""
        try:
            move = self.board.parse_san(inv[0].split(" ", 1)[-1])
        except ValueError:
            return frozenset()
        board = self.board
        piece = board.piece_at(move.from_square)
        out = {f"piece:{NAME[piece.piece_type]}", f"captures:{'yes' if board.is_capture(move) else 'no'}",
               f"lands:{'back-rank' if chess.square_rank(move.to_square) == 7 else 'elsewhere'}"}
        b = board.copy()
        b.push(move)
        check = b.is_check()
        out.add(f"check:{'yes' if check else 'no'}")
        guards = b.attackers(chess.BLACK, move.to_square)
        out.add(f"landing:{'guarded' if guards else 'open'}")
        if fine:
            kind = "none" if not guards else ("king-only" if all(b.piece_at(q).piece_type == chess.KING for q in guards)
                                              else "piece")
            out.add(f"guard:{kind}")
            out.add(f"backed:{'yes' if b.attackers(chess.WHITE, move.to_square) else 'no'}")
        k = b.king(chess.BLACK)
        if k is None:
            return frozenset(out)
        flight = any(b.piece_at(m.from_square).piece_type == chess.KING and m.to_square != move.to_square
                     for m in b.legal_moves) if check else any(
            not b.attackers(chess.WHITE, q) and (b.piece_at(q) is None or b.piece_at(q).color == chess.WHITE)
            for q in chess.SquareSet(chess.BB_KING_ATTACKS[k]))
        out.add(f"flight:{'open' if flight else 'none'}")
        between = chess.SquareSet(chess.between(move.to_square, k))
        block = check and any(m.to_square in between and b.piece_at(m.from_square).piece_type != chess.KING
                              for m in b.legal_moves)
        out.add(f"interpose:{'possible' if block else 'none'}")
        return frozenset(out)

    def recapture(self, move):
        """The authored reply (chess-sov-plan.md rung 1, a rule of this world as the wind is): Black takes on the square
        just taken, if it can, with its least valuable attacker; otherwise it passes."""
        if self.board.peek().to_square != move.to_square or not self.last_capture:
            return None
        legal = [m for m in self.board.legal_moves if m.to_square == move.to_square]
        if not legal:
            return None
        return min(legal, key=lambda m: (VALUE[self.board.piece_at(m.from_square).piece_type] or 99, m.uci()))

    # ---- imagining (chess-sov-plan.md "Lookahead"; Gerundelle's Params.imagine) ------------------------------

    def imagine(self, line):
        """A line of White's pushes (their labels) imagined from the board now by the rules, the other side's reply to
        each from `imagined_by`: 'stockfish' (its word: told), 'rules' (none: Black passes). What the last push of the
        line leaves: (facts, the changes it made) or None if a push is not a move there. The world itself is not
        changed. None when this world does not imagine."""
        if self.imagined_by is None:
            return None
        key = (self.board.fen(), tuple(line))
        if key in self._imagined:
            return self._imagined[key]
        saved = (self.board.copy(), dict(self.where), getattr(self, "last_capture", False))
        try:
            before = self.read()
            for k, label in enumerate(line):
                try:
                    move = self.board.parse_san(label.split(" ", 1)[-1])
                except ValueError:
                    out = None
                    break
                if k == len(line) - 1:
                    before = self.read()
                self.play(move)
                answer = self.engine_reply() if self.imagined_by == "stockfish" else None
                if answer is not None:
                    self.play(answer)
                else:
                    self.board.push(chess.Move.null())
            else:
                after = self.read()
                out = (frozenset(f"{o}_{st}" for o, st in after.items()),
                       frozenset(f"{o}_{st}" for o, st in after.items() if st != before[o]))
        finally:
            self.board, self.where, self.last_capture = saved
        self.imagined += 1
        self._imagined[key] = out
        return out

    def engine_reply(self):
        """Stockfish's move for Black in the imagined position, at a low fixed depth (None: no legal move)."""
        if self.board.is_game_over():
            return None
        if self.engine is None:
            self.engine = open_engine()
        board = chess.Board(self.board.fen())   # the position only (its history holds the passes)
        board.turn = chess.BLACK
        if not board.is_valid():
            return None
        return self.engine.play(board, chess.engine.Limit(depth=self.engine_depth)).move

    def close(self):
        if self.engine is not None:
            self.engine.quit()
            self.engine = None

    def ids_at(self, sq):
        return next(o for o, s in self.where.items() if s == sq)

    # ---- acting -----------------------------------------------------------------------------------------------

    def play(self, move):
        """A move on the board, the pieces' identities carried with it."""
        mover = self.ids_at(move.from_square)
        taken_sq = move.to_square
        if self.board.is_en_passant(move):
            taken_sq = move.to_square + (-8 if self.board.turn else 8)
        taken = next((o for o, s in self.where.items() if s == taken_sq), None)
        self.last_capture = taken is not None
        if self.board.is_castling(move):
            rook_from, rook_to = ((chess.H1, chess.F1) if self.board.is_kingside_castling(move) else (chess.A1, chess.D1)) \
                if self.board.turn else \
                ((chess.H8, chess.F8) if self.board.is_kingside_castling(move) else (chess.A8, chess.D8))
            self.where[self.ids_at(rook_from)] = rook_to
        self.board.push(move)
        if taken is not None:
            self.where[taken] = None
        self.where[mover] = move.to_square
        return mover

    def act(self, inv=None, hold=False):
        diffs = []
        for o, to in sorted(self.pending.items()):   # what the last move set going lands now
            diffs.append(f"{o}: {self.shown[o]} -> {to}")
            self.shown[o] = to
        self.pending = {}
        self.idle = 0 if inv is not None else self.idle + 1
        if inv is not None:
            san = inv[0].split(" ", 1)[-1]
            move = self.board.parse_san(san)
            mover = self.play(move)
            self.mated = self.mated or self.board.is_checkmate()
            answer = (self.recapture(move) if self.reply == "recapture" else
                      self.answer(move) if self.reply == "answer" else None)
            if answer is not None:
                was_check = self.board.is_check()
                k = self.board.piece_at(answer.from_square).piece_type == chess.KING
                self.last_reply = ("took" if answer.to_square == move.to_square else "stepped" if (was_check and k)
                                   else "interposed" if was_check else "moved")
                self.play(answer)
            else:
                self.last_reply = "passed"
                self.board.push(chess.Move.null())   # Black passes: White to move again (an experiment's next step)
            self.moved += 1
            now = self.read()
            if now[mover] != self.shown[mover]:   # the move's own slice: only the piece moved
                diffs.append(f"{mover}: {self.shown[mover]} -> {now[mover]} (to {chess.square_name(move.to_square)})")
                self.shown[mover] = now[mover]
            self.pending = {o: s for o, s in now.items() if s != self.shown[o]}
        self.diffs = diffs
        self.t += 1
        return diffs


# Rung 0's puzzle: White to move. The knight on d5 hangs to the rook; the bishop on f6 is attacked by the bishop on b2
# but defended twice (the decoy); the rest are safe. Two moves win material with no reply: Rxd5 and Bxf6.
RUNG0 = "6k1/5ppp/5b2/3n4/8/8/1B3PPP/2KR4 w - - 0 1"

# Rung 1's two configurations (chess-sov-plan.md rung 1), drawn per episode: they differ in one fact, the knight on d5
# defended (by the bishop on b7) or hanging (the bishop on c8). Black recaptures. Defended, Rxd5 loses the exchange
# (Bxd5); the defender can be traded off (Bxb7 Rxb7, even), and then Rxd5 wins the knight: a two-move combination.
# Undefended, Rxd5 wins at once.
RUNG1_DEFENDED = "1r4k1/1b3ppp/Bp6/1P1n4/8/8/5PPP/3R2K1 w - - 0 1"
RUNG1_HANGING = "1rb3k1/5ppp/Bp6/1P1n4/8/8/5PPP/3R2K1 w - - 0 1"
RUNG1 = (RUNG1_DEFENDED, RUNG1_HANGING)


def backrank(knight, bishop, luft):
    """Rung 1c's configurations: White Kg1, rooks d1 and e1, pawns f2 g2 h2; Black Kg8, pawns f7 g7 and the h-pawn;
    a black knight on b7 (guarding d8), a black bishop on b5 (guarding e8, and so able to interpose on e8 against a check
    from d8), and the h-pawn on h6 (luft: the king can
    step to h7) or h7. Rd8 mates only with d8 and e8 open and no flight; Re8 only with e8 open and no flight."""
    b = chess.Board("6k1/5pp1/8/8/8/8/5PPP/3RR1K1 w - - 0 1")
    b.set_piece_at(chess.H6 if luft else chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
    if knight:
        b.set_piece_at(chess.B7, chess.Piece(chess.KNIGHT, chess.BLACK))
    if bishop:
        b.set_piece_at(chess.B5, chess.Piece(chess.BISHOP, chess.BLACK))
    return b.fen()


# The first configuration holds every piece (names come from it): knight, bishop, the h-pawn on h7.
RUNG1C = tuple(backrank(n, b, l) for n in (True, False) for b in (True, False) for l in (False, True))
RUNG1C_RELATIONS = ("d8", "e8", "flight")


class DuelWorld(ChessWorld):
    """Rung 3: two minds on one board (civilization P4's way: each round every mind takes one step, `actor` naming it).

    - Turns: only the side to move is offered moves (the mind whose `actor` is that side); no authored reply.
    - Each mind perceives the board as it stands; what a move does is delivered to the mind that made it, in that mind's
      next slice (P4: "a mind must perceive the continuation of what it set going, or it credits others with its own
      deeds"); in the move's own slice only the piece moved changes (principle 0).
    - A side's standing (`standing_white`, `standing_black`: up, even, down, from that side's view) is the material balance
      read when its turn comes round again, after the other side has answered: delivered to it as what its own last move
      came to. A want judged at once ("material up") would be met by a capture the other side then takes back.
    - What a move would meet (`relations_of`) is read from the side to move's point of view.
    - An episode is `half_moves` moves (both sides), or ends at mate, or after IDLE slices with no move.
    - holding (opt-in, 2026-10-31): a side's `holding_<side>` is 'kept' while its standing is even or up, 'lost' while it
      is down, read and delivered with the standing. A want of 'kept' is met by a change back from lost: winning back
      what was taken, a defender's want (the user's sketch: Black wants "material not down"; one fact cannot say "even
      or up"). Off, the objects are not there, and rung 3's first runs stand as they were.
    - owned (opt-in, 2026-10-31): a captured piece leaves view (states() no longer has it or its safety), so a mind whose
      pieces are its given territory (Territory.given) reads a capture as a loss. Off, a captured piece stays in view.
    - `side_pieces(side)`: the pieces a side starts the episode with (its given territory).
    """
    SIDES = {"White": chess.WHITE, "Black": chess.BLACK}

    def __init__(self, fen, order=None, seed=0, half_moves=4, holding=False, owned=False):
        self.holding, self.owned = holding, owned
        super().__init__(fen, order=order, seed=seed, reply=None, moves=half_moves, relations=())
        self.objs.update({"standing_white": None, "standing_black": None})
        if holding:
            self.objs.update({"holding_white": None, "holding_black": None})
        self.actor = "White"
        self.horizon = 3   # a mind's watch spans the other side's answer

    def reset(self):
        super().reset()
        self.standing = {"White": "even", "Black": "even"}
        self.pend = {"White": {}, "Black": {}}
        self.has_moved = set()

    def side_pieces(self, side):
        return {o for o in self.ids.values() if o.startswith(side.lower() + "_")}

    def balance(self, side):
        d = self.material() - self.start_material
        d = d if side == "White" else -d
        return "even" if d == 0 else ("up" if d > 0 else "down")

    def states(self, tree=None):
        out = self.read()
        if self.owned:   # a captured piece leaves view (and its safety with it): what a side owned and lost is gone,
            for o in [o for o, st in out.items() if st == "captured"]:   # as a toy carried off is (fiction rung 5);
                out.pop(o)                                                 # its capture is still delivered as a change
                out.pop(f"{o}_safety", None)
        out["standing_white"], out["standing_black"] = self.standing["White"], self.standing["Black"]
        if self.holding:
            out["holding_white"], out["holding_black"] = self.held(self.standing["White"]), self.held(self.standing["Black"])
        return out

    @staticmethod
    def held(standing):
        return "lost" if standing == "down" else "kept"

    def restand(self, side, new):
        """A side's standing read anew (and its holding): the changes are delivered to it as what its own last move came
        to, if it has moved this episode."""
        old = self.standing[side]
        if new == old:
            return
        if side in self.has_moved:
            self.pend[side][f"standing_{side.lower()}"] = (old, new)
            if self.holding and self.held(old) != self.held(new):
                self.pend[side][f"holding_{side.lower()}"] = (self.held(old), self.held(new))
        self.standing[side] = new

    def invitations(self, tree=None):
        if self.mated or self.board.is_game_over() or self.SIDES.get(self.actor) != self.board.turn:
            return []
        out = []
        for m in self.board.legal_moves:
            piece = self.ids_at(m.from_square)
            out.append((self.label(m), piece, "present"))
        return sorted(out)

    def renew(self):
        if (self.moved >= self.moves or self.mated or (self.moved and self.idle >= IDLE)) \
                and not any(self.pend.values()):
            self.reset()
            self.diffs = []

    def playable(self, inv):
        """Whether a push can be made now: this side's turn, the game on, and its move legal for its own piece."""
        if self.SIDES.get(self.actor) != self.board.turn or self.mated or self.board.is_game_over():
            return False
        try:
            move = self.board.parse_san(inv[0].split(" ", 1)[-1])
        except ValueError:
            return False
        return self.where.get(inv[1]) == move.from_square

    def act(self, inv=None, hold=False):
        me = self.actor
        if inv is not None and inv[0] != "pass" and not self.playable(inv):
            # the world pushes back (2026-11-01): a move not on offer here (from another position, still in the mind's
            # attention) is tried and nothing happens: a slice with no move, and nothing delivered in it (what the side's
            # last move came to waits for its next slice, or the tried push would be credited with it). First it
            # raised: no mind could try one
            self.idle += 1
            self.diffs = []
            self.t += 1
            return []
        # what my last move came to, in a slice of mine that is not a move (in a move's own slice only the piece moved
        # changes: what is still undelivered then is old news, perceived on the board anyway)
        diffs = [] if inv is not None else [f"{o}: {a} -> {b}" for o, (a, b) in sorted(self.pend[me].items())]
        self.pend[me] = {}
        self.idle = 0 if inv is not None else self.idle + 1
        if inv is not None and inv[0] == "pass":   # a scripted side's pass (rung 3's authored Black)
            self.board.push(chess.Move.null())
            self.moved += 1
            self.has_moved.add(me)
            nxt = "White" if self.board.turn == chess.WHITE else "Black"
            self.restand(nxt, self.balance(nxt))
            self.diffs = diffs
            self.t += 1
            return diffs
        if inv is not None:
            move = self.board.parse_san(inv[0].split(" ", 1)[-1])
            before = self.read()
            mover = self.play(move)
            self.mated = self.board.is_checkmate()
            self.moved += 1
            self.has_moved.add(me)
            after = self.read()
            if after[mover] != before[mover]:
                diffs.append(f"{mover}: {before[mover]} -> {after[mover]} (to {chess.square_name(move.to_square)})")
            for o in after:   # the rest, a slice later, to me
                if o != mover and after[o] != before[o]:
                    self.pend[me][o] = (before[o], after[o])
            nxt = "Black" if self.board.turn == chess.BLACK else "White"   # whose turn it now is: its standing, read
            self.restand(nxt, self.balance(nxt))                             # now, is what its last move came to
                                                                             # (none delivered before its first move)
        self.diffs = diffs
        self.t += 1
        return diffs

    def relations_of(self, inv, fine=True):
        """What a move would meet, from the side to move's point of view (ChessWorld.relations_of, colour-relative)."""
        try:
            move = self.board.parse_san(inv[0].split(" ", 1)[-1])
        except ValueError:
            return frozenset()
        board, own = self.board, self.board.turn
        opp = not own
        piece = board.piece_at(move.from_square)
        back = 7 if own == chess.WHITE else 0
        out = {f"piece:{NAME[piece.piece_type]}", f"captures:{'yes' if board.is_capture(move) else 'no'}",
               f"lands:{'back-rank' if chess.square_rank(move.to_square) == back else 'elsewhere'}"}
        b = board.copy()
        b.push(move)
        check = b.is_check()
        out.add(f"check:{'yes' if check else 'no'}")
        guards = b.attackers(opp, move.to_square)
        out.add(f"landing:{'guarded' if guards else 'open'}")
        kind = "none" if not guards else ("king-only" if all(b.piece_at(q).piece_type == chess.KING for q in guards)
                                          else "piece")
        out.add(f"guard:{kind}")
        out.add(f"backed:{'yes' if b.attackers(own, move.to_square) else 'no'}")
        return frozenset(out)
