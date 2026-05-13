import os
import signal
import tempfile
import threading
import time
import urllib.request
import urllib.error
from enum import Enum

_TMP_DIR = os.path.join(tempfile.gettempdir(), "nexload_tmp")


class Status(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"


CHUNK_PARTS = 8
CHUNK_SIZE = 256 * 1024
MAX_RETRIES = 8
RETRY_DELAY = 5   # seconds between retries


class Download:
    def __init__(self, url, dest_path, filename, referrer=None, cookies=None):
        self.url = url
        self.dest_path = dest_path
        self.filename = filename
        self.referrer = referrer
        self.cookies = cookies

        self.total_size = 0
        self.downloaded = 0
        self.speed = 0.0        # bytes/sec
        self.eta = -1           # seconds remaining (-1 = unknown)
        self.connections = 0    # active parallel connections
        self.final_path = None  # set when complete
        self.status = Status.PENDING
        self.error_msg = ""

        self._lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancel_flag = False
        self._thread = None
        self._proc = None       # subprocess.Popen for yt-dlp downloads

        self.on_progress = None
        self.on_complete = None

    @property
    def progress(self):
        if self.total_size > 0:
            return min(self.downloaded / self.total_size, 1.0)
        return 0.0

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        if self._proc is not None:
            try:
                os.kill(self._proc.pid, signal.SIGSTOP)
            except Exception:
                pass
        else:
            self._pause_event.clear()
        self.status = Status.PAUSED
        self._notify()

    def resume(self):
        if self._proc is not None:
            try:
                os.kill(self._proc.pid, signal.SIGCONT)
            except Exception:
                pass
        else:
            self._pause_event.set()
        if self.status == Status.PAUSED:
            self.status = Status.DOWNLOADING
            self._notify()

    def cancel(self):
        self._cancel_flag = True
        self._pause_event.set()
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self.status = Status.CANCELLED
        self._notify()

    def retry(self):
        """Reset an errored HTTP download and restart it (resumes from partial file)."""
        if self.status not in (Status.ERROR, Status.CANCELLED):
            return
        self._cancel_flag = False
        self._pause_event.set()
        self.error_msg = ""
        self.status = Status.PENDING
        self._notify()

    def _notify(self):
        if self.on_progress:
            self.on_progress(self)

    def _build_opener(self):
        opener = urllib.request.build_opener()
        headers = [
            ("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) NexLoad/1.0"),
            ("Accept", "*/*"),
        ]
        if self.referrer:
            headers.append(("Referer", self.referrer))
        if self.cookies:
            headers.append(("Cookie", self.cookies))
        opener.addheaders = headers
        return opener

    def _head(self, opener):
        req = urllib.request.Request(self.url, method="HEAD")
        try:
            with opener.open(req, timeout=15) as resp:
                size = int(resp.headers.get("Content-Length", 0))
                accept_ranges = resp.headers.get("Accept-Ranges", "") == "bytes"
                return size, accept_ranges
        except Exception:
            return 0, False

    def _run(self):
        self.status = Status.DOWNLOADING
        dest_file = os.path.join(self.dest_path, self.filename)
        os.makedirs(self.dest_path, exist_ok=True)
        os.makedirs(_TMP_DIR, exist_ok=True)
        opener = self._build_opener()

        for attempt in range(MAX_RETRIES + 1):
            try:
                total, supports_range = self._head(opener)
                self.total_size = total

                if supports_range and total > 0 and CHUNK_PARTS > 1:
                    self._download_parallel(opener, dest_file, total)
                else:
                    self._download_sequential(opener, dest_file)

                if not self._cancel_flag:
                    self.final_path = dest_file
                    self.status = Status.COMPLETE
                    self.eta = 0
                    if self.on_complete:
                        self.on_complete(self)
                return

            except Exception as e:
                if self._cancel_flag:
                    return
                if attempt < MAX_RETRIES:
                    self.error_msg = f"Connection lost, retrying ({attempt + 1}/{MAX_RETRIES})…"
                    self._notify()
                    for _ in range(RETRY_DELAY):
                        if self._cancel_flag:
                            return
                        time.sleep(1)
                    self.error_msg = ""
                    self.status = Status.DOWNLOADING
                else:
                    self.status = Status.ERROR
                    self.error_msg = str(e)
                    self._notify()

    def _update_eta(self):
        if self.speed > 0 and self.total_size > self.downloaded:
            self.eta = int((self.total_size - self.downloaded) / self.speed)
        else:
            self.eta = -1

    def _download_sequential(self, opener, dest_file):
        tmp = os.path.join(_TMP_DIR, self.filename + ".part")
        start_byte = os.path.getsize(tmp) if os.path.exists(tmp) else 0

        headers = {}
        if start_byte:
            headers["Range"] = f"bytes={start_byte}-"

        req = urllib.request.Request(self.url, headers=headers)
        speed_start = time.monotonic()
        speed_bytes = 0
        self.connections = 1

        with opener.open(req, timeout=30) as resp, open(tmp, "ab") as f:
            self.downloaded = start_byte
            while True:
                self._pause_event.wait()
                if self._cancel_flag:
                    return
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                n = len(chunk)
                self.downloaded += n
                speed_bytes += n
                elapsed = time.monotonic() - speed_start
                if elapsed >= 0.5:
                    self.speed = speed_bytes / elapsed
                    speed_bytes = 0
                    speed_start = time.monotonic()
                    self._update_eta()
                self._notify()

        self.connections = 0
        os.replace(tmp, dest_file)

    def _download_parallel(self, opener, dest_file, total):
        part_size = total // CHUNK_PARTS
        ranges = []
        for i in range(CHUNK_PARTS):
            start = i * part_size
            end = (start + part_size - 1) if i < CHUNK_PARTS - 1 else (total - 1)
            ranges.append((start, end))

        tmp_parts = [
            os.path.join(_TMP_DIR, f"{self.filename}.part{i}")
            for i in range(CHUNK_PARTS)
        ]

        resume_bytes = sum(
            os.path.getsize(p) if os.path.exists(p) else 0
            for p in tmp_parts
        )
        self.downloaded = resume_bytes
        self.connections = CHUNK_PARTS

        errors = []
        threads = []
        for i, (start, end) in enumerate(ranges):
            t = threading.Thread(
                target=self._download_part,
                args=(opener, tmp_parts[i], start, end, errors),
                daemon=True,
            )
            threads.append(t)
            t.start()

        speed_start = time.monotonic()
        prev = self.downloaded
        while any(t.is_alive() for t in threads):
            time.sleep(0.4)
            elapsed = time.monotonic() - speed_start
            if elapsed > 0:
                cur = self.downloaded
                self.speed = (cur - prev) / elapsed
                prev = cur
                speed_start = time.monotonic()
                self._update_eta()
            self.connections = sum(1 for t in threads if t.is_alive())
            self._notify()

        self.connections = 0
        if errors:
            raise errors[0]

        with open(dest_file, "wb") as out:
            for part in tmp_parts:
                with open(part, "rb") as f:
                    while True:
                        buf = f.read(65536)
                        if not buf:
                            break
                        out.write(buf)
                os.remove(part)

    def _download_part(self, opener, part_path, start, end, errors):
        offset = os.path.getsize(part_path) if os.path.exists(part_path) else 0
        byte_start = start + offset
        if byte_start > end:
            return

        req = urllib.request.Request(
            self.url,
            headers={"Range": f"bytes={byte_start}-{end}"}
        )
        try:
            with opener.open(req, timeout=30) as resp, open(part_path, "ab") as f:
                while True:
                    self._pause_event.wait()
                    if self._cancel_flag:
                        return
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    with self._lock:
                        self.downloaded += len(chunk)
        except Exception as e:
            errors.append(e)
