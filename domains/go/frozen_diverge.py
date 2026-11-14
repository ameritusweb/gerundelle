"""Where frozen play parts from learning play, and which write decides it (frozen_poc.py: patient (Black) vs dogged (White) from the
same copies, learning and frozen, part at the third placement; frozen games churn to the cap). The pair is played twice, in two
processes, from frozen_poc/minds/ (copies; nothing saved): learning, and frozen (every SOV write queued, Abstract skipped, as
frozen_poc's first cut). Each records, every slice and for each colour: what the mind chose, the top-level bids of the pushes on offer,
the relations of the leading pushes, and every SOV write (made, or queued). The first slice where the two choices differ is shown with
both minds' leading bids, and the learning mind's writes before it that touch the pushes that led there, by kind (lived, seen, told).
Run: PYTHONHASHSEED=0 python -u -X utf8 frozen_diverge.py [black] [white] [slices]"""
import json
import multiprocessing as mp
import sys

HERE = __import__("paths").domain('go')
MINDS = f"{HERE}/frozen_poc/minds"


def play(job):
    black, white, mode, slices = job
    sys.path.insert(0, HERE)
    import run  # noqa: F401
    import checkpoint
    import molecules
    from force_world import inv_id
    from goduel import Duel
    writes = []   # (duel slice, colour, c, rel, other, how, made?)
    current = {"t": 0, "colour": None}
    add = molecules.Understanding.add

    def recording_add(self, c, rel, other, how, w=1.0):
        made = mode == "learning"
        writes.append((current["t"], current["colour"], c, rel, other, how, made))
        if made:
            return add(self, c, rel, other, how, w)
    molecules.Understanding.add = recording_add
    if mode != "learning":
        molecules.Understanding.analogize = lambda self, rec: None
    agents, seats = {}, {}
    for name, colour in ((black, "black"), (white, "white")):
        agent, seat, _ = checkpoint.load(f"{MINDS}/{name}_{colour}.pkl")
        agents[colour], seats[colour] = agent, seat
    d = Duel(seats=(seats["black"], seats["white"]))
    record = []

    for _ in range(slices):
        d.renew()
        for colour in d.order():
            agent, seat = agents[colour], seats[colour]
            current["t"], current["colour"] = d.clock, colour
            agent.mind.potentials = seat.potentials()
            offered = {inv_id(i) for i in seat.invitations()}
            choice, rec = agent.tick()
            agent._league_read, _ = run.give(agent, seat, agent.__dict__.get("_league_read", 0))
            if offered:
                lv = rec["levels"][-1] if rec.get("levels") else {"bids": {}}
                bids = {}
                for i, v in lv["bids"].items():
                    c = i.split("|")[0]
                    if c in offered:
                        bids[c] = max(bids.get(c, 0.0), v)
                top = sorted(bids.items(), key=lambda x: -x[1])[:6]
                rels = {c: sorted(f"{r} {o} {[round(x, 2) for x in e]}" for (r, o), e in agent.mind.understanding.rel.get(c, {}).items())
                        for c, _ in top[:3]}
                record.append(dict(t=d.clock, colour=colour, choice=inv_id(choice) if choice is not None and choice[0] != "commit" else
                                   (choice[1] if choice is not None else None), top=[(c, round(v, 3)) for c, v in top], rels=rels,
                                   goal=agent.goal, anti=agent.__dict__.get("anti")))
        d.end_slice()
        if d.results:
            break
    return dict(mode=mode, record=record, writes=writes)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    black = sys.argv[1] if len(sys.argv) > 1 else "patient"
    white = sys.argv[2] if len(sys.argv) > 2 else "dogged"
    slices = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    with mp.get_context("spawn").Pool(2) as pool:
        learn, frozen = pool.map(play, [(black, white, "learning", slices), (black, white, "frozen", slices)])
    with open(f"{HERE}/frozen_poc/diverge_{black}_{white}.json", "w", encoding="utf-8") as f:
        json.dump(dict(learning=learn, frozen=frozen), f)
    L, F = learn["record"], frozen["record"]
    k = next((i for i, (a, b) in enumerate(zip(L, F)) if (a["t"], a["colour"], a["choice"]) != (b["t"], b["colour"], b["choice"])), None)
    print(f"{black} (Black) vs {white} (White), {slices} slices: {len(L)} turns recorded")
    if k is None:
        print("no divergence in the window")
        return
    a, b = L[k], F[k]
    print(f"first divergence: slice {a['t']}, {a['colour']}'s turn (turn {k} of its records)")
    for name, x in (("learning", a), ("frozen", b)):
        print(f"\n  {name}: chose {x['choice']}; want {x['goal']}; anti {x['anti']}")
        print(f"    leading bids: {x['top']}")
        for c, rs in x["rels"].items():
            print(f"    {c}: {len(rs)} relations: {rs[:14]}")
    leaders = {c for c, _ in a["top"]} | {c for c, _ in b["top"]}
    before = [w for w in learn["writes"] if w[0] < a["t"] or (w[0] == a["t"] and w[1] != a["colour"])]
    touching = [w for w in before if w[2] in leaders or w[4] in leaders]
    by_kind = {}
    for w in before:
        by_kind[(w[5], w[3])] = by_kind.get((w[5], w[3]), 0) + 1
    print(f"\n  the learning game's writes before the divergence: {len(before)}; by (kind, relation): {sorted(by_kind.items(), key=lambda x: -x[1])[:14]}")
    print(f"  of those, touching a push that led at the divergence: {len(touching)}")
    for w in touching[:30]:
        print(f"    slice {w[0]} ({w[1]}): {w[2]} {w[3]} {w[4]} [{w[5]}]")
    print(f"\n  the turns before it (both games the same):")
    for x in L[max(0, k - 6):k]:
        print(f"    slice {x['t']} {x['colour']}: chose {x['choice']}; leading {x['top'][:3]}")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
