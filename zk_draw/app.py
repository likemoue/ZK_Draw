"""Application bootstrap."""

from __future__ import annotations

import signal
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import config, icons
from .controller import Controller
from .styles import stylesheet


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    app = QApplication(argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationDisplayName(config.APP_NAME)
    app.setDesktopFileName("zk-draw")
    app.setWindowIcon(QIcon(icons.app_icon(256)))
    app.setQuitOnLastWindowClosed(False)   # keep running in the tray
    app.setStyleSheet(stylesheet())

    # allow Ctrl+C in a terminal to quit cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    controller = Controller(app)
    # keep a reference so it is not garbage-collected
    app._zk_controller = controller  # type: ignore[attr-defined]

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
