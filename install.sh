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

echo "==> [4/4] Installing desktop entry + icon"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
cp -f "$HERE/assets/zk-draw-256.png" \
      "$HOME/.local/share/icons/hicolor/256x256/apps/zk-draw.png"
sed "s|@HERE@|$HERE|g" "$HERE/zk-draw.desktop.in" \
    > "$HOME/.local/share/applications/zk-draw.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo
echo "============================================================"
echo " ZK_Draw installed."
echo "   * From a terminal:   $HERE/run.sh"
echo "   * From the app menu: search for 'ZK_Draw'"
echo "============================================================"
