#!/usr/bin/env python3
"""
Fish Tank Donk v2.0 - Main Controller
=====================================

3D Wireframe Aquarium Simulator with keypad-summoned creatures.

Controls:
    [1] - Summon Shark (5s animation every 60s)
    [2] - Summon Jellyfish (3x bloop every 30s)
    [ESC/Q] - Exit

Run with: python3 fish_tank.py
"""

import os
import sys
import time
import math
import random
from typing import List, Dict, Optional

# Add project root to path
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.math3d import Vector3, Quaternion, lerp
from core.transform import Transform, Camera
from core.renderer import WireframeRenderer, Mesh
from core.display import TerminalDisplay, KeyCode
from core.colors import HSVColor, ColorGradient, Colors
from models.base_creature import CreatureState
from models.jellyfish import JellyfishModel

# Try to import shark if available
try:
    from models.shark import SharkModel
    SHARK_AVAILABLE = True
except ImportError:
    SHARK_AVAILABLE = False
    SharkModel = None

from icon_v2 import LOGO_V2_SMALL, VERSION, get_version_string


# =============================================================================
# FISH TANK CONFIGURATION
# =============================================================================

class TankConfig:
    """Fish tank configuration."""
    # Tank dimensions
    width: float = 12.0
    height: float = 8.0
    depth: float = 6.0

    # Camera
    camera_distance: float = 10.0
    camera_fov: float = 60.0

    # Background
    water_color = (10, 30, 60)
    bubble_count: int = 20

    # Creatures
    max_sharks: int = 3
    max_jellyfish: int = 5


# =============================================================================
# BUBBLE PARTICLE
# =============================================================================

class Bubble:
    """A simple bubble particle."""

    def __init__(self, tank_width: float, tank_height: float, tank_depth: float):
        self.x = random.uniform(-tank_width/2, tank_width/2)
        self.y = random.uniform(-tank_height/2, -tank_height/4)
        self.z = random.uniform(-tank_depth/2, tank_depth/2)
        self.speed = random.uniform(0.5, 1.5)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.size = random.choice(['·', '°', 'o', 'O'])
        self.tank_height = tank_height

    def update(self, dt: float) -> None:
        """Update bubble position."""
        self.y += self.speed * dt
        self.x += math.sin(self.y * 2 + self.wobble_phase) * 0.02

        # Reset when reaching top
        if self.y > self.tank_height / 2:
            self.y = -self.tank_height / 2
            self.x = random.uniform(-6, 6)


# =============================================================================
# FISH TANK CONTROLLER
# =============================================================================

class FishTank:
    """
    Main fish tank controller.

    Manages creatures, rendering, and input.
    """

    def __init__(self):
        """Initialize the fish tank."""
        self.config = TankConfig()

        # Display and rendering
        self.display: Optional[TerminalDisplay] = None
        self.renderer: Optional[WireframeRenderer] = None
        self.camera: Optional[Camera] = None

        # Creatures
        self.sharks: List = []
        self.jellyfish: List[JellyfishModel] = []

        # Particles
        self.bubbles: List[Bubble] = []

        # State
        self.running = False
        self.time = 0.0
        self.show_help = True
        self.show_fps = True

        # Stats
        self.frame_count = 0

    def initialize(self) -> None:
        """Initialize all components."""
        # Create bubbles
        for _ in range(self.config.bubble_count):
            self.bubbles.append(Bubble(
                self.config.width,
                self.config.height,
                self.config.depth
            ))

    def summon_shark(self) -> None:
        """Summon a shark (keypad 1)."""
        if not SHARK_AVAILABLE:
            return

        if len(self.sharks) >= self.config.max_sharks:
            # Remove oldest
            if self.sharks:
                self.sharks[0].despawn()
                self.sharks.pop(0)

        shark = SharkModel()
        shark.initialize()
        shark.spawn(Vector3(
            random.uniform(-4, 4),
            random.uniform(-1, 2),
            random.uniform(-2, 2)
        ))
        self.sharks.append(shark)

    def summon_jellyfish(self) -> None:
        """Summon a jellyfish (keypad 2)."""
        if len(self.jellyfish) >= self.config.max_jellyfish:
            # Remove oldest
            if self.jellyfish:
                self.jellyfish[0].despawn()
                self.jellyfish.pop(0)

        jf = JellyfishModel()
        jf.initialize()
        jf.spawn(Vector3(
            random.uniform(-4, 4),
            random.uniform(-1, 2),
            random.uniform(-2, 2)
        ))
        self.jellyfish.append(jf)

    def update(self, dt: float) -> None:
        """Update the fish tank."""
        self.time += dt
        self.frame_count += 1

        # Update bubbles
        for bubble in self.bubbles:
            bubble.update(dt)

        # Update sharks
        for shark in self.sharks[:]:
            shark.update(dt)
            if shark.state == CreatureState.INACTIVE:
                self.sharks.remove(shark)

        # Update jellyfish
        for jf in self.jellyfish[:]:
            jf.update(dt)
            if jf.state == CreatureState.INACTIVE:
                self.jellyfish.remove(jf)

    def render(self, display: 'TerminalDisplay') -> None:
        """Render the fish tank."""
        width = display.width
        height = display.height

        # Clear with water color
        display.clear(' ')

        # Draw tank border
        self._draw_tank_border(display, width, height)

        # Draw bubbles
        self._draw_bubbles(display, width, height)

        # Draw creatures info
        self._draw_creature_status(display, width, height)

        # Draw help text
        if self.show_help:
            self._draw_help(display, width, height)

        # Draw FPS
        if self.show_fps:
            fps_text = f"FPS: {display.fps:.0f}"
            display.set_string(width - len(fps_text) - 2, 1, fps_text, (100, 100, 100))

    def _draw_tank_border(self, display: 'TerminalDisplay', w: int, h: int) -> None:
        """Draw the tank border."""
        # Top border
        display.set_string(0, 0, "╔" + "═" * (w - 2) + "╗", (50, 100, 150))
        # Bottom border
        display.set_string(0, h - 1, "╚" + "═" * (w - 2) + "╝", (50, 100, 150))
        # Side borders
        for y in range(1, h - 1):
            display.set_char(0, y, "║", (50, 100, 150))
            display.set_char(w - 1, y, "║", (50, 100, 150))

        # Title
        title = f" Fish Tank Donk v{VERSION} "
        title_x = (w - len(title)) // 2
        display.set_string(title_x, 0, title, (100, 200, 255))

    def _draw_bubbles(self, display: 'TerminalDisplay', w: int, h: int) -> None:
        """Draw bubble particles."""
        for bubble in self.bubbles:
            # Convert 3D to screen position
            screen_x = int((bubble.x / self.config.width + 0.5) * (w - 4)) + 2
            screen_y = int((1 - (bubble.y / self.config.height + 0.5)) * (h - 4)) + 2

            if 2 <= screen_x < w - 2 and 2 <= screen_y < h - 2:
                # Color based on height
                brightness = int(100 + (bubble.y / self.config.height + 0.5) * 155)
                color = (brightness // 2, brightness, brightness)
                display.set_char(screen_x, screen_y, bubble.size, color)

    def _draw_creature_status(self, display: 'TerminalDisplay', w: int, h: int) -> None:
        """Draw creature status indicators."""
        y = 2

        # Shark status
        shark_text = f"🦈 Sharks: {len(self.sharks)}"
        if not SHARK_AVAILABLE:
            shark_text += " (not loaded)"
        display.set_string(2, y, shark_text, (150, 150, 180))

        # Jellyfish status
        y += 1
        jf_text = f"🪼 Jellyfish: {len(self.jellyfish)}"
        display.set_string(2, y, jf_text, (255, 150, 200))

        # Show active creature states
        y += 2
        for jf in self.jellyfish:
            state_text = f"  JF: {jf.state.name}"
            if jf.state == CreatureState.SPECIAL:
                state_text += f" (bloop {jf.bloop_state.bloop_count + 1}/3)"
            display.set_string(2, y, state_text, (200, 100, 255))
            y += 1
            if y > h - 5:
                break

    def _draw_help(self, display: 'TerminalDisplay', w: int, h: int) -> None:
        """Draw help text."""
        help_lines = [
            "─── Controls ───",
            "[1] Summon Shark",
            "[2] Summon Jellyfish",
            "[H] Toggle Help",
            "[ESC/Q] Quit",
        ]

        x = w - 22
        y = 2

        for line in help_lines:
            if y < h - 2:
                display.set_string(x, y, line, (100, 150, 100))
                y += 1

    def handle_input(self, display: 'TerminalDisplay') -> None:
        """Handle keyboard input."""
        input_mgr = display.input_manager

        for event in input_mgr.get_events():
            # Number keys for summoning
            if event.character == '1':
                self.summon_shark()
            elif event.character == '2':
                self.summon_jellyfish()

            # Toggle help
            elif event.character.lower() == 'h':
                self.show_help = not self.show_help

            # Toggle FPS
            elif event.character.lower() == 'f':
                self.show_fps = not self.show_fps

            # Quit
            elif event.key_code == KeyCode.ESCAPE or event.character.lower() == 'q':
                display.stop()

    def run(self) -> None:
        """Run the fish tank."""
        print(LOGO_V2_SMALL)
        print(get_version_string())
        print("\nStarting Fish Tank... Press any key.")
        print("Controls: [1] Shark, [2] Jellyfish, [ESC] Quit\n")

        self.initialize()

        def update_callback(dt: float) -> None:
            self.update(dt)
            self.handle_input(self.display)

        def render_callback(display: 'TerminalDisplay') -> None:
            self.display = display
            self.render(display)

        display = TerminalDisplay()
        self.display = display

        try:
            display.run(update_callback, render_callback)
        except KeyboardInterrupt:
            pass

        print("\nThanks for using Fish Tank Donk!")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    tank = FishTank()
    tank.run()


if __name__ == "__main__":
    main()
