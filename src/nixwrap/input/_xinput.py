"""XInput (Xbox controller) state detection via ctypes.

Ported from InGameRank controllers.py.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes


# XInput structures

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons",      wintypes.WORD),
        ("bLeftTrigger",  wintypes.BYTE),
        ("bRightTrigger", wintypes.BYTE),
        ("sThumbLX",      wintypes.SHORT),
        ("sThumbLY",      wintypes.SHORT),
        ("sThumbRX",      wintypes.SHORT),
        ("sThumbRY",      wintypes.SHORT),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad",        XINPUT_GAMEPAD),
    ]


# Button masks

XINPUT_DPAD_UP    = 0x0001
XINPUT_DPAD_DOWN  = 0x0002
XINPUT_DPAD_LEFT  = 0x0004
XINPUT_DPAD_RIGHT = 0x0008
XINPUT_START      = 0x0010
XINPUT_SELECT     = 0x0020   # "Back" / "View"
XINPUT_LS = 0x0040  # Left Stick click
XINPUT_RS = 0x0080  # Right Stick click
XINPUT_LB = 0x0100  # Left Bumper
XINPUT_RB = 0x0200  # Right Bumper
XINPUT_A  = 0x1000
XINPUT_B  = 0x2000
XINPUT_X  = 0x4000
XINPUT_Y  = 0x8000

XINPUT_BUTTON_DISPLAY: dict[int, str] = {
    XINPUT_DPAD_UP:    "D-Pad Up",
    XINPUT_DPAD_DOWN:  "D-Pad Down",
    XINPUT_DPAD_LEFT:  "D-Pad Left",
    XINPUT_DPAD_RIGHT: "D-Pad Right",
    XINPUT_START:      "Start",
    XINPUT_SELECT:     "Select",
    XINPUT_LS:         "L-Stick",
    XINPUT_RS:         "R-Stick",
    XINPUT_LB:         "LB",
    XINPUT_RB:         "RB",
    XINPUT_A:          "A",
    XINPUT_B:          "B",
    XINPUT_X:          "X",
    XINPUT_Y:          "Y",
}


# DLL loading

_xinput_dll = None
for _dll_name in ("xinput1_4", "xinput1_3"):
    try:
        _xinput_dll = ctypes.windll.LoadLibrary(_dll_name)
        break
    except OSError:
        continue


# Public API

class XInputState:
    """Typed wrapper around the raw XInput state."""

    __slots__ = ("packet_number", "buttons", "left_trigger", "right_trigger",
                 "thumb_lx", "thumb_ly", "thumb_rx", "thumb_ry")

    def __init__(self, raw: XINPUT_STATE) -> None:
        g = raw.Gamepad
        self.packet_number = raw.dwPacketNumber
        self.buttons = g.wButtons
        self.left_trigger = g.bLeftTrigger
        self.right_trigger = g.bRightTrigger
        self.thumb_lx = g.sThumbLX
        self.thumb_ly = g.sThumbLY
        self.thumb_rx = g.sThumbRX
        self.thumb_ry = g.sThumbRY

    def is_pressed(self, button_mask: int) -> bool:
        return (self.buttons & button_mask) == button_mask

    def __repr__(self) -> str:
        return f"XInputState(buttons=0x{self.buttons:04X}, lt={self.left_trigger}, rt={self.right_trigger})"


def get_xinput_state(user_index: int = 0) -> XInputState | None:
    """Read the current XInput state for controller user_index (0 to 3).

    Returns None if XInput is not available or the controller is
    not connected.
    """
    if _xinput_dll is None:
        return None
    state = XINPUT_STATE()
    if _xinput_dll.XInputGetState(user_index, ctypes.byref(state)) == 0:
        return XInputState(state)
    return None
