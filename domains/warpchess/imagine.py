"""World.imagine for Warp (Gerundelle's Params.imagine; after cognitivechess/chessworld.py's ChessWorld.imagine).

A move the mind has never made is an open force slot (README: "where a configuration invites a force that has not been applied, the
world has an open force slot: the question 'what would happen?' is itself a structure"). With Params.imagine, the planner's model imagines
such a move from the board now: the line is played on a copy by the engine's rules, the other side replying as the mind would in its shoes
(shoes.py; passing if none is set, as chess's 'rules'), and what the last move leaves is read as forces. The world itself is not changed. The planner believes what it imagines at the mind's credulity, and it
funds nothing (the firewall).
"""


class Imagines:   # with in_their_shoes set (a callable, world -> the opponent's move or None), the opponent replies in each imagined line
    """A mixin for a WarpWorld (or WarpDuel, GameWorld): imagine(line) -> (facts, changes) or None if a move isn't a move there."""

    def imagine(self, line):
        cache = self.__dict__.setdefault("_imagined", {})
        key = (self.board.to_fen(), tuple(line))
        if key in cache:
            return cache[key]
        saved = (self.board.copy(), dict(self.where), dict(getattr(self, "captured_by", {})))
        colour = self.board.turn
        out = None
        self.__dict__["imagining"] = True   # (an imagined move is no position of the game: dream.Remembers doesn't record it)
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
                mid = self.read() if k == len(line) - 1 else None
                reply = self.in_their_shoes(self) if getattr(self, "in_their_shoes", None) else None
                if reply is not None:   # the opponent's reply, as the mind would make it in their shoes (the user, 2026-11-07)
                    self.play(reply)
                if k == len(line) - 1:
                    after = self.read()
                    out = (frozenset(f"{o}_{st}" for o, st in after.items()),
                           frozenset(f"{o}_{st}" for o, st in after.items() if st != before.get(o)))
                    self.__dict__.setdefault("_starts", {})[key] = frozenset(f"{o}_{st}" for o, st in mid.items() if st != before.get(o))
        finally:
            self.__dict__["imagining"] = False
            self.board, self.where = saved[0], saved[1]
            if hasattr(self, "captured_by"):
                self.captured_by = saved[2]
        cache[key] = out
        return out

    def imagined_start(self, line):
        """What changed right after the last move of an imagined line, before the opponent's reply: the move's start, as a dream pair's
        and a lived concept's start are read (the full result, with the reply, is imagine()'s, for planning).
        A single move (what dream.wake asks; 2026-11-13, an exact speed-up): its start depends only on the board and the pieces' places,
        so it is read on its own (the board before, the move, the board after it: no reply in their shoes, no reading after the reply)
        and kept for that board and move across slices. First every untried move on offer was imagined in full every slice, and with
        the plans read in each imagined position waking was 73% of a slice (py-spy, rung4p.py --dreams)."""
        if len(line) != 1:
            out = self.imagine(line)
            if out is None:
                return None
            return self.__dict__.get("_starts", {}).get((self.board.to_fen(), tuple(line)))
        key = (self.board.to_fen(), frozenset(self.where.items()), line[0])
        cache = self.__dict__.setdefault("_start_cache", {})
        if key in cache:
            return cache[key]
        if len(cache) > 50_000:
            cache.clear()
        from warpworld import rehash
        saved = (self.board.copy(), dict(self.where), dict(getattr(self, "captured_by", {})))
        colour, out = self.board.turn, None
        self.__dict__["imagining"] = True
        self.__dict__["no_plans"] = True   # (a start keeps a piece's own readings and the files' pressure, carry.start_of: the opponent's
        # plans are never part of one, so they aren't read here (plansworld.read_forces); in games from the start, waking read them for
        # every untried move, every slice: 78% of the time, py-spy, 2026-11-13. The start returned has no plan changes: dream.wake reads
        # it through start_of, which never kept them)
        try:
            self.board.turn = colour
            rehash(self.board)
            move = next((m for m in self.board.legal_moves if self.label(m) == line[0]), None)
            if move is not None:
                before = self.read()
                self.play(move)
                mid = self.read()
                out = frozenset(f"{o}_{st}" for o, st in mid.items() if st != before.get(o))
        finally:
            self.__dict__["imagining"] = False
            self.__dict__["no_plans"] = False
            self.board, self.where = saved[0], saved[1]
            if hasattr(self, "captured_by"):
                self.captured_by = saved[2]
        cache[key] = out
        return out
