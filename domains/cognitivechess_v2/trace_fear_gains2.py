"""The game-12 mind (checkpoint) against random Black from a fresh game: each prediction the register stands as a loss whose effect ends a
plan (_none) or reaches a new forced mate, with the region's row at that moment and what the world shows."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from chessduel import fresh_seat
from gameworld import RandomSide
from plansworld import give, read_mate_passed
from rung4p import load_run
from sov_agent import SovAgent

caught = []
orig = SovAgent.stand_prediction


def stand(self, effect, n0, n, rel, pid, by_):
    region = self.owner_of(effect)
    row = dict(self.mind.territory.rows.get(region, {}))
    ins = orig(self, effect, n0, n, rel, pid, by_)
    if ins.get("loss") and (effect.endswith("_none") or effect.endswith("_new")):
        caught.append((self.mind.t, effect, region, row.get("holder"), sorted(row.get("held_states", ()) or ()), self.world.shown.get(region),
                       self.world.moved))
    return ins


SovAgent.stand_prediction = stand
a, w0, _, _ = load_run("checkpoints/rung4p_full_s0_g12.pkl")
w = fresh_seat(a, True, old=w0, half_moves=300)
black = RandomSide(w, 3)
for _ in range(400):
    if w.board.turn and not w.over():
        w.actor = "White"
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
    elif not w.over():
        black.tick()
        w.actor = "White"
        choice, _ = a.tick()
        read_mate_passed(a, choice)
        give(a, w)
    else:
        break
    if len(caught) >= 8:
        break
print("half-moves", w.moved, "| caught", len(caught))
for t, effect, region, holder, held, shown, moved in caught:
    print(f"t{t} half-move {moved}: {effect}: the row's holder {holder}, held states {held}; the world shows {shown}")
mate_oracle.close()
