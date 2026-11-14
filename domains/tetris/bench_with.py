"""Run bench_speed.py with another copy of molecules.py standing in for the one in place (a backup, e.g. molecules.py.before_late_speed),
without touching the file in place: the copy is loaded under the name `molecules` before anything imports it.
Run: PYTHONHASHSEED=0 python -u -X utf8 bench_with.py <molecules file> <checkpoint> [slices] [--profile [file.prof]]
"""
import importlib.machinery
import importlib.util
import runpy
import sys

src = sys.argv.pop(1)
sys.path.insert(0, __import__("paths").GERUNDELLE)
loader = importlib.machinery.SourceFileLoader("molecules", src)
spec = importlib.util.spec_from_loader("molecules", loader)
mod = importlib.util.module_from_spec(spec)
sys.modules["molecules"] = mod
loader.exec_module(mod)
print(f"molecules from {src}", flush=True)
sys.argv[0] = "bench_speed.py"
runpy.run_path("bench_speed.py", run_name="__main__")
