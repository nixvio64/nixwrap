""""Screen geometry and layout helpers.

Percentage-based layout scaling inspired by the InGameRank overlay.
Base design is 1920x1080, scaled to the actual screen via
min(scaleW, scaleH) for uniform proportions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScreenInfo:
    """Information about a display/monitor."""
    index: int = 0
    name: str = ""
    width: int = 1920
    height: int = 1080
    available_width: int = 1920
    available_height: int = 1040
    x: int = 0
    y: int = 0
    dpi: float = 96.0
    is_primary: bool = True


def get_primary_screen() -> ScreenInfo | None:
    """Return info for the primary display, or None if Qt is not available."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return None
        screen = app.primaryScreen()
        if screen is None:
            return None
        return _screen_to_info(screen, 0)
    except ImportError:
        return None


def get_all_screens() -> list[ScreenInfo]:
    """Return info for all connected displays."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QGuiApplication
        screens = QGuiApplication.screens()
        if not screens:
            return []
        primary_name = QApplication.instance().primaryScreen().name() if QApplication.instance() else ""
        result = []
        for i, s in enumerate(screens):
            info = _screen_to_info(s, i)
            info.is_primary = (info.name == primary_name)
            result.append(info)
        return result
    except ImportError:
        return []


def get_screen_containing(x: int, y: int) -> ScreenInfo | None:
    """Return the screen that contains the point (x, y)."""
    for s in get_all_screens():
        if s.x <= x <= s.x + s.width and s.y <= y <= s.y + s.height:
            return s
    return get_primary_screen()


def _screen_to_info(screen, index: int) -> ScreenInfo:
    geo = screen.availableGeometry()
    full = screen.geometry()
    return ScreenInfo(
        index=index,
        name=screen.name(),
        width=full.width(),
        height=full.height(),
        available_width=geo.width(),
        available_height=geo.height(),
        x=full.x(),
        y=full.y(),
        dpi=screen.logicalDotsPerInch(),
        is_primary=(index == 0),
    )


# Layout Calculator

class LayoutCalculator:
    """Percentage-based layout scaling.

    Mirrors the InGameRank overlay's layout math: base 1920x1080
    design, scaled uniformly via min(scaleW, scaleH).

    Parameters
    base_width:
        Reference design width (default 1920).
    base_height:
        Reference design height (default 1080).
    screen:
        Target ScreenInfo.  If None, uses the primary screen
        at init time.
    """

    def __init__(
        self,
        base_width: float = 1920.0,
        base_height: float = 1080.0,
        screen: ScreenInfo | None = None,
    ) -> None:
        self._base_w = base_width
        self._base_h = base_height
        if screen is None:
            screen = get_primary_screen()
        if screen is None:
            screen = ScreenInfo()
        self._screen = screen
        self._scale = min(
            screen.width / base_width,
            screen.height / base_height,
        )

    @property
    def screen(self) -> ScreenInfo:
        return self._screen

    def refresh_screen(self) -> None:
        """Re-query the primary screen geometry."""
        new_screen = get_primary_screen()
        if new_screen is not None:
            self._screen = new_screen
            self._scale = min(
                new_screen.width / self._base_w,
                new_screen.height / self._base_h,
            )

    # Scaling

    def scale_w(self, pct: float) -> int:
        """Scale a percentage of screen width to pixels."""
        return max(1, round(self._screen.width * (pct / 100.0)))

    def scale_h(self, pct: float) -> int:
        """Scale a percentage of screen height to pixels."""
        return max(1, round(self._screen.height * (pct / 100.0)))

    def scale(self, value: float) -> float:
        """Scale a font-size-like value uniformly."""
        return max(1.0, value * self._scale)

    def window_w(self, overlay_w: int, pct: float) -> int:
        """Percentage of an overlay's width."""
        return max(1, round(overlay_w * (pct / 100.0)))

    # Positioning

    def center_x(self, element_width: int) -> int:
        """Return the x position to centre *element_width* on screen."""
        return self._screen.x + ((self._screen.width - element_width) // 2)

    def bottom_y(self, element_height: int) -> int:
        """Return the y position to anchor to the bottom of the screen."""
        return self._screen.y + self._screen.height - element_height

    def top_y(self, element_height: int = 0) -> int:
        """Return the y position to anchor to the top of the screen."""
        return self._screen.y

    def center_y(self, element_height: int) -> int:
        """Return the y position to centre *element_height* vertically."""
        return self._screen.y + ((self._screen.height - element_height) // 2)
