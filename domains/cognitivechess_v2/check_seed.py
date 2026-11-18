"""Checks league.seat_copy: the game-12 mind copied to a White seat and a Black seat (fresh worlds at the start, its lifelong records
carried), the two copies playing one short game through chessduel. Nothing is saved. python -u -X utf8 check_seed.py [checkpoint]"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
import league
import mate_oracle
import rung4p
from chessduel import BLACK, WHITE, ChessDuel, configure

src = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/rung4p_full_s0_g12.pkl"
agents, worlds = {}, {}
for side, profile in ((WHITE, league.PROFILES["steady"]), (BLACK, league.PROFILES["grieving"])):
    a, w0, _, _ = rung4p.load_run(src)
    w = league.seat_copy(a, w0, side, seed=0, half_moves=12)
    configure(a, profile)
    agents[side], worlds[side] = a, w
    print(f"{w.me_name}: start {w.board.to_fen().split()[0] == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'}, moved {w.moved}, "
          f"games carried {len(w.games)}, forced mates carried {len(w.__dict__.get('forced_mate_log', []))}, "
          f"agent.world is the seat {a.world is w}, tool on the seat {a.tool.world is w}, act wrapped by it "
          f"{w.__dict__.get('_noticed_by') is a}, acceptance {a.mind.p.acceptance}, outcome object {w.outcome_obj in w.objs}")
d = ChessDuel(agents, worlds)
r = d.play_game()
print("result:", worlds[WHITE].games[-1], "|", worlds[BLACK].games[-1])
ok = worlds[WHITE].games[-1][0] == worlds[BLACK].games[-1][0] and len(worlds[WHITE].games) == 13
print("ALL OK" if ok else "BAD")
mate_oracle.close()
