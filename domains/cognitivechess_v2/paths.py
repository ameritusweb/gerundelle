"""Where this domain finds Gerundelle, its sibling domains and its outside tools, in the gerundelle repository.

- Gerundelle: reference/v4, or $GERUNDELLE. It is put first on sys.path here, and $GERUNDELLE is set to it.
- A sibling domain: domains/<name> (domain("tetris", "run.py")). Cognitive chess v2 reads the switches of tetris's and Go's run.py.
- The board: the chess_board Rust crate (chess_board/, built with maturin as its pyproject.toml says, then pip-installed).
- Stockfish (mate_oracle.py: forced mates read only after a capture, a check or a promotion): $STOCKFISH, else `stockfish` on PATH.
- Warp chess's self-play openings (optional, only gameworld.opening_rooms reads them): $MINI_GAMES, else "mini_games" beside the
  repository.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GERUNDELLE = os.environ.get("GERUNDELLE", os.path.join(REPO, "reference", "v4")).replace("\\", "/")
os.environ.setdefault("GERUNDELLE", GERUNDELLE)
STOCKFISH = os.environ.get("STOCKFISH") or shutil.which("stockfish") or "stockfish"
MINI_GAMES = os.environ.get("MINI_GAMES", os.path.join(os.path.dirname(REPO), "mini_games")).replace("\\", "/")
if GERUNDELLE not in sys.path:
    sys.path.insert(0, GERUNDELLE)


def domain(name, *rest):
    """A sibling domain's folder, or a file in it."""
    return os.path.join(REPO, "domains", name, *rest).replace("\\", "/")
