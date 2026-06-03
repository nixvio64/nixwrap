"""Color and gradient utilities for Qt painting."""

from __future__ import annotations

import math
from dataclasses import dataclass

# Lazy Qt import happens when methods are called


@dataclass(slots=True)
class Color:
    """An RGBA color (0-255)."""

    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 255

    # Factory methods

    @staticmethod
    def from_hex(hex_str: str) -> Color:
        """Parse a hex color string.

        Supports "#FF8040", "FF8040", "#FF8040C0" (with alpha).
        """
        h = hex_str.lstrip("#")
        if len(h) == 6:
            return Color(
                r=int(h[0:2], 16),
                g=int(h[2:4], 16),
                b=int(h[4:6], 16),
            )
        elif len(h) == 8:
            return Color(
                r=int(h[0:2], 16),
                g=int(h[2:4], 16),
                b=int(h[4:6], 16),
                a=int(h[6:8], 16),
            )
        raise ValueError(f"Invalid hex color: {hex_str!r}")

    @staticmethod
    def from_hsl(h: float, s: float, l: float, a: float = 1.0) -> Color:
        """Create from HSL (hue 0-360, saturation 0-1, lightness 0-1)."""
        h = h % 360 / 360.0
        if s == 0:
            r = g = b = int(l * 255)
        else:
            def hue2rgb(p: float, q: float, t: float) -> float:
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1 / 6: return p + (q - p) * 6 * t
                if t < 1 / 2: return q
                if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
                return p

            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue2rgb(p, q, h + 1 / 3)
            g = hue2rgb(p, q, h)
            b = hue2rgb(p, q, h - 1 / 3)
        return Color(
            r=int(r * 255), g=int(g * 255), b=int(b * 255),
            a=int(a * 255),
        )

    # Conversions

    def to_qcolor(self):
        """Convert to a QColor."""
        from PySide6.QtGui import QColor
        return QColor(self.r, self.g, self.b, self.a)

    def to_hex(self) -> str:
        """Return #RRGGBB or #RRGGBBAA."""
        if self.a == 255:
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}{self.a:02X}"

    # Helpers

    def with_alpha(self, a: int) -> Color:
        """Return a new Color with alpha changed."""
        return Color(self.r, self.g, self.b, max(0, min(255, a)))

    def lerp(self, other: Color, t: float) -> Color:
        """Linearly interpolate between this and *other* by *t* (0-1)."""
        t = max(0.0, min(1.0, t))
        return Color(
            r=int(self.r + (other.r - self.r) * t),
            g=int(self.g + (other.g - self.g) * t),
            b=int(self.b + (other.b - self.b) * t),
            a=int(self.a + (other.a - self.a) * t),
        )

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"


# Gradients

class Gradient:
    """A linear gradient with colour stops.

    Parameters
    stops:
        List of (position, Color) tuples where position is 0.0-1.0.
    direction:
        "horizontal" or "vertical".
    """

    def __init__(
        self,
        stops: list[tuple[float, Color]],
        direction: str = "horizontal",
    ) -> None:
        self.stops = sorted(stops, key=lambda s: s[0])
        self.direction = direction

    def to_qbrush(self, rect):
        """Convert to a QLinearGradient brush."""
        from PySide6.QtGui import QLinearGradient
        from PySide6.QtCore import QPointF

        if self.direction == "vertical":
            grad = QLinearGradient(
                QPointF(rect.left(), rect.top()),
                QPointF(rect.left(), rect.bottom()),
            )
        else:
            grad = QLinearGradient(
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right(), rect.top()),
            )
        for pos, color in self.stops:
            grad.setColorAt(pos, color.to_qcolor())
        return grad


# Pre-defined colors

TEAM_BLUE      = Color(79, 195, 247)
TEAM_ORANGE    = Color(255, 160, 64)
BACKGROUND_DARK = Color(17, 24, 39, 216)
DIVIDER_GRAY   = Color(45, 55, 72)
TEXT_MUTED     = Color(100, 116, 139)
TEXT_LIGHT     = Color(209, 213, 219)
TEXT_WHITE     = Color(255, 255, 255)
ACCENT_BLUE    = Color(59, 130, 246)
