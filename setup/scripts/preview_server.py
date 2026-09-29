#!/usr/bin/env python3
"""Hardened localhost preview server intended to sit behind an HTTPS tunnel."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

PREVIEW_ID = re.compile(r"^[0-9a-f]{16}$")


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "HermesPreview/1.0"

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

    def do_HEAD(self) -> None:
        self._serve(send_body=False)

    def do_GET(self) -> None:
        self._serve(send_body=True)

    def _error(self, code: int, message: str, send_body: bool) -> None:
        body = (message + "\n").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _serve(self, send_body: bool) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/healthz":
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)
            return

        try:
            decoded = unquote(parsed.path, errors="strict")
        except UnicodeError:
            self._error(400, "Bad request", send_body)
            return
        parts = decoded.split("/")
        if len(parts) < 3 or parts[0] != "" or parts[1] != "preview" or not PREVIEW_ID.fullmatch(parts[2]):
            self._error(404, "Not found", send_body)
            return
        relative_parts = parts[3:]
        if any(part in (".", "..") or "\\" in part or "\x00" in part for part in relative_parts):
            self._error(404, "Not found", send_body)
            return
        if ".preview_meta.json" in relative_parts:
            self._error(404, "Not found", send_body)
            return

        preview_root = (self.server.preview_root / parts[2]).resolve()
        if not preview_root.is_dir() or preview_root.parent != self.server.preview_root:
            self._error(404, "Not found", send_body)
            return
        target = preview_root.joinpath(*relative_parts).resolve()
        if target != preview_root and preview_root not in target.parents:
            self._error(404, "Not found", send_body)
            return

        if target.is_dir():
            if not parsed.path.endswith("/"):
                location = quote(parsed.path, safe="/%") + "/"
                if parsed.query:
                    location += "?" + parsed.query
                self.send_response(301)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            target = target / "index.html"
        if not target.is_file() or (target != preview_root and preview_root not in target.resolve().parents):
            self._error(404, "Not found", send_body)
            return

        try:
            size = target.stat().st_size
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if send_body:
                with target.open("rb") as source:
                    while chunk := source.read(64 * 1024):
                        self.wfile.write(chunk)
        except OSError:
            self._error(404, "Not found", send_body)

    def log_message(self, format: str, *args: object) -> None:
        super().log_message(format, *args)


class PreviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], preview_root: Path):
        self.preview_root = preview_root.resolve()
        super().__init__(address, PreviewHandler)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    if not root.is_dir():
        parser.error(f"directory does not exist: {root}")
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    PreviewServer((args.bind, args.port), root).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
