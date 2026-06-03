"""Font management for Qt text rendering.

Supports system fonts and custom .ttf / .otf files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class FontConfig:
    """Configuration for a font."""
    family: str = "Segoe UI"
    size: int = 12
    bold: bool = False
    italic: bool = False


class FontManager:
    """Manages font loading and caching.

    Usage::

        from nixwrap.gui import font_manager, FontConfig

        font = font_manager.get_font(FontConfig(family="Arial", size=14, bold=True))
    """

    def __init__(self) -> None:
        self._custom_fonts: dict[int, str] = {}   # font_id → family_name
        self._next_id = 1000

    def get_font(self, config: FontConfig):
        """Return a QFont for the given config."""
        from PySide6.QtGui import QFont
        font = QFont(config.family, config.size)
        font.setBold(config.bold)
        font.setItalic(config.italic)
        return font

    def load_font_file(self, path: str | Path) -> int:
        """Load a custom font file (.ttf / .otf).

        Returns a font ID that can be used with get_font_by_file().
        """
        from PySide6.QtGui import QFontDatabase
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Font file not found: {path}")
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            raise ValueError(f"Failed to load font: {path}")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            self._custom_fonts[font_id] = families[0]
        return font_id

    def get_font_by_file(self, font_id: int, size: int = 12) -> object:
        """Return a QFont for a previously loaded custom font."""
        from PySide6.QtGui import QFont
        family = self._custom_fonts.get(font_id)
        if family is None:
            raise ValueError(f"Unknown font ID: {font_id}")
        return QFont(family, size)

    def available_families(self) -> list[str]:
        """Return all available font family names."""
        from PySide6.QtGui import QFontDatabase
        return QFontDatabase.families()


# Module-level singleton
font_manager = FontManager()
