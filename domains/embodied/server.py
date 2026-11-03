"""The embodied server: serves the three.js scene and receives what the browser's Reader sends back.

    python server.py [port]        (default 8765, localhost only)

GET  /...                  static files under embodied/ (the scene is /scene/)
POST /api/save/<name>      the request body written to embodied/data/<name> (name: letters, digits, . _ -)
"""
import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        m = re.fullmatch(r"/api/save/([\w.-]+)", self.path)
        if not m:
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        os.makedirs(DATA, exist_ok=True)
        with open(os.path.join(DATA, m.group(1)), "wb") as f:
            f.write(body)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"saved {m.group(1)} ({n} bytes)".encode())

    def end_headers(self):   # the scene's modules change while it is being built: never cache them
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "POST" in (args[0] if args else ""):
            sys.stderr.write("[server] " + fmt % args + "\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=HERE))
    print(f"[server] http://127.0.0.1:{port}/scene/", flush=True)
    srv.serve_forever()
