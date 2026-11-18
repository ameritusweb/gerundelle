"""The chess one-on-one for the site (site/chess; the user, 2026-11-17: "update this with cognitivechess_v2 one on one"; "rust-wasm"): the
play app's game (play_mind.py), stepped a slice at a time from the page's worker so the page stays live. A fresh mind with every switch
on (chessduel.configure), the board the Rust board in WebAssembly (chess_board.py's shim), each of its moves explained (why.py). Every
call returns the view as JSON."""
import json
import time

import chess

import why
from chessduel import BLACK, NAME, WHITE, configure
from plansworld import give, read_mate_passed

PROFILES = {   # (league.py's: league imports multiprocessing, which the browser hasn't)
    "steady": {}, "impatient": dict(patience=2), "patient": dict(patience=6), "restless": dict(persistence=0.25, curiosity=2.0),
    "dogged": dict(persistence=4.0, curiosity=0.5), "trusting": dict(credulity=0.9), "skeptical": dict(credulity=0.1),
    "averse": dict(aversion=2.0), "unflinching": dict(aversion=0.5), "accepting": dict(acceptance=3), "grieving": dict(acceptance=12),
    "accepting_patient": dict(acceptance=3, patience=6), "scientific": dict(experimentation=3),
}
MAX_SLICES = 400


class Game:
    def __init__(self):
        self.a = self.w = None
        self.me = BLACK
        self.played, self.explanations, self.last = [], [], None
        self.slices, self.status = 0, "Choose your colour and a temperament, then New mind."
        self.mates = False

    # ---- calls from the page ---------------------------------------------------------------------------------------------------
    def new_mind(self, human_white=True, profile="accepting_patient", mates=False):
        import rung4p
        self.me = BLACK if human_white else WHITE
        w, a = rung4p.build(int(time.time()) % 1000, None, dreams=True, half_moves=300, me=self.me)
        configure(a, PROFILES.get(profile, {}))
        w.RESIGN_AFTER_NEW_MATES = 0
        w.mates_read = bool(mates)   # (forced mates: Stockfish in the browser, when the page has it)
        self.mates = bool(mates)
        w.shown = w.read()
        give(a, w)
        self.a, self.w = a, w
        self.played, self.explanations, self.last, self.slices = [], [], None, 0
        self.profile = profile
        self.status = f"A fresh {profile} mind plays {NAME[self.me]}." + (" Your move." if self.my_turn() is False else "")
        return self.view()

    def human(self, uci):
        w = self.w
        move = next((m for m in w.board.legal_moves if m.uci() == uci), None)
        if move is None or self.my_turn() is not False or self.over():
            return self.view()
        them = NAME[not self.me]
        san = chess.Board(w.board.to_fen()).san(chess.Move.from_uci(uci))
        w.actor = them
        w.pend[them] = {}
        w.act((w.label(move), w.ids_at(move.from_square), "present"))
        w.pend[them] = {}
        w.actor = NAME[self.me]
        self.played.append(san)
        self.last, self.slices = uci, 0
        self.status = self.end_text() or "The mind is thinking."
        return self.view()

    def think(self):
        """One slice of the mind's, when it's its turn. -> the view (thinking, or its move with its explanation)."""
        a, w = self.a, self.w
        if w is None or self.over() or not self.my_turn():
            return self.view()
        if self.slices >= MAX_SLICES:
            self.status = f"The mind made no move in {MAX_SLICES} slices."
            return self.view()
        a._route = None
        committed_before = bool(a.__dict__.get("committed"))
        fen0, n0 = w.board.to_fen(), w.moved
        w.actor = NAME[self.me]
        t0 = time.time()
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        self.slices += 1
        did = ("waited" if choice is None else "asked the tool" if choice[0] == "ask" else
               "committed to a sequence" if choice[0] == "commit" else "moved")
        self.status = f"The mind is thinking: slice {self.slices} ({did}, {time.time() - t0:.1f}s)."
        if w.moved > n0:
            route = a.__dict__.get("_route") or (("commit", None) if committed_before or a.__dict__.get("committed") else
                                                 ("experiment", None) if a.__dict__.get("running") or a.__dict__.get("queue") else None)
            e = why.explain(a, w, choice, route, fen0, NAME[self.me], w.moved, self.profile)
            self.explanations.append(e["text"])
            self.played.append(e["san"])
            self.last = e["uci"]
            self.status = self.end_text() or f"It played {e['san']} after {self.slices} slices. Your move."
        return self.view()

    def new_game(self):
        a, w = self.a, self.w
        if w is None:
            return self.view()
        g0 = len(w.games)
        for s in range(60):   # the mind sees the end; its world is set back
            if len(w.games) > g0:
                break
            w.pend[NAME[not self.me]] = {}
            w.actor = NAME[self.me]
            if w.moved < w.moves and not w.over():
                w.moved = w.moves
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
        self.played, self.last, self.slices = [], None, 0
        if w.moved:   # (it moved in the slice that set its world back)
            uci = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
            self.played.append(chess.Board().san(chess.Move.from_uci(uci)))
            self.last = uci
        self.status = "A new game, the same mind." + (" Your move." if self.my_turn() is False else "")
        return self.view()

    # ---- the view ----------------------------------------------------------------------------------------------------------------
    def my_turn(self):
        return None if self.w is None else self.w.board.turn == self.me

    def over(self):
        w = self.w
        return w is not None and (w.over() or w.moved >= w.moves)

    def end_text(self):
        w = self.w
        if not self.over():
            return None
        b = chess.Board(w.board.to_fen())
        res = b.result(claim_draw=False)
        why_ = w.draw_reason() if hasattr(w, "draw_reason") else None
        return f"Game over: {res}" + (f" ({why_})" if why_ else "") + (" (the 300 half-move cap)" if w.moved >= w.moves else "") + "."

    def view(self):
        w = self.w
        fen = w.board.to_fen() if w is not None else chess.STARTING_FEN
        legal = ([m.uci() for m in w.board.legal_moves] if w is not None and self.my_turn() is False and not self.over() else [])
        return json.dumps(dict(fen=fen, human_white=self.me == BLACK, mind_to_move=bool(self.my_turn()), over=self.over(),
                               legal=legal, played=self.played, last=self.last, status=self.status,
                               explanations=list(reversed(self.explanations)), slices=self.slices,
                               profiles=list(PROFILES), mates=self.mates))


game = Game()
