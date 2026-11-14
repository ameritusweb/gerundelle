"""The reference for a lightweight Abstract (the user, 2026-11-13: "we need to simulate or find a heuristic that mimics what Abstract
does"; "do it; then use it as frozen play's Abstract"). Plays a pair from frozen_poc/minds/ (copies; nothing saved) and records every call
of the real Abstract (Understanding.analogize): its time, and its outputs, the only parts of it the rest of the mind reads:
- new abstracts over whole structures (log "analogy"), and merges ("merged");
- concept abstracts formed ("concept analogy") and joined ("joined");
- expectations written by transfer (log "expect": a (concept, relation) whose slot an analogy predicts), and with Params.transfer_tells,
  links told by transfer ("transfer told");
- the analogies reported in the tick's record (rec["analogies"]).
Also each slice's total time, so Abstract's share is known, and the size of what it read (links, components).
Modes: learning (as in the league); frozen_live (frozen_poc's first cut, every SOV write queued, but the real Abstract left running: the
setting the stand-in will replace).
Run: PYTHONHASHSEED=0 python -u -X utf8 abstract_ref.py [black] [white] [slices]"""
import collections
import json
import multiprocessing as mp
import sys
import time

HERE = __import__("paths").domain('go')
MINDS = f"{HERE}/frozen_poc/minds"
KINDS = ("analogy", "merged", "concept analogy", "joined", "expect", "transfer told")


def play(job):
    black, white, mode, slices = job
    sys.path.insert(0, HERE)
    import run  # noqa: F401
    import checkpoint
    import molecules
    from goduel import Duel
    calls = []
    current = {"t": 0, "colour": None}
    if mode == "frozen_live":
        molecules.Understanding.add = lambda self, c, rel, other, how, w=1.0: None
    real = molecules.Understanding.analogize

    def recording(self, rec):
        n_log, n_an = len(self.log), len(rec.get("analogies", []))
        t0 = time.perf_counter()
        out = real(self, rec)
        dt = time.perf_counter() - t0
        new = [e for e in self.log[n_log:] if e[1] in KINDS]
        calls.append(dict(t=current["t"], colour=current["colour"], seconds=round(dt, 4),
                          links=len(self.__dict__.get("_edges_now") or ()), abstracts=len(self.abstracts),
                          concept_abstracts=len(self.__dict__.get("concept_abstracts", [])),
                          out=[(e[1], repr(e[2])[:200]) for e in new], analogies=len(rec.get("analogies", [])) - n_an))
        return out
    molecules.Understanding.analogize = recording
    agents, seats = {}, {}
    for name, colour in ((black, "black"), (white, "white")):
        agent, seat, _ = checkpoint.load(f"{MINDS}/{name}_{colour}.pkl")
        agents[colour], seats[colour] = agent, seat
        if mode == "learning_affords":   # (Params.affords_relation, from saved minds: their affordances, written as "enables" before the
            assert not agent.mind.p.polarity   # switch, relabelled "affords"; right only while polarity is off, so every "enables" is one)
            agent.mind.p.affords_relation = True
            und = agent.mind.understanding
            for c, rels in und.rel.items():
                for key in [k for k in rels if k[0] == "enables"]:
                    rels[("affords", key[1])] = rels.pop(key)
    d = Duel(seats=(seats["black"], seats["white"]))
    ticks = []
    for _ in range(slices):
        d.renew()
        for colour in d.order():
            agent, seat = agents[colour], seats[colour]
            current["t"], current["colour"] = d.clock, colour
            agent.mind.potentials = seat.potentials()
            t0 = time.perf_counter()
            agent.tick()
            ticks.append((d.clock, colour, round(time.perf_counter() - t0, 4)))
            agent._league_read, _ = run.give(agent, seat, agent.__dict__.get("_league_read", 0))
        d.end_slice()
        if d.results:
            break
    return dict(mode=mode, calls=calls, ticks=ticks, result=d.results[0] if d.results else None, slices=d.clock)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    black = sys.argv[1] if len(sys.argv) > 1 else "patient"
    white = sys.argv[2] if len(sys.argv) > 2 else "dogged"
    slices = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    modes = sys.argv[4:] or ["learning", "frozen_live"]
    with mp.get_context("spawn").Pool(len(modes)) as pool:
        runs = pool.map(play, [(black, white, m, slices) for m in modes])
    tag = "" if modes == ["learning", "frozen_live"] else "_" + "_".join(modes)
    with open(f"{HERE}/frozen_poc/abstract_ref_{black}_{white}{tag}.json", "w", encoding="utf-8") as f:
        json.dump(runs, f)
    for r in runs:
        calls, ticks = r["calls"], r["ticks"]
        a_time, t_time = sum(c["seconds"] for c in calls), sum(t[2] for t in ticks)
        kinds = collections.Counter(k for c in calls for k, _ in c["out"])
        busy = sum(1 for c in calls if c["out"])
        print(f"\n{r['mode']}: {r['slices']} slices, {len(ticks)} ticks, {t_time:.0f}s in ticks; Abstract {len(calls)} calls, {a_time:.0f}s "
              f"({100 * a_time / max(t_time, 1e-9):.0f}% of tick time); mean {a_time / max(1, len(calls)):.3f}s, max {max((c['seconds'] for c in calls), default=0):.2f}s")
        print(f"  links read: first {calls[0]['links'] if calls else 0}, last {calls[-1]['links'] if calls else 0}; abstracts first "
              f"{calls[0]['abstracts'] if calls else 0}, last {calls[-1]['abstracts'] if calls else 0}; concept abstracts last {calls[-1]['concept_abstracts'] if calls else 0}")
        print(f"  outputs: {dict(kinds)}; calls with any output {busy} of {len(calls)}; analogies in tick records {sum(c['analogies'] for c in calls)}")
        for c in [c for c in calls if c["out"]][:8]:
            print(f"    slice {c['t']} {c['colour']} ({c['seconds']}s): {c['out'][:3]}")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
