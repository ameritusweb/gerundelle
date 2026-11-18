"""Play chess against a fresh Gerundelle mind, its explanations shown (the user, 2026-11-17: "I want a new tkinter app, where I can play
against a fresh mind, and show the explanations").

- Your colour, then New mind: a fresh mind on its own seat for the other colour (chessduel.new_mind: rung 4p's switches, v2's
  want-dreams), with coverage (plansworld.covers_read) and explained needs (Params.explained_needs) as the checkboxes say.
- Click a piece, then where it goes (promotion: the "promote to" box). Your move is played in the mind's world as the other side's
  move, as the league's duel and random Black play theirs.
- The mind thinks in a background thread, slice by slice until it moves; the status line shows each slice. After its move, its
  explanation (why.py: how it chose, what it wanted and avoided, what the move was predicted to do, the tournament's top) is added
  to the Why panel, newest first.
- Endings: the rules (checkmate, stalemate, insufficient material, threefold repetition, the fifty-move rule) and the 300 half-move
  cap; seventh-heaven resignation is off here. New game: the same mind, lifelong, the board set back (it sees the end first). New
  mind: a fresh one.
Run: set PYTHONHASHSEED=0; python -X utf8 play_mind.py"""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

import chess

import mate_oracle
import why
from chessduel import BLACK, NAME, WHITE, new_mind
from plansworld import give, read_mate_passed

SQ, MARGIN = 72, 28
GLYPH = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
OUTLINE = {"k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙"}
MAX_SLICES = 400   # (a turn's cap on the mind's slices, so a stuck mind can't hang the app: it then passes the turn back as stuck)


class Play(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Play a Gerundelle mind")
        self.geometry("1700x900")
        self.q = queue.Queue()
        self.busy = False
        self.a = self.w = None
        self.sel = None
        self.last = None
        self.explanations = []

        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text="You play").pack(side="left")
        self.colour = tk.StringVar(value="White")
        ttk.Combobox(top, textvariable=self.colour, values=("White", "Black"), width=6, state="readonly").pack(side="left", padx=4)
        # every switch the user has decided on is on (the user, 2026-11-17: "you're supposed to turn on everything!!!"); the boxes
        # are there to turn one off for a comparison
        self.covers = tk.BooleanVar(value=True)
        self.explained = tk.BooleanVar(value=True)
        self.reach = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="coverage", variable=self.covers).pack(side="left", padx=6)
        ttk.Checkbutton(top, text="explained needs", variable=self.explained).pack(side="left", padx=6)
        ttk.Checkbutton(top, text="patience counts reach", variable=self.reach).pack(side="left", padx=6)
        from league import PROFILES
        self.profiles = PROFILES
        ttk.Label(top, text="temperament").pack(side="left", padx=(10, 2))
        self.profile = tk.StringVar(value="accepting_patient")   # (patience 6: patience counting reach needs a patience to count to)
        ttk.Combobox(top, textvariable=self.profile, values=list(PROFILES), width=17, state="readonly").pack(side="left")
        ttk.Button(top, text="New mind", command=self.new_mind).pack(side="left", padx=6)
        ttk.Button(top, text="New game", command=self.new_game).pack(side="left", padx=6)
        ttk.Button(top, text="Keep thinking", command=self.keep_thinking).pack(side="left", padx=6)
        ttk.Label(top, text="promote to").pack(side="left", padx=(16, 2))
        self.promo = tk.StringVar(value="q")
        ttk.Combobox(top, textvariable=self.promo, values=("q", "r", "b", "n"), width=3, state="readonly").pack(side="left")
        self.status = ttk.Label(top, text="Choose your colour and press New mind.", font=("Segoe UI", 10))
        self.status.pack(side="left", padx=16)

        body = ttk.Frame(self, padding=6)
        body.pack(fill="both", expand=True)
        size = 8 * SQ + 2 * MARGIN
        self.canvas = tk.Canvas(body, width=size, height=size, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", anchor="n")
        self.canvas.bind("<Button-1>", self.click)
        side = ttk.Frame(body, padding=(14, 0))
        side.pack(side="left", fill="both", expand=True)
        self.info = ttk.Label(side, text="", font=("Consolas", 10), justify="left")
        self.info.pack(anchor="nw")
        ttk.Label(side, text="Moves", font=("Segoe UI", 10, "bold")).pack(anchor="nw", pady=(8, 0))
        self.moves = tk.Text(side, width=120, height=4, font=("Consolas", 9), wrap="word")
        self.moves.pack(anchor="nw", fill="x")
        head = ttk.Frame(side)
        head.pack(anchor="nw", pady=(10, 0), fill="x")
        ttk.Label(head, text="Why (the mind's moves, newest first)", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(head, text="Copy", command=self.copy_why).pack(side="left", padx=8)
        self.copied = ttk.Label(head, text="")
        self.copied.pack(side="left")
        box = ttk.Frame(side)
        box.pack(anchor="nw", fill="both", expand=True)
        self.why = tk.Text(box, width=120, height=30, font=("Consolas", 9), wrap="word")
        sc = ttk.Scrollbar(box, command=self.why.yview)
        self.why.configure(yscrollcommand=sc.set)
        self.why.pack(side="left", fill="both", expand=True)
        sc.pack(side="left", fill="y")
        self.draw()
        self.after(100, self.poll)
        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---- the mind, in a background thread -------------------------------------------------------------------------------
    def run(self, fn, *args):
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self._wrap, args=(fn,) + args, daemon=True).start()

    def _wrap(self, fn, *args):
        try:
            fn(*args)
        except Exception as x:   # (shown, not swallowed: the app stays up)
            import traceback
            self.q.put(("status", f"error: {type(x).__name__}: {x}"))
            self.q.put(("why", traceback.format_exc()))
        finally:
            self.q.put(("done", None))

    def _build(self, me, covers, explained, reach=True, profile="patient"):
        self.q.put(("status", "building a fresh mind..."))
        a, w = new_mind(me, self.profiles.get(profile), seed=int(time.time()) % 1000, half_moves=300)
        w.RESIGN_AFTER_NEW_MATES = 0
        w.covers_read = covers
        a.mind.p.explained_needs = explained
        a.mind.p.patience_reach = reach
        w.shown = w.read()
        self.a, self.w, self.me = a, w, me
        self.explanations, self.played = [], []
        self.q.put(("board", None))
        self.q.put(("status", f"a fresh {profile} mind plays {NAME[me]}; switches: " +
                    ", ".join(n for n, on in (("coverage", covers), ("explained needs", explained), ("patience counts reach", reach)) if on)))
        if w.board.turn == me:
            self._mind_turn()

    def _mind_turn(self):
        a, w = self.a, self.w
        n0, games0 = w.moved, len(w.games)
        for s in range(MAX_SLICES):
            if w.over():
                break
            a._route = None
            committed_before = bool(a.__dict__.get("committed"))
            fen0 = w.board.to_fen()
            w.actor = NAME[self.me]
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
            did = ("waited" if choice is None else "asked the tool" if choice[0] == "ask" else
                   "committed" if choice[0] == "commit" else f"moved {choice[0].split(' ', 1)[1]}")
            self.q.put(("status", f"the mind thinks: slice {s + 1}, {did}"))
            if w.moved > n0 and len(w.games) == games0:
                route = a.__dict__.get("_route") or (("commit", None) if committed_before or a.__dict__.get("committed") else
                                                     ("experiment", None) if a.__dict__.get("running") or a.__dict__.get("queue") else None)
                e = why.explain(a, w, choice, route, fen0, NAME[self.me], w.moved, "fresh mind")
                self.explanations.append(e["text"])
                self.played.append(e["san"])
                self.last = e["uci"]
                self.q.put(("board", None))
                self.q.put(("why", None))
                break
        else:   # no move: the mind kept for a trace, what it was doing shown, the turn left open (Keep thinking)
            self._stuck()
            return
        self._ended()

    def _stuck(self):
        """The mind made no move in MAX_SLICES slices (the user, 2026-11-17: "it made no move in 400 slices, then froze up"): saved
        (rung4p.save_run, play_stuck_<time>.pkl) for a trace, and what it was doing put in the Why panel."""
        import rung4p
        a, w = self.a, self.w
        path = f"play_stuck_{time.strftime('%H%M%S')}.pkl"
        try:
            rung4p.save_run(path, a, w, None, {"fen": w.board.to_fen(), "played": list(self.played)})
        except Exception as x:
            path = f"(not saved: {type(x).__name__}: {x})"
        rec = a.__dict__.get("last_rec") or {}
        top = (rec.get("levels") or [{}])[-1]
        d = a.mind.__dict__.get("anti_defense") or {}
        invs = {f"{i[0]}_push:{i[1]}_{i[2]}": i for i in w.invitations()}
        lines = [f"NO MOVE in {MAX_SLICES} slices. Mind saved: {path}",
                 f"   FEN {w.board.to_fen()}",
                 f"   want {a.goal} (stack {a.stack}); anti {a.__dict__.get('anti')}",
                 f"   committed {bool(a.__dict__.get('committed'))}; watching {bool(a.watching)}; asking {bool(a.__dict__.get('asking'))}; "
                 f"experiment running {a.__dict__.get('running')}; queue {a.queue}; quiet {a.quiet}",
                 "   moves on offer (felt loss against waiting): " + ", ".join(f"{i[0]} {d.get(c, 0)}" for c, i in invs.items()),
                 "   top of its tournament: " + ", ".join(f"{x[:50]} {top.get('bids', {}).get(x, 0):.2f}"
                                                         for x in sorted(top.get("winners", []), key=lambda x: -top.get("bids", {}).get(x, 0))[:6])]
        self.explanations.append("\n".join(lines))
        self.q.put(("why", None))
        self.q.put(("status", f"the mind made no move in {MAX_SLICES} slices (saved for a trace); Keep thinking, or New game"))
        self.q.put(("stuck", None))

    def keep_thinking(self):
        if self.w is not None and self.w.board.turn == self.me and not self.w.over():
            self.run(self._mind_turn)

    def _ended(self):
        w = self.w
        if w.over() or w.moved >= w.moves:
            b = chess.Board(w.board.to_fen())
            why_ = w.draw_reason() if hasattr(w, "draw_reason") else None
            res = b.result(claim_draw=False)
            self.q.put(("status", f"game over: {res}" + (f" ({why_})" if why_ else "") + (" (the 300 half-move cap)" if w.moved >= w.moves else "")
                        + ". New game to play again (the mind sees the end first)."))
        else:
            self.q.put(("status", "your move"))

    def _human(self, move):
        a, w = self.a, self.w
        them = NAME[not self.me]
        w.actor = them
        w.pend[them] = {}
        san = chess.Board(w.board.to_fen()).san(chess.Move.from_uci(move.uci()))
        w.act((w.label(move), w.ids_at(move.from_square), "present"))
        w.pend[them] = {}
        w.actor = NAME[self.me]
        self.played.append(san)
        self.last = move.uci()
        self.q.put(("board", None))
        if w.over() or w.moved >= w.moves:
            self._ended()
            return
        self._mind_turn()

    def _new_game(self):
        a, w = self.a, self.w
        g0 = len(w.games)
        w.conclude() if hasattr(w, "conclude") else None
        for s in range(60):   # the mind sees the end; its world is set back
            if len(w.games) > g0:
                break
            w.pend[NAME[not self.me]] = {}
            w.actor = NAME[self.me]
            if w.moved < w.moves and not w.over():
                w.moved = w.moves   # (a game left unfinished: ended here, as the half-move cap ends one)
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
            self.q.put(("status", f"the mind sees the game's end: slice {s + 1}"))
        self.played, self.last = [], None
        if w.moved:   # (it moved in the slice that set its world back: White's first move)
            self.played.append(chess.Board().san(chess.Move.from_uci(next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1])))
        self.q.put(("board", None))
        if w.board.turn == self.me and not w.moved:
            self._mind_turn()
        else:
            self._ended()

    # ---- the window ---------------------------------------------------------------------------------------------------------
    def new_mind(self):
        me = BLACK if self.colour.get() == "White" else WHITE
        self.why.delete("1.0", "end")
        self.run(self._build, me, self.covers.get(), self.explained.get(), self.reach.get(), self.profile.get())

    def new_game(self):
        if self.w is not None:
            self.run(self._new_game)

    def poll(self):
        try:
            while True:
                kind, x = self.q.get_nowait()
                if kind == "status":
                    self.status.config(text=x)
                elif kind == "board":
                    self.draw()
                elif kind == "why":
                    self.why.delete("1.0", "end")
                    self.why.insert("end", x if x else "\n\n".join(reversed(self.explanations)))
                elif kind == "done":
                    self.busy = False
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def sq_at(self, x, y):
        f, r = int((x - MARGIN) // SQ), 7 - int((y - MARGIN) // SQ)
        if not (0 <= f < 8 and 0 <= r < 8):
            return None
        if self.w is not None and self.me == WHITE:   # (you play Black: the board flipped)
            f, r = 7 - f, 7 - r
        return chess.square(f, r)

    def click(self, ev):
        if self.busy or self.w is None or self.w.over() or self.w.board.turn == self.me:
            return
        sq = self.sq_at(ev.x, ev.y)
        if sq is None:
            return
        b = chess.Board(self.w.board.to_fen())
        if self.sel is None:
            p = b.piece_at(sq)
            if p and p.color == b.turn:
                self.sel = sq
                self.draw()
            return
        uci = chess.square_name(self.sel) + chess.square_name(sq)
        cands = [m for m in self.w.board.legal_moves if m.uci()[:4] == uci]
        self.sel = None
        if not cands:
            p = b.piece_at(sq)
            if p and p.color == b.turn:
                self.sel = sq
            self.draw()
            return
        move = next((m for m in cands if m.uci()[4:] == self.promo.get()), cands[0]) if len(cands) > 1 else cands[0]
        self.run(self._human, move)

    def draw(self):
        c = self.canvas
        c.delete("all")
        b = chess.Board(self.w.board.to_fen()) if self.w is not None else chess.Board()
        flip = self.w is not None and self.me == WHITE
        lm = chess.Move.from_uci(self.last) if self.last else None
        king = b.king(b.turn) if b.is_check() else None
        for sq in chess.SQUARES:
            f, r = chess.square_file(sq), chess.square_rank(sq)
            df, dr = (7 - f, 7 - r) if flip else (f, r)
            x, y = MARGIN + df * SQ, MARGIN + (7 - dr) * SQ
            light = (f + r) % 2 == 1
            col = "#f0d9b5" if light else "#b58863"
            if lm and sq in (lm.from_square, lm.to_square):
                col = "#cdd26a" if light else "#aaa23a"
            if sq == self.sel:
                col = "#7fb3e6"
            if sq == king:
                col = "#e65050"
            c.create_rectangle(x, y, x + SQ, y + SQ, fill=col, outline="")
            p = b.piece_at(sq)
            if p:
                s = p.symbol().lower()
                cx, cy = x + SQ / 2, y + SQ / 2 + 2
                if p.color:
                    c.create_text(cx, cy, text=GLYPH[s], font=("Segoe UI Symbol", 44), fill="white")
                    c.create_text(cx, cy, text=OUTLINE[s], font=("Segoe UI Symbol", 44), fill="black")
                else:
                    c.create_text(cx, cy, text=GLYPH[s], font=("Segoe UI Symbol", 44), fill="black")
        for i in range(8):
            files = "hgfedcba" if flip else "abcdefgh"
            c.create_text(MARGIN + i * SQ + SQ / 2, MARGIN + 8 * SQ + 14, text=files[i], font=("Segoe UI", 11))
            c.create_text(MARGIN / 2, MARGIN + i * SQ + SQ / 2, text=str(i + 1 if flip else 8 - i), font=("Segoe UI", 11))
        if self.w is not None:
            w = self.w
            self.info.config(text=f"you: {NAME[not self.me]}   mind: {NAME[self.me]}   half-moves {w.moved}   "
                                  f"White's balance {w.material() - w.start_material:+d}   games played {len(w.games)}\n"
                                  f"FEN {b.fen()}")
            self.moves.delete("1.0", "end")
            text =" ".join((f"{i // 2 + 1}. " if i % 2 == 0 else "") + s for i, s in enumerate(self.played))
            self.moves.insert("end", text)

    def copy_why(self):
        self.clipboard_clear()
        self.clipboard_append(f"Moves: {' '.join(self.played) if self.w else ''}\n\n" + self.why.get("1.0", "end").strip() + "\n")
        self.update()
        self.copied.config(text="copied")
        self.after(2000, lambda: self.copied.config(text=""))

    def close(self):
        try:
            mate_oracle.close()
        finally:
            self.destroy()


if __name__ == "__main__":
    Play().mainloop()
