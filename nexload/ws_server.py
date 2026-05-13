"""
Minimal HTTP server for browser-extension ↔ NexLoad communication.

Endpoints:
  GET  /ping     — keepalive probe from the extension
  POST /         — JSON download request from the extension
  OPTIONS *      — CORS / Private Network Access preflight
"""

import json
import select
import socket
import threading
import time

from . import WS_PORT

_DISCONNECTED_AFTER = 20   # seconds without a ping → treat as disconnected


# ─────────────────────────────────────────── HTTP helpers

def _recv_request(sock) -> bytes | None:
    raw = b""
    sock.settimeout(5)
    try:
        while b"\r\n\r\n" not in raw:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            raw += chunk
            if len(raw) > 65536:
                return None
    except Exception:
        return None
    return raw


def _parse_request(raw: bytes) -> tuple[str, str, dict, bytes]:
    """Return (method, path, headers, body)."""
    try:
        header_part, _, rest = raw.partition(b"\r\n\r\n")
        lines = header_part.decode("utf-8", errors="replace").split("\r\n")
        parts = lines[0].split()
        method = parts[0].upper() if parts else "GET"
        path = parts[1] if len(parts) > 1 else "/"
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        length = int(headers.get("content-length", 0))
        body = rest[:length]
        return method, path, headers, body
    except Exception:
        return "GET", "/", {}, b""


def _send_response(sock, status: str, body: bytes = b"", content_type="application/json"):
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Private-Network: true\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    try:
        sock.sendall(headers.encode() + body)
    except Exception:
        pass


def _send_preflight(sock):
    response = (
        "HTTP/1.1 204 No Content\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Private-Network: true\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    try:
        sock.sendall(response.encode())
    except Exception:
        pass


# ─────────────────────────────────────────── server class

class WebSocketServer:
    """Name kept for API compatibility; now uses plain HTTP."""

    def __init__(self, port=WS_PORT):
        self._port = port
        self._lock = threading.Lock()
        self._handlers: list = []
        self._connect_handlers: list = []
        self._disconnect_handlers: list = []
        self._server_sock = None
        self._running = False
        self._last_ping = 0.0
        self._extension_connected = False

    # ─────────────────────────────────────── public API

    def on_message(self, handler):
        self._handlers.append(handler)
        return handler

    def on_connect(self, handler):
        self._connect_handlers.append(handler)
        return handler

    def on_disconnect(self, handler):
        self._disconnect_handlers.append(handler)
        return handler

    def broadcast(self, obj):
        pass   # not used in HTTP model

    def start(self):
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._watchdog, daemon=True).start()

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    # ─────────────────────────────────────── internal

    def _fire_connect(self):
        for h in self._connect_handlers:
            try:
                h(None)
            except Exception:
                pass

    def _fire_disconnect(self):
        for h in self._disconnect_handlers:
            try:
                h(None)
            except Exception:
                pass

    def _note_ping(self):
        with self._lock:
            self._last_ping = time.monotonic()
            if not self._extension_connected:
                self._extension_connected = True
                fire = True
            else:
                fire = False
        if fire:
            self._fire_connect()

    def _watchdog(self):
        while self._running:
            time.sleep(5)
            with self._lock:
                elapsed = time.monotonic() - self._last_ping
                was = self._extension_connected
                if was and elapsed > _DISCONNECTED_AFTER:
                    self._extension_connected = False
                    fire = True
                else:
                    fire = False
            if fire:
                self._fire_disconnect()

    def _accept_loop(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server_sock.bind(("127.0.0.1", self._port))
        except OSError:
            self._server_sock.bind(("127.0.0.1", self._port + 1))
        self._server_sock.listen(20)

        while self._running:
            try:
                r, _, _ = select.select([self._server_sock], [], [], 1.0)
                if r:
                    conn, addr = self._server_sock.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(conn,),
                        daemon=True,
                    ).start()
            except Exception:
                break

    def _handle_client(self, sock):
        raw = _recv_request(sock)
        if not raw:
            sock.close()
            return

        method, path, headers, body = _parse_request(raw)

        if method == "OPTIONS":
            _send_preflight(sock)
            sock.close()
            return

        if method == "GET" and path in ("/ping", "/"):
            self._note_ping()
            _send_response(sock, "200 OK", b'{"status":"ok"}')
            sock.close()
            return

        if method == "POST":
            self._note_ping()
            try:
                msg = json.loads(body.decode("utf-8"))
            except Exception:
                _send_response(sock, "400 Bad Request", b'{"error":"bad json"}')
                sock.close()
                return
            _send_response(sock, "200 OK", b'{"status":"ok"}')
            sock.close()
            for h in self._handlers:
                try:
                    h(None, msg)
                except Exception:
                    pass
            return

        _send_response(sock, "404 Not Found", b'{"error":"not found"}')
        sock.close()
