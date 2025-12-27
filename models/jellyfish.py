"""
Fish Tank Donk - Jellyfish Model
================================

A detailed wireframe 3D jellyfish with bioluminescent coloring.
Features the iconic "bloop bloop bloop" swimming animation
like a Super Mario Blooper - 3 bloops every 30 seconds.

Keypad 2 to summon.
"""

import math
import os
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

# Ensure parent directory is in path for imports
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from core.math3d import (
    Vector3, Matrix4, Quaternion,
    lerp, clamp, smoothstep, ease_in_out_cubic,
    ease_out_elastic, ease_in_quad, ease_out_quad,
    PI, TAU, EPSILON, DEG_TO_RAD
)
from core.transform import Transform
from core.renderer import Mesh, Vertex, Edge
from core.colors import (
    ColorManager, HSVColor, ColorGradient, Colors,
    GradientType
)
from models.base_creature import (
    BaseCreature, CreatureState, Skeleton, Bone,
    SkinnedVertex, VertexWeight
)


# =============================================================================
# JELLYFISH CONFIGURATION
# =============================================================================

@dataclass
class JellyfishConfig:
    """Configuration parameters for the jellyfish model."""

    # Bell (dome) parameters
    bell_radius: float = 1.2
    bell_height: float = 0.9
    bell_segments: int = 16          # Horizontal segments around bell
    bell_rings: int = 8              # Vertical rings on bell
    bell_thickness: float = 0.08     # Thickness of bell edge

    # Oral arms (frilly inner parts)
    oral_arm_count: int = 4
    oral_arm_length: float = 0.6
    oral_arm_segments: int = 6
    oral_arm_waviness: float = 0.15

    # Tentacles
    tentacle_count: int = 16
    tentacle_length: float = 2.5
    tentacle_segments: int = 12
    tentacle_waviness: float = 0.3
    tentacle_taper: float = 0.7      # How much tentacles thin at end

    # Animation timing
    bloop_interval: float = 30.0     # Seconds between bloop sequences
    bloop_count: int = 3             # Number of bloops per sequence
    bloop_duration: float = 0.8      # Duration of single bloop
    bloop_pause: float = 0.3         # Pause between bloops
    bloop_contract: float = 0.4      # How much bell contracts (0-1)
    bloop_rise: float = 0.5          # How much jellyfish rises per bloop

    # Idle animation
    idle_bob_speed: float = 0.5      # Gentle bobbing speed
    idle_bob_amount: float = 0.1     # Bobbing amplitude
    idle_pulse_speed: float = 0.3    # Bell pulsing speed
    idle_pulse_amount: float = 0.05  # Bell pulse amplitude
    idle_tentacle_sway: float = 0.2  # Tentacle swaying amount
    idle_drift_speed: float = 0.1    # Horizontal drift speed

    # Entrance animation
    entrance_duration: float = 3.0
    entrance_start_scale: float = 0.0
    entrance_start_y: float = -5.0

    # Colors
    bell_hue: float = 300.0          # Pink/purple
    glow_intensity: float = 0.8
    tentacle_glow: float = 0.6


# =============================================================================
# BLOOP STATE MACHINE
# =============================================================================

class BloopPhase(Enum):
    """Phases of the bloop animation."""
    IDLE = auto()
    CONTRACT = auto()      # Bell contracts
    EXPAND = auto()        # Bell expands rapidly (propulsion)
    GLIDE = auto()         # Gliding after bloop
    PAUSE = auto()         # Pause between bloops


@dataclass
class BloopState:
    """Tracks the current bloop animation state."""
    phase: BloopPhase = BloopPhase.IDLE
    phase_time: float = 0.0
    bloop_count: int = 0           # Current bloop in sequence
    total_bloops: int = 3          # Total bloops in sequence
    contract_amount: float = 0.0   # Current contraction (0-1)
    velocity_y: float = 0.0        # Upward velocity from bloop

    def reset(self):
        """Reset to idle state."""
        self.phase = BloopPhase.IDLE
        self.phase_time = 0.0
        self.bloop_count = 0
        self.contract_amount = 0.0
        self.velocity_y = 0.0


# =============================================================================
# JELLYFISH MODEL
# =============================================================================

class JellyfishModel(BaseCreature):
    """
    A detailed wireframe 3D jellyfish.

    Features:
    - Dome-shaped bell with multiple rings
    - Oral arms (inner frilly parts)
    - Long flowing tentacles
    - Bioluminescent color gradient
    - "Bloop bloop bloop" swimming (3x every 30 seconds)
    - Idle floating with gentle pulsing
    - Skeletal animation for all parts

    Summon with keypad 2.
    """

    __slots__ = (
        'config', 'bloop_state',
        '_bell_rings_indices', '_oral_arm_indices', '_tentacle_indices',
        '_bell_apex_idx', '_bell_base_ring',
        '_original_positions', '_time_offset',
        '_entrance_start_pos', '_target_pos'
    )

    def __init__(self, config: JellyfishConfig = None):
        """
        Initialize the jellyfish.

        Args:
            config: Configuration parameters (uses defaults if None)
        """
        super().__init__("Jellyfish")

        self.config = config or JellyfishConfig()
        self.bloop_state = BloopState(total_bloops=self.config.bloop_count)

        # Geometry indices for animation
        self._bell_rings_indices: List[List[int]] = []
        self._oral_arm_indices: List[List[int]] = []
        self._tentacle_indices: List[List[int]] = []
        self._bell_apex_idx: int = -1
        self._bell_base_ring: List[int] = []

        # Store original positions for deformation
        self._original_positions: List[Vector3] = []

        # Random time offset for variety
        self._time_offset = 0.0

        # Position tracking
        self._entrance_start_pos = Vector3.zero()
        self._target_pos = Vector3.zero()

    # -------------------------------------------------------------------------
    # Configuration Methods
    # -------------------------------------------------------------------------

    def get_special_interval(self) -> float:
        """Bloop every 30 seconds."""
        return self.config.bloop_interval

    def get_special_duration(self) -> float:
        """Total duration of bloop sequence."""
        return (self.config.bloop_duration + self.config.bloop_pause) * self.config.bloop_count

    def get_entrance_duration(self) -> float:
        """Entrance animation duration."""
        return self.config.entrance_duration

    # -------------------------------------------------------------------------
    # Skeleton Building
    # -------------------------------------------------------------------------

    def _build_skeleton(self) -> None:
        """Build the jellyfish skeleton for animation."""

        # Root bone at center of bell
        root = self.skeleton.add_bone(
            "root",
            parent_idx=-1,
            position=Vector3.zero(),
            length=0.1
        )

        # Bell bone (controls dome expansion/contraction)
        bell = self.skeleton.add_bone(
            "bell",
            parent_idx=root,
            position=Vector3(0, 0.2, 0),
            length=self.config.bell_height
        )

        # Bell apex bone
        apex = self.skeleton.add_bone(
            "bell_apex",
            parent_idx=bell,
            position=Vector3(0, self.config.bell_height * 0.8, 0),
            length=0.2
        )

        # Bell rim bone (for edge deformation)
        rim = self.skeleton.add_bone(
            "bell_rim",
            parent_idx=bell,
            position=Vector3(0, -0.1, 0),
            length=self.config.bell_radius
        )

        # Oral arm bones (4 arms)
        for i in range(self.config.oral_arm_count):
            angle = (i / self.config.oral_arm_count) * TAU
            x = math.cos(angle) * 0.2
            z = math.sin(angle) * 0.2

            arm_root = self.skeleton.add_bone(
                f"oral_arm_{i}_root",
                parent_idx=bell,
                position=Vector3(x, -0.15, z),
                length=0.15
            )

            arm_mid = self.skeleton.add_bone(
                f"oral_arm_{i}_mid",
                parent_idx=arm_root,
                position=Vector3(0, -self.config.oral_arm_length * 0.4, 0),
                length=self.config.oral_arm_length * 0.3
            )

            arm_tip = self.skeleton.add_bone(
                f"oral_arm_{i}_tip",
                parent_idx=arm_mid,
                position=Vector3(0, -self.config.oral_arm_length * 0.3, 0),
                length=self.config.oral_arm_length * 0.3
            )

        # Tentacle bones (16 tentacles, each with 3 segments)
        for i in range(self.config.tentacle_count):
            angle = (i / self.config.tentacle_count) * TAU
            # Distribute around bell rim
            x = math.cos(angle) * self.config.bell_radius * 0.85
            z = math.sin(angle) * self.config.bell_radius * 0.85

            tent_root = self.skeleton.add_bone(
                f"tentacle_{i}_root",
                parent_idx=rim,
                position=Vector3(x, -0.1, z),
                length=self.config.tentacle_length * 0.15
            )

            tent_upper = self.skeleton.add_bone(
                f"tentacle_{i}_upper",
                parent_idx=tent_root,
                position=Vector3(0, -self.config.tentacle_length * 0.25, 0),
                length=self.config.tentacle_length * 0.25
            )

            tent_mid = self.skeleton.add_bone(
                f"tentacle_{i}_mid",
                parent_idx=tent_upper,
                position=Vector3(0, -self.config.tentacle_length * 0.25, 0),
                length=self.config.tentacle_length * 0.25
            )

            tent_lower = self.skeleton.add_bone(
                f"tentacle_{i}_lower",
                parent_idx=tent_mid,
                position=Vector3(0, -self.config.tentacle_length * 0.25, 0),
                length=self.config.tentacle_length * 0.25
            )

            tent_tip = self.skeleton.add_bone(
                f"tentacle_{i}_tip",
                parent_idx=tent_lower,
                position=Vector3(0, -self.config.tentacle_length * 0.1, 0),
                length=self.config.tentacle_length * 0.1
            )

    # -------------------------------------------------------------------------
    # Mesh Building - Bell (Dome)
    # -------------------------------------------------------------------------

    def _build_mesh(self) -> None:
        """Build the complete jellyfish mesh."""
        self._build_bell()
        self._build_oral_arms()
        self._build_tentacles()

        # Store original positions
        self._original_positions = [
            v.position.copy() for v in self.mesh.vertices
        ]

        # Calculate normals
        self.mesh.calculate_normals()

    def _build_bell(self) -> None:
        """Build the bell (dome) of the jellyfish."""
        cfg = self.config

        # Create apex vertex
        apex_pos = Vector3(0, cfg.bell_height, 0)
        self._bell_apex_idx = self.add_vertex_with_weight(apex_pos, "bell_apex", 1.0)

        self._bell_rings_indices = []

        # Build rings from top to bottom
        for ring in range(cfg.bell_rings):
            ring_vertices = []

            # Parameter t goes from 0 (apex) to 1 (rim)
            t = (ring + 1) / cfg.bell_rings

            # Bell profile: starts narrow, bulges out, curves back in slightly
            # Using a modified sine curve for natural bell shape
            bulge = math.sin(t * PI * 0.9) ** 0.7
            radius = cfg.bell_radius * bulge

            # Height decreases as we go down
            # Slight inward curve at bottom edge
            height = cfg.bell_height * (1.0 - t * 0.9)
            if t > 0.8:
                # Curve inward at rim
                height -= (t - 0.8) * 0.3

            # Determine bone weight based on ring position
            if t < 0.3:
                bone_name = "bell_apex"
                weight = 1.0 - t / 0.3
            elif t < 0.7:
                bone_name = "bell"
                weight = 1.0
            else:
                bone_name = "bell_rim"
                weight = (t - 0.7) / 0.3

            # Create vertices around this ring
            for seg in range(cfg.bell_segments):
                angle = (seg / cfg.bell_segments) * TAU

                x = math.cos(angle) * radius
                z = math.sin(angle) * radius

                pos = Vector3(x, height, z)

                # Multi-weight for smooth deformation
                if t < 0.3:
                    weights = [("bell_apex", 1.0 - t/0.3), ("bell", t/0.3)]
                elif t > 0.7:
                    weights = [("bell", 1.0 - (t-0.7)/0.3), ("bell_rim", (t-0.7)/0.3)]
                else:
                    weights = [("bell", 1.0)]

                idx = self.add_vertex_multi_weight(pos, weights)
                ring_vertices.append(idx)

            self._bell_rings_indices.append(ring_vertices)

        # Store base ring for tentacle attachment reference
        self._bell_base_ring = self._bell_rings_indices[-1].copy()

        # Connect apex to first ring
        first_ring = self._bell_rings_indices[0]
        for i, v_idx in enumerate(first_ring):
            self.mesh.add_edge(self._bell_apex_idx, v_idx)

        # Connect each ring to itself (horizontal edges)
        for ring_verts in self._bell_rings_indices:
            self.create_edge_chain(ring_verts, closed=True)

        # Connect rings to each other (vertical edges)
        for i in range(len(self._bell_rings_indices) - 1):
            ring1 = self._bell_rings_indices[i]
            ring2 = self._bell_rings_indices[i + 1]

            for j in range(len(ring1)):
                # Vertical edge
                self.mesh.add_edge(ring1[j], ring2[j])

                # Diagonal for structure (every other)
                if j % 2 == 0:
                    next_j = (j + 1) % len(ring2)
                    self.mesh.add_edge(ring1[j], ring2[next_j])

        # Add inner bell structure (thickness lines)
        self._build_bell_inner_structure()

    def _build_bell_inner_structure(self) -> None:
        """Build the inner structure of the bell for visual depth."""
        cfg = self.config

        # Create inner rings (smaller, offset inward)
        inner_scale = 1.0 - cfg.bell_thickness * 2

        for ring_idx, outer_ring in enumerate(self._bell_rings_indices):
            if ring_idx % 2 != 0:  # Every other ring for performance
                continue

            t = (ring_idx + 1) / cfg.bell_rings

            for seg_idx in range(0, len(outer_ring), 2):  # Every other segment
                outer_v = self.mesh.vertices[outer_ring[seg_idx]]

                # Create inner vertex
                inner_pos = Vector3(
                    outer_v.position.x * inner_scale,
                    outer_v.position.y + cfg.bell_thickness,
                    outer_v.position.z * inner_scale
                )

                # Use same weighting as outer
                if t < 0.3:
                    weights = [("bell_apex", 1.0 - t/0.3), ("bell", t/0.3)]
                elif t > 0.7:
                    weights = [("bell", 1.0 - (t-0.7)/0.3), ("bell_rim", (t-0.7)/0.3)]
                else:
                    weights = [("bell", 1.0)]

                inner_idx = self.add_vertex_multi_weight(inner_pos, weights)

                # Connect to outer vertex
                self.mesh.add_edge(outer_ring[seg_idx], inner_idx)

    # -------------------------------------------------------------------------
    # Mesh Building - Oral Arms
    # -------------------------------------------------------------------------

    def _build_oral_arms(self) -> None:
        """Build the oral arms (inner frilly parts)."""
        cfg = self.config

        self._oral_arm_indices = []

        for arm_idx in range(cfg.oral_arm_count):
            arm_vertices = []

            angle = (arm_idx / cfg.oral_arm_count) * TAU
            base_x = math.cos(angle) * 0.2
            base_z = math.sin(angle) * 0.2

            # Create wavy arm segments
            for seg in range(cfg.oral_arm_segments):
                t = seg / (cfg.oral_arm_segments - 1)

                # Wavy offset
                wave1 = math.sin(t * PI * 3 + arm_idx) * cfg.oral_arm_waviness
                wave2 = math.cos(t * PI * 2 + arm_idx * 0.7) * cfg.oral_arm_waviness * 0.5

                # Position along arm
                y = -0.1 - t * cfg.oral_arm_length
                x = base_x + wave1 * (1.0 - t * 0.5)
                z = base_z + wave2 * (1.0 - t * 0.5)

                pos = Vector3(x, y, z)

                # Bone weighting
                if t < 0.4:
                    bone = f"oral_arm_{arm_idx}_root"
                elif t < 0.7:
                    bone = f"oral_arm_{arm_idx}_mid"
                else:
                    bone = f"oral_arm_{arm_idx}_tip"

                idx = self.add_vertex_with_weight(pos, bone, 1.0)
                arm_vertices.append(idx)

                # Add frilly side vertices for width
                if seg > 0 and seg < cfg.oral_arm_segments - 1:
                    frill_width = 0.08 * (1.0 - t * 0.7)

                    # Left frill
                    frill_l = Vector3(
                        x + math.cos(angle + PI/2) * frill_width,
                        y + math.sin(t * PI * 4) * 0.02,
                        z + math.sin(angle + PI/2) * frill_width
                    )
                    frill_l_idx = self.add_vertex_with_weight(frill_l, bone, 1.0)
                    self.mesh.add_edge(idx, frill_l_idx)

                    # Right frill
                    frill_r = Vector3(
                        x + math.cos(angle - PI/2) * frill_width,
                        y + math.sin(t * PI * 4 + PI) * 0.02,
                        z + math.sin(angle - PI/2) * frill_width
                    )
                    frill_r_idx = self.add_vertex_with_weight(frill_r, bone, 1.0)
                    self.mesh.add_edge(idx, frill_r_idx)

            # Connect arm vertices
            self.create_edge_chain(arm_vertices)

            self._oral_arm_indices.append(arm_vertices)

    # -------------------------------------------------------------------------
    # Mesh Building - Tentacles
    # -------------------------------------------------------------------------

    def _build_tentacles(self) -> None:
        """Build the flowing tentacles."""
        cfg = self.config

        self._tentacle_indices = []

        for tent_idx in range(cfg.tentacle_count):
            tentacle_vertices = []

            # Position around bell rim
            angle = (tent_idx / cfg.tentacle_count) * TAU
            base_x = math.cos(angle) * cfg.bell_radius * 0.85
            base_z = math.sin(angle) * cfg.bell_radius * 0.85

            # Unique phase offset for variety
            phase = tent_idx * 0.5

            for seg in range(cfg.tentacle_segments):
                t = seg / (cfg.tentacle_segments - 1)

                # Natural hanging curve with gentle waves
                # Tentacles hang down with slight outward spread
                spread = 1.0 + t * 0.3

                # Wavy motion
                wave_x = math.sin(t * PI * 2 + phase) * cfg.tentacle_waviness * t
                wave_z = math.cos(t * PI * 2.5 + phase * 0.7) * cfg.tentacle_waviness * t

                # Calculate position
                y = -0.15 - t * cfg.tentacle_length
                x = base_x * spread + wave_x
                z = base_z * spread + wave_z

                # Taper: tentacles get thinner (visual only through vertex density)

                pos = Vector3(x, y, z)

                # Bone weighting based on segment
                if t < 0.15:
                    bone = f"tentacle_{tent_idx}_root"
                elif t < 0.35:
                    bone = f"tentacle_{tent_idx}_upper"
                elif t < 0.6:
                    bone = f"tentacle_{tent_idx}_mid"
                elif t < 0.85:
                    bone = f"tentacle_{tent_idx}_lower"
                else:
                    bone = f"tentacle_{tent_idx}_tip"

                idx = self.add_vertex_with_weight(pos, bone, 1.0)
                tentacle_vertices.append(idx)

                # Add intermediate detail vertices for longer tentacles
                if seg > 0 and seg < cfg.tentacle_segments - 1 and seg % 2 == 0:
                    # Small branches
                    branch_len = 0.05 * (1.0 - t)
                    branch_angle = angle + (PI / 6) * (1 if seg % 4 == 0 else -1)

                    branch_pos = Vector3(
                        x + math.cos(branch_angle) * branch_len,
                        y + 0.02,
                        z + math.sin(branch_angle) * branch_len
                    )
                    branch_idx = self.add_vertex_with_weight(branch_pos, bone, 1.0)
                    self.mesh.add_edge(idx, branch_idx)

            # Connect tentacle vertices
            self.create_edge_chain(tentacle_vertices)

            self._tentacle_indices.append(tentacle_vertices)

    # -------------------------------------------------------------------------
    # Skin Weights Setup
    # -------------------------------------------------------------------------

    def _setup_skin_weights(self) -> None:
        """Setup is done during mesh building with add_vertex_with_weight."""
        pass

    # -------------------------------------------------------------------------
    # Color Setup
    # -------------------------------------------------------------------------

    def _setup_colors(self) -> None:
        """Setup bioluminescent jellyfish colors."""
        # Create jellyfish gradient (pink -> purple -> cyan)
        gradient = ColorGradient(GradientType.SMOOTH)
        gradient.add_stop(0.0, HSVColor(300, 0.7, 0.5))   # Deep purple
        gradient.add_stop(0.25, HSVColor(320, 0.6, 0.7))  # Pink
        gradient.add_stop(0.5, HSVColor(280, 0.5, 0.85))  # Light purple
        gradient.add_stop(0.75, HSVColor(200, 0.4, 0.9))  # Cyan
        gradient.add_stop(1.0, HSVColor(180, 0.3, 1.0))   # Bright cyan glow

        self.color_manager.set_gradient(gradient, speed=0.1)
        self.color_manager.enable_pulse(speed=1.5, amount=0.2)

    # -------------------------------------------------------------------------
    # Entrance Animation
    # -------------------------------------------------------------------------

    def _animate_entrance(self, time: float, dt: float) -> bool:
        """
        Animate the jellyfish entrance.

        Floats up from below with a gentle pulsing motion.

        Returns True when complete.
        """
        cfg = self.config
        duration = cfg.entrance_duration

        if time >= duration:
            return True

        t = time / duration
        eased_t = ease_out_elastic(min(1.0, t * 1.2))

        # Scale up from nothing
        scale = lerp(cfg.entrance_start_scale, 1.0, eased_t)
        self.transform.scale = Vector3(scale, scale, scale)

        # Rise up from below
        start_y = cfg.entrance_start_y
        target_y = self._target_pos.y if self._target_pos else 0.0
        current_y = lerp(start_y, target_y, ease_out_quad(t))

        pos = self.transform.position
        self.transform.position = Vector3(pos.x, current_y, pos.z)

        # Gentle rotation during entrance
        rotation_angle = math.sin(time * 2) * 0.1
        self.skeleton.bones[0].current_rotation = Quaternion.from_euler(
            0, rotation_angle, 0
        )

        # Pulsing bell during entrance
        pulse = math.sin(time * 4) * 0.1 * t
        self._animate_bell_contract(pulse)

        return False

    # -------------------------------------------------------------------------
    # Idle Animation
    # -------------------------------------------------------------------------

    def _animate_idle(self, time: float, dt: float) -> None:
        """
        Animate idle floating behavior.

        Gentle bobbing, slow pulsing, tentacle swaying.
        """
        cfg = self.config
        t = time + self._time_offset

        # Gentle vertical bobbing
        bob = math.sin(t * cfg.idle_bob_speed * TAU) * cfg.idle_bob_amount
        pos = self.transform.position
        base_y = self._target_pos.y if self._target_pos else pos.y
        self.transform.position = Vector3(pos.x, base_y + bob, pos.z)

        # Slow bell pulsing
        pulse = math.sin(t * cfg.idle_pulse_speed * TAU) * cfg.idle_pulse_amount
        self._animate_bell_contract(pulse)

        # Slight rotation/tilting
        tilt_x = math.sin(t * 0.3) * 0.05
        tilt_z = math.cos(t * 0.25) * 0.05
        self.skeleton.bones[0].current_rotation = Quaternion.from_euler(
            tilt_x, 0, tilt_z
        )

        # Animate tentacles swaying
        self._animate_tentacles_sway(t, cfg.idle_tentacle_sway)

        # Animate oral arms
        self._animate_oral_arms(t)

    # -------------------------------------------------------------------------
    # Special Animation (Bloop Bloop Bloop)
    # -------------------------------------------------------------------------

    def _animate_special(self, time: float, dt: float) -> bool:
        """
        Animate the "bloop bloop bloop" swimming motion.

        Like a Super Mario Blooper:
        1. Bell contracts (intake)
        2. Bell expands rapidly (propulsion)
        3. Glide upward
        4. Repeat 3 times

        Returns True when complete.
        """
        cfg = self.config
        state = self.bloop_state

        state.phase_time += dt

        # State machine for bloop animation
        if state.phase == BloopPhase.IDLE:
            # Start first bloop
            state.phase = BloopPhase.CONTRACT
            state.phase_time = 0.0
            state.bloop_count = 0

        elif state.phase == BloopPhase.CONTRACT:
            # Bell contracting - building up for propulsion
            contract_duration = cfg.bloop_duration * 0.4

            if state.phase_time >= contract_duration:
                state.phase = BloopPhase.EXPAND
                state.phase_time = 0.0
            else:
                t = state.phase_time / contract_duration
                state.contract_amount = ease_in_quad(t) * cfg.bloop_contract
                self._animate_bell_contract(state.contract_amount)

                # Tentacles pull in slightly
                self._animate_tentacles_contract(t * 0.3)

        elif state.phase == BloopPhase.EXPAND:
            # Rapid expansion - propulsion!
            expand_duration = cfg.bloop_duration * 0.3

            if state.phase_time >= expand_duration:
                state.phase = BloopPhase.GLIDE
                state.phase_time = 0.0
                state.velocity_y = cfg.bloop_rise
            else:
                t = state.phase_time / expand_duration
                # Rapid expansion with overshoot
                expand = ease_out_elastic(t) * -0.15
                state.contract_amount = expand
                self._animate_bell_contract(expand)

                # Tentacles flare out
                self._animate_tentacles_flare(t)

                # Start upward motion
                state.velocity_y = cfg.bloop_rise * ease_out_quad(t)
                pos = self.transform.position
                self.transform.position = Vector3(
                    pos.x,
                    pos.y + state.velocity_y * dt * 2,
                    pos.z
                )

        elif state.phase == BloopPhase.GLIDE:
            # Gliding after propulsion
            glide_duration = cfg.bloop_duration * 0.3

            if state.phase_time >= glide_duration:
                state.bloop_count += 1

                if state.bloop_count >= state.total_bloops:
                    # All bloops complete
                    state.reset()
                    return True
                else:
                    # Pause before next bloop
                    state.phase = BloopPhase.PAUSE
                    state.phase_time = 0.0
            else:
                t = state.phase_time / glide_duration

                # Decelerate upward motion
                state.velocity_y *= 0.95
                pos = self.transform.position
                self.transform.position = Vector3(
                    pos.x,
                    pos.y + state.velocity_y * dt,
                    pos.z
                )

                # Bell returns to normal
                state.contract_amount = lerp(state.contract_amount, 0, t)
                self._animate_bell_contract(state.contract_amount)

                # Tentacles trail behind
                self._animate_tentacles_trail(t)

        elif state.phase == BloopPhase.PAUSE:
            # Short pause between bloops
            if state.phase_time >= cfg.bloop_pause:
                state.phase = BloopPhase.CONTRACT
                state.phase_time = 0.0
            else:
                # Gentle drift
                self._animate_idle(time, dt)

        return False

    # -------------------------------------------------------------------------
    # Exit Animation
    # -------------------------------------------------------------------------

    def _animate_exit(self, time: float, dt: float) -> bool:
        """
        Animate the jellyfish exit.

        Floats upward and fades out.

        Returns True when complete.
        """
        duration = 2.0

        if time >= duration:
            return True

        t = time / duration

        # Float upward
        pos = self.transform.position
        self.transform.position = Vector3(
            pos.x,
            pos.y + dt * 2.0,
            pos.z
        )

        # Shrink
        scale = 1.0 - ease_in_quad(t)
        self.transform.scale = Vector3(scale, scale, scale)

        # Continue gentle motion
        self._animate_bell_contract(math.sin(time * 4) * 0.1)

        return False

    # -------------------------------------------------------------------------
    # Animation Helpers
    # -------------------------------------------------------------------------

    def _animate_bell_contract(self, amount: float) -> None:
        """
        Animate bell contraction/expansion.

        Args:
            amount: Contraction amount (positive = contract, negative = expand)
        """
        bell_bone = self.skeleton.get_bone("bell")
        if bell_bone:
            # Scale the bell horizontally (contract) and vertically (compress)
            scale_xy = 1.0 - amount * 0.5
            scale_y = 1.0 - amount * 0.3
            bell_bone.current_scale = Vector3(scale_xy, scale_y, scale_xy)

        rim_bone = self.skeleton.get_bone("bell_rim")
        if rim_bone:
            # Rim contracts more
            scale = 1.0 - amount * 0.7
            rim_bone.current_scale = Vector3(scale, 1.0, scale)

        apex_bone = self.skeleton.get_bone("bell_apex")
        if apex_bone:
            # Apex moves down during contraction
            apex_bone.current_position = Vector3(0, -amount * 0.2, 0)

    def _animate_tentacles_sway(self, time: float, amount: float) -> None:
        """Animate tentacles swaying gently."""
        for i in range(self.config.tentacle_count):
            phase = i * 0.4

            # Each tentacle segment sways with phase offset
            for seg_name in ['root', 'upper', 'mid', 'lower', 'tip']:
                bone = self.skeleton.get_bone(f"tentacle_{i}_{seg_name}")
                if bone:
                    seg_phase = {'root': 0, 'upper': 0.5, 'mid': 1.0, 'lower': 1.5, 'tip': 2.0}[seg_name]

                    sway_x = math.sin(time * 0.8 + phase + seg_phase) * amount * 0.1
                    sway_z = math.cos(time * 0.6 + phase * 0.7 + seg_phase) * amount * 0.1

                    bone.current_rotation = Quaternion.from_euler(sway_x, 0, sway_z)

    def _animate_tentacles_contract(self, amount: float) -> None:
        """Animate tentacles pulling inward during bloop intake."""
        for i in range(self.config.tentacle_count):
            for seg_name in ['root', 'upper', 'mid', 'lower', 'tip']:
                bone = self.skeleton.get_bone(f"tentacle_{i}_{seg_name}")
                if bone:
                    # Pull tentacles inward and up
                    seg_mult = {'root': 0.2, 'upper': 0.4, 'mid': 0.6, 'lower': 0.8, 'tip': 1.0}[seg_name]

                    pull = amount * seg_mult * 0.3
                    bone.current_rotation = Quaternion.from_euler(-pull, 0, 0)

    def _animate_tentacles_flare(self, t: float) -> None:
        """Animate tentacles flaring outward during propulsion."""
        for i in range(self.config.tentacle_count):
            angle = (i / self.config.tentacle_count) * TAU

            for seg_name in ['root', 'upper', 'mid', 'lower', 'tip']:
                bone = self.skeleton.get_bone(f"tentacle_{i}_{seg_name}")
                if bone:
                    seg_mult = {'root': 0.3, 'upper': 0.5, 'mid': 0.7, 'lower': 0.9, 'tip': 1.0}[seg_name]

                    # Flare outward
                    flare = t * seg_mult * 0.4
                    bone.current_rotation = Quaternion.from_euler(
                        flare * math.cos(angle),
                        0,
                        flare * math.sin(angle)
                    )

    def _animate_tentacles_trail(self, t: float) -> None:
        """Animate tentacles trailing behind during glide."""
        for i in range(self.config.tentacle_count):
            for seg_name in ['root', 'upper', 'mid', 'lower', 'tip']:
                bone = self.skeleton.get_bone(f"tentacle_{i}_{seg_name}")
                if bone:
                    seg_mult = {'root': 0.2, 'upper': 0.4, 'mid': 0.6, 'lower': 0.8, 'tip': 1.0}[seg_name]

                    # Trail downward
                    trail = (1.0 - t) * seg_mult * 0.2
                    bone.current_rotation = Quaternion.from_euler(trail, 0, 0)

    def _animate_oral_arms(self, time: float) -> None:
        """Animate oral arms with gentle waving."""
        for i in range(self.config.oral_arm_count):
            phase = i * 1.5

            for seg_name in ['root', 'mid', 'tip']:
                bone = self.skeleton.get_bone(f"oral_arm_{i}_{seg_name}")
                if bone:
                    seg_phase = {'root': 0, 'mid': 0.5, 'tip': 1.0}[seg_name]

                    wave_x = math.sin(time * 1.2 + phase + seg_phase) * 0.15
                    wave_z = math.cos(time * 0.9 + phase * 0.8 + seg_phase) * 0.1

                    bone.current_rotation = Quaternion.from_euler(wave_x, 0, wave_z)

    # -------------------------------------------------------------------------
    # Spawning
    # -------------------------------------------------------------------------

    def spawn(self, position: Vector3 = None) -> None:
        """Spawn the jellyfish at a position."""
        import random

        if position:
            self._target_pos = position.copy()
        else:
            self._target_pos = Vector3(
                random.uniform(-3, 3),
                random.uniform(0, 2),
                random.uniform(-2, 2)
            )

        # Start below target
        start_pos = Vector3(
            self._target_pos.x,
            self.config.entrance_start_y,
            self._target_pos.z
        )

        self._time_offset = random.uniform(0, 10)
        self.transform.position = start_pos
        self.transform.scale = Vector3.zero()

        super().spawn(start_pos)

    def __repr__(self) -> str:
        return f"JellyfishModel(state={self.state.name}, bloop_phase={self.bloop_state.phase.name})"
