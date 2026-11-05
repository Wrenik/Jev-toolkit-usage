"""The guarded base handler shared by the small local HTTP servers (router, scan, monitor, context).

Security model, identical for all of them: the server binds to 127.0.0.1 only, every request must carry
the tool's custom header (`HEADER: 1`; a web page cannot add a custom header without a CORS preflight,
which these servers never approve), and the Host header must name this server (stops DNS rebinding).
Request bodies are read in full and capped, so a refusal never resets the connection.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class GuardedServer(ThreadingHTTPServer):
    """Threading HTTP server that refuses to share its port.

    The standard library sets SO_REUSEADDR, which on Windows lets a second process bind the same port as well:
    two servers (say the router's and the context server) then listen side by side and requests reach either.
    On Windows reuse is therefore switched off, so the second process fails to bind and the caller can take over.
    """

    allow_reuse_address = os.name != "nt"


class GuardedHandler(BaseHTTPRequestHandler):
    """Subclass and set `HEADER` (and optionally `MAX_BODY_BYTES`); use `_read_body` and `_allowed` in do_GET/do_POST."""

    HEADER = "X-Jev-Router"
    MAX_BODY_BYTES = 1_000_000

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes | None:
        """Reads the whole body first. None, after answering 400/413, when the length is missing, negative or too big."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > self.MAX_BODY_BYTES:
            self.close_connection = True
            self._send(413 if length > self.MAX_BODY_BYTES else 400, {"ok": False, "error": "bad Content-Length"})
            return None
        return self.rfile.read(length) if length else b""

    def _allowed(self) -> bool:
        if self.headers.get(self.HEADER) != "1":
            self._send(403, {"ok": False, "error": f"missing {self.HEADER} header"})
            return False
        port = int(self.server.server_address[1])  # type: ignore[index]
        if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            self._send(403, {"ok": False, "error": "wrong Host header"})
            return False
        return True

    def log_message(self, *args: Any) -> None:
        pass  # decisions go to the tools' JSONL logs, not stderr
