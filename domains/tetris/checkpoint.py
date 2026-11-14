"""Checkpoints for a run of the tetris mind (the user, 2026-11-11: "a sort of 'checkpoint', to resume from a certain slice"): the agent
(its mind, register, territory, everything it has learned) and the world, saved together to one file and loaded back to go on from
that slice.

Pickle can't carry functions, and a few are held as attributes (warpchess/dream.py's dreaming_mind sets the register's aside the same
way): the world's act, wrapped by the agent so it notices changes itself (Params.self_noticed), and the agent kept on the world for that;
the register's kind and owner. They are set aside to save and rebuilt on load: the register's own owner and the agent's kind as they
are made (molecules.Understanding.__init__, SovAgent.__init__), the role-kind wrapper the force predictions add made again on their next
tick, and the world wrapped again by the agent.

save(agent, world, slice, path); load(path) -> (agent, world, slice). Load and run with the same PYTHONHASHSEED the run was saved with.
"""
import os
import pickle


def save(agent, world, t, path):
    und = agent.mind.understanding
    held_und = {k: und.__dict__.pop(k) for k in ("kind", "owner", "lien_holds") if k in und.__dict__}
    held_world = {k: world.__dict__.pop(k) for k in ("act", "_noticed_by") if k in world.__dict__}
    role = und.__dict__.pop("_role_kinds", None)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)   # (a fresh copy has no checkpoints/ folder yet, 2026-11-14)
        with open(path, "wb") as f:
            pickle.dump({"agent": agent, "world": world, "slice": t}, f, protocol=4)
    finally:
        und.__dict__.update(held_und)
        world.__dict__.update(held_world)
        if role is not None:
            und._role_kinds = role


def load(path):
    with open(path, "rb") as f:
        box = pickle.load(f)
    agent, world = box["agent"], box["world"]
    und = agent.mind.understanding
    und.owner = lambda c: (c.split(":", 1)[1].rsplit("_", 1)[0] if "_push:" in c else und.owners.get(c))   # (as Understanding.__init__)
    und.kind = lambda c: "act" if c.split(":", 1)[0].endswith("_push") else "change"                         # (as SovAgent.__init__)
    und._role_kinds = False   # the force predictions wrap kind again on their next tick (SovAgent.force_predict)
    if agent.mind.p.self_noticed:
        agent.noticing()   # the agent wraps the world's act again, its memory of what it last saw kept (last_seen)
    return agent, world, box["slice"]
