import threading
import time
import os
import urllib.request
import urllib.error
from enum import Enum


class Status(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"


CHUNK_PARTS = 8       # parallel connections per download
CHUNK_SIZE = 256*1024 # bytes per read per thread


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
        self.status = Status.PENDING
        self.error_msg = ""

        self._lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancel_flag = False
        self._thread = None

        self.on_progress = None   # callback(download)
        self.on_complete = None   # callback(download)

    @property
    def progress(self):
        if self.total_size > 0:
            return self.downloaded / self.total_size
        return 0.0

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        self._pause_event.clear()
        self.status = Status.PAUSED
        self._notify()

    def resume(self):
        self._pause_event.set()
        if self.status == Status.PAUSED:
            self.status = Status.DOWNLOADING
            self._notify()

    def cancel(self):
        self._cancel_flag = True
        self._pause_event.set()
        self.status = Status.CANCELLED
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
        filepath = os.path.join(self.dest_path, self.filename)
        os.makedirs(self.dest_path, exist_ok=True)
        opener = self._build_opener()

        try:
            total, supports_range = self._head(opener)
            self.total_size = total

            if supports_range and total > 0 and CHUNK_PARTS > 1:
                self._download_parallel(opener, filepath, total)
            else:
                self._download_sequential(opener, filepath)

            if not self._cancel_flag:
                self.status = Status.COMPLETE
                if self.on_complete:
                    self.on_complete(self)
        except Exception as e:
            if not self._cancel_flag:
                self.status = Status.ERROR
                self.error_msg = str(e)
                self._notify()

    def _download_sequential(self, opener, filepath):
        tmp = filepath + ".nexload_tmp"
        start_byte = 0

        if os.path.exists(tmp):
            start_byte = os.path.getsize(tmp)

        headers = {}
        if start_byte:
            headers["Range"] = f"bytes={start_byte}-"

        req = urllib.request.Request(self.url, headers=headers)
        speed_start = time.monotonic()
        speed_bytes = 0

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
                self._notify()

        os.replace(tmp, filepath)

    def _download_parallel(self, opener, filepath, total):
        part_size = total // CHUNK_PARTS
        ranges = []
        for i in range(CHUNK_PARTS):
            start = i * part_size
            end = (start + part_size - 1) if i < CHUNK_PARTS - 1 else (total - 1)
            ranges.append((start, end))

        tmp_parts = [f"{filepath}.part{i}" for i in range(CHUNK_PARTS)]

        # resume: skip already-complete parts
        resume_bytes = sum(
            os.path.getsize(p) if os.path.exists(p) else 0
            for p in tmp_parts
        )
        self.downloaded = resume_bytes

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
            time.sleep(0.5)
            elapsed = time.monotonic() - speed_start
            cur = self.downloaded
            self.speed = (cur - prev) / elapsed
            prev = cur
            speed_start = time.monotonic()
            self._notify()

        if errors:
            raise errors[0]

        # assemble
        with open(filepath, "wb") as out:
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
