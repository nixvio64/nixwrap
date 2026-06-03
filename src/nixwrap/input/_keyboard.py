"""Keyboard hotkey detection.

Uses the keyboard library (Windows only).

Ported from InGameRank config.py / controllers.py.
"""

from __future__ import annotations


def is_key_pressed(key: str) -> bool:
    """Check if a keyboard key is currently held down.

    Requires keyboard library: pip install keyboard.

    Parameters
    key:
        Key name as recognised by the keyboard library
        (e.g. "tab", "ctrl", "shift").

    Returns
    bool
        True if the key is currently pressed, False otherwise
        (or if keyboard is not available).
    """
    try:
        import keyboard
        return bool(keyboard.is_pressed(key))
    except ImportError:
        return False


def detect_hotkey(timeout: float | None = None) -> dict | None:
    """Wait for the user to press a keyboard key and return the binding info.

    This function blocks until timeout seconds pass or a key is pressed.
    Pass timeout=None to wait indefinitely.

    Returns a dict compatible with the config format::

        {"hotkey": "tab", "is_controller": False}

    Returns None if keyboard is not available or timeout expires.
    """
    try:
        import keyboard
        import time

        result: dict | None = None

        def _on_press(e):
            nonlocal result
            if result is None:
                result = {
                    "hotkey": e.name,
                    "is_controller": False,
                    "controller_type": "",
                    "controller_button": 0,
                }

        keyboard.on_press(_on_press)

        start = time.time()
        while result is None:
            if timeout is not None and time.time() - start > timeout:
                break
            time.sleep(0.01)

        keyboard.unhook_all()
        return result
    except ImportError:
        return None
