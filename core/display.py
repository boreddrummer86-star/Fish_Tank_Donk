"""
Fish Tank Donk - Terminal Display Module
=========================================

Advanced terminal display management using curses for real-time
rendering with color support, double buffering, and input handling.
Optimized for 60fps stable rendering.
"""

import sys
import os
import time
import threading
from typing import List, Tuple, Optional, Callable, Dict, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False


# =============================================================================
# CONSTANTS
# =============================================================================

TARGET_FPS = 60
FRAME_TIME = 1.0 / TARGET_FPS
MIN_FRAME_TIME = 1.0 / 120.0


# =============================================================================
# INPUT HANDLING
# =============================================================================

class KeyCode(Enum):
    """Key codes for input handling."""
    NONE = 0
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    ENTER = auto()
    ESCAPE = auto()
    SPACE = auto()
    TAB = auto()
    BACKSPACE = auto()
    DELETE = auto()
    HOME = auto()
    END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()
    NUMPAD_0 = auto()
    NUMPAD_1 = auto()
    NUMPAD_2 = auto()
    NUMPAD_3 = auto()
    NUMPAD_4 = auto()
    NUMPAD_5 = auto()
    NUMPAD_6 = auto()
    NUMPAD_7 = auto()
    NUMPAD_8 = auto()
    NUMPAD_9 = auto()


@dataclass
class InputEvent:
    """Input event data."""
    key_code: KeyCode
    character: str
    modifiers: Set[str] = field(default_factory=set)
    timestamp: float = 0.0


class InputManager:
    """
    Manages keyboard input with buffering and event handling.
    """

    __slots__ = (
        '_key_states', '_key_pressed', '_key_released',
        '_event_queue', '_callbacks', '_max_queue_size'
    )

    def __init__(self, max_queue_size: int = 32):
        """
        Initialize the input manager.

        Args:
            max_queue_size: Maximum number of events to queue
        """
        self._key_states: Dict[str, bool] = {}
        self._key_pressed: Set[str] = set()
        self._key_released: Set[str] = set()
        self._event_queue: deque = deque(maxlen=max_queue_size)
        self._callbacks: Dict[str, List[Callable]] = {}
        self._max_queue_size = max_queue_size

    def process_key(self, key: int) -> Optional[InputEvent]:
        """
        Process a key code from curses.

        Args:
            key: Key code from curses.getch()

        Returns:
            InputEvent or None if no valid key
        """
        if key == -1 or key == curses.ERR:
            return None

        event = self._create_event(key)
        if event.key_code != KeyCode.NONE or event.character:
            self._event_queue.append(event)

            key_name = event.character or event.key_code.name
            if key_name:
                self._key_pressed.add(key_name)
                self._key_states[key_name] = True

                if key_name in self._callbacks:
                    for callback in self._callbacks[key_name]:
                        callback(event)

        return event

    def _create_event(self, key: int) -> InputEvent:
        """Create an input event from a key code."""
        event = InputEvent(
            key_code=KeyCode.NONE,
            character='',
            timestamp=time.time()
        )

        key_mapping = {
            curses.KEY_UP: KeyCode.UP,
            curses.KEY_DOWN: KeyCode.DOWN,
            curses.KEY_LEFT: KeyCode.LEFT,
            curses.KEY_RIGHT: KeyCode.RIGHT,
            curses.KEY_ENTER: KeyCode.ENTER,
            10: KeyCode.ENTER,
            13: KeyCode.ENTER,
            27: KeyCode.ESCAPE,
            32: KeyCode.SPACE,
            9: KeyCode.TAB,
            curses.KEY_BACKSPACE: KeyCode.BACKSPACE,
            127: KeyCode.BACKSPACE,
            curses.KEY_DC: KeyCode.DELETE,
            curses.KEY_HOME: KeyCode.HOME,
            curses.KEY_END: KeyCode.END,
            curses.KEY_PPAGE: KeyCode.PAGE_UP,
            curses.KEY_NPAGE: KeyCode.PAGE_DOWN,
            curses.KEY_F1: KeyCode.F1,
            curses.KEY_F2: KeyCode.F2,
            curses.KEY_F3: KeyCode.F3,
            curses.KEY_F4: KeyCode.F4,
            curses.KEY_F5: KeyCode.F5,
            curses.KEY_F6: KeyCode.F6,
            curses.KEY_F7: KeyCode.F7,
            curses.KEY_F8: KeyCode.F8,
            curses.KEY_F9: KeyCode.F9,
            curses.KEY_F10: KeyCode.F10,
            curses.KEY_F11: KeyCode.F11,
            curses.KEY_F12: KeyCode.F12,
        }

        if key in key_mapping:
            event.key_code = key_mapping[key]
        elif 48 <= key <= 57:
            event.character = chr(key)
            numpad_mapping = {
                48: KeyCode.NUMPAD_0, 49: KeyCode.NUMPAD_1,
                50: KeyCode.NUMPAD_2, 51: KeyCode.NUMPAD_3,
                52: KeyCode.NUMPAD_4, 53: KeyCode.NUMPAD_5,
                54: KeyCode.NUMPAD_6, 55: KeyCode.NUMPAD_7,
                56: KeyCode.NUMPAD_8, 57: KeyCode.NUMPAD_9,
            }
            event.key_code = numpad_mapping.get(key, KeyCode.NONE)
        elif 32 <= key <= 126:
            event.character = chr(key)

        return event

    def is_key_down(self, key: str) -> bool:
        """Check if a key is currently held down."""
        return self._key_states.get(key, False)

    def is_key_pressed(self, key: str) -> bool:
        """Check if a key was just pressed this frame."""
        return key in self._key_pressed

    def is_key_released(self, key: str) -> bool:
        """Check if a key was just released this frame."""
        return key in self._key_released

    def get_events(self) -> List[InputEvent]:
        """Get all queued events and clear the queue."""
        events = list(self._event_queue)
        self._event_queue.clear()
        return events

    def register_callback(self, key: str, callback: Callable) -> None:
        """Register a callback for a specific key."""
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)

    def unregister_callback(self, key: str, callback: Callable) -> None:
        """Unregister a callback for a specific key."""
        if key in self._callbacks and callback in self._callbacks[key]:
            self._callbacks[key].remove(callback)

    def update(self) -> None:
        """Update key states for the next frame."""
        self._key_pressed.clear()
        self._key_released.clear()

    def clear(self) -> None:
        """Clear all input state."""
        self._key_states.clear()
        self._key_pressed.clear()
        self._key_released.clear()
        self._event_queue.clear()


# =============================================================================
# DISPLAY BUFFER
# =============================================================================

@dataclass
class ColorPair:
    """A foreground/background color pair."""
    fg: Tuple[int, int, int]
    bg: Tuple[int, int, int] = (0, 0, 0)


class DisplayBuffer:
    """
    Double-buffered display for flicker-free rendering.
    """

    __slots__ = (
        'width', 'height',
        '_front_chars', '_front_colors',
        '_back_chars', '_back_colors',
        '_dirty_cells'
    )

    def __init__(self, width: int, height: int):
        """
        Initialize the display buffer.

        Args:
            width: Buffer width
            height: Buffer height
        """
        self.width = width
        self.height = height

        self._front_chars = [[' ' for _ in range(width)] for _ in range(height)]
        self._front_colors = [[None for _ in range(width)] for _ in range(height)]

        self._back_chars = [[' ' for _ in range(width)] for _ in range(height)]
        self._back_colors = [[None for _ in range(width)] for _ in range(height)]

        self._dirty_cells: Set[Tuple[int, int]] = set()

    def resize(self, width: int, height: int) -> None:
        """Resize the buffer."""
        self.width = width
        self.height = height

        self._front_chars = [[' ' for _ in range(width)] for _ in range(height)]
        self._front_colors = [[None for _ in range(width)] for _ in range(height)]
        self._back_chars = [[' ' for _ in range(width)] for _ in range(height)]
        self._back_colors = [[None for _ in range(width)] for _ in range(height)]
        self._dirty_cells.clear()

    def clear(self, char: str = ' ',
              color: Tuple[int, int, int] = None) -> None:
        """Clear the back buffer."""
        for y in range(self.height):
            for x in range(self.width):
                self._back_chars[y][x] = char
                self._back_colors[y][x] = color

    def set_char(self, x: int, y: int, char: str,
                 color: Tuple[int, int, int] = None) -> None:
        """Set a character in the back buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._back_chars[y][x] = char
            self._back_colors[y][x] = color

    def set_string(self, x: int, y: int, text: str,
                   color: Tuple[int, int, int] = None) -> None:
        """Set a string in the back buffer."""
        for i, char in enumerate(text):
            self.set_char(x + i, y, char, color)

    def get_char(self, x: int, y: int) -> Tuple[str, Optional[Tuple[int, int, int]]]:
        """Get a character and its color from the back buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._back_chars[y][x], self._back_colors[y][x]
        return ' ', None

    def swap(self) -> Set[Tuple[int, int]]:
        """
        Swap buffers and return dirty cells.

        Returns:
            Set of (x, y) coordinates that changed
        """
        self._dirty_cells.clear()

        for y in range(self.height):
            for x in range(self.width):
                if (self._back_chars[y][x] != self._front_chars[y][x] or
                    self._back_colors[y][x] != self._front_colors[y][x]):
                    self._dirty_cells.add((x, y))
                    self._front_chars[y][x] = self._back_chars[y][x]
                    self._front_colors[y][x] = self._back_colors[y][x]

        return self._dirty_cells

    def get_front_buffer(self) -> List[List[str]]:
        """Get the front buffer characters."""
        return self._front_chars

    def get_front_colors(self) -> List[List[Optional[Tuple[int, int, int]]]]:
        """Get the front buffer colors."""
        return self._front_colors

    def copy_from_renderer(self, char_buffer: List[List[str]],
                           color_buffer: List[List[Optional[Tuple[int, int, int]]]]) -> None:
        """Copy data from a renderer buffer."""
        for y in range(min(self.height, len(char_buffer))):
            for x in range(min(self.width, len(char_buffer[y]))):
                self._back_chars[y][x] = char_buffer[y][x]
                if y < len(color_buffer) and x < len(color_buffer[y]):
                    self._back_colors[y][x] = color_buffer[y][x]


# =============================================================================
# TERMINAL DISPLAY
# =============================================================================

class TerminalDisplay:
    """
    Main terminal display class using curses.

    Provides high-performance rendering with color support,
    double buffering, and input handling. Targets 60fps.
    """

    __slots__ = (
        '_screen', '_buffer', '_input',
        '_width', '_height',
        '_running', '_paused',
        '_frame_count', '_fps', '_last_fps_time',
        '_frame_times', '_target_fps',
        '_color_pairs', '_next_pair_id',
        '_has_colors', '_can_change_colors',
        '_update_callback', '_render_callback',
        '_on_resize', '_last_frame_time'
    )

    def __init__(self):
        """Initialize the terminal display."""
        if not CURSES_AVAILABLE:
            raise RuntimeError("curses module not available")

        self._screen = None
        self._buffer: Optional[DisplayBuffer] = None
        self._input = InputManager()

        self._width = 80
        self._height = 24

        self._running = False
        self._paused = False

        self._frame_count = 0
        self._fps = 0.0
        self._last_fps_time = 0.0
        self._frame_times: deque = deque(maxlen=60)
        self._target_fps = TARGET_FPS
        self._last_frame_time = 0.0

        self._color_pairs: Dict[Tuple[int, int, int], int] = {}
        self._next_pair_id = 1
        self._has_colors = False
        self._can_change_colors = False

        self._update_callback: Optional[Callable] = None
        self._render_callback: Optional[Callable] = None
        self._on_resize: Optional[Callable] = None

    @property
    def width(self) -> int:
        """Get the display width."""
        return self._width

    @property
    def height(self) -> int:
        """Get the display height."""
        return self._height

    @property
    def fps(self) -> float:
        """Get the current FPS."""
        return self._fps

    @property
    def frame_count(self) -> int:
        """Get the total frame count."""
        return self._frame_count

    @property
    def is_running(self) -> bool:
        """Check if the display is running."""
        return self._running

    @property
    def input_manager(self) -> InputManager:
        """Get the input manager."""
        return self._input

    def set_update_callback(self, callback: Callable[[float], None]) -> None:
        """Set the update callback (called each frame with dt)."""
        self._update_callback = callback

    def set_render_callback(self, callback: Callable[['TerminalDisplay'], None]) -> None:
        """Set the render callback."""
        self._render_callback = callback

    def set_resize_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set the resize callback."""
        self._on_resize = callback

    def _init_colors(self) -> None:
        """Initialize color support."""
        self._has_colors = curses.has_colors()
        if self._has_colors:
            curses.start_color()
            curses.use_default_colors()
            self._can_change_colors = curses.can_change_color()

            self._color_pairs.clear()
            self._next_pair_id = 1

    def _get_color_pair(self, color: Tuple[int, int, int]) -> int:
        """
        Get or create a color pair for the given color.

        Args:
            color: RGB color tuple (0-255 each)

        Returns:
            Curses color pair number
        """
        if not self._has_colors:
            return 0

        if color in self._color_pairs:
            return self._color_pairs[color]

        r, g, b = color
        curses_color = self._rgb_to_curses_color(r, g, b)

        if self._next_pair_id < curses.COLOR_PAIRS - 1:
            pair_id = self._next_pair_id
            self._next_pair_id += 1

            try:
                curses.init_pair(pair_id, curses_color, -1)
                self._color_pairs[color] = pair_id
                return pair_id
            except curses.error:
                return 0

        return 0

    def _rgb_to_curses_color(self, r: int, g: int, b: int) -> int:
        """Convert RGB to the nearest curses color."""
        colors = [
            (0, 0, 0, curses.COLOR_BLACK),
            (255, 0, 0, curses.COLOR_RED),
            (0, 255, 0, curses.COLOR_GREEN),
            (255, 255, 0, curses.COLOR_YELLOW),
            (0, 0, 255, curses.COLOR_BLUE),
            (255, 0, 255, curses.COLOR_MAGENTA),
            (0, 255, 255, curses.COLOR_CYAN),
            (255, 255, 255, curses.COLOR_WHITE),
        ]

        min_dist = float('inf')
        best_color = curses.COLOR_WHITE

        for cr, cg, cb, cc in colors:
            dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
            if dist < min_dist:
                min_dist = dist
                best_color = cc

        return best_color

    def _handle_resize(self) -> None:
        """Handle terminal resize."""
        self._height, self._width = self._screen.getmaxyx()
        self._height = max(1, self._height - 1)
        self._width = max(1, self._width)

        if self._buffer:
            self._buffer.resize(self._width, self._height)

        if self._on_resize:
            self._on_resize(self._width, self._height)

    def _process_input(self) -> None:
        """Process all pending input."""
        self._input.update()

        while True:
            try:
                key = self._screen.getch()
                if key == -1:
                    break

                if key == curses.KEY_RESIZE:
                    self._handle_resize()
                else:
                    self._input.process_key(key)
            except curses.error:
                break

    def clear(self, char: str = ' ',
              color: Tuple[int, int, int] = None) -> None:
        """Clear the display buffer."""
        if self._buffer:
            self._buffer.clear(char, color)

    def set_char(self, x: int, y: int, char: str,
                 color: Tuple[int, int, int] = None) -> None:
        """Set a character in the buffer."""
        if self._buffer:
            self._buffer.set_char(x, y, char, color)

    def set_string(self, x: int, y: int, text: str,
                   color: Tuple[int, int, int] = None) -> None:
        """Set a string in the buffer."""
        if self._buffer:
            self._buffer.set_string(x, y, text, color)

    def draw_buffer(self, char_buffer: List[List[str]],
                    color_buffer: List[List[Optional[Tuple[int, int, int]]]] = None) -> None:
        """Draw a buffer to the display."""
        if not self._buffer:
            return

        for y in range(min(self._height, len(char_buffer))):
            for x in range(min(self._width, len(char_buffer[y]))):
                char = char_buffer[y][x]
                color = None
                if color_buffer and y < len(color_buffer) and x < len(color_buffer[y]):
                    color = color_buffer[y][x]
                self._buffer.set_char(x, y, char, color)

    def _render(self) -> None:
        """Render the buffer to the screen."""
        if not self._buffer or not self._screen:
            return

        dirty_cells = self._buffer.swap()

        front_chars = self._buffer.get_front_buffer()
        front_colors = self._buffer.get_front_colors()

        for x, y in dirty_cells:
            if y >= self._height or x >= self._width:
                continue

            char = front_chars[y][x]
            color = front_colors[y][x]

            try:
                if color and self._has_colors:
                    pair = self._get_color_pair(color)
                    self._screen.addch(y, x, char, curses.color_pair(pair))
                else:
                    self._screen.addch(y, x, char)
            except curses.error:
                pass

        try:
            self._screen.refresh()
        except curses.error:
            pass

    def _update_fps(self, dt: float) -> None:
        """Update FPS calculation."""
        self._frame_times.append(dt)
        self._frame_count += 1

        current_time = time.time()
        if current_time - self._last_fps_time >= 1.0:
            if self._frame_times:
                avg_frame_time = sum(self._frame_times) / len(self._frame_times)
                self._fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            self._last_fps_time = current_time

    def run(self, update_callback: Callable[[float], None] = None,
            render_callback: Callable[['TerminalDisplay'], None] = None) -> None:
        """
        Run the main display loop.

        Args:
            update_callback: Called each frame with delta time
            render_callback: Called each frame for rendering
        """
        if update_callback:
            self._update_callback = update_callback
        if render_callback:
            self._render_callback = render_callback

        def main(screen):
            self._screen = screen
            self._running = True

            curses.curs_set(0)
            screen.nodelay(True)
            screen.keypad(True)

            self._init_colors()
            self._handle_resize()

            self._buffer = DisplayBuffer(self._width, self._height)

            self._last_frame_time = time.time()
            self._last_fps_time = time.time()

            try:
                while self._running:
                    current_time = time.time()
                    dt = current_time - self._last_frame_time

                    if dt < FRAME_TIME:
                        sleep_time = FRAME_TIME - dt
                        if sleep_time > MIN_FRAME_TIME:
                            time.sleep(sleep_time * 0.9)
                        continue

                    self._last_frame_time = current_time

                    self._process_input()

                    if not self._paused:
                        if self._update_callback:
                            self._update_callback(dt)

                        if self._render_callback:
                            self._render_callback(self)

                    self._render()
                    self._update_fps(dt)

            except KeyboardInterrupt:
                self._running = False

        curses.wrapper(main)

    def stop(self) -> None:
        """Stop the display loop."""
        self._running = False

    def pause(self) -> None:
        """Pause updates (rendering continues)."""
        self._paused = True

    def resume(self) -> None:
        """Resume updates."""
        self._paused = False

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self._paused = not self._paused


# =============================================================================
# SIMPLE DISPLAY (NON-CURSES FALLBACK)
# =============================================================================

class SimpleDisplay:
    """
    Simple ANSI-based display for systems without curses.
    """

    __slots__ = ('width', 'height', '_buffer', '_running')

    ANSI_CLEAR = '\033[2J'
    ANSI_HOME = '\033[H'
    ANSI_RESET = '\033[0m'

    def __init__(self, width: int = 80, height: int = 24):
        """Initialize the simple display."""
        self.width = width
        self.height = height
        self._buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self._running = False

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]

    def set_char(self, x: int, y: int, char: str) -> None:
        """Set a character in the buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._buffer[y][x] = char

    def render(self) -> None:
        """Render to stdout."""
        output = self.ANSI_HOME
        for row in self._buffer:
            output += ''.join(row) + '\n'
        sys.stdout.write(output)
        sys.stdout.flush()

    def run(self, update_callback: Callable[[float], None],
            render_callback: Callable[['SimpleDisplay'], None]) -> None:
        """Run the main loop."""
        self._running = True
        last_time = time.time()

        print(self.ANSI_CLEAR, end='')

        try:
            while self._running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                update_callback(dt)
                render_callback(self)
                self.render()

                time.sleep(max(0, FRAME_TIME - dt))
        except KeyboardInterrupt:
            self._running = False

        print(self.ANSI_RESET)

    def stop(self) -> None:
        """Stop the display loop."""
        self._running = False
