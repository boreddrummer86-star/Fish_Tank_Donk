"""
Fish Tank Donk - Transform Module
=================================

Transform and Camera systems for 3D scene management.
Provides hierarchical transformations and camera projections.
"""

import math
from typing import Optional, List, Callable
from .math3d import (
    Vector3, Matrix4, Quaternion,
    PI, DEG_TO_RAD, RAD_TO_DEG, EPSILON,
    lerp, clamp
)


# =============================================================================
# TRANSFORM CLASS
# =============================================================================

class Transform:
    """
    A 3D transform with position, rotation, and scale.

    Supports hierarchical transformations with parent-child relationships.
    Maintains local and world transformation matrices with automatic
    dirty flag management for efficient updates.
    """

    __slots__ = (
        '_position', '_rotation', '_scale',
        '_parent', '_children',
        '_local_matrix', '_world_matrix',
        '_local_dirty', '_world_dirty',
        'name'
    )

    def __init__(self, name: str = "Transform"):
        """
        Initialize a new transform.

        Args:
            name: Optional name for the transform
        """
        self._position = Vector3.zero()
        self._rotation = Quaternion.identity()
        self._scale = Vector3.one()

        self._parent: Optional['Transform'] = None
        self._children: List['Transform'] = []

        self._local_matrix: Optional[Matrix4] = None
        self._world_matrix: Optional[Matrix4] = None
        self._local_dirty = True
        self._world_dirty = True

        self.name = name

    # -------------------------------------------------------------------------
    # Position Properties
    # -------------------------------------------------------------------------

    @property
    def position(self) -> Vector3:
        """Get the local position."""
        return self._position.copy()

    @position.setter
    def position(self, value: Vector3) -> None:
        """Set the local position."""
        self._position.x = value.x
        self._position.y = value.y
        self._position.z = value.z
        self._mark_dirty()

    @property
    def world_position(self) -> Vector3:
        """Get the world position."""
        return self.world_matrix.get_translation()

    @world_position.setter
    def world_position(self, value: Vector3) -> None:
        """Set the world position."""
        if self._parent is not None:
            parent_inv = self._parent.world_matrix.inverse
            if parent_inv:
                local_pos = parent_inv.transform_point(value)
                self.position = local_pos
        else:
            self.position = value

    # -------------------------------------------------------------------------
    # Rotation Properties
    # -------------------------------------------------------------------------

    @property
    def rotation(self) -> Quaternion:
        """Get the local rotation."""
        return self._rotation.copy()

    @rotation.setter
    def rotation(self, value: Quaternion) -> None:
        """Set the local rotation."""
        self._rotation.x = value.x
        self._rotation.y = value.y
        self._rotation.z = value.z
        self._rotation.w = value.w
        self._mark_dirty()

    @property
    def euler_angles(self) -> Vector3:
        """Get the local rotation as Euler angles (radians)."""
        return self._rotation.euler_angles

    @euler_angles.setter
    def euler_angles(self, value: Vector3) -> None:
        """Set the local rotation from Euler angles (radians)."""
        self.rotation = Quaternion.from_euler(value.x, value.y, value.z)

    @property
    def euler_angles_degrees(self) -> Vector3:
        """Get the local rotation as Euler angles (degrees)."""
        angles = self._rotation.euler_angles
        return Vector3(
            angles.x * RAD_TO_DEG,
            angles.y * RAD_TO_DEG,
            angles.z * RAD_TO_DEG
        )

    @euler_angles_degrees.setter
    def euler_angles_degrees(self, value: Vector3) -> None:
        """Set the local rotation from Euler angles (degrees)."""
        self.rotation = Quaternion.from_euler(
            value.x * DEG_TO_RAD,
            value.y * DEG_TO_RAD,
            value.z * DEG_TO_RAD
        )

    @property
    def world_rotation(self) -> Quaternion:
        """Get the world rotation."""
        if self._parent is None:
            return self._rotation.copy()
        return self._parent.world_rotation * self._rotation

    @world_rotation.setter
    def world_rotation(self, value: Quaternion) -> None:
        """Set the world rotation."""
        if self._parent is not None:
            parent_inv = self._parent.world_rotation.inverse
            self.rotation = parent_inv * value
        else:
            self.rotation = value

    # -------------------------------------------------------------------------
    # Scale Properties
    # -------------------------------------------------------------------------

    @property
    def scale(self) -> Vector3:
        """Get the local scale."""
        return self._scale.copy()

    @scale.setter
    def scale(self, value: Vector3) -> None:
        """Set the local scale."""
        self._scale.x = value.x
        self._scale.y = value.y
        self._scale.z = value.z
        self._mark_dirty()

    @property
    def lossy_scale(self) -> Vector3:
        """Get the approximate world scale."""
        return self.world_matrix.get_scale()

    # -------------------------------------------------------------------------
    # Direction Properties
    # -------------------------------------------------------------------------

    @property
    def forward(self) -> Vector3:
        """Get the forward direction in world space."""
        return self.world_rotation.forward

    @property
    def back(self) -> Vector3:
        """Get the back direction in world space."""
        return -self.forward

    @property
    def up(self) -> Vector3:
        """Get the up direction in world space."""
        return self.world_rotation.up

    @property
    def down(self) -> Vector3:
        """Get the down direction in world space."""
        return -self.up

    @property
    def right(self) -> Vector3:
        """Get the right direction in world space."""
        return self.world_rotation.right

    @property
    def left(self) -> Vector3:
        """Get the left direction in world space."""
        return -self.right

    # -------------------------------------------------------------------------
    # Matrix Properties
    # -------------------------------------------------------------------------

    @property
    def local_matrix(self) -> Matrix4:
        """Get the local transformation matrix."""
        if self._local_dirty or self._local_matrix is None:
            self._local_matrix = Matrix4.trs(
                self._position,
                self._rotation,
                self._scale
            )
            self._local_dirty = False
        return self._local_matrix

    @property
    def world_matrix(self) -> Matrix4:
        """Get the world transformation matrix."""
        if self._world_dirty or self._world_matrix is None:
            if self._parent is None:
                self._world_matrix = self.local_matrix.copy()
            else:
                self._world_matrix = self._parent.world_matrix * self.local_matrix
            self._world_dirty = False
        return self._world_matrix

    @property
    def world_to_local_matrix(self) -> Matrix4:
        """Get the matrix that transforms from world to local space."""
        return self.world_matrix.inverse or Matrix4.identity()

    # -------------------------------------------------------------------------
    # Hierarchy Properties
    # -------------------------------------------------------------------------

    @property
    def parent(self) -> Optional['Transform']:
        """Get the parent transform."""
        return self._parent

    @parent.setter
    def parent(self, value: Optional['Transform']) -> None:
        """Set the parent transform."""
        if self._parent == value:
            return

        if self._parent is not None:
            self._parent._children.remove(self)

        self._parent = value

        if self._parent is not None:
            self._parent._children.append(self)

        self._mark_world_dirty()

    @property
    def children(self) -> List['Transform']:
        """Get a list of child transforms."""
        return self._children.copy()

    @property
    def child_count(self) -> int:
        """Get the number of children."""
        return len(self._children)

    @property
    def root(self) -> 'Transform':
        """Get the root transform in the hierarchy."""
        current = self
        while current._parent is not None:
            current = current._parent
        return current

    # -------------------------------------------------------------------------
    # Dirty Flag Management
    # -------------------------------------------------------------------------

    def _mark_dirty(self) -> None:
        """Mark local and world matrices as dirty."""
        self._local_dirty = True
        self._mark_world_dirty()

    def _mark_world_dirty(self) -> None:
        """Mark world matrix as dirty for self and all children."""
        self._world_dirty = True
        for child in self._children:
            child._mark_world_dirty()

    # -------------------------------------------------------------------------
    # Hierarchy Operations
    # -------------------------------------------------------------------------

    def set_parent(self, parent: Optional['Transform'],
                   world_position_stays: bool = True) -> None:
        """
        Set the parent transform.

        Args:
            parent: New parent transform
            world_position_stays: If True, maintain world position
        """
        if world_position_stays:
            world_pos = self.world_position
            world_rot = self.world_rotation
            world_scale = self.lossy_scale

        self.parent = parent

        if world_position_stays:
            self.world_position = world_pos
            self.world_rotation = world_rot

    def detach_children(self) -> None:
        """Detach all children from this transform."""
        for child in self._children[:]:
            child.parent = None

    def get_child(self, index: int) -> Optional['Transform']:
        """Get a child by index."""
        if 0 <= index < len(self._children):
            return self._children[index]
        return None

    def find(self, name: str) -> Optional['Transform']:
        """Find a child by name (not recursive)."""
        for child in self._children:
            if child.name == name:
                return child
        return None

    def find_recursive(self, name: str) -> Optional['Transform']:
        """Find a descendant by name (recursive)."""
        for child in self._children:
            if child.name == name:
                return child
            result = child.find_recursive(name)
            if result is not None:
                return result
        return None

    def is_child_of(self, parent: 'Transform') -> bool:
        """Check if this is a child of the given transform."""
        current = self._parent
        while current is not None:
            if current == parent:
                return True
            current = current._parent
        return False

    # -------------------------------------------------------------------------
    # Transformation Operations
    # -------------------------------------------------------------------------

    def translate(self, translation: Vector3, space: str = 'self') -> None:
        """
        Move the transform.

        Args:
            translation: Translation vector
            space: 'self' for local space, 'world' for world space
        """
        if space == 'world':
            self.position = self._position + translation
        else:
            self.position = self._position + self._rotation.rotate_vector(translation)

    def rotate(self, euler_angles: Vector3, space: str = 'self') -> None:
        """
        Rotate the transform by Euler angles.

        Args:
            euler_angles: Rotation in radians (x, y, z)
            space: 'self' for local space, 'world' for world space
        """
        rotation = Quaternion.from_euler(euler_angles.x, euler_angles.y, euler_angles.z)
        if space == 'world':
            self.rotation = rotation * self._rotation
        else:
            self.rotation = self._rotation * rotation

    def rotate_around(self, point: Vector3, axis: Vector3, angle: float) -> None:
        """
        Rotate around a point in world space.

        Args:
            point: Point to rotate around
            axis: Axis of rotation
            angle: Angle in radians
        """
        rotation = Quaternion.from_axis_angle(axis, angle)

        offset = self.world_position - point
        offset = rotation.rotate_vector(offset)
        self.world_position = point + offset
        self.world_rotation = rotation * self.world_rotation

    def look_at(self, target: Vector3, up: Vector3 = None) -> None:
        """
        Look at a target position.

        Args:
            target: Position to look at
            up: Up direction (default is Vector3.up())
        """
        if up is None:
            up = Vector3.up()

        direction = target - self.world_position
        if direction.magnitude_squared < EPSILON:
            return

        self.world_rotation = Quaternion.look_rotation(direction, up)

    def scale_by(self, scale_factor: Vector3) -> None:
        """
        Scale the transform by a factor.

        Args:
            scale_factor: Scale multiplier
        """
        self.scale = Vector3(
            self._scale.x * scale_factor.x,
            self._scale.y * scale_factor.y,
            self._scale.z * scale_factor.z
        )

    # -------------------------------------------------------------------------
    # Space Conversion
    # -------------------------------------------------------------------------

    def transform_point(self, point: Vector3) -> Vector3:
        """Transform a point from local to world space."""
        return self.world_matrix.transform_point(point)

    def transform_direction(self, direction: Vector3) -> Vector3:
        """Transform a direction from local to world space."""
        return self.world_rotation.rotate_vector(direction)

    def transform_vector(self, vector: Vector3) -> Vector3:
        """Transform a vector from local to world space (includes scale)."""
        return self.world_matrix.transform_direction(vector)

    def inverse_transform_point(self, point: Vector3) -> Vector3:
        """Transform a point from world to local space."""
        return self.world_to_local_matrix.transform_point(point)

    def inverse_transform_direction(self, direction: Vector3) -> Vector3:
        """Transform a direction from world to local space."""
        return self.world_rotation.inverse.rotate_vector(direction)

    def inverse_transform_vector(self, vector: Vector3) -> Vector3:
        """Transform a vector from world to local space (includes scale)."""
        return self.world_to_local_matrix.transform_direction(vector)

    # -------------------------------------------------------------------------
    # Reset Operations
    # -------------------------------------------------------------------------

    def reset(self) -> None:
        """Reset to identity transform."""
        self._position = Vector3.zero()
        self._rotation = Quaternion.identity()
        self._scale = Vector3.one()
        self._mark_dirty()

    def reset_local(self) -> None:
        """Reset local transform only."""
        self._position = Vector3.zero()
        self._rotation = Quaternion.identity()
        self._scale = Vector3.one()
        self._mark_dirty()

    # -------------------------------------------------------------------------
    # Copy Operations
    # -------------------------------------------------------------------------

    def copy_from(self, other: 'Transform') -> None:
        """Copy transform values from another transform."""
        self._position = other._position.copy()
        self._rotation = other._rotation.copy()
        self._scale = other._scale.copy()
        self._mark_dirty()

    def copy(self) -> 'Transform':
        """Create a copy of this transform (without hierarchy)."""
        result = Transform(self.name + "_copy")
        result._position = self._position.copy()
        result._rotation = self._rotation.copy()
        result._scale = self._scale.copy()
        result._mark_dirty()
        return result

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def set_position_and_rotation(self, position: Vector3,
                                   rotation: Quaternion) -> None:
        """Set both position and rotation at once."""
        self._position.x = position.x
        self._position.y = position.y
        self._position.z = position.z
        self._rotation.x = rotation.x
        self._rotation.y = rotation.y
        self._rotation.z = rotation.z
        self._rotation.w = rotation.w
        self._mark_dirty()

    def get_position_and_rotation(self) -> tuple:
        """Get both position and rotation."""
        return self.position, self.rotation

    def traverse(self, callback: Callable[['Transform'], None]) -> None:
        """
        Traverse the transform hierarchy depth-first.

        Args:
            callback: Function to call for each transform
        """
        callback(self)
        for child in self._children:
            child.traverse(callback)

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (f"Transform('{self.name}', "
                f"pos={self._position}, "
                f"rot={self._rotation}, "
                f"scale={self._scale})")

    def __str__(self) -> str:
        return f"Transform '{self.name}'"


# =============================================================================
# CAMERA CLASS
# =============================================================================

class Camera:
    """
    A 3D camera for rendering scenes.

    Supports perspective and orthographic projections with
    configurable field of view, aspect ratio, and clipping planes.
    Integrates with Transform for positioning and orientation.
    """

    __slots__ = (
        'transform',
        '_fov', '_aspect', '_near', '_far',
        '_ortho_size', '_is_orthographic',
        '_projection_matrix', '_projection_dirty',
        '_view_matrix_cache', '_view_dirty',
        'clear_color', 'depth'
    )

    def __init__(self, name: str = "Camera"):
        """
        Initialize a new camera.

        Args:
            name: Optional name for the camera
        """
        self.transform = Transform(name)

        self._fov = 60.0 * DEG_TO_RAD
        self._aspect = 16.0 / 9.0
        self._near = 0.1
        self._far = 1000.0

        self._ortho_size = 5.0
        self._is_orthographic = False

        self._projection_matrix: Optional[Matrix4] = None
        self._projection_dirty = True

        self._view_matrix_cache: Optional[Matrix4] = None
        self._view_dirty = True

        self.clear_color = (0.0, 0.0, 0.0, 1.0)
        self.depth = 0

    # -------------------------------------------------------------------------
    # Projection Properties
    # -------------------------------------------------------------------------

    @property
    def fov(self) -> float:
        """Get the field of view in radians."""
        return self._fov

    @fov.setter
    def fov(self, value: float) -> None:
        """Set the field of view in radians."""
        self._fov = clamp(value, 0.01, PI - 0.01)
        self._projection_dirty = True

    @property
    def fov_degrees(self) -> float:
        """Get the field of view in degrees."""
        return self._fov * RAD_TO_DEG

    @fov_degrees.setter
    def fov_degrees(self, value: float) -> None:
        """Set the field of view in degrees."""
        self.fov = value * DEG_TO_RAD

    @property
    def aspect(self) -> float:
        """Get the aspect ratio."""
        return self._aspect

    @aspect.setter
    def aspect(self, value: float) -> None:
        """Set the aspect ratio."""
        self._aspect = max(0.01, value)
        self._projection_dirty = True

    @property
    def near_clip(self) -> float:
        """Get the near clipping plane distance."""
        return self._near

    @near_clip.setter
    def near_clip(self, value: float) -> None:
        """Set the near clipping plane distance."""
        self._near = max(0.001, value)
        self._projection_dirty = True

    @property
    def far_clip(self) -> float:
        """Get the far clipping plane distance."""
        return self._far

    @far_clip.setter
    def far_clip(self, value: float) -> None:
        """Set the far clipping plane distance."""
        self._far = max(self._near + 0.01, value)
        self._projection_dirty = True

    @property
    def orthographic_size(self) -> float:
        """Get the orthographic size (half-height of view)."""
        return self._ortho_size

    @orthographic_size.setter
    def orthographic_size(self, value: float) -> None:
        """Set the orthographic size."""
        self._ortho_size = max(0.01, value)
        self._projection_dirty = True

    @property
    def is_orthographic(self) -> bool:
        """Check if using orthographic projection."""
        return self._is_orthographic

    @is_orthographic.setter
    def is_orthographic(self, value: bool) -> None:
        """Set projection mode."""
        self._is_orthographic = value
        self._projection_dirty = True

    # -------------------------------------------------------------------------
    # Matrix Properties
    # -------------------------------------------------------------------------

    @property
    def projection_matrix(self) -> Matrix4:
        """Get the projection matrix."""
        if self._projection_dirty or self._projection_matrix is None:
            if self._is_orthographic:
                half_height = self._ortho_size
                half_width = half_height * self._aspect
                self._projection_matrix = Matrix4.orthographic(
                    -half_width, half_width,
                    -half_height, half_height,
                    self._near, self._far
                )
            else:
                self._projection_matrix = Matrix4.perspective(
                    self._fov, self._aspect,
                    self._near, self._far
                )
            self._projection_dirty = False
        return self._projection_matrix

    @property
    def view_matrix(self) -> Matrix4:
        """Get the view matrix."""
        world_matrix = self.transform.world_matrix
        return world_matrix.inverse or Matrix4.identity()

    @property
    def view_projection_matrix(self) -> Matrix4:
        """Get the combined view-projection matrix."""
        return self.projection_matrix * self.view_matrix

    # -------------------------------------------------------------------------
    # Position and Orientation
    # -------------------------------------------------------------------------

    @property
    def position(self) -> Vector3:
        """Get the camera world position."""
        return self.transform.world_position

    @position.setter
    def position(self, value: Vector3) -> None:
        """Set the camera world position."""
        self.transform.world_position = value

    @property
    def rotation(self) -> Quaternion:
        """Get the camera world rotation."""
        return self.transform.world_rotation

    @rotation.setter
    def rotation(self, value: Quaternion) -> None:
        """Set the camera world rotation."""
        self.transform.world_rotation = value

    @property
    def forward(self) -> Vector3:
        """Get the camera forward direction."""
        return self.transform.forward

    @property
    def up(self) -> Vector3:
        """Get the camera up direction."""
        return self.transform.up

    @property
    def right(self) -> Vector3:
        """Get the camera right direction."""
        return self.transform.right

    # -------------------------------------------------------------------------
    # Camera Operations
    # -------------------------------------------------------------------------

    def look_at(self, target: Vector3, up: Vector3 = None) -> None:
        """
        Point the camera at a target.

        Args:
            target: Position to look at
            up: Up direction (default is Vector3.up())
        """
        self.transform.look_at(target, up)

    def set_look_at(self, eye: Vector3, target: Vector3,
                    up: Vector3 = None) -> None:
        """
        Set camera position and look at a target.

        Args:
            eye: Camera position
            target: Position to look at
            up: Up direction (default is Vector3.up())
        """
        self.transform.world_position = eye
        self.look_at(target, up)

    # -------------------------------------------------------------------------
    # Coordinate Transformation
    # -------------------------------------------------------------------------

    def world_to_screen(self, world_pos: Vector3,
                        screen_width: int, screen_height: int) -> Optional[tuple]:
        """
        Transform a world position to screen coordinates.

        Args:
            world_pos: Position in world space
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels

        Returns:
            Tuple of (x, y, depth) or None if behind camera
        """
        view_pos = self.view_matrix.transform_point(world_pos)

        if view_pos.z >= 0:
            return None

        clip_pos = self.projection_matrix.transform_point(view_pos)

        ndc_x = clip_pos.x
        ndc_y = clip_pos.y

        screen_x = (ndc_x + 1.0) * 0.5 * screen_width
        screen_y = (1.0 - ndc_y) * 0.5 * screen_height

        return (screen_x, screen_y, -view_pos.z)

    def screen_to_world_ray(self, screen_x: float, screen_y: float,
                            screen_width: int, screen_height: int) -> tuple:
        """
        Create a ray from screen coordinates.

        Args:
            screen_x: X coordinate on screen
            screen_y: Y coordinate on screen
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels

        Returns:
            Tuple of (origin, direction) vectors
        """
        ndc_x = (screen_x / screen_width) * 2.0 - 1.0
        ndc_y = 1.0 - (screen_y / screen_height) * 2.0

        inv_proj = self.projection_matrix.inverse
        inv_view = self.view_matrix.inverse

        if inv_proj is None or inv_view is None:
            return self.position, self.forward

        near_point = Vector3(ndc_x, ndc_y, -1.0)
        far_point = Vector3(ndc_x, ndc_y, 1.0)

        near_world = inv_view.transform_point(
            inv_proj.transform_point(near_point)
        )
        far_world = inv_view.transform_point(
            inv_proj.transform_point(far_point)
        )

        direction = (far_world - near_world).normalized

        return near_world, direction

    def screen_point_to_ray(self, screen_pos: Vector3,
                            screen_width: int, screen_height: int) -> tuple:
        """
        Create a ray from a screen point (convenience method).

        Args:
            screen_pos: Screen position (z is ignored)
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels

        Returns:
            Tuple of (origin, direction) vectors
        """
        return self.screen_to_world_ray(
            screen_pos.x, screen_pos.y,
            screen_width, screen_height
        )

    # -------------------------------------------------------------------------
    # Frustum Methods
    # -------------------------------------------------------------------------

    def get_frustum_corners(self, distance: float) -> List[Vector3]:
        """
        Get the corners of the view frustum at a given distance.

        Args:
            distance: Distance from camera

        Returns:
            List of 4 corner positions [top-left, top-right, bottom-right, bottom-left]
        """
        if self._is_orthographic:
            half_height = self._ortho_size
            half_width = half_height * self._aspect
        else:
            half_height = distance * math.tan(self._fov / 2.0)
            half_width = half_height * self._aspect

        forward = self.forward
        right = self.right
        up = self.up
        center = self.position + forward * distance

        corners = [
            center + up * half_height - right * half_width,
            center + up * half_height + right * half_width,
            center - up * half_height + right * half_width,
            center - up * half_height - right * half_width
        ]

        return corners

    def is_point_visible(self, point: Vector3) -> bool:
        """
        Check if a point is within the camera's view frustum.

        Args:
            point: Point to check

        Returns:
            True if the point is visible
        """
        result = self.world_to_screen(point, 100, 100)
        if result is None:
            return False

        x, y, depth = result
        return (0 <= x <= 100 and 0 <= y <= 100 and
                self._near <= depth <= self._far)

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        mode = "orthographic" if self._is_orthographic else "perspective"
        return (f"Camera('{self.transform.name}', {mode}, "
                f"fov={self._fov * RAD_TO_DEG:.1f}deg, "
                f"aspect={self._aspect:.2f})")

    def __str__(self) -> str:
        return f"Camera '{self.transform.name}'"


# =============================================================================
# TRANSFORM ANIMATION HELPERS
# =============================================================================

class TransformAnimator:
    """
    Helper class for animating transforms.

    Provides smooth interpolation between transform states
    with various easing functions.
    """

    __slots__ = (
        'transform',
        '_start_position', '_end_position',
        '_start_rotation', '_end_rotation',
        '_start_scale', '_end_scale',
        '_duration', '_elapsed',
        '_ease_func', '_is_playing'
    )

    def __init__(self, transform: Transform):
        """
        Initialize the animator.

        Args:
            transform: Transform to animate
        """
        self.transform = transform
        self._start_position = Vector3.zero()
        self._end_position = Vector3.zero()
        self._start_rotation = Quaternion.identity()
        self._end_rotation = Quaternion.identity()
        self._start_scale = Vector3.one()
        self._end_scale = Vector3.one()
        self._duration = 1.0
        self._elapsed = 0.0
        self._ease_func = lambda t: t
        self._is_playing = False

    def animate_to(self, position: Vector3 = None,
                   rotation: Quaternion = None,
                   scale: Vector3 = None,
                   duration: float = 1.0,
                   ease_func: Callable[[float], float] = None) -> None:
        """
        Start animating to a target state.

        Args:
            position: Target position (or None to keep current)
            rotation: Target rotation (or None to keep current)
            scale: Target scale (or None to keep current)
            duration: Animation duration in seconds
            ease_func: Easing function (default is linear)
        """
        self._start_position = self.transform.position
        self._start_rotation = self.transform.rotation
        self._start_scale = self.transform.scale

        self._end_position = position if position else self._start_position.copy()
        self._end_rotation = rotation if rotation else self._start_rotation.copy()
        self._end_scale = scale if scale else self._start_scale.copy()

        self._duration = max(0.001, duration)
        self._elapsed = 0.0
        self._ease_func = ease_func if ease_func else (lambda t: t)
        self._is_playing = True

    def update(self, dt: float) -> bool:
        """
        Update the animation.

        Args:
            dt: Delta time in seconds

        Returns:
            True if animation is still playing
        """
        if not self._is_playing:
            return False

        self._elapsed += dt
        t = min(1.0, self._elapsed / self._duration)
        eased_t = self._ease_func(t)

        self.transform.position = self._start_position.lerp(
            self._end_position, eased_t
        )
        self.transform.rotation = self._start_rotation.slerp(
            self._end_rotation, eased_t
        )
        self.transform.scale = self._start_scale.lerp(
            self._end_scale, eased_t
        )

        if t >= 1.0:
            self._is_playing = False
            return False

        return True

    def stop(self) -> None:
        """Stop the animation."""
        self._is_playing = False

    @property
    def is_playing(self) -> bool:
        """Check if animation is playing."""
        return self._is_playing

    @property
    def progress(self) -> float:
        """Get the animation progress (0-1)."""
        return min(1.0, self._elapsed / self._duration)
