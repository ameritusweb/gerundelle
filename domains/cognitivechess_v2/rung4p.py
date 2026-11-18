"""Rung 4p (PLAN.md step 4): games against a random Black with the opponent's plans as the mind's territory, the tool, and commit through
lines (the user, 2026-11-13: "Plans on the game world", "have the mind make the decision", "do it all").

The mind plays White (rung 4's Player: rung 1f's main mind), with rung 1g's switches, the shared switch set and Go's switches (as rung 1i),
the tool (Params.tool_use; tool.MindTool: plan questions and, new, "what follows this move?", whose lines stand as two-move predictions),
and Params.commit_waits_turn. No want is placed: wants come from the territory (plansworld.give), as in Go. Black plays random legal moves.
Turns as rung 4: on White's turn up to TURN_STEPS slices until it moves; Black answers; White has a slice in which it sees the answer.

Reported per game: result, half-moves, White's material balance; commits made, by length (one move, or a line through Black's reply),
and how they came out (came, did not come, dissolved); the tool's calls by kind and the slices they took; seconds per slice.
Run: python -u -X utf8 rung4p.py [--games 1] [--seed 0] [--room|--start]"""
import argparse
import collections
import re
import sys
import time

import dream
import shoes
from imagine import Imagines

import rung1d
from gameworld import RandomSide
from plansgame import PlansGame
from plansworld import give, read_mate_passed
from rung4 import TURN_STEPS, Player, switch
from tool import MindTool
from warpworld import RUNG1_TWO


class DreamingGame(dream.Remembers, Imagines, PlansGame):
    """The plans game that remembers its positions and can imagine lines (for the dream planner, dream.py)."""


class DreamingPlayer(Player):
    """Rung 4's player that wakes from its dreams (dream.wake: a move fitting a dream pair gets it as imagined experience). (First with
    carry.Carries too, as probe_dream.py had it: carrying lived experience to never-made moves imagines every one of them every slice,
    and with the plans read in each imagined position it was 72% of an 18 s slice (py-spy); it isn't the dream planner.)"""

    # which way a move was chosen, kept for its explanation (why.py; the user, 2026-11-17: "don't throw it away; show a readable
    # explanation for the last N moves"): recorded only, the choice itself unchanged
    def planned(self, invs):
        out = super().planned(invs)
        if out is not None:
            self._route = ("planned", self.goal)
        return out

    def winner(self, rec, invs):
        out = super().winner(rec, invs)
        if out is not None:   # (a commitment that won: its first step is the move, why.py says so; first called the top move, and a
            # move played as a commitment's step read as the tournament's top pick, the top moves listed beside it others)
            self._route = ("commit-winner", out) if out[0] == "commit" else ("winner", None)
        return out

    def perceive(self):
        self.world.__dict__.pop("_imagined", None)
        inputs, invs = super().perceive()
        self.woken = dream.wake(self, invs) if self.mind.p.dreams else 0   # (--no-imagination: the register unread, 2026-11-16)
        if self.mind.p.dream_for_want:   # the dream tied to the want in hand (--dream-want, 2026-11-16)
            self.want_dreamt = 0 if want_dream_stopped(self, invs) else timed_want_dream(self, invs)
        return inputs, invs


def want_dream_stopped(agent, invs):
    """--stop-at-want-dream N (the user, 2026-11-17, "make a new flag then for 14 want-dreams"): a game ends when the mind is about to
    want-dream for the Nth time in that game, counting only want-dreams that ran (as --stop-at-dream counts the old dreamer's). A
    want-dream runs when a want is held, moves are on offer, and this (want, position) hasn't been dreamed (dream.dream_for_want)."""
    stop_at = agent.__dict__.get("stop_at_want_dream")
    if not stop_at:
        return False
    w = agent.world
    if agent.goal is None or not invs or (agent.goal, w.board.zobrist_hash()) in agent.__dict__.get("dream_want_memo", set()):
        return False   # (it wouldn't run)
    if agent.__dict__.get("want_dreams_game") != len(w.games):   # (counted per game)
        agent.want_dreams_game, agent.want_dreams_count = len(w.games), 0
    if agent.want_dreams_count + 1 >= stop_at:
        w.ended_early = f"stopped at want-dream {agent.want_dreams_count + 1} (mind slice {agent.mind.t}), for {str(agent.goal)[:80]}"
        return True
    return False


def timed_want_dream(agent, invs):
    """A want-dream, recorded (want_dreams_done: slice, want, moves dreamed, seconds, the game's index) and counted for this game if
    it ran."""
    t0 = time.time()
    n = dream.dream_for_want(agent, invs)
    if n:
        agent.__dict__.setdefault("want_dreams_done", []).append((agent.mind.t, str(agent.goal), n, round(time.time() - t0, 1),
                                                                  len(agent.world.games)))
        if agent.__dict__.get("want_dreams_game") != len(agent.world.games):
            agent.want_dreams_game, agent.want_dreams_count = len(agent.world.games), 0
        agent.want_dreams_count += 1
    return n


IN_GAME_TRIALS = 10   # a dream's trials in the middle of a game (the user, 2026-11-13: "lower it to 50", then "lower dream trials to 10"; dream.py's DREAM_TRIALS, 200, stays
#                       for dreams between games)


def dreamer(agent, concept):
    """Params.dream_when_stuck's dreamer (the user, 2026-11-13: stuck on something not on offer, the mind goes straight into the dream
    planner, the game paused): the stuck concept's first move (a commit's, or the move's own) and its piece; the latest position of this
    game where that move was on offer; the dream from there with that move. The game doesn't move while it runs (the mind's own slice)."""
    w = agent.world
    found = re.findall(r"(\d{3} \S+?)_push:(\w+?)_present", concept)
    if not found:   # (nothing to dream from: a plan, the game's outcome, asking the tool; no dream, and nothing counted)
        agent.__dict__.setdefault("dreams_not_run", []).append((agent.mind.t, concept, "no move in it"))
        return 0
    label, mover = found[0]
    starts = [(b, wh, label, mover) for b, wh, _, _ in reversed(w.__dict__.get("game_positions", []))
              if wh.get(mover) is not None and any(w.label(m) == label for m in b.legal_moves)][:1]
    if not starts:
        agent.__dict__.setdefault("dreams_not_run", []).append((agent.mind.t, concept, "no position of this game had it"))
        return 0
    stop_at = agent.__dict__.get("stop_at_dream_slice")   # (--stop-at-dream N: a game ends when the mind is about to dream on its Nth
    game = len(w.games)                                   #  slice with dreams in that game, counting only dreams that run; the user,
    if agent.__dict__.get("dream_slices_game") != game:   #  2026-11-14: "EACH game can stop at the second dream", "Count only dreams
        agent.dream_slices_game, agent.dream_slices = game, []   # that ran")
    slices_ = agent.dream_slices
    if stop_at and agent.mind.t not in slices_ and len(slices_) + 1 >= stop_at:
        w.ended_early = f"stopped at dream {len(slices_) + 1} (mind slice {agent.mind.t}), about {concept[:80]}"
        return 0
    t0 = time.time()
    trials, edges = dream.dream(agent, focus=starts, budget=IN_GAME_TRIALS)
    agent.__dict__.setdefault("dreams_done", []).append((agent.mind.t, concept, True, trials, edges, round(time.time() - t0, 1)))
    if trials and agent.mind.t not in slices_:
        slices_.append(agent.mind.t)
    return trials   # (dreamed through or not: SovAgent.dream_if_stuck resolves the stuck only if it was)


CACHES = ("_plan_memo", "_plan_read", "_start_cache", "_imagined", "_pp_memo", "_starts")   # the world's exact caches (rebuilt as needed)


def save_run(path, agent, world, black, state):
    """A checkpoint of the run (the user, 2026-11-13: "restart with a checkpoint after every game"; tetris/checkpoint.py's way): the agent
    (its mind, register, territory, everything learned), the world, Black (its random source, so a resumed run plays as an unbroken one),
    and the run's own counts. Set aside to save and rebuilt on load: what pickle can't carry (the register's kind and owner, the world's
    act as the agent wraps it, the world's in_their_shoes, the agent's dreamer) and what needn't be saved (the world's and the tool's
    exact caches, which only cost time to rebuild)."""
    import pickle
    und = agent.mind.understanding
    held_und = {k: und.__dict__.pop(k) for k in ("kind", "owner", "lien_holds") if k in und.__dict__}
    role = und.__dict__.pop("_role_kinds", None)
    held_world = {k: world.__dict__.pop(k) for k in ("act", "_noticed_by", "in_their_shoes") + CACHES if k in world.__dict__}
    held_agent = {k: agent.__dict__.pop(k) for k in ("dreamer", "_pushed_by_fact", "_dreamed_by_fact", "_dreamed_by_inv")
                  if k in agent.__dict__}   # (the register indexes are exact caches: rebuilt, not saved; 2026-11-16)
    tool = getattr(agent, "tool", None)
    table = tool.tool.table if tool is not None else None
    if tool is not None:
        tool.tool.table = {}
    try:
        with open(path, "wb") as f:
            pickle.dump({"agent": agent, "world": world, "black": black, "state": state}, f, protocol=4)
    finally:
        und.__dict__.update(held_und)
        if role is not None:
            und._role_kinds = role
        world.__dict__.update(held_world)
        agent.__dict__.update(held_agent)
        if tool is not None:
            tool.tool.table = table


def load_run(path):
    """-> (agent, world, black, state) from save_run's file. Run with the PYTHONHASHSEED it was saved with."""
    import pickle
    import __main__   # (checkpoints saved while rung4p.py ran as the main program name its classes __main__.*: give them here)
    import rung4p as module
    for name in ("DreamingGame", "DreamingPlayer", "dreamer"):
        if not hasattr(__main__, name):
            setattr(__main__, name, getattr(module, name))
    with open(path, "rb") as f:
        box = pickle.load(f)
    agent, world = box["agent"], box["world"]
    if not hasattr(world.board, "press_map"):   # a checkpoint saved by the Python engine (WarpOneChess), its boards remade on the Rust
        from rustboard import WarpBoard         # board by FEN (2026-11-16, for the dream-speed work; the engines agree field by field,
        world.board = WarpBoard.from_fen(world.board.to_fen())   # check_rustboard.py — but the Rust board carries the castling fix, so
        for key in ("game_positions", "last_game"):              # a resumed run continues on the fixed rules, not the saved engine's)
            world.__dict__[key] = [(WarpBoard.from_fen(b.to_fen()), wh, lab, mv) for b, wh, lab, mv in world.__dict__.get(key, [])]
    und = agent.mind.understanding
    und.owner = lambda c: (c.split(":", 1)[1].rsplit("_", 1)[0] if "_push:" in c else und.owners.get(c))   # (as Understanding.__init__)
    und.kind = lambda c: "act" if c.split(":", 1)[0].endswith("_push") else "change"                         # (as SovAgent.__init__)
    und._role_kinds = False   # (the force predictions wrap kind again on their next tick)
    world._plan_memo, world._plan_read = {}, {}
    if agent.mind.p.self_noticed:
        agent.noticing()
    if agent.mind.p.dreams:
        world.in_their_shoes = shoes.in_their_shoes(agent)
    if agent.mind.p.dream_when_stuck:
        agent.dreamer = dreamer
    agent.__dict__.pop("dream_slices_game", None)   # (the per-game dream count starts afresh: a checkpoint saved by the code that counted
    agent.__dict__.pop("dream_slices", None)        #  attempts held one, and the first game after resuming was stopped at its first real
    return agent, world, box["black"], box["state"]   # dream, 2026-11-14)


def build(seed, fen, dreams=False, half_moves=None, me=True):
    """A mind and its world; `me`, the seat's colour (True: White, as every run before the league; the league seats Black too)."""
    kw = {} if half_moves is None else {"half_moves": half_moves}   # (the game's cap: GameWorld's HALF_MOVES, 80, unless given)
    w = (DreamingGame if dreams else PlansGame)(seed=seed, fen=fen, me=me, **kw)
    w.actor = w.me_name
    a = (DreamingPlayer if dreams else Player)(w, "game")
    switch(a.mind, True)
    for k, v in {**rung1d.shared_switches(), **rung1d.go_switches()}.items():
        setattr(a.mind.p, k, v)
    a.tool = MindTool(w)
    a.mind.p.tool_use = True
    a.mind.p.commit_waits_turn = True
    if dreams:   # (the dream planner: Params.dreams; stuck on something not on offer, dream at once: Params.dream_when_stuck)
        w.in_their_shoes = shoes.in_their_shoes(a)
        a.mind.p.dreams = True
        a.mind.p.dream_when_stuck = True
        a.dreamer = dreamer
    return w, a


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--start", action="store_true", help="the rulebook's starting position (else rung 1's two-move room)")
    ap.add_argument("--dreams", action="store_true", help="v2 (the user, 2026-11-17): want-dreams on the quiet register, warpchess's arm G "
                    "(dream_for_want on; the old dreamer off and its imagination register unread). --old-dreamer: warpchess's original")
    ap.add_argument("--old-dreamer", action="store_true", help="with --dreams: warpchess's original dreaming (the dream planner, dreaming "
                    "when stuck, the imagination register read), for a control arm")
    ap.add_argument("--half-moves", type=int, default=None, help="a game's cap in half-moves (default GameWorld's, 80)")
    ap.add_argument("--max-slices", type=int, default=3000, help="the run's budget: stop after this many of the mind's slices")
    ap.add_argument("--resume", default=None, help="a checkpoint (save_run's file) to go on from")
    ap.add_argument("--dream-workers", type=int, default=None, help="dream trials in waves across this many worker processes (dream.py)")
    ap.add_argument("--stop-at-dream", type=int, default=0, help="end a game when the mind tries to dream on its Nth slice with dreams in it")
    ap.add_argument("--stop-at-want-dream", type=int, default=0, help="end a game when the mind is about to want-dream for the Nth time in "
                    "it, counting only want-dreams that ran (the user, 2026-11-17)")
    ap.add_argument("--dream-fork", action="store_true", help="dream trials in forked children: the OS copies the mind, nothing pickled (POSIX only; 2026-11-16)")
    ap.add_argument("--dreamed-conditions", action="store_true", help="arm E (2026-11-16, the understanding loop): dreamed conditions join told conditions as Inquiry hypotheses (cleancode's promotion arc)")
    ap.add_argument("--dream-want", action="store_true", help="arm F (2026-11-16): dreams tied to the want in hand — moves on offer played for the held want, what served written told, the next real move the experiment (dream.dream_for_want)")
    ap.add_argument("--no-new-dreams", action="store_true", help="control arm (2026-11-16, is dreaming helpful): no in-game dreams; the imagination register stays read")
    ap.add_argument("--no-imagination", action="store_true", help="control arm: no in-game dreams AND the register unread (wake, makers, dreamed modes, dreamed wants)")
    ap.add_argument("--tag", default=None, help="checkpoint tag (default rung4p_<room>_s<seed>; give the control arms their own)")
    ap.add_argument("--fen", default=None, help="start every game from this position (checks; cognitivechess_v2, 2026-11-17)")
    args = ap.parse_args()
    fen = args.fen or (None if args.start else RUNG1_TWO)
    import os
    os.makedirs("checkpoints", exist_ok=True)
    tag = args.tag or f"rung4p_{'start' if args.start else 'room'}_s{args.seed}"
    if args.resume:
        a, w, black, state = load_run(args.resume)
        print(f"resumed from {args.resume}: {state}", flush=True)
        if args.half_moves is not None:   # (the checkpoint's world keeps its own cap; a given one replaces it, 2026-11-17)
            w.moves = args.half_moves
    else:
        w, a = build(args.seed, fen, args.dreams, args.half_moves)
        black = RandomSide(w, args.seed)
        state = {}
    if args.no_new_dreams or args.no_imagination:   # the control arms resume a dreaming mind and stop its dreaming (and, for
        a.mind.p.dream_when_stuck = False           # --no-imagination, its reading of what it dreamed)
        a.__dict__.pop("dreamer", None)
    if args.no_imagination:
        a.mind.p.dreams = False
    if args.dreams and not args.old_dreamer:   # v2's dreaming (the user, 2026-11-17, "the quiet register with want-dreams"): warpchess's
        a.mind.p.dream_when_stuck = False      # arm G, as --no-imagination --dream-want set it there: no old dreams, the register unread,
        a.__dict__.pop("dreamer", None)        # the dream tied to the want in hand (DREAM_SPEED.md)
        a.mind.p.dreams = False
        a.mind.p.dream_for_want = True
    t0, slices, games_seen = time.time(), state.get("slices", 0), state.get("games", 0)
    if args.stop_at_dream:
        a.stop_at_dream_slice = args.stop_at_dream
    else:
        a.__dict__.pop("stop_at_dream_slice", None)   # a checkpoint's stale stop (as the stale dream count, 2026-11-14): g18 carried
        #                                               stop-at-4 and truncated arm E's games to 18 half-moves, 2026-11-16
    if args.stop_at_want_dream:
        a.stop_at_want_dream = args.stop_at_want_dream
    else:
        a.__dict__.pop("stop_at_want_dream", None)
    a.__dict__.pop("want_dreams_game", None)   # (a resumed run counts afresh)
    if args.dream_workers is not None:
        a.dream_workers = args.dream_workers   # (the user, 2026-11-14: a whole 10-trial dream in one wave of 10 workers)   # (per game: plansgame.PlansGame.ended_early)
    if args.dream_fork:
        a.dream_fork = True
    if args.dreamed_conditions:
        a.mind.p.dreamed_conditions = True
    if args.dream_want:
        a.mind.p.dream_for_want = True
    last_move, stall_shown = (0, 0), False   # (half-moves, the slice they last changed)
    steps = lambda c: c.count("_push:") - 1   # a commit's sequence length: its pushes, the commit's own name aside
    terr = a.mind.territory
    loss_wants, sub_read = list(state.get("loss_wants", [])), state.get("sub_read", 0)   # wants set for a loss of the mind's own: another
    #                                                                                       state of a region the register holds now
    mark = dict(commits=len(a.__dict__.get("commit_log", [])), tools=len(a.__dict__.get("tool_log", [])), dreams=len(a.__dict__.get("dreams_done", [])),
                subs=len(a.sub_log), losses=len(loss_wants), slices=slices, t=time.time(),
                wdreams=len(a.__dict__.get("want_dreams_done", [])))   # (from where a resumed run stands)

    def check_wants():
        nonlocal sub_read
        for t_, g_, k_ in a.sub_log[sub_read:]:
            if k_ != "set" or g_.startswith(("all:", "potential:")):
                continue
            r_ = a.owner_of(g_)
            now_ = w.shown.get(r_)
            if terr.rows.get(r_, {}).get("holder") == "mine" and now_ is not None and g_ != f"{r_}_{now_}":
                loss_wants.append((t_, g_))
        sub_read = len(a.sub_log)

    def game_summary(n_, g_):
        log_, tools_, dreams_ = a.__dict__.get("commit_log", []), a.__dict__.get("tool_log", []), a.__dict__.get("dreams_done", [])
        new_c = log_[mark["commits"]:]
        sets = [x for x in a.sub_log[mark["subs"]:] if x[2] == "set"]
        print(f"game {n_}: {g_[0]}{' (the half-move cap)' if g_[0] == 'unfinished' else ''}, White's balance {g_[1]:+d}, {g_[2]} half-moves; "
              f"{slices - mark['slices']} slices, {time.time() - mark['t']:.0f}s", flush=True)
        print(f"    commits made {collections.Counter('line' if steps(x[1]) > 1 else 'one move' for x in new_c if x[2] == 'made')}, "
              f"outcomes {dict(collections.Counter(x[2] for x in new_c if x[2] != 'made'))}; tool calls {len(tools_) - mark['tools']}; "
              f"dreams {len(dreams_) - mark['dreams']}; want-dreams {sum(1 for x in a.__dict__.get('want_dreams_done', []) if x[4] == n_ - 1)}; "
              f"wants set {len(sets)} "
              f"{dict(collections.Counter(x[1].rsplit('_', 1)[-1] for x in sets).most_common(5))}; "
              f"wants for a loss of its own {len(loss_wants) - mark['losses']} {loss_wants[mark['losses']:][:3]}", flush=True)
        mark.update(commits=len(log_), tools=len(tools_), dreams=len(dreams_), subs=len(a.sub_log), losses=len(loss_wants),
                    slices=slices, t=time.time(), wdreams=len(a.__dict__.get("want_dreams_done", [])))
    def step(note=""):
        """One slice of the mind's, logged with its time and what it did (the user, 2026-11-13: "log every slice with timings")."""
        nonlocal slices
        dreams0, tools0, subs0 = len(a.__dict__.get("dreams_done", [])), len(a.__dict__.get("tool_log", [])), len(a.sub_log)
        wd0 = len(a.__dict__.get("want_dreams_done", []))
        mat0, games0 = w.material() - w.start_material, len(w.games)   # (the user, 2026-11-17: "why doesn't it print material changes??")
        ts = time.time()
        choice, _ = a.tick()
        read_mate_passed(a, choice)   # (cognitivechess_v2: a mate passed up is a loss of territory)
        give(a, w)
        dt = time.time() - ts
        slices += 1
        did = ("waited" if choice is None else "asked the tool" if choice[0] == "ask" else
               f"committed ({steps(inv_id_(choice))} move{'s' if steps(inv_id_(choice)) > 1 else ''})" if choice[0] == "commit" else
               f"moved {choice[0]}")
        if a.__dict__.get("committed") and choice is not None and choice[0] not in ("commit", "ask"):
            did += " (committed)"
        extra = []
        nd = len(a.__dict__.get("dreams_done", [])) - dreams0
        if nd:
            extra.append(f"DREAMED {nd} ({', '.join(f'{x[3]} trials, {x[5]}s' for x in a.dreams_done[-nd:])})")
        reads = w.__dict__.get("forced_mate_reads", [])   # Stockfish's forced mates read since the last line (the user, 2026-11-17: "does the
        for state_, x_, side_, uci_ in reads[w.__dict__.get("_fm_logged", 0):]:   # log mention when there is a stockfish mate-in-x?")
            extra.append(f"FORCED MATE in {x_} ({state_}, after {side_}'s {uci_})")
        w._fm_logged = len(reads)
        mat1 = w.material() - w.start_material   # White's balance against the last one logged in this game (Black's capture comes before
        prev = w.__dict__.get("_mat_logged", 0) if w.__dict__.get("_mat_game") == len(w.games) else 0   # its slice, so not mat0)
        if mat1 != prev:
            extra.append(f"material {mat1:+d} ({mat1 - prev:+d})")
        w._mat_logged, w._mat_game = mat1, len(w.games)
        nw = len(a.__dict__.get("want_dreams_done", [])) - wd0
        if nw:
            x = a.want_dreams_done[-1]
            extra.append(f"WANT-DREAMED {a.__dict__.get('want_dreams_count', 0)} this game ({x[2]} moves, {x[3]}s, for {x[1][:50]})")
        if len(a.__dict__.get("tool_log", [])) > tools0:
            extra.append(f"tool answered in {a.tool_log[-1][3]} slices")
        sets = [g for _, g, k in a.sub_log[subs0:] if k == "set"]
        if sets:
            extra.append(f"want set {sets[0][:60]}")
        print(f"   s{slices} {dt:5.1f}s{' SLOW' if dt > 30 else ''}: {note}{did}; half-moves {w.moved}{'; ' + '; '.join(extra) if extra else ''}",
              flush=True)

    inv_id_ = lambda i: f"{i[0]}_push:{i[1]}_{i[2]}"
    while len(w.games) < args.games and slices < args.max_slices and not a.__dict__.get("stop_requested"):
        if w.board.turn == 1 and not w.over():
            w.actor = "White"
            n = len([x for x in w.log if x[2]])
            for _ in range(TURN_STEPS):
                step()
                if len([x for x in w.log if x[2]]) > n:
                    break
        elif not w.over():
            black.tick()
            w.actor = "White"
            step("Black answered; ")
        else:
            w.actor = "White"
            w.pend["Black"] = {}   # (Black, a random player, reads nothing, as RandomSide.tick clears it: else a game ended on White's move
            #                       would wait for Black's news forever before being set back)
            step("game over; ")   # the world sets it back at the mind's next slice
        check_wants()
        if slices % 20 == 0:
            com = collections.Counter((steps(x[1]) if x[2] == "made" else None, x[2]) for x in a.__dict__.get("commit_log", []))
            print(f"  slice {slices} ({time.time() - t0:.0f}s): half-moves {w.moved}, games {len(w.games)}; commits {dict(com)}; "
                  f"tool calls {len(a.__dict__.get('tool_log', []))}", flush=True)
        if w.moved != last_move[0]:
            last_move = (w.moved, slices)
        elif slices - last_move[1] >= 50 and not stall_shown:   # no half-move for 50 slices: what the board and the mind are doing
            stall_shown = True
            b = w.board
            print(f"  STALL at slice {slices}: half-moves {w.moved}, turn {'White' if b.turn else 'Black'}, over {w.over()}, "
                  f"legal {len(b.legal_moves)}, kings {b._king_sq}, actor {w.actor}, offers {len(w.offers())}, invitations "
                  f"{len(w.invitations())}, pend {dict((k, len(v)) for k, v in w.pend.items())}, moves cap {w.moves}; mind: goal {a.goal}, "
                  f"committed {bool(a.__dict__.get('committed'))}, asking {bool(a.__dict__.get('asking'))}, watching {bool(a.watching)}, "
                  f"queue {a.queue}; fen {b.to_fen()}", flush=True)
        while games_seen < len(w.games):
            g = w.games[games_seen]
            games_seen += 1
            game_summary(games_seen, g)
            path = f"checkpoints/{tag}_g{games_seen}.pkl"   # a checkpoint after every game (the user, 2026-11-13)
            save_run(path, a, w, black, dict(slices=slices, games=games_seen, sub_read=sub_read, loss_wants=loss_wants))
            print(f"    saved {path} ({os.path.getsize(path) / 1e6:.1f} MB)", flush=True)
    if a.__dict__.get("stop_requested"):
        path = f"checkpoints/{tag}_stopped.pkl"
        save_run(path, a, w, black, dict(slices=slices, games=games_seen, sub_read=sub_read, loss_wants=loss_wants))
        print(f"STOPPED: {a.stop_requested}; half-moves {w.moved}; saved {path}", flush=True)
    log = a.__dict__.get("commit_log", [])
    made = [x for x in log if x[2] == "made"]
    print(f"slices {slices}, {(time.time() - t0) / max(1, slices):.1f}s a slice")
    print("commits made by length:", collections.Counter("line" if steps(x[1]) > 1 else "one move" for x in made))
    print("commit outcomes:", collections.Counter(x[2] for x in log if x[2] != "made"))
    for x in [x for x in made if steps(x[1]) > 1][:8]:
        print("   line commit:", x[0], x[1][:160])
    tools = a.__dict__.get("tool_log", [])
    print("tool calls:", collections.Counter("line" if "_push:" in c else "plan" for _, c, _, _ in tools),
          "| slices waited:", sum(s for *_, s in tools))
    print("dreams when stuck:", [(t, c[:70], found, tr, ed, sec) for t, c, found, tr, ed, sec in a.__dict__.get("dreams_done", [])][:10])
    print("wants set:", collections.Counter(g.rsplit("_", 1)[-1] for _, g, k in a.sub_log if k == "set").most_common(6))
    print("wants for a loss of its own, over the run:", len(loss_wants), loss_wants[:6])


if __name__ == "__main__":   # (run through the module, so a checkpoint names rung4p's classes as rung4p.*, loadable from any script)
    import rung4p
    rung4p.main()
