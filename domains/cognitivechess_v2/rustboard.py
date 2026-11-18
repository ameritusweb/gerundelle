"""Standard chess on the chess Rust board (chess_board/, PLAN.md step 1), behind warpchess's rustboard.py interface, so the domain layer
copied from warpchess imports it unchanged.

One 8x8 board, squares 0..63 (a1 = 0, python-chess's numbering), names like `e4`, moves named as UCI (`e2e4`, `e7e8q`). Warp's names
are kept where the copied code imports them: `WarpMove` and `WarpBoard` (aliased `ChessMove`, `ChessBoard`), the side and flip helpers
(one side: square_side is 0, flip_square is the square itself, no move flips), CRAB (never on the board). What differs from
warpchess's version:
- The board's moves are every move that doesn't leave the mover's own king attacked: exactly chess's legal moves in a legal position,
  and on a turned board (the side not to move in check) the capture of that king too (PLAN.md: checkmate is the king's piece gain).
- No origin sides: arrays() gives origin 0 for an occupied square.
- check_chessboard.py checks the board against python-chess (perft, random games, pressure).
"""
from dataclasses import dataclass
from typing import Optional

import chess_board as _cb

WHITE, BLACK = True, False
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, CRAB = 1, 2, 3, 4, 5, 6, 7
PIECE_NAMES = {PAWN: "P", KNIGHT: "N", BISHOP: "B", ROOK: "R", QUEEN: "Q", KING: "K", CRAB: "C"}
PIECE_FROM_CHAR = {v: k for k, v in PIECE_NAMES.items()}
PIECE_VALUES = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 0, CRAB: 3}
NUM_PIECE_TYPES = 6
BOARD_FILES, BOARD_RANKS = 8, 8
SQUARES_PER_SIDE, TOTAL_SQUARES = 64, 64
LEFT, RIGHT = 0, 1
NO_FLIP, PRE_FLIP, POST_FLIP = 0, 1, 2
FILE_NAMES, RANK_NAMES = "abcdefgh", "12345678"


def square(side, file, rank):
    return rank * 8 + file


def square_side(sq):
    return LEFT


def square_file(sq):
    return sq & 7


def square_rank(sq):
    return sq >> 3


def flip_square(sq):
    return sq


def is_playable(sq):
    return 0 <= sq < 64


def square_name(sq):
    return f"{FILE_NAMES[square_file(sq)]}{square_rank(sq) + 1}"


def square_from_name(name):
    return square(LEFT, ord(name[0]) - ord("a"), int(name[1]) - 1)


@dataclass(frozen=True, slots=True)
class WarpMove:
    """A move: from_square, to_square, promotion (warpchess's move shape; flip_type is always NO_FLIP in chess)."""
    from_square: int
    to_square: int
    promotion: Optional[int] = None
    flip_type: int = NO_FLIP
    flip_from: int = -1
    flip_to: int = -1

    @property
    def final_square(self):
        return self.to_square

    def uci(self):
        promo = PIECE_NAMES.get(self.promotion, "").lower() if self.promotion else ""
        return f"{square_name(self.from_square)}{square_name(self.to_square)}{promo}"

    def __repr__(self):
        return f"ChessMove({self.uci()})"


ChessMove = WarpMove
_MOVES = {}   # a move's tuple -> its move object (made once)


def _move(t):
    m = _MOVES.get(t)
    if m is None:
        m = _MOVES[t] = WarpMove(t[0], t[1], t[2] or None)
    return m


class _Field(list):
    """A board's pieces, colours or origins: read as a list; a write sets that square on the board."""
    __slots__ = ("_board",)

    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        self._board._square_written(k)


_CACHED = ("pieces", "colors", "origin_side", "_king_sq")


class WarpBoard:
    WK, WQ, BK, BQ = 1, 2, 4, 8
    _legal_cache = {}

    def __init__(self, rust=None):
        self._rb = rust if rust is not None else _cb.ChessBoard.starting_position()

    @classmethod
    def from_fen(cls, fen):
        return cls(_cb.ChessBoard.from_fen(fen))

    @classmethod
    def starting_position(cls):
        return cls(_cb.ChessBoard.starting_position())

    def to_fen(self):
        return self._rb.to_fen()

    def copy(self):
        return WarpBoard(self._rb.copy())

    def __reduce__(self):
        return (WarpBoard.from_fen, (self.to_fen(),))

    def _moved(self):
        d = self.__dict__
        for k in _CACHED:
            d.pop(k, None)

    def __getattr__(self, name):
        if name in ("pieces", "colors", "origin_side"):
            p, c, o = self._rb.arrays()
            pieces, colors = _Field(p), _Field([c[i] if p[i] else None for i in range(TOTAL_SQUARES)])
            origin = _Field([-1 if x == 255 else x for x in o])
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
        self._rb.set_square(sq, self.pieces[sq], bool(self.colors[sq]))
        self._moved()

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
        self._rb.set_square(sq, piece_type, bool(color))
        self._moved()

    @property
    def legal_moves(self):
        return [_move(t) for t in self._rb.legal_move_tuples()]

    def push(self, move):
        self._rb.push_move(move.from_square, move.to_square, move.promotion or 0)
        self._moved()

    def press_map(self, colour, need_kings=True):
        return self._rb.press_map(colour, need_kings)

    def reach(self, me):
        return self._rb.reach(me)

    def zobrist_hash(self):
        return self._rb.zobrist_hash()

    def _compute_hash(self):
        return self._rb.zobrist_hash()

    def is_attacked_by(self, sq, attacker_color):
        return self._rb.is_attacked_by(sq, attacker_color)

    def is_in_check(self, color):
        return self._rb.is_in_check(color)

    def is_checkmate(self):
        return self._rb.is_checkmate()

    def is_stalemate(self):
        return self._rb.is_stalemate()

    def is_game_over(self):
        return self._rb.is_game_over()

    def result(self):
        return self._rb.result()


ChessBoard = WarpBoard
