#!/usr/bin/env bash
# One-shot installer for ZK_Draw on Ubuntu 24.04.
#
#   chmod +x install.sh && ./install.sh
#
# It installs the system libraries the Qt xcb backend needs, creates an
# isolated Python virtual-environment, installs PySide6 into it, and adds a
# launcher to the applications menu.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> [1/4] Installing system dependencies (sudo password may be asked)"
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-util1 \
    libegl1 libgl1 libglib2.0-0 libdbus-1-3

echo "==> [2/4] Creating virtual environment (.venv)"
python3 -m venv "$HERE/.venv"
"$HERE/.venv/bin/pip" install --upgrade pip wheel
"$HERE/.venv/bin/pip" install -r "$HERE/requirements.txt"

echo "==> [3/4] Installing launcher scripts"
chmod +x "$HERE/run.sh"

echo "==> [4/4] Installing desktop entry"
# Install the menu entry for the REAL user even when the script is run with
# sudo (needed when ZK_Draw lives under /opt). Otherwise the .desktop file
# would land in root's home and never show in the user's app menu.
if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
else
    REAL_USER="$(id -un)"
    REAL_HOME="$HOME"
fi

APPDIR="$REAL_HOME/.local/share/applications"
mkdir -p "$APPDIR"
# The .desktop uses an ABSOLUTE icon path ($HERE/assets), so no icon-theme
# copy is required and it works no matter where ZK_Draw is installed.
sed "s|@HERE@|$HERE|g" "$HERE/zk-draw.desktop.in" > "$APPDIR/zk-draw.desktop"
chmod +x "$APPDIR/zk-draw.desktop" 2>/dev/null || true
if [[ "$REAL_USER" != "$(id -un)" ]]; then
    chown "$REAL_USER:" "$APPDIR/zk-draw.desktop" 2>/dev/null || true
fi
update-desktop-database "$APPDIR" 2>/dev/null || true

echo "==> [5/5] Creating Desktop shortcut"
DESKTOP_DIR="$(sudo -u "$REAL_USER" xdg-user-dir DESKTOP 2>/dev/null || echo "$REAL_HOME/Desktop")"
if [ -d "$DESKTOP_DIR" ]; then
    cp "$APPDIR/zk-draw.desktop" "$DESKTOP_DIR/"
    chmod +x "$DESKTOP_DIR/zk-draw.desktop"
    if [[ "$REAL_USER" != "$(id -un)" ]]; then
        chown "$REAL_USER:" "$DESKTOP_DIR/zk-draw.desktop" 2>/dev/null || true
    fi
    # Trust the shortcut (important for Cinnamon/GNOME on Linux Mint)
    if command -v gio >/dev/null 2>&1; then
        sudo -u "$REAL_USER" gio set "$DESKTOP_DIR/zk-draw.desktop" metadata::trusted true 2>/dev/null || true
    fi
fi

echo
echo "============================================================"
echo " ZK_Draw installed."
echo "   * From a terminal:   $HERE/run.sh"
echo "   * From the app menu: search for 'ZK_Draw'"
echo "============================================================"
