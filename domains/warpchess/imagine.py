"""World.imagine for Warp (Gerundelle's Params.imagine; after cognitivechess/chessworld.py's ChessWorld.imagine).

A move the mind has never made is an open force slot (README: "where a configuration invites a force that has not been applied, the
world has an open force slot: the question 'what would happen?' is itself a structure"). With Params.imagine, the planner's model imagines
such a move from the board now: the line is played on a copy by the engine's rules, the other side passing (chess's 'rules'), and what the
last move leaves is read as forces. The world itself is not changed. The planner believes what it imagines at the mind's credulity, and it
funds nothing (the firewall).
"""


class Imagines:
    """A mixin for a WarpWorld (or WarpDuel, GameWorld): imagine(line) -> (facts, changes) or None if a move isn't a move there."""

    def imagine(self, line):
        cache = self.__dict__.setdefault("_imagined", {})
        key = (self.board.to_fen(), tuple(line))
        if key in cache:
            return cache[key]
        saved = (self.board.copy(), dict(self.where), dict(getattr(self, "captured_by", {})))
        colour = self.board.turn
        out = None
        try:
            for k, label in enumerate(line):
                self.board.turn = colour
                from warpworld import rehash
                rehash(self.board)
                move = next((m for m in self.board.legal_moves if self.label(m) == label), None)
                if move is None:
                    out = None
                    break
                before = self.read() if k == len(line) - 1 else None
                self.play(move)
                if k == len(line) - 1:
                    after = self.read()
                    out = (frozenset(f"{o}_{st}" for o, st in after.items()),
                           frozenset(f"{o}_{st}" for o, st in after.items() if st != before.get(o)))
        finally:
            self.board, self.where = saved[0], saved[1]
            if hasattr(self, "captured_by"):
                self.captured_by = saved[2]
        cache[key] = out
        return out
