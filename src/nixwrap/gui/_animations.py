"""Animation helpers for overlay windows.

- FadeAnimation: smooth opacity fade-in/fade-out.
- SlideAnimation: slide window in/out (e.g. from bottom of screen).
- PropertyAnimation: interpolate any numeric property over time
  (build your own custom animations).

All are designed to be driven by a QTimer (approx 50ms ticks).
"""

from __future__ import annotations


class FadeAnimation:
    """Smooth fade-in/fade-out for a window.

    Usage::

        anim = FadeAnimation(window)
        timer = QTimer()
        timer.timeout.connect(anim.tick)
        timer.start(50)
        anim.show()   # fade in
    """

    def __init__(
        self,
        window,
        fade_in_step: float = 0.3,
        fade_out_step: float = 1.0 / 6.0,
    ) -> None:
        self._window = window
        self._fade_in_step = fade_in_step
        self._fade_out_step = fade_out_step
        self._current: float = 0.0
        self._target: float = 0.0

    def show(self) -> None:
        self._target = 1.0

    def hide(self) -> None:
        self._target = 0.0

    def toggle(self) -> None:
        self._target = 0.0 if self._target > 0.5 else 1.0

    def tick(self) -> None:
        if self._current == self._target:
            if self._current <= 0.0:
                try:
                    self._window.hide()
                except Exception:
                    pass
            return

        if self._current < self._target:
            self._current = min(self._target,
                                self._current + self._fade_in_step)
        else:
            self._current = max(self._target,
                                self._current - self._fade_out_step)

        try:
            self._window.set_opacity(self._current)
        except Exception:
            pass

        if self._current > 0.0:
            try:
                self._window.show()
            except Exception:
                pass
        elif self._current <= 0.0:
            try:
                self._window.hide()
            except Exception:
                pass

    @property
    def current_opacity(self) -> float:
        return self._current

    @property
    def is_visible(self) -> bool:
        return self._current > 0.0

    @property
    def is_animating(self) -> bool:
        return self._current != self._target


# Slide animation

class SlideAnimation:
    """Slide a window in/out from the bottom (or any edge) of the screen.

    Usage::

        anim = SlideAnimation(window, direction="bottom")
        timer = QTimer()
        timer.timeout.connect(anim.tick)
        timer.start(50)
        anim.show()   # slides up into view
    """

    def __init__(
        self,
        window,
        direction: str = "bottom",
        speed: float = 40.0,    # pixels per tick
    ) -> None:
        self._window = window
        self._direction = direction
        self._speed = speed

        # Capture resting position from the actual widget geometry
        try:
            geo = window.widget.geometry()
            self._rest_x = geo.x()
            self._rest_y = geo.y()
        except Exception:
            self._rest_x = 0
            self._rest_y = 0

        # Start off-screen (same as hidden state)
        self._off_offset = self._calc_off_offset()
        self._current_offset: float = float(self._off_offset)
        self._target_offset: float = float(self._off_offset)
        self._target_visible: bool = False

        # Push the widget off-screen immediately
        self._apply_offset()

        # Ensure hidden until animation starts
        try:
            self._window.hide()
        except Exception:
            pass

    def _calc_off_offset(self) -> int:
        h = self._window.config.height
        w = self._window.config.width
        if self._direction == "bottom":
            return h + 40
        elif self._direction == "top":
            return -(h + 40)
        elif self._direction == "left":
            return -(w + 40)
        elif self._direction == "right":
            return w + 40
        return 0

    def show(self) -> None:
        self._target_visible = True
        self._target_offset = 0.0

    def hide(self) -> None:
        self._target_visible = False
        self._target_offset = float(self._off_offset)

    def tick(self) -> None:
        if self._current_offset == self._target_offset:
            if not self._target_visible:
                try:
                    self._window.hide()
                except Exception:
                    pass
            return

        diff = self._target_offset - self._current_offset
        step = min(abs(diff), self._speed) * (1 if diff > 0 else -1)
        self._current_offset += step
        self._apply_offset()

        if self._target_visible:
            try:
                self._window.show()
            except Exception:
                pass

    def _apply_offset(self) -> None:
        x, y = self._rest_x, self._rest_y
        if self._direction == "bottom":
            y += int(self._current_offset)
        elif self._direction == "top":
            y += int(self._current_offset)
        elif self._direction == "left":
            x += int(self._current_offset)
        elif self._direction == "right":
            x += int(self._current_offset)
        try:
            self._window.set_position(x, y)
        except Exception:
            pass


# General property animation

class PropertyAnimation:
    """Interpolate any numeric window property over time.

    Usage::

        anim = PropertyAnimation(window, "opacity", 0.0, 1.0, duration_ms=300)
        timer = QTimer()
        timer.timeout.connect(anim.tick)
        timer.start(16)    # approx 60fps

    Supported property names:
        "opacity", "x", "y", "width", "height"
    """

    def __init__(
        self,
        window,
        property_name: str,
        from_value: float,
        to_value: float,
        duration_ms: int = 300,
    ) -> None:
        self._window = window
        self._prop = property_name
        self._from = float(from_value)
        self._to = float(to_value)
        self._duration = max(1, duration_ms)
        self._elapsed: float = 0.0
        self._finished = False

    def tick(self, delta_ms: int = 16) -> None:
        if self._finished:
            return
        self._elapsed += delta_ms
        t = min(1.0, self._elapsed / self._duration)
        # Ease-out cubic
        eased = 1.0 - (1.0 - t) ** 3
        value = self._from + (self._to - self._from) * eased

        try:
            if self._prop == "opacity":
                self._window.set_opacity(value)
            elif self._prop == "x":
                self._window.set_position(int(value), self._window.config.y or 0)
            elif self._prop == "y":
                self._window.set_position(self._window.config.x or 0, int(value))
            elif self._prop == "width":
                self._window.set_size(int(value), self._window.config.height)
            elif self._prop == "height":
                self._window.set_size(self._window.config.width, int(value))
        except Exception:
            pass

        if t >= 1.0:
            self._finished = True

    @property
    def is_finished(self) -> bool:
        return self._finished
