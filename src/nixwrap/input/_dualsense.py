"""PS5 DualSense controller. Needs dualsense-controller + bundled hidapi.dll.

PS4 DS4 not supported - use DS4Windows to emulate XInput instead.
"""

from __future__ import annotations

import atexit
import ctypes
import logging
import os
import signal
import sys
import threading
import warnings
from typing import Any

_log = logging.getLogger(__name__)

ps_controller: Any | None = None

DS4_BUTTONS = [
    "btn_cross", "btn_circle", "btn_square", "btn_triangle",
    "btn_l1", "btn_r1", "btn_l2", "btn_r2",
    "btn_l3", "btn_r3", "btn_options", "btn_create",
    "btn_ps", "btn_touchpad", "btn_mute",
    "btn_up", "btn_down", "btn_left", "btn_right",
]

DS4_BUTTON_DISPLAY: dict[str, str] = {
    "btn_cross":    "Cross",
    "btn_circle":   "Circle",
    "btn_square":   "Square",
    "btn_triangle": "Triangle",
    "btn_l1": "L1",              "btn_r1": "R1",
    "btn_l2": "L2",              "btn_r2": "R2",
    "btn_l3": "L3",              "btn_r3": "R3",
    "btn_options": "Options",    "btn_create": "Create",
    "btn_ps": "PS",              "btn_touchpad": "Touchpad",
    "btn_mute": "Mute",
    "btn_up": "D-Pad Up",        "btn_down": "D-Pad Down",
    "btn_left": "D-Pad Left",    "btn_right": "D-Pad Right",
}

_ps_pressed: set[str] = set()
_ps_controller_instance: Any | None = None


# hidapi.dll resolution

def _resource_path(relative_path: str) -> str:
    """Get absolute path to a bundled resource.

    Works for dev (pip install -e) and for wheel installs.
    """
    try:
        # PyInstaller / frozen
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        # Normal Python: the directory this file lives in
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def _ensure_hidapi_on_path() -> bool:
    """Add the bundled hidapi.dll directory to the DLL search path.

    Returns True if hidapi.dll was found (bundled or system).
    """
    bundled = _resource_path("hidapi.dll")
    if os.path.exists(bundled):
        # Add the input/ directory to PATH so ctypes can find it
        dll_dir = os.path.dirname(bundled)
        if dll_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(dll_dir)  # Python 3.8+
        except AttributeError:
            pass
        return True

    # Check system install
    for name in ("hidapi.dll", "hidapi", "libhidapi"):
        try:
            ctypes.cdll.LoadLibrary(name)
            return True
        except OSError:
            continue
    return False


# Public API

def is_dualsense_connected() -> bool:
    """Check if at least one DualSense controller is physically connected."""
    try:
        from dualsense_controller import DualSenseController
        return len(DualSenseController.enumerate_devices()) >= 1
    except ImportError:
        return False


def setup_dualsense() -> Any | None:
    """Initialise and activate a DualSense controller.

    The bundled hidapi.dll is automatically loaded, no manual setup.

    Returns
    DualSenseController or None
        None if no controller is connected, dualsense-controller
        is not installed, or hidapi.dll could not be loaded.
    """
    global ps_controller, _ps_controller_instance

    if not _ensure_hidapi_on_path():
        _log.warning(
            "hidapi.dll not found, DualSense requires the HID API library. "
            "The bundled dll should be at: %s",
            _resource_path("hidapi.dll"),
        )
        return None

    if not is_dualsense_connected():
        return None

    try:
        from dualsense_controller import DualSenseController

        controller = DualSenseController()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            controller.activate()

        for btn_name in DS4_BUTTONS:
            getattr(controller, btn_name).on_change(_make_handler(btn_name))

        controller.on_error(lambda: _disconnect_handler(controller))

        ps_controller = controller
        _ps_controller_instance = controller
        return controller
    except ImportError:
        _log.warning("dualsense-controller not installed. pip install nixwrap[input]")
        return None


def get_dualsense_inputs() -> list[str]:
    """Return the list of currently held DualSense button names."""
    return sorted(_ps_pressed)


# Monitor thread (auto-reconnect)

def start_dualsense_monitor() -> threading.Thread:
    """Start a background thread that reconnects the DualSense on disconnect.

    Mirrors the _ps_monitor_thread from InGameRank.
    """
    def _monitor() -> None:
        global ps_controller
        while True:
            import time
            time.sleep(1)
            if ps_controller is None:
                result = setup_dualsense()
                if result:
                    _log.info("DualSense reconnected")

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()
    return t


# Internals

def _make_handler(name: str):
    def handler(value: bool) -> None:
        if value:
            _ps_pressed.add(name)
        else:
            _ps_pressed.discard(name)
    return handler


def _disconnect_handler(controller: Any) -> None:
    global ps_controller, _ps_pressed

    def _reconnect_loop() -> None:
        global ps_controller
        _ps_pressed.clear()
        try:
            controller.deactivate()
        except Exception:
            pass
        ps_controller = None
        _log.info("DualSense disconnected")

    threading.Thread(target=_reconnect_loop, daemon=True).start()


def _cleanup() -> None:
    """Deactivate the controller on process exit. Registered via atexit."""
    global ps_controller
    if ps_controller:
        try:
            t = threading.Thread(target=ps_controller.deactivate, daemon=True)
            t.start()
            t.join(timeout=2.0)
        except Exception:
            pass
        ps_controller = None


def _sigint_handler(sig: int, frame: Any) -> None:
    _cleanup()
    os._exit(0)


atexit.register(_cleanup)
signal.signal(signal.SIGINT, _sigint_handler)
