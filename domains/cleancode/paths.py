"""Where this domain finds Gerundelle and its sibling domains, in the gerundelle repository.

- Gerundelle: reference/v4, or $GERUNDELLE. It is put first on sys.path here, and $GERUNDELLE is set to it, so a domain borrowed from
  (warpchess's dream and potential, mysterymaze's dream_maze) runs on the same version.
- A sibling domain: domains/<name> (domain("tetris", "run.py")). Clean code reads the switches of tetris's and Go's run.py, and takes
  warpchess's potential and dream, and mysterymaze's dream_maze.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GERUNDELLE = os.environ.get("GERUNDELLE", os.path.join(REPO, "reference", "v4")).replace("\\", "/")
os.environ.setdefault("GERUNDELLE", GERUNDELLE)
if GERUNDELLE not in sys.path:
    sys.path.insert(0, GERUNDELLE)


def domain(name, *rest):
    """A sibling domain's folder, or a file in it."""
    return os.path.join(REPO, "domains", name, *rest).replace("\\", "/")
