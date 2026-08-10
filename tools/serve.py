#!/usr/bin/env python3
"""serve.py — local preview that behaves like the production host.

Vercel serves this site with `cleanUrls: true`, so every internal link is
extensionless (`/features`, not `/features.html`). A plain
`python3 -m http.server` does NOT do that mapping, so local previews 404 on
every page and hide real problems. This server mirrors production: clean URLs,
the custom 404, and the same no-trailing-slash behaviour.

    python3 tools/serve.py            # http://localhost:8000
    python3 tools/serve.py --port 9000
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        candidate = os.path.join(ROOT, clean.lstrip("/"))
        if clean in ("", "/"):
            return os.path.join(ROOT, "index.html")
        if os.path.isfile(candidate):
            return candidate
        # cleanUrls: /features -> features.html
        html = candidate.rstrip("/") + ".html"
        if os.path.isfile(html):
            return html
        return candidate

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = os.path.join(ROOT, "404.html")
            if os.path.isfile(page):
                body = open(page, "rb").read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    handler = functools.partial(CleanURLHandler, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"Kairos preview (production-like clean URLs) http://localhost:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
