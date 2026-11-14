"""Run a tetris trace script on the Gerundelle code clean5 was started with (11-12, about 17:25): molecules.py and sov_agent.py from the
first backups made after that (clean5_code/), every other module as it is (none changed since). Loaded before run.py puts the live
folder first on the path, so the cached modules are these. python -u -X utf8 with_clean5_code.py <script.py> [args...]"""
import os
import runpy
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __import__("paths").GERUNDELLE)
sys.path.insert(0, os.path.join(here, "clean5_code"))
import molecules  # noqa: E402,F401
import sov_agent  # noqa: E402,F401
assert molecules.__file__.startswith(os.path.join(here, "clean5_code")), molecules.__file__
assert sov_agent.__file__.startswith(os.path.join(here, "clean5_code")), sov_agent.__file__
print(f"clean5 code: {molecules.__file__}, {sov_agent.__file__}", flush=True)
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
