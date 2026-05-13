"""NexLoad GTK4 window — dark glass design."""

import os
import re
import subprocess
import threading
import types
import urllib.parse

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk, Pango

try:
    import cairo as _cairo
    _HAVE_CAIRO = True
except ImportError:
    _HAVE_CAIRO = False

from .download_manager import DownloadManager, DEFAULT_DOWNLOAD_DIR
from .downloader import Download, Status, find_aria2c, find_axel
from . import video_info
from . import settings as _settings


# ── File-type helpers ─────────────────────────────────────────────────────────

_EXT_ICON = {
    **dict.fromkeys((".mp4",".mkv",".webm",".avi",".mov",".m4v",".flv",".m3u8",".mpd",".wmv"),
                    "video-x-generic-symbolic"),
    **dict.fromkeys((".mp3",".m4a",".flac",".ogg",".wav",".opus",".aac",".wma"),
                    "audio-x-generic-symbolic"),
    **dict.fromkeys((".jpg",".jpeg",".png",".gif",".webp",".svg",".bmp",".tiff"),
                    "image-x-generic-symbolic"),
    **dict.fromkeys((".zip",".tar",".gz",".rar",".7z",".xz",".bz2"),
                    "package-x-generic-symbolic"),
    **dict.fromkeys((".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".odt",".ods"),
                    "x-office-document-symbolic"),
    **dict.fromkeys((".gguf",".bin",".pt",".safetensors"),
                    "application-x-executable-symbolic"),
}
_VIDEO_EXT = {".mp4",".mkv",".webm",".avi",".mov",".m4v",".flv",".m3u8",".mpd",".wmv"}
_AUDIO_EXT = {".mp3",".m4a",".flac",".ogg",".wav",".opus",".aac",".wma"}
_IMAGE_EXT = {".jpg",".jpeg",".png",".gif",".webp",".svg",".bmp",".tiff"}
_DOC_EXT   = {".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".txt",".odt"}


def _file_icon(name: str) -> str:
    return _EXT_ICON.get(os.path.splitext(name)[1].lower(), "text-x-generic-symbolic")


def _ext_cat(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    if ext in _VIDEO_EXT: return "video"
    if ext in _AUDIO_EXT: return "music"
    if ext in _IMAGE_EXT: return "images"
    if ext in _DOC_EXT:   return "documents"
    return "other"


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = b"""
window { background-color: #0d0d14; color: #dde0ef; }

headerbar {
    background-color: #111118;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    box-shadow: none;
    color: #dde0ef;
}
headerbar label { color: #dde0ef; }
headerbar button { border-radius: 8px; color: rgba(255,255,255,0.75); }
headerbar button:hover { background-color: rgba(255,255,255,0.08); }

scrolledwindow, viewport { background-color: transparent; }

/* Sidebar */
.nx-sidebar {
    background-color: #0d0d14;
    border-right: 1px solid rgba(255,255,255,0.07);
}
.nx-sec-label {
    font-size: 10px;
    font-family: monospace;
    font-weight: 500;
    color: rgba(255,255,255,0.28);
}
.nx-nav-btn {
    border-radius: 10px;
    background: transparent;
    border: 1px solid transparent;
    padding: 7px 10px;
    color: rgba(255,255,255,0.52);
    font-size: 13px;
}
.nx-nav-btn:hover {
    background-color: rgba(255,255,255,0.04);
    color: rgba(255,255,255,0.82);
}
.nx-nav-btn.nx-active {
    background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
    border-color: rgba(255,255,255,0.11);
    color: #e8eaf6;
}
.nx-count { font-size: 10px; font-family: monospace; color: rgba(255,255,255,0.28); }

/* Cards */
.nx-card {
    background-color: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
}
.nx-card:hover {
    background-color: rgba(255,255,255,0.052);
    border-color: rgba(255,255,255,0.10);
}

/* Progress bars */
.nx-bar trough {
    background-color: rgba(255,255,255,0.07);
    border-radius: 999px;
    min-height: 6px;
    border: none;
}
.nx-bar trough progress {
    background: linear-gradient(to right, #00d4a0, #7c3aed);
    border-radius: 999px;
    min-height: 6px;
}
.nx-bar.error trough progress { background: #f87171; }
.nx-bar.complete trough progress { background: #00d4a0; }
.nx-bar.paused trough progress { background: rgba(255,255,255,0.25); }

/* Buttons */
.nx-btn {
    min-height: 26px;
    padding: 3px 10px;
    border-radius: 8px;
    background-color: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    color: rgba(255,255,255,0.65);
    font-size: 12px;
}
.nx-btn:hover { background-color: rgba(255,255,255,0.09); color: rgba(255,255,255,0.9); }
.nx-btn.stop { color: #f87171; border-color: rgba(248,113,113,0.3); }
.nx-btn.stop:hover { background-color: rgba(248,113,113,0.08); }
.nx-btn.retry { color: #00d4a0; border-color: rgba(0,212,160,0.3); }

/* Text */
.nx-filename { font-size: 13px; font-weight: 500; color: #e0e4f5; }
.nx-meta { font-size: 11px; font-family: monospace; color: rgba(255,255,255,0.35); }
.nx-speed { font-size: 11px; font-family: monospace; color: #00d4a0; font-weight: 500; }
.nx-eta   { font-size: 11px; font-family: monospace; color: rgba(255,255,255,0.40); }
.nx-size  { font-size: 11px; font-family: monospace; color: rgba(255,255,255,0.38); }
.nx-error { font-size: 11px; color: #f87171; }

/* Toolbar */
.nx-toolbar {
    background-color: rgba(255,255,255,0.02);
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.nx-toolbar button {
    border-radius: 8px;
    background-color: transparent;
    border: 1px solid rgba(255,255,255,0.09);
    color: rgba(255,255,255,0.55);
    font-size: 12px;
    padding: 4px 10px;
    min-height: 28px;
}
.nx-toolbar button:hover {
    background-color: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.85);
}

/* Status pill */
.nx-pill {
    padding: 4px 12px;
    border-radius: 999px;
    background-color: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    font-size: 11px;
    font-family: monospace;
    color: rgba(255,255,255,0.52);
}

/* Empty state */
.nx-empty-h { font-size: 22px; color: rgba(255,255,255,0.22); font-weight: 300; }
.nx-empty-s { font-size: 13px; color: rgba(255,255,255,0.18); }

/* Total speed */
.nx-total-speed { font-size: 12px; font-family: monospace; font-weight: 500; color: #00d4a0; }

/* Settings dialog */
.nx-settings-frame > border { border-color: rgba(255,255,255,0.10); border-radius: 8px; }
"""


def _apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_bytes(GLib.Bytes.new(_CSS))
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_size(n):
    if n <= 0: return "—"
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def _fmt_speed(bps):
    if bps <= 0: return ""
    for u in ("B/s", "KB/s", "MB/s", "GB/s"):
        if bps < 1024: return f"{bps:.1f} {u}"
        bps /= 1024
    return f"{bps:.1f} GB/s"


def _fmt_eta(secs):
    if secs < 0: return ""
    if secs < 60: return f"{secs}s"
    if secs < 3600: return f"{secs // 60}m {secs % 60:02d}s"
    h = secs // 3600; m = (secs % 3600) // 60
    return f"{h}h {m:02d}m"


def _xdg_open(path):
    try: subprocess.Popen(["xdg-open", path])
    except Exception: pass


# ── Speed sparkline ───────────────────────────────────────────────────────────

class SpeedGraph(Gtk.DrawingArea):
    _N = 60

    def __init__(self):
        super().__init__()
        self._data = [0.0] * self._N
        self.set_content_height(36)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)

    def push(self, bps: float):
        self._data.pop(0)
        self._data.append(bps)
        self.queue_draw()

    def _draw(self, _area, cr, w, h):
        mx = max(self._data) if self._data else 0
        if mx <= 0:
            return
        step = w / (self._N - 1)
        pts = [(i * step, h - (v / mx) * (h - 6) - 3) for i, v in enumerate(self._data)]

        cr.move_to(0, h)
        for x, y in pts:
            cr.line_to(x, y)
        cr.line_to(w, h)
        cr.close_path()
        if _HAVE_CAIRO:
            grad = _cairo.LinearGradient(0, 0, 0, h)
            grad.add_color_stop_rgba(0, 0.0, 0.83, 0.63, 0.22)
            grad.add_color_stop_rgba(1, 0.0, 0.83, 0.63, 0.0)
            cr.set_source(grad)
        else:
            cr.set_source_rgba(0.0, 0.83, 0.63, 0.15)
        cr.fill()

        cr.move_to(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            cr.line_to(x, y)
        cr.set_source_rgba(0.0, 0.83, 0.63, 0.85)
        cr.set_line_width(1.5)
        cr.stroke()


# ── Download row card ─────────────────────────────────────────────────────────

class DownloadRow(Gtk.Box):
    def __init__(self, dl: Download, on_remove, on_retry=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add_css_class("nx-card")
        self.set_margin_bottom(8)

        self._dl = dl
        self._on_remove = on_remove
        self._on_retry  = on_retry

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        inner.set_margin_top(13)
        inner.set_margin_bottom(11)
        inner.set_margin_start(15)
        inner.set_margin_end(15)
        self.append(inner)

        # Row 1: icon · filename · size
        r1 = Gtk.Box(spacing=9)
        inner.append(r1)

        icon = Gtk.Image.new_from_icon_name(_file_icon(dl.filename))
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        icon.set_opacity(0.45)
        r1.append(icon)

        self._name = Gtk.Label(xalign=0)
        self._name.add_css_class("nx-filename")
        self._name.set_hexpand(True)
        self._name.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        r1.append(self._name)

        self._size = Gtk.Label(xalign=1)
        self._size.add_css_class("nx-size")
        r1.append(self._size)

        # Row 2: progress bar
        self._bar = Gtk.ProgressBar()
        self._bar.set_show_text(False)
        self._bar.add_css_class("nx-bar")
        inner.append(self._bar)

        # Row 3: status · speed · eta
        r3 = Gtk.Box(spacing=10)
        inner.append(r3)

        self._status = Gtk.Label(xalign=0)
        self._status.set_hexpand(True)
        self._status.add_css_class("nx-meta")
        r3.append(self._status)

        self._speed = Gtk.Label(xalign=1)
        self._speed.add_css_class("nx-speed")
        r3.append(self._speed)

        self._eta = Gtk.Label(xalign=1)
        self._eta.add_css_class("nx-eta")
        r3.append(self._eta)

        # Row 4: action buttons
        r4 = Gtk.Box(spacing=5)
        inner.append(r4)

        self._pause_btn  = self._btn("⏸ Pause",     self._do_pause_resume)
        self._stop_btn   = self._btn("⏹ Stop",      self._do_stop,   css="stop")
        self._retry_btn  = self._btn("↺ Retry",     self._do_retry,  css="retry")
        self._folder_btn = self._btn("📁 Folder",   self._do_folder)
        self._file_btn   = self._btn("📄 Open",     self._do_open)
        self._remove_btn = self._btn("✕ Remove",    self._do_remove)

        for b in (self._pause_btn, self._stop_btn, self._retry_btn,
                  self._folder_btn, self._file_btn, self._remove_btn):
            r4.append(b)

        self.refresh()

    def _btn(self, label, cb, css=None):
        b = Gtk.Button(label=label)
        b.add_css_class("nx-btn")
        if css:
            b.add_css_class(css)
        b.connect("clicked", lambda _: cb())
        return b

    def _do_pause_resume(self):
        if self._dl.status == Status.PAUSED:    self._dl.resume()
        elif self._dl.status == Status.DOWNLOADING: self._dl.pause()

    def _do_stop(self):   self._dl.cancel()
    def _do_retry(self):
        if self._on_retry: self._on_retry(self._dl)
    def _do_remove(self): self._on_remove(self._dl)

    def _do_folder(self):
        path = self._dl.final_path or self._dl.dest_path
        _xdg_open(os.path.dirname(path) if os.path.isfile(path) else path)

    def _do_open(self):
        if self._dl.final_path and os.path.isfile(self._dl.final_path):
            _xdg_open(self._dl.final_path)

    def refresh(self):
        dl = self._dl
        st = dl.status

        self._name.set_text(dl.filename)
        self._size.set_text(_fmt_size(dl.total_size))
        self._bar.set_fraction(dl.progress)

        # bar style
        for cls in ("error", "complete", "paused"):
            self._bar.remove_css_class(cls)
        if st == Status.ERROR:     self._bar.add_css_class("error")
        elif st == Status.COMPLETE: self._bar.add_css_class("complete")
        elif st == Status.PAUSED:   self._bar.add_css_class("paused")

        # status text
        self._status.remove_css_class("nx-error")
        self._status.add_css_class("nx-meta")
        if st == Status.ERROR:
            self._status.remove_css_class("nx-meta")
            self._status.add_css_class("nx-error")
            self._status.set_text(f"Error: {dl.error_msg}")
        elif st == Status.DOWNLOADING and dl.total_size > 0:
            self._status.set_text(
                f"{dl.progress*100:.1f}%  ·  {_fmt_size(dl.downloaded)} of {_fmt_size(dl.total_size)}"
            )
        elif st == Status.COMPLETE:
            self._status.set_text(f"Complete  ·  {_fmt_size(dl.total_size)}")
        else:
            self._status.set_text(st.value)

        # speed / ETA
        if st == Status.DOWNLOADING:
            self._speed.set_text(_fmt_speed(dl.speed))
            eta = _fmt_eta(dl.eta)
            self._eta.set_text(f"ETA {eta}" if eta else "")
        else:
            self._speed.set_text("")
            self._eta.set_text("")

        # button visibility
        active = st in (Status.DOWNLOADING, Status.PAUSED)
        failed = st in (Status.ERROR, Status.CANCELLED)
        self._pause_btn.set_visible(active)
        self._pause_btn.set_label("▶ Resume" if st == Status.PAUSED else "⏸ Pause")
        self._stop_btn.set_visible(active)
        self._retry_btn.set_visible(
            failed and self._on_retry is not None and dl._proc is None
        )
        self._file_btn.set_sensitive(
            st == Status.COMPLETE
            and bool(dl.final_path)
            and os.path.isfile(dl.final_path or "")
        )
        self._remove_btn.set_visible(not active)


# ── Empty state ───────────────────────────────────────────────────────────────

class EmptyState(Gtk.Box):
    def __init__(self, message="No downloads yet.", sub="Add a URL or click Download in your browser."):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("emblem-downloads-symbolic")
        icon.set_icon_size(Gtk.IconSize.LARGE)
        icon.set_opacity(0.18)
        icon.set_pixel_size(64)
        self.append(icon)

        h = Gtk.Label(label=message)
        h.add_css_class("nx-empty-h")
        self.append(h)

        s = Gtk.Label(label=sub)
        s.add_css_class("nx-empty-s")
        self.append(s)


# ── Format chooser dialog ─────────────────────────────────────────────────────

class FormatChooserDialog(Gtk.Dialog):
    def __init__(self, parent, title, formats):
        super().__init__(title="Select Format", transient_for=parent, modal=True)
        self.set_default_size(500, 400)
        self.selected_format = None

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_Download", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_margin_top(12); box.set_margin_bottom(12)
        box.set_margin_start(12); box.set_margin_end(12)
        box.set_spacing(8)

        lbl = Gtk.Label(label=f"<b>{GLib.markup_escape_text(title)}</b>", use_markup=True)
        lbl.set_wrap(True); lbl.set_max_width_chars(58)
        box.append(lbl)
        box.append(Gtk.Separator())

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        box.append(scroll)

        self._store   = Gtk.StringList()
        self._formats = []
        for f in formats:
            if f.has_video:
                self._formats.append(f)
                self._store.append(f.label)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda _f, item: item.set_child(
            Gtk.Label(xalign=0, margin_start=8, margin_end=8, margin_top=6, margin_bottom=6)
        ))
        factory.connect("bind", lambda _f, item: item.get_child().set_text(item.get_item().get_string()))

        sel = Gtk.SingleSelection(model=self._store)
        sel.set_selected(0)
        self._sel = sel
        lv = Gtk.ListView(model=sel, factory=factory)
        lv.set_show_separators(True)
        scroll.set_child(lv)

    def get_selected_format(self):
        idx = self._sel.get_selected()
        return self._formats[idx] if idx < len(self._formats) else None


# ── Add download dialog ───────────────────────────────────────────────────────

class AddDownloadDialog(Gtk.Dialog):
    def __init__(self, parent, prefill_url=""):
        super().__init__(title="Add Download", transient_for=parent, modal=True)
        self.set_default_size(520, 220)

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        btn = self.add_button("_Add", Gtk.ResponseType.OK)
        btn.add_css_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(16); box.set_margin_end(16)
        box.set_spacing(10)

        grid = Gtk.Grid(row_spacing=8, column_spacing=10)
        box.append(grid)

        grid.attach(Gtk.Label(label="URL:", xalign=1), 0, 0, 1, 1)
        self._url = Gtk.Entry()
        self._url.set_hexpand(True)
        self._url.set_text(prefill_url)
        self._url.set_activates_default(True)
        self._url.set_placeholder_text("https://…")
        grid.attach(self._url, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Save to:", xalign=1), 0, 1, 1, 1)
        dest_box = Gtk.Box(spacing=6)
        self._dest = _settings.get("download_dir", DEFAULT_DOWNLOAD_DIR)
        self._dest_lbl = Gtk.Label(label=self._dest, xalign=0)
        self._dest_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        self._dest_lbl.set_hexpand(True)
        dest_box.append(self._dest_lbl)
        browse = Gtk.Button(label="Browse…")
        browse.connect("clicked", self._browse)
        dest_box.append(browse)
        grid.attach(dest_box, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Filename:", xalign=1), 0, 2, 1, 1)
        self._fname = Gtk.Entry()
        self._fname.set_hexpand(True)
        self._fname.set_placeholder_text("leave blank to auto-detect")
        self._fname.set_activates_default(True)
        grid.attach(self._fname, 1, 2, 1, 1)

    def _browse(self, _btn):
        d = Gtk.FileDialog()
        d.set_title("Choose download folder")
        d.select_folder(self.get_root(), None, self._folder_chosen)

    def _folder_chosen(self, dialog, result):
        try:
            f = dialog.select_folder_finish(result)
            if f:
                self._dest = f.get_path()
                self._dest_lbl.set_text(self._dest)
        except Exception:
            pass

    @property
    def url(self):      return self._url.get_text().strip()
    @property
    def dest(self):     return self._dest
    @property
    def filename(self):
        n = self._fname.get_text().strip()
        if not n and self.url:
            try:   n = os.path.basename(urllib.parse.urlparse(self.url).path) or "download"
            except: n = "download"
        return n


# ── Settings dialog ───────────────────────────────────────────────────────────

class SettingsDialog(Gtk.Dialog):
    _DL_OPTS = [
        ("auto",    "Auto  (aria2c → axel → built-in)"),
        ("aria2c",  "aria2c  — best for large files & torrents"),
        ("axel",    "axel  — lightweight, fast HTTP"),
        ("builtin", "Built-in  — no dependencies"),
    ]

    def __init__(self, parent):
        super().__init__(title="Settings", transient_for=parent, modal=True)
        self.set_default_size(460, 0)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        ok = self.add_button("_Save", Gtk.ResponseType.OK)
        ok.add_css_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        s   = _settings.all_settings()
        box = self.get_content_area()
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(16); box.set_margin_end(16)
        box.set_spacing(14)

        # Downloader frame
        dl_f = Gtk.Frame(label=" Downloader ")
        dl_f.set_label_align(0.02)
        box.append(dl_f)
        dl_b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        dl_b.set_margin_top(10); dl_b.set_margin_bottom(10)
        dl_b.set_margin_start(12); dl_b.set_margin_end(12)
        dl_f.set_child(dl_b)

        r = Gtk.Box(spacing=10)
        r.append(Gtk.Label(label="Engine:", xalign=0, width_chars=14))
        self._dl_keys = [k for k, _ in self._DL_OPTS]
        opts = Gtk.StringList()
        cur  = s.get("downloader", "auto")
        cur_i = next((i for i, (k, _) in enumerate(self._DL_OPTS) if k == cur), 0)
        for _, lbl in self._DL_OPTS:
            opts.append(lbl)
        self._dl_combo = Gtk.DropDown(model=opts)
        self._dl_combo.set_selected(cur_i)
        self._dl_combo.set_hexpand(True)
        r.append(self._dl_combo)
        dl_b.append(r)

        # install status
        badges = Gtk.Box(spacing=18)
        badges.set_margin_start(24)
        for tool, finder in (("aria2c", find_aria2c), ("axel", find_axel)):
            found = finder() is not None
            sym  = "✓" if found else "✗"
            note = "installed" if found else "not installed"
            lbl  = Gtk.Label(label=f"{sym}  {tool}  {note}", xalign=0)
            lbl.add_css_class("nx-meta" if found else "nx-error")
            badges.append(lbl)
        dl_b.append(badges)

        # connections
        r2 = Gtk.Box(spacing=10)
        r2.append(Gtk.Label(label="Connections:", xalign=0, width_chars=14))
        adj = Gtk.Adjustment(value=s.get("connections", 16), lower=1, upper=64,
                             step_increment=1, page_increment=4)
        self._conn = Gtk.SpinButton(adjustment=adj, numeric=True)
        r2.append(self._conn)
        r2.append(Gtk.Label(label="per download", xalign=0))
        dl_b.append(r2)

        # retries
        r3 = Gtk.Box(spacing=10)
        r3.append(Gtk.Label(label="Max retries:", xalign=0, width_chars=14))
        adj2 = Gtk.Adjustment(value=s.get("max_retries", 8), lower=0, upper=50,
                              step_increment=1, page_increment=5)
        self._retries = Gtk.SpinButton(adjustment=adj2, numeric=True)
        r3.append(self._retries)
        r3.append(Gtk.Label(label="built-in only", xalign=0))
        dl_b.append(r3)

        # Folder frame
        dir_f = Gtk.Frame(label=" Default Download Folder ")
        dir_f.set_label_align(0.02)
        box.append(dir_f)
        dir_b = Gtk.Box(spacing=8)
        dir_b.set_margin_top(10); dir_b.set_margin_bottom(10)
        dir_b.set_margin_start(12); dir_b.set_margin_end(12)
        dir_f.set_child(dir_b)

        self._dir = s.get("download_dir", DEFAULT_DOWNLOAD_DIR)
        self._dir_lbl = Gtk.Label(label=self._dir, xalign=0)
        self._dir_lbl.set_hexpand(True)
        self._dir_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        dir_b.append(self._dir_lbl)
        browse = Gtk.Button(label="Browse…")
        browse.connect("clicked", self._browse_dir)
        dir_b.append(browse)

    def _browse_dir(self, _btn):
        d = Gtk.FileDialog()
        d.set_title("Choose default download folder")
        d.select_folder(self.get_root(), None, self._dir_chosen)

    def _dir_chosen(self, dialog, result):
        try:
            f = dialog.select_folder_finish(result)
            if f:
                self._dir = f.get_path()
                self._dir_lbl.set_text(self._dir)
        except Exception:
            pass

    def get_values(self) -> dict:
        return {
            "downloader":   self._dl_keys[self._dl_combo.get_selected()],
            "connections":  int(self._conn.get_value()),
            "max_retries":  int(self._retries.get_value()),
            "download_dir": self._dir,
        }


# ── Main window ───────────────────────────────────────────────────────────────

_STREAM_RE = re.compile(r'\.(m3u8|mpd)(\?|#|$)', re.IGNORECASE)

_NAV = [
    ("active",    "Active",     "media-playback-start-symbolic"),
    ("queued",    "Queued",     "document-send-symbolic"),
    ("done",      "Completed",  "object-select-symbolic"),
    None,
    ("video",     "Video",      "video-x-generic-symbolic"),
    ("music",     "Music",      "audio-x-generic-symbolic"),
    ("images",    "Images",     "image-x-generic-symbolic"),
    ("documents", "Documents",  "x-office-document-symbolic"),
    ("other",     "Other",      "text-x-generic-symbolic"),
]

_EMPTY_MSGS = {
    "active":    ("No active downloads", "Start one from the browser extension or + Add."),
    "queued":    ("Queue is empty",       "Downloads will queue when slots are full."),
    "done":      ("No completed files",   "Finished downloads will appear here."),
    "video":     ("No video files",       ""),
    "music":     ("No audio files",       ""),
    "images":    ("No image files",       ""),
    "documents": ("No documents",         ""),
    "other":     ("No other files",       ""),
}


class NexLoadWindow(Gtk.ApplicationWindow):
    def __init__(self, app, manager: DownloadManager, ws_server):
        super().__init__(application=app, title="NexLoad")
        self.set_default_size(900, 580)

        _apply_css()

        self._manager = manager
        self._ws      = ws_server
        self._rows: dict = {}
        self._filter  = "active"
        self._speed_graph = SpeedGraph()
        self._speed_history = [0.0] * 60

        manager.connect_changed(self._on_changed)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(outer)

        outer.append(self._build_headerbar())
        outer.append(self._build_toolbar())

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        paned.set_position(210)
        paned.set_shrink_start_child(False)
        paned.set_shrink_end_child(False)
        outer.append(paned)

        paned.set_start_child(self._build_sidebar())
        paned.set_end_child(self._build_content())

    def _build_headerbar(self):
        hb = Gtk.HeaderBar()
        hb.set_show_title_buttons(True)

        # Left: logo + name
        left = Gtk.Box(spacing=8)
        logo = Gtk.Image.new_from_icon_name("emblem-downloads")
        logo.set_icon_size(Gtk.IconSize.NORMAL)
        left.append(logo)
        left.append(Gtk.Label(label="NexLoad"))
        hb.pack_start(left)

        # Right: speed graph + settings + add
        right = Gtk.Box(spacing=8)

        self._total_lbl = Gtk.Label(label="")
        self._total_lbl.add_css_class("nx-total-speed")
        right.append(self._total_lbl)

        right.append(self._speed_graph)

        settings_btn = Gtk.Button(label="⚙")
        settings_btn.set_tooltip_text("Settings")
        settings_btn.connect("clicked", self._on_settings)
        right.append(settings_btn)

        add_btn = Gtk.Button(label="+ Add")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add)
        right.append(add_btn)

        hb.pack_end(right)
        return hb

    def _build_toolbar(self):
        bar = Gtk.Box(spacing=6)
        bar.add_css_class("nx-toolbar")
        bar.set_margin_start(8); bar.set_margin_end(8)
        bar.set_margin_top(6);   bar.set_margin_bottom(6)

        for label, cb in (
            ("⏸ Pause All",  lambda _: self._manager.pause_all()),
            ("▶ Resume All", lambda _: self._manager.resume_all()),
            ("✕ Clear Done", lambda _: self._on_clear_done()),
            ("🗑 Clear Temp", lambda _: self._on_clear_temp()),
        ):
            btn = Gtk.Button(label=label)
            btn.connect("clicked", cb)
            bar.append(btn)

        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self._ext_lbl = Gtk.Label(label="⬤  Extension: not connected")
        self._ext_lbl.add_css_class("nx-meta")
        bar.append(self._ext_lbl)

        return bar

    def _build_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("nx-sidebar")
        box.set_margin_top(14)
        box.set_margin_start(8); box.set_margin_end(8)
        box.set_margin_bottom(14)

        self._nav_btns   = {}
        self._count_lbls = {}

        for item in _NAV:
            if item is None:
                sep = Gtk.Separator()
                sep.set_margin_top(6); sep.set_margin_bottom(6)
                box.append(sep)
                continue
            key, label, icon = item
            row = Gtk.Box(spacing=0)

            btn = Gtk.Button()
            btn.add_css_class("nx-nav-btn")
            btn.set_hexpand(True)

            btn_inner = Gtk.Box(spacing=9)
            img = Gtk.Image.new_from_icon_name(icon)
            img.set_icon_size(Gtk.IconSize.NORMAL)
            img.set_pixel_size(15)
            btn_inner.append(img)
            btn_inner.append(Gtk.Label(label=label, xalign=0, hexpand=True))

            cnt = Gtk.Label(label="", xalign=1)
            cnt.add_css_class("nx-count")
            btn_inner.append(cnt)

            btn.set_child(btn_inner)
            btn.connect("clicked", self._on_nav, key)

            if key == self._filter:
                btn.add_css_class("nx-active")

            row.append(btn)
            box.append(row)
            self._nav_btns[key]   = btn
            self._count_lbls[key] = cnt

        return box

    def _build_content(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)

        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._content_box.set_margin_top(12)
        self._content_box.set_margin_bottom(12)
        self._content_box.set_margin_start(12)
        self._content_box.set_margin_end(12)

        self._empty = EmptyState(*_EMPTY_MSGS.get(self._filter, ("No downloads", "")))
        self._content_box.append(self._empty)

        scroll.set_child(self._content_box)
        return scroll

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_nav(self, _btn, key):
        if self._nav_btns.get(self._filter):
            self._nav_btns[self._filter].remove_css_class("nx-active")
        self._filter = key
        if self._nav_btns.get(key):
            self._nav_btns[key].add_css_class("nx-active")
        msg = _EMPTY_MSGS.get(key, ("No downloads", ""))
        self._empty = EmptyState(*msg)
        self._on_changed()

    def _filter_downloads(self, downloads):
        f = self._filter
        if f == "active":    return [d for d in downloads if d.status == Status.DOWNLOADING]
        if f == "queued":    return [d for d in downloads if d.status == Status.PENDING]
        if f == "done":      return [d for d in downloads if d.status == Status.COMPLETE]
        return [d for d in downloads if _ext_cat(d.filename) == f]

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _on_changed(self):
        downloads = self._manager.downloads
        visible   = self._filter_downloads(downloads)
        vis_ids   = {id(d) for d in visible}

        # Update nav badge counts
        count_map = {
            "active":    sum(1 for d in downloads if d.status == Status.DOWNLOADING),
            "queued":    sum(1 for d in downloads if d.status == Status.PENDING),
            "done":      sum(1 for d in downloads if d.status == Status.COMPLETE),
            "video":     sum(1 for d in downloads if _ext_cat(d.filename) == "video"),
            "music":     sum(1 for d in downloads if _ext_cat(d.filename) == "music"),
            "images":    sum(1 for d in downloads if _ext_cat(d.filename) == "images"),
            "documents": sum(1 for d in downloads if _ext_cat(d.filename) == "documents"),
            "other":     sum(1 for d in downloads if _ext_cat(d.filename) == "other"),
        }
        for key, cnt in count_map.items():
            if key in self._count_lbls:
                self._count_lbls[key].set_text(str(cnt) if cnt else "")

        # Remove rows no longer visible
        for key in list(self._rows):
            if key not in vis_ids:
                row = self._rows.pop(key)
                self._content_box.remove(row)

        # Add or refresh rows
        for dl in visible:
            key = id(dl)
            if key in self._rows:
                self._rows[key].refresh()
            else:
                row = DownloadRow(dl, self._manager.remove, self._manager.retry)
                self._rows[key] = row
                self._content_box.append(row)

        # Empty state
        self._empty.set_visible(len(visible) == 0)

        # Total speed + sparkline
        active = [d for d in downloads if d.status == Status.DOWNLOADING]
        total_speed = sum(d.speed for d in active)
        if active:
            self._total_lbl.set_text(_fmt_speed(total_speed) + f"  ·  {len(active)} active")
        else:
            self._total_lbl.set_text("")
        self._speed_graph.push(total_speed)

    # ── Add / format chooser ──────────────────────────────────────────────────

    def _on_add(self, _btn):
        d = AddDownloadDialog(self)
        d.connect("response", self._add_response, "")
        d.present()

    def _add_response(self, dialog, response, referrer):
        if response == Gtk.ResponseType.OK and dialog.url:
            self._start_download_or_video(dialog.url, dialog.filename, dialog.dest, referrer)
        dialog.destroy()

    def _start_download_or_video(self, url, filename, dest, referrer=""):
        if _looks_like_video_site(url):
            self._fetch_formats(url, dest or DEFAULT_DOWNLOAD_DIR, referrer)
        else:
            self._manager.add(url, filename, dest or DEFAULT_DOWNLOAD_DIR, referrer=referrer or None)

    def _download_stream_url(self, url, dest, referrer="", title=""):
        if not title:
            try:
                title = os.path.splitext(os.path.basename(urllib.parse.urlparse(url).path))[0] or "video"
            except Exception:
                title = "video"
        fmt = types.SimpleNamespace(format_id="best", ext="mp4", filesize=0)
        self._run_ytdlp(url, fmt, title, dest)

    def _fetch_formats(self, url, dest, referrer=""):
        def _worker():
            try:
                title, formats = video_info.get_formats(url)
                GLib.idle_add(self._show_format_chooser, url, title, formats, dest)
            except Exception as e:
                GLib.idle_add(self._show_error, f"Could not fetch formats:\n{e}")
        threading.Thread(target=_worker, daemon=True).start()

    def _show_format_chooser(self, url, title, formats, dest):
        if not formats:
            self._show_error("No downloadable formats found.")
            return
        d = FormatChooserDialog(self, title, formats)
        d.connect("response", self._fmt_response, url, title, formats, dest)
        d.present()

    def _fmt_response(self, dialog, response, url, title, formats, dest):
        if response == Gtk.ResponseType.OK:
            fmt = dialog.get_selected_format()
            if fmt:
                self._run_ytdlp(url, fmt, title, dest)
        dialog.destroy()

    def _run_ytdlp(self, url, fmt, title, dest):
        safe = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in title)[:80]
        dl = Download(url, dest, f"{safe}.{fmt.ext}")
        dl.on_progress = self._manager._on_download_progress
        dl.on_complete = self._manager._on_download_complete
        dl.status      = Status.DOWNLOADING
        dl.total_size  = fmt.filesize or 0

        with self._manager._lock:
            self._manager._downloads.append(dl)
        self._manager._notify()

        def _worker():
            try:
                def _prog(pct, speed_bps, eta_secs):
                    dl.downloaded = int(pct)
                    dl.total_size = 100
                    dl.speed      = speed_bps
                    dl.eta        = eta_secs
                    GLib.idle_add(self._manager._notify)

                def _on_proc(proc):
                    dl._proc = proc

                final = video_info.download_video(
                    url, fmt.format_id, dest,
                    on_progress=_prog, on_proc=_on_proc, title=title,
                )
                if not dl._cancel_flag:
                    dl.status     = Status.COMPLETE
                    dl.downloaded = 100
                    dl.total_size = 100
                    dl.eta        = 0
                    dl.speed      = 0
                    dl.final_path = final
            except Exception as e:
                if not dl._cancel_flag:
                    dl.status    = Status.ERROR
                    dl.error_msg = str(e)
            GLib.idle_add(self._manager._notify)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Toolbar actions ───────────────────────────────────────────────────────

    def _on_clear_done(self):
        for d in [d for d in self._manager.downloads
                  if d.status in (Status.COMPLETE, Status.ERROR, Status.CANCELLED)]:
            self._manager.remove(d)

    def _on_clear_temp(self):
        from .downloader import _TMP_DIR
        active = {d.filename for d in self._manager.downloads
                  if d.status in (Status.DOWNLOADING, Status.PAUSED)}
        try:
            n = 0
            for name in os.listdir(_TMP_DIR):
                base = name.split(".part")[0]
                if base not in active:
                    try:
                        os.remove(os.path.join(_TMP_DIR, name))
                        n += 1
                    except Exception:
                        pass
        except FileNotFoundError:
            n = 0

    def _on_settings(self, _btn):
        d = SettingsDialog(self)
        d.connect("response", self._settings_response)
        d.present()

    def _settings_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            _settings.save(dialog.get_values())
        dialog.destroy()

    # ── Error dialog ──────────────────────────────────────────────────────────

    def _show_error(self, msg):
        d = Gtk.AlertDialog()
        d.set_message("Error")
        d.set_detail(msg)
        d.show(self)

    # ── Extension callbacks ───────────────────────────────────────────────────

    def handle_extension_message(self, _client, msg):
        action   = msg.get("action", "")
        url      = msg.get("url", "")
        referrer = msg.get("referrer", "")
        filename = msg.get("filename", "")
        title    = msg.get("title", "")

        if action == "download":
            GLib.idle_add(self._start_download_or_video, url, filename, None, referrer)
        elif action == "download_video":
            if _STREAM_RE.search(url):
                GLib.idle_add(self._download_stream_url, url, DEFAULT_DOWNLOAD_DIR, referrer, title)
            else:
                GLib.idle_add(self._fetch_formats, url, DEFAULT_DOWNLOAD_DIR, referrer)

    def notify_extension_connected(self):
        GLib.idle_add(self._ext_lbl.set_label, "⬤  Extension: connected")

    def notify_extension_disconnected(self):
        GLib.idle_add(self._ext_lbl.set_label, "⬤  Extension: not connected")


# ── URL helpers ───────────────────────────────────────────────────────────────

def _is_direct_stream(url):
    return bool(_STREAM_RE.search(url))


def _looks_like_video_site(url):
    if _is_direct_stream(url):
        return True
    video_hosts = (
        "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
        "twitch.tv", "tiktok.com", "twitter.com", "x.com",
        "facebook.com", "instagram.com", "reddit.com",
    )
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return any(host == h or host.endswith("." + h) for h in video_hosts)
    except Exception:
        return False
