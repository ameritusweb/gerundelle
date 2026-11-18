"""The lifelong coverage test (PLAN.md, L1-L3, written before the run): one mind lives episodes in the fork rooms (cover_rooms.json), one
room per episode: White's move (the mind's), random Black's reply, then the next room. Walk-ins: the room's moves that would uncover a
set (the covers-on reading, the same list for both arms).
python -u -X utf8 cover_lifelong.py on|off [passes]  -> cover_lifelong_<arm>.log"""
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
import rung4p
from chessduel import configure
from gameworld import RandomSide
from plansworld import give, read_mate_passed
from rung4 import TURN_STEPS
from rustboard import TOTAL_SQUARES, WarpBoard, square_name
from warpworld import NAMES

arm = sys.argv[1]
passes = int(sys.argv[2]) if len(sys.argv) > 2 else 3
rooms = json.load(open("cover_rooms.json"))
order = [r for _ in range(passes) for r in rooms]
w, a = rung4p.build(0, order[0]["fen"], dreams=True, half_moves=2)
configure(a)
w.covers_read = arm == "on"
w.shown = w.read()
black = RandomSide(w, 0)
give(a, w)
walked, first_walk, l1 = [], None, None
t0 = time.time()
for ep, room in enumerate(order):
    if ep:   # the next room: the world set back to it at the mind's next slice
        w.fen = room["fen"]
        nb = WarpBoard.from_fen(room["fen"])   # (each piece named by its kind and the square it stands on in this room, as WarpWorld's
        w.ids = {sq: f"{'white' if nb.colors[sq] else 'black'}_{NAMES[nb.pieces[sq]]}_{square_name(sq)}"   # __init__ names them: the
                 for sq in range(TOTAL_SQUARES) if nb.pieces[sq]}   # identities were the first room's, and the reset read stale squares)
        w.actor = "White"
        guard = 0
        while w.moved and guard < 20:   # (the episode is over: both moves made; the mind's slices see the end and the world resets)
            w.pend["Black"] = {}
            choice, _ = a.tick()
            read_mate_passed(a, choice)
            give(a, w)
            guard += 1
    move = None
    if ep and w.moved == 1:   # (the slice that set the world back to this room also made the mind's move: the episode's move)
        move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
    elif ep and w.board.to_fen().split()[:4] != room["fen"].split()[:4]:
        raise RuntimeError(f"episode {ep + 1}: not set to its room: {w.board.to_fen()}")
    n = len([x for x in w.log if x[2]])
    w.actor = "White"
    for _ in range(0 if move else TURN_STEPS * 4):
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
        if len([x for x in w.log if x[2]]) > n:
            move = next(x[1] for x in reversed(w.log) if x[2]).split(" ", 1)[1]
            break
    walk = move in room["walk"]
    walked.append(walk)
    if walk and first_walk is None:
        first_walk = ep + 1
    if move is not None and not w.over():
        black.tick()
        w.actor = "White"
    rels = sorted(r for r in a.mind.understanding.__dict__.get("loss_rels", set()) if r.startswith("cover+"))
    if first_walk is not None and l1 is None and rels:
        l1 = ep + 1
    print(f"ep {ep + 1} ({time.time() - t0:.0f}s): moved {move}{' WALKED IN' if walk else ''} (walk-ins here {room['walk']}); "
          f"cover losses learned {rels}", flush=True)
k = len(order) // 3
first, last, rest = sum(walked[:k]), sum(walked[-k:]), sum(walked[k:])
print(f"\narm {arm}: walk-ins {sum(walked)}/{len(walked)}; first {k} {first}, last {k} {last}, episodes {k + 1}-{len(order)} {rest}")
print(f"first walk-in at episode {first_walk}; a cover loss kind learned by episode {l1}")
json.dump(dict(arm=arm, walked=walked, first_walk=first_walk, l1=l1), open(f"cover_lifelong_{arm}.json", "w"))
mate_oracle.close()
