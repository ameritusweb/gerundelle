"""Serves the site locally as IIS will with site/chess/web.config: cross-origin isolated (COOP same-origin, COEP require-corp) and .wasm as
application/wasm, so the chess page can be tried before it goes up. python -X utf8 serve.py [port] -> http://localhost:<port>/chess/"""
import functools
import http.server
import sys

ROOT = "E:/vscode/substance-structural-coherence/site"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm", ".js": "text/javascript",
                      ".mjs": "text/javascript"}

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)).serve_forever()
