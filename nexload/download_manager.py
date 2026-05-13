import json
import os
import threading

from gi.repository import GLib

from .downloader import Download, Status

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
MAX_CONCURRENT = 3
_HISTORY_FILE = os.path.expanduser("~/.local/share/nexload/history.json")


def _save_history(downloads):
    os.makedirs(os.path.dirname(_HISTORY_FILE), exist_ok=True)
    records = []
    for dl in downloads:
        records.append({
            "url": dl.url,
            "filename": dl.filename,
            "dest_path": dl.dest_path,
            "final_path": dl.final_path,
            "total_size": dl.total_size,
            "status": dl.status.value,
            "error_msg": dl.error_msg,
        })
    try:
        with open(_HISTORY_FILE, "w") as f:
            json.dump(records, f, indent=2)
    except Exception:
        pass


def _load_history():
    try:
        with open(_HISTORY_FILE) as f:
            records = json.load(f)
    except Exception:
        return []

    downloads = []
    status_map = {s.value: s for s in Status}
    for r in records:
        dl = Download(r["url"], r["dest_path"], r["filename"])
        dl.final_path = r.get("final_path")
        dl.total_size = r.get("total_size", 0)
        dl.error_msg = r.get("error_msg", "")
        # Only restore finished states; never re-run incomplete downloads
        raw = r.get("status", "")
        if raw in (Status.COMPLETE.value, Status.ERROR.value, Status.CANCELLED.value):
            dl.status = status_map.get(raw, Status.CANCELLED)
            dl.downloaded = dl.total_size
        else:
            dl.status = Status.CANCELLED
        downloads.append(dl)
    return downloads


class DownloadManager:
    def __init__(self):
        self._downloads = _load_history()
        self._lock = threading.Lock()
        self._on_changed = []

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

    def retry(self, dl):
        dl.retry()
        self._schedule()

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
        _save_history(self._downloads)
        for cb in self._on_changed:
            cb()
        return False
