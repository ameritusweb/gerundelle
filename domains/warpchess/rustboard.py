"""Warp 1 Chess on the Rust board alone (the user, 2026-11-14: "it needs to only use the rust board").

The Rust board (`warp_board`, the engine's rust_board, with the castling fix of 2026-11-14) behind the interface this domain used from
the Python engine (`WarpOneChess.board.WarpBoard`, `WarpOneChess.move`): the same move objects and names (`La2Lb4=Rb4`), square
helpers and constants, and a board with the fields and methods read here. The Python engine is no longer needed.

- The board's state is the Rust board's. Its pieces, colours and origin sides are read from its arrays once per position (an empty
  square: piece 0, colour None, origin -1); turn, castling rights, en passant square and clocks are read and set on it directly (its
  setters recompute its hash, so the Python engine's rehash() after a write is a no-op here). A piece set or taken away, through
  set_piece_at or the arrays, is set on it square by square (set_square).
- The kings' squares are read off the pieces (the Python engine's _king_sq could be stale after a king was taken; plans.py).
- Legal moves come as tuples, each made into a WarpMove once (the same move is the same object).
- Speed (2026-11-14): the first version read every field from the FEN and rebuilt the board from a FEN on every write; 15 slices of
  rung 4p took 15.7 s a slice under the profiler, 104 s of it in reading the FEN. The Rust board's setters, arrays and move tuples
  were added for this (rust_board/src/lib.rs), and so were press_map and reach, the pressure plans.py and the world read (their
  Python readings stay as plans.press_py, plans.reach_py and WarpWorld.pressure_py; check_rustboard.py checks they agree). The same
  15 slices, the same game: 3.9 s a slice on the Python engine (with the Rust board for plans.py's legal moves), 7.8 s with the first
  version, 3.3 s with the setters, 1.9 s with press_map and reach.
- Pickled as its FEN (the Rust board can't be pickled; checkpoints pickle the world). A move history isn't kept across a pickle.
check_rustboard.py checks it against the Python engine, field by field, on random positions.
"""
from dataclasses import dataclass
from typing import Optional

import warp_board as _wb

WHITE, BLACK = True, False
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, CRAB = 1, 2, 3, 4, 5, 6, 7
PIECE_NAMES = {PAWN: "P", KNIGHT: "N", BISHOP: "B", ROOK: "R", QUEEN: "Q", KING: "K", CRAB: "C"}
PIECE_FROM_CHAR = {v: k for k, v in PIECE_NAMES.items()}
PIECE_VALUES = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 0, CRAB: 3}
NUM_PIECE_TYPES = 7
BOARD_FILES, BOARD_RANKS = 8, 7
SQUARES_PER_SIDE, TOTAL_SQUARES = 64, 128
LEFT, RIGHT = 0, 1
NO_FLIP, PRE_FLIP, POST_FLIP = 0, 1, 2
FILE_NAMES, RANK_NAMES = "abcdefgh", "1234567"


def square(side, file, rank):
    return side * 64 + rank * 8 + file


def square_side(sq):
    return sq >> 6


def square_file(sq):
    return sq & 7


def square_rank(sq):
    return (sq >> 3) & 7


def flip_square(sq):
    return sq ^ 64


def is_playable(sq):
    return square_rank(sq) < BOARD_RANKS


def square_name(sq):
    return f"{'L' if square_side(sq) == LEFT else 'R'}{chr(ord('a') + square_file(sq))}{square_rank(sq) + 1}"


def square_from_name(name):
    return square(LEFT if name[0] == "L" else RIGHT, ord(name[1]) - ord("a"), int(name[2]) - 1)


@dataclass(frozen=True, slots=True)
class WarpMove:
    """A move: from_square, to_square, promotion, flip_type (NO_FLIP, PRE_FLIP, POST_FLIP), flip_from, flip_to."""
    from_square: int
    to_square: int
    promotion: Optional[int] = None
    flip_type: int = NO_FLIP
    flip_from: int = -1
    flip_to: int = -1

    @property
    def final_square(self):
        return self.flip_to if self.flip_type == POST_FLIP else self.to_square

    def uci(self):
        f, t = square_name(self.from_square), square_name(self.to_square)
        promo = PIECE_NAMES.get(self.promotion, "").lower() if self.promotion else ""
        if self.flip_type == PRE_FLIP:
            return f"{f}>{square_name(self.flip_to)}{t}{promo}"
        if self.flip_type == POST_FLIP:
            return f"{f}{t}={square_name(self.flip_to)}{promo}"
        return f"{f}{t}{promo}"

    def __repr__(self):
        return f"WarpMove({self.uci()})"


def _to_rust(m):
    return _wb.PyWarpMove(m.from_square, m.to_square, m.promotion, int(m.flip_type), m.flip_from, m.flip_to)


_MOVES = {}   # a move's tuple -> its WarpMove (made once)


def _move(t):
    m = _MOVES.get(t)
    if m is None:
        m = _MOVES[t] = WarpMove(t[0], t[1], t[2] or None, t[3], t[4], t[5])
    return m


class _Field(list):
    """A board's pieces, colours or origin sides: read as a list; a write sets that square on the board."""
    __slots__ = ("_board",)

    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        self._board._square_written(k)


_CACHED = ("pieces", "colors", "origin_side", "_king_sq")


class WarpBoard:
    WK, WQ, BK, BQ = 1, 2, 4, 8
    _legal_cache = {}   # (the Python engine's legal-move cache, cleared by checks; the Rust board has none to clear)

    def __init__(self, rust=None):
        self._rb = rust if rust is not None else _wb.PyWarpBoard()

    # ---- made from the Rust board ----------------------------------------------------------------------------------------------
    @classmethod
    def from_fen(cls, fen):
        return cls(_wb.PyWarpBoard.from_fen(fen))

    @classmethod
    def starting_position(cls):
        return cls(_wb.PyWarpBoard.starting_position())

    def to_fen(self):
        return self._rb.to_fen()

    def copy(self):
        return WarpBoard(self._rb.copy())

    def __reduce__(self):
        return (WarpBoard.from_fen, (self.to_fen(),))

    def _moved(self):
        """The position changed: its arrays and kings are read again when next asked for."""
        d = self.__dict__
        for k in _CACHED:
            d.pop(k, None)

    def __getattr__(self, name):   # (only for what isn't read yet: the arrays of this position, and the kings read off them)
        if name in ("pieces", "colors", "origin_side"):
            p, c, o = self._rb.arrays()
            pieces, colors, origin = _Field(p), _Field([c[i] if p[i] else None for i in range(TOTAL_SQUARES)]),                 _Field([-1 if x == 255 else x for x in o])
            for f_ in (pieces, colors, origin):
                f_._board = self
            d = self.__dict__
            d["pieces"], d["colors"], d["origin_side"] = pieces, colors, origin
            return d[name]
        if name == "_king_sq":
            pieces, colors = self.pieces, self.colors
            out = {WHITE: -1, BLACK: -1}
            for sq in range(TOTAL_SQUARES):
                if pieces[sq] == KING:
                    out[colors[sq]] = sq
            self.__dict__["_king_sq"] = out
            return out
        raise AttributeError(name)

    def _square_written(self, sq):
        """A square written through the arrays: set on the Rust board as the arrays now have it."""
        pt = self.pieces[sq]
        orig = self.origin_side[sq]
        self._rb.set_square(sq, pt, bool(self.colors[sq]), orig if orig >= 0 else square_side(sq))
        self._moved()

    # ---- fields -----------------------------------------------------------------------------------------------------------------
    @property
    def turn(self):
        return self._rb.turn

    @turn.setter
    def turn(self, v):
        self._rb.turn = bool(v)

    @property
    def castling(self):
        return self._rb.castling

    @castling.setter
    def castling(self, v):
        self._rb.castling = v

    @property
    def en_passant(self):
        return self._rb.en_passant

    @en_passant.setter
    def en_passant(self, v):
        self._rb.en_passant = v

    @property
    def halfmove_clock(self):
        return self._rb.halfmove_clock

    @property
    def fullmove_number(self):
        return self._rb.fullmove_number

    def set_piece_at(self, sq, piece_type, color, orig_side=-1):
        self._rb.set_square(sq, piece_type, bool(color), orig_side if orig_side >= 0 else square_side(sq))
        self._moved()

    # ---- play ---------------------------------------------------------------------------------------------------------------------
    @property
    def legal_moves(self):
        return [_move(t) for t in self._rb.legal_move_tuples()]

    def push(self, move):
        self._rb.push(_to_rust(move))
        self._moved()

    def press_map(self, colour, need_kings=True):
        """square -> the squares colour's pieces press it from (the Rust board's; plans.press, warpworld.WarpWorld.pressure)."""
        return self._rb.press_map(colour, need_kings)

    def reach(self, me):
        """Every square some move of me's would leave pressed by me (the Rust board's; plans.reach)."""
        return self._rb.reach(me)

    def zobrist_hash(self):
        return self._rb.zobrist_hash()

    def _compute_hash(self):
        return self._rb.zobrist_hash()

    def is_attacked_by(self, sq, attacker_color):
        return self._rb.is_attacked_by(sq, attacker_color)

    def is_in_check(self, color):
        return self._rb.is_in_check(color)

    def is_game_over(self):
        return self._rb.is_game_over()

    def result(self):
        return self._rb.result()
