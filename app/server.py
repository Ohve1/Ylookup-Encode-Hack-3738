#!/usr/bin/env python3
"""Serve the reviewer lens. No API keys. Fixture only."""
from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample-close.json"
STATIC = Path(__file__).resolve().parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        if self.path in ("/api/close", "/api/close.json"):
            data = FIXTURE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, fmt, *args):
        print("[reviewer]", fmt % args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8378)
    args = parser.parse_args()
    if not FIXTURE.exists():
        raise SystemExit(f"missing fixture: {FIXTURE}")
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Reviewer lens → http://127.0.0.1:{args.port}")
    print(f"Fixture        → {FIXTURE}")
    print("Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
