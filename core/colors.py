"""
Fish Tank Donk - Color Management Module
=========================================

Advanced color management with HSV support, gradients, palettes,
and color animations for dynamic wireframe coloring.
"""

import math
from typing import Tuple, List, Optional, Callable, Dict
from dataclasses import dataclass
from enum import Enum, auto


# =============================================================================
# COLOR TYPES
# =============================================================================

RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]
HSV = Tuple[float, float, float]
HSL = Tuple[float, float, float]


# =============================================================================
# HSV COLOR CLASS
# =============================================================================

@dataclass
class HSVColor:
    """
    A color in HSV (Hue, Saturation, Value) format.

    HSV is ideal for color animations and transitions as it
    separates hue from brightness, allowing smooth rainbow effects.
    """
    h: float  # Hue: 0-360 degrees
    s: float  # Saturation: 0-1
    v: float  # Value (brightness): 0-1

    def __post_init__(self):
        """Normalize values to valid ranges."""
        self.h = self.h % 360.0
        self.s = max(0.0, min(1.0, self.s))
        self.v = max(0.0, min(1.0, self.v))

    def to_rgb(self) -> RGB:
        """Convert to RGB (0-255 per channel)."""
        h = self.h / 60.0
        i = int(h) % 6
        f = h - int(h)
        p = self.v * (1.0 - self.s)
        q = self.v * (1.0 - f * self.s)
        t = self.v * (1.0 - (1.0 - f) * self.s)

        if i == 0:
            r, g, b = self.v, t, p
        elif i == 1:
            r, g, b = q, self.v, p
        elif i == 2:
            r, g, b = p, self.v, t
        elif i == 3:
            r, g, b = p, q, self.v
        elif i == 4:
            r, g, b = t, p, self.v
        else:
            r, g, b = self.v, p, q

        return (int(r * 255), int(g * 255), int(b * 255))

    def to_rgb_float(self) -> Tuple[float, float, float]:
        """Convert to RGB (0-1 per channel)."""
        rgb = self.to_rgb()
        return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> 'HSVColor':
        """Create from RGB values (0-255)."""
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c

        if diff == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if max_c == 0 else diff / max_c
        v = max_c

        return cls(h, s, v)

    @classmethod
    def from_rgb_tuple(cls, rgb: RGB) -> 'HSVColor':
        """Create from an RGB tuple."""
        return cls.from_rgb(rgb[0], rgb[1], rgb[2])

    def copy(self) -> 'HSVColor':
        """Create a copy of this color."""
        return HSVColor(self.h, self.s, self.v)

    def with_hue(self, h: float) -> 'HSVColor':
        """Return a copy with modified hue."""
        return HSVColor(h, self.s, self.v)

    def with_saturation(self, s: float) -> 'HSVColor':
        """Return a copy with modified saturation."""
        return HSVColor(self.h, s, self.v)

    def with_value(self, v: float) -> 'HSVColor':
        """Return a copy with modified value."""
        return HSVColor(self.h, self.s, v)

    def rotate_hue(self, degrees: float) -> 'HSVColor':
        """Return a copy with rotated hue."""
        return HSVColor((self.h + degrees) % 360, self.s, self.v)

    def lerp(self, other: 'HSVColor', t: float) -> 'HSVColor':
        """
        Linear interpolation to another color.

        Handles hue wrapping correctly for smooth transitions.
        """
        t = max(0.0, min(1.0, t))

        h1, h2 = self.h, other.h
        if abs(h2 - h1) > 180:
            if h1 < h2:
                h1 += 360
            else:
                h2 += 360

        return HSVColor(
            (h1 + (h2 - h1) * t) % 360,
            self.s + (other.s - self.s) * t,
            self.v + (other.v - self.v) * t
        )

    def complementary(self) -> 'HSVColor':
        """Get the complementary color."""
        return self.rotate_hue(180)

    def triadic(self) -> Tuple['HSVColor', 'HSVColor']:
        """Get triadic colors."""
        return (self.rotate_hue(120), self.rotate_hue(240))

    def analogous(self, angle: float = 30) -> Tuple['HSVColor', 'HSVColor']:
        """Get analogous colors."""
        return (self.rotate_hue(-angle), self.rotate_hue(angle))

    def split_complementary(self, angle: float = 30) -> Tuple['HSVColor', 'HSVColor']:
        """Get split complementary colors."""
        comp = self.complementary()
        return (comp.rotate_hue(-angle), comp.rotate_hue(angle))

    def desaturate(self, amount: float = 0.5) -> 'HSVColor':
        """Reduce saturation."""
        return HSVColor(self.h, self.s * (1 - amount), self.v)

    def saturate(self, amount: float = 0.5) -> 'HSVColor':
        """Increase saturation."""
        return HSVColor(self.h, min(1.0, self.s + (1 - self.s) * amount), self.v)

    def lighten(self, amount: float = 0.2) -> 'HSVColor':
        """Increase brightness."""
        return HSVColor(self.h, self.s, min(1.0, self.v + (1 - self.v) * amount))

    def darken(self, amount: float = 0.2) -> 'HSVColor':
        """Decrease brightness."""
        return HSVColor(self.h, self.s, self.v * (1 - amount))


# =============================================================================
# COLOR GRADIENT
# =============================================================================

class GradientType(Enum):
    """Types of gradient interpolation."""
    LINEAR = auto()
    EASE_IN = auto()
    EASE_OUT = auto()
    EASE_IN_OUT = auto()
    SMOOTH = auto()


@dataclass
class GradientStop:
    """A color stop in a gradient."""
    position: float  # 0-1
    color: HSVColor

    def __post_init__(self):
        self.position = max(0.0, min(1.0, self.position))


class ColorGradient:
    """
    A multi-stop color gradient with various interpolation modes.
    """

    __slots__ = ('_stops', '_gradient_type', '_cached_colors', '_cache_size')

    def __init__(self, gradient_type: GradientType = GradientType.LINEAR):
        """
        Initialize the gradient.

        Args:
            gradient_type: Type of interpolation
        """
        self._stops: List[GradientStop] = []
        self._gradient_type = gradient_type
        self._cached_colors: Optional[List[RGB]] = None
        self._cache_size = 0

    def add_stop(self, position: float, color: HSVColor) -> 'ColorGradient':
        """
        Add a color stop to the gradient.

        Args:
            position: Position (0-1)
            color: Color at this position

        Returns:
            Self for chaining
        """
        self._stops.append(GradientStop(position, color))
        self._stops.sort(key=lambda s: s.position)
        self._cached_colors = None
        return self

    def add_rgb_stop(self, position: float, r: int, g: int, b: int) -> 'ColorGradient':
        """Add a color stop from RGB values."""
        return self.add_stop(position, HSVColor.from_rgb(r, g, b))

    def clear(self) -> None:
        """Clear all stops."""
        self._stops.clear()
        self._cached_colors = None

    def get_color(self, t: float) -> HSVColor:
        """
        Get the color at position t.

        Args:
            t: Position (0-1)

        Returns:
            Interpolated color
        """
        if not self._stops:
            return HSVColor(0, 0, 0)

        if len(self._stops) == 1:
            return self._stops[0].color.copy()

        t = max(0.0, min(1.0, t))
        t = self._apply_easing(t)

        if t <= self._stops[0].position:
            return self._stops[0].color.copy()

        if t >= self._stops[-1].position:
            return self._stops[-1].color.copy()

        for i in range(len(self._stops) - 1):
            if self._stops[i].position <= t <= self._stops[i + 1].position:
                local_t = (t - self._stops[i].position) / (
                    self._stops[i + 1].position - self._stops[i].position
                )
                return self._stops[i].color.lerp(self._stops[i + 1].color, local_t)

        return self._stops[-1].color.copy()

    def get_rgb(self, t: float) -> RGB:
        """Get the RGB color at position t."""
        return self.get_color(t).to_rgb()

    def _apply_easing(self, t: float) -> float:
        """Apply easing function based on gradient type."""
        if self._gradient_type == GradientType.LINEAR:
            return t
        elif self._gradient_type == GradientType.EASE_IN:
            return t * t
        elif self._gradient_type == GradientType.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif self._gradient_type == GradientType.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            return 1 - 2 * (1 - t) * (1 - t)
        elif self._gradient_type == GradientType.SMOOTH:
            return t * t * (3 - 2 * t)
        return t

    def get_cached_colors(self, size: int) -> List[RGB]:
        """
        Get a cached array of colors for fast lookup.

        Args:
            size: Number of colors to cache

        Returns:
            List of RGB colors
        """
        if self._cached_colors is not None and self._cache_size == size:
            return self._cached_colors

        self._cached_colors = [
            self.get_rgb(i / (size - 1)) if size > 1 else self.get_rgb(0)
            for i in range(size)
        ]
        self._cache_size = size

        return self._cached_colors

    @classmethod
    def rainbow(cls) -> 'ColorGradient':
        """Create a rainbow gradient."""
        gradient = cls()
        for i in range(7):
            gradient.add_stop(i / 6.0, HSVColor(i * 60, 1.0, 1.0))
        return gradient

    @classmethod
    def ocean(cls) -> 'ColorGradient':
        """Create an ocean gradient (blue to cyan to white)."""
        gradient = cls()
        gradient.add_stop(0.0, HSVColor(220, 1.0, 0.3))
        gradient.add_stop(0.3, HSVColor(200, 0.9, 0.6))
        gradient.add_stop(0.6, HSVColor(180, 0.7, 0.8))
        gradient.add_stop(1.0, HSVColor(180, 0.2, 1.0))
        return gradient

    @classmethod
    def fire(cls) -> 'ColorGradient':
        """Create a fire gradient (red to yellow to white)."""
        gradient = cls()
        gradient.add_stop(0.0, HSVColor(0, 1.0, 0.5))
        gradient.add_stop(0.3, HSVColor(20, 1.0, 0.8))
        gradient.add_stop(0.6, HSVColor(40, 0.9, 1.0))
        gradient.add_stop(1.0, HSVColor(60, 0.5, 1.0))
        return gradient

    @classmethod
    def bioluminescent(cls) -> 'ColorGradient':
        """Create a bioluminescent gradient (cyan/green glow)."""
        gradient = cls()
        gradient.add_stop(0.0, HSVColor(180, 1.0, 0.2))
        gradient.add_stop(0.3, HSVColor(160, 0.9, 0.5))
        gradient.add_stop(0.6, HSVColor(140, 0.8, 0.8))
        gradient.add_stop(1.0, HSVColor(120, 0.6, 1.0))
        return gradient

    @classmethod
    def jellyfish(cls) -> 'ColorGradient':
        """Create a jellyfish gradient (pink/purple/cyan bioluminescent)."""
        gradient = cls()
        gradient.add_stop(0.0, HSVColor(300, 0.8, 0.4))  # Deep purple
        gradient.add_stop(0.25, HSVColor(280, 0.9, 0.6))  # Purple-pink
        gradient.add_stop(0.5, HSVColor(320, 0.7, 0.8))  # Pink
        gradient.add_stop(0.75, HSVColor(200, 0.6, 0.9))  # Cyan
        gradient.add_stop(1.0, HSVColor(180, 0.5, 1.0))  # Light cyan glow
        return gradient

    @classmethod
    def deep_sea(cls) -> 'ColorGradient':
        """Create a deep sea gradient (dark blue to bioluminescent)."""
        gradient = cls()
        gradient.add_stop(0.0, HSVColor(240, 1.0, 0.1))  # Very dark blue
        gradient.add_stop(0.3, HSVColor(220, 0.9, 0.3))  # Dark blue
        gradient.add_stop(0.6, HSVColor(200, 0.8, 0.5))  # Blue
        gradient.add_stop(0.8, HSVColor(180, 0.7, 0.7))  # Cyan
        gradient.add_stop(1.0, HSVColor(160, 0.5, 0.9))  # Light cyan-green
        return gradient


# =============================================================================
# COLOR MANAGER
# =============================================================================

class ColorManager:
    """
    Manages color animations and transitions for creatures.
    """

    __slots__ = (
        '_base_color', '_current_color', '_target_color',
        '_transition_time', '_transition_elapsed',
        '_animation_func', '_animation_time',
        '_gradient', '_gradient_speed',
        '_pulse_enabled', '_pulse_speed', '_pulse_amount',
        '_rainbow_enabled', '_rainbow_speed'
    )

    def __init__(self, base_color: HSVColor = None):
        """
        Initialize the color manager.

        Args:
            base_color: Base color (default is white)
        """
        self._base_color = base_color or HSVColor(0, 0, 1)
        self._current_color = self._base_color.copy()
        self._target_color = self._base_color.copy()

        self._transition_time = 0.0
        self._transition_elapsed = 0.0

        self._animation_func: Optional[Callable[[float], HSVColor]] = None
        self._animation_time = 0.0

        self._gradient: Optional[ColorGradient] = None
        self._gradient_speed = 1.0

        self._pulse_enabled = False
        self._pulse_speed = 2.0
        self._pulse_amount = 0.3

        self._rainbow_enabled = False
        self._rainbow_speed = 30.0  # degrees per second

    @property
    def current_color(self) -> HSVColor:
        """Get the current color."""
        return self._current_color

    @property
    def current_rgb(self) -> RGB:
        """Get the current color as RGB."""
        return self._current_color.to_rgb()

    def set_base_color(self, color: HSVColor) -> None:
        """Set the base color."""
        self._base_color = color.copy()

    def set_color(self, color: HSVColor, transition_time: float = 0.0) -> None:
        """
        Set the target color with optional transition.

        Args:
            color: Target color
            transition_time: Time to transition (0 for instant)
        """
        if transition_time <= 0:
            self._current_color = color.copy()
            self._target_color = color.copy()
            self._transition_time = 0
        else:
            self._target_color = color.copy()
            self._transition_time = transition_time
            self._transition_elapsed = 0.0

    def set_rgb(self, r: int, g: int, b: int, transition_time: float = 0.0) -> None:
        """Set the target color from RGB."""
        self.set_color(HSVColor.from_rgb(r, g, b), transition_time)

    def set_gradient(self, gradient: ColorGradient, speed: float = 1.0) -> None:
        """
        Set a gradient animation.

        Args:
            gradient: Color gradient to animate through
            speed: Animation speed (cycles per second)
        """
        self._gradient = gradient
        self._gradient_speed = speed
        self._animation_time = 0.0

    def clear_gradient(self) -> None:
        """Clear the gradient animation."""
        self._gradient = None

    def enable_pulse(self, speed: float = 2.0, amount: float = 0.3) -> None:
        """
        Enable pulsing brightness effect.

        Args:
            speed: Pulse speed (cycles per second)
            amount: Pulse intensity (0-1)
        """
        self._pulse_enabled = True
        self._pulse_speed = speed
        self._pulse_amount = amount

    def disable_pulse(self) -> None:
        """Disable pulsing effect."""
        self._pulse_enabled = False

    def enable_rainbow(self, speed: float = 30.0) -> None:
        """
        Enable rainbow hue rotation.

        Args:
            speed: Rotation speed (degrees per second)
        """
        self._rainbow_enabled = True
        self._rainbow_speed = speed

    def disable_rainbow(self) -> None:
        """Disable rainbow effect."""
        self._rainbow_enabled = False

    def set_animation(self, func: Callable[[float], HSVColor]) -> None:
        """
        Set a custom animation function.

        Args:
            func: Function that takes time and returns a color
        """
        self._animation_func = func
        self._animation_time = 0.0

    def clear_animation(self) -> None:
        """Clear custom animation."""
        self._animation_func = None

    def update(self, dt: float) -> None:
        """
        Update color animations.

        Args:
            dt: Delta time in seconds
        """
        self._animation_time += dt

        if self._transition_time > 0:
            self._transition_elapsed += dt
            t = min(1.0, self._transition_elapsed / self._transition_time)
            self._current_color = self._current_color.lerp(self._target_color, t)
            if t >= 1.0:
                self._transition_time = 0

        if self._animation_func:
            self._current_color = self._animation_func(self._animation_time)
        elif self._gradient:
            t = (self._animation_time * self._gradient_speed) % 1.0
            self._current_color = self._gradient.get_color(t)

        if self._rainbow_enabled:
            hue_offset = self._animation_time * self._rainbow_speed
            self._current_color = self._current_color.rotate_hue(hue_offset)

        if self._pulse_enabled:
            pulse = (math.sin(self._animation_time * self._pulse_speed * math.pi * 2) + 1) / 2
            v_offset = self._pulse_amount * pulse
            self._current_color = self._current_color.with_value(
                min(1.0, self._current_color.v + v_offset)
            )

    def get_color_at_position(self, position: float) -> RGB:
        """
        Get color at a specific position (for gradient creatures).

        Args:
            position: Position along the creature (0-1)

        Returns:
            RGB color
        """
        if self._gradient:
            base = self._gradient.get_color(position)
        else:
            base = self._current_color.copy()

        if self._rainbow_enabled:
            offset = position * 60
            base = base.rotate_hue(self._animation_time * self._rainbow_speed + offset)

        if self._pulse_enabled:
            phase_offset = position * math.pi * 2
            pulse = (math.sin(self._animation_time * self._pulse_speed * math.pi * 2 + phase_offset) + 1) / 2
            base = base.with_value(min(1.0, base.v + self._pulse_amount * pulse))

        return base.to_rgb()

    def reset(self) -> None:
        """Reset to base color with no animations."""
        self._current_color = self._base_color.copy()
        self._target_color = self._base_color.copy()
        self._transition_time = 0
        self._animation_func = None
        self._gradient = None
        self._pulse_enabled = False
        self._rainbow_enabled = False


# =============================================================================
# PRESET COLORS
# =============================================================================

class Colors:
    """Preset colors for convenience."""

    BLACK = HSVColor(0, 0, 0)
    WHITE = HSVColor(0, 0, 1)
    RED = HSVColor(0, 1, 1)
    GREEN = HSVColor(120, 1, 1)
    BLUE = HSVColor(240, 1, 1)
    YELLOW = HSVColor(60, 1, 1)
    CYAN = HSVColor(180, 1, 1)
    MAGENTA = HSVColor(300, 1, 1)
    ORANGE = HSVColor(30, 1, 1)
    PURPLE = HSVColor(270, 1, 1)
    PINK = HSVColor(330, 0.7, 1)
    LIME = HSVColor(90, 1, 1)
    TEAL = HSVColor(180, 1, 0.7)
    NAVY = HSVColor(240, 1, 0.5)
    MAROON = HSVColor(0, 1, 0.5)
    OLIVE = HSVColor(60, 1, 0.5)

    # Ocean colors
    OCEAN_BLUE = HSVColor(210, 0.8, 0.6)
    DEEP_SEA = HSVColor(220, 1.0, 0.3)
    CORAL = HSVColor(16, 0.8, 1)
    SEA_GREEN = HSVColor(160, 0.7, 0.6)
    BIOLUMINESCENT = HSVColor(160, 0.9, 0.8)

    # Jellyfish colors
    JELLYFISH_PINK = HSVColor(320, 0.6, 0.9)
    JELLYFISH_PURPLE = HSVColor(280, 0.7, 0.8)
    JELLYFISH_CYAN = HSVColor(190, 0.6, 0.9)
    JELLYFISH_GLOW = HSVColor(300, 0.4, 1.0)

    # Shark colors
    SHARK_GRAY = HSVColor(210, 0.1, 0.5)
    SHARK_DARK = HSVColor(210, 0.15, 0.3)
    SHARK_LIGHT = HSVColor(210, 0.05, 0.7)

    @classmethod
    def get_all(cls) -> Dict[str, HSVColor]:
        """Get all preset colors as a dictionary."""
        return {
            name: value for name, value in vars(cls).items()
            if isinstance(value, HSVColor)
        }
