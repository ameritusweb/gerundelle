"""Where this domain finds Gerundelle and its sibling domains, in the gerundelle repository.

- Gerundelle: reference/v3, or $GERUNDELLE. It is put first on sys.path here, and $GERUNDELLE is set to it, so a domain borrowed from
  (mysterymaze's gerundelle_path reads $GERUNDELLE) runs on the same version.
- A sibling domain: domains/<name> (domain("tetris", "run.py")).
- Warp chess's self-play openings (optional: only rung4.py's --room other than the chevron reads them): $MINI_GAMES, else a folder
  "mini_games" beside the repository. Warp chess's rules are the Rust board's (domains/warpchess/rust_board, built as its README says).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GERUNDELLE = os.environ.get("GERUNDELLE", os.path.join(REPO, "reference", "v3")).replace("\\", "/")
os.environ.setdefault("GERUNDELLE", GERUNDELLE)
MINI_GAMES = os.environ.get("MINI_GAMES", os.path.join(os.path.dirname(REPO), "mini_games")).replace("\\", "/")
if GERUNDELLE not in sys.path:
    sys.path.insert(0, GERUNDELLE)


def domain(name, *rest):
    """A sibling domain's folder, or a file in it."""
    return os.path.join(REPO, "domains", name, *rest).replace("\\", "/")
