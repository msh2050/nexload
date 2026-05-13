import os
import re
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.error
from enum import Enum

_TMP_DIR = os.path.join(tempfile.gettempdir(), "nexload_tmp")


# ── aria2c discovery ──────────────────────────────────────────────────────────

_ARIA2C_BIN = None
_ARIA2C_CHECKED = False
_ARIA2C_LOCK = threading.Lock()


def _find_aria2c():
    global _ARIA2C_BIN, _ARIA2C_CHECKED
    with _ARIA2C_LOCK:
        if _ARIA2C_CHECKED:
            return _ARIA2C_BIN
        _ARIA2C_CHECKED = True
        for candidate in ("aria2c", "/usr/bin/aria2c", "/usr/local/bin/aria2c"):
            try:
                subprocess.run(
                    [candidate, "--version"],
                    capture_output=True, timeout=5, check=True,
                )
                _ARIA2C_BIN = candidate
                return candidate
            except Exception:
                continue
        return None


# ── aria2c output parsing ─────────────────────────────────────────────────────

# Matches: [#abc123 5.55GiB/21.1GiB(26%) CN:8 DL:1.10MiB/s ETA:9m20s]
_ARIA2_RE = re.compile(
    r'\[#\w+\s+([\d.]+\S+?)/([\d.]+\S+?)\((\d+)%\)'
    r'(?:\s+CN:(\d+))?'
    r'(?:.*?DL:([\d.]+\S+/s))?'
    r'(?:.*?ETA:(\S+))?\]',
    re.DOTALL,
)

_SIZE_UNITS  = {"GiB": 1 << 30, "MiB": 1 << 20, "KiB": 1 << 10, "B": 1,
                "GB": 10**9,    "MB": 10**6,    "KB": 10**3}
_SPEED_UNITS = {"GiB/s": 1 << 30, "MiB/s": 1 << 20, "KiB/s": 1 << 10, "B/s": 1,
                "GB/s": 10**9,    "MB/s": 10**6,    "KB/s": 10**3}


def _parse_size(s: str) -> int:
    for u, m in _SIZE_UNITS.items():
        if s.endswith(u):
            try:
                return int(float(s[: -len(u)]) * m)
            except ValueError:
                pass
    return 0


def _parse_aria2_speed(s: str) -> float:
    if not s:
        return 0.0
    for u, m in _SPEED_UNITS.items():
        if s.endswith(u):
            try:
                return float(s[: -len(u)]) * m
            except ValueError:
                pass
    return 0.0


def _parse_aria2_eta(s: str) -> int:
    if not s or s in ("--", "N/A", "?"):
        return -1
    total = 0
    for num, unit in re.findall(r"(\d+)([hms])", s):
        n = int(num)
        if unit == "h":
            total += n * 3600
        elif unit == "m":
            total += n * 60
        elif unit == "s":
            total += n
    return total if total > 0 else -1


# ── constants ─────────────────────────────────────────────────────────────────

CHUNK_PARTS = 8       # urllib fallback parallel connections
CHUNK_SIZE  = 256 * 1024
MAX_RETRIES = 8       # urllib fallback retries
RETRY_DELAY = 5       # seconds between urllib retries


# ── Status ────────────────────────────────────────────────────────────────────

class Status(Enum):
    PENDING    = "Pending"
    DOWNLOADING = "Downloading"
    PAUSED     = "Paused"
    COMPLETE   = "Complete"
    ERROR      = "Error"
    CANCELLED  = "Cancelled"


# ── Download ──────────────────────────────────────────────────────────────────

class Download:
    def __init__(self, url, dest_path, filename, referrer=None, cookies=None):
        self.url       = url
        self.dest_path = dest_path
        self.filename  = filename
        self.referrer  = referrer
        self.cookies   = cookies

        self.total_size  = 0
        self.downloaded  = 0
        self.speed       = 0.0   # bytes/sec
        self.eta         = -1    # seconds remaining (-1 = unknown)
        self.connections = 0
        self.final_path  = None
        self.status      = Status.PENDING
        self.error_msg   = ""

        self._lock        = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancel_flag = False
        self._thread      = None
        self._proc        = None

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
        """Reset an errored/cancelled HTTP download and requeue it."""
        if self.status not in (Status.ERROR, Status.CANCELLED):
            return
        self._cancel_flag = False
        self._pause_event.set()
        self.error_msg = ""
        self.status    = Status.PENDING
        self._notify()

    def _notify(self):
        if self.on_progress:
            self.on_progress(self)

    # ── entry point ───────────────────────────────────────────────────────────

    def _run(self):
        self.status = Status.DOWNLOADING
        dest_file = os.path.join(self.dest_path, self.filename)
        os.makedirs(self.dest_path, exist_ok=True)
        os.makedirs(_TMP_DIR, exist_ok=True)

        aria2c = _find_aria2c()
        if aria2c:
            self._run_aria2c(aria2c, dest_file)
        else:
            self._run_urllib(dest_file)

    # ── aria2c backend ────────────────────────────────────────────────────────

    def _run_aria2c(self, aria2c_bin, dest_file):
        tmp_file = os.path.join(_TMP_DIR, self.filename)

        args = [
            aria2c_bin,
            "--dir",   _TMP_DIR,
            "--out",   self.filename,
            "--continue=true",
            "--split=16",
            "--max-connection-per-server=16",
            "--min-split-size=1M",
            "--max-tries=0",          # retry forever (built-in)
            "--retry-wait=5",
            "--file-allocation=none",
            "--console-log-level=notice",
            "--show-console-readout=false",
            "--summary-interval=1",   # progress line every second
            "--enable-color=false",
        ]
        if self.referrer:
            args += ["--referer", self.referrer]
        if self.cookies:
            args += ["--header", f"Cookie: {self.cookies}"]
        args.append(self.url)

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._proc = proc

        buf = ""
        while True:
            chunk = proc.stdout.read(512)
            if not chunk:
                break
            buf += chunk
            parts = re.split(r"[\r\n]+", buf)
            buf = parts[-1]
            for line in parts[:-1]:
                self._parse_aria2c_line(line.strip())

        proc.wait()
        self._proc = None

        if self._cancel_flag:
            return

        if proc.returncode == 0 and os.path.exists(tmp_file):
            os.makedirs(self.dest_path, exist_ok=True)
            os.replace(tmp_file, dest_file)
            self.final_path  = dest_file
            self.status      = Status.COMPLETE
            self.downloaded  = self.total_size
            self.eta         = 0
            self.speed       = 0.0
            self.connections = 0
            if self.on_complete:
                self.on_complete(self)
        else:
            self.status    = Status.ERROR
            self.error_msg = f"aria2c exited with code {proc.returncode}"
            self._notify()

    def _parse_aria2c_line(self, line):
        m = _ARIA2_RE.search(line)
        if not m:
            return
        dl_str, tot_str, _pct, cn_str, speed_str, eta_str = m.groups()
        total = _parse_size(tot_str)
        if total > 0:
            self.total_size = total
            self.downloaded = _parse_size(dl_str)
        self.connections = int(cn_str or 1)
        self.speed       = _parse_aria2_speed(speed_str or "")
        self.eta         = _parse_aria2_eta(eta_str or "")
        self._notify()

    # ── urllib fallback backend ───────────────────────────────────────────────

    def _run_urllib(self, dest_file):
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
                    self.status     = Status.COMPLETE
                    self.eta        = 0
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
                    self.status    = Status.DOWNLOADING
                else:
                    self.status    = Status.ERROR
                    self.error_msg = str(e)
                    self._notify()

    def _build_opener(self):
        opener  = urllib.request.build_opener()
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
                size          = int(resp.headers.get("Content-Length", 0))
                accept_ranges = resp.headers.get("Accept-Ranges", "") == "bytes"
                return size, accept_ranges
        except Exception:
            return 0, False

    def _update_eta(self):
        if self.speed > 0 and self.total_size > self.downloaded:
            self.eta = int((self.total_size - self.downloaded) / self.speed)
        else:
            self.eta = -1

    def _download_sequential(self, opener, dest_file):
        tmp        = os.path.join(_TMP_DIR, self.filename + ".part")
        start_byte = os.path.getsize(tmp) if os.path.exists(tmp) else 0

        headers = {}
        if start_byte:
            headers["Range"] = f"bytes={start_byte}-"

        req         = urllib.request.Request(self.url, headers=headers)
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
                n            = len(chunk)
                self.downloaded += n
                speed_bytes  += n
                elapsed = time.monotonic() - speed_start
                if elapsed >= 0.5:
                    self.speed  = speed_bytes / elapsed
                    speed_bytes = 0
                    speed_start = time.monotonic()
                    self._update_eta()
                self._notify()

        self.connections = 0
        os.replace(tmp, dest_file)

    def _download_parallel(self, opener, dest_file, total):
        part_size = total // CHUNK_PARTS
        ranges    = []
        for i in range(CHUNK_PARTS):
            start = i * part_size
            end   = (start + part_size - 1) if i < CHUNK_PARTS - 1 else (total - 1)
            ranges.append((start, end))

        tmp_parts = [
            os.path.join(_TMP_DIR, f"{self.filename}.part{i}")
            for i in range(CHUNK_PARTS)
        ]

        resume_bytes     = sum(os.path.getsize(p) if os.path.exists(p) else 0 for p in tmp_parts)
        self.downloaded  = resume_bytes
        self.connections = CHUNK_PARTS

        errors  = []
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
        prev        = self.downloaded
        while any(t.is_alive() for t in threads):
            time.sleep(0.4)
            elapsed = time.monotonic() - speed_start
            if elapsed > 0:
                cur         = self.downloaded
                self.speed  = (cur - prev) / elapsed
                prev        = cur
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
        offset     = os.path.getsize(part_path) if os.path.exists(part_path) else 0
        byte_start = start + offset
        if byte_start > end:
            return

        req = urllib.request.Request(
            self.url, headers={"Range": f"bytes={byte_start}-{end}"}
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
