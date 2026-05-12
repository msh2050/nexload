import os
import threading
import urllib.parse

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio, Pango

from .download_manager import DownloadManager, DEFAULT_DOWNLOAD_DIR
from .downloader import Status
from . import video_info


# ══════════════════════════════════════════════════════════ format chooser

class FormatChooserDialog(Gtk.Dialog):
    """Shows available video formats; user picks one."""

    def __init__(self, parent, title, formats):
        super().__init__(title="Select Format", transient_for=parent, modal=True)
        self.set_default_size(480, 400)
        self.selected_format = None

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_Download", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
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
            if f.has_video:       # show only video-bearing formats
                self._formats.append(f)
                self._store.append(f.label)

        self._list_view_setup(scroll)

    def _list_view_setup(self, scroll):
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
        label.set_margin_start(8)
        label.set_margin_end(8)
        label.set_margin_top(6)
        label.set_margin_bottom(6)
        item.set_child(label)

    @staticmethod
    def _bind_item(factory, item):
        label = item.get_child()
        string_obj = item.get_item()
        label.set_text(string_obj.get_string())

    def get_selected_format(self):
        idx = self._selection.get_selected()
        if idx < len(self._formats):
            return self._formats[idx]
        return None


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
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_spacing(10)

        grid = Gtk.Grid(row_spacing=8, column_spacing=10)
        box.append(grid)

        # URL
        grid.attach(Gtk.Label(label="URL:", xalign=1), 0, 0, 1, 1)
        self._url_entry = Gtk.Entry()
        self._url_entry.set_hexpand(True)
        self._url_entry.set_text(prefill_url)
        self._url_entry.set_activates_default(True)
        self._url_entry.set_placeholder_text("https://…")
        grid.attach(self._url_entry, 1, 0, 1, 1)

        # Save to
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

        # Filename (optional)
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


# ══════════════════════════════════════════════════════════ main window

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


class DownloadRow(Gtk.Box):
    """One row in the download list."""

    def __init__(self, dl):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(10)
        self.set_margin_end(10)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(top)

        self._name_lbl = Gtk.Label(label=dl.filename, xalign=0)
        self._name_lbl.set_hexpand(True)
        self._name_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self._name_lbl.add_css_class("heading")
        top.append(self._name_lbl)

        self._size_lbl = Gtk.Label(label="", xalign=1)
        self._size_lbl.add_css_class("dim-label")
        top.append(self._size_lbl)

        self._progress = Gtk.ProgressBar()
        self._progress.set_show_text(True)
        self.append(self._progress)

        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(bottom)

        self._status_lbl = Gtk.Label(label=dl.status.value, xalign=0)
        self._status_lbl.add_css_class("dim-label")
        self._status_lbl.set_hexpand(True)
        bottom.append(self._status_lbl)

        self._speed_lbl = Gtk.Label(label="", xalign=1)
        self._speed_lbl.add_css_class("dim-label")
        bottom.append(self._speed_lbl)

        self._dl = dl
        self.refresh()

    def refresh(self):
        dl = self._dl
        self._name_lbl.set_text(dl.filename)
        self._size_lbl.set_text(_fmt_size(dl.total_size))
        self._progress.set_fraction(dl.progress)
        pct = f"{dl.progress * 100:.1f}%"
        self._progress.set_text(pct)
        self._status_lbl.set_text(dl.status.value)
        self._speed_lbl.set_text(_fmt_speed(dl.speed))

        if dl.status == Status.ERROR:
            self._status_lbl.set_text(f"Error: {dl.error_msg}")
            self._status_lbl.add_css_class("error")


class NexLoadWindow(Gtk.ApplicationWindow):
    def __init__(self, app, manager: DownloadManager, ws_server):
        super().__init__(application=app, title="NexLoad")
        self.set_default_size(720, 480)

        self._manager = manager
        self._ws = ws_server
        self._rows: dict = {}   # dl → DownloadRow

        manager.connect_changed(self._on_downloads_changed)
        self._build_ui()

    # ─────────────────────────────────────────────── build

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(outer)

        outer.append(self._build_headerbar())
        outer.append(self._build_toolbar())

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        outer.append(scroll)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.set_show_separators(True)
        self._list_box.add_css_class("boxed-list")
        self._list_box.set_margin_top(8)
        self._list_box.set_margin_bottom(8)
        self._list_box.set_margin_start(8)
        self._list_box.set_margin_end(8)
        scroll.set_child(self._list_box)

        self._placeholder = Gtk.Label(
            label="No downloads yet.\nClick  + Add  or use the browser extension."
        )
        self._placeholder.add_css_class("dim-label")
        self._placeholder.set_justify(Gtk.Justification.CENTER)
        self._list_box.set_placeholder(self._placeholder)

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

        return hb

    def _build_toolbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.set_margin_top(4)
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_bottom(4)

        pause_btn = Gtk.Button(label="⏸ Pause All")
        pause_btn.connect("clicked", lambda _: self._manager.pause_all())
        bar.append(pause_btn)

        resume_btn = Gtk.Button(label="▶ Resume All")
        resume_btn.connect("clicked", lambda _: self._manager.resume_all())
        bar.append(resume_btn)

        clear_btn = Gtk.Button(label="✕ Clear Done")
        clear_btn.connect("clicked", self._on_clear_done)
        bar.append(clear_btn)

        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self._ext_status = Gtk.Label(label="⬤  Extension: not connected")
        self._ext_status.add_css_class("dim-label")
        bar.append(self._ext_status)

        return bar

    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bar.add_css_class("toolbar")
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_top(4)
        bar.set_margin_bottom(4)

        self._statusbar_lbl = Gtk.Label(label="Ready", xalign=0)
        self._statusbar_lbl.set_hexpand(True)
        bar.append(self._statusbar_lbl)
        return bar

    # ─────────────────────────────────────────────── callbacks

    def _on_add_clicked(self, btn):
        self._show_add_dialog()

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
        is_video = _looks_like_video_site(url)
        if is_video:
            self._fetch_formats_and_download(url, dest, referrer)
        else:
            self._manager.add(url, filename, dest, referrer=referrer or None)

    def _fetch_formats_and_download(self, url, dest, referrer=""):
        def _worker():
            try:
                title, formats = video_info.get_formats(url)
                GLib.idle_add(self._show_format_chooser, url, title,
                              formats, dest)
            except Exception as e:
                GLib.idle_add(self._show_error, f"Could not fetch formats:\n{e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _show_format_chooser(self, url, title, formats, dest):
        if not formats:
            self._show_error("No downloadable formats found.")
            return
        dialog = FormatChooserDialog(self, title, formats)
        dialog.connect("response", self._on_format_response,
                       url, title, formats, dest)
        dialog.present()

    def _on_format_response(self, dialog, response, url, title, formats, dest):
        if response == Gtk.ResponseType.OK:
            fmt = dialog.get_selected_format()
            if fmt:
                self._start_video_download(url, fmt, title, dest)
        dialog.destroy()

    def _start_video_download(self, url, fmt, title, dest):
        safe = "".join(c if c.isalnum() or c in " ._-()" else "_"
                       for c in title)[:80]
        filename = f"{safe}.{fmt.ext}"
        dl = self._manager.add(url, filename, dest)
        # replace sequential download with yt-dlp subprocess
        dl.cancel()
        self._manager.remove(dl)

        self._run_ytdlp_download(url, fmt.format_id, title, dest)

    def _run_ytdlp_download(self, url, fmt_id, title, dest):
        from .downloader import Download, Status
        safe = "".join(c if c.isalnum() or c in " ._-()" else "_"
                       for c in title)[:80]
        dl = Download(url, dest, f"{safe}.*")
        dl.on_progress = self._manager._on_download_progress
        dl.on_complete = self._manager._on_download_complete
        dl.status = Status.DOWNLOADING

        with self._manager._lock:
            self._manager._downloads.append(dl)
        self._manager._notify()

        def _worker():
            try:
                def _prog(pct, speed):
                    dl.downloaded = int(pct)
                    dl.total_size = 100
                    dl.speed = 0
                    GLib.idle_add(self._manager._notify)

                video_info.download_video(url, fmt_id, dest, on_progress=_prog)
                dl.status = Status.COMPLETE
                dl.downloaded = 100
                dl.total_size = 100
            except Exception as e:
                dl.status = Status.ERROR
                dl.error_msg = str(e)
            GLib.idle_add(self._manager._notify)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_clear_done(self, btn):
        done = [d for d in self._manager.downloads
                if d.status in (Status.COMPLETE, Status.ERROR,
                                Status.CANCELLED)]
        for d in done:
            self._manager.remove(d)

    def _show_error(self, msg):
        dialog = Gtk.AlertDialog()
        dialog.set_message("Error")
        dialog.set_detail(msg)
        dialog.show(self)

    # ─────────────────────────────────────────────── list refresh

    def _on_downloads_changed(self):
        downloads = self._manager.downloads
        dl_set = set(id(d) for d in downloads)

        # remove stale rows
        for dl_id in list(self._rows):
            if dl_id not in dl_set:
                row_widget = self._rows.pop(dl_id)
                self._list_box.remove(row_widget.get_parent() or row_widget)

        # add / refresh
        for dl in downloads:
            key = id(dl)
            if key in self._rows:
                self._rows[key].refresh()
            else:
                row = DownloadRow(dl)
                self._rows[key] = row
                self._list_box.append(row)

        # status bar
        active = [d for d in downloads if d.status == Status.DOWNLOADING]
        total_speed = sum(d.speed for d in active)
        if active:
            txt = f"{len(active)} downloading  ·  {_fmt_speed(total_speed)}"
        elif downloads:
            txt = f"{len(downloads)} item(s)"
        else:
            txt = "Ready"
        self._statusbar_lbl.set_text(txt)

    # ─────────────────────────────────────────────── extension callback

    def handle_extension_message(self, client, msg):
        """Called by WebSocket server on main thread (via GLib.idle_add)."""
        action = msg.get("action")
        url = msg.get("url", "")
        referrer = msg.get("referrer", "")
        filename = msg.get("filename", "")

        if action == "download":
            GLib.idle_add(
                self._start_download_or_video, url, filename, None, referrer
            )
        elif action == "download_video":
            GLib.idle_add(
                self._fetch_formats_and_download, url,
                DEFAULT_DOWNLOAD_DIR, referrer
            )

        self._ext_status.set_label("⬤  Extension: connected")

    def notify_extension_disconnected(self):
        GLib.idle_add(
            self._ext_status.set_label, "⬤  Extension: not connected"
        )


def _looks_like_video_site(url):
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
