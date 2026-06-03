"""Rocket League window focus and geometry helpers (Windows only).

All functions return graceful None / False on non-Windows
platforms or when Rocket League is not running.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from ctypes import windll


# EnumWindows callback type: BOOL CALLBACK EnumWindowsProc(HWND, LPARAM)
_EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def _rl_hwnd(window_title: str = "Rocket League") -> int | None:
    """Find Rocket League's window handle, or None."""
    if sys.platform != "win32":
        return None

    # Exact match first
    hwnd = windll.user32.FindWindowW(None, window_title)
    if hwnd:
        return hwnd

    # Partial match fallback
    results: list[int] = []

    @_EnumWindowsProc
    def enum_cb(h: int, _lparam: int) -> bool:
        name = _get_window_text(h)
        if name and window_title.lower() in name.lower():
            if windll.user32.IsWindowVisible(h):
                results.append(h)
        return True

    try:
        windll.user32.EnumWindows(enum_cb, 0)
    except Exception:
        pass

    return results[0] if results else None


def _get_window_text(hwnd: int) -> str:
    length = windll.user32.GetWindowTextLengthW(hwnd) + 1
    buf = (wintypes.WCHAR * length)()
    windll.user32.GetWindowTextW(hwnd, buf, length)
    return buf.value


def is_rocket_league_focused(window_title: str = "Rocket League") -> bool:
    """Check if the Rocket League window currently has keyboard focus."""
    if sys.platform != "win32":
        return False
    hwnd = windll.user32.GetForegroundWindow()
    if not hwnd:
        return False
    title = _get_window_text(hwnd)
    return window_title.lower() in title.lower()


def get_rocket_league_window_rect(
    window_title: str = "Rocket League"
) -> tuple[int, int, int, int] | None:
    """Get the (left, top, right, bottom) pixel rect of the RL window."""
    hwnd = _rl_hwnd(window_title)
    if hwnd is None:
        return None
    rect = wintypes.RECT()
    if windll.user32.GetWindowRect(hwnd, rect):
        return (rect.left, rect.top, rect.right, rect.bottom)
    return None


def is_cursor_inside_rl_window(
    window_title: str = "Rocket League"
) -> bool:
    """Check whether the mouse cursor is inside the RL window."""
    rect = get_rocket_league_window_rect(window_title)
    if rect is None:
        return False
    left, top, right, bottom = rect
    pt = wintypes.POINT()
    windll.user32.GetCursorPos(pt)
    return left <= pt.x <= right and top <= pt.y <= bottom
