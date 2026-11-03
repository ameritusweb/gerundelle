"""Run one test of the suite from a given Gerundelle folder: python run_one.py <folder> <test name>."""
import os
import sys

folder, name = sys.argv[1], sys.argv[2]
sys.path.insert(0, folder)
os.chdir(folder)
import test_molecules as T  # noqa: E402

fn = getattr(T, name)
fn = T.seeded(fn) if fn.__name__ in T.SEEDED else fn
title, arms = fn()
print(name, [(a, m.get("passed") if isinstance(m, dict) else None, ok) for a, m, ok in arms])
