# NexLoad

A fast, open-source Linux download manager with browser integration — inspired by Internet Download Manager.

## Features

- **Browser extension** (Chrome/Edge/Firefox) with:
  - Floating **"⬇ Download with NexLoad"** button that appears above every video on any website
  - Right-click context menu: **"Download link with NexLoad"** / **"Download video with NexLoad"**
  - Auto-detects video URLs on YouTube, Vimeo, Twitter/X, TikTok, Facebook, and any site with `<video>` tags
- **Video format selection dialog** — choose resolution (1080p, 720p, 360p…) and codec before downloading
- **Parallel multi-connection downloads** — splits files into chunks for maximum speed
- **Resume support** — interrupted downloads pick up where they left off
- **GTK4 native UI** — clean, modern Linux interface
- **yt-dlp integration** — auto-downloads the yt-dlp binary on first video download if not installed

---

## Requirements

| Requirement | Notes |
|---|---|
| Python ≥ 3.10 | Standard library only (no pip dependencies) |
| GTK 4 + PyGObject | Usually pre-installed on GNOME desktops |
| yt-dlp | Auto-downloaded on first use; or `sudo apt install yt-dlp` |
| Chrome/Edge/Firefox | For browser extension |

---

## Installation

```bash
git clone https://github.com/msh2050/nexload.git
cd nexload
./nexload.py
```

Or run as a module:

```bash
python3 -m nexload
```

---

## Browser Extension Setup

### Chrome / Edge

1. Open `chrome://extensions` (or `edge://extensions`)
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder inside this repo

### Firefox

1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select `extension/manifest.json`

> **Permanent Firefox install:** Pack the extension with `web-ext build` and install the `.xpi`

---

## How It Works

```
Browser tab                  Extension              NexLoad App
──────────────────────       ──────────────────     ───────────────────────
<video> element detected  →  content.js overlay  →  WebSocket (port 9119)
User clicks button        →  background.js       →  Format chooser dialog
                                                  →  yt-dlp subprocess
                                                  →  Download engine
Right-click link          →  context menu        →  Direct HTTP download
```

### Architecture

| File | Role |
|---|---|
| `nexload/app.py` | GTK4 Application, lifecycle |
| `nexload/window.py` | Main window, Add dialog, Format chooser |
| `nexload/download_manager.py` | Queue, concurrency (max 3 parallel) |
| `nexload/downloader.py` | Multi-threaded HTTP downloader with resume |
| `nexload/video_info.py` | yt-dlp subprocess wrapper, format parsing |
| `nexload/ws_server.py` | Pure-stdlib WebSocket server (RFC 6455) |
| `extension/content.js` | Video detection, floating button, DOM injection |
| `extension/background.js` | WebSocket client, context menus, message routing |

---

## Configuration

Default download directory: `~/Downloads`  
WebSocket port: `9119`  
Max parallel downloads: `3`  
Parallel connections per file: `8`

These constants are in `nexload/__init__.py`, `nexload/download_manager.py`, and `nexload/downloader.py`.

---

## License

MIT © 2026
