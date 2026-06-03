"""Application-level helpers for overlay apps.

Provides:
- QtApp: a QApplication wrapper that handles Ctrl+C gracefully
  (uses SetConsoleCtrlHandler on Windows, which works even while
  Qt's event loop is blocking).
- snap_to_rl_monitor: position a window on the same monitor as RL.
- is_rl_active: check whether RL is focused (for hotkey-driven overlays).
"""

from __future__ import annotations

import ctypes
import sys


# Ctrl+C handling

class QtApp:
    """A QApplication wrapper with working Ctrl+C on Windows.

    Qt's event loop blocks SIGINT.  This class uses
    SetConsoleCtrlHandler (Windows) which fires before the process
    is killed, letting us call QApplication.quit() cleanly.

    Usage::

        from nixwrap.gui import QtApp, create_overlay

        app = QtApp([])
        win = create_overlay(600, 200)
        win.show()
        app.run()          # Ctrl+C now closes cleanly
    """

    def __init__(self, argv: list[str] | None = None) -> None:
        from PySide6.QtWidgets import QApplication

        if argv is None:
            argv = sys.argv

        self._app = QApplication(argv)

        # Windows: SetConsoleCtrlHandler (the only way that works)
        if sys.platform == "win32":
            self._install_windows_handler()

    def _install_windows_handler(self) -> None:
        """Register a console control handler that calls app.quit().

        SetConsoleCtrlHandler callback runs in a separate thread
        spawned by the OS.  We can't call Qt functions from that thread
        directly, so we flag a variable and poll it with a QTimer.
        """
        from PySide6.QtCore import QTimer

        self._ctrl_c_hit = False

        # The OS-level handler, must be kept alive (assigned to self)
        _HANDLER_TYPE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)

        @_HANDLER_TYPE
        def _handler(ctrl_type: int) -> bool:
            if ctrl_type == 0:  # CTRL_C_EVENT
                self._ctrl_c_hit = True
                return True     # handled → don't kill process
            return False

        self._console_handler = _handler  # prevent GC
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_handler, True)

        # Poll the flag from the Qt thread
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._check_ctrl_c)
        self._poll_timer.start(100)  # 10x per second, responsive

    def _check_ctrl_c(self) -> None:
        if self._ctrl_c_hit:
            self._app.quit()

    @property
    def app(self):
        """The underlying QApplication."""
        return self._app

    def run(self) -> int:
        """Start the Qt event loop.  Returns the exit code."""
        return self._app.exec()


# Rocket League monitor detection

def get_rl_monitor() -> int | None:
    """Return the index of the monitor Rocket League is on.

    Returns None if RL is not running or the window can't be found.
    """
    try:
        from nixwrap.process import get_rocket_league_window_rect
    except ImportError:
        return None

    rect = get_rocket_league_window_rect()
    if rect is None:
        return None

    left, top, _, _ = rect
    center_x = left + 100
    center_y = top + 100

    from nixwrap.gui._geometry import get_all_screens
    screens = get_all_screens()
    for i, s in enumerate(screens):
        if s.x <= center_x <= s.x + s.width and s.y <= center_y <= s.y + s.height:
            return i
    return 0  # fallback: primary


def snap_to_rl_monitor(window) -> None:
    """Reposition *window* to the same monitor Rocket League is on.

    If RL can't be found, falls back to the primary screen centred.
    """
    rl_monitor = get_rl_monitor()
    if rl_monitor is not None and rl_monitor >= 0:
        window.center_on_screen(rl_monitor)
    else:
        window.center_on_screen(0)


# Overlay visibility helpers

def is_rl_active(check_focus: bool = True,
                 check_cursor: bool = False) -> bool:
    """Check whether the overlay should be visible.

    By default only checks whether RL has keyboard focus.  Pass
    check_cursor=True to additionally require the mouse cursor to
    be inside the RL window.
    """
    try:
        from nixwrap.process import (
            is_rocket_league_focused, is_cursor_inside_rl_window,
        )
    except ImportError:
        return True  # can't check → always show

    if not is_rocket_league_focused():
        return False
    if check_cursor and not is_cursor_inside_rl_window():
        return False
    return True
