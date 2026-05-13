#!/usr/bin/env bash
# Nexload — development environment setup
# Run once: bash setup.sh
set -e

ARCH=$(uname -m)
OS=$(uname -s)

echo "==> Nexload setup ($OS $ARCH)"

# ── Rust ─────────────────────────────────────────────────────
if ! command -v cargo &>/dev/null; then
  echo "--> Installing Rust via rustup"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
else
  echo "--> Rust $(rustc --version) already installed"
fi

# ── Node (via nvm) ───────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo "--> Installing Node via nvm"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  nvm install --lts
else
  echo "--> Node $(node --version) already installed"
fi

# ── pnpm ─────────────────────────────────────────────────────
if ! command -v pnpm &>/dev/null; then
  echo "--> Installing pnpm"
  npm install -g pnpm
fi

# ── Tauri CLI ─────────────────────────────────────────────────
if ! command -v cargo-tauri &>/dev/null; then
  echo "--> Installing Tauri CLI"
  cargo install tauri-cli --version "^2"
fi

# ── Linux system libs ─────────────────────────────────────────
if [ "$OS" = "Linux" ]; then
  echo "--> Installing system dependencies"
  sudo apt-get update -q
  sudo apt-get install -y \
    libwebkit2gtk-4.1-dev \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libsoup-3.0-dev \
    aria2 yt-dlp
fi

# ── Sidecar binaries ──────────────────────────────────────────
TRIPLE="${ARCH}-unknown-linux-gnu"
if [ "$OS" = "Darwin" ]; then
  TRIPLE="${ARCH}-apple-darwin"
fi

echo "--> Setting up sidecar binaries for $TRIPLE"
mkdir -p src-tauri/binaries

# aria2c
ARIA2=$(which aria2c 2>/dev/null || true)
if [ -n "$ARIA2" ]; then
  cp "$ARIA2" "src-tauri/binaries/aria2c-${TRIPLE}"
  echo "    aria2c -> src-tauri/binaries/aria2c-${TRIPLE}"
fi

# yt-dlp
YTDLP=$(which yt-dlp 2>/dev/null || true)
if [ -z "$YTDLP" ]; then
  echo "--> Downloading yt-dlp"
  curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o "src-tauri/binaries/yt-dlp-${TRIPLE}"
  chmod +x "src-tauri/binaries/yt-dlp-${TRIPLE}"
else
  cp "$YTDLP" "src-tauri/binaries/yt-dlp-${TRIPLE}"
  echo "    yt-dlp -> src-tauri/binaries/yt-dlp-${TRIPLE}"
fi

# ── Placeholder icons (replace with real ones) ────────────────
echo "--> Creating placeholder app icons (replace with real icons)"
mkdir -p src-tauri/icons
if command -v convert &>/dev/null; then
  convert -size 128x128 xc:'#00d0af' src-tauri/icons/128x128.png 2>/dev/null || true
  convert -size 32x32   xc:'#00d0af' src-tauri/icons/32x32.png   2>/dev/null || true
  cp src-tauri/icons/128x128.png src-tauri/icons/"128x128@2x.png" 2>/dev/null || true
fi

echo ""
echo "✓ Setup complete."
echo ""
echo "Run the app:"
echo "  cargo tauri dev"
echo ""
echo "Build for distribution:"
echo "  cargo tauri build"
