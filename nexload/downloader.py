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

CHUNK_SIZE  = 256 * 1024
CHUNK_PARTS = 8   # urllib parallel connections (overridden by settings)


# ── tool discovery ────────────────────────────────────────────────────────────

_TOOL_LOCK = threading.Lock()
_ARIA2C_BIN: str | None = None
_ARIA2C_CHECKED = False
_AXEL_BIN: str | None = None
_AXEL_CHECKED = False


def find_aria2c() -> str | None:
    global _ARIA2C_BIN, _ARIA2C_CHECKED
    with _TOOL_LOCK:
        if _ARIA2C_CHECKED:
            return _ARIA2C_BIN
        _ARIA2C_CHECKED = True
        for c in ("aria2c", "/usr/bin/aria2c", "/usr/local/bin/aria2c"):
            try:
                subprocess.run([c, "--version"], capture_output=True, timeout=5, check=True)
                _ARIA2C_BIN = c
                return c
            except Exception:
                continue
        return None


def find_axel() -> str | None:
    global _AXEL_BIN, _AXEL_CHECKED
    with _TOOL_LOCK:
        if _AXEL_CHECKED:
            return _AXEL_BIN
        _AXEL_CHECKED = True
        for c in ("axel", "/usr/bin/axel", "/usr/local/bin/axel"):
            try:
                subprocess.run([c, "--version"], capture_output=True, timeout=5, check=True)
                _AXEL_BIN = c
                return c
            except Exception:
                continue
        return None


# ── aria2c output parsers ─────────────────────────────────────────────────────

# [#abc123 5.55GiB/21.1GiB(26%) CN:8 DL:1.10MiB/s ETA:9m20s]
_ARIA2_RE = re.compile(
    r'\[#\w+\s+([\d.]+\S+?)/([\d.]+\S+?)\((\d+)%\)'
    r'(?:\s+CN:(\d+))?'
    r'(?:.*?DL:([\d.]+\S+/s))?'
    r'(?:.*?ETA:(\S+))?\]',
    re.DOTALL,
)

_IEC = {"GiB": 1 << 30, "MiB": 1 << 20, "KiB": 1 << 10, "B": 1,
        "GB": 10**9,    "MB": 10**6,    "KB": 10**3}
_BPS = {"GiB/s": 1 << 30, "MiB/s": 1 << 20, "KiB/s": 1 << 10, "B/s": 1,
        "GB/s": 10**9,    "MB/s": 10**6,    "KB/s": 10**3}


def _parse_iec(s: str) -> int:
    for u, m in _IEC.items():
        if s.endswith(u):
            try:
                return int(float(s[:-len(u)]) * m)
            except ValueError:
                pass
    return 0


def _parse_bps(s: str) -> float:
    if not s:
        return 0.0
    for u, m in _BPS.items():
        if s.endswith(u):
            try:
                return float(s[:-len(u)]) * m
            except ValueError:
                pass
    return 0.0


def _parse_hms(s: str) -> int:
    """'9m20s' or '1h23m45s' → seconds. -1 on failure."""
    if not s or s in ("--", "--:--", "N/A", "?"):
        return -1
    total = 0
    for num, unit in re.findall(r"(\d+)([hms])", s):
        n = int(num)
        if unit == "h":   total += n * 3600
        elif unit == "m": total += n * 60
        elif unit == "s": total += n
    return total if total > 0 else -1


# ── axel output parsers ───────────────────────────────────────────────────────

# [ 26%] [=====>    ] [  1.1 MB/s] [  9m20s ETA]
_AXEL_PCT_RE   = re.compile(r'\[\s*(\d+)%\]')
_AXEL_SPEED_RE = re.compile(r'\[\s*([\d.]+)\s*(KB|MB|GB|B)/s')
_AXEL_ETA_RE   = re.compile(r'\[\s*([\dhms ]+?)\s*ETA\s*\]')
_AXEL_SIZE_RE  = re.compile(r'File size:\s*(\d+)\s*bytes')

_SI = {"GB": 10**9, "MB": 10**6, "KB": 10**3, "B": 1}


def _parse_axel_speed(n: str, unit: str) -> float:
    return float(n) * _SI.get(unit, 1)


def _parse_axel_eta(s: str) -> int:
    return _parse_hms(s.replace(" ", ""))


# ── Status ────────────────────────────────────────────────────────────────────

class Status(Enum):
    PENDING     = "Pending"
    DOWNLOADING = "Downloading"
    PAUSED      = "Paused"
    COMPLETE    = "Complete"
    ERROR       = "Error"
    CANCELLED   = "Cancelled"


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
        self.speed       = 0.0
        self.eta         = -1
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
        from . import settings as _s
        pref  = _s.get("downloader", "auto")
        conns = int(_s.get("connections", 16))

        self.status = Status.DOWNLOADING
        dest_file = os.path.join(self.dest_path, self.filename)
        os.makedirs(self.dest_path, exist_ok=True)
        os.makedirs(_TMP_DIR, exist_ok=True)

        if pref == "aria2c":
            bin_ = find_aria2c()
            if bin_:
                self._run_aria2c(bin_, dest_file, conns)
                return
        elif pref == "axel":
            bin_ = find_axel()
            if bin_:
                self._run_axel(bin_, dest_file, conns)
                return
        elif pref == "builtin":
            self._run_urllib(dest_file, conns)
            return

        # auto: aria2c → axel → builtin
        bin_ = find_aria2c()
        if bin_:
            self._run_aria2c(bin_, dest_file, conns)
            return
        bin_ = find_axel()
        if bin_:
            self._run_axel(bin_, dest_file, conns)
            return
        self._run_urllib(dest_file, conns)

    # ── aria2c backend ────────────────────────────────────────────────────────

    def _run_aria2c(self, aria2c_bin, dest_file, conns):
        tmp_file = os.path.join(_TMP_DIR, self.filename)

        args = [
            aria2c_bin,
            "--dir",   _TMP_DIR,
            "--out",   self.filename,
            "--continue=true",
            f"--split={conns}",
            f"--max-connection-per-server={conns}",
            "--min-split-size=1M",
            "--max-tries=0",
            "--retry-wait=5",
            "--file-allocation=none",
            "--console-log-level=notice",
            "--show-console-readout=false",
            "--summary-interval=1",
            "--enable-color=false",
        ]
        if self.referrer:
            args += ["--referer", self.referrer]
        if self.cookies:
            args += ["--header", f"Cookie: {self.cookies}"]
        args.append(self.url)

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        self._proc = proc
        self.connections = conns

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
        self._finish_proc(proc.returncode, tmp_file, dest_file)

    def _parse_aria2c_line(self, line):
        m = _ARIA2_RE.search(line)
        if not m:
            return
        dl_s, tot_s, _pct, cn_s, spd_s, eta_s = m.groups()
        total = _parse_iec(tot_s)
        if total > 0:
            self.total_size = total
            self.downloaded = _parse_iec(dl_s)
        self.connections = int(cn_s or self.connections or 1)
        self.speed       = _parse_bps(spd_s or "")
        self.eta         = _parse_hms(eta_s or "")
        self._notify()

    # ── axel backend ──────────────────────────────────────────────────────────

    def _run_axel(self, axel_bin, dest_file, conns):
        tmp_file = os.path.join(_TMP_DIR, self.filename)

        args = [
            axel_bin,
            f"--num-connections={conns}",
            f"--output={tmp_file}",
            "--no-clobber",   # resume if .st file exists
        ]
        if self.referrer:
            args += [f"--header=Referer: {self.referrer}"]
        if self.cookies:
            args += [f"--header=Cookie: {self.cookies}"]
        args.append(self.url)

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        self._proc = proc
        self.connections = conns

        buf = ""
        while True:
            chunk = proc.stdout.read(512)
            if not chunk:
                break
            buf += chunk
            parts = re.split(r"[\r\n]+", buf)
            buf = parts[-1]
            for line in parts[:-1]:
                self._parse_axel_line(line.strip())

        proc.wait()
        self._proc = None
        self._finish_proc(proc.returncode, tmp_file, dest_file)

    def _parse_axel_line(self, line):
        size_m = _AXEL_SIZE_RE.search(line)
        if size_m:
            self.total_size = int(size_m.group(1))

        pct_m = _AXEL_PCT_RE.search(line)
        if not pct_m:
            return
        pct = int(pct_m.group(1))
        if self.total_size > 0:
            self.downloaded = int(self.total_size * pct / 100)

        spd_m = _AXEL_SPEED_RE.search(line)
        if spd_m:
            self.speed = _parse_axel_speed(spd_m.group(1), spd_m.group(2))

        eta_m = _AXEL_ETA_RE.search(line)
        if eta_m:
            self.eta = _parse_axel_eta(eta_m.group(1))

        self._notify()

    # ── shared proc finish ────────────────────────────────────────────────────

    def _finish_proc(self, returncode, tmp_file, dest_file):
        if self._cancel_flag:
            return
        if returncode == 0 and os.path.exists(tmp_file):
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
            self.error_msg = f"Exited with code {returncode}"
            self._notify()

    # ── urllib fallback ───────────────────────────────────────────────────────

    def _run_urllib(self, dest_file, conns=8):
        from . import settings as _s
        max_retries = int(_s.get("max_retries", 8))
        opener = self._build_opener()

        for attempt in range(max_retries + 1):
            try:
                total, supports_range = self._head(opener)
                self.total_size = total

                parts = min(conns, CHUNK_PARTS)
                if supports_range and total > 0 and parts > 1:
                    self._download_parallel(opener, dest_file, total, parts)
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
                if attempt < max_retries:
                    self.error_msg = f"Connection lost, retrying ({attempt + 1}/{max_retries})…"
                    self._notify()
                    for _ in range(5):
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
        headers    = {"Range": f"bytes={start_byte}-"} if start_byte else {}
        req        = urllib.request.Request(self.url, headers=headers)

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

    def _download_parallel(self, opener, dest_file, total, parts):
        part_size = total // parts
        ranges    = []
        for i in range(parts):
            start = i * part_size
            end   = (start + part_size - 1) if i < parts - 1 else (total - 1)
            ranges.append((start, end))

        tmp_parts = [
            os.path.join(_TMP_DIR, f"{self.filename}.part{i}")
            for i in range(parts)
        ]
        resume_bytes     = sum(os.path.getsize(p) if os.path.exists(p) else 0 for p in tmp_parts)
        self.downloaded  = resume_bytes
        self.connections = parts

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
