"""Assembles the chess one-on-one into the site (the user, 2026-11-17: "update this with cognitivechess_v2 one on one"; "rust-wasm"): the
page (web/page), the Rust board in WebAssembly (chess_board/pkg-web: wasm-pack build --release --target web --out-dir pkg-web --
--no-default-features --features wasm), Stockfish 19 lite (web/vendor, from the npm package), and bundle.txt: the mind's code
(Gerundelle's register from E:/vscode/analogy/molecules, cognitivechess_v2, python-chess) with the browser's chess_board.py and
mate_oracle.py in place of the native ones. One text file for the code, because a host may refuse to serve .py (IIS does by default).
Run: python -X utf8 build_chess_site.py [--site DIR]"""
import argparse
import base64
import json
import os
import shutil
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.dirname(HERE)
ROOT = os.path.dirname(CC)
G = "E:/vscode/analogy"
MODULES = ["carry", "chessduel", "dream", "dream_worker", "duel", "gameworld", "imagine", "offers", "pairs3", "pieceminds", "plans",
           "plansgame", "plansworld", "potential", "rooms3", "rung0", "rung1d", "rung4", "rung4p", "rustboard", "shoes", "tool",
           "warpworld", "why"]


def files():
    out = [(f"{G}/molecules/molecules.py", "g/molecules.py"), (f"{G}/molecules/sov_agent.py", "g/sov_agent.py"),
           (f"{G}/molecules/force_world.py", "g/force_world.py"), (f"{G}/forces/poc.py", "forces/poc.py"),
           (f"{ROOT}/structuralsimilarity/pair.py", "app/structuralsimilarity/pair.py"),
           (f"{ROOT}/structuralsimilarity/forward.py", "app/structuralsimilarity/forward.py"),
           (f"{HERE}/chess_board.py", "app/cognitivechess_v2/chess_board.py"),
           (f"{HERE}/mate_oracle.py", "app/cognitivechess_v2/mate_oracle.py"),
           (f"{HERE}/web_chess.py", "app/cognitivechess_v2/web_chess.py"),
           # the switch sets rung1d reads out of tetris's and Go's run.py (its /mnt/e fallback)
           (f"{ROOT}/tetris/run.py", "mnt/e/vscode/substance-structural-coherence/tetris/run.py"),
           (f"{ROOT}/go/run.py", "mnt/e/vscode/substance-structural-coherence/go/run.py")]
    out += [(f"{CC}/{m}.py", f"app/cognitivechess_v2/{m}.py") for m in MODULES]
    import chess   # python-chess, pure Python: shipped as files (no package install in the browser)
    pkg = os.path.dirname(chess.__file__)
    for name in os.listdir(pkg):
        if name.endswith(".py"):
            out.append((os.path.join(pkg, name), f"app/chess/{name}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=f"{ROOT}/site/chess")
    args = ap.parse_args()
    os.makedirs(args.site, exist_ok=True)
    for page in ("index.html", "worker.js", "sf_bridge.js", "web.config"):
        shutil.copyfile(os.path.join(HERE, "page", page), os.path.join(args.site, page))
    for name in ("chess_board.js", "chess_board_bg.wasm"):
        shutil.copyfile(os.path.join(CC, "chess_board", "pkg-web", name), os.path.join(args.site, name))
    for name in ("stockfish-19-lite-single.js", "stockfish-19-lite-single.wasm"):
        shutil.copyfile(os.path.join(HERE, "vendor", "package", "bin", name), os.path.join(args.site, name))
    shutil.copyfile(os.path.join(HERE, "vendor", "package", "Copying.txt"), os.path.join(args.site, "stockfish-COPYING.txt"))
    fs = files()
    data = {dst: base64.b64encode(open(src, "rb").read()).decode("ascii") for src, dst in fs}
    with open(os.path.join(args.site, "bundle.txt"), "wb") as f:
        f.write(base64.b64encode(zlib.compress(json.dumps(data).encode("utf-8"), 9)))
    size = sum(os.path.getsize(os.path.join(args.site, n)) for n in os.listdir(args.site))
    print(f"built {args.site}: {len(fs)} files in the bundle; {len(os.listdir(args.site))} files, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
