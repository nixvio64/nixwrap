"""Pixmap/image cache for efficient overlay rendering."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class ImageCache:
    """Thread-safe pixmap cache keyed by (path, width, height).

    Usage::

        from nixwrap.gui import image_cache

        pm = image_cache.get("Tiers", "10.png", 32, 32)
        if pm:
            painter.drawPixmap(x, y, pm)
    """

    def __init__(self) -> None:
        self._cache: dict[str, object] = {}

    def get(
        self,
        folder: str,
        filename: str,
        target_w: Optional[int] = None,
        target_h: Optional[int] = None,
    ):
        """Return a cached QPixmap, loading and scaling if necessary.

        Returns None if the file does not exist or is not a valid image.
        """
        path = os.path.join(str(folder), str(filename))
        cache_key = f"{path}_{target_w}x{target_h}"

        if cache_key not in self._cache:
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import Qt

            if os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    if target_w is None and target_h is not None:
                        scaled = pm.scaledToHeight(
                            target_h,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    elif target_h is None and target_w is not None:
                        scaled = pm.scaledToWidth(
                            target_w,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    elif target_w is not None and target_h is not None:
                        scaled = pm.scaled(
                            target_w, target_h,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    else:
                        scaled = pm
                    self._cache[cache_key] = scaled
                else:
                    self._cache[cache_key] = None
            else:
                self._cache[cache_key] = None

        return self._cache[cache_key]

    def preload(
        self,
        directory: str | Path,
        pattern: str = "*.png",
    ) -> int:
        """Preload all images matching *pattern* from *directory*."""
        import glob
        count = 0
        for f in glob.glob(os.path.join(str(directory), pattern)):
            self.get(str(directory), os.path.basename(f), None, None)
            count += 1
        return count

    def clear(self) -> None:
        """Remove all cached pixmaps."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


# Module-level singleton
image_cache = ImageCache()
