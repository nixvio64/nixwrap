"""Pre-built colour themes for overlay applications."""

from __future__ import annotations

from dataclasses import dataclass, field

from nixwrap.gui._colors import Color


@dataclass
class Theme:
    """A named set of colours for consistent UI styling."""

    background: Color = field(default_factory=lambda: Color(17, 24, 39))
    surface: Color = field(default_factory=lambda: Color(30, 41, 59))
    text_primary: Color = field(default_factory=lambda: Color(209, 213, 219))
    text_secondary: Color = field(default_factory=lambda: Color(100, 116, 139))
    accent: Color = field(default_factory=lambda: Color(59, 130, 246))
    divider: Color = field(default_factory=lambda: Color(45, 55, 72))


# Built-in themes

THEME_DARK = Theme(
    background=Color(17, 24, 39),
    surface=Color(30, 41, 59),
    text_primary=Color(209, 213, 219),
    text_secondary=Color(100, 116, 139),
    accent=Color(59, 130, 246),
    divider=Color(45, 55, 72),
)

THEME_LIGHT = Theme(
    background=Color(248, 250, 252),
    surface=Color(255, 255, 255),
    text_primary=Color(15, 23, 42),
    text_secondary=Color(100, 116, 139),
    accent=Color(37, 99, 235),
    divider=Color(226, 232, 240),
)
