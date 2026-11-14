"""Watch the temperament league (league.py) as it plays: a tkinter window that reads the league's files and redraws on Refresh (or every
few seconds with Auto on). Nothing is written; the league is never touched.

- Standings: each profile's Elo (league/state.json), games, wins, losses and draws (from both its minds), and its record as Black
  and as White.
- The grid: one cell per pairing, the row profile's Black mind against the column profile's White mind; the cell shows the Black
  mind's wins-losses-draws in that pairing and the last game's area, coloured by how the row profile scored.
- Running now: the games of the sub-round in progress (their logs exist but hold no result yet).
- Recent games: the latest results.

Run: python -X utf8 watch_league.py [league folder, default go/league]"""
import collections
import json
import os
import sys
import tkinter as tk
from tkinter import ttk

FOLDER = sys.argv[1] if len(sys.argv) > 1 else __import__("paths").domain('go', 'league')
def names_of(folder):
    """The profiles the folder's league plays: an evolution's population (population.json, evo_make.py) in its order, else the minds
    saved there, else the first league's eleven."""
    try:
        with open(os.path.join(folder, "population.json"), encoding="utf-8") as f:
            return list(json.load(f)["population"])
    except (OSError, ValueError, KeyError):
        pass
    minds = os.path.join(folder, "minds")
    if os.path.isdir(minds):
        found = sorted(n[:-len("_black.pkl")] for n in os.listdir(minds) if n.endswith("_black.pkl"))
        if found:
            return found
    return ["steady", "impatient", "patient", "restless", "dogged", "trusting", "skeptical", "averse", "unflinching", "accepting", "grieving"]


NAMES = names_of(FOLDER)
SUBROUNDS_PER_ROUND = len(NAMES) - 1
AUTO_MS = 10000


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
        for name in os.listdir(logs):
            tag = name[:-4]
            if name.endswith(".log") and tag not in done:
                running.append(tag)
    return state, results, sorted(running)


def blend(score):
    """A cell's colour from the row profile's score in it (0 lost every game .. 1 won every game); grey with no games."""
    if score is None:
        return "#eeeeee"
    if score >= 0.5:   # white to green
        k = (score - 0.5) * 2
        return "#%02x%02x%02x" % (int(255 - 120 * k), int(255 - 40 * k), int(255 - 120 * k))
    k = (0.5 - score) * 2   # white to red
    return "#%02x%02x%02x" % (int(255 - 30 * k), int(255 - 130 * k), int(255 - 130 * k))


class Watch(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Go temperament league: {FOLDER}")
        self.geometry("1880x940")
        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left")
        self.auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text=f"Auto ({AUTO_MS // 1000}s)", variable=self.auto, command=self.tick).pack(side="left", padx=8)
        self.status = ttk.Label(top, text="", font=("Segoe UI", 10))
        self.status.pack(side="left", padx=12)

        body = ttk.Frame(self, padding=6)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Standings", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cols = ("rank", "profile", "elo", "games", "w", "l", "d", "as_black", "as_white")
        heads = ("#", "profile", "Elo", "games", "W", "L", "D", "as Black W-L-D", "as White W-L-D")
        widths = (28, 90, 50, 48, 32, 32, 32, 100, 100)
        self.table = ttk.Treeview(left, columns=cols, show="headings", height=len(NAMES))
        for c, h, wd in zip(cols, heads, widths):
            self.table.heading(c, text=h)
            self.table.column(c, width=wd, anchor="center")
        self.table.pack(anchor="w")
        ttk.Label(left, text="Running now", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.running = tk.Listbox(left, height=11, width=52, font=("Consolas", 9))
        self.running.pack(anchor="w")
        ttk.Label(left, text="Recent games", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 0))
        self.recent = tk.Listbox(left, height=16, width=78, font=("Consolas", 9))
        self.recent.pack(anchor="w", fill="y", expand=True)

        right = ttk.Frame(body, padding=(16, 0))
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="The grid: row = that profile's Black mind, column = White mind; cell = row's W-L-D, last game's area (B-W)",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.grid_frame = ttk.Frame(right)
        self.grid_frame.pack(anchor="nw", pady=6)
        self.cells = {}
        tk.Label(self.grid_frame, text="Black \\ White", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="nsew")
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
            b, w, win = r["black"], r["white"], r["winner"]
            if win == "black":
                rec[b]["w"] += 1; rec[b]["bw"] += 1; rec[w]["l"] += 1; rec[w]["wl"] += 1
                pair[(b, w)]["w"] += 1
            elif win == "white":
                rec[b]["l"] += 1; rec[b]["bl"] += 1; rec[w]["w"] += 1; rec[w]["ww"] += 1
                pair[(b, w)]["l"] += 1
            else:
                rec[b]["d"] += 1; rec[b]["bd"] += 1; rec[w]["d"] += 1; rec[w]["wd"] += 1
                pair[(b, w)]["d"] += 1
            last[(b, w)] = r
        for item in self.table.get_children():
            self.table.delete(item)
        order = sorted(NAMES, key=lambda n: -elo.get(n, 1500.0))
        for k, n in enumerate(order, 1):
            c = rec[n]
            self.table.insert("", "end", values=(k, n, f"{elo.get(n, 1500.0):.0f}", c["w"] + c["l"] + c["d"], c["w"], c["l"], c["d"],
                                                 f"{c['bw']}-{c['bl']}-{c['bd']}", f"{c['ww']}-{c['wl']}-{c['wd']}"))
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
            lab.config(text=f"{p['w']}-{p['l']}-{p['d']}\n{r['black_area']}-{r['white_area']}" + (" called" if r.get("called") else ""),
                       bg=blend(score))
        self.running.delete(0, "end")
        for tag in running:
            self.running.insert("end", tag)
        self.recent.delete(0, "end")
        for r in reversed(results[-60:]):
            self.recent.insert("end", f"r{r.get('round', 0) + 1}.{r.get('k', '?'):<2} {r['black']:>11} (B) vs {r['white']:<11} (W): "
                                      f"{r['winner']:<5} {r['black_area']:>2}-{r['white_area']:<2} {r['stones']:>3} stones {r['seconds']:>4}s")
        totals = collections.Counter(r["winner"] for r in results)
        rnd = done // SUBROUNDS_PER_ROUND + 1
        self.status.config(text=f"sub-rounds done {done} (round {rnd}, sub-round {done % SUBROUNDS_PER_ROUND + 1} next)   games {len(results)}   "
                                f"Black {totals['black']}  White {totals['white']}  draws {totals['draw']}   running {len(running)}")


if __name__ == "__main__":
    Watch().mainloop()
