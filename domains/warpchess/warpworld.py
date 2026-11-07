"""Warp 1 Chess behind the interface Gerundelle's SovAgent reads (cognitivechess/chessworld.py is the precedent). The rules are the user's engine, WarpOneChess/board.py.

    objs           every piece by identity ('black_knight_Ld5'), its safety ('<piece>_safety'), and 'material'
    states()       a piece 'present' or 'captured'; its safety 'safe', 'attacked', 'hanging'; material 'even', 'up', 'down'
    invitations()  the legal moves, flips included: (label, the piece moved, its state)
    act(inv, hold) the move, Black passing; in its own slice only the piece moved can change, and what it does to anything else lands a slice later (principle 0)
    renew()        an episode is one try: the position is set back, never in the middle of an experiment

A move not on offer does nothing: the world pushes back. Piece values appear only to read material, the want's own fact. They never reach the mind as values.
"""
import os
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, os.environ.get("WARP", "E:/vscode/warponechess"))
from WarpOneChess.board import WarpBoard  # noqa: E402
from WarpOneChess.move import BLACK, PIECE_VALUES, TOTAL_SQUARES, WHITE, flip_square, square_file, square_name, square_rank, square_side  # noqa: E402

NAMES = {1: "pawn", 2: "knight", 3: "bishop", 4: "rook", 5: "queen", 6: "king", 7: "crab"}

# Rung 0: White Kc1 Rd1 Bb2, pawns f2 g2 h2. Black's knight on d5 hangs to the rook, and its bishop on f6 is attacked by the bishop on b2 but defended by the knight on e4. Black's king is on the other board.
RUNG0 = "8/5b2/3n4/4n3/8/1B3PPP/2KR4|||8/8/8/8/8/8/4k3 w - - 0 1"

# Rung 1: Black's knight on d4 and king on e1, on the other board. From d6 the rook can flip and take; from d3 a forward flip isn't allowed, so it must advance first.
RUNG1_ONE = "8/3R4/8/8/8/5PPP/2K5|||8/8/8/3n4/8/8/4k3 w - - 0 1"
RUNG1_TWO = "8/8/8/8/3R4/5PPP/2K5|||8/8/8/3n4/8/8/4k3 w - - 0 1"
# Rung 2: as RUNG1_TWO, with a Black bishop on a6. From d6 the rook presses both the knight and the bishop across the boards: Black can save one.
RUNG2 = "8/8/8/8/3R4/5PPP/2K5|||8/b7/8/3n4/8/8/4k3 w - - 0 1"
RUNG2B = "8/8/8/8/3R4/5PPP/2K5|||8/8/b7/3n4/8/8/k7 w - - 0 1"   # RUNG2 with Black's bishop on a5 and king on a1: neither side can capture on its first move (find_rung2b.py)
IDLE = 6   # slices with no move that end an episode already begun
FILE_PRESSED = 3   # squares of a file a side must press for the file to be under its pressure (my choice)



def rehash(board):
    """After setting a board's turn or en passant square directly: the engine caches legal moves by its Zobrist hash, which only push and pop keep up to date. Without this, a board turned to the other side is served the first side's moves."""
    board._hash = board._compute_hash()

class WarpWorld:
    still = True    # nothing moves between the mind's pushes unless it acts
    gamma = 0.7
    horizon = 2     # the move's slice, and the slice its consequences land in

    def __init__(self, fen, seed=0, name="warp", moves=1, forces=False, reply=None):
        """forces: read each piece's doing off the forces, and pressure on the files (rung 1b). Off, rungs 0 and 1 as they ran."""
        self.fen, self.seed, self.name, self.moves, self.forces, self.reply = fen, seed, name, moves, forces, reply
        self.reply_rng = random.Random(7000 + seed)
        board = WarpBoard.from_fen(fen)
        self.ids = {sq: f"{'white' if board.colors[sq] else 'black'}_{NAMES[board.pieces[sq]]}_{square_name(sq)}"
                    for sq in range(TOTAL_SQUARES) if board.pieces[sq]}
        if forces:
            files = [f"file_{b}{f}" for b in "LR" for f in "abcdefgh"]
            self.objs = {o: None for o in list(self.ids.values()) + [f"{o}_exerting" for o in self.ids.values()]
                         + [f"{o}_bearing" for o in self.ids.values()] + [f"{o}_unique" for o in self.ids.values()] + files + ["material"]}
        else:
            self.objs = {o: None for o in list(self.ids.values()) + [f"{o}_safety" for o in self.ids.values()] + ["material"]}
        self.tree = SimpleNamespace(doer=None, kids=[])
        self.t, self.diffs, self.log = 0, [], []   # log: (tick, label, on offer, material after)
        self.reset()

    def reset(self):
        self.captured_by = {}   # piece -> what it has captured this game: its for good
        self.board = WarpBoard.from_fen(self.fen)
        self.where = {o: sq for sq, o in self.ids.items()}
        self.start_material = self.material()
        self.shown = self.read()
        self.pending, self.moved, self.idle = {}, 0, 0

    def renew(self):
        if (self.moved >= self.moves or (self.moved and self.idle >= IDLE)) and not self.pending:
            self.reset()
            self.diffs = []

    def material(self):
        return sum(PIECE_VALUES[self.board.pieces[sq]] * (1 if self.board.colors[sq] else -1) for sq in range(TOTAL_SQUARES) if self.board.pieces[sq])

    def pressure(self, colour):
        """The squares a side's pieces put a force on: square -> the squares the force comes from. A move that can't capture exerts none."""
        b = self.board.copy()
        b.turn = colour; rehash(b)
        b.en_passant = -1; rehash(b)
        out = {}
        for m in b.legal_moves:
            kind = b.pieces[m.from_square]
            d_file, d_rank = abs(square_file(m.from_square) - square_file(m.to_square)), abs(square_rank(m.from_square) - square_rank(m.to_square))
            if kind == 1 and d_file == 0:       # a pawn's push
                continue
            if kind in (6, 7) and (d_file == 2 or d_rank == 2) and (d_file == 0 or d_rank == 0):   # a king's or crab's jump
                continue
            out.setdefault(m.final_square, set()).add(m.from_square)
        return out

    def read_forces(self):
        white, black = self.pressure(WHITE), self.pressure(BLACK)
        press = {WHITE: white, BLACK: black}
        out = {}
        for o, sq in self.where.items():
            out[o] = "present" if sq is not None else "captured"
            if sq is None:
                continue
            mine = self.board.colors[sq]
            enemy = press[not mine]
            on_it = sq in enemy
            guarded = self.board.is_attacked_by(sq, mine)
            out[f"{o}_bearing"] = "free" if not on_it else "pressed" if guarded else "hanging"
            hits = any(sq in sources and self.board.pieces[target] and self.board.colors[target] != mine for target, sources in press[mine].items())
            out[f"{o}_exerting"] = "pressing" if hits else "idle"
        for o, sq in self.where.items():   # what a piece alone presses: uniqueness, a form of ownership; a capture owns for good
            if sq is None:
                continue
            colour = self.board.colors[sq]
            side = press[colour]
            mine = [t for t, sources in side.items() if sq in sources and self.board.pieces[t] and self.board.colors[t] != colour]
            out[f"{o}_unique"] = "owns" if self.captured_by.get(o) else ("alone" if any(len(side[t]) == 1 for t in mine) else "shared") if mine else "none"
        for side, board in ((0, "L"), (1, "R")):
            for f, name in enumerate("abcdefgh"):
                squares = {sq for sq in range(TOTAL_SQUARES) if square_side(sq) == side and square_file(sq) == f}
                w, k = len(squares & set(white)) >= FILE_PRESSED, len(squares & set(black)) >= FILE_PRESSED
                out[f"file_{board}{name}"] = "contested" if w and k else "white" if w else "black" if k else "open"
        m = self.material() - self.start_material
        out["material"] = "up" if m > 0 else "down" if m < 0 else "even"
        return out

    def read(self):
        if self.forces:
            return self.read_forces()
        out = {}
        for o, sq in self.where.items():
            out[o] = "present" if sq is not None else "captured"
            if sq is None:
                continue
            mine = self.board.colors[sq]
            if self.board.is_attacked_by(sq, not mine):
                out[f"{o}_safety"] = "attacked" if self.board.is_attacked_by(sq, mine) else "hanging"
            else:
                out[f"{o}_safety"] = "safe"
        m = self.material() - self.start_material
        out["material"] = "up" if m > 0 else "down" if m < 0 else "even"
        return out

    def states(self, tree=None):
        return dict(self.shown)

    def label(self, move):
        rank = random.Random(f"{self.seed}:{move.uci()}").randrange(1000)
        return f"{rank:03d} {move.uci()}"

    def offers(self):
        """The moves on offer now: label -> move. A game that's over offers none."""
        if self.board.turn != WHITE or self.board._king_sq[BLACK] < 0 or self.board._king_sq[WHITE] < 0:
            return {}
        return {self.label(m): m for m in self.board.legal_moves}

    def invitations(self, tree=None):
        if self.moved >= self.moves:   # the episode's tries are made: nothing more is on offer until it's set back
            return []
        out = []
        for label, move in sorted(self.offers().items()):
            mover = self.ids_at(move.from_square)
            out.append((label, mover, self.shown[mover]))
        return out

    def ids_at(self, sq):
        return next(o for o, s in self.where.items() if s == sq)

    def play(self, move):
        """A move on the board, the pieces' identities carried with it. The piece's landing square is read from the board, because a forced flip can carry it past the move's own final square. Anything no longer on its square has been taken, which covers captures, flips onto a piece, and forced flips."""
        mover = self.ids_at(move.from_square)
        colour = self.board.colors[move.from_square]
        kinds = {o: (self.board.pieces[s], self.board.colors[s]) for o, s in self.where.items() if s is not None}
        before = {sq for sq in range(TOTAL_SQUARES) if self.board.pieces[sq]}
        before_where = dict(self.where)
        final = move.final_square
        self.board.push(move)
        now = {sq for sq in range(TOTAL_SQUARES) if self.board.pieces[sq]}
        fresh = [sq for sq in now - before if self.board.colors[sq] == colour]
        if final in fresh or flip_square(final) in fresh:
            landed = final if final in fresh else flip_square(final)
        elif fresh:
            landed = fresh[0]
        else:   # it landed where something stood: the move's square, or that square's other side after a forced flip
            options = [sq for sq in (final, flip_square(final)) if self.board.pieces[sq] and self.board.colors[sq] == colour and sq != move.from_square]
            landed = options[0] if options else final
        for o, sq in list(self.where.items()):
            if sq is None or o == mover:
                continue
            if sq == landed or (self.board.pieces[sq], self.board.colors[sq]) != kinds[o]:
                self.where[o] = None
                if kinds[o][1] != colour:   # taken from the other side: the mover's own for good
                    self.captured_by.setdefault(mover, []).append(o)
        self.where[mover] = landed if self.board.pieces[landed] else None
        # a piece carried along by the move, as a rook is by castling, isn't taken: it's the piece of its kind that left its square as another appeared
        # squares where a piece of the mover's colour appeared, or replaced another (the engine's castling moves the rook
        # onto whatever stands on its square, even with no castling rights: rung 4, a king's jump e1-g1)
        before_kind = {sq: kinds[o] for o, sq in before_where.items() if sq is not None and o in kinds}
        appeared = [sq for sq in range(TOTAL_SQUARES) if self.board.pieces[sq] and self.board.colors[sq] == colour
                    and before_kind.get(sq) != (self.board.pieces[sq], self.board.colors[sq])]
        for sq in appeared:
            if sq != landed:
                carried = next((o for o, was in before_where.items() if o != mover and self.where[o] is None and was is not None
                                and (was not in now or before_kind.get(was) != (self.board.pieces[was], self.board.colors[was]))
                                and kinds.get(o) == (self.board.pieces[sq], self.board.colors[sq])), None)
                if carried:
                    self.where[carried] = sq
        return mover

    def black_safety(self):
        """Black's reply when reply='escape': each of its pieces wants safety. If any is hanging, one of them moves to a square where nothing presses it; otherwise Black passes."""
        if self.board._king_sq[BLACK] < 0 or self.board._king_sq[WHITE] < 0:
            return None
        self.board.turn = BLACK; rehash(self.board)
        self.board.en_passant = -1; rehash(self.board)
        white = self.pressure(WHITE)
        hanging = [sq for o, sq in sorted(self.where.items()) if sq is not None and not self.board.colors[sq] and sq in white and not self.board.is_attacked_by(sq, BLACK)]
        moves = self.board.legal_moves
        if not moves:
            self.board.turn = WHITE; rehash(self.board)
            return None
        if not hanging:
            self.board.turn = WHITE; rehash(self.board)
            return None
        sq = self.reply_rng.choice(hanging)
        own = [m for m in moves if m.from_square == sq] or moves
        safe = []
        for m in own:
            b = self.board.copy()
            b.push(m)
            keep = self.board
            self.board = b
            ok = m.final_square not in self.pressure(WHITE)
            self.board = keep
            if ok:
                safe.append(m)
        move = self.reply_rng.choice(sorted(safe or own, key=lambda m: m.uci()))
        self.play(move)
        self.board.turn = WHITE; rehash(self.board)
        return move

    def pass_black(self):
        if self.board._king_sq[BLACK] >= 0:
            self.board.turn = WHITE; rehash(self.board)
            self.board.en_passant = -1; rehash(self.board)

    def act(self, inv=None, hold=False):
        diffs = []
        for o, to in sorted(self.pending.items()):
            diffs.append(f"{o}: {self.shown.get(o)} -> {to}")
            self.shown[o] = to
        self.pending = {}
        self.idle = 0 if inv is not None else self.idle + 1
        if inv is not None:
            move = None if self.moved >= self.moves else self.offers().get(inv[0])
            if move is not None and self.ids_at(move.from_square) == inv[1]:
                mover = self.play(move)
                if self.reply == "escape":
                    self.black_safety()
                else:
                    self.pass_black()
                self.moved += 1
                now = self.read()
                if now[mover] != self.shown[mover]:
                    diffs.append(f"{mover}: {self.shown[mover]} -> {now[mover]}")
                    self.shown[mover] = now[mover]
                self.pending = {o: s for o, s in now.items() if s != self.shown.get(o)}
                self.log.append((self.t, inv[0], True, now["material"]))
            else:
                self.log.append((self.t, inv[0], False, None))
        self.diffs = diffs
        self.t += 1
        return diffs
