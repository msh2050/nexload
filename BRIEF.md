# Nexload — Build Brief

## What we're building

A cross-platform desktop download manager. Modern, charming UI powered by a fast Rust backend that wraps yt-dlp and aria2c. Ships as a tiny native binary on Linux, macOS, and Windows.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Desktop shell | Tauri 2.x | ~5 MB binary, system WebView |
| Backend | Rust (src-tauri/) | Download engine, IPC, sniffer |
| UI | React 18 + Babel-in-browser | Keep JSX editable without a bundler |
| Video | yt-dlp sidecar | Best-in-class YouTube/Vimeo/etc extraction |
| Direct DL | aria2c sidecar | 16 connections, resume, JSON-RPC |
| DB | rusqlite (bundled SQLite) | Persistent queue + library |

## Repo layout

```
nexload/
├── BRIEF.md
├── setup.sh                    # one-time dev environment setup
├── design/                     # original UI concepts (do not modify)
├── app/                        # production UI (fork of design)
│   ├── index.html
│   ├── lib/api.js              # Tauri invoke wrapper
│   ├── primitives.jsx          # icons, Sparkline, RingProgress, Mascot
│   ├── screens-dashboard.jsx   # main download view (props-driven)
│   ├── screens-states.jsx      # empty, completed library, settings
│   ├── screens-widgets.jsx     # sniffer toast, drop zone
│   └── app.jsx                 # app root, routing, event subscriptions
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   ├── binaries/               # yt-dlp + aria2c sidecars (setup.sh fills these)
│   ├── icons/                  # app icons (replace placeholders)
│   ├── capabilities/
│   │   └── default.json
│   └── src/
│       ├── main.rs             # Tauri setup, state, background tasks
│       ├── commands.rs         # #[tauri::command] handlers
│       ├── settings.rs         # Settings struct + JSON persistence
│       ├── engine/
│       │   ├── direct.rs       # aria2c JSON-RPC client + subprocess
│       │   ├── video.rs        # yt-dlp metadata probe + download
│       │   └── queue.rs        # 500ms poll loop → download://update events
│       ├── store/
│       │   ├── mod.rs          # rusqlite layer
│       │   └── schema.sql
│       └── sniffer/
│           ├── mod.rs          # Unix socket listener → sniffer://detected event
│           └── browser_ext.rs  # native-messaging manifest installer
└── extension/
    ├── chrome/                 # Chrome/Chromium MV3 extension
    └── firefox/                # Firefox MV2 extension
```

## Getting started

```bash
# 1. Install toolchain + system libs + sidecar binaries
bash setup.sh

# 2. Run in dev mode (opens the app, hot-reloads CSS/JSX without a bundler)
cargo tauri dev

# 3. Build distributable
cargo tauri build
# → src-tauri/target/release/bundle/appimage/nexload_0.1.0_amd64.AppImage
# → src-tauri/target/release/bundle/deb/nexload_0.1.0_amd64.deb
```

## Tauri events (frontend ↔ backend)

| Event | Direction | Payload |
|---|---|---|
| `download://update` | backend → frontend | `DownloadUpdate[]` (id, value, speed, eta, state, got, total) |
| `global://stat` | backend → frontend | `{ totalSpeed, activeCount }` |
| `sniffer://detected` | backend → frontend | `{ url, title?, contentType }` |

## Tauri commands

```js
API.probeUrl(url)                // → ProbeResult { title, formats, isVideo, … }
API.addDownload(url, opts)       // → DownloadRecord
API.listActive()                 // → DownloadRecord[]
API.listCompleted(kind?, limit?) // → DownloadRecord[]
API.pauseDownload(id, gid)
API.resumeDownload(id, gid)
API.cancelDownload(id, gid)
API.revealInFolder(id)
API.getSettings()                // → Settings
API.updateSettings(patch)        // → Settings
API.storageStats()               // → StorageStats
```

## Browser extension

Load unpacked from `extension/chrome/` in Chrome, or `extension/firefox/` in Firefox.

The extension uses the `webRequest` API to detect video content types and forwards
URLs to Nexload via native messaging (`com.nexload.sniffer`). The app's sniffer
module listens on a Unix socket (`$XDG_RUNTIME_DIR/nexload.sock`) and emits
a `sniffer://detected` Tauri event that the frontend renders as a toast.

## Notes for contributors

- Don't introduce a JS bundler — Babel-in-browser keeps JSX editable by designers.
- Don't shell-out with `shell=true` — always pass argv arrays.
- All URLs are allowlisted to `http://https://` before reaching CLI tools.
- The `design/` folder is the reference; `app/` is the production fork.
