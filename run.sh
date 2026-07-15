#!/usr/bin/env bash
# Launch ZK_Draw. Forces the X11/XWayland Qt backend, which is required for a
# reliable frameless, always-on-top, click-through full-screen overlay.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use the X11 (xcb) platform even on a Wayland session (runs via XWayland).
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
# Quiet Qt scaling warnings; the app is DPI-aware already.
export QT_ENABLE_HIGHDPI_SCALING="${QT_ENABLE_HIGHDPI_SCALING:-1}"

PY="$HERE/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
    PY="$(command -v python3 || command -v python)"
fi

exec "$PY" "$HERE/main.py" "$@"
