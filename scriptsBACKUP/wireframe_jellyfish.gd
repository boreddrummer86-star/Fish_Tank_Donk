extends Node3D
class_name WireframeJellyfish
## ============================================================================
## WIREFRAME JELLYFISH - Electric Neon Outline
## Anatomically inspired Aurelia aurita (Moon Jellyfish) style
##
## STRUCTURE:
##   - Bell (dome): The umbrella-shaped body
##   - Oral arms: 4 frilly appendages (center)
##   - Tentacles: 8 long trailing tentacles
##   - Radial canals: Internal symmetry lines
##   - Gonad pattern: 4-fold symmetry rings
##
## ANIMATION TARGETS:
##   - Bloop: Bell contracts/expands for propulsion
##   - Drift: Gentle swaying in currents
##   - Tentacle flow: Trailing physics-like motion
##
## MESH ORIENTATION:
##   - Bell top at +Y
##   - Tentacles trail at -Y
##   - Faces -Z (Godot forward convention)
## ============================================================================

# Jellyfish dimensions
const BELL_RADIUS: float = 18.0
const BELL_HEIGHT: float = 12.0
const TENTACLE_LENGTH: float = 35.0
const ORAL_ARM_LENGTH: float = 20.0

# Number of subdivisions for smooth curves
const BELL_RINGS: int = 8
const BELL_SEGMENTS: int = 16
const TENTACLE_SEGMENTS: int = 12

# Electric blue color - same as shark
const WIRE_COLOR: Color = Color(0.0, 0.85, 1.0, 1.0)

# Mesh components
var mesh_instance: MeshInstance3D
var wireframe_mesh: ArrayMesh

# Key points for animation
var bell_top: Vector3
var bell_rim_points: Array[Vector3] = []
var tentacle_bases: Array[Vector3] = []
var oral_arm_bases: Array[Vector3] = []


func _ready() -> void:
	_create_wireframe_mesh()


func _create_wireframe_mesh() -> void:
	wireframe_mesh = ArrayMesh.new()
	var vertices: PackedVector3Array = PackedVector3Array()

	# =========================================================================
	# BELL (DOME) - The umbrella-shaped body
	# Parabolic dome shape, slightly flattened
	# =========================================================================
	bell_top = Vector3(0, BELL_HEIGHT, 0)

	# Create bell rings from top to rim
	var bell_rings: Array[Array] = []

	for ring in range(BELL_RINGS + 1):
		var t: float = float(ring) / float(BELL_RINGS)
		# Parabolic profile: y = height * (1 - t^2), radius expands
		var ring_y: float = BELL_HEIGHT * (1.0 - t * t * 0.9)
		var ring_radius: float = BELL_RADIUS * sqrt(t) * 1.1

		# Slight flattening at the top
		if ring < 2:
			ring_radius *= 0.3 + t * 0.7

		var ring_points: Array[Vector3] = []
		for seg in range(BELL_SEGMENTS):
			var angle: float = float(seg) * TAU / float(BELL_SEGMENTS)
			var x: float = cos(angle) * ring_radius
			var z: float = sin(angle) * ring_radius
			ring_points.append(Vector3(x, ring_y, z))

		bell_rings.append(ring_points)

	# Draw horizontal rings
	for ring in bell_rings:
		for i in range(ring.size()):
			vertices.append(ring[i])
			vertices.append(ring[(i + 1) % ring.size()])

	# Draw vertical meridian lines (every other segment for cleaner look)
	for seg in range(0, BELL_SEGMENTS, 2):
		for ring in range(BELL_RINGS):
			vertices.append(bell_rings[ring][seg])
			vertices.append(bell_rings[ring + 1][seg])

	# Connect to bell top
	for seg in range(0, BELL_SEGMENTS, 4):
		vertices.append(bell_top)
		vertices.append(bell_rings[0][seg])

	# Store rim points for animation
	bell_rim_points = []
	for pt in bell_rings[BELL_RINGS]:
		bell_rim_points.append(pt)

	# =========================================================================
	# RADIAL CANALS - Internal symmetry (4-fold)
	# =========================================================================
	for i in range(4):
		var angle: float = float(i) * TAU / 4.0 + PI / 4.0
		var inner_r: float = BELL_RADIUS * 0.2
		var outer_r: float = BELL_RADIUS * 0.95
		var canal_y: float = BELL_HEIGHT * 0.3

		# Radial line from center to rim
		var inner_pt := Vector3(cos(angle) * inner_r, canal_y, sin(angle) * inner_r)
		var outer_pt := Vector3(cos(angle) * outer_r, canal_y * 0.2, sin(angle) * outer_r)
		vertices.append(inner_pt)
		vertices.append(outer_pt)

	# =========================================================================
	# GONADS - 4 horseshoe shapes (characteristic of Aurelia)
	# =========================================================================
	for i in range(4):
		var base_angle: float = float(i) * TAU / 4.0
		var gonad_r: float = BELL_RADIUS * 0.5
		var gonad_y: float = BELL_HEIGHT * 0.4

		# Horseshoe arc
		var arc_points: Array[Vector3] = []
		for j in range(7):
			var arc_t: float = float(j) / 6.0 - 0.5  # -0.5 to 0.5
			var arc_angle: float = base_angle + arc_t * 0.8
			var r: float = gonad_r + sin(abs(arc_t) * PI) * 4.0
			var y: float = gonad_y + cos(arc_t * PI) * 1.5
			arc_points.append(Vector3(cos(arc_angle) * r, y, sin(arc_angle) * r))

		for j in range(arc_points.size() - 1):
			vertices.append(arc_points[j])
			vertices.append(arc_points[j + 1])

	# =========================================================================
	# BELL RIM DETAIL - Scalloped edge
	# =========================================================================
	var rim_y: float = bell_rings[BELL_RINGS][0].y
	for seg in range(BELL_SEGMENTS):
		var angle: float = float(seg) * TAU / float(BELL_SEGMENTS)
		var next_angle: float = float(seg + 1) * TAU / float(BELL_SEGMENTS)
		var mid_angle: float = (angle + next_angle) / 2.0

		# Scallop dips down between segments
		var rim_pt := bell_rings[BELL_RINGS][seg]
		var scallop_pt := Vector3(
			cos(mid_angle) * BELL_RADIUS * 1.02,
			rim_y - 1.5,
			sin(mid_angle) * BELL_RADIUS * 1.02
		)
		vertices.append(rim_pt)
		vertices.append(scallop_pt)
		vertices.append(scallop_pt)
		vertices.append(bell_rings[BELL_RINGS][(seg + 1) % BELL_SEGMENTS])

	# =========================================================================
	# ORAL ARMS - 4 frilly appendages from center
	# =========================================================================
	oral_arm_bases = []
	var oral_center_y: float = BELL_HEIGHT * 0.2

	for arm in range(4):
		var base_angle: float = float(arm) * TAU / 4.0
		var arm_base := Vector3(cos(base_angle) * 3.0, oral_center_y, sin(base_angle) * 3.0)
		oral_arm_bases.append(arm_base)

		# Each oral arm has a wavy, frilly structure
		var arm_segments: int = 8
		var prev_left: Vector3 = arm_base
		var prev_right: Vector3 = arm_base
		var prev_center: Vector3 = arm_base

		for seg in range(arm_segments):
			var t: float = float(seg + 1) / float(arm_segments)
			var y: float = oral_center_y - t * ORAL_ARM_LENGTH

			# Wavy spreading pattern
			var spread: float = 2.0 + t * 5.0
			var wave: float = sin(t * PI * 3.0) * 2.0

			var center := Vector3(
				cos(base_angle) * (3.0 + t * 2.0),
				y,
				sin(base_angle) * (3.0 + t * 2.0)
			)

			var left := Vector3(
				cos(base_angle - 0.3) * (3.0 + spread + wave),
				y - wave * 0.3,
				sin(base_angle - 0.3) * (3.0 + spread + wave)
			)

			var right := Vector3(
				cos(base_angle + 0.3) * (3.0 + spread - wave),
				y + wave * 0.3,
				sin(base_angle + 0.3) * (3.0 + spread - wave)
			)

			# Draw frilly edges
			vertices.append(prev_center)
			vertices.append(center)
			vertices.append(prev_left)
			vertices.append(left)
			vertices.append(prev_right)
			vertices.append(right)

			# Cross connections for frills
			if seg % 2 == 0:
				vertices.append(center)
				vertices.append(left)
				vertices.append(center)
				vertices.append(right)

			prev_center = center
			prev_left = left
			prev_right = right

	# =========================================================================
	# TENTACLES - 8 long trailing tentacles
	# =========================================================================
	tentacle_bases = []

	for tent in range(8):
		var angle: float = float(tent) * TAU / 8.0
		var base_x: float = cos(angle) * BELL_RADIUS * 0.9
		var base_z: float = sin(angle) * BELL_RADIUS * 0.9
		var base_y: float = bell_rings[BELL_RINGS][0].y - 0.5

		var tent_base := Vector3(base_x, base_y, base_z)
		tentacle_bases.append(tent_base)

		# Tentacle curves down and trails
		var prev_pt: Vector3 = tent_base
		for seg in range(TENTACLE_SEGMENTS):
			var t: float = float(seg + 1) / float(TENTACLE_SEGMENTS)

			# Gentle S-curve as tentacle trails
			var wave_x: float = sin(t * PI * 2.0 + angle) * 3.0 * t
			var wave_z: float = cos(t * PI * 1.5 + angle * 0.5) * 2.0 * t

			# Gradually move outward and down
			var x: float = base_x * (1.0 + t * 0.3) + wave_x
			var z: float = base_z * (1.0 + t * 0.3) + wave_z
			var y: float = base_y - t * TENTACLE_LENGTH

			var pt := Vector3(x, y, z)
			vertices.append(prev_pt)
			vertices.append(pt)
			prev_pt = pt

	# =========================================================================
	# BELL INTERIOR STRUCTURE - Cross bracing
	# =========================================================================
	var interior_y: float = BELL_HEIGHT * 0.5
	var interior_r: float = BELL_RADIUS * 0.6

	# Central hub
	var hub_pts: Array[Vector3] = []
	for i in range(8):
		var angle: float = float(i) * TAU / 8.0
		hub_pts.append(Vector3(cos(angle) * 4.0, interior_y, sin(angle) * 4.0))

	for i in range(8):
		vertices.append(hub_pts[i])
		vertices.append(hub_pts[(i + 1) % 8])

	# Spokes from hub to rim
	for i in range(0, 8, 2):
		var angle: float = float(i) * TAU / 8.0
		vertices.append(hub_pts[i])
		vertices.append(Vector3(cos(angle) * interior_r, interior_y * 0.6, sin(angle) * interior_r))

	# =========================================================================
	# CREATE MESH
	# =========================================================================
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices

	wireframe_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_LINES, arrays)

	# Create material - electric blue, unshaded
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = WIRE_COLOR
	material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED

	wireframe_mesh.surface_set_material(0, material)

	# Create mesh instance
	mesh_instance = MeshInstance3D.new()
	mesh_instance.mesh = wireframe_mesh
	add_child(mesh_instance)


# ============================================================================
# PUBLIC API FOR ANIMATION
# ============================================================================

## Get bell top position
func get_bell_top() -> Vector3:
	return global_transform * bell_top


## Get bell rim points (for bloop animation)
func get_bell_rim_points() -> Array[Vector3]:
	var world_points: Array[Vector3] = []
	for pt in bell_rim_points:
		world_points.append(global_transform * pt)
	return world_points


## Get tentacle base positions
func get_tentacle_bases() -> Array[Vector3]:
	var world_bases: Array[Vector3] = []
	for pt in tentacle_bases:
		world_bases.append(global_transform * pt)
	return world_bases


## Get oral arm bases
func get_oral_arm_bases() -> Array[Vector3]:
	var world_bases: Array[Vector3] = []
	for pt in oral_arm_bases:
		world_bases.append(global_transform * pt)
	return world_bases


## Get bell radius
func get_bell_radius() -> float:
	return BELL_RADIUS


## Get bell height
func get_bell_height() -> float:
	return BELL_HEIGHT


## Get center position
func get_center() -> Vector3:
	return global_position
