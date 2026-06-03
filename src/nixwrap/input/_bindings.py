"""Hotkey binding helpers.

Unified API for checking whether a hotkey (keyboard or controller)
is currently being held.

Ported from InGameRank controllers.py is_hotkey_pressed().
"""

from __future__ import annotations

from enum import Enum


class ControllerType(Enum):
    XINPUT = "xinput"
    DUALSENSE = "dualsense"
    KEYBOARD = "keyboard"


def get_button_display(controller_type: str, raw_button: int | str) -> str:
    """Convert a raw button identifier to a human-readable name.

    Parameters
    controller_type:
        "xinput" or "dualsense".
    raw_button:
        For XInput: the button mask (int, e.g. 0x1000 for A).
        For DualSense: the button name (str, e.g. "btn_cross").

    Returns
    str
        Human-readable button name (e.g. "A", "Cross").
    """
    if controller_type == "dualsense":
        from nixwrap.input._dualsense import DS4_BUTTONS, DS4_BUTTON_DISPLAY
        if isinstance(raw_button, int):
            raw_button = DS4_BUTTONS[raw_button] if 0 <= raw_button < len(DS4_BUTTONS) else "?"
        return DS4_BUTTON_DISPLAY.get(str(raw_button), str(raw_button))
    else:
        from nixwrap.input._xinput import XINPUT_BUTTON_DISPLAY
        if isinstance(raw_button, int):
            return XINPUT_BUTTON_DISPLAY.get(raw_button, f"Btn 0x{raw_button:04X}")
        return str(raw_button)


def is_hotkey_pressed(config: dict) -> bool:
    """Check whether the configured hotkey is currently held.

    Supports keyboard, XInput, and DualSense bindings.

    Parameters
    config:
        A dict with the following keys (matching InGameRank's config.json format):

        - is_controller (bool): True for controller, False for keyboard.
        - hotkey (str): Keyboard key name (e.g. "tab").
        - controller_type (str): "xinput" or "dualsense".
        - controller_button (int): Button mask (XInput) or button index (DualSense).

    Returns
    bool
        True if the bound button/key is currently held.
    """
    try:
        if config.get("is_controller", False):
            ctrl_type = config.get("controller_type", "xinput")
            if ctrl_type == "dualsense":
                from nixwrap.input._dualsense import (
                    ps_controller, get_dualsense_inputs, DS4_BUTTONS,
                )
                if ps_controller is None:
                    return False
                btns = get_dualsense_inputs()
                btn_idx = config.get("controller_button", 0)
                mask = DS4_BUTTONS[btn_idx] if 0 <= btn_idx < len(DS4_BUTTONS) else ""
                return mask in btns
            else:
                from nixwrap.input._xinput import get_xinput_state
                state = get_xinput_state()
                if state:
                    btn = config.get("controller_button", 0)
                    return state.is_pressed(btn)
                return False
        else:
            from nixwrap.input._keyboard import is_key_pressed
            return is_key_pressed(config.get("hotkey", "tab"))
    except Exception:
        return False
