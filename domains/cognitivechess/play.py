"""Play the chess mind, with a view into its thinking (tkinter).

You play one side; the other is a Gerundelle mind as rung 3 and the stress test left it: base arm, pieces as given territory,
White wanting its standing up, Black a keeper of what it holds, with winner_acts, the imagination lane, news in the structure
and stuck_earns on. It knows nothing of chess values and does not perceive squares: expect weak play, and watch it learn.

Self-play games (N, in the window): both minds first play N games of up to 120 half-moves against each other, in the world's
usual rules; the mind on your opposite side then carries that experience into your game.

While you play: the world's rule that ends a game after idle slices is off, so the mind can think as long as it needs. If it
has not moved after MAX_TICKS ticks the panel says so and "Force a move" plays its highest-bid legal move, logged as forced.

Run: python -X utf8 play.py [--games N] [--side white|black] [--seed 0] [--curiosity 1.0] [--persistence 1.0] [--patience N]
Test without a window: python -X utf8 experiments/play_check.py
"""
import argparse
import os
import queue
import re
import sys
import threading
import time
import traceback
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fiction"))

import chess  # noqa: E402
from rung3 import make, TURN_STEPS  # noqa: E402  (puts Gerundelle on the path)
from force_world import inv_id  # noqa: E402
from molecules import is_exp, is_meta, is_own, is_phase, is_sov  # noqa: E402

MAX_TICKS = 60        # ticks of thinking before the panel offers to force a move
TRAIN_HALF_MOVES = 120
SNAPSHOT_EVERY = 0.15  # seconds between thinking updates while the mind thinks


def pretty(i):
    """A molecule's id, readable: order ranks gone, a push as its move."""
    s = re.sub(r"\b\d{3} ", "", i)
    s = re.sub(r"_push:(white|black)_(\w+?)_([a-h][1-8])_present", r" (\2 \3)", s)
    return s.replace("own:q:", "question ").replace("own:", "").replace("q:", "asks ").replace("sov:", "understanding ")


def lane(i, imagined):
    if i in imagined:
        return "imagined"
    if is_own(i):
        return "ownership"
    if is_phase(i):
        return "feeling"
    if is_meta(i):
        return "about its thinking"
    if is_sov(i):
        return "questions"
    if is_exp(i):
        return "experiments"
    if "_push:" in i:
        return "moves on offer"
    return "thoughts"


class Engine(threading.Thread):
    """Owns the world and the minds, in its own thread. Commands go in by `send`; snapshots (plain dicts, safe to read
    anywhere) come out on `out`."""

    def __init__(self, games=0, side="white", seed=0, curiosity=1.0, persistence=1.0, patience=None):
        super().__init__(daemon=True)
        self.games, self.human, self.seed = games, chess.WHITE if side == "white" else chess.BLACK, seed
        self.temper = dict(curiosity=curiosity, persistence=persistence, patience=patience)
        self.cmd, self.out = queue.Queue(), queue.Queue()
        self.log, self.learned, self.playing, self.stalled = [], [], False, False
        self.status, self.last_move, self.ticks, self.why = "Starting…", None, 0, ""
        self.expected, self.seen_splits = "", set()

    def send(self, *cmd):
        self.cmd.put(cmd)

    # ---- the thread -----------------------------------------------------------------------------------------------

    def run(self):
        try:
            self.setup()
            self.train()
            self.begin_game()
            while True:
                c = self.cmd.get()
                if c[0] == "move":
                    self.human_move(c[1], c[2])
                elif c[0] == "force":
                    self.force()
                elif c[0] == "new":
                    self.new_game()
                elif c[0] == "stop":
                    return
        except Exception:
            self.out.put(dict(error=traceback.format_exc()))

    def setup(self):
        self.w, minds = make(self.seed, "mind", "base", "keeper", given=True, fen=chess.STARTING_FEN,
                             half_moves=TRAIN_HALF_MOVES)
        self.minds = {m.name: m for m in minds}
        for m in minds:
            p = m.agent.mind.p
            p.winner_acts = p.imagined_lane = p.news_in_structure = p.stuck_earns = True
            p.curiosity, p.persistence, p.patience = self.temper["curiosity"], self.temper["persistence"], self.temper["patience"]
        self.seen = {m.name: 0 for m in minds}
        self.mind_name = "Black" if self.human == chess.WHITE else "White"
        self.human_name = "White" if self.human == chess.WHITE else "Black"
        self.mind = self.minds[self.mind_name]
        a = self.mind.agent
        self.planned_now = None
        planned = a.planned

        def traced(invs):
            self.planned_now = planned(invs)
            return self.planned_now
        a.planned = traced
        renew = self.w.renew
        self.w.renew = lambda: None if self.playing else renew()   # while you play, only "new game" sets the board back

    def train(self):
        if not self.games:
            return
        w, done, t0 = self.w, [0], time.time()
        reset = w.reset

        def counted():
            done[0] += 1
            self.status = f"Self-play: game {done[0]} of {self.games} ({time.time() - t0:.0f}s)"
            self.post()
            reset()
        w.reset = counted
        self.status = f"Self-play: game 1 of {self.games}…"
        self.post()
        while done[0] < self.games:
            mover = "White" if w.board.turn == chess.WHITE else "Black"
            other = "Black" if mover == "White" else "White"
            before = (w.moved, len(w.episodes))
            for _ in range(TURN_STEPS):
                self.step(mover)
                if (w.moved, len(w.episodes)) != before:
                    break
            self.step(other)
        w.reset = reset

    def step(self, name):
        self.w.actor = name
        self.seen[name] = self.minds[name].step(self.seen[name])

    # ---- a game ---------------------------------------------------------------------------------------------------

    def begin_game(self):
        w = self.w
        self.settle()
        w.moves = 10 ** 6
        w.reset()
        w.diffs = []
        self.playing, self.stalled, self.log, self.last_move = True, False, [], None
        a = self.mind.agent
        a.queue, a.running = [], None
        self.seen_splits = set(a.mind.meta.splits)
        if self.human == chess.WHITE:
            self.status = "Your move."
            self.post()
        else:
            self.mind_turn()

    def settle(self):
        """Let a push under way finish being watched, so the board isn't set back in the middle of one."""
        for m in self.minds.values():
            for _ in range(8):
                if not m.agent.watching:
                    break
                self.step(m.name)

    def new_game(self):
        self.playing = True
        self.begin_game()

    def over(self):
        b = self.w.board
        if self.w.mated or b.is_checkmate():
            return ("You win: checkmate." if b.turn != self.human else "The mind mates you.")
        if b.is_game_over():
            return f"Draw ({b.outcome().termination.name.lower().replace('_', ' ')})."
        return None

    def human_move(self, frm, to):
        w = self.w
        if w.board.turn != self.human or self.over():
            return
        move = next((m for m in w.board.legal_moves if m.from_square == frm and m.to_square == to
                     and (m.promotion in (None, chess.QUEEN))), None)
        if move is None:
            return
        san = w.board.san(move).rstrip("+#")
        inv = (w.label(move), w.ids_at(move.from_square), "present")
        w.actor = self.human_name
        w.act(inv)
        self.last_move = (move.from_square, move.to_square)
        self.log.append((self.human_name, san, "you"))
        self.stalled = False
        self.mind_turn()

    def mind_turn(self):
        w, a = self.w, self.mind.agent
        done = self.over()
        if done:
            self.status = done
            self.post()
            return
        before, self.ticks, last = w.moved, 0, 0.0
        self.status = "The mind is thinking…"
        self.post()
        while w.moved == before and self.ticks < MAX_TICKS:
            pre = (list(a.queue), a.running)
            self.planned_now = None
            n0 = len(a.tried)
            board_before = w.board.copy()
            self.step(self.mind_name)
            self.ticks += 1
            self.note_learning(n0)
            if w.moved != before:
                self.record_move(board_before, pre)
            if time.time() - last > SNAPSHOT_EVERY:
                last = time.time()
                self.post()
        self.finish_turn(before)

    def finish_turn(self, before):
        w = self.w
        if w.moved == before:
            self.stalled = True
            self.status = f"The mind has not moved after {self.ticks} ticks: nothing it attends to is a move it can play."
        else:
            self.stalled = False
            self.status = self.over() or "Your move."
        self.post()

    def record_move(self, board, pre, forced=False):
        """The move the mind just made, and what chose it."""
        a = self.mind.agent
        move = self.w.board.peek()
        self.last_move = (move.from_square, move.to_square)
        san = board.san(move).rstrip("+#")
        queue_, running = pre
        if forced:
            why = "forced: you pressed the button"
        elif self.planned_now is not None:
            why = "planner: a way to its want, by its own records"
        elif queue_ or a.running or running:
            why = "experiment: " + pretty(a.running or running or "the next step of one")
        else:
            why = "attention: this move won the top level"
        self.why = f"{san} — {why}"
        watching = a.watching
        if watching:
            pred = a.predict(watching[0], watching[1])
            self.expected = f"{san}: expects " + (", ".join(pretty(x) for x in sorted(pred)) if pred else "nothing known: never tried in this reading")
        self.log.append((self.mind_name, san, why.split(":")[0]))

    def force(self):
        w, a = self.w, self.mind.agent
        if w.board.turn == self.human or self.over():
            return
        for _ in range(8):   # a push being watched finishes first
            if not a.watching:
                break
            self.step(self.mind_name)
        w.actor = self.mind_name
        invs = {inv_id(i): i for i in w.invitations()}
        if not invs:
            return
        bids = a.last_rec["levels"][0]["bids"] if a.last_rec else {}
        best = max(sorted(invs), key=lambda c: max((b for i, b in bids.items() if i.split("|")[0] == c), default=0.0))
        before, board_before = w.moved, w.board.copy()
        a.tick(force=invs[best])
        if w.moved != before:
            self.record_move(board_before, ([], None), forced=True)
        self.finish_turn(before)

    def note_learning(self, n0):
        a = self.mind.agent
        meta = a.mind.meta
        for x, sp in meta.splits.items():
            if x not in self.seen_splits:
                self.seen_splits.add(x)
                self.learned.append(f"{pretty(x.split('|')[0])} depends on: {pretty(sp['tag'])}")
        for _, inv, names in a.tried[n0:]:
            self.learned.append(f"{inv[0].split(' ', 1)[-1]} led to: " + ", ".join(pretty(n) for n in names[:6]))
        del self.learned[:-14]

    # ---- what the window shows ----------------------------------------------------------------------------------------

    def post(self):
        w, a = self.w, self.mind.agent
        mind = a.mind
        rec = a.last_rec
        attention = {}
        if rec:
            top = rec["levels"][-1]
            imagined = mind.imagined(top["bids"])
            for i in top["winners"]:
                attention.setdefault(lane(i, imagined), []).append((round(top["bids"].get(i, 0.0), 2), pretty(i)))
        terr = mind.territory
        holders = Counter(terr.rows[r]["holder"] for r in terr.given if r in terr.rows)
        lost = sorted(r for r in terr.given if terr.rows.get(r, {}).get("holder") == "lost")
        slots = Counter(k for k, _ in terr.open_slots())
        feelings = []
        if mind.phases:
            for p in mind.phases.live():
                inf = mind.phases.info[p]
                feelings.append((round(mind.pool[p].act, 2), inf["kind"], pretty(str(inf["anchor"]))))
            feelings.sort(reverse=True)
        self.out.put(dict(
            fen=w.board.fen(), last=self.last_move, status=self.status, stalled=self.stalled, playing=self.playing,
            human=self.human, mind=self.mind_name, log=list(self.log), ticks=self.ticks, why=self.why, expected=self.expected,
            want=pretty(a.goal) if a.goal else "nothing right now" + (" (a keeper: it holds what it has)" if self.mind.keep else ""),
            stack=[pretty(g) for g in a.stack], attention=attention, feelings=feelings[:8], learned=list(self.learned),
            holders=dict(holders), lost=lost, slots=dict(slots),
            size=dict(pool=len(mind.pool), splits=len(mind.meta.splits), concepts=len(mind.understanding.rel), pushes=len(a.tried))))


# ---- the window ---------------------------------------------------------------------------------------------------------

GLYPH = {"P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔", "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚"}
LANES = ("moves on offer", "experiments", "questions", "ownership", "thoughts", "imagined", "feeling", "about its thinking")


class App:
    SIZE = 68

    def __init__(self, root, args):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.root, self.args, self.engine = tk, root, args, None
        self.sel, self.snap, self.flip = None, None, False
        root.title("Cognitive chess: play the mind")
        top = ttk.Frame(root, padding=6)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(top, text="You play").pack(side="left")
        self.side = tk.StringVar(value=args.side)
        ttk.Combobox(top, textvariable=self.side, values=("white", "black"), width=6, state="readonly").pack(side="left", padx=4)
        ttk.Label(top, text="Self-play games first (N)").pack(side="left", padx=(10, 2))
        self.n = tk.IntVar(value=args.games)
        ttk.Spinbox(top, from_=0, to=200, textvariable=self.n, width=5).pack(side="left")
        ttk.Label(top, text="Seed").pack(side="left", padx=(10, 2))
        self.seed = tk.IntVar(value=args.seed)
        ttk.Spinbox(top, from_=0, to=9999, textvariable=self.seed, width=5).pack(side="left")
        self.start_btn = ttk.Button(top, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=10)
        self.new_btn = ttk.Button(top, text="New game (same mind)", command=lambda: self.engine and self.engine.send("new"), state="disabled")
        self.new_btn.pack(side="left")
        self.force_btn = ttk.Button(top, text="Force a move", command=lambda: self.engine and self.engine.send("force"), state="disabled")
        self.force_btn.pack(side="left", padx=6)
        left = ttk.Frame(root, padding=6)
        left.grid(row=1, column=0, sticky="n")
        self.canvas = tk.Canvas(left, width=8 * self.SIZE, height=8 * self.SIZE, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)
        self.status = tk.StringVar(value="Choose your side and N, then Start.")
        ttk.Label(left, textvariable=self.status, wraplength=8 * self.SIZE, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=4)
        self.moves = tk.Text(left, width=60, height=9, font=("Consolas", 9), state="disabled", wrap="word")
        self.moves.pack(fill="x")
        right = ttk.Frame(root, padding=6)
        right.grid(row=1, column=1, sticky="nsew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        ttk.Label(right, text="Inside the mind", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.panel = tk.Text(right, width=78, height=38, font=("Consolas", 9), state="disabled", wrap="word")
        self.panel.pack(fill="both", expand=True)
        self.panel.tag_configure("h", font=("Consolas", 10, "bold"), foreground="#1a4d8f", spacing1=6)
        self.draw(chess.Board())
        root.after(60, self.poll)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def start(self):
        if self.engine:
            self.engine.send("stop")
        a = self.args
        self.flip = self.side.get() == "black"
        self.engine = Engine(games=int(self.n.get()), side=self.side.get(), seed=int(self.seed.get()),
                             curiosity=a.curiosity, persistence=a.persistence, patience=a.patience)
        self.sel, self.snap = None, None
        self.status.set("Starting…")
        self.new_btn.config(state="disabled")
        self.engine.start()

    def close(self):
        if self.engine:
            self.engine.send("stop")
        self.root.destroy()

    def poll(self):
        latest = None
        if self.engine:
            try:
                while True:
                    latest = self.engine.out.get_nowait()
            except queue.Empty:
                pass
        if latest is not None:
            self.show(latest)
        self.root.after(60, self.poll)

    def show(self, s):
        if "error" in s:
            self.status.set("The engine stopped with an error; see the panel.")
            self.write(self.panel, [("h", "Error"), (None, s["error"])])
            return
        self.snap = s
        self.status.set(s["status"])
        self.draw(chess.Board(s["fen"]))
        self.new_btn.config(state="normal" if s["playing"] else "disabled")
        self.force_btn.config(state="normal" if s["stalled"] else "disabled")
        self.write(self.moves, [(None, " ".join(f"{k // 2 + 1}{'.' if who == 'White' else '…'}{san}" + (f"[{why}]" if why != "you" else "")
                                                 for k, (who, san, why) in enumerate(s["log"])) or "No moves yet.")])
        out = [("h", f"Playing {s['mind']}  ·  tick {s['ticks']} of this turn"),
               ("h", "What it wants"), (None, s["want"] + ("\n  on the way: " + " → ".join(s["stack"]) if s["stack"] else "")),
               ("h", "Its last move, and why"), (None, s["why"] or "–")]
        if s["expected"]:
            out.append((None, s["expected"]))
        out.append(("h", "What holds its attention (top level, bid)"))
        for name in LANES:
            items = s["attention"].get(name)
            if items:
                out.append((None, f"{name}: " + "; ".join(f"{t} {b}" for b, t in sorted(items, reverse=True))))
        out.append(("h", "What it feels"))
        out.append((None, "\n".join(f"{k} about {a} ({v})" for v, k, a in s["feelings"]) or "nothing right now"))
        out.append(("h", "What it holds"))
        out.append((None, f"its pieces: {s['holders']}" + (f"; lost: {', '.join(s['lost'])}" if s["lost"] else "")))
        out.append((None, f"open slots: {s['slots']}"))
        out.append(("h", "What it just learned"))
        out.append((None, "\n".join(s["learned"][-10:]) or "nothing yet"))
        z = s["size"]
        out.append(("h", "Its records"))
        out.append((None, f"{z['pushes']} moves tried; {z['concepts']} concepts; {z['splits']} conditions split on; {z['pool']} molecules in play"))
        self.write(self.panel, out)

    def write(self, widget, parts):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for tag, text in parts:
            widget.insert("end", text + "\n", (tag,) if tag else ())
        widget.config(state="disabled")

    def xy(self, sq):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        return (7 - f, r) if self.flip else (f, 7 - r)

    def square_at(self, x, y):
        c, r = x // self.SIZE, y // self.SIZE
        if not (0 <= c < 8 and 0 <= r < 8):
            return None
        return chess.square(7 - c, r) if self.flip else chess.square(c, 7 - r)

    def draw(self, board):
        cv, S = self.canvas, self.SIZE
        cv.delete("all")
        last = self.snap["last"] if self.snap else None
        targets = set()
        if self.sel is not None:
            targets = {m.to_square for m in board.legal_moves if m.from_square == self.sel}
        for sq in chess.SQUARES:
            c, r = self.xy(sq)
            light = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
            col = "#f0d9b5" if light else "#b58863"
            if last and sq in last:
                col = "#e8e288" if light else "#c9c04f"
            if sq == self.sel:
                col = "#8fbf6a"
            cv.create_rectangle(c * S, r * S, (c + 1) * S, (r + 1) * S, fill=col, outline="")
            if sq in targets:
                cv.create_oval(c * S + S * .38, r * S + S * .38, c * S + S * .62, r * S + S * .62, fill="#4f7a3a", outline="")
            p = board.piece_at(sq)
            if p:
                cv.create_text(c * S + S / 2, r * S + S / 2, text=GLYPH[p.symbol()], font=("Segoe UI Symbol", int(S * .62)), fill="#111111")

    def click(self, e):
        s = self.snap
        if not s or not s["playing"] or s["status"].startswith("The mind is"):
            return
        board = chess.Board(s["fen"])
        if board.turn != s["human"]:
            return
        sq = self.square_at(e.x, e.y)
        if sq is None:
            return
        if self.sel is not None and any(m.from_square == self.sel and m.to_square == sq for m in board.legal_moves):
            self.engine.send("move", self.sel, sq)
            self.sel = None
            self.status.set("The mind is thinking…")
        else:
            p = board.piece_at(sq)
            self.sel = sq if p and p.color == s["human"] else None
        self.draw(board)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=0, help="self-play games before you play (N)")
    ap.add_argument("--side", default="white", choices=("white", "black"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--curiosity", type=float, default=1.0)
    ap.add_argument("--persistence", type=float, default=1.0)
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--smoke", type=float, default=0, help="close the window after this many seconds (a check)")
    args = ap.parse_args()
    import tkinter as tk
    root = tk.Tk()
    app = App(root, args)
    if args.smoke:
        app.start()
        root.after(int(args.smoke * 1000), app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
