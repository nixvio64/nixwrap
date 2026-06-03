"""Keyboard, XInput (Xbox), DualSense (PS5) input detection."""

from nixwrap.input._xinput import (
    XInputState,
    XINPUT_A, XINPUT_B, XINPUT_X, XINPUT_Y,
    XINPUT_LB, XINPUT_RB, XINPUT_LS, XINPUT_RS,
    XINPUT_START, XINPUT_SELECT,
    XINPUT_DPAD_UP, XINPUT_DPAD_DOWN, XINPUT_DPAD_LEFT, XINPUT_DPAD_RIGHT,
    XINPUT_BUTTON_DISPLAY,
    get_xinput_state,
)

from nixwrap.input._keyboard import (
    is_key_pressed,
    detect_hotkey,
)

from nixwrap.input._bindings import (
    get_button_display,
    is_hotkey_pressed,
    ControllerType,
)

from nixwrap.input._dualsense import (
    setup_dualsense,
    get_dualsense_inputs,
    is_dualsense_connected,
    start_dualsense_monitor,
    DS4_BUTTON_DISPLAY,
    DS4_BUTTONS,
    ps_controller,
)

__all__ = [
    # XInput
    "XInputState",
    "get_xinput_state",
    "XINPUT_A", "XINPUT_B", "XINPUT_X", "XINPUT_Y",
    "XINPUT_LB", "XINPUT_RB", "XINPUT_LS", "XINPUT_RS",
    "XINPUT_START", "XINPUT_SELECT",
    "XINPUT_DPAD_UP", "XINPUT_DPAD_DOWN", "XINPUT_DPAD_LEFT", "XINPUT_DPAD_RIGHT",
    "XINPUT_BUTTON_DISPLAY",
    # DualSense
    "setup_dualsense", "get_dualsense_inputs", "is_dualsense_connected",
    "start_dualsense_monitor",
    "DS4_BUTTON_DISPLAY", "DS4_BUTTONS", "ps_controller",
    # Keyboard
    "is_key_pressed", "detect_hotkey",
    # Bindings
    "is_hotkey_pressed", "get_button_display", "ControllerType",
]
