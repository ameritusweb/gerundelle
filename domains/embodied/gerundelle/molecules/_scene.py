from force_world import ForceWorld, ForceAgent, node
import poc
from poc import Obj
O = {o.name: o for o in [Obj("ground", 0.0), Obj("block", 2.0, grip=3.0), Obj("prop", 1.0, base=0.5),
     Obj("boulder", 20.0, capacity=100), Obj("wall", 50.0, base=100.0, grip=100.0), Obj("agent", 0.0)]}
def scene():
    return poc.anchoring("ground", node(O, "resting", "block"), node(O, "supporting", "prop", node(O, "resting", "boulder")),
                         node(O, "standing", "wall"))
