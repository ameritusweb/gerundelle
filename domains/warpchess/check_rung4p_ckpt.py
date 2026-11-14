"""Whether a rung 4p run saved and resumed (rung4p.save_run / load_run) plays as an unbroken one (as go/check_checkpoint.py did):
  straight  N slices from the start, recording moves, commits, tool calls, wants, dreams
  save      N/2 slices, then save
  resume    load (in a fresh process) and play the other N/2
The straight run's record must equal save's followed by resume's. The room, seed 0, dreams on (PYTHONHASHSEED=0).
Run: PYTHONHASHSEED=0 python -u -X utf8 check_rung4p_ckpt.py straight|save|resume [slices]; then: check_rung4p_ckpt.py compare"""
import json
import sys

import rung0  # noqa: F401


def record(w, a):
    return dict(moves=[list(x[:3]) for x in w.log], commits=[list(map(str, x)) for x in a.__dict__.get("commit_log", [])],
                tools=[[str(x[0]), str(x[1]), str(x[3])] for x in a.__dict__.get("tool_log", [])], wants=[list(x) for x in a.sub_log],
                dreams=[[x[0], x[1], x[3], x[4]] for x in a.__dict__.get("dreams_done", [])], t=a.mind.t)


def play(w, a, black, n):
    from plansworld import give
    from rung4 import TURN_STEPS
    done = 0
    while done < n:
        if w.board.turn == 1 and not w.over():
            w.actor = "White"
            k = len([x for x in w.log if x[2]])
            for _ in range(TURN_STEPS):
                a.tick()
                give(a, w)
                done += 1
                if len([x for x in w.log if x[2]]) > k or done >= n:
                    break
        elif not w.over():
            black.tick()
            w.actor = "White"
            a.tick()
            give(a, w)
            done += 1
        else:
            w.actor = "White"
            a.tick()
            give(a, w)
            done += 1


def main():
    import rung4p
    from gameworld import RandomSide
    from warpworld import RUNG1_TWO
    mode = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    if mode == "compare":
        s, a_, b_ = (json.load(open(f"ckpt_check_{m}.json")) for m in ("straight", "save", "resume"))
        for k in ("moves", "commits", "tools", "wants", "dreams"):
            print(k, "identical" if s[k] == b_[k] else "DIFFERENT", len(s[k]), "| saved half", len(a_[k]))
        print("mind's slice", s["t"], b_["t"])
        return
    if mode == "resume":
        a, w, black, state = rung4p.load_run("checkpoints/ckpt_check.pkl")
        play(w, a, black, n // 2)
    else:
        w, a = rung4p.build(0, RUNG1_TWO, dreams=True, half_moves=25)
        black = RandomSide(w, 0)
        play(w, a, black, n if mode == "straight" else n // 2)
        if mode == "save":
            rung4p.save_run("checkpoints/ckpt_check.pkl", a, w, black, {})
    json.dump(record(w, a), open(f"ckpt_check_{mode}.json", "w"))
    print(mode, "done", a.mind.t)


if __name__ == "__main__":
    main()
