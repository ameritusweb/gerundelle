"""Watch a tetris mind play from a checkpoint (the user, 2026-11-11: "a tkinter app that shows the 17000 checkpoint tetris mind
playing"). Loads a checkpoint (checkpoint.py), goes on from it one slice at a time exactly as the run did (the world's potential
forces to the mind, the mind's tick, luck earned), and draws the well after each slice with what the mind is doing beside it.

The well: each settled block in the colour of the piece it came in; the falling piece outlined; a row or a piece coming apart in white;
blocks with nothing under them (falling after a clear) hatched. Beside it: the slice, the mind's decision (a push, a wait, or watching
what its last push did), what was on offer, its want and the wants above it, the anti-want held, the phases in its pool, the
predictions it owns, luck and what it has earned, and its last decisions.

The mind runs in its own thread and only that thread touches it; the window reads snapshots. Nothing is saved: closing the window
leaves the checkpoint as it was. A late mind takes a second or more a slice.

Run: python watch_mind.py [slice or checkpoint file, default 17000]      e.g. python watch_mind.py 18000, for
     checkpoints/decisions_18000.pkl (it restarts itself with PYTHONHASHSEED=0, the seed the checkpoints were saved with)
     python watch_mind.py [checkpoint] --smoke 3     load, run 3 slices, draw one frame and close (a check, no window left open)
     python watch_mind.py clean3_13000 --commit     the same mind with the commit push on offer (Params.commit): when it commits to a
                                                    prediction, the decision line says so until the world answers
     --as-saved: the well as the checkpoint saved it (without it the well is set back empty on load, as a game ends)
"""
import collections
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("PYTHONHASHSEED") != "0":   # the checkpoints were saved under hash seed 0: the same seed, or the run isn't the same run
    env = dict(os.environ, PYTHONHASHSEED="0")
    sys.exit(subprocess.call([sys.executable, "-X", "utf8", os.path.abspath(__file__), *sys.argv[1:]], env=env, cwd=HERE))

os.chdir(HERE)
sys.path.insert(0, HERE)
import tkinter as tk  # noqa: E402

CELL = 26
PALETTE = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
           "#dcbeff", "#9a6324", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075"]
SMOKE = int(sys.argv[sys.argv.index("--smoke") + 1]) if "--smoke" in sys.argv else 0
AS_SAVED = "--as-saved" in sys.argv   # the checkpoint's well as it was; without it the well is set back empty on load
skip = {sys.argv.index("--smoke") + 1} if "--smoke" in sys.argv else set()
args = [x for k, x in enumerate(sys.argv) if k >= 1 and k not in skip and not x.startswith("--")]
PATH = args[0] if args else "checkpoints/decisions_17000.pkl"
if PATH.isdigit():   # a checkpoint by its slice: 18000 -> checkpoints/decisions_18000.pkl
    PATH = f"checkpoints/decisions_{PATH}.pkl"
elif not os.path.exists(PATH) and os.path.exists(f"checkpoints/{PATH}.pkl"):   # or by its name: clean3_13000
    PATH = f"checkpoints/{PATH}.pkl"
if not os.path.exists(PATH):
    import glob
    have = sorted(int(os.path.basename(p)[len("decisions_"):-len(".pkl")]) for p in glob.glob("checkpoints/decisions_*.pkl")
                  if os.path.basename(p)[len("decisions_"):-len(".pkl")].isdigit())
    sys.exit(f"no checkpoint at {PATH}; saved so far: {', '.join(str(n) for n in have) or 'none'}")


def snapshot(a, w, t, choice, offers, took):
    """What the window draws: read from the agent and the world by the mind's thread, plain values only."""
    falling = dict(zip(w.part_list(), w.piece_blocks)) if w.piece is not None else {}
    cells = {}
    for c, b in w.block_at.items():
        cells[c] = dict(piece=w.piece_of.get(b), falling=False, apart=(c[1] in w.coming_apart or w.piece_of.get(b) in w.clearing), loose=b in w.loose)
    for c, b in falling.items():
        if c[1] >= 0:
            cells[c] = dict(piece=w.piece_of.get(b), falling=True, apart=False, loose=False)
    phases = collections.Counter(i.split(":")[1] for i in a.mind.pool if i.startswith("phase:"))
    com = a.__dict__.get("committed")
    decision = (f"committed: watching until slice {com['ins']['due']}" if com and (choice is None or choice[0] == "commit") else
                "watching what its push did" if choice is None and a.watching else "wait" if choice is None else choice[0].replace("_", " "))
    return dict(t=t, cells=cells, width=w.width, height=w.height, doing=w.doing, alignment=w.shown.get("piece_alignment"),
                decision=decision, pushed=choice is not None, offers=[i[0].replace("_", " ") for i in offers],
                goal=a.goal, stack=list(a.stack), anti=a.__dict__.get("anti"), phases=dict(phases),
                predictions=len(a.__dict__.get("predicted", {})), luck=w.luck, earned=w.earned, placed=w.placed, lines=w.lines,
                pieces_cleared=w.__dict__.get("pieces_cleared", 0), games=len(w.games), took=took,
                regions=len(a.mind.territory.rows), pool=len(a.mind.pool))


def anti_words(anti):
    """The anti-want as what it is, a loss the mind doesn't want (its name is the region lost: first shown bare, and a lost prediction
    read as if the clear itself were unwanted)."""
    if not anti:
        return "none"
    if anti.startswith("potential_"):   # an owned prediction: losing it
        return f"losing my prediction: {anti[len('potential_'):].replace('_', ' ')}"
    if anti.startswith("held_"):   # relative: a region it holds, doing that
        return f"losing a region I hold while it is {anti[len('held_'):].replace('_', ' ')}"
    return f"losing {anti.replace('_', ' ')}"


def amnesia(a, w):
    """The viewer's, not the mind's (Gerundelle forgets nothing by itself: dormancy stores and wakes): the well set back empty, and the
    game that was in it forgotten, so the mind starts a new well without living the old one's blocks as lost. A push in flight is
    abandoned (its watch, any experiment's steps), and every block of the well, its sides and bond, is wiped: its territory row, its last
    sight (last_seen, seen_objs), the concepts about it in the SOV, every molecule naming it (ownership slots, candidate wants, SOV
    molecules, questions), a want or sub-want about it, and the predictions pending (unanswered, not rejected). What it has learned of
    pushes, rows, cells, its owned predictions, Abstract's patterns and its temperament stays. -> how many objects were forgotten."""
    gone = set()
    for b in set(w.block_at.values()) | set(w.piece_blocks):
        gone |= {b, f"{b}_left", f"{b}_right", f"{b}_bond"}
    w.reset()   # (the world's own set-back: the well empty, a new piece forming, the game counted)
    w.diffs = []
    a.watching, a.queue, a.running, a.intent = None, [], None, None
    mind, terr, und = a.mind, a.mind.territory, a.mind.understanding
    about = lambda s: any(s == o or s.startswith(o + "_") or f":{o}" in s or f":{o}_" in s for o in gone)
    for o in gone:
        terr.rows.pop(o, None)
        terr.given.discard(o)
        terr.__dict__.get("dormant", {}).pop(o, None)
        a.__dict__.get("last_seen", {}).pop(o, None)
        a.seen_objs.discard(o)
    for c in [c for c in und.rel if about(c)]:
        del und.rel[c]
    for i in [i for i in mind.pool if about(i)]:
        del mind.pool[i]
    for q in [q for q in und.questions if about(q)]:
        del und.questions[q]
    if a.goal is not None and about(a.goal):
        a.goal = a.stack.pop() if a.stack else None
    a.stack = [g for g in a.stack if not about(g)]
    a.__dict__["predicted"] = {}   # pending predictions: unanswered (their owned regions stay held)
    if a.__dict__.get("last_seen") is not None:   # the new well as its first sight
        a.last_seen.update(w.states())
    return len(gone)


class Mind(threading.Thread):
    """The mind's own thread: loads the checkpoint, then a slice at a time while playing (or one when stepped)."""

    def __init__(self, path, out):
        super().__init__(daemon=True)
        self.path, self.out = path, out
        self.playing, self.step, self.stop, self.delay = threading.Event(), threading.Event(), threading.Event(), 0.0
        self.playing.set()

    def run(self):
        import checkpoint
        import run
        try:
            self.out.put(("status", f"loading {self.path} ..."))
            t0 = time.time()
            a, w, t = checkpoint.load(self.path)
            if "--commit" in sys.argv:   # the commit push switched on for this mind (Params.commit; the user, 2026-11-12)
                a.mind.p.commit = True
            self.out.put(("status", f"loaded at slice {t} in {time.time() - t0:.0f}s"))
            if not AS_SAVED and (w.settled or w.placed):   # start from an empty well, the game in it forgotten (the user: "why can't you just
                n = amnesia(a, w)                          # clear the pieces?", "why isn't there something like an 'amnesia' memory wipe?")
                self.out.put(("status", f"loaded at slice {t} in {time.time() - t0:.0f}s; the well set back empty and its game forgotten "
                                        f"({n} objects); --as-saved shows the checkpoint as it was"))
            self.out.put(("frame", snapshot(a, w, t, None, w.invitations(), 0.0)))
            while not self.stop.is_set():
                if not self.playing.is_set() and not self.step.is_set():
                    time.sleep(0.05)
                    continue
                self.step.clear()
                t1 = time.time()
                offers = w.invitations()
                a.mind.potentials = w.potentials()
                choice, rec = a.tick()
                run.after_tick(a, w)   # luck, clears, the open rows, the pieces on the ground: as run.py (first the rows were missing here)
                t += 1
                self.out.put(("frame", snapshot(a, w, t, choice, offers, time.time() - t1)))
                if self.delay:
                    time.sleep(self.delay)
        except Exception as e:   # shown in the window, not lost in a thread
            import traceback
            self.out.put(("status", f"stopped: {type(e).__name__}: {e}"))
            self.out.put(("error", traceback.format_exc()))


class App:
    def __init__(self, root, path):
        self.root, self.q = root, queue.Queue()
        root.title(f"Tetris mind: {os.path.basename(path)}")
        root.configure(bg="#1b1b1f")
        self.canvas = tk.Canvas(root, width=10 * CELL + 2, height=20 * CELL + 2, bg="#0e0e11", highlightthickness=1, highlightbackground="#444")
        self.canvas.grid(row=0, column=0, rowspan=3, padx=12, pady=12)
        self.status = tk.Label(root, text="starting ...", fg="#cfcfcf", bg="#1b1b1f", font=("Segoe UI", 10), anchor="w", justify="left")
        self.status.grid(row=0, column=1, sticky="nw", padx=(0, 12), pady=(12, 0))
        self.info = tk.Label(root, text="", fg="#e8e8e8", bg="#1b1b1f", font=("Consolas", 10), anchor="nw", justify="left", width=62)
        self.info.grid(row=1, column=1, sticky="nw", padx=(0, 12))
        bar = tk.Frame(root, bg="#1b1b1f")
        bar.grid(row=2, column=1, sticky="sw", padx=(0, 12), pady=(0, 12))
        self.toggle = tk.Button(bar, text="Pause", width=8, command=self.pause)
        self.toggle.pack(side="left")
        tk.Button(bar, text="Step", width=8, command=self.step).pack(side="left", padx=6)
        tk.Label(bar, text="  hold each slice (s)", fg="#cfcfcf", bg="#1b1b1f").pack(side="left")
        self.hold = tk.Scale(bar, from_=0, to=2, resolution=0.1, orient="horizontal", length=140, bg="#1b1b1f", fg="#cfcfcf",
                             highlightthickness=0, command=lambda v: setattr(self.mind, "delay", float(v)))
        self.hold.pack(side="left")
        self.recent = collections.deque(maxlen=14)
        self.mind = Mind(path, self.q)
        self.mind.start()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.poll)

    def pause(self):
        if self.mind.playing.is_set():
            self.mind.playing.clear()
            self.toggle.config(text="Play")
        else:
            self.mind.playing.set()
            self.toggle.config(text="Pause")

    def step(self):
        self.mind.playing.clear()
        self.toggle.config(text="Play")
        self.mind.step.set()

    def close(self):
        self.mind.stop.set()
        self.root.destroy()

    def poll(self):
        frame = None
        try:
            while True:
                kind, x = self.q.get_nowait()
                if kind == "status":
                    self.status.config(text=x)
                elif kind == "error":
                    print(x, file=sys.stderr, flush=True)
                else:
                    frame = x
                    if x["pushed"] or x["decision"] == "wait":
                        self.recent.appendleft(f"{x['t']:>6}  {x['decision']}")
        except queue.Empty:
            pass
        if frame is not None:
            self.draw(frame)
        self.root.after(50, self.poll)

    def draw(self, f):
        c = self.canvas
        c.delete("all")
        for x in range(f["width"] + 1):
            c.create_line(1 + x * CELL, 1, 1 + x * CELL, 1 + f["height"] * CELL, fill="#1d1d22")
        for y in range(f["height"] + 1):
            c.create_line(1, 1 + y * CELL, 1 + f["width"] * CELL, 1 + y * CELL, fill="#1d1d22")
        for (x, y), cell in f["cells"].items():
            colour = "#ffffff" if cell["apart"] else PALETTE[(cell["piece"] or 0) % len(PALETTE)]
            x0, y0 = 1 + x * CELL, 1 + y * CELL
            c.create_rectangle(x0 + 1, y0 + 1, x0 + CELL - 1, y0 + CELL - 1, fill=colour, outline="#ffffff" if cell["falling"] else "#000000",
                               width=2 if cell["falling"] else 1, stipple="gray50" if cell["loose"] else "")
        short = lambda s, n=44: s if s is None or len(str(s)) <= n else str(s)[:n - 1] + "…"
        lines = [
            f"slice           {f['t']}    ({f['took']:.1f}s for this slice)",
            f"the piece       {f['doing']}, {f['alignment']}",
            f"decision        {f['decision']}",
            f"on offer        {', '.join(f['offers']) or 'nothing (gravity carries it)'}",
            "",
            f"want            {short(f['goal'])}",
            f"wants above     {len(f['stack'])}" + (f": {short(f['stack'][-1], 36)}" if f["stack"] else ""),
            f"anti-want       {anti_words(f['anti'])}",
            f"phases          {', '.join(f'{k} {v}' for k, v in sorted(f['phases'].items(), key=lambda kv: -kv[1])) or 'none'}",
            f"predictions     {f['predictions']} standing",
            "",
            f"luck            {f['luck']}   (earned down {f['earned']} times)",
            f"this game       {f['placed']} pieces placed",
            f"over the run    {f['lines']} rows cleared, {f['pieces_cleared']} pieces cleared by runs, {f['games']} games ended",
            f"the mind        {f['regions']} regions in its territory, {f['pool']} molecules in its pool",
            "",
            "last decisions (slice, what it did):",
        ] + [f"  {r}" for r in self.recent]
        self.info.config(text="\n".join(lines))


if __name__ == "__main__":   # (a script: the window; imported, only its pieces, e.g. amnesia for a trace)
    if SMOKE:   # load, run a few slices, draw one frame, close
        q = queue.Queue()
        m = Mind(PATH, q)
        m.playing.clear()
        m.start()
        frames, deadline = 0, time.time() + 900
        last = None
        while frames < SMOKE + 1 and time.time() < deadline:
            kind, x = q.get(timeout=900)
            if kind == "status":
                print(x, flush=True)
            elif kind == "error":
                print(x, flush=True)
                sys.exit(1)
            else:
                frames, last = frames + 1, x
                print(f"frame at slice {x['t']}: {len(x['cells'])} cells drawn, decision {x['decision']}, on offer {x['offers']}, luck {x['luck']}, took {x['took']:.1f}s", flush=True)
                m.step.set()
        m.stop.set()
        root = tk.Tk()
        app = App.__new__(App)
        app.root, app.recent = root, collections.deque(["  17001  drop"], maxlen=14)
        app.canvas = tk.Canvas(root, width=10 * CELL + 2, height=20 * CELL + 2)
        app.info = tk.Label(root)
        app.draw(last)
        root.update()
        print("drew one frame:", len(app.canvas.find_all()), "canvas items;", app.info.cget("text").splitlines()[2])
        root.destroy()
    else:
        root = tk.Tk()
        App(root, PATH)
        root.mainloop()
