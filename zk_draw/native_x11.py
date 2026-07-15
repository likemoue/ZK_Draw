"""Native X11 input pass-through via the XShape extension.

Toggling ``Qt.WindowTransparentForInput`` at runtime forces Qt to destroy and
re-create the native window (a full-screen re-map → visible flash on
X11/XWayland).  Instead we set/clear the window's *input shape* directly with
XShapeCombineRectangles, which changes only whether clicks fall through — the
window stays mapped, so there is no flash and no focus/stacking churn.

Everything is wrapped so that on a non-X11 platform (or if the libraries are
missing) the helpers simply report failure and the caller falls back to the
portable ``setWindowFlag`` path.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os

# XShape kinds / ops
_SHAPE_INPUT = 2
_SHAPE_SET = 0


class _State:
    loaded = False
    ok = False
    dpy = None
    xlib = None
    xext = None
    err_handler = None   # keep the CFUNCTYPE alive


def _noop_error_handler(display, event):  # pragma: no cover - X callback
    # SHAPE requests are replyless; a bad XID would otherwise reach Xlib's
    # default handler and print to stderr. Swallow it silently.
    return 0


def _load() -> bool:
    if _State.loaded:
        return _State.ok
    _State.loaded = True

    # Only meaningful under X11 / XWayland.
    if os.name != "posix":
        return False
    if not (os.environ.get("DISPLAY")):
        return False
    try:
        xname = ctypes.util.find_library("X11") or "libX11.so.6"
        extname = ctypes.util.find_library("Xext") or "libXext.so.6"
        xlib = ctypes.CDLL(xname)
        xext = ctypes.CDLL(extname)

        xlib.XOpenDisplay.restype = ctypes.c_void_p
        xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        xlib.XFlush.argtypes = [ctypes.c_void_p]

        xext.XShapeCombineRectangles.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
            ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ]
        xext.XShapeCombineMask.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int,
        ]

        dpy = xlib.XOpenDisplay(None)
        if not dpy:
            return False

        # Silence async X errors on this private connection (we never read it).
        try:
            handler_t = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                         ctypes.c_void_p)
            _State.err_handler = handler_t(_noop_error_handler)
            xlib.XSetErrorHandler.argtypes = [ctypes.c_void_p]
            xlib.XSetErrorHandler(
                ctypes.cast(_State.err_handler, ctypes.c_void_p))
        except Exception:
            pass

        _State.xlib = xlib
        _State.xext = xext
        _State.dpy = dpy
        _State.ok = True
    except Exception:
        _State.ok = False
    return _State.ok


def available() -> bool:
    return _load()


def set_input_passthrough(win_id: int, enabled: bool) -> bool:
    """Make the window click-through (*enabled*) or interactive again.

    Returns True if the native call succeeded, False if the caller should use
    the portable fallback instead.
    """
    if not _load() or not win_id:
        return False
    try:
        win = ctypes.c_ulong(int(win_id))
        if enabled:
            # An empty input region → every click falls through to the desktop.
            _State.xext.XShapeCombineRectangles(
                _State.dpy, win, _SHAPE_INPUT, 0, 0, None, 0, _SHAPE_SET, 0)
        else:
            # Reset the input region to the whole window → captures clicks.
            _State.xext.XShapeCombineMask(
                _State.dpy, win, _SHAPE_INPUT, 0, 0, ctypes.c_ulong(0),
                _SHAPE_SET)
        _State.xlib.XFlush(_State.dpy)
        return True
    except Exception:
        return False
