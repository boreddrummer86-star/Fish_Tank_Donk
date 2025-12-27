"""
Fish Tank Donk - 3D Mathematics Module
======================================

Comprehensive 3D mathematical primitives for wireframe rendering.
Includes Vector3, Matrix4, and Quaternion classes with full
operation support for transformations, rotations, and projections.
"""

import math
from typing import Union, Tuple, List, Optional
from dataclasses import dataclass
from functools import lru_cache


# =============================================================================
# CONSTANTS
# =============================================================================

PI = math.pi
TAU = 2.0 * PI
HALF_PI = PI / 2.0
QUARTER_PI = PI / 4.0
DEG_TO_RAD = PI / 180.0
RAD_TO_DEG = 180.0 / PI
EPSILON = 1e-10


# =============================================================================
# VECTOR3 CLASS
# =============================================================================

class Vector3:
    """
    A 3D vector class with comprehensive mathematical operations.

    Supports all standard vector operations including dot product,
    cross product, normalization, interpolation, and transformation.
    Optimized for performance with __slots__ and cached properties.
    """

    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """
        Initialize a 3D vector.

        Args:
            x: X component (default 0.0)
            y: Y component (default 0.0)
            z: Z component (default 0.0)
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def zero(cls) -> 'Vector3':
        """Create a zero vector (0, 0, 0)."""
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def one(cls) -> 'Vector3':
        """Create a unit vector (1, 1, 1)."""
        return cls(1.0, 1.0, 1.0)

    @classmethod
    def up(cls) -> 'Vector3':
        """Create an up vector (0, 1, 0)."""
        return cls(0.0, 1.0, 0.0)

    @classmethod
    def down(cls) -> 'Vector3':
        """Create a down vector (0, -1, 0)."""
        return cls(0.0, -1.0, 0.0)

    @classmethod
    def left(cls) -> 'Vector3':
        """Create a left vector (-1, 0, 0)."""
        return cls(-1.0, 0.0, 0.0)

    @classmethod
    def right(cls) -> 'Vector3':
        """Create a right vector (1, 0, 0)."""
        return cls(1.0, 0.0, 0.0)

    @classmethod
    def forward(cls) -> 'Vector3':
        """Create a forward vector (0, 0, 1)."""
        return cls(0.0, 0.0, 1.0)

    @classmethod
    def back(cls) -> 'Vector3':
        """Create a back vector (0, 0, -1)."""
        return cls(0.0, 0.0, -1.0)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float]) -> 'Vector3':
        """Create a vector from a tuple."""
        return cls(t[0], t[1], t[2])

    @classmethod
    def from_list(cls, lst: List[float]) -> 'Vector3':
        """Create a vector from a list."""
        return cls(lst[0], lst[1], lst[2])

    @classmethod
    def from_spherical(cls, radius: float, theta: float, phi: float) -> 'Vector3':
        """
        Create a vector from spherical coordinates.

        Args:
            radius: Distance from origin
            theta: Azimuthal angle (radians)
            phi: Polar angle (radians)
        """
        sin_phi = math.sin(phi)
        return cls(
            radius * sin_phi * math.cos(theta),
            radius * math.cos(phi),
            radius * sin_phi * math.sin(theta)
        )

    @classmethod
    def from_cylindrical(cls, radius: float, theta: float, height: float) -> 'Vector3':
        """
        Create a vector from cylindrical coordinates.

        Args:
            radius: Distance from Y axis
            theta: Angle around Y axis (radians)
            height: Y coordinate
        """
        return cls(
            radius * math.cos(theta),
            height,
            radius * math.sin(theta)
        )

    @classmethod
    def random_unit(cls) -> 'Vector3':
        """Create a random unit vector on the unit sphere."""
        import random
        theta = random.uniform(0, TAU)
        phi = math.acos(random.uniform(-1, 1))
        return cls.from_spherical(1.0, theta, phi)

    @classmethod
    def random_in_sphere(cls, radius: float = 1.0) -> 'Vector3':
        """Create a random vector inside a sphere."""
        import random
        r = radius * (random.random() ** (1/3))
        return cls.random_unit() * r

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def magnitude(self) -> float:
        """Get the magnitude (length) of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def magnitude_squared(self) -> float:
        """Get the squared magnitude (faster, no sqrt)."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    @property
    def normalized(self) -> 'Vector3':
        """Get a normalized copy of this vector."""
        mag = self.magnitude
        if mag < EPSILON:
            return Vector3.zero()
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    @property
    def tuple(self) -> Tuple[float, float, float]:
        """Get the vector as a tuple."""
        return (self.x, self.y, self.z)

    @property
    def list(self) -> List[float]:
        """Get the vector as a list."""
        return [self.x, self.y, self.z]

    # -------------------------------------------------------------------------
    # Basic Operations
    # -------------------------------------------------------------------------

    def copy(self) -> 'Vector3':
        """Create a copy of this vector."""
        return Vector3(self.x, self.y, self.z)

    def set(self, x: float, y: float, z: float) -> 'Vector3':
        """Set all components of the vector."""
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        return self

    def normalize(self) -> 'Vector3':
        """Normalize this vector in place."""
        mag = self.magnitude
        if mag > EPSILON:
            self.x /= mag
            self.y /= mag
            self.z /= mag
        return self

    def negate(self) -> 'Vector3':
        """Negate this vector in place."""
        self.x = -self.x
        self.y = -self.y
        self.z = -self.z
        return self

    def abs(self) -> 'Vector3':
        """Get a vector with absolute values of components."""
        return Vector3(abs(self.x), abs(self.y), abs(self.z))

    def floor(self) -> 'Vector3':
        """Get a vector with floored components."""
        return Vector3(math.floor(self.x), math.floor(self.y), math.floor(self.z))

    def ceil(self) -> 'Vector3':
        """Get a vector with ceiling components."""
        return Vector3(math.ceil(self.x), math.ceil(self.y), math.ceil(self.z))

    def round(self, decimals: int = 0) -> 'Vector3':
        """Get a vector with rounded components."""
        return Vector3(
            round(self.x, decimals),
            round(self.y, decimals),
            round(self.z, decimals)
        )

    # -------------------------------------------------------------------------
    # Vector Operations
    # -------------------------------------------------------------------------

    def dot(self, other: 'Vector3') -> float:
        """
        Calculate the dot product with another vector.

        Args:
            other: The other vector

        Returns:
            The dot product scalar
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        """
        Calculate the cross product with another vector.

        Args:
            other: The other vector

        Returns:
            The cross product vector
        """
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def distance_to(self, other: 'Vector3') -> float:
        """Calculate the distance to another vector."""
        return (self - other).magnitude

    def distance_squared_to(self, other: 'Vector3') -> float:
        """Calculate the squared distance to another vector."""
        return (self - other).magnitude_squared

    def angle_to(self, other: 'Vector3') -> float:
        """
        Calculate the angle between this and another vector.

        Returns:
            Angle in radians
        """
        dot = self.dot(other)
        mag_product = self.magnitude * other.magnitude
        if mag_product < EPSILON:
            return 0.0
        cos_angle = max(-1.0, min(1.0, dot / mag_product))
        return math.acos(cos_angle)

    def signed_angle_to(self, other: 'Vector3', axis: 'Vector3') -> float:
        """
        Calculate the signed angle between vectors around an axis.

        Args:
            other: The other vector
            axis: The axis to measure rotation around

        Returns:
            Signed angle in radians
        """
        cross = self.cross(other)
        angle = self.angle_to(other)
        if cross.dot(axis) < 0:
            angle = -angle
        return angle

    def project_onto(self, other: 'Vector3') -> 'Vector3':
        """Project this vector onto another vector."""
        other_mag_sq = other.magnitude_squared
        if other_mag_sq < EPSILON:
            return Vector3.zero()
        scalar = self.dot(other) / other_mag_sq
        return other * scalar

    def project_onto_plane(self, normal: 'Vector3') -> 'Vector3':
        """Project this vector onto a plane defined by its normal."""
        return self - self.project_onto(normal)

    def reflect(self, normal: 'Vector3') -> 'Vector3':
        """Reflect this vector around a normal."""
        return self - normal * (2.0 * self.dot(normal))

    def refract(self, normal: 'Vector3', eta: float) -> Optional['Vector3']:
        """
        Refract this vector through a surface.

        Args:
            normal: Surface normal
            eta: Ratio of indices of refraction

        Returns:
            Refracted vector or None for total internal reflection
        """
        cos_i = -self.dot(normal)
        sin_t2 = eta * eta * (1.0 - cos_i * cos_i)
        if sin_t2 > 1.0:
            return None
        cos_t = math.sqrt(1.0 - sin_t2)
        return self * eta + normal * (eta * cos_i - cos_t)

    # -------------------------------------------------------------------------
    # Interpolation
    # -------------------------------------------------------------------------

    def lerp(self, other: 'Vector3', t: float) -> 'Vector3':
        """
        Linear interpolation to another vector.

        Args:
            other: Target vector
            t: Interpolation factor (0-1)

        Returns:
            Interpolated vector
        """
        return Vector3(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t
        )

    def slerp(self, other: 'Vector3', t: float) -> 'Vector3':
        """
        Spherical linear interpolation to another vector.

        Args:
            other: Target vector
            t: Interpolation factor (0-1)

        Returns:
            Spherically interpolated vector
        """
        dot = max(-1.0, min(1.0, self.normalized.dot(other.normalized)))
        theta = math.acos(dot) * t
        relative = (other - self * dot).normalized
        return self * math.cos(theta) + relative * math.sin(theta)

    def move_towards(self, target: 'Vector3', max_distance: float) -> 'Vector3':
        """
        Move towards a target by a maximum distance.

        Args:
            target: Target vector
            max_distance: Maximum distance to move

        Returns:
            New position vector
        """
        diff = target - self
        dist = diff.magnitude
        if dist <= max_distance or dist < EPSILON:
            return target.copy()
        return self + diff / dist * max_distance

    def smooth_damp(self, target: 'Vector3', velocity: 'Vector3',
                    smooth_time: float, dt: float,
                    max_speed: float = float('inf')) -> Tuple['Vector3', 'Vector3']:
        """
        Smoothly damp towards a target position.

        Args:
            target: Target position
            velocity: Current velocity (will be modified)
            smooth_time: Approximate time to reach target
            dt: Delta time
            max_speed: Maximum speed

        Returns:
            Tuple of (new position, new velocity)
        """
        smooth_time = max(0.0001, smooth_time)
        omega = 2.0 / smooth_time
        x = omega * dt
        exp_factor = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)

        diff = self - target
        max_dist = max_speed * smooth_time

        if diff.magnitude > max_dist:
            diff = diff.normalized * max_dist

        temp = (velocity + diff * omega) * dt
        new_velocity = (velocity - temp * omega) * exp_factor
        new_position = target + (diff + temp) * exp_factor

        return new_position, new_velocity

    # -------------------------------------------------------------------------
    # Component Operations
    # -------------------------------------------------------------------------

    def min_component(self) -> float:
        """Get the minimum component value."""
        return min(self.x, self.y, self.z)

    def max_component(self) -> float:
        """Get the maximum component value."""
        return max(self.x, self.y, self.z)

    def min_component_index(self) -> int:
        """Get the index of the minimum component (0=x, 1=y, 2=z)."""
        if self.x <= self.y and self.x <= self.z:
            return 0
        elif self.y <= self.z:
            return 1
        return 2

    def max_component_index(self) -> int:
        """Get the index of the maximum component (0=x, 1=y, 2=z)."""
        if self.x >= self.y and self.x >= self.z:
            return 0
        elif self.y >= self.z:
            return 1
        return 2

    @staticmethod
    def component_min(a: 'Vector3', b: 'Vector3') -> 'Vector3':
        """Get a vector with minimum components from two vectors."""
        return Vector3(min(a.x, b.x), min(a.y, b.y), min(a.z, b.z))

    @staticmethod
    def component_max(a: 'Vector3', b: 'Vector3') -> 'Vector3':
        """Get a vector with maximum components from two vectors."""
        return Vector3(max(a.x, b.x), max(a.y, b.y), max(a.z, b.z))

    def clamp(self, min_vec: 'Vector3', max_vec: 'Vector3') -> 'Vector3':
        """Clamp this vector between two vectors component-wise."""
        return Vector3(
            max(min_vec.x, min(max_vec.x, self.x)),
            max(min_vec.y, min(max_vec.y, self.y)),
            max(min_vec.z, min(max_vec.z, self.z))
        )

    def clamp_magnitude(self, max_magnitude: float) -> 'Vector3':
        """Clamp the magnitude of this vector."""
        if self.magnitude_squared > max_magnitude * max_magnitude:
            return self.normalized * max_magnitude
        return self.copy()

    # -------------------------------------------------------------------------
    # Arithmetic Operators
    # -------------------------------------------------------------------------

    def __add__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        return Vector3(self.x + other, self.y + other, self.z + other)

    def __radd__(self, other: float) -> 'Vector3':
        return Vector3(other + self.x, other + self.y, other + self.z)

    def __iadd__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            self.x += other.x
            self.y += other.y
            self.z += other.z
        else:
            self.x += other
            self.y += other
            self.z += other
        return self

    def __sub__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        return Vector3(self.x - other, self.y - other, self.z - other)

    def __rsub__(self, other: float) -> 'Vector3':
        return Vector3(other - self.x, other - self.y, other - self.z)

    def __isub__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
        else:
            self.x -= other
            self.y -= other
            self.z -= other
        return self

    def __mul__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other: float) -> 'Vector3':
        return Vector3(other * self.x, other * self.y, other * self.z)

    def __imul__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            self.x *= other.x
            self.y *= other.y
            self.z *= other.z
        else:
            self.x *= other
            self.y *= other
            self.z *= other
        return self

    def __truediv__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
        return Vector3(self.x / other, self.y / other, self.z / other)

    def __rtruediv__(self, other: float) -> 'Vector3':
        return Vector3(other / self.x, other / self.y, other / self.z)

    def __itruediv__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            self.x /= other.x
            self.y /= other.y
            self.z /= other.z
        else:
            self.x /= other
            self.y /= other
            self.z /= other
        return self

    def __floordiv__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x // other.x, self.y // other.y, self.z // other.z)
        return Vector3(self.x // other, self.y // other, self.z // other)

    def __mod__(self, other: Union['Vector3', float]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x % other.x, self.y % other.y, self.z % other.z)
        return Vector3(self.x % other, self.y % other, self.z % other)

    def __neg__(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)

    def __pos__(self) -> 'Vector3':
        return self.copy()

    # -------------------------------------------------------------------------
    # Comparison Operators
    # -------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3):
            return False
        return (abs(self.x - other.x) < EPSILON and
                abs(self.y - other.y) < EPSILON and
                abs(self.z - other.z) < EPSILON)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def approximately_equal(self, other: 'Vector3', tolerance: float = EPSILON) -> bool:
        """Check if approximately equal within a tolerance."""
        return (abs(self.x - other.x) < tolerance and
                abs(self.y - other.y) < tolerance and
                abs(self.z - other.z) < tolerance)

    # -------------------------------------------------------------------------
    # Indexing
    # -------------------------------------------------------------------------

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z
        raise IndexError(f"Vector3 index {index} out of range")

    def __setitem__(self, index: int, value: float) -> None:
        if index == 0:
            self.x = float(value)
        elif index == 1:
            self.y = float(value)
        elif index == 2:
            self.z = float(value)
        else:
            raise IndexError(f"Vector3 index {index} out of range")

    def __len__(self) -> int:
        return 3

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    # -------------------------------------------------------------------------
    # String Representations
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Vector3({self.x:.6f}, {self.y:.6f}, {self.z:.6f})"

    def __str__(self) -> str:
        return f"({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6), round(self.z, 6)))


# =============================================================================
# MATRIX4 CLASS
# =============================================================================

class Matrix4:
    """
    A 4x4 transformation matrix for 3D graphics.

    Supports all standard matrix operations including multiplication,
    inversion, and decomposition. Used for transformations, projections,
    and view matrices.

    Matrix layout (row-major):
        [ m00 m01 m02 m03 ]
        [ m10 m11 m12 m13 ]
        [ m20 m21 m22 m23 ]
        [ m30 m31 m32 m33 ]
    """

    __slots__ = ('m',)

    def __init__(self, values: Optional[List[List[float]]] = None):
        """
        Initialize a 4x4 matrix.

        Args:
            values: 4x4 list of values (default is identity matrix)
        """
        if values is None:
            self.m = [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ]
        else:
            self.m = [[float(values[i][j]) for j in range(4)] for i in range(4)]

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def identity(cls) -> 'Matrix4':
        """Create an identity matrix."""
        return cls()

    @classmethod
    def zero(cls) -> 'Matrix4':
        """Create a zero matrix."""
        return cls([[0.0] * 4 for _ in range(4)])

    @classmethod
    def from_flat(cls, values: List[float]) -> 'Matrix4':
        """Create a matrix from a flat list of 16 values (row-major)."""
        return cls([
            [values[0], values[1], values[2], values[3]],
            [values[4], values[5], values[6], values[7]],
            [values[8], values[9], values[10], values[11]],
            [values[12], values[13], values[14], values[15]]
        ])

    @classmethod
    def translation(cls, x: float, y: float, z: float) -> 'Matrix4':
        """Create a translation matrix."""
        result = cls()
        result.m[0][3] = x
        result.m[1][3] = y
        result.m[2][3] = z
        return result

    @classmethod
    def translation_vec(cls, v: Vector3) -> 'Matrix4':
        """Create a translation matrix from a vector."""
        return cls.translation(v.x, v.y, v.z)

    @classmethod
    def scale(cls, x: float, y: float, z: float) -> 'Matrix4':
        """Create a scale matrix."""
        result = cls()
        result.m[0][0] = x
        result.m[1][1] = y
        result.m[2][2] = z
        return result

    @classmethod
    def scale_uniform(cls, s: float) -> 'Matrix4':
        """Create a uniform scale matrix."""
        return cls.scale(s, s, s)

    @classmethod
    def scale_vec(cls, v: Vector3) -> 'Matrix4':
        """Create a scale matrix from a vector."""
        return cls.scale(v.x, v.y, v.z)

    @classmethod
    def rotation_x(cls, angle: float) -> 'Matrix4':
        """
        Create a rotation matrix around the X axis.

        Args:
            angle: Rotation angle in radians
        """
        c = math.cos(angle)
        s = math.sin(angle)
        result = cls()
        result.m[1][1] = c
        result.m[1][2] = -s
        result.m[2][1] = s
        result.m[2][2] = c
        return result

    @classmethod
    def rotation_y(cls, angle: float) -> 'Matrix4':
        """
        Create a rotation matrix around the Y axis.

        Args:
            angle: Rotation angle in radians
        """
        c = math.cos(angle)
        s = math.sin(angle)
        result = cls()
        result.m[0][0] = c
        result.m[0][2] = s
        result.m[2][0] = -s
        result.m[2][2] = c
        return result

    @classmethod
    def rotation_z(cls, angle: float) -> 'Matrix4':
        """
        Create a rotation matrix around the Z axis.

        Args:
            angle: Rotation angle in radians
        """
        c = math.cos(angle)
        s = math.sin(angle)
        result = cls()
        result.m[0][0] = c
        result.m[0][1] = -s
        result.m[1][0] = s
        result.m[1][1] = c
        return result

    @classmethod
    def rotation_axis(cls, axis: Vector3, angle: float) -> 'Matrix4':
        """
        Create a rotation matrix around an arbitrary axis.

        Args:
            axis: The axis to rotate around (will be normalized)
            angle: Rotation angle in radians
        """
        axis = axis.normalized
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c

        x, y, z = axis.x, axis.y, axis.z

        return cls([
            [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y,  0.0],
            [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x,  0.0],
            [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c,    0.0],
            [0.0,          0.0,          0.0,          1.0]
        ])

    @classmethod
    def rotation_euler(cls, x: float, y: float, z: float,
                       order: str = 'xyz') -> 'Matrix4':
        """
        Create a rotation matrix from Euler angles.

        Args:
            x: Rotation around X axis in radians
            y: Rotation around Y axis in radians
            z: Rotation around Z axis in radians
            order: Order of rotations ('xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx')
        """
        rx = cls.rotation_x(x)
        ry = cls.rotation_y(y)
        rz = cls.rotation_z(z)

        matrices = {'x': rx, 'y': ry, 'z': rz}

        result = cls()
        for axis in order:
            result = result * matrices[axis]

        return result

    @classmethod
    def look_at(cls, eye: Vector3, target: Vector3, up: Vector3) -> 'Matrix4':
        """
        Create a look-at view matrix.

        Args:
            eye: Camera position
            target: Point to look at
            up: Up direction
        """
        forward = (target - eye).normalized
        right = forward.cross(up).normalized
        actual_up = right.cross(forward)

        return cls([
            [right.x,      right.y,      right.z,      -right.dot(eye)],
            [actual_up.x,  actual_up.y,  actual_up.z,  -actual_up.dot(eye)],
            [-forward.x,   -forward.y,   -forward.z,   forward.dot(eye)],
            [0.0,          0.0,          0.0,          1.0]
        ])

    @classmethod
    def perspective(cls, fov: float, aspect: float,
                    near: float, far: float) -> 'Matrix4':
        """
        Create a perspective projection matrix.

        Args:
            fov: Field of view in radians
            aspect: Aspect ratio (width/height)
            near: Near clipping plane
            far: Far clipping plane
        """
        tan_half_fov = math.tan(fov / 2.0)

        result = cls.zero()
        result.m[0][0] = 1.0 / (aspect * tan_half_fov)
        result.m[1][1] = 1.0 / tan_half_fov
        result.m[2][2] = -(far + near) / (far - near)
        result.m[2][3] = -(2.0 * far * near) / (far - near)
        result.m[3][2] = -1.0

        return result

    @classmethod
    def orthographic(cls, left: float, right: float, bottom: float,
                     top: float, near: float, far: float) -> 'Matrix4':
        """
        Create an orthographic projection matrix.

        Args:
            left: Left plane
            right: Right plane
            bottom: Bottom plane
            top: Top plane
            near: Near plane
            far: Far plane
        """
        result = cls.zero()
        result.m[0][0] = 2.0 / (right - left)
        result.m[1][1] = 2.0 / (top - bottom)
        result.m[2][2] = -2.0 / (far - near)
        result.m[0][3] = -(right + left) / (right - left)
        result.m[1][3] = -(top + bottom) / (top - bottom)
        result.m[2][3] = -(far + near) / (far - near)
        result.m[3][3] = 1.0

        return result

    @classmethod
    def from_quaternion(cls, q: 'Quaternion') -> 'Matrix4':
        """Create a rotation matrix from a quaternion."""
        x, y, z, w = q.x, q.y, q.z, q.w

        x2, y2, z2 = x + x, y + y, z + z
        xx, xy, xz = x * x2, x * y2, x * z2
        yy, yz, zz = y * y2, y * z2, z * z2
        wx, wy, wz = w * x2, w * y2, w * z2

        return cls([
            [1.0 - (yy + zz),  xy - wz,          xz + wy,          0.0],
            [xy + wz,          1.0 - (xx + zz),  yz - wx,          0.0],
            [xz - wy,          yz + wx,          1.0 - (xx + yy),  0.0],
            [0.0,              0.0,              0.0,              1.0]
        ])

    @classmethod
    def trs(cls, translation: Vector3, rotation: 'Quaternion',
            scale: Vector3) -> 'Matrix4':
        """
        Create a transformation matrix from translation, rotation, and scale.

        Args:
            translation: Translation vector
            rotation: Rotation quaternion
            scale: Scale vector
        """
        rot_matrix = cls.from_quaternion(rotation)

        result = rot_matrix.copy()
        result.m[0][0] *= scale.x
        result.m[0][1] *= scale.x
        result.m[0][2] *= scale.x
        result.m[1][0] *= scale.y
        result.m[1][1] *= scale.y
        result.m[1][2] *= scale.y
        result.m[2][0] *= scale.z
        result.m[2][1] *= scale.z
        result.m[2][2] *= scale.z
        result.m[0][3] = translation.x
        result.m[1][3] = translation.y
        result.m[2][3] = translation.z

        return result

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def determinant(self) -> float:
        """Calculate the determinant of the matrix."""
        m = self.m

        s0 = m[0][0] * m[1][1] - m[1][0] * m[0][1]
        s1 = m[0][0] * m[1][2] - m[1][0] * m[0][2]
        s2 = m[0][0] * m[1][3] - m[1][0] * m[0][3]
        s3 = m[0][1] * m[1][2] - m[1][1] * m[0][2]
        s4 = m[0][1] * m[1][3] - m[1][1] * m[0][3]
        s5 = m[0][2] * m[1][3] - m[1][2] * m[0][3]

        c5 = m[2][2] * m[3][3] - m[3][2] * m[2][3]
        c4 = m[2][1] * m[3][3] - m[3][1] * m[2][3]
        c3 = m[2][1] * m[3][2] - m[3][1] * m[2][2]
        c2 = m[2][0] * m[3][3] - m[3][0] * m[2][3]
        c1 = m[2][0] * m[3][2] - m[3][0] * m[2][2]
        c0 = m[2][0] * m[3][1] - m[3][0] * m[2][1]

        return s0 * c5 - s1 * c4 + s2 * c3 + s3 * c2 - s4 * c1 + s5 * c0

    @property
    def is_identity(self) -> bool:
        """Check if this is an identity matrix."""
        for i in range(4):
            for j in range(4):
                expected = 1.0 if i == j else 0.0
                if abs(self.m[i][j] - expected) > EPSILON:
                    return False
        return True

    @property
    def transposed(self) -> 'Matrix4':
        """Get the transpose of this matrix."""
        return Matrix4([
            [self.m[j][i] for j in range(4)]
            for i in range(4)
        ])

    @property
    def inverse(self) -> Optional['Matrix4']:
        """
        Get the inverse of this matrix.

        Returns:
            Inverse matrix or None if not invertible
        """
        m = self.m

        s0 = m[0][0] * m[1][1] - m[1][0] * m[0][1]
        s1 = m[0][0] * m[1][2] - m[1][0] * m[0][2]
        s2 = m[0][0] * m[1][3] - m[1][0] * m[0][3]
        s3 = m[0][1] * m[1][2] - m[1][1] * m[0][2]
        s4 = m[0][1] * m[1][3] - m[1][1] * m[0][3]
        s5 = m[0][2] * m[1][3] - m[1][2] * m[0][3]

        c5 = m[2][2] * m[3][3] - m[3][2] * m[2][3]
        c4 = m[2][1] * m[3][3] - m[3][1] * m[2][3]
        c3 = m[2][1] * m[3][2] - m[3][1] * m[2][2]
        c2 = m[2][0] * m[3][3] - m[3][0] * m[2][3]
        c1 = m[2][0] * m[3][2] - m[3][0] * m[2][2]
        c0 = m[2][0] * m[3][1] - m[3][0] * m[2][1]

        det = s0 * c5 - s1 * c4 + s2 * c3 + s3 * c2 - s4 * c1 + s5 * c0

        if abs(det) < EPSILON:
            return None

        inv_det = 1.0 / det

        return Matrix4([
            [
                (m[1][1] * c5 - m[1][2] * c4 + m[1][3] * c3) * inv_det,
                (-m[0][1] * c5 + m[0][2] * c4 - m[0][3] * c3) * inv_det,
                (m[3][1] * s5 - m[3][2] * s4 + m[3][3] * s3) * inv_det,
                (-m[2][1] * s5 + m[2][2] * s4 - m[2][3] * s3) * inv_det
            ],
            [
                (-m[1][0] * c5 + m[1][2] * c2 - m[1][3] * c1) * inv_det,
                (m[0][0] * c5 - m[0][2] * c2 + m[0][3] * c1) * inv_det,
                (-m[3][0] * s5 + m[3][2] * s2 - m[3][3] * s1) * inv_det,
                (m[2][0] * s5 - m[2][2] * s2 + m[2][3] * s1) * inv_det
            ],
            [
                (m[1][0] * c4 - m[1][1] * c2 + m[1][3] * c0) * inv_det,
                (-m[0][0] * c4 + m[0][1] * c2 - m[0][3] * c0) * inv_det,
                (m[3][0] * s4 - m[3][1] * s2 + m[3][3] * s0) * inv_det,
                (-m[2][0] * s4 + m[2][1] * s2 - m[2][3] * s0) * inv_det
            ],
            [
                (-m[1][0] * c3 + m[1][1] * c1 - m[1][2] * c0) * inv_det,
                (m[0][0] * c3 - m[0][1] * c1 + m[0][2] * c0) * inv_det,
                (-m[3][0] * s3 + m[3][1] * s1 - m[3][2] * s0) * inv_det,
                (m[2][0] * s3 - m[2][1] * s1 + m[2][2] * s0) * inv_det
            ]
        ])

    # -------------------------------------------------------------------------
    # Operations
    # -------------------------------------------------------------------------

    def copy(self) -> 'Matrix4':
        """Create a copy of this matrix."""
        return Matrix4([row[:] for row in self.m])

    def transpose(self) -> 'Matrix4':
        """Transpose this matrix in place."""
        m = self.m
        for i in range(4):
            for j in range(i + 1, 4):
                m[i][j], m[j][i] = m[j][i], m[i][j]
        return self

    def transform_point(self, v: Vector3) -> Vector3:
        """
        Transform a point by this matrix (applies translation).

        Args:
            v: The point to transform

        Returns:
            Transformed point
        """
        m = self.m
        w = m[3][0] * v.x + m[3][1] * v.y + m[3][2] * v.z + m[3][3]
        if abs(w) < EPSILON:
            w = 1.0
        return Vector3(
            (m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z + m[0][3]) / w,
            (m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z + m[1][3]) / w,
            (m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z + m[2][3]) / w
        )

    def transform_direction(self, v: Vector3) -> Vector3:
        """
        Transform a direction by this matrix (ignores translation).

        Args:
            v: The direction to transform

        Returns:
            Transformed direction
        """
        m = self.m
        return Vector3(
            m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
            m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
            m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z
        )

    def transform_normal(self, v: Vector3) -> Vector3:
        """
        Transform a normal vector (uses inverse transpose).

        Args:
            v: The normal to transform

        Returns:
            Transformed normal
        """
        inv = self.inverse
        if inv is None:
            return v.copy()
        m = inv.transposed.m
        return Vector3(
            m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
            m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
            m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z
        ).normalized

    def decompose(self) -> Tuple[Vector3, 'Quaternion', Vector3]:
        """
        Decompose this matrix into translation, rotation, and scale.

        Returns:
            Tuple of (translation, rotation, scale)
        """
        m = self.m

        translation = Vector3(m[0][3], m[1][3], m[2][3])

        sx = Vector3(m[0][0], m[1][0], m[2][0]).magnitude
        sy = Vector3(m[0][1], m[1][1], m[2][1]).magnitude
        sz = Vector3(m[0][2], m[1][2], m[2][2]).magnitude

        if self.determinant < 0:
            sx = -sx

        scale = Vector3(sx, sy, sz)

        rot_matrix = Matrix4([
            [m[0][0]/sx, m[0][1]/sy, m[0][2]/sz, 0],
            [m[1][0]/sx, m[1][1]/sy, m[1][2]/sz, 0],
            [m[2][0]/sx, m[2][1]/sy, m[2][2]/sz, 0],
            [0, 0, 0, 1]
        ])

        rotation = Quaternion.from_matrix(rot_matrix)

        return translation, rotation, scale

    def get_translation(self) -> Vector3:
        """Get the translation component of this matrix."""
        return Vector3(self.m[0][3], self.m[1][3], self.m[2][3])

    def get_scale(self) -> Vector3:
        """Get the scale component of this matrix."""
        return Vector3(
            Vector3(self.m[0][0], self.m[1][0], self.m[2][0]).magnitude,
            Vector3(self.m[0][1], self.m[1][1], self.m[2][1]).magnitude,
            Vector3(self.m[0][2], self.m[1][2], self.m[2][2]).magnitude
        )

    def set_translation(self, v: Vector3) -> 'Matrix4':
        """Set the translation component of this matrix."""
        self.m[0][3] = v.x
        self.m[1][3] = v.y
        self.m[2][3] = v.z
        return self

    # -------------------------------------------------------------------------
    # Arithmetic Operators
    # -------------------------------------------------------------------------

    def __mul__(self, other: Union['Matrix4', Vector3, float]) -> Union['Matrix4', Vector3]:
        if isinstance(other, Matrix4):
            result = Matrix4.zero()
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        result.m[i][j] += self.m[i][k] * other.m[k][j]
            return result
        elif isinstance(other, Vector3):
            return self.transform_point(other)
        else:
            return Matrix4([
                [self.m[i][j] * other for j in range(4)]
                for i in range(4)
            ])

    def __rmul__(self, other: float) -> 'Matrix4':
        return Matrix4([
            [other * self.m[i][j] for j in range(4)]
            for i in range(4)
        ])

    def __add__(self, other: 'Matrix4') -> 'Matrix4':
        return Matrix4([
            [self.m[i][j] + other.m[i][j] for j in range(4)]
            for i in range(4)
        ])

    def __sub__(self, other: 'Matrix4') -> 'Matrix4':
        return Matrix4([
            [self.m[i][j] - other.m[i][j] for j in range(4)]
            for i in range(4)
        ])

    # -------------------------------------------------------------------------
    # Comparison and Indexing
    # -------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix4):
            return False
        for i in range(4):
            for j in range(4):
                if abs(self.m[i][j] - other.m[i][j]) > EPSILON:
                    return False
        return True

    def __getitem__(self, key: Tuple[int, int]) -> float:
        return self.m[key[0]][key[1]]

    def __setitem__(self, key: Tuple[int, int], value: float) -> None:
        self.m[key[0]][key[1]] = float(value)

    # -------------------------------------------------------------------------
    # String Representations
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        rows = []
        for i in range(4):
            row = ', '.join(f'{self.m[i][j]:.4f}' for j in range(4))
            rows.append(f'[{row}]')
        return f"Matrix4([\n  {chr(10).join(rows)}\n])"

    def __str__(self) -> str:
        return self.__repr__()


# =============================================================================
# QUATERNION CLASS
# =============================================================================

class Quaternion:
    """
    A quaternion for representing 3D rotations.

    Quaternions provide smooth interpolation and avoid gimbal lock.
    This implementation uses (x, y, z, w) component order where w
    is the scalar part.
    """

    __slots__ = ('x', 'y', 'z', 'w')

    def __init__(self, x: float = 0.0, y: float = 0.0,
                 z: float = 0.0, w: float = 1.0):
        """
        Initialize a quaternion.

        Args:
            x: X component (default 0.0)
            y: Y component (default 0.0)
            z: Z component (default 0.0)
            w: W component (scalar, default 1.0)
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def identity(cls) -> 'Quaternion':
        """Create an identity quaternion (no rotation)."""
        return cls(0.0, 0.0, 0.0, 1.0)

    @classmethod
    def from_axis_angle(cls, axis: Vector3, angle: float) -> 'Quaternion':
        """
        Create a quaternion from an axis and angle.

        Args:
            axis: Rotation axis (will be normalized)
            angle: Rotation angle in radians
        """
        axis = axis.normalized
        half_angle = angle / 2.0
        s = math.sin(half_angle)
        return cls(
            axis.x * s,
            axis.y * s,
            axis.z * s,
            math.cos(half_angle)
        )

    @classmethod
    def from_euler(cls, x: float, y: float, z: float,
                   order: str = 'xyz') -> 'Quaternion':
        """
        Create a quaternion from Euler angles.

        Args:
            x: Rotation around X axis in radians
            y: Rotation around Y axis in radians
            z: Rotation around Z axis in radians
            order: Order of rotations ('xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx')
        """
        cx = math.cos(x / 2)
        sx = math.sin(x / 2)
        cy = math.cos(y / 2)
        sy = math.sin(y / 2)
        cz = math.cos(z / 2)
        sz = math.sin(z / 2)

        if order == 'xyz':
            return cls(
                sx * cy * cz + cx * sy * sz,
                cx * sy * cz - sx * cy * sz,
                cx * cy * sz + sx * sy * cz,
                cx * cy * cz - sx * sy * sz
            )
        elif order == 'xzy':
            return cls(
                sx * cy * cz - cx * sy * sz,
                cx * sy * cz - sx * cy * sz,
                cx * cy * sz + sx * sy * cz,
                cx * cy * cz + sx * sy * sz
            )
        elif order == 'yxz':
            return cls(
                sx * cy * cz + cx * sy * sz,
                cx * sy * cz - sx * cy * sz,
                cx * cy * sz - sx * sy * cz,
                cx * cy * cz + sx * sy * sz
            )
        elif order == 'yzx':
            return cls(
                sx * cy * cz + cx * sy * sz,
                cx * sy * cz + sx * cy * sz,
                cx * cy * sz - sx * sy * cz,
                cx * cy * cz - sx * sy * sz
            )
        elif order == 'zxy':
            return cls(
                sx * cy * cz - cx * sy * sz,
                cx * sy * cz + sx * cy * sz,
                cx * cy * sz + sx * sy * cz,
                cx * cy * cz - sx * sy * sz
            )
        elif order == 'zyx':
            return cls(
                sx * cy * cz - cx * sy * sz,
                cx * sy * cz + sx * cy * sz,
                cx * cy * sz - sx * sy * cz,
                cx * cy * cz + sx * sy * sz
            )
        else:
            raise ValueError(f"Unknown rotation order: {order}")

    @classmethod
    def from_matrix(cls, m: Matrix4) -> 'Quaternion':
        """
        Create a quaternion from a rotation matrix.

        Args:
            m: A rotation matrix (3x3 upper-left portion is used)
        """
        trace = m.m[0][0] + m.m[1][1] + m.m[2][2]

        if trace > 0:
            s = 0.5 / math.sqrt(trace + 1.0)
            return cls(
                (m.m[2][1] - m.m[1][2]) * s,
                (m.m[0][2] - m.m[2][0]) * s,
                (m.m[1][0] - m.m[0][1]) * s,
                0.25 / s
            )
        elif m.m[0][0] > m.m[1][1] and m.m[0][0] > m.m[2][2]:
            s = 2.0 * math.sqrt(1.0 + m.m[0][0] - m.m[1][1] - m.m[2][2])
            return cls(
                0.25 * s,
                (m.m[0][1] + m.m[1][0]) / s,
                (m.m[0][2] + m.m[2][0]) / s,
                (m.m[2][1] - m.m[1][2]) / s
            )
        elif m.m[1][1] > m.m[2][2]:
            s = 2.0 * math.sqrt(1.0 + m.m[1][1] - m.m[0][0] - m.m[2][2])
            return cls(
                (m.m[0][1] + m.m[1][0]) / s,
                0.25 * s,
                (m.m[1][2] + m.m[2][1]) / s,
                (m.m[0][2] - m.m[2][0]) / s
            )
        else:
            s = 2.0 * math.sqrt(1.0 + m.m[2][2] - m.m[0][0] - m.m[1][1])
            return cls(
                (m.m[0][2] + m.m[2][0]) / s,
                (m.m[1][2] + m.m[2][1]) / s,
                0.25 * s,
                (m.m[1][0] - m.m[0][1]) / s
            )

    @classmethod
    def from_to_rotation(cls, from_dir: Vector3, to_dir: Vector3) -> 'Quaternion':
        """
        Create a quaternion that rotates from one direction to another.

        Args:
            from_dir: Starting direction
            to_dir: Target direction
        """
        from_dir = from_dir.normalized
        to_dir = to_dir.normalized

        dot = from_dir.dot(to_dir)

        if dot > 0.999999:
            return cls.identity()

        if dot < -0.999999:
            axis = Vector3.right().cross(from_dir)
            if axis.magnitude_squared < EPSILON:
                axis = Vector3.up().cross(from_dir)
            axis = axis.normalized
            return cls.from_axis_angle(axis, PI)

        axis = from_dir.cross(to_dir)

        return cls(
            axis.x,
            axis.y,
            axis.z,
            1.0 + dot
        ).normalized

    @classmethod
    def look_rotation(cls, forward: Vector3,
                      up: Vector3 = None) -> 'Quaternion':
        """
        Create a quaternion looking in a direction.

        Args:
            forward: Forward direction
            up: Up direction (default is Vector3.up())
        """
        if up is None:
            up = Vector3.up()

        forward = forward.normalized
        right = up.cross(forward).normalized
        actual_up = forward.cross(right)

        m = Matrix4([
            [right.x,      actual_up.x,  forward.x,  0],
            [right.y,      actual_up.y,  forward.y,  0],
            [right.z,      actual_up.z,  forward.z,  0],
            [0,            0,            0,          1]
        ])

        return cls.from_matrix(m)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def magnitude(self) -> float:
        """Get the magnitude of the quaternion."""
        return math.sqrt(self.x*self.x + self.y*self.y +
                        self.z*self.z + self.w*self.w)

    @property
    def magnitude_squared(self) -> float:
        """Get the squared magnitude of the quaternion."""
        return self.x*self.x + self.y*self.y + self.z*self.z + self.w*self.w

    @property
    def normalized(self) -> 'Quaternion':
        """Get a normalized copy of this quaternion."""
        mag = self.magnitude
        if mag < EPSILON:
            return Quaternion.identity()
        return Quaternion(self.x/mag, self.y/mag, self.z/mag, self.w/mag)

    @property
    def conjugate(self) -> 'Quaternion':
        """Get the conjugate of this quaternion."""
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    @property
    def inverse(self) -> 'Quaternion':
        """Get the inverse of this quaternion."""
        mag_sq = self.magnitude_squared
        if mag_sq < EPSILON:
            return Quaternion.identity()
        return Quaternion(
            -self.x / mag_sq,
            -self.y / mag_sq,
            -self.z / mag_sq,
            self.w / mag_sq
        )

    @property
    def euler_angles(self) -> Vector3:
        """
        Get Euler angles (in radians) from this quaternion.

        Returns:
            Vector3 with (pitch, yaw, roll) in radians
        """
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(HALF_PI, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return Vector3(pitch, yaw, roll)

    @property
    def axis(self) -> Vector3:
        """Get the rotation axis."""
        s = math.sqrt(1 - self.w * self.w)
        if s < EPSILON:
            return Vector3.up()
        return Vector3(self.x / s, self.y / s, self.z / s)

    @property
    def angle(self) -> float:
        """Get the rotation angle in radians."""
        return 2 * math.acos(max(-1.0, min(1.0, self.w)))

    @property
    def forward(self) -> Vector3:
        """Get the forward direction of this rotation."""
        return self.rotate_vector(Vector3.forward())

    @property
    def up(self) -> Vector3:
        """Get the up direction of this rotation."""
        return self.rotate_vector(Vector3.up())

    @property
    def right(self) -> Vector3:
        """Get the right direction of this rotation."""
        return self.rotate_vector(Vector3.right())

    # -------------------------------------------------------------------------
    # Operations
    # -------------------------------------------------------------------------

    def copy(self) -> 'Quaternion':
        """Create a copy of this quaternion."""
        return Quaternion(self.x, self.y, self.z, self.w)

    def normalize(self) -> 'Quaternion':
        """Normalize this quaternion in place."""
        mag = self.magnitude
        if mag > EPSILON:
            self.x /= mag
            self.y /= mag
            self.z /= mag
            self.w /= mag
        return self

    def set(self, x: float, y: float, z: float, w: float) -> 'Quaternion':
        """Set all components of the quaternion."""
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)
        return self

    def rotate_vector(self, v: Vector3) -> Vector3:
        """
        Rotate a vector by this quaternion.

        Args:
            v: Vector to rotate

        Returns:
            Rotated vector
        """
        qv = Vector3(self.x, self.y, self.z)
        uv = qv.cross(v)
        uuv = qv.cross(uv)
        return v + (uv * self.w + uuv) * 2.0

    def dot(self, other: 'Quaternion') -> float:
        """Calculate the dot product with another quaternion."""
        return self.x*other.x + self.y*other.y + self.z*other.z + self.w*other.w

    def angle_to(self, other: 'Quaternion') -> float:
        """
        Calculate the angle between two quaternions.

        Returns:
            Angle in radians
        """
        dot = abs(self.dot(other))
        return 2.0 * math.acos(min(1.0, dot))

    # -------------------------------------------------------------------------
    # Interpolation
    # -------------------------------------------------------------------------

    def lerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """
        Linear interpolation to another quaternion.

        Args:
            other: Target quaternion
            t: Interpolation factor (0-1)

        Returns:
            Interpolated quaternion (normalized)
        """
        if self.dot(other) < 0:
            other = Quaternion(-other.x, -other.y, -other.z, -other.w)

        return Quaternion(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t,
            self.w + (other.w - self.w) * t
        ).normalized

    def slerp(self, other: 'Quaternion', t: float) -> 'Quaternion':
        """
        Spherical linear interpolation to another quaternion.

        Args:
            other: Target quaternion
            t: Interpolation factor (0-1)

        Returns:
            Spherically interpolated quaternion
        """
        dot = self.dot(other)

        if dot < 0:
            other = Quaternion(-other.x, -other.y, -other.z, -other.w)
            dot = -dot

        if dot > 0.9995:
            return self.lerp(other, t)

        theta_0 = math.acos(dot)
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        sin_theta_0 = math.sin(theta_0)

        s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0

        return Quaternion(
            s0 * self.x + s1 * other.x,
            s0 * self.y + s1 * other.y,
            s0 * self.z + s1 * other.z,
            s0 * self.w + s1 * other.w
        )

    def rotate_towards(self, target: 'Quaternion',
                       max_degrees_delta: float) -> 'Quaternion':
        """
        Rotate towards a target quaternion by a maximum angle.

        Args:
            target: Target rotation
            max_degrees_delta: Maximum angle to rotate in degrees

        Returns:
            New rotation quaternion
        """
        angle = self.angle_to(target)
        if angle < EPSILON:
            return target.copy()

        t = min(1.0, max_degrees_delta * DEG_TO_RAD / angle)
        return self.slerp(target, t)

    # -------------------------------------------------------------------------
    # Arithmetic Operators
    # -------------------------------------------------------------------------

    def __mul__(self, other: Union['Quaternion', Vector3, float]) -> Union['Quaternion', Vector3]:
        if isinstance(other, Quaternion):
            return Quaternion(
                self.w*other.x + self.x*other.w + self.y*other.z - self.z*other.y,
                self.w*other.y - self.x*other.z + self.y*other.w + self.z*other.x,
                self.w*other.z + self.x*other.y - self.y*other.x + self.z*other.w,
                self.w*other.w - self.x*other.x - self.y*other.y - self.z*other.z
            )
        elif isinstance(other, Vector3):
            return self.rotate_vector(other)
        else:
            return Quaternion(self.x*other, self.y*other, self.z*other, self.w*other)

    def __rmul__(self, other: float) -> 'Quaternion':
        return Quaternion(other*self.x, other*self.y, other*self.z, other*self.w)

    def __neg__(self) -> 'Quaternion':
        return Quaternion(-self.x, -self.y, -self.z, -self.w)

    # -------------------------------------------------------------------------
    # Comparison
    # -------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quaternion):
            return False
        return (abs(self.x - other.x) < EPSILON and
                abs(self.y - other.y) < EPSILON and
                abs(self.z - other.z) < EPSILON and
                abs(self.w - other.w) < EPSILON)

    def approximately_equal(self, other: 'Quaternion',
                            tolerance: float = EPSILON) -> bool:
        """Check if approximately equal (accounts for double cover)."""
        dot = abs(self.dot(other))
        return dot > 1.0 - tolerance

    # -------------------------------------------------------------------------
    # String Representations
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Quaternion({self.x:.6f}, {self.y:.6f}, {self.z:.6f}, {self.w:.6f})"

    def __str__(self) -> str:
        return f"({self.x:.3f}, {self.y:.3f}, {self.z:.3f}, {self.w:.3f})"

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6),
                    round(self.z, 6), round(self.w, 6)))


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values."""
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, value: float) -> float:
    """Get the interpolation factor for a value between a and b."""
    if abs(b - a) < EPSILON:
        return 0.0
    return (value - a) / (b - a)


def remap(value: float, from_min: float, from_max: float,
          to_min: float, to_max: float) -> float:
    """Remap a value from one range to another."""
    t = inverse_lerp(from_min, from_max, value)
    return lerp(to_min, to_max, t)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def clamp01(value: float) -> float:
    """Clamp a value between 0 and 1."""
    return max(0.0, min(1.0, value))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smooth Hermite interpolation."""
    t = clamp01((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0: float, edge1: float, x: float) -> float:
    """Smoother Hermite interpolation (Ken Perlin's version)."""
    t = clamp01((x - edge0) / (edge1 - edge0))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out."""
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out."""
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out."""
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out."""
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_in_elastic(t: float) -> float:
    """Elastic ease-in."""
    if t == 0.0 or t == 1.0:
        return t
    return -math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * TAU / 3.0)


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out."""
    if t == 0.0 or t == 1.0:
        return t
    return math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * TAU / 3.0) + 1.0


def ease_in_out_elastic(t: float) -> float:
    """Elastic ease-in-out."""
    if t == 0.0 or t == 1.0:
        return t
    if t < 0.5:
        return -(math.pow(2.0, 20.0 * t - 10.0) *
                 math.sin((20.0 * t - 11.125) * TAU / 4.5)) / 2.0
    return (math.pow(2.0, -20.0 * t + 10.0) *
            math.sin((20.0 * t - 11.125) * TAU / 4.5)) / 2.0 + 1.0


def ease_in_bounce(t: float) -> float:
    """Bounce ease-in."""
    return 1.0 - ease_out_bounce(1.0 - t)


def ease_out_bounce(t: float) -> float:
    """Bounce ease-out."""
    n1 = 7.5625
    d1 = 2.75

    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_in_out_bounce(t: float) -> float:
    """Bounce ease-in-out."""
    if t < 0.5:
        return (1.0 - ease_out_bounce(1.0 - 2.0 * t)) / 2.0
    return (1.0 + ease_out_bounce(2.0 * t - 1.0)) / 2.0
