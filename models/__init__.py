"""
Fish Tank Donk - 3D Creature Models
===================================

Wireframe 3D models for aquatic creatures.
Each creature includes detailed geometry and rigging points.
"""

from .base_creature import BaseCreature, CreatureState, Skeleton, Bone

# Lazy imports to avoid circular dependencies
_shark_model = None
_jellyfish_model = None


def get_shark_model():
    """Get the SharkModel class (lazy import)."""
    global _shark_model
    if _shark_model is None:
        from .shark import SharkModel
        _shark_model = SharkModel
    return _shark_model


def get_jellyfish_model():
    """Get the JellyfishModel class (lazy import)."""
    global _jellyfish_model
    if _jellyfish_model is None:
        from .jellyfish import JellyfishModel
        _jellyfish_model = JellyfishModel
    return _jellyfish_model


# Direct imports (will be available after modules are created)
try:
    from .shark import SharkModel
except ImportError:
    SharkModel = None

try:
    from .jellyfish import JellyfishModel
except ImportError:
    JellyfishModel = None


__all__ = [
    'BaseCreature', 'CreatureState', 'Skeleton', 'Bone',
    'SharkModel', 'JellyfishModel',
    'get_shark_model', 'get_jellyfish_model'
]
