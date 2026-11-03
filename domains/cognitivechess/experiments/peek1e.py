import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rung1e
arm, ticks = sys.argv[1], int(sys.argv[2])
per, done, noticed, m = rung1e.run(0, arm, 20, ticks)
w = m.world
print(arm, "ticks", ticks, "pushes", len(m.agent.tried), "position", w.at, "mated", done, "noticed", noticed,
      "trials", len(m.agent.trials), "subs", len(m.agent.sub_log))
