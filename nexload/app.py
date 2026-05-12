import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio

from . import APP_ID, WS_PORT
from .download_manager import DownloadManager
from .ws_server import WebSocketServer
from .window import NexLoadWindow


class NexLoadApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._manager = DownloadManager()
        self._ws = WebSocketServer(WS_PORT)
        self._win = None

    # ────────────────────────────────────────────────── lifecycle

    def do_activate(self):
        if self._win is None:
            self._win = NexLoadWindow(self, self._manager, self._ws)
            self._ws.on_message(self._on_ws_message)
            self._ws.start()
        self._win.present()

    def do_shutdown(self):
        self._ws.stop()
        Gtk.Application.do_shutdown(self)

    # ────────────────────────────────────────────────── WebSocket messages

    def _on_ws_message(self, client, msg):
        if self._win:
            self._win.handle_extension_message(client, msg)
