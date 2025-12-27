"""
Fish Tank Donk - Wireframe Renderer Module
==========================================

Advanced wireframe rendering engine for terminal-based 3D graphics.
Supports edges, faces, depth sorting, and ASCII character rendering
with proper projection and clipping.
"""

import math
from typing import List, Tuple, Optional, Dict, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from .math3d import Vector3, Matrix4, Quaternion, EPSILON, clamp, lerp
from .transform import Transform, Camera


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Vertex:
    """
    A vertex with position, normal, and UV coordinates.
    """
    position: Vector3
    normal: Optional[Vector3] = None
    uv: Optional[Tuple[float, float]] = None
    color: Optional[Tuple[int, int, int]] = None

    def copy(self) -> 'Vertex':
        """Create a copy of this vertex."""
        return Vertex(
            position=self.position.copy(),
            normal=self.normal.copy() if self.normal else None,
            uv=self.uv,
            color=self.color
        )

    def transformed(self, matrix: Matrix4) -> 'Vertex':
        """Create a transformed copy of this vertex."""
        result = self.copy()
        result.position = matrix.transform_point(self.position)
        if self.normal:
            result.normal = matrix.transform_normal(self.normal)
        return result


@dataclass
class Edge:
    """
    An edge connecting two vertices.
    """
    v1_idx: int
    v2_idx: int
    color: Optional[Tuple[int, int, int]] = None
    thickness: float = 1.0
    style: str = 'solid'

    def copy(self) -> 'Edge':
        """Create a copy of this edge."""
        return Edge(
            v1_idx=self.v1_idx,
            v2_idx=self.v2_idx,
            color=self.color,
            thickness=self.thickness,
            style=self.style
        )


@dataclass
class Face:
    """
    A face defined by vertex indices.
    """
    vertex_indices: List[int]
    normal: Optional[Vector3] = None
    color: Optional[Tuple[int, int, int]] = None
    visible: bool = True

    def copy(self) -> 'Face':
        """Create a copy of this face."""
        return Face(
            vertex_indices=self.vertex_indices.copy(),
            normal=self.normal.copy() if self.normal else None,
            color=self.color,
            visible=self.visible
        )

    def calculate_normal(self, vertices: List[Vertex]) -> Vector3:
        """Calculate the face normal from vertices."""
        if len(self.vertex_indices) < 3:
            return Vector3.up()

        v0 = vertices[self.vertex_indices[0]].position
        v1 = vertices[self.vertex_indices[1]].position
        v2 = vertices[self.vertex_indices[2]].position

        edge1 = v1 - v0
        edge2 = v2 - v0

        return edge1.cross(edge2).normalized


class RenderMode(Enum):
    """Rendering modes for the wireframe renderer."""
    WIREFRAME = auto()
    POINTS = auto()
    SOLID = auto()
    WIREFRAME_SOLID = auto()


# =============================================================================
# MESH CLASS
# =============================================================================

class Mesh:
    """
    A 3D mesh containing vertices, edges, and faces.
    """

    __slots__ = (
        'vertices', 'edges', 'faces', 'name',
        '_bounds_min', '_bounds_max', '_bounds_dirty'
    )

    def __init__(self, name: str = "Mesh"):
        """
        Initialize a new mesh.

        Args:
            name: Name of the mesh
        """
        self.vertices: List[Vertex] = []
        self.edges: List[Edge] = []
        self.faces: List[Face] = []
        self.name = name

        self._bounds_min = Vector3.zero()
        self._bounds_max = Vector3.zero()
        self._bounds_dirty = True

    def add_vertex(self, position: Vector3,
                   normal: Vector3 = None,
                   uv: Tuple[float, float] = None,
                   color: Tuple[int, int, int] = None) -> int:
        """
        Add a vertex to the mesh.

        Returns:
            Index of the new vertex
        """
        idx = len(self.vertices)
        self.vertices.append(Vertex(position, normal, uv, color))
        self._bounds_dirty = True
        return idx

    def add_edge(self, v1_idx: int, v2_idx: int,
                 color: Tuple[int, int, int] = None,
                 thickness: float = 1.0,
                 style: str = 'solid') -> int:
        """
        Add an edge to the mesh.

        Returns:
            Index of the new edge
        """
        idx = len(self.edges)
        self.edges.append(Edge(v1_idx, v2_idx, color, thickness, style))
        return idx

    def add_face(self, vertex_indices: List[int],
                 color: Tuple[int, int, int] = None) -> int:
        """
        Add a face to the mesh.

        Returns:
            Index of the new face
        """
        idx = len(self.faces)
        face = Face(vertex_indices, color=color)
        face.normal = face.calculate_normal(self.vertices)
        self.faces.append(face)
        return idx

    def add_triangle(self, v0: int, v1: int, v2: int,
                     color: Tuple[int, int, int] = None,
                     add_edges: bool = True) -> int:
        """
        Add a triangle face and optionally its edges.

        Returns:
            Index of the new face
        """
        face_idx = self.add_face([v0, v1, v2], color)

        if add_edges:
            self.add_edge(v0, v1, color)
            self.add_edge(v1, v2, color)
            self.add_edge(v2, v0, color)

        return face_idx

    def add_quad(self, v0: int, v1: int, v2: int, v3: int,
                 color: Tuple[int, int, int] = None,
                 add_edges: bool = True) -> int:
        """
        Add a quad face and optionally its edges.

        Returns:
            Index of the new face
        """
        face_idx = self.add_face([v0, v1, v2, v3], color)

        if add_edges:
            self.add_edge(v0, v1, color)
            self.add_edge(v1, v2, color)
            self.add_edge(v2, v3, color)
            self.add_edge(v3, v0, color)

        return face_idx

    def calculate_normals(self) -> None:
        """Calculate normals for all faces and vertices."""
        for face in self.faces:
            face.normal = face.calculate_normal(self.vertices)

        for vertex in self.vertices:
            vertex.normal = Vector3.zero()

        for face in self.faces:
            if face.normal:
                for idx in face.vertex_indices:
                    if self.vertices[idx].normal:
                        self.vertices[idx].normal += face.normal

        for vertex in self.vertices:
            if vertex.normal and vertex.normal.magnitude_squared > EPSILON:
                vertex.normal.normalize()

    def get_bounds(self) -> Tuple[Vector3, Vector3]:
        """
        Get the bounding box of the mesh.

        Returns:
            Tuple of (min, max) vectors
        """
        if self._bounds_dirty:
            if not self.vertices:
                self._bounds_min = Vector3.zero()
                self._bounds_max = Vector3.zero()
            else:
                self._bounds_min = self.vertices[0].position.copy()
                self._bounds_max = self.vertices[0].position.copy()

                for vertex in self.vertices[1:]:
                    pos = vertex.position
                    self._bounds_min = Vector3.component_min(
                        self._bounds_min, pos
                    )
                    self._bounds_max = Vector3.component_max(
                        self._bounds_max, pos
                    )

            self._bounds_dirty = False

        return self._bounds_min.copy(), self._bounds_max.copy()

    def get_center(self) -> Vector3:
        """Get the center of the mesh bounds."""
        min_b, max_b = self.get_bounds()
        return (min_b + max_b) * 0.5

    def get_size(self) -> Vector3:
        """Get the size of the mesh bounds."""
        min_b, max_b = self.get_bounds()
        return max_b - min_b

    def transform(self, matrix: Matrix4) -> 'Mesh':
        """
        Create a transformed copy of this mesh.

        Args:
            matrix: Transformation matrix

        Returns:
            New transformed mesh
        """
        result = Mesh(self.name + "_transformed")

        for vertex in self.vertices:
            result.vertices.append(vertex.transformed(matrix))

        for edge in self.edges:
            result.edges.append(edge.copy())

        for face in self.faces:
            new_face = face.copy()
            if new_face.normal:
                new_face.normal = matrix.transform_normal(face.normal)
            result.faces.append(new_face)

        return result

    def merge(self, other: 'Mesh') -> None:
        """
        Merge another mesh into this one.

        Args:
            other: Mesh to merge
        """
        vertex_offset = len(self.vertices)

        for vertex in other.vertices:
            self.vertices.append(vertex.copy())

        for edge in other.edges:
            new_edge = edge.copy()
            new_edge.v1_idx += vertex_offset
            new_edge.v2_idx += vertex_offset
            self.edges.append(new_edge)

        for face in other.faces:
            new_face = face.copy()
            new_face.vertex_indices = [
                idx + vertex_offset for idx in face.vertex_indices
            ]
            self.faces.append(new_face)

        self._bounds_dirty = True

    def clear(self) -> None:
        """Clear all mesh data."""
        self.vertices.clear()
        self.edges.clear()
        self.faces.clear()
        self._bounds_dirty = True

    def copy(self) -> 'Mesh':
        """Create a copy of this mesh."""
        result = Mesh(self.name)
        for v in self.vertices:
            result.vertices.append(v.copy())
        for e in self.edges:
            result.edges.append(e.copy())
        for f in self.faces:
            result.faces.append(f.copy())
        return result


# =============================================================================
# MESH PRIMITIVES
# =============================================================================

class MeshPrimitives:
    """Factory methods for creating primitive meshes."""

    @staticmethod
    def create_cube(size: float = 1.0,
                    color: Tuple[int, int, int] = None) -> Mesh:
        """Create a cube mesh."""
        mesh = Mesh("Cube")
        h = size / 2.0

        positions = [
            Vector3(-h, -h, -h), Vector3(h, -h, -h),
            Vector3(h, h, -h), Vector3(-h, h, -h),
            Vector3(-h, -h, h), Vector3(h, -h, h),
            Vector3(h, h, h), Vector3(-h, h, h)
        ]

        for pos in positions:
            mesh.add_vertex(pos, color=color)

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        for v1, v2 in edges:
            mesh.add_edge(v1, v2, color)

        faces = [
            [0, 1, 2, 3], [4, 5, 6, 7],
            [0, 1, 5, 4], [2, 3, 7, 6],
            [0, 3, 7, 4], [1, 2, 6, 5]
        ]

        for face in faces:
            mesh.add_face(face, color)

        mesh.calculate_normals()
        return mesh

    @staticmethod
    def create_sphere(radius: float = 1.0,
                      segments: int = 16,
                      rings: int = 12,
                      color: Tuple[int, int, int] = None) -> Mesh:
        """Create a sphere mesh."""
        mesh = Mesh("Sphere")

        mesh.add_vertex(Vector3(0, radius, 0), color=color)

        for ring in range(1, rings):
            phi = math.pi * ring / rings
            y = radius * math.cos(phi)
            ring_radius = radius * math.sin(phi)

            for seg in range(segments):
                theta = 2 * math.pi * seg / segments
                x = ring_radius * math.cos(theta)
                z = ring_radius * math.sin(theta)
                mesh.add_vertex(Vector3(x, y, z), color=color)

        mesh.add_vertex(Vector3(0, -radius, 0), color=color)

        for seg in range(segments):
            next_seg = (seg + 1) % segments
            mesh.add_edge(0, 1 + seg, color)
            mesh.add_face([0, 1 + seg, 1 + next_seg], color)

        for ring in range(rings - 2):
            ring_start = 1 + ring * segments
            next_ring_start = ring_start + segments

            for seg in range(segments):
                next_seg = (seg + 1) % segments
                v0 = ring_start + seg
                v1 = ring_start + next_seg
                v2 = next_ring_start + next_seg
                v3 = next_ring_start + seg

                mesh.add_edge(v0, v1, color)
                mesh.add_edge(v0, v3, color)
                mesh.add_face([v0, v1, v2, v3], color)

        bottom_idx = len(mesh.vertices) - 1
        last_ring_start = 1 + (rings - 2) * segments

        for seg in range(segments):
            next_seg = (seg + 1) % segments
            mesh.add_edge(last_ring_start + seg, bottom_idx, color)
            mesh.add_face([bottom_idx, last_ring_start + next_seg,
                          last_ring_start + seg], color)

        mesh.calculate_normals()
        return mesh

    @staticmethod
    def create_cylinder(radius: float = 1.0,
                        height: float = 2.0,
                        segments: int = 16,
                        color: Tuple[int, int, int] = None) -> Mesh:
        """Create a cylinder mesh."""
        mesh = Mesh("Cylinder")
        half_height = height / 2.0

        top_center = mesh.add_vertex(Vector3(0, half_height, 0), color=color)

        for seg in range(segments):
            theta = 2 * math.pi * seg / segments
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            mesh.add_vertex(Vector3(x, half_height, z), color=color)

        bottom_center = mesh.add_vertex(Vector3(0, -half_height, 0), color=color)

        for seg in range(segments):
            theta = 2 * math.pi * seg / segments
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            mesh.add_vertex(Vector3(x, -half_height, z), color=color)

        for seg in range(segments):
            next_seg = (seg + 1) % segments
            mesh.add_edge(1 + seg, 1 + next_seg, color)
            mesh.add_face([top_center, 1 + seg, 1 + next_seg], color)

        bottom_ring_start = segments + 2
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            mesh.add_edge(bottom_ring_start + seg,
                         bottom_ring_start + next_seg, color)
            mesh.add_face([bottom_center, bottom_ring_start + next_seg,
                          bottom_ring_start + seg], color)

        for seg in range(segments):
            next_seg = (seg + 1) % segments
            top_v = 1 + seg
            top_next = 1 + next_seg
            bot_v = bottom_ring_start + seg
            bot_next = bottom_ring_start + next_seg

            mesh.add_edge(top_v, bot_v, color)
            mesh.add_face([top_v, top_next, bot_next, bot_v], color)

        mesh.calculate_normals()
        return mesh

    @staticmethod
    def create_cone(radius: float = 1.0,
                    height: float = 2.0,
                    segments: int = 16,
                    color: Tuple[int, int, int] = None) -> Mesh:
        """Create a cone mesh."""
        mesh = Mesh("Cone")

        apex = mesh.add_vertex(Vector3(0, height, 0), color=color)

        base_center = mesh.add_vertex(Vector3(0, 0, 0), color=color)

        for seg in range(segments):
            theta = 2 * math.pi * seg / segments
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            mesh.add_vertex(Vector3(x, 0, z), color=color)

        base_ring_start = 2
        for seg in range(segments):
            next_seg = (seg + 1) % segments

            mesh.add_edge(apex, base_ring_start + seg, color)
            mesh.add_face([apex, base_ring_start + seg,
                          base_ring_start + next_seg], color)

            mesh.add_edge(base_ring_start + seg,
                         base_ring_start + next_seg, color)
            mesh.add_face([base_center, base_ring_start + next_seg,
                          base_ring_start + seg], color)

        mesh.calculate_normals()
        return mesh

    @staticmethod
    def create_torus(major_radius: float = 1.0,
                     minor_radius: float = 0.3,
                     major_segments: int = 24,
                     minor_segments: int = 12,
                     color: Tuple[int, int, int] = None) -> Mesh:
        """Create a torus mesh."""
        mesh = Mesh("Torus")

        for major in range(major_segments):
            theta = 2 * math.pi * major / major_segments
            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)

            for minor in range(minor_segments):
                phi = 2 * math.pi * minor / minor_segments
                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)

                x = (major_radius + minor_radius * cos_phi) * cos_theta
                y = minor_radius * sin_phi
                z = (major_radius + minor_radius * cos_phi) * sin_theta

                mesh.add_vertex(Vector3(x, y, z), color=color)

        for major in range(major_segments):
            next_major = (major + 1) % major_segments

            for minor in range(minor_segments):
                next_minor = (minor + 1) % minor_segments

                v0 = major * minor_segments + minor
                v1 = major * minor_segments + next_minor
                v2 = next_major * minor_segments + next_minor
                v3 = next_major * minor_segments + minor

                mesh.add_edge(v0, v1, color)
                mesh.add_edge(v0, v3, color)
                mesh.add_face([v0, v1, v2, v3], color)

        mesh.calculate_normals()
        return mesh

    @staticmethod
    def create_grid(width: float = 10.0,
                    depth: float = 10.0,
                    divisions_x: int = 10,
                    divisions_z: int = 10,
                    color: Tuple[int, int, int] = None) -> Mesh:
        """Create a grid mesh."""
        mesh = Mesh("Grid")

        half_width = width / 2.0
        half_depth = depth / 2.0

        for z in range(divisions_z + 1):
            z_pos = -half_depth + depth * z / divisions_z
            v1 = mesh.add_vertex(Vector3(-half_width, 0, z_pos), color=color)
            v2 = mesh.add_vertex(Vector3(half_width, 0, z_pos), color=color)
            mesh.add_edge(v1, v2, color)

        for x in range(divisions_x + 1):
            x_pos = -half_width + width * x / divisions_x
            v1 = mesh.add_vertex(Vector3(x_pos, 0, -half_depth), color=color)
            v2 = mesh.add_vertex(Vector3(x_pos, 0, half_depth), color=color)
            mesh.add_edge(v1, v2, color)

        return mesh

    @staticmethod
    def create_axes(length: float = 1.0) -> Mesh:
        """Create an axes indicator mesh."""
        mesh = Mesh("Axes")

        origin = mesh.add_vertex(Vector3(0, 0, 0))

        x_end = mesh.add_vertex(Vector3(length, 0, 0), color=(255, 0, 0))
        mesh.add_edge(origin, x_end, color=(255, 0, 0))

        y_end = mesh.add_vertex(Vector3(0, length, 0), color=(0, 255, 0))
        mesh.add_edge(origin, y_end, color=(0, 255, 0))

        z_end = mesh.add_vertex(Vector3(0, 0, length), color=(0, 0, 255))
        mesh.add_edge(origin, z_end, color=(0, 0, 255))

        return mesh


# =============================================================================
# WIREFRAME RENDERER
# =============================================================================

@dataclass
class ProjectedVertex:
    """A projected vertex for rendering."""
    screen_x: float
    screen_y: float
    depth: float
    original_idx: int
    visible: bool = True


@dataclass
class ProjectedEdge:
    """A projected edge for rendering."""
    v1: ProjectedVertex
    v2: ProjectedVertex
    color: Tuple[int, int, int]
    depth: float
    thickness: float = 1.0
    style: str = 'solid'


class WireframeRenderer:
    """
    Renders 3D wireframe meshes to a 2D character buffer.

    Supports depth sorting, back-face culling, and various
    rendering styles for terminal-based display.
    """

    __slots__ = (
        'width', 'height',
        '_char_buffer', '_depth_buffer', '_color_buffer',
        '_camera', '_render_mode',
        '_backface_culling', '_depth_testing',
        '_edge_chars', '_point_char',
        '_ambient_light', '_light_direction'
    )

    EDGE_CHARS = {
        'horizontal': '─',
        'vertical': '│',
        'diagonal_up': '╱',
        'diagonal_down': '╲',
        'cross': '┼',
        'dot': '·',
        'default': '·'
    }

    INTENSITY_CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

    def __init__(self, width: int = 80, height: int = 24):
        """
        Initialize the renderer.

        Args:
            width: Buffer width in characters
            height: Buffer height in characters
        """
        self.width = width
        self.height = height

        self._char_buffer: List[List[str]] = []
        self._depth_buffer: List[List[float]] = []
        self._color_buffer: List[List[Optional[Tuple[int, int, int]]]] = []

        self._camera: Optional[Camera] = None
        self._render_mode = RenderMode.WIREFRAME

        self._backface_culling = True
        self._depth_testing = True

        self._edge_chars = self.EDGE_CHARS.copy()
        self._point_char = '●'

        self._ambient_light = 0.2
        self._light_direction = Vector3(0.5, 1.0, 0.3).normalized

        self.clear()

    def resize(self, width: int, height: int) -> None:
        """Resize the render buffer."""
        self.width = width
        self.height = height
        self.clear()

    def clear(self, char: str = ' ',
              color: Tuple[int, int, int] = None) -> None:
        """Clear the render buffer."""
        self._char_buffer = [
            [char for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self._depth_buffer = [
            [float('inf') for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self._color_buffer = [
            [color for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def set_camera(self, camera: Camera) -> None:
        """Set the camera for rendering."""
        self._camera = camera
        self._camera.aspect = self.width / (self.height * 2.0)

    @property
    def render_mode(self) -> RenderMode:
        """Get the current render mode."""
        return self._render_mode

    @render_mode.setter
    def render_mode(self, mode: RenderMode) -> None:
        """Set the render mode."""
        self._render_mode = mode

    @property
    def backface_culling(self) -> bool:
        """Get backface culling state."""
        return self._backface_culling

    @backface_culling.setter
    def backface_culling(self, value: bool) -> None:
        """Set backface culling state."""
        self._backface_culling = value

    def project_vertex(self, vertex: Vertex,
                       transform: Matrix4) -> Optional[ProjectedVertex]:
        """
        Project a vertex to screen space.

        Args:
            vertex: Vertex to project
            transform: World transformation matrix

        Returns:
            Projected vertex or None if behind camera
        """
        if self._camera is None:
            return None

        world_pos = transform.transform_point(vertex.position)

        result = self._camera.world_to_screen(
            world_pos, self.width, self.height * 2
        )

        if result is None:
            return None

        screen_x, screen_y, depth = result

        screen_y = screen_y / 2.0

        return ProjectedVertex(
            screen_x=screen_x,
            screen_y=screen_y,
            depth=depth,
            original_idx=0,
            visible=True
        )

    def render_mesh(self, mesh: Mesh, transform: Transform,
                    color_override: Tuple[int, int, int] = None) -> None:
        """
        Render a mesh to the buffer.

        Args:
            mesh: Mesh to render
            transform: Transform of the mesh
            color_override: Optional color override for all geometry
        """
        if self._camera is None:
            return

        world_matrix = transform.world_matrix

        projected_vertices: List[Optional[ProjectedVertex]] = []
        for i, vertex in enumerate(mesh.vertices):
            pv = self.project_vertex(vertex, world_matrix)
            if pv:
                pv.original_idx = i
            projected_vertices.append(pv)

        if self._render_mode in (RenderMode.WIREFRAME, RenderMode.WIREFRAME_SOLID):
            projected_edges: List[ProjectedEdge] = []

            for edge in mesh.edges:
                pv1 = projected_vertices[edge.v1_idx]
                pv2 = projected_vertices[edge.v2_idx]

                if pv1 is None or pv2 is None:
                    continue

                if not pv1.visible or not pv2.visible:
                    continue

                color = color_override or edge.color or (255, 255, 255)
                depth = (pv1.depth + pv2.depth) / 2.0

                projected_edges.append(ProjectedEdge(
                    v1=pv1,
                    v2=pv2,
                    color=color,
                    depth=depth,
                    thickness=edge.thickness,
                    style=edge.style
                ))

            projected_edges.sort(key=lambda e: e.depth, reverse=True)

            for edge in projected_edges:
                self._draw_edge(edge)

        if self._render_mode == RenderMode.POINTS:
            for pv in projected_vertices:
                if pv and pv.visible:
                    self._draw_point(pv, color_override or (255, 255, 255))

    def _draw_edge(self, edge: ProjectedEdge) -> None:
        """Draw an edge to the buffer using Bresenham's algorithm."""
        x0, y0 = int(edge.v1.screen_x), int(edge.v1.screen_y)
        x1, y1 = int(edge.v2.screen_x), int(edge.v2.screen_y)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        total_dist = math.sqrt(dx * dx + dy * dy)
        if total_dist < EPSILON:
            total_dist = 1.0

        step = 0
        max_steps = max(dx, dy) + 1

        while step < max_steps:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                t = step / max_steps if max_steps > 0 else 0
                depth = lerp(edge.v1.depth, edge.v2.depth, t)

                if not self._depth_testing or depth < self._depth_buffer[y0][x0]:
                    char = self._get_edge_char(x0, y0, x1, y1, dx, dy)
                    self._char_buffer[y0][x0] = char
                    self._depth_buffer[y0][x0] = depth
                    self._color_buffer[y0][x0] = edge.color

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

            step += 1

    def _get_edge_char(self, x0: int, y0: int, x1: int, y1: int,
                       dx: int, dy: int) -> str:
        """Get the appropriate character for an edge segment."""
        if dx == 0:
            return self._edge_chars['vertical']
        if dy == 0:
            return self._edge_chars['horizontal']

        slope = dy / dx if dx != 0 else float('inf')

        if slope < 0.5:
            return self._edge_chars['horizontal']
        elif slope < 2.0:
            if (x1 > x0 and y1 < y0) or (x1 < x0 and y1 > y0):
                return self._edge_chars['diagonal_up']
            else:
                return self._edge_chars['diagonal_down']
        else:
            return self._edge_chars['vertical']

    def _draw_point(self, pv: ProjectedVertex,
                    color: Tuple[int, int, int]) -> None:
        """Draw a point to the buffer."""
        x, y = int(pv.screen_x), int(pv.screen_y)

        if 0 <= x < self.width and 0 <= y < self.height:
            if not self._depth_testing or pv.depth < self._depth_buffer[y][x]:
                self._char_buffer[y][x] = self._point_char
                self._depth_buffer[y][x] = pv.depth
                self._color_buffer[y][x] = color

    def set_char(self, x: int, y: int, char: str,
                 color: Tuple[int, int, int] = None,
                 depth: float = 0.0) -> None:
        """
        Set a character directly in the buffer.

        Args:
            x: X coordinate
            y: Y coordinate
            char: Character to set
            color: Optional color
            depth: Depth value for z-testing
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            if not self._depth_testing or depth <= self._depth_buffer[y][x]:
                self._char_buffer[y][x] = char
                self._color_buffer[y][x] = color
                self._depth_buffer[y][x] = depth

    def draw_line(self, x0: int, y0: int, x1: int, y1: int,
                  color: Tuple[int, int, int] = None,
                  char: str = None) -> None:
        """
        Draw a 2D line directly to the buffer.

        Args:
            x0, y0: Start point
            x1, y1: End point
            color: Line color
            char: Character to use (auto-selected if None)
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                c = char if char else self._get_edge_char(x0, y0, x1, y1, dx, dy)
                self._char_buffer[y0][x0] = c
                self._color_buffer[y0][x0] = color

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_text(self, x: int, y: int, text: str,
                  color: Tuple[int, int, int] = None) -> None:
        """
        Draw text to the buffer.

        Args:
            x: Starting X coordinate
            y: Y coordinate
            text: Text to draw
            color: Text color
        """
        for i, char in enumerate(text):
            if 0 <= x + i < self.width and 0 <= y < self.height:
                self._char_buffer[y][x + i] = char
                self._color_buffer[y][x + i] = color

    def draw_box(self, x: int, y: int, width: int, height: int,
                 color: Tuple[int, int, int] = None,
                 fill: bool = False) -> None:
        """
        Draw a box to the buffer.

        Args:
            x, y: Top-left corner
            width, height: Box dimensions
            color: Box color
            fill: Whether to fill the box
        """
        box_chars = {
            'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
            'h': '─', 'v': '│'
        }

        if y >= 0 and y < self.height:
            if x >= 0:
                self.set_char(x, y, box_chars['tl'], color)
            if x + width - 1 < self.width:
                self.set_char(x + width - 1, y, box_chars['tr'], color)
            for i in range(1, width - 1):
                if 0 <= x + i < self.width:
                    self.set_char(x + i, y, box_chars['h'], color)

        if y + height - 1 >= 0 and y + height - 1 < self.height:
            if x >= 0:
                self.set_char(x, y + height - 1, box_chars['bl'], color)
            if x + width - 1 < self.width:
                self.set_char(x + width - 1, y + height - 1, box_chars['br'], color)
            for i in range(1, width - 1):
                if 0 <= x + i < self.width:
                    self.set_char(x + i, y + height - 1, box_chars['h'], color)

        for j in range(1, height - 1):
            if 0 <= y + j < self.height:
                if x >= 0:
                    self.set_char(x, y + j, box_chars['v'], color)
                if x + width - 1 < self.width:
                    self.set_char(x + width - 1, y + j, box_chars['v'], color)

                if fill:
                    for i in range(1, width - 1):
                        if 0 <= x + i < self.width:
                            self.set_char(x + i, y + j, ' ', color)

    def get_buffer(self) -> List[str]:
        """
        Get the rendered buffer as a list of strings.

        Returns:
            List of strings, one per row
        """
        return [''.join(row) for row in self._char_buffer]

    def get_buffer_with_colors(self) -> List[Tuple[str, List[Optional[Tuple[int, int, int]]]]]:
        """
        Get the rendered buffer with color information.

        Returns:
            List of (string, colors) tuples
        """
        result = []
        for y in range(self.height):
            row_str = ''.join(self._char_buffer[y])
            row_colors = self._color_buffer[y].copy()
            result.append((row_str, row_colors))
        return result

    def __repr__(self) -> str:
        return f"WireframeRenderer({self.width}x{self.height})"
