"""Two sides, each with minds, on one Warp board (LADDER.md, rung 2). After cognitivechess/chessworld.py's DuelWorld.

- Turns: only the side to move is offered moves (the side named by `actor`).
- What a move came to reaches the mind that made it in its own next slice; in the move's own slice only the piece moved changes (principle 0).
- A side's standing (standing_white, standing_black: up, even or down, from that side's view) is read when its turn comes round, after the other side has answered.
- An episode is `half_moves` moves, or ends when a king is taken, or after IDLE slices with no move.
"""
from warpworld import BLACK, IDLE, WHITE, WarpWorld

SIDES = {"White": WHITE, "Black": BLACK}


class WarpDuel(WarpWorld):
    def __init__(self, fen, seed=0, half_moves=4):
        super().__init__(fen, seed=seed, moves=half_moves, forces=True)
        self.objs.update({"standing_white": None, "standing_black": None})
        self.actor = "White"
        self.horizon = 3   # a mind's watch spans the other side's answer
        self.episodes = []   # White's balance at each episode's end

    def reset(self):
        if hasattr(self, "standing") and getattr(self, "moved", 0):
            self.episodes.append(self.material() - self.start_material)
        super().reset()
        self.standing = {"White": "even", "Black": "even"}
        self.pend = {"White": {}, "Black": {}}
        self.has_moved = set()

    def over(self):
        return self.board._king_sq[WHITE] < 0 or self.board._king_sq[BLACK] < 0 or not self.board.legal_moves

    def balance(self, side):
        d = self.material() - self.start_material
        d = d if side == "White" else -d
        return "even" if d == 0 else ("up" if d > 0 else "down")

    def states(self, tree=None):
        out = dict(self.shown)
        out["standing_white"], out["standing_black"] = self.standing["White"], self.standing["Black"]
        return out

    def restand(self, side, new):
        old = self.standing[side]
        if new != old:
            if side in self.has_moved:
                self.pend[side][f"standing_{side.lower()}"] = (old, new)
            self.standing[side] = new

    def offers(self):
        if self.over() or SIDES.get(self.actor) != self.board.turn:
            return {}
        return {self.label(m): m for m in self.board.legal_moves}

    def invitations(self, tree=None):
        if self.moved >= self.moves:
            return []
        return [(label, self.ids_at(m.from_square), "present") for label, m in sorted(self.offers().items())]

    def renew(self):
        if (self.moved >= self.moves or self.over() or (self.moved and self.idle >= IDLE)) and not any(self.pend.values()):
            self.reset()
            self.diffs = []

    def act(self, inv=None, hold=False):
        me = self.actor
        move = self.offers().get(inv[0]) if inv is not None else None
        if inv is not None and (move is None or self.ids_at(move.from_square) != inv[1] or self.moved >= self.moves):
            self.idle += 1   # the world pushes back: a move not on offer does nothing
            self.diffs = []
            self.t += 1
            self.log.append((self.t, inv[0], False, None))
            return []
        diffs = [] if inv is not None else [f"{o}: {a} -> {b}" for o, (a, b) in sorted(self.pend[me].items())]
        if inv is None:
            for o, (a, b) in self.pend[me].items():
                self.shown[o] = b
        self.pend[me] = {}
        self.idle = 0 if inv is not None else self.idle + 1
        if inv is not None:
            before = dict(self.shown)
            mover = self.play(move)
            self.moved += 1
            self.has_moved.add(me)
            after = self.read()
            if after[mover] != before.get(mover):
                diffs.append(f"{mover}: {before.get(mover)} -> {after[mover]}")
                self.shown[mover] = after[mover]
            for o, st in after.items():   # the rest of what it did reaches the mover in its next slice; the other side perceives the board as it stands
                if o != mover and st != before.get(o):
                    self.pend[me][o] = (before.get(o), st)
            for o, st in after.items():
                if o not in self.pend[me]:
                    self.shown[o] = st
            nxt = "White" if self.board.turn == WHITE else "Black"
            self.restand(nxt, self.balance(nxt))
            self.log.append((self.t, inv[0], True, self.balance("White")))
        self.diffs = diffs
        self.t += 1
        return diffs
