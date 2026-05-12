"""
yt-dlp wrapper — fetches available formats for a video URL.
Tries system yt-dlp first, then ~/.local/bin/yt-dlp, then offers to
download the standalone binary on first use.
"""

import json
import os
import subprocess
import threading
import urllib.request


_YT_DLP_PATHS = [
    "yt-dlp",
    os.path.expanduser("~/.local/bin/yt-dlp"),
    "/usr/local/bin/yt-dlp",
    "/usr/bin/yt-dlp",
]
_YT_DLP_BIN = None     # cached path
_YT_DLP_LOCK = threading.Lock()
_DOWNLOAD_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
)


def _find_or_install():
    global _YT_DLP_BIN
    with _YT_DLP_LOCK:
        if _YT_DLP_BIN:
            return _YT_DLP_BIN
        for p in _YT_DLP_PATHS:
            try:
                subprocess.run(
                    [p, "--version"],
                    capture_output=True,
                    timeout=5,
                    check=True,
                )
                _YT_DLP_BIN = p
                return p
            except Exception:
                continue
        # auto-install
        dest = os.path.expanduser("~/.local/bin/yt-dlp")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        urllib.request.urlretrieve(_DOWNLOAD_URL, dest)
        os.chmod(dest, 0o755)
        _YT_DLP_BIN = dest
        return dest


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


def get_formats(url, timeout=30):
    """Return (title, list[VideoFormat]) or raise on error."""
    ytdlp = _find_or_install()
    result = subprocess.run(
        [ytdlp, "--dump-json", "--no-playlist", url],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed")

    info = json.loads(result.stdout)
    title = info.get("title", "video")
    raw_formats = info.get("formats", [])

    formats = []
    for f in raw_formats:
        vf = VideoFormat(f)
        # skip manifests and storyboards
        if vf.ext in ("mhtml", "vtt"):
            continue
        formats.append(vf)

    # put best combined first, then video-only, then audio-only
    formats.sort(key=lambda f: (
        not (f.has_video and f.has_audio),
        -f.tbr,
    ))
    return title, formats


def best_combined_format(formats):
    for f in formats:
        if f.has_video and f.has_audio:
            return f
    return formats[0] if formats else None


def download_video(url, fmt_id, dest_dir, on_progress=None, timeout=3600):
    """
    Invoke yt-dlp to download video to dest_dir.
    on_progress(percent: float, speed_str: str) called periodically.
    Returns final filepath.
    """
    ytdlp = _find_or_install()
    args = [
        ytdlp,
        "-f", fmt_id,
        "-o", os.path.join(dest_dir, "%(title)s.%(ext)s"),
        "--newline",
        url,
    ]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    last_file = None
    for line in proc.stdout:
        line = line.strip()
        if on_progress and "%" in line:
            try:
                pct = float(line.split("%")[0].split()[-1])
                speed = ""
                if "at" in line:
                    speed = line.split("at")[1].split()[0]
                on_progress(pct, speed)
            except Exception:
                pass
        if line.startswith("[download] Destination:"):
            last_file = line.split("Destination:", 1)[1].strip()
        elif line.startswith("[Merger] Merging"):
            pass
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("yt-dlp exited with error")
    return last_file
