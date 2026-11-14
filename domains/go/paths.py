"""Where this domain finds Gerundelle, its sibling domains and Warp chess's engine, in the gerundelle repository.

- Gerundelle: reference/v3, or $GERUNDELLE. It is put first on sys.path here, and $GERUNDELLE is set to it, so a domain borrowed from
  (mysterymaze's gerundelle_path reads $GERUNDELLE) runs on the same version.
- A sibling domain: domains/<name> (domain("tetris", "run.py")).
- Warp chess's engine (WarpOneChess, the user's; not in this repository): $WARP, else a folder "warponechess" beside the repository.
  The Rust board (warp_board) is a separate wheel, built from that engine's rust_board.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GERUNDELLE = os.environ.get("GERUNDELLE", os.path.join(REPO, "reference", "v3")).replace("\\", "/")
os.environ.setdefault("GERUNDELLE", GERUNDELLE)
WARP = os.environ.get("WARP", os.path.join(os.path.dirname(REPO), "warponechess")).replace("\\", "/")
if GERUNDELLE not in sys.path:
    sys.path.insert(0, GERUNDELLE)


def domain(name, *rest):
    """A sibling domain's folder, or a file in it."""
    return os.path.join(REPO, "domains", name, *rest).replace("\\", "/")


def warp(*rest):
    """Warp chess's engine folder, or a path in it."""
    return os.path.join(WARP, *rest).replace("\\", "/")
