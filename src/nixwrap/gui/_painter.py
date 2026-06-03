"""Canvas-like drawing primitives wrapping QPainter.

Usage::

    from nixwrap.gui import Painter, Color

    class MyWindow(BaseWindow):
        def _paint(self, painter_q):
            p = Painter(painter_q)
            p.fill_rect(0, 0, self.width, self.height,
                         Color(17, 24, 39, 216), radius=8)
            p.draw_text("Hello", 20, 30,
                        color=Color(255, 255, 255))
"""

from __future__ import annotations

from pathlib import Path

from nixwrap.gui._colors import Color


class Painter:
    """Wraps a QPainter with a simplified canvas API.

    All coordinates are in pixels relative to the widget origin.
    """

    def __init__(self, painter) -> None:
        self._p = painter
        self._default_font = None

    # Shapes

    def fill_rect(
        self, x: float, y: float, w: float, h: float,
        color: Color, radius: float = 0,
    ) -> None:
        """Draw a filled rectangle, optionally with rounded corners."""
        from PySide6.QtCore import QRectF, QSizeF, QPointF
        from PySide6.QtGui import QPainterPath

        self._p.setBrush(color.to_qcolor())
        self._p.setPen(color.to_qcolor())  # no border

        if radius > 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
            self._p.drawPath(path)
        else:
            self._p.drawRect(QRectF(x, y, w, h))

    def stroke_rect(
        self, x: float, y: float, w: float, h: float,
        color: Color, width: float = 1.0, radius: float = 0,
    ) -> None:
        """Draw the outline of a rectangle."""
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QPen, QPainterPath
        from PySide6.QtCore import Qt

        pen = QPen(color.to_qcolor(), width)
        self._p.setPen(pen)
        self._p.setBrush(Qt.BrushStyle.NoBrush)

        if radius > 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
            self._p.drawPath(path)
        else:
            self._p.drawRect(QRectF(x, y, w, h))

    def fill_circle(
        self, cx: float, cy: float, r: float, color: Color,
    ) -> None:
        """Draw a filled circle centred at (cx, cy)."""
        from PySide6.QtCore import QPointF
        self._p.setBrush(color.to_qcolor())
        self._p.setPen(color.to_qcolor())
        self._p.drawEllipse(QPointF(cx, cy), r, r)

    def stroke_circle(
        self, cx: float, cy: float, r: float,
        color: Color, width: float = 1.0,
    ) -> None:
        """Draw the outline of a circle."""
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QPen

        pen = QPen(color.to_qcolor(), width)
        self._p.setPen(pen)
        self._p.setBrush(Qt.BrushStyle.NoBrush)
        self._p.drawEllipse(QPointF(cx, cy), r, r)

    def draw_line(
        self, x1: float, y1: float, x2: float, y2: float,
        color: Color, width: float = 1.0,
    ) -> None:
        """Draw a straight line from (x1, y1) to (x2, y2)."""
        from PySide6.QtGui import QPen
        pen = QPen(color.to_qcolor(), width)
        self._p.setPen(pen)
        self._p.drawLine(
            int(x1), int(y1),
            int(x2), int(y2),
        )

    def draw_polygon(
        self,
        points: list[tuple[float, float]],
        fill_color: Color | None = None,
        stroke_color: Color | None = None,
        stroke_width: float = 1.0,
    ) -> None:
        """Draw a filled and/or stroked polygon."""
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QPolygonF, QPen

        qpoints = [QPointF(x, y) for x, y in points]
        poly = QPolygonF(qpoints)

        if fill_color:
            self._p.setBrush(fill_color.to_qcolor())
        else:
            self._p.setBrush(Qt.BrushStyle.NoBrush)

        if stroke_color:
            self._p.setPen(QPen(stroke_color.to_qcolor(), stroke_width))
        else:
            self._p.setPen(Qt.PenStyle.NoPen)

        self._p.drawPolygon(poly)

    # Text

    def draw_text(
        self,
        text: str,
        x: float, y: float,
        font = None,
        color: Color | None = None,
        alignment: int = 0x0001,  # Qt.AlignLeft
    ) -> object:
        """Draw text at (x, y) and return the bounding QRectF."""
        from PySide6.QtCore import QRectF

        if font is not None:
            self._p.setFont(font)
        if color is not None:
            self._p.setPen(color.to_qcolor())

        return self._p.drawText(QRectF(x, y, 10000, 1000), alignment, text)

    # Images

    def draw_pixmap(self, pixmap, x: float, y: float) -> None:
        """Draw a QPixmap at (x, y)."""
        self._p.drawPixmap(int(x), int(y), pixmap)

    def draw_image(
        self,
        path: str | Path,
        x: float, y: float,
        width: float = 0, height: float = 0,
    ) -> None:
        """Load and draw an image from file.

        If *width* / *height* are 0, the native size is used.
        """
        from nixwrap.gui._images import image_cache
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt

        pm = QPixmap(str(path))
        if pm.isNull():
            return
        if width > 0 and height > 0:
            pm = pm.scaled(
                int(width), int(height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.draw_pixmap(pm, x, y)

    # State

    def save(self) -> None:
        """Push the current painter state."""
        self._p.save()

    def restore(self) -> None:
        """Pop the last saved painter state."""
        self._p.restore()

    def set_opacity(self, value: float) -> None:
        """Set the painter's global opacity (0.0 to 1.0)."""
        self._p.setOpacity(max(0.0, min(1.0, value)))

    def set_clip_rect(
        self, x: float, y: float, w: float, h: float,
    ) -> None:
        """Clip all subsequent drawing to the given rectangle."""
        from PySide6.QtCore import QRectF
        self._p.setClipRect(QRectF(x, y, w, h))
