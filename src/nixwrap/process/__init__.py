"""Find running RL process, detect Steam vs Epic, window focus checks."""

from nixwrap.process._detector import (
    RLPlatform,
    RLProcessInfo,
    find_rocket_league,
    detect_platform,
    get_save_data_path,
)
from nixwrap.process._window import (
    is_rocket_league_focused,
    get_rocket_league_window_rect,
    is_cursor_inside_rl_window,
)

__all__ = [
    "RLPlatform",
    "RLProcessInfo",
    "find_rocket_league",
    "detect_platform",
    "get_save_data_path",
    "is_rocket_league_focused",
    "get_rocket_league_window_rect",
    "is_cursor_inside_rl_window",
]
