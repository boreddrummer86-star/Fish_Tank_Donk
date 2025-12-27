"""
Fish Tank Donk - Core Engine
============================

A robust 3D wireframe rendering engine for terminal-based aquarium animations.
Provides mathematical primitives, transformation matrices, projection systems,
and real-time terminal rendering capabilities.

Modules:
    - math3d: 3D mathematical primitives and operations
    - transform: Transformation matrices and operations
    - renderer: Wireframe rendering engine
    - display: Terminal display management with curses
    - colors: Color management and gradient systems
"""

from .math3d import Vector3, Matrix4, Quaternion
from .transform import Transform, Camera
from .renderer import WireframeRenderer, Edge, Face
from .display import TerminalDisplay, DisplayBuffer
from .colors import ColorManager, ColorGradient, HSVColor

__all__ = [
    'Vector3', 'Matrix4', 'Quaternion',
    'Transform', 'Camera',
    'WireframeRenderer', 'Edge', 'Face',
    'TerminalDisplay', 'DisplayBuffer',
    'ColorManager', 'ColorGradient', 'HSVColor'
]

__version__ = '1.0.0'
__author__ = 'Fish Tank Donk'
