"""Overlay/GUI toolkit. Needs PySide6 (pip install nixwrap[gui])."""


def __getattr__(name: str):
    """Lazy-load all public names, checking for PySide6."""
    _ensure_pyside6()
    # Import the real module
    if name in _EXPORTS:
        mod_name, attr = _EXPORTS[name]
        mod = __import__(f"nixwrap.gui.{mod_name}", fromlist=[attr])
        return getattr(mod, attr)
    raise AttributeError(f"module 'nixwrap.gui' has no attribute {name!r}")


def _ensure_pyside6() -> None:
    try:
        import PySide6  # noqa: F401
    except ImportError:
        raise ImportError(
            "The nixwrap.gui module requires PySide6.\n"
            "Install with:  pip install nixwrap[gui]\n"
            "Or directly:   pip install PySide6"
        ) from None


# Map public names to (module, attr)
_EXPORTS: dict[str, tuple[str, str]] = {
    # _window
    "BaseWindow": ("_window", "BaseWindow"),
    "WindowConfig": ("_window", "WindowConfig"),
    "WindowType": ("_window", "WindowType"),
    "create_overlay": ("_window", "create_overlay"),
    "create_frameless_window": ("_window", "create_frameless_window"),
    "create_window": ("_window", "create_window"),
    # _painter
    "Painter": ("_painter", "Painter"),
    # _colors
    "Color": ("_colors", "Color"),
    "Gradient": ("_colors", "Gradient"),
    "TEAM_BLUE": ("_colors", "TEAM_BLUE"),
    "TEAM_ORANGE": ("_colors", "TEAM_ORANGE"),
    "BACKGROUND_DARK": ("_colors", "BACKGROUND_DARK"),
    "DIVIDER_GRAY": ("_colors", "DIVIDER_GRAY"),
    "TEXT_MUTED": ("_colors", "TEXT_MUTED"),
    "TEXT_LIGHT": ("_colors", "TEXT_LIGHT"),
    "TEXT_WHITE": ("_colors", "TEXT_WHITE"),
    "ACCENT_BLUE": ("_colors", "ACCENT_BLUE"),
    # _geometry
    "LayoutCalculator": ("_geometry", "LayoutCalculator"),
    "ScreenInfo": ("_geometry", "ScreenInfo"),
    "get_primary_screen": ("_geometry", "get_primary_screen"),
    "get_all_screens": ("_geometry", "get_all_screens"),
    "get_screen_containing": ("_geometry", "get_screen_containing"),
    # _text
    "FontConfig": ("_text", "FontConfig"),
    "FontManager": ("_text", "FontManager"),
    "font_manager": ("_text", "font_manager"),
    # _images
    "ImageCache": ("_images", "ImageCache"),
    "image_cache": ("_images", "image_cache"),
    # _animations
    "FadeAnimation": ("_animations", "FadeAnimation"),
    "SlideAnimation": ("_animations", "SlideAnimation"),
    "PropertyAnimation": ("_animations", "PropertyAnimation"),
    # _themes
    "Theme": ("_themes", "Theme"),
    "THEME_DARK": ("_themes", "THEME_DARK"),
    "THEME_LIGHT": ("_themes", "THEME_LIGHT"),
    # _app
    "QtApp": ("_app", "QtApp"),
    "get_rl_monitor": ("_app", "get_rl_monitor"),
    "snap_to_rl_monitor": ("_app", "snap_to_rl_monitor"),
    "is_rl_active": ("_app", "is_rl_active"),
}


__all__ = list(_EXPORTS.keys())
