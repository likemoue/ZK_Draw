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


class _XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data", ctypes.c_long * 5),
    ]


def set_window_above(win_id: int, above: bool) -> bool:
    """Dynamically add or remove _NET_WM_STATE_ABOVE via EWMH ClientMessage.

    This changes the X11 window layer without destroying/recreating the Qt window.
    """
    if not _load() or not win_id:
        return False
    try:
        dpy = _State.dpy
        xlib = _State.xlib
        xlib.XDefaultRootWindow.restype = ctypes.c_ulong
        root = xlib.XDefaultRootWindow(dpy)

        wm_state = xlib.XInternAtom(dpy, b"_NET_WM_STATE", False)
        wm_above = xlib.XInternAtom(dpy, b"_NET_WM_STATE_ABOVE", False)

        action = 1 if above else 0  # 1 = _NET_WM_STATE_ADD, 0 = _NET_WM_STATE_REMOVE
        data = (ctypes.c_long * 5)(action, wm_above, 0, 1, 0)
        ev = _XClientMessageEvent(
            type=33,  # ClientMessage
            serial=0,
            send_event=1,
            display=dpy,
            window=ctypes.c_ulong(int(win_id)),
            message_type=wm_state,
            format=32,
            data=data,
        )
        mask = 0x00100000 | 0x00080000  # SubstructureRedirectMask | SubstructureNotifyMask
        xlib.XSendEvent.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.c_void_p
        ]
        xlib.XSendEvent(dpy, root, False, mask, ctypes.byref(ev))
        xlib.XFlush(dpy)
        return True
    except Exception:
        return False


def restack_above(above_win_ids: list[int], below_win_id: int) -> bool:
    """Explicitly restack above_win_ids directly above below_win_id in X11 stacking order.

    XRestackWindows restacks windows in the order given from top to bottom.
    """
    if not _load() or not below_win_id:
        return False
    try:
        all_ids = [int(w) for w in above_win_ids if w] + [int(below_win_id)]
        if len(all_ids) < 2:
            return False
        _State.xlib.XRestackWindows.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_int
        ]
        windows = (ctypes.c_ulong * len(all_ids))(*all_ids)
        _State.xlib.XRestackWindows(_State.dpy, windows, len(all_ids))
        _State.xlib.XFlush(_State.dpy)
        return True
    except Exception:
        return False


class XRectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_short),
        ("y", ctypes.c_short),
        ("width", ctypes.c_ushort),
        ("height", ctypes.c_ushort),
    ]


def update_canvas_input_shape(
    canvas_win_id: int,
    click_through: bool,
    exclude_rects: list[tuple[int, int, int, int]] | None = None,
) -> bool:
    """Configure CanvasWindow's input shape.

    If click_through is True:
        Input shape is empty (all clicks pass through to desktop).
    If click_through is False:
        Input shape covers the whole canvas, MINUS the exclude_rects (toolbar & panel).
        This guarantees the toolbar and panel can NEVER be drawn on and receive clicks directly!
    """
    if not _load() or not canvas_win_id:
        return False
    try:
        win = ctypes.c_ulong(int(canvas_win_id))
        if click_through:
            _State.xext.XShapeCombineRectangles(
                _State.dpy, win, _SHAPE_INPUT, 0, 0, None, 0, _SHAPE_SET, 0
            )
        else:
            # 1. Reset input region to entire window
            _State.xext.XShapeCombineMask(
                _State.dpy, win, _SHAPE_INPUT, 0, 0, ctypes.c_ulong(0), _SHAPE_SET
            )
            # 2. Subtract excluded chrome rects (toolbar, panel)
            if exclude_rects:
                xrects = (XRectangle * len(exclude_rects))()
                for i, (x, y, w, h) in enumerate(exclude_rects):
                    # Add 2px safety padding around chrome
                    xrects[i] = XRectangle(max(0, x - 2), max(0, y - 2), w + 4, h + 4)
                _SHAPE_SUBTRACT = 3
                _State.xext.XShapeCombineRectangles(
                    _State.dpy, win, _SHAPE_INPUT, 0, 0, xrects, len(exclude_rects), _SHAPE_SUBTRACT, 0
                )
        _State.xlib.XFlush(_State.dpy)
        return True
    except Exception:
        return False
