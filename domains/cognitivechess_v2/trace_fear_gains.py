"""Why "ends a plan of theirs" kinds are among a mind's lived losses (loss_rels; why.py marked them feared, 2026-11-17's league): a short
duel of two fresh minds, every prediction the register stands as a loss caught (SovAgent.stand_prediction) with the region's row and
the world's showing of it at that moment."""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import mate_oracle
from chessduel import BLACK, WHITE, ChessDuel, new_mind
from sov_agent import SovAgent

caught = []
orig = SovAgent.stand_prediction


def stand(self, effect, n0, n, rel, pid, by_):
    region = self.owner_of(effect)
    row = dict(self.mind.territory.rows.get(region, {}))
    ins = orig(self, effect, n0, n, rel, pid, by_)
    if ins.get("loss"):
        caught.append((self.world.me_name, self.mind.t, effect, rel, region, row.get("holder"), sorted(row.get("held_states", ()) or ()),
                       self.world.shown.get(region)))
    return ins


SovAgent.stand_prediction = stand
aw, ww = new_mind(WHITE, half_moves=16, seed=0)
ab, wb = new_mind(BLACK, half_moves=16, seed=1)
d = ChessDuel({WHITE: aw, BLACK: ab}, {WHITE: ww, BLACK: wb}, log=lambda s: None)
d.play_game()
print("losses stood:", len(caught), "| by the effect's new doing:", Counter(c[2].rsplit("_", 1)[1] for c in caught))
for c in [c for c in caught if c[2].endswith("_none")][:12]:
    side, t, effect, rel, region, holder, held, shown = c
    print(f"{side} t{t}: {effect} ({rel}) — row holder {holder}, held states {held}, the world shows {region}: {shown}")
mate_oracle.close()
