"""
yt-dlp wrapper — fetches available formats and downloads video.
Tries system yt-dlp first, then ~/.local/bin/yt-dlp, then auto-installs.
"""

import json
import os
import signal
import subprocess
import tempfile
import threading
import urllib.request


_YT_DLP_PATHS = [
    # venv with curl_cffi (impersonation support) takes priority
    os.path.expanduser("~/.local/share/nexload/venv/bin/yt-dlp"),
    "yt-dlp",
    os.path.expanduser("~/.local/bin/yt-dlp"),
    "/usr/local/bin/yt-dlp",
    "/usr/bin/yt-dlp",
]
_YT_DLP_BIN = None
_YT_DLP_LOCK = threading.Lock()
_DOWNLOAD_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
)

NEXLOAD_TMP = os.path.join(tempfile.gettempdir(), "nexload_tmp")


def _find_or_install():
    global _YT_DLP_BIN
    with _YT_DLP_LOCK:
        if _YT_DLP_BIN:
            return _YT_DLP_BIN
        for p in _YT_DLP_PATHS:
            try:
                subprocess.run([p, "--version"], capture_output=True,
                               timeout=5, check=True)
                _YT_DLP_BIN = p
                return p
            except Exception:
                continue
        dest = os.path.expanduser("~/.local/bin/yt-dlp")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        urllib.request.urlretrieve(_DOWNLOAD_URL, dest)
        os.chmod(dest, 0o755)
        _YT_DLP_BIN = dest
        return dest


# ─────────────────────────────────────────── speed / ETA parsers

def _parse_speed(s: str) -> float:
    """'5.23MiB/s' → bytes/sec (0 on failure)."""
    units = {
        "GiB/s": 1024 ** 3, "MiB/s": 1024 ** 2, "KiB/s": 1024,
        "GB/s": 1000 ** 3,  "MB/s": 1000 ** 2,  "KB/s": 1000,
        "B/s": 1,
    }
    s = s.strip()
    for u, m in units.items():
        if s.endswith(u):
            try:
                return float(s[: -len(u)]) * m
            except ValueError:
                pass
    return 0.0


def _parse_eta(s: str) -> int:
    """'01:23' or '01:23:45' → seconds (-1 on failure)."""
    parts = s.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    return -1


# ─────────────────────────────────────────── format model

class VideoFormat:
    __slots__ = ("format_id", "ext", "resolution", "vcodec", "acodec",
                 "filesize", "tbr", "note")

    def __init__(self, d):
        self.format_id = d.get("format_id", "")
        self.ext = d.get("ext", "")
        self.resolution = d.get("resolution") or _res(d)
        self.vcodec = d.get("vcodec", "none")
        self.acodec = d.get("acodec", "none")
        self.filesize = d.get("filesize") or d.get("filesize_approx") or 0
        self.tbr = d.get("tbr") or 0
        self.note = d.get("format_note") or ""

    @property
    def has_video(self):
        return self.vcodec != "none"

    @property
    def has_audio(self):
        return self.acodec != "none"

    @property
    def label(self):
        parts = []
        if self.resolution and self.resolution != "audio only":
            parts.append(self.resolution)
        if self.ext:
            parts.append(self.ext.upper())
        if self.filesize:
            parts.append(_fmt_size(self.filesize))
        if self.note:
            parts.append(self.note)
        return "  ".join(parts) or self.format_id


def _res(d):
    w, h = d.get("width"), d.get("height")
    if w and h:
        return f"{w}x{h}"
    if h:
        return f"{h}p"
    return "audio only"


def _fmt_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ─────────────────────────────────────────── public API

_IMPERSONATE = ["--impersonate", "chrome"]
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def get_formats(url, timeout=30):
    """Return (title, list[VideoFormat]) or raise on error."""
    ytdlp = _find_or_install()
    result = subprocess.run(
        [ytdlp, "--dump-json", "--no-playlist",
         "--user-agent", _UA] + _IMPERSONATE + [url],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed")

    info = json.loads(result.stdout)
    title = info.get("title", "video")
    formats = []
    for f in info.get("formats", []):
        vf = VideoFormat(f)
        if vf.ext in ("mhtml", "vtt"):
            continue
        formats.append(vf)

    formats.sort(key=lambda f: (not (f.has_video and f.has_audio), -f.tbr))
    return title, formats


def best_combined_format(formats):
    for f in formats:
        if f.has_video and f.has_audio:
            return f
    return formats[0] if formats else None


def download_video(url, fmt_id, dest_dir, on_progress=None,
                   on_proc=None, timeout=3600, title=None):
    """
    Invoke yt-dlp to download video.
    Partial files go to NEXLOAD_TMP (system temp); only the finished file
    lands in dest_dir.

    on_progress(pct: float, speed_bps: float, eta_secs: int)
    on_proc(proc: subprocess.Popen)  — called immediately after Popen
    Returns final filepath or None.
    """
    ytdlp = _find_or_install()
    os.makedirs(NEXLOAD_TMP, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)

    if title:
        safe = "".join(
            c if (c.isalnum() or c in " ._-()") else "_" for c in title
        ).strip()[:120]
        out_tmpl = os.path.join(dest_dir, f"{safe}.%(ext)s")
    else:
        out_tmpl = os.path.join(dest_dir, "%(title)s.%(ext)s")

    args = [
        ytdlp,
        "-f", fmt_id,
        "-o", out_tmpl,
        "--paths", f"temp:{NEXLOAD_TMP}",
        "--newline",
        "--progress",
        "--no-playlist",
        "--user-agent", _UA,
    ] + _IMPERSONATE + [url]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if on_proc:
        on_proc(proc)

    last_file = None
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("[download] Destination:"):
            last_file = line.split("Destination:", 1)[1].strip()
        elif line.startswith("[Merger] Merging"):
            pass
        elif on_progress and "%" in line and "[download]" in line:
            try:
                # Example: [download]  45.3% of   1.50GiB at   5.23MiB/s ETA 00:15
                pct = float(line.split("%")[0].split()[-1])
                speed_bps = 0.0
                eta_secs = -1
                if " at " in line:
                    after_at = line.split(" at ", 1)[1].strip()
                    speed_token = after_at.split()[0]
                    speed_bps = _parse_speed(speed_token)
                if "ETA " in line:
                    eta_token = line.split("ETA ", 1)[1].strip().split()[0]
                    eta_secs = _parse_eta(eta_token)
                on_progress(pct, speed_bps, eta_secs)
            except Exception:
                pass

    proc.wait()
    if proc.returncode not in (0, -signal.SIGTERM, -signal.SIGKILL):
        raise RuntimeError("yt-dlp exited with error")
    return last_file
