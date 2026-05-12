"""
Pure-stdlib WebSocket server (RFC 6455, text frames only).
The browser extension connects here; messages are JSON objects.
"""

import base64
import hashlib
import json
import select
import socket
import struct
import threading

from . import WS_PORT

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


# ─────────────────────────────────────────── low-level WebSocket framing

def _handshake(sock, raw_request: bytes) -> bool:
    headers = {}
    try:
        lines = raw_request.decode("utf-8", errors="replace").split("\r\n")
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
    except Exception:
        return False

    key = headers.get("sec-websocket-key")
    if not key:
        return False

    accept = base64.b64encode(
        hashlib.sha1((key + _GUID).encode()).digest()
    ).decode()

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "\r\n"
    )
    sock.sendall(response.encode())
    return True


def _recv_frame(sock) -> tuple[int, bytes] | None:
    """Return (opcode, payload) or None on error/close."""
    try:
        header = _recv_exact(sock, 2)
        if not header:
            return None
        b1, b2 = header
        opcode = b1 & 0x0F
        masked = bool(b2 & 0x80)
        length = b2 & 0x7F

        if length == 126:
            length = struct.unpack(">H", _recv_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack(">Q", _recv_exact(sock, 8))[0]

        mask_key = _recv_exact(sock, 4) if masked else None
        payload = _recv_exact(sock, length) if length else b""

        if masked and mask_key:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

        return opcode, payload
    except Exception:
        return None


def _send_frame(sock, message: str):
    payload = message.encode("utf-8")
    length = len(payload)
    if length < 126:
        header = bytes([0x81, length])
    elif length < 65536:
        header = bytes([0x81, 126]) + struct.pack(">H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack(">Q", length)
    try:
        sock.sendall(header + payload)
    except Exception:
        pass


def _recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf


# ─────────────────────────────────────────────────────── server class

class Client:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr

    def send(self, obj):
        _send_frame(self.sock, json.dumps(obj))

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


class WebSocketServer:
    def __init__(self, port=WS_PORT):
        self._port = port
        self._clients: list[Client] = []
        self._lock = threading.Lock()
        self._handlers: list = []    # (msg_type, callback)
        self._server_sock = None
        self._running = False

    def on_message(self, handler):
        """Register handler(client, msg_dict)."""
        self._handlers.append(handler)
        return handler

    def broadcast(self, obj):
        with self._lock:
            dead = []
            for c in self._clients:
                try:
                    c.send(obj)
                except Exception:
                    dead.append(c)
            for c in dead:
                self._clients.remove(c)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    # ─────────────────────────────────────── internal

    def _accept_loop(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server_sock.bind(("127.0.0.1", self._port))
        except OSError:
            # try next port
            self._server_sock.bind(("127.0.0.1", self._port + 1))
        self._server_sock.listen(10)

        while self._running:
            try:
                r, _, _ = select.select([self._server_sock], [], [], 1.0)
                if r:
                    conn, addr = self._server_sock.accept()
                    t = threading.Thread(
                        target=self._handle_client,
                        args=(conn, addr),
                        daemon=True,
                    )
                    t.start()
            except Exception:
                break

    def _handle_client(self, sock, addr):
        # read HTTP upgrade request
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = sock.recv(4096)
            if not chunk:
                sock.close()
                return
            raw += chunk
            if len(raw) > 8192:
                sock.close()
                return

        if not _handshake(sock, raw):
            sock.close()
            return

        client = Client(sock, addr)
        with self._lock:
            self._clients.append(client)

        try:
            while True:
                frame = _recv_frame(sock)
                if frame is None:
                    break
                opcode, payload = frame
                if opcode == 8:   # close
                    break
                if opcode == 9:   # ping → pong
                    _send_frame(sock, "")
                    continue
                if opcode in (1, 2):  # text / binary
                    try:
                        msg = json.loads(payload.decode("utf-8"))
                    except Exception:
                        continue
                    for h in self._handlers:
                        try:
                            h(client, msg)
                        except Exception:
                            pass
        finally:
            with self._lock:
                try:
                    self._clients.remove(client)
                except ValueError:
                    pass
            client.close()
