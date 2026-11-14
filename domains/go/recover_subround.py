"""Finish a league sub-round that a crash cut short, without replaying the games that finished (the user, 2026-11-13: "why not re-run
from round 2???"). A finished game saved its two minds and printed its result as the last line of its log (league.play); a game that
crashed saved nothing, so its minds are as they were before the sub-round. This replays only the games with no result, then records
the whole sub-round as league.main would: results appended, Elo applied in the jobs' own order, the sub-round marked done.
Run: PYTHONHASHSEED=0 python -u -X utf8 recover_subround.py <folder> <round> <k> <name> <name> ..."""
import json
import os
import sys

HERE = __import__("paths").domain('go')
sys.path.insert(0, HERE)
import league  # noqa: E402


def main():
    folder, rnd, k, names = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
    n = len(names)
    out = sys.stdout
    jobs = [(names[i], names[(i + k) % n], f"r{rnd}_k{k}_{names[i]}_vs_{names[(i + k) % n]}", folder) for i in range(n)]
    state_path = f"{folder}/state.json"
    state = json.load(open(state_path))
    assert f"{rnd}:{k}" not in state["done"], "this sub-round is already recorded"
    results = []
    for job in jobs:
        log = f"{folder}/logs/{job[2]}.log"
        last = ""
        if os.path.exists(log):
            lines = [x for x in open(log, encoding="utf-8").read().splitlines() if x.strip()]
            last = lines[-1] if lines else ""
        try:
            r = json.loads(last)
            out.write(f"{job[2]}: from its log, {r['winner']}\n")
        except ValueError:
            out.write(f"{job[2]}: no result, replaying\n")
            out.flush()
            r = league.play(job)   # (it writes its own log, as in the league)
            sys.stdout = out
            out.write(f"{job[2]}: replayed, {r['winner']} {r['black_area']}-{r['white_area']}, {r['stones']} stones\n")
        results.append(r)
    for r in results:   # as league.main: Elo in the jobs' order
        s = 1.0 if r["winner"] == "black" else 0.0 if r["winner"] == "white" else 0.5
        eb = league.expected(state["elo"][r["black"]], state["elo"][r["white"]])
        state["elo"][r["black"]] += league.K * (s - eb)
        state["elo"][r["white"]] += league.K * ((1 - s) - (1 - eb))
        state["games"][r["black"]] += 1
        state["games"][r["white"]] += 1
        with open(f"{folder}/results.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(r, round=rnd, k=k)) + "\n")
    state["done"].append(f"{rnd}:{k}")
    json.dump(state, open(state_path, "w"), indent=1)
    out.write("Elo: " + ", ".join(f"{a} {e:.0f}" for a, e in sorted(state["elo"].items(), key=lambda x: -x[1])) + "\n")


if __name__ == "__main__":
    main()
