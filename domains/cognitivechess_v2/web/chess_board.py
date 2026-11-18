"""chess_board for the browser (site/chess; the user, 2026-11-17: "rust-wasm"): the pyo3 extension's ChessBoard interface over the same
Rust board compiled to WebAssembly (chess_board/src/lib.rs, feature "wasm": WasmBoard), reached through Pyodide's JS bridge. rustboard.py
imports it unchanged. Each crossing of the bridge costs, so what a board reads is kept (hash, FEN, arrays, moves, pressure, attacks)
until the board changes; copies start with their original's readings (a copy is the same position)."""
import js

_W = js.WasmBoard


def _bytes(x):
    return x.to_py().tolist()


class ChessBoard:
    __slots__ = ("_b", "_c")

    def __init__(self, b=None):
        self._b = b if b is not None else _W.starting_position()
        self._c = {}

    @staticmethod
    def starting_position():
        return ChessBoard(_W.starting_position())

    @staticmethod
    def from_fen(fen):
        try:
            return ChessBoard(_W.from_fen(fen))
        except Exception as x:
            raise ValueError(str(x))

    def _changed(self):
        self._c = {}

    def to_fen(self):
        c = self._c
        if "fen" not in c:
            c["fen"] = self._b.to_fen()
        return c["fen"]

    def copy(self):
        out = ChessBoard(self._b.copy())
        out._c = dict(self._c)
        return out

    @property
    def turn(self):
        c = self._c
        if "turn" not in c:
            c["turn"] = bool(self._b.turn())
        return c["turn"]

    @turn.setter
    def turn(self, v):
        self._b.set_turn(bool(v))
        self._changed()

    @property
    def castling(self):
        return int(self._b.castling())

    @castling.setter
    def castling(self, v):
        self._b.set_castling(int(v))
        self._changed()

    @property
    def en_passant(self):
        return int(self._b.en_passant())

    @en_passant.setter
    def en_passant(self, v):
        self._b.set_en_passant(int(v))
        self._changed()

    @property
    def halfmove_clock(self):
        return int(self._b.halfmove_clock())

    @property
    def fullmove_number(self):
        return int(self._b.fullmove_number())

    def arrays(self):
        c = self._c
        if "arrays" not in c:
            a = _bytes(self._b.arrays())
            pieces, colors = a[:64], [bool(x) for x in a[64:]]
            c["arrays"] = (pieces, colors, [255 if p == 0 else 0 for p in pieces])
        p, col, o = c["arrays"]
        return list(p), list(col), list(o)

    def set_square(self, sq, piece_type, color, orig_side=0):
        self._b.set_square(int(sq), int(piece_type), bool(color))
        self._changed()

    def legal_move_tuples(self):
        c = self._c
        if "moves" not in c:
            m = _bytes(self._b.legal_moves())
            c["moves"] = [(m[i], m[i + 1], m[i + 2], 0, -1, -1) for i in range(0, len(m), 3)]
        return c["moves"]

    def push_move(self, from_square, to_square, promotion=0):
        self._b.push_move(int(from_square), int(to_square), int(promotion or 0))
        self._changed()

    def press_map(self, colour, need_kings=True):
        key = ("press", bool(colour), bool(need_kings))
        c = self._c
        if key not in c:
            flat = _bytes(self._b.press_map(bool(colour), bool(need_kings)))
            out, i = {}, 0
            while i < len(flat):
                t, n = flat[i], flat[i + 1]
                out[t] = set(flat[i + 2:i + 2 + n])
                i += 2 + n
            c[key] = out
        return c[key]

    def reach(self, me):
        key = ("reach", bool(me))
        c = self._c
        if key not in c:
            c[key] = set(_bytes(self._b.reach(bool(me))))
        return c[key]

    def zobrist_hash(self):
        c = self._c
        if "hash" not in c:
            c["hash"] = int(self._b.zobrist_hash())
        return c["hash"]

    def is_attacked_by(self, sq, attacker_color):
        key = ("att", int(sq), bool(attacker_color))
        c = self._c
        if key not in c:
            c[key] = bool(self._b.is_attacked_by(int(sq), bool(attacker_color)))
        return c[key]

    def is_in_check(self, color):
        key = ("check", bool(color))
        c = self._c
        if key not in c:
            c[key] = bool(self._b.is_in_check(bool(color)))
        return c[key]

    def is_game_over(self):
        return bool(self._b.is_game_over())

    def is_checkmate(self):
        return bool(self._b.is_checkmate())

    def is_stalemate(self):
        return bool(self._b.is_stalemate())

    def result(self):
        return str(self._b.result())

    def __repr__(self):
        return f"ChessBoard({self.to_fen()})"
