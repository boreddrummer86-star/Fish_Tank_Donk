"""
Fish Tank Donk - Base Creature Model
====================================

Abstract base class for all creature models.
Provides common functionality for mesh management,
rigging, and state handling.
"""

import math
import os
import sys
from typing import List, Dict, Optional, Tuple, Callable
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field

# Ensure parent directory is in path for imports
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from core.math3d import Vector3, Matrix4, Quaternion, lerp, clamp, EPSILON
from core.transform import Transform
from core.renderer import Mesh, Vertex, Edge
from core.colors import ColorManager, HSVColor, ColorGradient, Colors


# =============================================================================
# CREATURE STATE ENUM
# =============================================================================

class CreatureState(Enum):
    """States a creature can be in."""
    INACTIVE = auto()       # Not visible/spawned
    ENTERING = auto()       # Playing entrance animation
    IDLE = auto()           # Normal swimming/floating
    SPECIAL = auto()        # Special animation (shark attack, jellyfish bloop)
    EXITING = auto()        # Playing exit animation


# =============================================================================
# BONE/JOINT SYSTEM
# =============================================================================

@dataclass
class Bone:
    """
    A bone for skeletal animation.
    """
    name: str
    parent_idx: int = -1  # -1 for root
    local_position: Vector3 = field(default_factory=Vector3.zero)
    local_rotation: Quaternion = field(default_factory=Quaternion.identity)
    local_scale: Vector3 = field(default_factory=Vector3.one)

    # Animation state
    current_rotation: Quaternion = field(default_factory=Quaternion.identity)
    current_position: Vector3 = field(default_factory=Vector3.zero)
    current_scale: Vector3 = field(default_factory=Vector3.one)

    # Bone-specific properties
    length: float = 1.0
    weight_indices: List[int] = field(default_factory=list)  # Vertex indices this bone affects

    def get_local_matrix(self) -> Matrix4:
        """Get the local transformation matrix."""
        pos = self.local_position + self.current_position
        rot = self.local_rotation * self.current_rotation
        scale = Vector3(
            self.local_scale.x * self.current_scale.x,
            self.local_scale.y * self.current_scale.y,
            self.local_scale.z * self.current_scale.z
        )
        return Matrix4.trs(pos, rot, scale)


@dataclass
class Skeleton:
    """
    A skeleton for rigging and animation.
    """
    bones: List[Bone] = field(default_factory=list)
    bone_matrices: List[Matrix4] = field(default_factory=list)

    def add_bone(self, name: str, parent_idx: int = -1,
                 position: Vector3 = None,
                 rotation: Quaternion = None,
                 length: float = 1.0) -> int:
        """Add a bone and return its index."""
        bone = Bone(
            name=name,
            parent_idx=parent_idx,
            local_position=position or Vector3.zero(),
            local_rotation=rotation or Quaternion.identity(),
            length=length
        )
        idx = len(self.bones)
        self.bones.append(bone)
        self.bone_matrices.append(Matrix4.identity())
        return idx

    def get_bone(self, name: str) -> Optional[Bone]:
        """Get a bone by name."""
        for bone in self.bones:
            if bone.name == name:
                return bone
        return None

    def get_bone_index(self, name: str) -> int:
        """Get a bone index by name."""
        for i, bone in enumerate(self.bones):
            if bone.name == name:
                return i
        return -1

    def update_matrices(self) -> None:
        """Update all bone matrices from the hierarchy."""
        for i, bone in enumerate(self.bones):
            local = bone.get_local_matrix()
            if bone.parent_idx >= 0:
                parent = self.bone_matrices[bone.parent_idx]
                self.bone_matrices[i] = parent * local
            else:
                self.bone_matrices[i] = local

    def reset_pose(self) -> None:
        """Reset all bones to their default pose."""
        for bone in self.bones:
            bone.current_rotation = Quaternion.identity()
            bone.current_position = Vector3.zero()
            bone.current_scale = Vector3.one()
        self.update_matrices()


# =============================================================================
# VERTEX WEIGHT SYSTEM
# =============================================================================

@dataclass
class VertexWeight:
    """Weight influence of a bone on a vertex."""
    bone_idx: int
    weight: float


@dataclass
class SkinnedVertex:
    """A vertex with bone weights for skeletal animation."""
    base_position: Vector3
    weights: List[VertexWeight] = field(default_factory=list)

    def get_skinned_position(self, bone_matrices: List[Matrix4]) -> Vector3:
        """Calculate the skinned position based on bone weights."""
        if not self.weights:
            return self.base_position.copy()

        result = Vector3.zero()
        total_weight = 0.0

        for vw in self.weights:
            if vw.bone_idx >= 0 and vw.bone_idx < len(bone_matrices):
                pos = bone_matrices[vw.bone_idx].transform_point(self.base_position)
                result += pos * vw.weight
                total_weight += vw.weight

        if total_weight > EPSILON:
            result = result / total_weight
        else:
            result = self.base_position.copy()

        return result


# =============================================================================
# BASE CREATURE CLASS
# =============================================================================

class BaseCreature(ABC):
    """
    Abstract base class for all creatures.

    Provides common functionality for:
    - Mesh management
    - Skeletal animation
    - Color management
    - State machine
    - Transform hierarchy
    """

    __slots__ = (
        'name', 'transform', 'mesh', 'base_mesh',
        'skeleton', 'skinned_vertices',
        'color_manager', 'state', 'state_time',
        'visible', 'spawn_time', 'lifetime',
        '_special_timer', '_special_interval',
        '_animation_callbacks', '_on_state_change'
    )

    def __init__(self, name: str = "Creature"):
        """
        Initialize the creature.

        Args:
            name: Name of the creature
        """
        self.name = name
        self.transform = Transform(name)
        self.mesh = Mesh(name + "_mesh")
        self.base_mesh: Optional[Mesh] = None  # Original mesh for skinning

        self.skeleton = Skeleton()
        self.skinned_vertices: List[SkinnedVertex] = []

        self.color_manager = ColorManager()

        self.state = CreatureState.INACTIVE
        self.state_time = 0.0

        self.visible = False
        self.spawn_time = 0.0
        self.lifetime = 0.0

        self._special_timer = 0.0
        self._special_interval = 60.0  # Default: special every 60 seconds

        self._animation_callbacks: Dict[CreatureState, Callable] = {}
        self._on_state_change: Optional[Callable] = None

    # -------------------------------------------------------------------------
    # Abstract Methods - Must be implemented by subclasses
    # -------------------------------------------------------------------------

    @abstractmethod
    def _build_mesh(self) -> None:
        """Build the creature's mesh geometry."""
        pass

    @abstractmethod
    def _build_skeleton(self) -> None:
        """Build the creature's skeleton for animation."""
        pass

    @abstractmethod
    def _setup_skin_weights(self) -> None:
        """Setup vertex weights for skeletal deformation."""
        pass

    @abstractmethod
    def _animate_idle(self, time: float, dt: float) -> None:
        """Animate the idle state."""
        pass

    @abstractmethod
    def _animate_entrance(self, time: float, dt: float) -> bool:
        """
        Animate the entrance.
        Returns True when complete.
        """
        pass

    @abstractmethod
    def _animate_special(self, time: float, dt: float) -> bool:
        """
        Animate the special action.
        Returns True when complete.
        """
        pass

    @abstractmethod
    def _animate_exit(self, time: float, dt: float) -> bool:
        """
        Animate the exit.
        Returns True when complete.
        """
        pass

    @abstractmethod
    def get_special_interval(self) -> float:
        """Get the interval between special animations."""
        pass

    @abstractmethod
    def get_special_duration(self) -> float:
        """Get the duration of the special animation."""
        pass

    @abstractmethod
    def get_entrance_duration(self) -> float:
        """Get the duration of the entrance animation."""
        pass

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize the creature (call after construction)."""
        self._build_skeleton()
        self._build_mesh()
        self._setup_skin_weights()

        # Store base mesh for skinning reference
        self.base_mesh = self.mesh.copy()

        # Setup color
        self._setup_colors()

        # Set intervals
        self._special_interval = self.get_special_interval()

    def _setup_colors(self) -> None:
        """Setup default colors - can be overridden."""
        self.color_manager.set_base_color(Colors.WHITE)

    # -------------------------------------------------------------------------
    # State Management
    # -------------------------------------------------------------------------

    def set_state(self, new_state: CreatureState) -> None:
        """
        Change the creature's state.

        Args:
            new_state: The new state
        """
        if new_state == self.state:
            return

        old_state = self.state
        self.state = new_state
        self.state_time = 0.0

        if new_state == CreatureState.ENTERING:
            self.visible = True
            self._special_timer = 0.0
        elif new_state == CreatureState.INACTIVE:
            self.visible = False

        if self._on_state_change:
            self._on_state_change(old_state, new_state)

    def spawn(self, position: Vector3 = None) -> None:
        """
        Spawn the creature with entrance animation.

        Args:
            position: Starting position (optional)
        """
        if position:
            self.transform.position = position

        self.spawn_time = 0.0
        self.lifetime = 0.0
        self._special_timer = 0.0
        self.set_state(CreatureState.ENTERING)

    def despawn(self) -> None:
        """Despawn the creature with exit animation."""
        self.set_state(CreatureState.EXITING)

    def force_despawn(self) -> None:
        """Immediately despawn without animation."""
        self.set_state(CreatureState.INACTIVE)

    def trigger_special(self) -> None:
        """Trigger the special animation immediately."""
        if self.state == CreatureState.IDLE:
            self.set_state(CreatureState.SPECIAL)

    # -------------------------------------------------------------------------
    # Update Loop
    # -------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """
        Update the creature.

        Args:
            dt: Delta time in seconds
        """
        if self.state == CreatureState.INACTIVE:
            return

        self.state_time += dt
        self.lifetime += dt

        # Update color animations
        self.color_manager.update(dt)

        # State machine
        if self.state == CreatureState.ENTERING:
            if self._animate_entrance(self.state_time, dt):
                self.set_state(CreatureState.IDLE)

        elif self.state == CreatureState.IDLE:
            self._animate_idle(self.state_time, dt)

            # Check for special animation trigger
            self._special_timer += dt
            if self._special_timer >= self._special_interval:
                self._special_timer = 0.0
                self.set_state(CreatureState.SPECIAL)

        elif self.state == CreatureState.SPECIAL:
            if self._animate_special(self.state_time, dt):
                self.set_state(CreatureState.IDLE)

        elif self.state == CreatureState.EXITING:
            if self._animate_exit(self.state_time, dt):
                self.set_state(CreatureState.INACTIVE)

        # Apply skeletal animation
        self._apply_skinning()

    def _apply_skinning(self) -> None:
        """Apply skeletal deformation to the mesh."""
        if not self.base_mesh or not self.skinned_vertices:
            return

        self.skeleton.update_matrices()

        for i, sv in enumerate(self.skinned_vertices):
            if i < len(self.mesh.vertices):
                new_pos = sv.get_skinned_position(self.skeleton.bone_matrices)
                self.mesh.vertices[i].position = new_pos

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_render_color(self, vertex_index: int = 0) -> Tuple[int, int, int]:
        """
        Get the color for rendering.

        Args:
            vertex_index: Optional vertex index for gradient coloring

        Returns:
            RGB color tuple
        """
        if self.mesh.vertices and vertex_index < len(self.mesh.vertices):
            # Calculate position along creature for gradient
            bounds_min, bounds_max = self.mesh.get_bounds()
            size = bounds_max - bounds_min
            if size.z > EPSILON:
                pos = self.mesh.vertices[vertex_index].position
                t = (pos.z - bounds_min.z) / size.z
                return self.color_manager.get_color_at_position(t)

        return self.color_manager.current_rgb

    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    def set_state_change_callback(self, callback: Callable) -> None:
        """Set callback for state changes."""
        self._on_state_change = callback

    def set_animation_callback(self, state: CreatureState,
                               callback: Callable) -> None:
        """Set callback for specific animation state."""
        self._animation_callbacks[state] = callback

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def add_vertex_with_weight(self, position: Vector3,
                                bone_name: str,
                                weight: float = 1.0) -> int:
        """
        Add a vertex with bone weight.

        Args:
            position: Vertex position
            bone_name: Name of bone to attach to
            weight: Weight influence (0-1)

        Returns:
            Vertex index
        """
        idx = self.mesh.add_vertex(position)

        bone_idx = self.skeleton.get_bone_index(bone_name)

        sv = SkinnedVertex(
            base_position=position.copy(),
            weights=[VertexWeight(bone_idx, weight)] if bone_idx >= 0 else []
        )
        self.skinned_vertices.append(sv)

        # Add vertex index to bone's influence list
        if bone_idx >= 0:
            self.skeleton.bones[bone_idx].weight_indices.append(idx)

        return idx

    def add_vertex_multi_weight(self, position: Vector3,
                                 weights: List[Tuple[str, float]]) -> int:
        """
        Add a vertex with multiple bone weights.

        Args:
            position: Vertex position
            weights: List of (bone_name, weight) tuples

        Returns:
            Vertex index
        """
        idx = self.mesh.add_vertex(position)

        vertex_weights = []
        for bone_name, weight in weights:
            bone_idx = self.skeleton.get_bone_index(bone_name)
            if bone_idx >= 0:
                vertex_weights.append(VertexWeight(bone_idx, weight))
                self.skeleton.bones[bone_idx].weight_indices.append(idx)

        sv = SkinnedVertex(
            base_position=position.copy(),
            weights=vertex_weights
        )
        self.skinned_vertices.append(sv)

        return idx

    def create_edge_chain(self, vertex_indices: List[int],
                          color: Tuple[int, int, int] = None,
                          closed: bool = False) -> List[int]:
        """
        Create a chain of edges connecting vertices.

        Args:
            vertex_indices: List of vertex indices to connect
            color: Edge color
            closed: Whether to close the loop

        Returns:
            List of edge indices
        """
        edges = []
        for i in range(len(vertex_indices) - 1):
            edge_idx = self.mesh.add_edge(
                vertex_indices[i],
                vertex_indices[i + 1],
                color
            )
            edges.append(edge_idx)

        if closed and len(vertex_indices) > 2:
            edge_idx = self.mesh.add_edge(
                vertex_indices[-1],
                vertex_indices[0],
                color
            )
            edges.append(edge_idx)

        return edges

    def create_ring(self, center: Vector3, radius: float,
                    segments: int, normal: Vector3,
                    bone_name: str = None,
                    weight: float = 1.0) -> List[int]:
        """
        Create a ring of vertices.

        Args:
            center: Center of the ring
            radius: Ring radius
            segments: Number of segments
            normal: Ring normal direction
            bone_name: Bone to attach to (optional)
            weight: Bone weight

        Returns:
            List of vertex indices
        """
        # Create rotation to align Z-up ring with the normal
        up = Vector3.up()
        if abs(normal.dot(up)) > 0.99:
            up = Vector3.forward()

        right = normal.cross(up).normalized
        actual_up = right.cross(normal).normalized

        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            offset = right * (math.cos(angle) * radius) + actual_up * (math.sin(angle) * radius)
            pos = center + offset

            if bone_name:
                idx = self.add_vertex_with_weight(pos, bone_name, weight)
            else:
                idx = self.mesh.add_vertex(pos)
                self.skinned_vertices.append(SkinnedVertex(pos.copy()))

            vertices.append(idx)

        return vertices

    def connect_rings(self, ring1: List[int], ring2: List[int],
                      color: Tuple[int, int, int] = None) -> List[int]:
        """
        Connect two rings with edges.

        Args:
            ring1: First ring vertex indices
            ring2: Second ring vertex indices
            color: Edge color

        Returns:
            List of edge indices
        """
        edges = []
        n = min(len(ring1), len(ring2))

        for i in range(n):
            # Longitudinal edges
            edges.append(self.mesh.add_edge(ring1[i], ring2[i], color))

            # Diagonal edges for structure
            next_i = (i + 1) % n
            edges.append(self.mesh.add_edge(ring1[i], ring2[next_i], color))

        return edges

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}', state={self.state.name})"
