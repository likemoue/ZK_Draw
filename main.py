#!/usr/bin/env python3
"""ZK_Draw launcher.

Run with:  python3 main.py
(the run.sh wrapper also forces the X11/XWayland Qt backend on Wayland).
"""

import os
import sys

# On a Wayland session force the xcb (X11/XWayland) backend: a frameless,
# always-on-top, click-through full-screen overlay is only reliable there.
if sys.platform.startswith("linux") and not os.environ.get("QT_QPA_PLATFORM"):
    if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

from zk_draw.app import run  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run())
