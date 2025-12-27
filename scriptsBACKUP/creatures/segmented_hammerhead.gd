class_name SegmentedHammerhead
extends Node3D
## ============================================================================
## DONK_TANK - Segmented Wireframe Hammerhead Shark
##
## Anatomically accurate great hammerhead (Sphyrna mokarran) built as
## articulated segments for smooth swimming animation.
##
## ORIENTATION: Shark faces -Z direction (Godot's forward convention)
##   - Nose/Hammer at -Z
##   - Tail at +Z
##   - Dorsal fin up (+Y)
##   - Pectoral fins spread on X axis
##
## SEGMENTS (pivot at FRONT of each segment):
##   0. Hammer (cephalofoil) - electroreception scanning
##   1. Head/Neck - connects hammer to body
##   2. Front Body - pectoral fins, gills
##   3. Mid Body - dorsal fin, thickest part
##   4. Rear Body - second dorsal, narrowing
##   5. Tail - caudal fin, maximum thrust
##
## PERFORMANCE: 6 Node3D rotations per frame = trivial CPU cost
## ============================================================================

# Shark dimensions
const SHARK_LENGTH: float = 70.0
const SHARK_HEIGHT: float = 18.0
const SHARK_WIDTH: float = 12.0
const HAMMER_WIDTH: float = 25.0

## ============================================================================
## ELECTRIC NEON COLOR PALETTE
## All colors are bright, saturated neon/electric style to match the wireframe aesthetic
## ============================================================================

const NEON_COLORS: Array[Color] = [
	Color(0.0, 0.85, 1.0, 1.0),    # Electric Blue (default)
	Color(0.0, 1.0, 0.9, 1.0),     # Cyan/Teal
	Color(0.6, 0.0, 1.0, 1.0),     # Electric Purple
	Color(0.85, 0.0, 1.0, 1.0),    # Magenta/Pink
	Color(1.0, 0.0, 0.5, 1.0),     # Hot Pink
	Color(1.0, 0.2, 0.0, 1.0),     # Electric Orange
	Color(1.0, 1.0, 0.0, 1.0),     # Electric Yellow
	Color(0.5, 1.0, 0.0, 1.0),     # Lime Green
	Color(0.0, 1.0, 0.4, 1.0),     # Electric Green
	Color(0.0, 1.0, 0.7, 1.0),     # Aqua/Seafoam
	Color(0.3, 0.5, 1.0, 1.0),     # Soft Blue
]

# Current color index
var _color_index: int = 0

# Default starting color
var current_color: Color = NEON_COLORS[0]

# Segment boundaries (normalized 0-1 along body, 0=nose, 1=tail)
const SEGMENT_BOUNDS: Array[float] = [
	0.0,    # Hammer tip (nose)
	0.14,   # Hammer end / Head start
	0.28,   # Head end / Front body start
	0.48,   # Front body end / Mid body start
	0.70,   # Mid body end / Rear body start
	0.88,   # Rear body end / Tail start
	1.0     # Tail tip
]

# Segment nodes (for animation access)
var segment_hammer: Node3D
var segment_head: Node3D
var segment_front: Node3D
var segment_mid: Node3D
var segment_rear: Node3D
var segment_tail: Node3D

# All segments array for iteration
var all_segments: Array[Node3D] = []

# Material (shared for performance)
var wire_material: StandardMaterial3D


func _ready() -> void:
	# Randomize starting color so each shark is unique!
	_color_index = randi() % NEON_COLORS.size()
	current_color = NEON_COLORS[_color_index]

	_create_material()
	_create_segments()

	print("[SHARK] Spawned with color: ", get_color_name())


func _create_material() -> void:
	wire_material = StandardMaterial3D.new()
	wire_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	wire_material.albedo_color = current_color
	wire_material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED


## ============================================================================
## COLOR CYCLING API
## ============================================================================

## Cycle to the next color in the palette
func cycle_color() -> void:
	_color_index = (_color_index + 1) % NEON_COLORS.size()
	set_color(NEON_COLORS[_color_index])


## Cycle to a random different color
func cycle_color_random() -> void:
	var new_index: int = _color_index
	# Make sure we get a different color
	while new_index == _color_index and NEON_COLORS.size() > 1:
		new_index = randi() % NEON_COLORS.size()
	_color_index = new_index
	set_color(NEON_COLORS[_color_index])


## Set a specific color by index
func set_color_by_index(index: int) -> void:
	if index < 0 or index >= NEON_COLORS.size():
		return
	_color_index = index
	set_color(NEON_COLORS[_color_index])


## Set a specific color directly
func set_color(color: Color) -> void:
	current_color = color
	if wire_material:
		wire_material.albedo_color = color


## Get current color
func get_color() -> Color:
	return current_color


## Get current color index
func get_color_index() -> int:
	return _color_index


## Get total number of colors in palette
func get_color_count() -> int:
	return NEON_COLORS.size()


## Get color name for UI/debug (optional)
func get_color_name() -> String:
	var names: Array[String] = [
		"Electric Blue", "Cyan", "Purple", "Magenta",
		"Hot Pink", "Orange", "Yellow", "Lime",
		"Green", "Aqua", "Soft Blue"
	]
	if _color_index < names.size():
		return names[_color_index]
	return "Unknown"


func _create_segments() -> void:
	# Create segment nodes as a chain (each is child of previous for proper rotation propagation)
	# Pivots are at the FRONT (toward nose) of each segment
	# Chain extends along -Z direction (nose at -Z, tail at +Z)

	# Hammer (pivot at front tip of hammer - the nose)
	segment_hammer = Node3D.new()
	segment_hammer.name = "Hammer"
	segment_hammer.position.z = _get_segment_z(0)  # Nose position
	add_child(segment_hammer)

	# Head (pivot at hammer-head junction)
	segment_head = Node3D.new()
	segment_head.name = "Head"
	segment_head.position.z = _get_segment_length(0, 1)  # Offset from parent
	segment_hammer.add_child(segment_head)

	# Front body (pivot at head-body junction)
	segment_front = Node3D.new()
	segment_front.name = "FrontBody"
	segment_front.position.z = _get_segment_length(1, 2)
	segment_head.add_child(segment_front)

	# Mid body
	segment_mid = Node3D.new()
	segment_mid.name = "MidBody"
	segment_mid.position.z = _get_segment_length(2, 3)
	segment_front.add_child(segment_mid)

	# Rear body
	segment_rear = Node3D.new()
	segment_rear.name = "RearBody"
	segment_rear.position.z = _get_segment_length(3, 4)
	segment_mid.add_child(segment_rear)

	# Tail
	segment_tail = Node3D.new()
	segment_tail.name = "Tail"
	segment_tail.position.z = _get_segment_length(4, 5)
	segment_rear.add_child(segment_tail)

	all_segments = [segment_hammer, segment_head, segment_front, segment_mid, segment_rear, segment_tail]

	# Build meshes for each segment
	_build_hammer_mesh(segment_hammer)
	_build_head_mesh(segment_head)
	_build_front_body_mesh(segment_front)
	_build_mid_body_mesh(segment_mid)
	_build_rear_body_mesh(segment_rear)
	_build_tail_mesh(segment_tail)


## Get Z position for a segment boundary (shark centered at origin)
## -Z = nose (front), +Z = tail (back)
func _get_segment_z(bound_idx: int) -> float:
	var normalized: float = SEGMENT_BOUNDS[bound_idx]
	# Map 0-1 to -half_length to +half_length
	return (normalized - 0.5) * SHARK_LENGTH


## Get length between two segment boundaries
func _get_segment_length(start_idx: int, end_idx: int) -> float:
	return (SEGMENT_BOUNDS[end_idx] - SEGMENT_BOUNDS[start_idx]) * SHARK_LENGTH


## Get body dimensions at a normalized position (0=nose, 1=tail)
func _get_body_size(pos: float) -> Vector2:
	# Height and width profiles (approximated from research)
	# Returns Vector2(height, width) at body position
	var h_profile: Array[float] = [0.3, 0.55, 0.85, 1.0, 0.7, 0.25, 0.0]
	var w_profile: Array[float] = [0.2, 0.6, 0.95, 1.0, 0.6, 0.2, 0.05]

	# Find which segment we're in
	var seg_idx: int = 0
	for i in range(SEGMENT_BOUNDS.size() - 1):
		if pos >= SEGMENT_BOUNDS[i] and pos < SEGMENT_BOUNDS[i + 1]:
			seg_idx = i
			break
	if pos >= 1.0:
		seg_idx = SEGMENT_BOUNDS.size() - 2

	# Lerp between segment boundaries
	var seg_start: float = SEGMENT_BOUNDS[seg_idx]
	var seg_end: float = SEGMENT_BOUNDS[seg_idx + 1]
	var t: float = (pos - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0.0
	var h: float = lerp(h_profile[seg_idx], h_profile[seg_idx + 1], t) * SHARK_HEIGHT * 0.5
	var w: float = lerp(w_profile[seg_idx], w_profile[seg_idx + 1], t) * SHARK_WIDTH * 0.5

	return Vector2(h, w)


## Create mesh and add to segment
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
## SEGMENT MESH BUILDERS
## All coordinates are LOCAL to each segment's origin
## Segment origin is at the FRONT (toward nose) of that segment
## Mesh extends in +Z direction (toward tail)
## ============================================================================

func _build_hammer_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()

	# Hammer dimensions
	var hw: float = HAMMER_WIDTH * 0.5  # Half width (X axis)
	var hd: float = _get_segment_length(0, 1)  # Hammer depth (Z axis)
	var hh: float = 4.0  # Hammer height (Y axis)

	# The hammer extends from Z=0 (tip/nose) to Z=hd (back where neck starts)

	# --- HAMMER TOP OUTLINE ---
	var top_pts: Array[Vector3] = [
		Vector3(-hw, hh * 0.6, 2.0),           # Left tip
		Vector3(-hw * 0.85, hh * 0.5, 0.5),    # Left front curve
		Vector3(0, hh * 0.4, 0),               # Center front (nose tip)
		Vector3(hw * 0.85, hh * 0.5, 0.5),     # Right front curve
		Vector3(hw, hh * 0.6, 2.0),            # Right tip
	]

	# --- HAMMER BOTTOM OUTLINE ---
	var bot_pts: Array[Vector3] = [
		Vector3(-hw, -hh * 0.4, 2.0),
		Vector3(-hw * 0.85, -hh * 0.3, 0.5),
		Vector3(0, -hh * 0.3, 0),
		Vector3(hw * 0.85, -hh * 0.3, 0.5),
		Vector3(hw, -hh * 0.4, 2.0),
	]

	# Draw front edge (top)
	for i in range(top_pts.size() - 1):
		verts.append(top_pts[i])
		verts.append(top_pts[i + 1])

	# Draw front edge (bottom)
	for i in range(bot_pts.size() - 1):
		verts.append(bot_pts[i])
		verts.append(bot_pts[i + 1])

	# Connect top to bottom (vertical edges)
	for i in range(top_pts.size()):
		verts.append(top_pts[i])
		verts.append(bot_pts[i])

	# --- BACK EDGE OF HAMMER (where it connects to head) ---
	var back_z: float = hd  # Back of hammer segment
	var back_hw: float = hw * 0.65  # Narrower at back
	var back_top_l := Vector3(-back_hw, hh * 0.7, back_z)
	var back_top_r := Vector3(back_hw, hh * 0.7, back_z)
	var back_bot_l := Vector3(-back_hw, -hh * 0.5, back_z)
	var back_bot_r := Vector3(back_hw, -hh * 0.5, back_z)

	# Connect hammer tips to back
	verts.append(top_pts[0])
	verts.append(back_top_l)
	verts.append(top_pts[4])
	verts.append(back_top_r)
	verts.append(bot_pts[0])
	verts.append(back_bot_l)
	verts.append(bot_pts[4])
	verts.append(back_bot_r)

	# Back edge rectangle
	verts.append(back_top_l)
	verts.append(back_top_r)
	verts.append(back_bot_l)
	verts.append(back_bot_r)
	verts.append(back_top_l)
	verts.append(back_bot_l)
	verts.append(back_top_r)
	verts.append(back_bot_r)

	# --- EYES AT HAMMER TIPS ---
	for ex in [-hw + 1.5, hw - 1.5]:
		var eye_center := Vector3(ex, 0, 2.5)
		var eye_r: float = 1.8
		for j in range(8):
			var a1: float = j * PI / 4.0
			var a2: float = (j + 1) * PI / 4.0
			verts.append(eye_center + Vector3(0, cos(a1) * eye_r, sin(a1) * eye_r * 0.6))
			verts.append(eye_center + Vector3(0, cos(a2) * eye_r, sin(a2) * eye_r * 0.6))

	# --- LONGITUDINAL LINES ON HAMMER ---
	# Top center line
	verts.append(Vector3(0, hh * 0.4, 0))
	verts.append(Vector3(0, hh * 0.7, back_z))
	# Bottom center line
	verts.append(Vector3(0, -hh * 0.3, 0))
	verts.append(Vector3(0, -hh * 0.5, back_z))

	_add_mesh_to_segment(segment, verts)


func _build_head_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()
	var seg_length: float = _get_segment_length(1, 2)

	# Draw cross-section ribs along the head
	for i in range(3):
		var t: float = float(i) / 2.0
		var body_pos: float = lerp(SEGMENT_BOUNDS[1], SEGMENT_BOUNDS[2], t)
		var local_z: float = t * seg_length
		var size := _get_body_size(body_pos)

		_add_rib(verts, local_z, size.x, size.y)

	# Gill slits (5 per side)
	var gill_start_z: float = seg_length * 0.3
	for side in [-1.0, 1.0]:
		for g in range(5):
			var gz: float = gill_start_z + g * 2.0
			var size := _get_body_size(SEGMENT_BOUNDS[1] + 0.05)
			verts.append(Vector3(size.y * 0.9 * side, size.x * 0.6, gz))
			verts.append(Vector3((size.y + 0.5) * side, -size.x * 0.4, gz + 1.5))

	# Spine lines connecting ribs
	_add_spine_lines(verts, 0.0, seg_length, SEGMENT_BOUNDS[1], SEGMENT_BOUNDS[2], 3)

	_add_mesh_to_segment(segment, verts)


func _build_front_body_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()
	var seg_length: float = _get_segment_length(2, 3)

	# Body ribs
	for i in range(4):
		var t: float = float(i) / 3.0
		var body_pos: float = lerp(SEGMENT_BOUNDS[2], SEGMENT_BOUNDS[3], t)
		var local_z: float = t * seg_length
		var size := _get_body_size(body_pos)

		_add_rib(verts, local_z, size.x, size.y)

	# Spine lines
	_add_spine_lines(verts, 0.0, seg_length, SEGMENT_BOUNDS[2], SEGMENT_BOUNDS[3], 4)

	# --- PECTORAL FINS ---
	var pec_z: float = seg_length * 0.25
	var pec_y: float = -SHARK_HEIGHT * 0.35
	var pec_w: float = SHARK_WIDTH * 0.5

	for side in [-1.0, 1.0]:
		var base := Vector3(pec_w * side, pec_y, pec_z)
		var tip := Vector3((pec_w + 12) * side, pec_y - 5, pec_z + 8)
		var back := Vector3((pec_w + 5) * side, pec_y - 1, pec_z + 14)
		var inner := Vector3(pec_w * 0.8 * side, pec_y, pec_z + 6)

		verts.append(base)
		verts.append(tip)
		verts.append(tip)
		verts.append(back)
		verts.append(back)
		verts.append(inner)
		verts.append(inner)
		verts.append(base)

		# Fin rays
		var mid := Vector3((pec_w + 6) * side, pec_y - 2, pec_z + 5)
		verts.append(base)
		verts.append(mid)
		verts.append(mid)
		verts.append(tip)

	# --- PRIMARY DORSAL FIN ---
	var dorsal_z: float = seg_length * 0.4
	var dorsal_base_h: float = SHARK_HEIGHT * 0.5
	var dorsal_peak := Vector3(0, dorsal_base_h + 14, dorsal_z + 4)
	var dorsal_back := Vector3(0, dorsal_base_h + 2, dorsal_z + 12)

	verts.append(Vector3(0, dorsal_base_h, dorsal_z))
	verts.append(dorsal_peak)
	verts.append(dorsal_peak)
	verts.append(dorsal_back)
	verts.append(dorsal_back)
	verts.append(Vector3(0, dorsal_base_h * 0.9, dorsal_z + 14))

	_add_mesh_to_segment(segment, verts)


func _build_mid_body_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()
	var seg_length: float = _get_segment_length(3, 4)

	# Body ribs (thickest part of shark)
	for i in range(4):
		var t: float = float(i) / 3.0
		var body_pos: float = lerp(SEGMENT_BOUNDS[3], SEGMENT_BOUNDS[4], t)
		var local_z: float = t * seg_length
		var size := _get_body_size(body_pos)

		_add_rib(verts, local_z, size.x, size.y)

	# Spine lines
	_add_spine_lines(verts, 0.0, seg_length, SEGMENT_BOUNDS[3], SEGMENT_BOUNDS[4], 4)

	# --- PELVIC FINS ---
	var pelv_z: float = seg_length * 0.5
	var pelv_y: float = -SHARK_HEIGHT * 0.45
	var pelv_w: float = SHARK_WIDTH * 0.35

	for side in [-1.0, 1.0]:
		var base := Vector3(pelv_w * side, pelv_y, pelv_z)
		var tip := Vector3((pelv_w + 4) * side, pelv_y - 2, pelv_z + 4)
		var back := Vector3((pelv_w + 1) * side, pelv_y, pelv_z + 5)

		verts.append(base)
		verts.append(tip)
		verts.append(tip)
		verts.append(back)
		verts.append(back)
		verts.append(base)

	_add_mesh_to_segment(segment, verts)


func _build_rear_body_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()
	var seg_length: float = _get_segment_length(4, 5)

	# Body ribs (narrowing toward tail)
	for i in range(4):
		var t: float = float(i) / 3.0
		var body_pos: float = lerp(SEGMENT_BOUNDS[4], SEGMENT_BOUNDS[5], t)
		var local_z: float = t * seg_length
		var size := _get_body_size(body_pos)

		_add_rib(verts, local_z, size.x, size.y)

	# Spine lines
	_add_spine_lines(verts, 0.0, seg_length, SEGMENT_BOUNDS[4], SEGMENT_BOUNDS[5], 4)

	# --- SECOND DORSAL FIN (small) ---
	var d2_z: float = seg_length * 0.3
	var d2_h: float = SHARK_HEIGHT * 0.25
	verts.append(Vector3(0, d2_h, d2_z))
	verts.append(Vector3(0, d2_h + 4, d2_z + 2))
	verts.append(Vector3(0, d2_h + 4, d2_z + 2))
	verts.append(Vector3(0, d2_h + 0.5, d2_z + 4))

	# --- ANAL FIN ---
	var anal_z: float = seg_length * 0.4
	var anal_y: float = -SHARK_HEIGHT * 0.3
	verts.append(Vector3(0, anal_y, anal_z))
	verts.append(Vector3(0, anal_y - 3, anal_z + 2))
	verts.append(Vector3(0, anal_y - 3, anal_z + 2))
	verts.append(Vector3(0, anal_y - 0.5, anal_z + 4))

	_add_mesh_to_segment(segment, verts)


func _build_tail_mesh(segment: Node3D) -> void:
	var verts := PackedVector3Array()
	var seg_length: float = _get_segment_length(5, 6)

	# Tail peduncle (narrow section)
	var ped_size := _get_body_size(SEGMENT_BOUNDS[5])

	# Peduncle rib at start
	_add_rib(verts, 0.0, ped_size.x, ped_size.y)

	# Keels on peduncle (horizontal stabilizers)
	for side in [-1.0, 1.0]:
		verts.append(Vector3(ped_size.y * 0.8 * side, 0, -2))
		verts.append(Vector3(ped_size.y * 0.5 * side, 0, 6))

	# --- CAUDAL FIN (asymmetric crescent - upper lobe larger) ---
	var tail_base_z: float = seg_length * 0.3
	var fork_top := Vector3(0, 14, seg_length + 6)
	var fork_bot := Vector3(0, -8, seg_length + 2)
	var notch := Vector3(0, 0, seg_length - 2)

	# Main structure
	verts.append(Vector3(0, ped_size.x * 0.8, tail_base_z))
	verts.append(fork_top)
	verts.append(Vector3(0, -ped_size.x * 0.8, tail_base_z))
	verts.append(fork_bot)
	verts.append(Vector3(0, 0, tail_base_z))
	verts.append(notch)

	# Crescent curves
	verts.append(fork_top)
	verts.append(notch)
	verts.append(fork_bot)
	verts.append(notch)

	# Intermediate rays
	verts.append(Vector3(0, ped_size.x * 0.5, tail_base_z))
	verts.append(Vector3(0, 8, seg_length + 3))
	verts.append(Vector3(0, -ped_size.x * 0.5, tail_base_z))
	verts.append(Vector3(0, -5, seg_length + 1))

	# Connect rays to fork
	verts.append(fork_top)
	verts.append(Vector3(0, 8, seg_length + 3))
	verts.append(fork_bot)
	verts.append(Vector3(0, -5, seg_length + 1))

	_add_mesh_to_segment(segment, verts)


## Helper: Add octagonal rib at Z position
func _add_rib(verts: PackedVector3Array, z: float, h: float, w: float) -> void:
	if h < 0.5:
		return

	var points: Array[Vector3] = []
	for i in range(8):
		var angle: float = i * PI / 4.0
		# Y = height (up/down), X = width (left/right), Z = position along body
		points.append(Vector3(sin(angle) * w, cos(angle) * h, z))

	for i in range(8):
		verts.append(points[i])
		verts.append(points[(i + 1) % 8])


## Helper: Add spine lines between two Z positions
func _add_spine_lines(verts: PackedVector3Array, z_start: float, z_end: float, body_start: float, body_end: float, divisions: int) -> void:
	for i in range(divisions - 1):
		var t1: float = float(i) / float(divisions - 1)
		var t2: float = float(i + 1) / float(divisions - 1)
		var z1: float = lerp(z_start, z_end, t1)
		var z2: float = lerp(z_start, z_end, t2)
		var body_pos1: float = lerp(body_start, body_end, t1)
		var body_pos2: float = lerp(body_start, body_end, t2)
		var size1 := _get_body_size(body_pos1)
		var size2 := _get_body_size(body_pos2)

		# Top spine (dorsal)
		verts.append(Vector3(0, size1.x, z1))
		verts.append(Vector3(0, size2.x, z2))

		# Bottom spine (ventral)
		verts.append(Vector3(0, -size1.x, z1))
		verts.append(Vector3(0, -size2.x, z2))

		# Side spines (left and right)
		verts.append(Vector3(size1.y, 0, z1))
		verts.append(Vector3(size2.y, 0, z2))
		verts.append(Vector3(-size1.y, 0, z1))
		verts.append(Vector3(-size2.y, 0, z2))


## ============================================================================
## PUBLIC API - For Spine Rig Integration
## ============================================================================

## Body positions for each segment (0=nose, 1=tail)
## These define where along the shark's body each segment's pivot point is
const SEGMENT_BODY_POSITIONS: Array[float] = [
	0.07,   # Hammer - near tip
	0.21,   # Head - behind hammer
	0.38,   # Front body - pectoral region
	0.59,   # Mid body - thickest part
	0.79,   # Rear body - narrowing
	0.94,   # Tail - near tip
]


## Get segment body positions for rig setup
func get_segment_body_positions() -> Array:
	return [0.07, 0.21, 0.38, 0.59, 0.79, 0.94]


## Get segment data for SwimController setup (legacy support)
func get_segment_data() -> Array:
	return [
		{ "node": segment_hammer, "body_position": 0.07 },
		{ "node": segment_head, "body_position": 0.21 },
		{ "node": segment_front, "body_position": 0.38 },
		{ "node": segment_mid, "body_position": 0.59 },
		{ "node": segment_rear, "body_position": 0.79 },
		{ "node": segment_tail, "body_position": 0.94 },
	]


## Apply rotations from spine rig to all segments
## rotations: Array of Vector3 (pitch, yaw, roll) for each segment
func apply_rig_rotations(rig: SharkSpineRig) -> void:
	if rig == null or all_segments.size() == 0:
		return

	for i in range(min(all_segments.size(), rig.get_segment_count())):
		var seg: Node3D = all_segments[i]
		if seg == null:
			continue

		var rot: Vector3 = rig.get_segment_rotation(i)
		# Apply rotation: pitch (X), yaw (Y), roll (Z)
		seg.rotation = Vector3(rot.x, rot.y, rot.z)


## Apply single segment rotation (for manual control)
func set_segment_rotation(index: int, rotation: Vector3) -> void:
	if index < 0 or index >= all_segments.size():
		return
	var seg: Node3D = all_segments[index]
	if seg:
		seg.rotation = rotation


## Get segment node by index
func get_segment(index: int) -> Node3D:
	if index < 0 or index >= all_segments.size():
		return null
	return all_segments[index]


## Get number of segments
func get_segment_count() -> int:
	return all_segments.size()


## Get shark length
func get_shark_length() -> float:
	return SHARK_LENGTH
