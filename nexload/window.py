import os
import re
import subprocess
import threading
import types
import urllib.parse

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio, Pango

from .download_manager import DownloadManager, DEFAULT_DOWNLOAD_DIR
from .downloader import Download, Status, find_aria2c, find_axel
from . import video_info
from . import settings as _settings


# ══════════════════════════════════════════════════════════ helpers

def _fmt_size(n):
    if n <= 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _fmt_speed(bps):
    if bps <= 0:
        return ""
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if bps < 1024:
            return f"{bps:.1f} {unit}"
        bps /= 1024
    return f"{bps:.1f} GB/s"


def _fmt_eta(secs):
    if secs < 0:
        return ""
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m {secs % 60:02d}s"
    h = secs // 3600
    m = (secs % 3600) // 60
    return f"{h}h {m:02d}m"


def _xdg_open(path):
    try:
        subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# ══════════════════════════════════════════════════════════ format chooser

class FormatChooserDialog(Gtk.Dialog):
    def __init__(self, parent, title, formats):
        super().__init__(title="Select Format", transient_for=parent, modal=True)
        self.set_default_size(480, 400)
        self.selected_format = None

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_Download", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_margin_top(12); box.set_margin_bottom(12)
        box.set_margin_start(12); box.set_margin_end(12)
        box.set_spacing(8)

        lbl = Gtk.Label(label=f"<b>{GLib.markup_escape_text(title)}</b>",
                        use_markup=True)
        lbl.set_wrap(True)
        lbl.set_max_width_chars(55)
        box.append(lbl)
        box.append(Gtk.Separator())

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        box.append(scroll)

        self._store = Gtk.StringList()
        self._formats = []
        for f in formats:
            if f.has_video:
                self._formats.append(f)
                self._store.append(f.label)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_item)
        factory.connect("bind", self._bind_item)
        selection = Gtk.SingleSelection(model=self._store)
        selection.set_selected(0)
        self._selection = selection
        lv = Gtk.ListView(model=selection, factory=factory)
        lv.set_show_separators(True)
        scroll.set_child(lv)

    @staticmethod
    def _setup_item(factory, item):
        label = Gtk.Label()
        label.set_xalign(0)
        label.set_margin_start(8); label.set_margin_end(8)
        label.set_margin_top(6); label.set_margin_bottom(6)
        item.set_child(label)

    @staticmethod
    def _bind_item(factory, item):
        item.get_child().set_text(item.get_item().get_string())

    def get_selected_format(self):
        idx = self._selection.get_selected()
        if idx < len(self._formats):
            return self._formats[idx]
        return None


# ══════════════════════════════════════════════════════════ settings dialog

class SettingsDialog(Gtk.Dialog):
    _DOWNLOADER_OPTIONS = [
        ("auto",    "Auto (aria2c → axel → built-in)"),
        ("aria2c",  "aria2c  — best for large files / torrents"),
        ("axel",    "axel  — lightweight, fast HTTP"),
        ("builtin", "Built-in  — no dependencies required"),
    ]

    def __init__(self, parent):
        super().__init__(title="Settings", transient_for=parent, modal=True)
        self.set_default_size(460, 0)

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        btn = self.add_button("_Save", Gtk.ResponseType.OK)
        btn.add_css_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        s = _settings.all_settings()

        box = self.get_content_area()
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(16); box.set_margin_end(16)
        box.set_spacing(16)

        # ── Downloader section
        dl_frame = Gtk.Frame(label=" Downloader ")
        dl_frame.set_label_align(0.02)
        box.append(dl_frame)

        dl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        dl_box.set_margin_top(10); dl_box.set_margin_bottom(10)
        dl_box.set_margin_start(12); dl_box.set_margin_end(12)
        dl_frame.set_child(dl_box)

        # downloader combo
        row = Gtk.Box(spacing=10)
        row.append(Gtk.Label(label="Engine:", xalign=0, width_chars=14))
        self._dl_combo = Gtk.DropDown()
        opts = Gtk.StringList()
        self._dl_keys = []
        current_idx = 0
        for i, (key, label) in enumerate(self._DOWNLOADER_OPTIONS):
            opts.append(label)
            self._dl_keys.append(key)
            if key == s.get("downloader", "auto"):
                current_idx = i
        self._dl_combo.set_model(opts)
        self._dl_combo.set_selected(current_idx)
        self._dl_combo.set_hexpand(True)
        row.append(self._dl_combo)
        dl_box.append(row)

        # status badges
        status_box = Gtk.Box(spacing=16)
        status_box.set_margin_start(14 + 10)
        for tool, finder in (("aria2c", find_aria2c), ("axel", find_axel)):
            found = finder() is not None
            badge = Gtk.Label(
                label=f"{'✓' if found else '✗'}  {tool}  {'installed' if found else 'not found'}",
                xalign=0,
            )
            badge.add_css_class("dim-label")
            if not found:
                badge.add_css_class("error")
            status_box.append(badge)
        dl_box.append(status_box)

        # connections
        row2 = Gtk.Box(spacing=10)
        row2.append(Gtk.Label(label="Connections:", xalign=0, width_chars=14))
        adj = Gtk.Adjustment(
            value=s.get("connections", 16),
            lower=1, upper=64, step_increment=1, page_increment=4,
        )
        self._conn_spin = Gtk.SpinButton(adjustment=adj, numeric=True)
        row2.append(self._conn_spin)
        hint = Gtk.Label(label="parallel connections per download", xalign=0)
        hint.add_css_class("dim-label")
        row2.append(hint)
        dl_box.append(row2)

        # max retries (built-in only)
        row3 = Gtk.Box(spacing=10)
        row3.append(Gtk.Label(label="Max retries:", xalign=0, width_chars=14))
        adj2 = Gtk.Adjustment(
            value=s.get("max_retries", 8),
            lower=0, upper=50, step_increment=1, page_increment=5,
        )
        self._retry_spin = Gtk.SpinButton(adjustment=adj2, numeric=True)
        row3.append(self._retry_spin)
        hint2 = Gtk.Label(label="for built-in downloader", xalign=0)
        hint2.add_css_class("dim-label")
        row3.append(hint2)
        dl_box.append(row3)

        # ── Download folder section
        dir_frame = Gtk.Frame(label=" Default Download Folder ")
        dir_frame.set_label_align(0.02)
        box.append(dir_frame)

        dir_box = Gtk.Box(spacing=8)
        dir_box.set_margin_top(10); dir_box.set_margin_bottom(10)
        dir_box.set_margin_start(12); dir_box.set_margin_end(12)
        dir_frame.set_child(dir_box)

        self._dir_path = s.get("download_dir", DEFAULT_DOWNLOAD_DIR)
        self._dir_label = Gtk.Label(label=self._dir_path, xalign=0)
        self._dir_label.set_hexpand(True)
        self._dir_label.set_ellipsize(Pango.EllipsizeMode.START)
        dir_box.append(self._dir_label)

        browse = Gtk.Button(label="Browse…")
        browse.connect("clicked", self._on_browse)
        dir_box.append(browse)

    def _on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose default download folder")
        dialog.select_folder(self.get_root(), None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self._dir_path = folder.get_path()
                self._dir_label.set_text(self._dir_path)
        except Exception:
            pass

    def get_values(self) -> dict:
        idx = self._dl_combo.get_selected()
        return {
            "downloader":   self._dl_keys[idx],
            "connections":  int(self._conn_spin.get_value()),
            "max_retries":  int(self._retry_spin.get_value()),
            "download_dir": self._dir_path,
        }


# ══════════════════════════════════════════════════════════ add download dialog

class AddDownloadDialog(Gtk.Dialog):
    def __init__(self, parent, prefill_url=""):
        super().__init__(title="Add Download", transient_for=parent, modal=True)
        self.set_default_size(500, 240)

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
        self._url_entry = Gtk.Entry()
        self._url_entry.set_hexpand(True)
        self._url_entry.set_text(prefill_url)
        self._url_entry.set_activates_default(True)
        self._url_entry.set_placeholder_text("https://…")
        grid.attach(self._url_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Save to:", xalign=1), 0, 1, 1, 1)
        dest_box = Gtk.Box(spacing=6)
        self._dest_label = Gtk.Label(label=DEFAULT_DOWNLOAD_DIR, xalign=0)
        self._dest_label.set_ellipsize(Pango.EllipsizeMode.START)
        self._dest_label.set_hexpand(True)
        dest_box.append(self._dest_label)
        browse_btn = Gtk.Button(label="Browse…")
        browse_btn.connect("clicked", self._browse)
        dest_box.append(browse_btn)
        grid.attach(dest_box, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Filename:", xalign=1), 0, 2, 1, 1)
        self._filename_entry = Gtk.Entry()
        self._filename_entry.set_hexpand(True)
        self._filename_entry.set_placeholder_text("leave blank to auto-detect")
        self._filename_entry.set_activates_default(True)
        grid.attach(self._filename_entry, 1, 2, 1, 1)

        self._dest = DEFAULT_DOWNLOAD_DIR

    def _browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose download folder")
        dialog.select_folder(self.get_root(), None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self._dest = folder.get_path()
                self._dest_label.set_text(self._dest)
        except Exception:
            pass

    @property
    def url(self):
        return self._url_entry.get_text().strip()

    @property
    def dest(self):
        return self._dest

    @property
    def filename(self):
        name = self._filename_entry.get_text().strip()
        if not name and self.url:
            try:
                path = urllib.parse.urlparse(self.url).path
                name = os.path.basename(path) or "download"
            except Exception:
                name = "download"
        return name


# ══════════════════════════════════════════════════════════ download row

class DownloadRow(Gtk.Box):
    """One row per download with progress, stats and per-file action buttons."""

    def __init__(self, dl: Download, on_remove, on_retry=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(10)
        self.set_margin_end(10)

        self._dl = dl
        self._on_remove = on_remove
        self._on_retry = on_retry

        # ── row 1: name + size
        top = Gtk.Box(spacing=8)
        self.append(top)

        self._name_lbl = Gtk.Label(label=dl.filename, xalign=0)
        self._name_lbl.set_hexpand(True)
        self._name_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self._name_lbl.add_css_class("heading")
        top.append(self._name_lbl)

        self._size_lbl = Gtk.Label(label="", xalign=1)
        self._size_lbl.add_css_class("dim-label")
        top.append(self._size_lbl)

        # ── row 2: progress bar
        self._progress = Gtk.ProgressBar()
        self._progress.set_show_text(True)
        self.append(self._progress)

        # ── row 3: speed · ETA · connections
        stats = Gtk.Box(spacing=12)
        self.append(stats)

        self._status_lbl = Gtk.Label(label="", xalign=0)
        self._status_lbl.set_hexpand(True)
        self._status_lbl.add_css_class("dim-label")
        stats.append(self._status_lbl)

        self._speed_lbl = Gtk.Label(label="", xalign=1)
        self._speed_lbl.add_css_class("dim-label")
        stats.append(self._speed_lbl)

        self._eta_lbl = Gtk.Label(label="", xalign=1)
        self._eta_lbl.add_css_class("dim-label")
        stats.append(self._eta_lbl)

        self._conn_lbl = Gtk.Label(label="", xalign=1)
        self._conn_lbl.add_css_class("dim-label")
        stats.append(self._conn_lbl)

        # ── row 4: action buttons
        actions = Gtk.Box(spacing=6)
        self.append(actions)

        self._pause_btn = Gtk.Button(label="⏸ Pause")
        self._pause_btn.connect("clicked", self._on_pause_resume)
        actions.append(self._pause_btn)

        self._stop_btn = Gtk.Button(label="⏹ Stop")
        self._stop_btn.connect("clicked", self._on_stop)
        self._stop_btn.add_css_class("destructive-action")
        actions.append(self._stop_btn)

        self._folder_btn = Gtk.Button(label="📁 Open Folder")
        self._folder_btn.connect("clicked", self._on_open_folder)
        actions.append(self._folder_btn)

        self._file_btn = Gtk.Button(label="📄 Open File")
        self._file_btn.connect("clicked", self._on_open_file)
        actions.append(self._file_btn)

        self._retry_btn = Gtk.Button(label="↺ Retry")
        self._retry_btn.connect("clicked", self._on_retry_clicked)
        actions.append(self._retry_btn)

        self._remove_btn = Gtk.Button(label="✕ Remove")
        self._remove_btn.connect("clicked", self._on_remove_clicked)
        actions.append(self._remove_btn)

        self.refresh()

    # ── button callbacks

    def _on_pause_resume(self, btn):
        dl = self._dl
        if dl.status == Status.PAUSED:
            dl.resume()
        elif dl.status == Status.DOWNLOADING:
            dl.pause()

    def _on_stop(self, btn):
        self._dl.cancel()

    def _on_open_folder(self, btn):
        path = self._dl.final_path or self._dl.dest_path
        folder = os.path.dirname(path) if os.path.isfile(path) else path
        _xdg_open(folder)

    def _on_open_file(self, btn):
        if self._dl.final_path and os.path.isfile(self._dl.final_path):
            _xdg_open(self._dl.final_path)

    def _on_retry_clicked(self, btn):
        if self._on_retry:
            self._on_retry(self._dl)

    def _on_remove_clicked(self, btn):
        self._on_remove(self._dl)

    # ── refresh (called from main thread)

    def refresh(self):
        dl = self._dl
        st = dl.status

        self._name_lbl.set_text(dl.filename)
        self._size_lbl.set_text(_fmt_size(dl.total_size))

        pct = dl.progress * 100
        self._progress.set_fraction(dl.progress)
        self._progress.set_text(f"{pct:.1f}%")

        # status label
        if st == Status.ERROR:
            self._status_lbl.set_text(f"Error: {dl.error_msg}")
            self._status_lbl.add_css_class("error")
        else:
            self._status_lbl.remove_css_class("error")
            self._status_lbl.set_text(st.value)

        # speed / ETA / connections
        if st == Status.DOWNLOADING:
            self._speed_lbl.set_text(_fmt_speed(dl.speed))
            eta = _fmt_eta(dl.eta)
            self._eta_lbl.set_text(f"ETA {eta}" if eta else "")
            conns = dl.connections
            self._conn_lbl.set_text(f"{conns} conn" if conns > 1 else "")
        else:
            self._speed_lbl.set_text("")
            self._eta_lbl.set_text("")
            self._conn_lbl.set_text("")

        # button states
        active = st in (Status.DOWNLOADING, Status.PAUSED)
        failed = st in (Status.ERROR, Status.CANCELLED)
        self._pause_btn.set_visible(active)
        self._stop_btn.set_visible(active)
        self._pause_btn.set_label(
            "▶ Resume" if st == Status.PAUSED else "⏸ Pause"
        )
        self._file_btn.set_sensitive(
            st == Status.COMPLETE
            and bool(dl.final_path)
            and os.path.isfile(dl.final_path or "")
        )
        self._retry_btn.set_visible(failed and self._on_retry is not None and dl._proc is None)
        self._remove_btn.set_visible(not active)


# ══════════════════════════════════════════════════════════ main window

class NexLoadWindow(Gtk.ApplicationWindow):
    def __init__(self, app, manager: DownloadManager, ws_server):
        super().__init__(application=app, title="NexLoad")
        self.set_default_size(760, 520)

        self._manager = manager
        self._ws = ws_server
        self._rows: dict = {}   # id(dl) → DownloadRow

        manager.connect_changed(self._on_downloads_changed)
        self._build_ui()

    # ─────────────────────────────────────────── build

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(outer)

        outer.append(self._build_headerbar())
        outer.append(self._build_toolbar())

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        outer.append(scroll)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.set_show_separators(True)
        self._list_box.add_css_class("boxed-list")
        self._list_box.set_margin_top(8)
        self._list_box.set_margin_bottom(8)
        self._list_box.set_margin_start(8)
        self._list_box.set_margin_end(8)
        scroll.set_child(self._list_box)

        placeholder = Gtk.Label(
            label="No downloads yet.\nClick  + Add  or use the browser extension."
        )
        placeholder.add_css_class("dim-label")
        placeholder.set_justify(Gtk.Justification.CENTER)
        self._list_box.set_placeholder(placeholder)

        outer.append(self._build_statusbar())

    def _build_headerbar(self):
        hb = Gtk.HeaderBar()
        hb.set_show_title_buttons(True)

        logo = Gtk.Image.new_from_icon_name("emblem-downloads")
        logo.set_icon_size(Gtk.IconSize.LARGE)
        hb.pack_start(logo)

        add_btn = Gtk.Button(label="+ Add")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_clicked)
        hb.pack_end(add_btn)

        settings_btn = Gtk.Button(label="⚙")
        settings_btn.set_tooltip_text("Settings")
        settings_btn.connect("clicked", self._on_settings_clicked)
        hb.pack_end(settings_btn)

        return hb

    def _build_toolbar(self):
        bar = Gtk.Box(spacing=6)
        bar.set_margin_top(4); bar.set_margin_start(8)
        bar.set_margin_end(8); bar.set_margin_bottom(4)

        pause_btn = Gtk.Button(label="⏸ Pause All")
        pause_btn.connect("clicked", lambda _: self._manager.pause_all())
        bar.append(pause_btn)

        resume_btn = Gtk.Button(label="▶ Resume All")
        resume_btn.connect("clicked", lambda _: self._manager.resume_all())
        bar.append(resume_btn)

        clear_btn = Gtk.Button(label="✕ Clear Done")
        clear_btn.connect("clicked", self._on_clear_done)
        bar.append(clear_btn)

        tmp_btn = Gtk.Button(label="🗑 Clear Temp")
        tmp_btn.set_tooltip_text("Delete partial/temp files from stopped downloads")
        tmp_btn.connect("clicked", self._on_clear_temp)
        bar.append(tmp_btn)

        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self._ext_status = Gtk.Label(label="⬤  Extension: not connected")
        self._ext_status.add_css_class("dim-label")
        bar.append(self._ext_status)

        return bar

    def _build_statusbar(self):
        bar = Gtk.Box()
        bar.add_css_class("toolbar")
        bar.set_margin_start(8); bar.set_margin_end(8)
        bar.set_margin_top(4); bar.set_margin_bottom(4)

        self._statusbar_lbl = Gtk.Label(label="Ready", xalign=0)
        self._statusbar_lbl.set_hexpand(True)
        bar.append(self._statusbar_lbl)
        return bar

    # ─────────────────────────────────────────── callbacks

    def _on_add_clicked(self, btn):
        self._show_add_dialog()

    def _on_settings_clicked(self, btn):
        dialog = SettingsDialog(self)
        dialog.connect("response", self._on_settings_response)
        dialog.present()

    def _on_settings_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            _settings.save(dialog.get_values())
        dialog.destroy()

    def _show_add_dialog(self, prefill_url="", referrer=""):
        dialog = AddDownloadDialog(self, prefill_url)
        dialog.connect("response", self._on_add_response, referrer)
        dialog.present()

    def _on_add_response(self, dialog, response, referrer):
        if response == Gtk.ResponseType.OK:
            url = dialog.url
            if url:
                self._start_download_or_video(url, dialog.filename,
                                              dialog.dest, referrer)
        dialog.destroy()

    def _start_download_or_video(self, url, filename, dest, referrer=""):
        if _looks_like_video_site(url):
            self._fetch_formats_and_download(url, dest or DEFAULT_DOWNLOAD_DIR, referrer)
        else:
            self._manager.add(url, filename, dest or DEFAULT_DOWNLOAD_DIR,
                              referrer=referrer or None)

    def _download_stream_url(self, url, dest, referrer="", title=""):
        """Download a captured M3U8/MPD stream directly with yt-dlp best format."""
        if not title:
            try:
                path = urllib.parse.urlparse(url).path
                title = os.path.splitext(os.path.basename(path))[0] or "video"
            except Exception:
                title = "video"
        fmt = types.SimpleNamespace(format_id="best", ext="mp4", filesize=0)
        self._run_ytdlp_download(url, fmt, title, dest)

    def _fetch_formats_and_download(self, url, dest, referrer=""):
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
        dialog = FormatChooserDialog(self, title, formats)
        dialog.connect("response", self._on_format_response, url, title, formats, dest)
        dialog.present()

    def _on_format_response(self, dialog, response, url, title, formats, dest):
        if response == Gtk.ResponseType.OK:
            fmt = dialog.get_selected_format()
            if fmt:
                self._run_ytdlp_download(url, fmt, title, dest)
        dialog.destroy()

    def _run_ytdlp_download(self, url, fmt, title, dest):
        safe = "".join(c if c.isalnum() or c in " ._-()" else "_"
                       for c in title)[:80]
        dl = Download(url, dest, f"{safe}.{fmt.ext}")
        dl.on_progress = self._manager._on_download_progress
        dl.on_complete = self._manager._on_download_complete
        dl.status = Status.DOWNLOADING
        dl.total_size = fmt.filesize or 0

        with self._manager._lock:
            self._manager._downloads.append(dl)
        self._manager._notify()

        def _worker():
            try:
                def _prog(pct, speed_bps, eta_secs):
                    dl.downloaded = int(pct)
                    dl.total_size = 100
                    dl.speed = speed_bps
                    dl.eta = eta_secs
                    GLib.idle_add(self._manager._notify)

                def _on_proc(proc):
                    dl._proc = proc

                final = video_info.download_video(
                    url, fmt.format_id, dest,
                    on_progress=_prog,
                    on_proc=_on_proc,
                    title=title,
                )
                if not dl._cancel_flag:
                    dl.status = Status.COMPLETE
                    dl.downloaded = 100
                    dl.total_size = 100
                    dl.eta = 0
                    dl.speed = 0
                    dl.final_path = final
            except Exception as e:
                if not dl._cancel_flag:
                    dl.status = Status.ERROR
                    dl.error_msg = str(e)
            GLib.idle_add(self._manager._notify)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_clear_done(self, btn):
        done = [d for d in self._manager.downloads
                if d.status in (Status.COMPLETE, Status.ERROR, Status.CANCELLED)]
        for d in done:
            self._manager.remove(d)

    def _on_clear_temp(self, btn):
        from .downloader import _TMP_DIR
        active = {d.filename for d in self._manager.downloads
                  if d.status in (Status.DOWNLOADING, Status.PAUSED)}
        try:
            deleted = 0
            for name in os.listdir(_TMP_DIR):
                base = name.split(".part")[0]
                if base not in active:
                    try:
                        os.remove(os.path.join(_TMP_DIR, name))
                        deleted += 1
                    except Exception:
                        pass
            self._statusbar_lbl.set_text(
                f"Deleted {deleted} temp file(s) from {_TMP_DIR}"
            )
        except FileNotFoundError:
            self._statusbar_lbl.set_text("Temp folder is already empty.")

    def _show_error(self, msg):
        dialog = Gtk.AlertDialog()
        dialog.set_message("Error")
        dialog.set_detail(msg)
        dialog.show(self)

    # ─────────────────────────────────────────── list refresh

    def _on_downloads_changed(self):
        downloads = self._manager.downloads
        dl_ids = {id(d) for d in downloads}

        for key in list(self._rows):
            if key not in dl_ids:
                row_widget = self._rows.pop(key)
                parent = row_widget.get_parent()
                self._list_box.remove(parent if parent else row_widget)

        for dl in downloads:
            key = id(dl)
            if key in self._rows:
                self._rows[key].refresh()
            else:
                row = DownloadRow(dl, self._manager.remove, self._manager.retry)
                self._rows[key] = row
                self._list_box.append(row)

        active = [d for d in downloads if d.status == Status.DOWNLOADING]
        total_speed = sum(d.speed for d in active)
        if active:
            txt = f"{len(active)} downloading  ·  {_fmt_speed(total_speed)}"
        elif downloads:
            txt = f"{len(downloads)} item(s)"
        else:
            txt = "Ready"
        self._statusbar_lbl.set_text(txt)

    # ─────────────────────────────────────────── extension callbacks

    def handle_extension_message(self, client, msg):
        action = msg.get("action")
        url = msg.get("url", "")
        referrer = msg.get("referrer", "")
        filename = msg.get("filename", "")
        title = msg.get("title", "")

        if action == "download":
            GLib.idle_add(
                self._start_download_or_video, url, filename, None, referrer
            )
        elif action == "download_video":
            if _is_direct_stream(url):
                GLib.idle_add(
                    self._download_stream_url, url,
                    DEFAULT_DOWNLOAD_DIR, referrer, title
                )
            else:
                GLib.idle_add(
                    self._fetch_formats_and_download, url,
                    DEFAULT_DOWNLOAD_DIR, referrer
                )

    def notify_extension_connected(self):
        GLib.idle_add(self._ext_status.set_label, "⬤  Extension: connected")

    def notify_extension_disconnected(self):
        GLib.idle_add(self._ext_status.set_label, "⬤  Extension: not connected")


_STREAM_RE = re.compile(r'\.(m3u8|mpd)(\?|#|$)', re.IGNORECASE)


def _is_direct_stream(url):
    return bool(_STREAM_RE.search(url))


def _looks_like_video_site(url):
    if _is_direct_stream(url):
        return True
    video_hosts = (
        "youtube.com", "youtu.be", "vimeo.com",
        "dailymotion.com", "twitch.tv", "tiktok.com",
        "twitter.com", "x.com", "facebook.com",
        "instagram.com", "reddit.com",
    )
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return any(host.endswith(h) for h in video_hosts)
    except Exception:
        return False
