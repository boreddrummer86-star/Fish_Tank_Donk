class_name SegmentedJellyfish
extends Node3D
## ============================================================================
## DONK_TANK - Segmented Wireframe Jellyfish
##
## Anatomically inspired moon jellyfish built as articulated segments
## for smooth bloop animation (Mario Blooper style).
##
## ORIENTATION: Jellyfish bell at top (+Y), tentacles trail down (-Y)
##   - Swims by contracting/expanding bell
##   - Tentacles follow with physics-like delay
##
## SEGMENTS (for animation):
##   0. Bell Top - crown of the dome
##   1. Bell Mid - middle of bell
##   2. Bell Rim - edge where tentacles attach
##   3. Oral Arms - 4 central feeding arms
##   4. Tentacles Upper - first half of trailing
##   5. Tentacles Lower - second half of trailing
##
## BLOOP ANIMATION:
##   - Bell contracts (squishes down, widens)
##   - Pushes water down = jellyfish moves up
##   - Bell relaxes (returns to dome shape)
##   - Repeat 3x for "bloop bloop bloop"
## ============================================================================

# Jellyfish dimensions
const BELL_RADIUS: float = 18.0
const BELL_HEIGHT: float = 12.0
const TENTACLE_LENGTH: float = 35.0
const ORAL_ARM_LENGTH: float = 20.0

# Animation constants
const BLOOP_DURATION: float = 0.6  # One bloop cycle
const BLOOP_SQUISH: float = 0.6    # How much bell compresses (0.6 = 40% squish)
const BLOOP_EXPAND: float = 1.15   # How much bell widens

## ============================================================================
## ELECTRIC NEON COLOR PALETTE
## Same as shark for consistency
## ============================================================================

const NEON_COLORS: Array[Color] = [
	Color(1.0, 0.4, 0.8, 1.0),     # Pink (default for jellyfish)
	Color(0.0, 0.85, 1.0, 1.0),    # Electric Blue
	Color(0.0, 1.0, 0.9, 1.0),     # Cyan/Teal
	Color(0.6, 0.0, 1.0, 1.0),     # Electric Purple
	Color(0.85, 0.0, 1.0, 1.0),    # Magenta
	Color(1.0, 0.0, 0.5, 1.0),     # Hot Pink
	Color(1.0, 0.2, 0.0, 1.0),     # Electric Orange
	Color(1.0, 1.0, 0.0, 1.0),     # Electric Yellow
	Color(0.5, 1.0, 0.0, 1.0),     # Lime Green
	Color(0.0, 1.0, 0.4, 1.0),     # Electric Green
	Color(0.0, 1.0, 0.7, 1.0),     # Aqua/Seafoam
]

# Current color index
var _color_index: int = 0
var current_color: Color = NEON_COLORS[0]

# Segment nodes
var segment_bell_top: Node3D
var segment_bell_mid: Node3D
var segment_bell_rim: Node3D
var segment_oral_arms: Node3D
var segment_tentacles_upper: Node3D
var segment_tentacles_lower: Node3D

# All segments array
var all_segments: Array[Node3D] = []

# Material (shared)
var wire_material: StandardMaterial3D

# Bloop animation state
var bloop_phase: float = 0.0  # 0-1 through bloop cycle
var is_blooping: bool = false
var bloop_count: int = 0
var target_bloop_count: int = 0


func _ready() -> void:
	# Randomize starting color - pink-ish tones preferred for jellyfish
	_color_index = randi() % 6  # Favor the pink/purple end
	current_color = NEON_COLORS[_color_index]

	_create_material()
	_create_segments()

	print("[JELLYFISH] Spawned with color: ", get_color_name())


func _create_material() -> void:
	wire_material = StandardMaterial3D.new()
	wire_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	wire_material.albedo_color = current_color
	wire_material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED


## ============================================================================
## COLOR CYCLING API
## ============================================================================

func cycle_color() -> void:
	_color_index = (_color_index + 1) % NEON_COLORS.size()
	set_color(NEON_COLORS[_color_index])


func cycle_color_random() -> void:
	var new_index: int = _color_index
	while new_index == _color_index and NEON_COLORS.size() > 1:
		new_index = randi() % NEON_COLORS.size()
	_color_index = new_index
	set_color(NEON_COLORS[_color_index])


func set_color_by_index(index: int) -> void:
	if index < 0 or index >= NEON_COLORS.size():
		return
	_color_index = index
	set_color(NEON_COLORS[_color_index])


func set_color(color: Color) -> void:
	current_color = color
	if wire_material:
		wire_material.albedo_color = color


func get_color() -> Color:
	return current_color


func get_color_index() -> int:
	return _color_index


func get_color_count() -> int:
	return NEON_COLORS.size()


func get_color_name() -> String:
	var names: Array[String] = [
		"Pink", "Electric Blue", "Cyan", "Purple", "Magenta",
		"Hot Pink", "Orange", "Yellow", "Lime", "Green", "Aqua"
	]
	if _color_index < names.size():
		return names[_color_index]
	return "Unknown"


## ============================================================================
## SEGMENT CREATION
## ============================================================================

func _create_segments() -> void:
	# Bell Top (crown) - root segment
	segment_bell_top = Node3D.new()
	segment_bell_top.name = "BellTop"
	segment_bell_top.position = Vector3(0, BELL_HEIGHT, 0)
	add_child(segment_bell_top)

	# Bell Mid
	segment_bell_mid = Node3D.new()
	segment_bell_mid.name = "BellMid"
	segment_bell_mid.position = Vector3(0, -BELL_HEIGHT * 0.4, 0)
	segment_bell_top.add_child(segment_bell_mid)

	# Bell Rim
	segment_bell_rim = Node3D.new()
	segment_bell_rim.name = "BellRim"
	segment_bell_rim.position = Vector3(0, -BELL_HEIGHT * 0.5, 0)
	segment_bell_mid.add_child(segment_bell_rim)

	# Oral Arms (attached to center of bell rim)
	segment_oral_arms = Node3D.new()
	segment_oral_arms.name = "OralArms"
	segment_oral_arms.position = Vector3(0, -2.0, 0)
	segment_bell_rim.add_child(segment_oral_arms)

	# Tentacles Upper
	segment_tentacles_upper = Node3D.new()
	segment_tentacles_upper.name = "TentaclesUpper"
	segment_tentacles_upper.position = Vector3(0, -ORAL_ARM_LENGTH * 0.5, 0)
	segment_oral_arms.add_child(segment_tentacles_upper)

	# Tentacles Lower
	segment_tentacles_lower = Node3D.new()
	segment_tentacles_lower.name = "TentaclesLower"
	segment_tentacles_lower.position = Vector3(0, -TENTACLE_LENGTH * 0.4, 0)
	segment_tentacles_upper.add_child(segment_tentacles_lower)

	all_segments = [
		segment_bell_top,
		segment_bell_mid,
		segment_bell_rim,
		segment_oral_arms,
		segment_tentacles_upper,
		segment_tentacles_lower
	]

	# Build meshes
	_build_bell_top_mesh(segment_bell_top)
	_build_bell_mid_mesh(segment_bell_mid)
	_build_bell_rim_mesh(segment_bell_rim)
	_build_oral_arms_mesh(segment_oral_arms)
	_build_tentacles_upper_mesh(segment_tentacles_upper)
	_build_tentacles_lower_mesh(segment_tentacles_lower)


func _add_mesh_to_segment(segment: Node3D, vertices: PackedVector3Array) -> void:
	if vertices.size() < 2:
		return

	var mesh := ArrayMesh.new()
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices

	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_LINES, arrays)
	mesh.surface_set_material(0, wire_material)

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.mesh = mesh
	segment.add_child(mesh_instance)


## ============================================================================
## MESH BUILDERS - Bell segments
## ============================================================================

func _build_bell_top_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# Crown dome - top portion of bell
	var rings: int = 3
	var segs: int = 12

	for ring in range(rings + 1):
		var t: float = float(ring) / float(rings)
		var y: float = -t * BELL_HEIGHT * 0.4
		var r: float = BELL_RADIUS * 0.3 * (0.2 + t * 0.8)

		var ring_pts: Array[Vector3] = []
		for s in range(segs):
			var angle: float = float(s) * TAU / float(segs)
			ring_pts.append(Vector3(cos(angle) * r, y, sin(angle) * r))

		# Horizontal ring
		for i in range(segs):
			verts.append(ring_pts[i])
			verts.append(ring_pts[(i + 1) % segs])

	# Vertical meridians
	for s in range(0, segs, 3):
		var angle: float = float(s) * TAU / float(segs)
		for ring in range(rings):
			var t1: float = float(ring) / float(rings)
			var t2: float = float(ring + 1) / float(rings)
			var y1: float = -t1 * BELL_HEIGHT * 0.4
			var y2: float = -t2 * BELL_HEIGHT * 0.4
			var r1: float = BELL_RADIUS * 0.3 * (0.2 + t1 * 0.8)
			var r2: float = BELL_RADIUS * 0.3 * (0.2 + t2 * 0.8)

			verts.append(Vector3(cos(angle) * r1, y1, sin(angle) * r1))
			verts.append(Vector3(cos(angle) * r2, y2, sin(angle) * r2))

	# Top point
	for s in range(0, segs, 3):
		var angle: float = float(s) * TAU / float(segs)
		verts.append(Vector3(0, 0, 0))
		verts.append(Vector3(cos(angle) * BELL_RADIUS * 0.06, -BELL_HEIGHT * 0.05, sin(angle) * BELL_RADIUS * 0.06))

	_add_mesh_to_segment(segment, verts)


func _build_bell_mid_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# Middle section of bell - widening dome
	var rings: int = 4
	var segs: int = 16

	for ring in range(rings + 1):
		var t: float = float(ring) / float(rings)
		var y: float = -t * BELL_HEIGHT * 0.5
		# Bell widens following parabolic curve
		var r: float = BELL_RADIUS * (0.3 + t * 0.5)

		var ring_pts: Array[Vector3] = []
		for s in range(segs):
			var angle: float = float(s) * TAU / float(segs)
			ring_pts.append(Vector3(cos(angle) * r, y, sin(angle) * r))

		for i in range(segs):
			verts.append(ring_pts[i])
			verts.append(ring_pts[(i + 1) % segs])

	# Meridians
	for s in range(0, segs, 2):
		var angle: float = float(s) * TAU / float(segs)
		for ring in range(rings):
			var t1: float = float(ring) / float(rings)
			var t2: float = float(ring + 1) / float(rings)
			var y1: float = -t1 * BELL_HEIGHT * 0.5
			var y2: float = -t2 * BELL_HEIGHT * 0.5
			var r1: float = BELL_RADIUS * (0.3 + t1 * 0.5)
			var r2: float = BELL_RADIUS * (0.3 + t2 * 0.5)

			verts.append(Vector3(cos(angle) * r1, y1, sin(angle) * r1))
			verts.append(Vector3(cos(angle) * r2, y2, sin(angle) * r2))

	# Gonad patterns (4-fold symmetry)
	for g in range(4):
		var base_angle: float = float(g) * TAU / 4.0 + PI / 4.0
		var gonad_r: float = BELL_RADIUS * 0.45
		var gonad_y: float = -BELL_HEIGHT * 0.25

		var arc_pts: Array[Vector3] = []
		for j in range(7):
			var arc_t: float = float(j) / 6.0 - 0.5
			var arc_angle: float = base_angle + arc_t * 0.6
			var r: float = gonad_r + sin(abs(arc_t) * PI) * 3.0
			arc_pts.append(Vector3(cos(arc_angle) * r, gonad_y, sin(arc_angle) * r))

		for j in range(arc_pts.size() - 1):
			verts.append(arc_pts[j])
			verts.append(arc_pts[j + 1])

	_add_mesh_to_segment(segment, verts)


func _build_bell_rim_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# Rim of bell with scalloped edge
	var segs: int = 16
	var rim_r: float = BELL_RADIUS * 0.95

	# Main rim ring
	var rim_pts: Array[Vector3] = []
	for s in range(segs):
		var angle: float = float(s) * TAU / float(segs)
		rim_pts.append(Vector3(cos(angle) * rim_r, 0, sin(angle) * rim_r))

	for i in range(segs):
		verts.append(rim_pts[i])
		verts.append(rim_pts[(i + 1) % segs])

	# Scalloped edge (dips between segments)
	for s in range(segs):
		var angle: float = float(s) * TAU / float(segs)
		var next_angle: float = float(s + 1) * TAU / float(segs)
		var mid_angle: float = (angle + next_angle) / 2.0

		var scallop_pt := Vector3(
			cos(mid_angle) * rim_r * 1.02,
			-1.5,
			sin(mid_angle) * rim_r * 1.02
		)
		verts.append(rim_pts[s])
		verts.append(scallop_pt)
		verts.append(scallop_pt)
		verts.append(rim_pts[(s + 1) % segs])

	# Radial canals to rim
	for i in range(4):
		var angle: float = float(i) * TAU / 4.0
		verts.append(Vector3(cos(angle) * 2.0, 0, sin(angle) * 2.0))
		verts.append(Vector3(cos(angle) * rim_r * 0.9, -0.5, sin(angle) * rim_r * 0.9))

	_add_mesh_to_segment(segment, verts)


func _build_oral_arms_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# 4 frilly oral arms
	for arm in range(4):
		var base_angle: float = float(arm) * TAU / 4.0
		var arm_segs: int = 6
		var prev_center := Vector3(cos(base_angle) * 2.0, 0, sin(base_angle) * 2.0)
		var prev_left := prev_center
		var prev_right := prev_center

		for s in range(arm_segs):
			var t: float = float(s + 1) / float(arm_segs)
			var y: float = -t * ORAL_ARM_LENGTH * 0.5

			var spread: float = 1.5 + t * 4.0
			var wave: float = sin(t * PI * 2.5) * 1.5

			var center := Vector3(
				cos(base_angle) * (2.0 + t * 1.5),
				y,
				sin(base_angle) * (2.0 + t * 1.5)
			)

			var left := Vector3(
				cos(base_angle - 0.25) * (2.0 + spread + wave),
				y - wave * 0.2,
				sin(base_angle - 0.25) * (2.0 + spread + wave)
			)

			var right := Vector3(
				cos(base_angle + 0.25) * (2.0 + spread - wave),
				y + wave * 0.2,
				sin(base_angle + 0.25) * (2.0 + spread - wave)
			)

			verts.append(prev_center)
			verts.append(center)
			verts.append(prev_left)
			verts.append(left)
			verts.append(prev_right)
			verts.append(right)

			if s % 2 == 0:
				verts.append(center)
				verts.append(left)
				verts.append(center)
				verts.append(right)

			prev_center = center
			prev_left = left
			prev_right = right

	_add_mesh_to_segment(segment, verts)


func _build_tentacles_upper_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# 8 tentacles - upper portion
	for tent in range(8):
		var angle: float = float(tent) * TAU / 8.0
		var base := Vector3(cos(angle) * BELL_RADIUS * 0.85, 0, sin(angle) * BELL_RADIUS * 0.85)
		var tent_segs: int = 6
		var prev_pt := base

		for s in range(tent_segs):
			var t: float = float(s + 1) / float(tent_segs)
			var y: float = -t * TENTACLE_LENGTH * 0.4

			# Gentle wave
			var wave_x: float = sin(t * PI * 1.5 + angle) * 2.0 * t
			var wave_z: float = cos(t * PI * 1.2 + angle * 0.5) * 1.5 * t

			var pt := Vector3(
				base.x * (1.0 + t * 0.2) + wave_x,
				y,
				base.z * (1.0 + t * 0.2) + wave_z
			)

			verts.append(prev_pt)
			verts.append(pt)
			prev_pt = pt

	_add_mesh_to_segment(segment, verts)


func _build_tentacles_lower_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# 8 tentacles - lower portion (thinner, more trailing)
	for tent in range(8):
		var angle: float = float(tent) * TAU / 8.0
		var base := Vector3(cos(angle) * BELL_RADIUS * 0.95, 0, sin(angle) * BELL_RADIUS * 0.95)
		var tent_segs: int = 6
		var prev_pt := base

		for s in range(tent_segs):
			var t: float = float(s + 1) / float(tent_segs)
			var y: float = -t * TENTACLE_LENGTH * 0.5

			# More pronounced wave at ends
			var wave_x: float = sin(t * PI * 2.0 + angle) * 4.0 * t
			var wave_z: float = cos(t * PI * 1.8 + angle * 0.7) * 3.0 * t

			var pt := Vector3(
				base.x * (1.0 + t * 0.3) + wave_x,
				y,
				base.z * (1.0 + t * 0.3) + wave_z
			)

			verts.append(prev_pt)
			verts.append(pt)
			prev_pt = pt

	_add_mesh_to_segment(segment, verts)


## ============================================================================
## BLOOP ANIMATION API
## ============================================================================

## Start the bloop animation (3 times for "bloop bloop bloop")
func start_bloop(count: int = 3) -> void:
	if is_blooping:
		return

	is_blooping = true
	bloop_count = 0
	target_bloop_count = count
	bloop_phase = 0.0
	print("[JELLYFISH] Starting bloop x", count)


## Update bloop animation (call in _process)
func update_bloop(delta: float) -> void:
	if not is_blooping:
		return

	bloop_phase += delta / BLOOP_DURATION

	if bloop_phase >= 1.0:
		bloop_phase = 0.0
		bloop_count += 1
		if bloop_count >= target_bloop_count:
			is_blooping = false
			_reset_segments()
			return

	# Calculate bloop deformation
	# Phase 0-0.4: contract (squish down)
	# Phase 0.4-1.0: expand (return to normal)
	var squish_amount: float
	if bloop_phase < 0.4:
		var t: float = bloop_phase / 0.4
		squish_amount = 1.0 - (1.0 - BLOOP_SQUISH) * sin(t * PI / 2.0)
	else:
		var t: float = (bloop_phase - 0.4) / 0.6
		squish_amount = BLOOP_SQUISH + (1.0 - BLOOP_SQUISH) * sin(t * PI / 2.0)

	var expand_amount: float
	if bloop_phase < 0.4:
		var t: float = bloop_phase / 0.4
		expand_amount = 1.0 + (BLOOP_EXPAND - 1.0) * sin(t * PI / 2.0)
	else:
		var t: float = (bloop_phase - 0.4) / 0.6
		expand_amount = BLOOP_EXPAND - (BLOOP_EXPAND - 1.0) * sin(t * PI / 2.0)

	# Apply to bell segments (Y scale = squish, XZ scale = expand)
	segment_bell_top.scale = Vector3(expand_amount, squish_amount, expand_amount)
	segment_bell_mid.scale = Vector3(expand_amount * 1.1, squish_amount * 0.9, expand_amount * 1.1)
	segment_bell_rim.scale = Vector3(expand_amount * 1.15, squish_amount * 0.85, expand_amount * 1.15)

	# Tentacles trail behind (delayed reaction)
	var trail_delay: float = 0.15
	var trail_phase: float = clampf(bloop_phase - trail_delay, 0.0, 1.0)

	# Tentacles swing outward during push
	var swing_amount: float = sin(trail_phase * PI) * 0.2
	segment_tentacles_upper.rotation.x = swing_amount
	segment_tentacles_lower.rotation.x = swing_amount * 0.5


func _reset_segments() -> void:
	for seg in all_segments:
		seg.scale = Vector3.ONE
		seg.rotation = Vector3.ZERO


## Check if currently blooping
func is_currently_blooping() -> bool:
	return is_blooping


## ============================================================================
## PUBLIC API
## ============================================================================

func get_segment(index: int) -> Node3D:
	if index < 0 or index >= all_segments.size():
		return null
	return all_segments[index]


func get_segment_count() -> int:
	return all_segments.size()


func get_bell_radius() -> float:
	return BELL_RADIUS


func get_bell_height() -> float:
	return BELL_HEIGHT
