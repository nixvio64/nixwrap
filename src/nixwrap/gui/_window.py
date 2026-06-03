"""Window types for the GUI module.

Provides frameless overlay windows (like InGameRank), frameless normal
windows, standard windows, and dialogs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WindowType(Enum):
    OVERLAY = "overlay"         # frameless, transparent bg, always-on-top, input-transparent
    FRAMELESS = "frameless"     # frameless, not always-on-top
    NORMAL = "normal"           # standard window with title bar
    DIALOG = "dialog"           # standard dialog


@dataclass(slots=True)
class WindowConfig:
    """Configuration for a BaseWindow.

    Attributes
    window_type:
        The window style.
    title:
        Window title (shown in taskbar, and for NORMAL/DIALOG in the
        title bar).
    width, height:
        Initial window dimensions in pixels.
    x, y:
        Initial position.  None means "centre on screen".
    corner_radius:
        Radius for rounded corners (pixels).  0 = square edges.
    opacity:
        Window opacity (0.0-1.0).
    stay_on_top:
        Keep window above others.
    transparent_for_input:
        Mouse events pass through the window.
    visible:
        Whether the window starts visible.
    """
    window_type: WindowType = WindowType.OVERLAY
    title: str = ""
    width: int = 400
    height: int = 300
    x: int | None = None
    y: int | None = None
    corner_radius: int = 8
    opacity: float = 1.0
    stay_on_top: bool = False
    transparent_for_input: bool = False
    visible: bool = True


class BaseWindow:
    """A flexible Qt window configured via WindowConfig.

    Override _paint() to draw custom content.

    Usage::

        from nixwrap.gui import BaseWindow, WindowConfig, WindowType

        config = WindowConfig(
            window_type=WindowType.OVERLAY,
            width=600, height=200,
            corner_radius=12,
            opacity=0.95,
        )
        win = BaseWindow(config)
        win.show()
    """

    _widget = None  # set after _create()

    def __init__(self, config: WindowConfig) -> None:
        self._config = config
        self._create()

    def _create(self) -> None:
        from PySide6.QtWidgets import QWidget, QApplication
        from PySide6.QtCore import Qt

        w = QWidget()
        cfg = self._config

        # Window flags
        flags = Qt.WindowType.Widget
        if cfg.window_type == WindowType.OVERLAY:
            flags = (
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.WindowTransparentForInput |
                Qt.WindowType.Tool
            )
        elif cfg.window_type == WindowType.FRAMELESS:
            flags = Qt.WindowType.FramelessWindowHint
        elif cfg.window_type == WindowType.DIALOG:
            flags = Qt.WindowType.Dialog
        else:
            flags = Qt.WindowType.Window

        if cfg.stay_on_top and cfg.window_type not in (
            WindowType.OVERLAY, WindowType.DIALOG
        ):
            flags |= Qt.WindowType.WindowStaysOnTopHint

        w.setWindowFlags(flags)

        if cfg.window_type == WindowType.OVERLAY:
            w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Title
        if cfg.title:
            w.setWindowTitle(cfg.title)

        # Opacity
        w.setWindowOpacity(cfg.opacity)

        # Geometry
        if cfg.x is None:
            cfg.x = self._screen_center_x(cfg.width)
        if cfg.y is None:
            cfg.y = self._screen_center_y(cfg.height)
        w.setGeometry(cfg.x, cfg.y, cfg.width, cfg.height)

        # Visibility
        if cfg.visible:
            w.show()

        # Override paint
        original_paint = w.paintEvent

        def _paint_wrapper(event):
            from PySide6.QtGui import QPainter
            painter = QPainter(w)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            self._paint(painter)
            painter.end()

        w.paintEvent = _paint_wrapper
        self._widget = w

    def _paint(self, painter) -> None:
        """Override this method to draw custom content.

        Called during the widget's paintEvent with a QPainter
        already configured for antialiased rendering.
        """

    # Public methods

    @property
    def widget(self):
        """The underlying QWidget."""
        return self._widget

    @property
    def config(self) -> WindowConfig:
        return self._config

    def show(self) -> None:
        self._widget.show()

    def hide(self) -> None:
        self._widget.hide()

    def close(self) -> None:
        self._widget.close()

    def set_opacity(self, value: float) -> None:
        """Set window opacity (0.0 to 1.0)."""
        self._config.opacity = max(0.0, min(1.0, value))
        self._widget.setWindowOpacity(self._config.opacity)

    def set_corner_radius(self, radius: int) -> None:
        """Set the corner radius for rounded rectangles."""
        self._config.corner_radius = max(0, radius)

    def set_position(self, x: int, y: int) -> None:
        """Move the window to (x, y)."""
        self._config.x = x
        self._config.y = y
        self._widget.move(x, y)

    def set_size(self, width: int, height: int) -> None:
        """Resize the window."""
        self._config.width = width
        self._config.height = height
        self._widget.resize(width, height)

    def center_on_screen(self, screen_index: int = 0) -> None:
        """Centre the window on the specified screen."""
        from nixwrap.gui._geometry import get_all_screens, get_primary_screen
        screens = get_all_screens()
        if screen_index < len(screens):
            s = screens[screen_index]
        else:
            s = get_primary_screen()
        if s is None:
            return
        x = s.x + (s.available_width - self._config.width) // 2
        y = s.y + (s.available_height - self._config.height) // 2
        self.set_position(x, y)

    def snap_to_bottom_center(self, margin: int = 0) -> None:
        """Position at the bottom centre of the primary screen."""
        s = self._primary_screen()
        if s is None:
            return
        x = s.x + (s.available_width - self._config.width) // 2
        y = s.y + s.available_height - self._config.height - margin
        self.set_position(x, y)

    def snap_to_top_center(self, margin: int = 0) -> None:
        """Position at the top centre of the primary screen."""
        s = self._primary_screen()
        if s is None:
            return
        x = s.x + (s.available_width - self._config.width) // 2
        y = s.y + margin
        self.set_position(x, y)

    # Helpers

    @staticmethod
    def _primary_screen():
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return None
        from nixwrap.gui._geometry import ScreenInfo
        screen = app.primaryScreen()
        if screen is None:
            return None
        geo = screen.availableGeometry()
        return ScreenInfo(
            width=screen.geometry().width(),
            height=screen.geometry().height(),
            available_width=geo.width(),
            available_height=geo.height(),
            x=screen.geometry().x(),
            y=screen.geometry().y(),
        )

    @staticmethod
    def _screen_center_x(width: int) -> int:
        s = BaseWindow._primary_screen()
        if s is None:
            return 0
        return s.x + (s.available_width - width) // 2

    @staticmethod
    def _screen_center_y(height: int) -> int:
        s = BaseWindow._primary_screen()
        if s is None:
            return 0
        return s.y + (s.available_height - height) // 2


# Factory functions

def create_overlay(
    width: int = 400,
    height: int = 300,
    **kwargs,
) -> BaseWindow:
    """Create a transparent overlay window."""
    config = WindowConfig(
        window_type=WindowType.OVERLAY,
        width=width, height=height,
        **kwargs,
    )
    return BaseWindow(config)


def create_frameless_window(
    width: int = 400,
    height: int = 300,
    **kwargs,
) -> BaseWindow:
    """Create a frameless (but not transparent) window."""
    config = WindowConfig(
        window_type=WindowType.FRAMELESS,
        width=width, height=height,
        **kwargs,
    )
    return BaseWindow(config)


def create_window(
    title: str = "",
    width: int = 400,
    height: int = 300,
    **kwargs,
) -> BaseWindow:
    """Create a normal window with title bar."""
    config = WindowConfig(
        window_type=WindowType.NORMAL,
        title=title,
        width=width, height=height,
        **kwargs,
    )
    return BaseWindow(config)
