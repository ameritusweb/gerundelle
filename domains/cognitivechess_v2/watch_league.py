"""Watch the chess temperament league (league.py) as it plays: a tkinter window that reads the league's files and redraws on Refresh (or
every few seconds with Auto on). Nothing is written; the league is never touched. After go/watch_league.py.

- Standings: each profile's Elo (league/state.json), games, wins, losses and draws (from both its minds), its record as White and as
  Black, and its new forced mates and mates in one passed up (summed over its games).
- The grid: one cell per pairing, the row profile's White mind against the column profile's Black mind; the cell shows the White
  mind's wins-losses-draws in that pairing and how the last game ended, coloured by how the row profile scored.
- Running now: the games in progress (their logs exist but hold no result yet), with each game's half-moves so far.
- Recent games: the latest results.

Run: python -X utf8 watch_league.py [league folder, default cognitivechess_v2/league]"""
import collections
import json
import os
import re
import sys
import tkinter as tk
from tkinter import ttk

FOLDER = sys.argv[1] if len(sys.argv) > 1 else __import__("paths").domain('cognitivechess_v2', 'league')
from league import PROFILES   # (the league's own list: 12 since accepting_patient)
NAMES = list(PROFILES)
SUBROUNDS_PER_ROUND = len(NAMES) - 1
AUTO_MS = 10000


def how(r):
    """A short word for how a game ended."""
    res = r["result"]
    if "resigned" in res:
        return "resign"
    if "cap" in res:
        return "cap"
    if res in ("1-0", "0-1"):
        return "mate"
    m = re.search(r"\((.*)\)", res)
    return (m.group(1) if m else res)[:10]


def tail_half_moves(path):
    """The half-moves so far in a running game's log (its last slice line)."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4000))
            text = f.read().decode("utf-8", "ignore")
    except OSError:
        return None
    found = re.findall(r"half-moves (\d+)", text)
    return int(found[-1]) if found else 0


def read():
    state, results = {}, []
    try:
        with open(os.path.join(FOLDER, "state.json"), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        pass
    try:
        with open(os.path.join(FOLDER, "results.jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except ValueError:
                        pass   # (a line being written)
    except OSError:
        pass
    running = []
    logs = os.path.join(FOLDER, "logs")
    if os.path.isdir(logs):
        done = {r.get("tag") for r in results}
        for name in sorted(os.listdir(logs)):
            tag = name[:-4]
            if name.endswith(".log") and tag not in done:
                full = os.path.join(logs, name)
                finished = None
                try:   # a game finished in a sub-round still playing: its result is its log's last line (league.play), not yet in
                    with open(full, "rb") as f:   # results.jsonl, which the league writes when the whole sub-round is done
                        f.seek(0, 2)
                        f.seek(max(0, f.tell() - 3000))
                        last_line = f.read().decode("utf-8", "ignore").strip().splitlines()[-1:]
                    if last_line and last_line[0].startswith("{"):
                        finished = json.loads(last_line[0])
                except (OSError, ValueError):
                    pass
                if finished:
                    m = re.match(r"r(\d+)_k(\d+)_", tag)
                    if m:
                        finished.update(round=int(m.group(1)), k=int(m.group(2)))
                    results.append(finished)
                else:
                    running.append((tag, tail_half_moves(full), False))
    return state, results, running


def blend(score):
    """A cell's colour from the row profile's score in it (0 lost every game .. 1 won every game); grey with no games."""
    if score is None:
        return "#eeeeee"
    if score >= 0.5:   # white to green
        k = (score - 0.5) * 2
        return "#%02x%02x%02x" % (int(255 - 120 * k), int(255 - 40 * k), int(255 - 120 * k))
    k = (0.5 - score) * 2   # white to red
    return "#%02x%02x%02x" % (int(255 - 30 * k), int(255 - 130 * k), int(255 - 130 * k))


GLYPH = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
OUTLINE = {"k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙"}
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}
SQ, MARGIN = 64, 28


def replay(tag):
    """A running game's board, replayed from its log's moves (both seats' moves are logged by the duel, chessduel.step). -> (board,
    last move uci, the log's last lines)"""
    import chess
    b, last, tail = chess.Board(), None, []
    try:   # (a White first move carried into the game and not logged, by the league before 2026-11-17's fix: <tag>.first)
        with open(os.path.join(FOLDER, "logs", f"{tag}.first"), encoding="utf-8") as f:
            last = f.read().strip()
            b.push_uci(last)
    except (OSError, ValueError):
        pass
    try:
        with open(os.path.join(FOLDER, "logs", f"{tag}.log"), encoding="utf-8") as f:
            for line in f:
                if "game over" in line:
                    break
                tail = (tail + [line.rstrip()])[-6:]
                m = re.search(r"(?:White|Black)\s+[\d.]+s: .*?moved \d+ ([a-h][1-8][a-h][1-8][qrbn]?)", line)
                if m:
                    try:
                        b.push_uci(m.group(1))
                        last = m.group(1)
                    except ValueError:
                        break
    except OSError:
        pass
    return b, last, tail


class GameTab:
    """A tab with one running game's board."""

    def __init__(self, book, tag):
        self.tag = tag
        self.frame = ttk.Frame(book, padding=10)
        m = re.match(r"r(\d+)_k(\d+)_(.+)_vs_(.+)", tag)
        self.white, self.black = (m.group(3), m.group(4)) if m else ("?", "?")
        book.add(self.frame, text=f"{self.white} v {self.black}")
        ttk.Label(self.frame, text=f"{self.white} (White) vs {self.black} (Black)   [{tag}]",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        row = ttk.Frame(self.frame)
        row.pack(anchor="nw", pady=8)
        size = 8 * SQ + 2 * MARGIN
        self.canvas = tk.Canvas(row, width=size, height=size, bg="white", highlightthickness=0)
        self.canvas.pack(side="left")
        side = ttk.Frame(row, padding=(16, 0))
        side.pack(side="left", fill="y")
        self.info = ttk.Label(side, text="", font=("Consolas", 11), justify="left")
        self.info.pack(anchor="nw")
        ttk.Label(side, text="Log (last lines)", font=("Segoe UI", 10, "bold")).pack(anchor="nw", pady=(16, 0))
        self.log = tk.Text(side, width=110, height=6, font=("Consolas", 9), wrap="none")
        self.log.pack(anchor="nw")
        head = ttk.Frame(side)
        head.pack(anchor="nw", pady=(12, 0))
        ttk.Label(head, text="Why: the last", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.n_why = tk.IntVar(value=6)
        ttk.Spinbox(head, from_=1, to=60, width=4, textvariable=self.n_why, command=self.refresh).pack(side="left", padx=4)
        ttk.Label(head, text="moves, newest first (each mind's own record: how it chose, what it wanted and avoided, what the move was "
                             "predicted to do, the tournament's top)", font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(head, text="Copy", command=self.copy_why).pack(side="left", padx=8)
        self.copied = ttk.Label(head, text="", font=("Segoe UI", 9))
        self.copied.pack(side="left")
        box = ttk.Frame(side)
        box.pack(anchor="nw", fill="both", expand=True)
        self.why = tk.Text(box, width=130, height=22, font=("Consolas", 9), wrap="word")
        scroll = ttk.Scrollbar(box, command=self.why.yview)
        self.why.configure(yscrollcommand=scroll.set)
        self.why.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

    def copy_why(self):
        """The explanations shown, to the clipboard (with the game's name on top)."""
        text = f"{self.white} (White) vs {self.black} (Black) [{self.tag}]\n\n" + self.why.get("1.0", "end").strip() + "\n"
        top = self.frame.winfo_toplevel()
        top.clipboard_clear()
        top.clipboard_append(text)
        top.update()   # (keeps the clipboard's contents after the window moves on)
        self.copied.config(text="copied")
        self.frame.after(2000, lambda: self.copied.config(text=""))

    def refresh(self):
        import chess
        b, last, tail = replay(self.tag)
        c = self.canvas
        c.delete("all")
        lm = chess.Move.from_uci(last) if last else None
        king = b.king(b.turn) if b.is_check() else None
        for sq in chess.SQUARES:
            f, r = chess.square_file(sq), chess.square_rank(sq)
            x, y = MARGIN + f * SQ, MARGIN + (7 - r) * SQ
            light = (f + r) % 2 == 1
            colour = "#f0d9b5" if light else "#b58863"
            if lm and sq in (lm.from_square, lm.to_square):
                colour = "#cdd26a" if light else "#aaa23a"
            if sq == king:
                colour = "#e65050"
            c.create_rectangle(x, y, x + SQ, y + SQ, fill=colour, outline="")
            p = b.piece_at(sq)
            if p:
                s = p.symbol().lower()
                cx, cy = x + SQ / 2, y + SQ / 2 + 2
                if p.color:   # White: the solid glyph filled white under the outline glyph
                    c.create_text(cx, cy, text=GLYPH[s], font=("Segoe UI Symbol", 40), fill="white")
                    c.create_text(cx, cy, text=OUTLINE[s], font=("Segoe UI Symbol", 40), fill="black")
                else:
                    c.create_text(cx, cy, text=GLYPH[s], font=("Segoe UI Symbol", 40), fill="black")
        for i in range(8):
            c.create_text(MARGIN + i * SQ + SQ / 2, MARGIN + 8 * SQ + 14, text="abcdefgh"[i], font=("Segoe UI", 11))
            c.create_text(MARGIN / 2, MARGIN + i * SQ + SQ / 2, text=str(8 - i), font=("Segoe UI", 11))
        mat = {True: 0, False: 0}
        for p in b.piece_map().values():
            mat[p.color] += VALUE[p.symbol().lower()]
        to_move = "White" if b.turn else "Black"
        self.info.config(text=f"half-moves  {len(b.move_stack)}\n"
                              f"to move     {to_move}{' (in check)' if b.is_check() else ''}\n"
                              f"last move   {last or '-'}\n"
                              f"material    White {mat[True]}, Black {mat[False]} ({mat[True] - mat[False]:+d})\n"
                              f"fifty-move  {b.halfmove_clock} half-moves since a capture or pawn move\n\n"
                              f"FEN  {b.fen()}")
        self.log.delete("1.0", "end")
        self.log.insert("end", "\n".join(tail))
        entries = []
        try:
            with open(os.path.join(FOLDER, "logs", f"{self.tag}.why.jsonl"), encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except ValueError:
                        pass   # (a line being written)
        except OSError:
            pass
        try:
            n = max(1, int(self.n_why.get()))
        except (tk.TclError, ValueError):
            n = 6
        top = self.why.yview()[0]
        self.why.delete("1.0", "end")
        if not entries:
            self.why.insert("end", "(no explanations yet: games started before 2026-11-17's change have none)")
        for e in reversed(entries[-n:]):
            self.why.insert("end", e.get("text", "") + "\n\n")
        self.why.yview_moveto(top)


class Watch(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Chess temperament league: {FOLDER}")
        self.geometry("1900x940")
        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        self.auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text=f"Auto ({AUTO_MS // 1000}s)", variable=self.auto, command=self.tick).pack(side="left", padx=8)
        self.status = ttk.Label(top, text="", font=("Segoe UI", 10))
        self.status.pack(side="left", padx=12)

        self.book = ttk.Notebook(self)
        self.book.pack(fill="both", expand=True)
        body = ttk.Frame(self.book, padding=6)
        self.book.add(body, text="League")
        self.boards = {}   # tag -> GameTab, one per running game
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Standings", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("rank", "profile", "elo", "games", "w", "l", "d", "as_white", "as_black", "mates", "passed")
        heads = ("#", "profile", "Elo", "games", "W", "L", "D", "as White W-L-D", "as Black W-L-D", "forced mates", "mate-in-1 passed")
        widths = (28, 90, 50, 48, 32, 32, 32, 100, 100, 84, 104)
        self.table = ttk.Treeview(left, columns=cols, show="headings", height=len(NAMES))
        for c, h, wd in zip(cols, heads, widths):
            self.table.heading(c, text=h)
            self.table.column(c, width=wd, anchor="center")
        self.table.pack(anchor="w")
        ttk.Label(left, text="Running now", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.running = tk.Listbox(left, height=11, width=70, font=("Consolas", 9))
        self.running.pack(anchor="w")
        ttk.Label(left, text="Recent games", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.recent = tk.Listbox(left, height=16, width=110, font=("Consolas", 9))
        self.recent.pack(anchor="w", fill="y", expand=True)

        right = ttk.Frame(body, padding=(16, 0))
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="The grid: row = that profile's White mind, column = Black mind; cell = row's W-L-D, last game's ending "
                              "and White's balance", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.grid_frame = ttk.Frame(right)
        self.grid_frame.pack(anchor="nw", pady=6)
        self.cells = {}
        tk.Label(self.grid_frame, text="White \\ Black", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="nsew")
        for j, n in enumerate(NAMES):
            tk.Label(self.grid_frame, text=n, font=("Segoe UI", 8, "bold"), width=9, wraplength=70).grid(row=0, column=j + 1, sticky="nsew")
        for i, rname in enumerate(NAMES):
            tk.Label(self.grid_frame, text=rname, font=("Segoe UI", 8, "bold"), anchor="e", width=10).grid(row=i + 1, column=0, sticky="nsew")
            for j, cname in enumerate(NAMES):
                lab = tk.Label(self.grid_frame, text="", width=9, height=3, relief="ridge", font=("Consolas", 8), bg="#eeeeee")
                lab.grid(row=i + 1, column=j + 1, sticky="nsew", padx=1, pady=1)
                self.cells[(rname, cname)] = lab
        self.refresh()
        self.tick()

    def tick(self):
        if getattr(self, "_job", None):
            self.after_cancel(self._job)
            self._job = None
        if self.auto.get():
            self._job = self.after(AUTO_MS, lambda: (self.refresh(), self.tick()))

    def refresh(self):
        state, results, running = read()
        elo = state.get("elo", {})
        done = len(state.get("done", []))
        rec = {n: collections.Counter() for n in NAMES}
        pair = collections.defaultdict(lambda: collections.Counter())
        last = {}
        for r in results:
            w, b, win = r["white"], r["black"], r["winner"]
            if win == "white":
                rec[w]["w"] += 1; rec[w]["ww"] += 1; rec[b]["l"] += 1; rec[b]["bl"] += 1
                pair[(w, b)]["w"] += 1
            elif win == "black":
                rec[w]["l"] += 1; rec[w]["wl"] += 1; rec[b]["w"] += 1; rec[b]["bw"] += 1
                pair[(w, b)]["l"] += 1
            else:
                rec[w]["d"] += 1; rec[w]["wd"] += 1; rec[b]["d"] += 1; rec[b]["bd"] += 1
                pair[(w, b)]["d"] += 1
            rec[w]["fm"] += r.get("white_new_forced_mates", 0); rec[b]["fm"] += r.get("black_new_forced_mates", 0)
            rec[w]["mp"] += r.get("white_mates_passed", 0); rec[b]["mp"] += r.get("black_mates_passed", 0)
            last[(w, b)] = r
        for item in self.table.get_children():
            self.table.delete(item)
        order = sorted(NAMES, key=lambda n: -elo.get(n, 1500.0))
        for k, n in enumerate(order, 1):
            c = rec[n]
            self.table.insert("", "end", values=(k, n, f"{elo.get(n, 1500.0):.0f}", c["w"] + c["l"] + c["d"], c["w"], c["l"], c["d"],
                                                 f"{c['ww']}-{c['wl']}-{c['wd']}", f"{c['bw']}-{c['bl']}-{c['bd']}", c["fm"], c["mp"]))
        for (rname, cname), lab in self.cells.items():
            if rname == cname:
                lab.config(text="—", bg="#d9d9d9")
                continue
            p = pair.get((rname, cname))
            if not p:
                lab.config(text="", bg=blend(None))
                continue
            n = p["w"] + p["l"] + p["d"]
            score = (p["w"] + 0.5 * p["d"]) / n
            r = last[(rname, cname)]
            lab.config(text=f"{p['w']}-{p['l']}-{p['d']}\n{how(r)} {r['white_balance']:+d}", bg=blend(score))
        self.running.delete(0, "end")
        live = [x for x in running if not x[2]]
        for tag, hm, _ in live:
            self.running.insert("end", f"{tag:<52} half-moves {hm if hm is not None else '?'}")
        live_tags = {tag for tag, _, _ in live}
        for tag in [t for t in self.boards if t not in live_tags]:   # a finished game's tab goes
            self.book.forget(self.boards.pop(tag).frame)
        for tag in sorted(live_tags):
            if tag not in self.boards:
                self.boards[tag] = GameTab(self.book, tag)
            self.boards[tag].refresh()
        self.recent.delete(0, "end")
        for r in reversed(results[-60:]):
            self.recent.insert("end", f"r{r.get('round', 0) + 1}.{r.get('k', '?'):<2} {r['white']:>11} (W) vs {r['black']:<11} (B): "
                                      f"{r['result']:<40} {r['half_moves']:>3} hm  bal {r['white_balance']:+3d}  "
                                      f"mates W{r.get('white_new_forced_mates', 0)}/B{r.get('black_new_forced_mates', 0)}  {r['seconds']:>5}s")
        totals = collections.Counter(r["winner"] for r in results)
        rnd = done // SUBROUNDS_PER_ROUND + 1
        self.status.config(text=f"sub-rounds done {done} (round {rnd}, sub-round {done % SUBROUNDS_PER_ROUND + 1} next)   games {len(results)}   "
                                f"White {totals['white']}  Black {totals['black']}  draws {totals['draw']}   running {len(live)}")


if __name__ == "__main__":
    Watch().mainloop()
