import os
import threading
from gi.repository import GLib
from .downloader import Download, Status

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
MAX_CONCURRENT = 3


class DownloadManager:
    def __init__(self):
        self._downloads = []       # ordered list of Download objects
        self._lock = threading.Lock()
        self._on_changed = []      # GTK-safe callbacks

    # ------------------------------------------------------------------ public

    def add(self, url, filename, dest=None, referrer=None, cookies=None):
        dest = dest or DEFAULT_DOWNLOAD_DIR
        dl = Download(url, dest, filename, referrer=referrer, cookies=cookies)
        dl.on_progress = self._on_download_progress
        dl.on_complete = self._on_download_complete
        with self._lock:
            self._downloads.append(dl)
        self._notify()
        self._schedule()
        return dl

    def remove(self, dl):
        dl.cancel()
        with self._lock:
            try:
                self._downloads.remove(dl)
            except ValueError:
                pass
        self._notify()

    def pause_all(self):
        for dl in self._active():
            dl.pause()

    def resume_all(self):
        for dl in self._downloads:
            if dl.status == Status.PAUSED:
                dl.resume()
        self._schedule()

    @property
    def downloads(self):
        with self._lock:
            return list(self._downloads)

    def connect_changed(self, callback):
        self._on_changed.append(callback)

    # ----------------------------------------------------------------- private

    def _active(self):
        return [d for d in self._downloads if d.status == Status.DOWNLOADING]

    def _schedule(self):
        pending = [d for d in self._downloads if d.status == Status.PENDING]
        slots = MAX_CONCURRENT - len(self._active())
        for dl in pending[:slots]:
            dl.start()

    def _on_download_progress(self, dl):
        GLib.idle_add(self._notify)

    def _on_download_complete(self, dl):
        GLib.idle_add(self._notify)
        GLib.idle_add(self._schedule)

    def _notify(self):
        for cb in self._on_changed:
            cb()
        return False   # don't re-schedule idle callback
