extends Node3D
class_name WireframeFish
## ============================================================================
## WIREFRAME FISH - Electric Blue Neon Outline
## Structured for swim and hunt animation rigging
##
## BONE STRUCTURE (for future rigging):
##   - head_bone: Segments 0-3 (nose to gills)
##   - spine_1: Segment 4-5
##   - spine_2: Segment 5-6
##   - spine_3: Segment 6-7
##   - spine_4: Segment 7-8
##   - spine_5: Segment 8-9
##   - tail_base: Segment 9-10 (peduncle)
##   - tail_fin: Segment 10-11 (caudal fin)
##   - dorsal_fin: Attached to spine_1 through spine_4
##   - pectoral_L/R: Attached to head_bone end
##   - anal_fin: Attached to spine_4/5
##
## ANIMATION TARGETS:
##   - Swimming: S-wave through spine segments, tail oscillation
##   - Hunting: Mouth open, pectoral flare, lunge forward
## ============================================================================

# Fish dimensions (units)
const FISH_LENGTH: float = 50.0
const FISH_HEIGHT: float = 15.0
const FISH_WIDTH: float = 8.0

# Segment positions along length (0.0 = nose, 1.0 = tail tip)
const SEGMENTS: Array[float] = [
	0.0,   # 0: Nose tip
	0.06,  # 1: Upper jaw
	0.12,  # 2: Eye position
	0.20,  # 3: Gill/head end
	0.30,  # 4: Body start
	0.42,  # 5: Body mid-front
	0.54,  # 6: Body center (widest)
	0.66,  # 7: Body mid-back
	0.78,  # 8: Body end
	0.88,  # 9: Tail peduncle start
	0.94,  # 10: Tail peduncle end
	1.0    # 11: Tail tip
]

# Height profile at each segment (multiplier of FISH_HEIGHT)
const HEIGHT_PROFILE: Array[float] = [
	0.15,  # 0: Nose (narrow)
	0.25,  # 1: Jaw
	0.45,  # 2: Eye
	0.65,  # 3: Gills
	0.80,  # 4: Body start
	0.95,  # 5: Growing
	1.0,   # 6: Widest
	0.90,  # 7: Tapering
	0.70,  # 8: Narrowing
	0.35,  # 9: Peduncle
	0.25,  # 10: Peduncle end
	0.0    # 11: Tail tip (spreads into fin)
]

# Width profile at each segment (multiplier of FISH_WIDTH)
const WIDTH_PROFILE: Array[float] = [
	0.1,   # 0: Nose
	0.3,   # 1: Jaw
	0.6,   # 2: Eye
	0.8,   # 3: Gills
	0.95,  # 4: Body
	1.0,   # 5: Widest
	1.0,   # 6: Widest
	0.85,  # 7: Tapering
	0.6,   # 8: Narrowing
	0.3,   # 9: Peduncle
	0.2,   # 10: Peduncle end
	0.05   # 11: Tail tip
]

# Electric blue color
const WIRE_COLOR: Color = Color(0.0, 0.85, 1.0, 1.0)

# Mesh instance
var mesh_instance: MeshInstance3D
var wireframe_mesh: ArrayMesh

# Segment positions (for future animation access)
var segment_positions: Array[Vector3] = []


func _ready() -> void:
	_create_wireframe_mesh()


func _create_wireframe_mesh() -> void:
	wireframe_mesh = ArrayMesh.new()
	var vertices: PackedVector3Array = PackedVector3Array()

	# Calculate all segment center positions
	segment_positions.clear()
	for i in range(SEGMENTS.size()):
		var x: float = (SEGMENTS[i] - 0.5) * FISH_LENGTH  # Center fish at origin
		segment_positions.append(Vector3(x, 0, 0))

	# =========================================================================
	# BODY CROSS-SECTION RIBS
	# Each segment gets an octagonal cross-section for 3D wireframe effect
	# =========================================================================
	for i in range(SEGMENTS.size() - 1):  # Skip tail tip (point)
		var x: float = segment_positions[i].x
		var h: float = HEIGHT_PROFILE[i] * FISH_HEIGHT * 0.5
		var w: float = WIDTH_PROFILE[i] * FISH_WIDTH * 0.5

		# Skip if too small (nose/tail)
		if h < 1.0 and i != 2:  # Keep eye segment
			continue

		# 8-point cross-section (octagon)
		var rib_points: Array[Vector3] = []
		for angle_idx in range(8):
			var angle: float = angle_idx * PI / 4.0
			var y: float = cos(angle) * h
			var z: float = sin(angle) * w
			rib_points.append(Vector3(x, y, z))

		# Connect rib points in a loop
		for j in range(8):
			vertices.append(rib_points[j])
			vertices.append(rib_points[(j + 1) % 8])

	# =========================================================================
	# LONGITUDINAL SPINE LINES (connect ribs)
	# =========================================================================
	# Top spine
	for i in range(SEGMENTS.size() - 1):
		var x1: float = segment_positions[i].x
		var x2: float = segment_positions[i + 1].x
		var h1: float = HEIGHT_PROFILE[i] * FISH_HEIGHT * 0.5
		var h2: float = HEIGHT_PROFILE[i + 1] * FISH_HEIGHT * 0.5
		vertices.append(Vector3(x1, h1, 0))
		vertices.append(Vector3(x2, h2, 0))

	# Bottom spine
	for i in range(SEGMENTS.size() - 1):
		var x1: float = segment_positions[i].x
		var x2: float = segment_positions[i + 1].x
		var h1: float = HEIGHT_PROFILE[i] * FISH_HEIGHT * 0.5
		var h2: float = HEIGHT_PROFILE[i + 1] * FISH_HEIGHT * 0.5
		vertices.append(Vector3(x1, -h1, 0))
		vertices.append(Vector3(x2, -h2, 0))

	# Side spines (left and right)
	for side in [-1.0, 1.0]:
		for i in range(SEGMENTS.size() - 1):
			var x1: float = segment_positions[i].x
			var x2: float = segment_positions[i + 1].x
			var w1: float = WIDTH_PROFILE[i] * FISH_WIDTH * 0.5 * side
			var w2: float = WIDTH_PROFILE[i + 1] * FISH_WIDTH * 0.5 * side
			vertices.append(Vector3(x1, 0, w1))
			vertices.append(Vector3(x2, 0, w2))

	# =========================================================================
	# HEAD DETAILS
	# =========================================================================
	var head_x: float = segment_positions[0].x
	var eye_x: float = segment_positions[2].x
	var jaw_x: float = segment_positions[1].x
	var gill_x: float = segment_positions[3].x

	# Eye circles (left and right) - small octagons
	var eye_y: float = HEIGHT_PROFILE[2] * FISH_HEIGHT * 0.25
	var eye_z_offset: float = WIDTH_PROFILE[2] * FISH_WIDTH * 0.3
	var eye_radius: float = 1.5

	for side in [-1.0, 1.0]:
		var eye_center := Vector3(eye_x, eye_y, eye_z_offset * side)
		var eye_points: Array[Vector3] = []
		for angle_idx in range(6):
			var angle: float = angle_idx * PI / 3.0
			eye_points.append(eye_center + Vector3(0, cos(angle) * eye_radius, sin(angle) * eye_radius * 0.5))
		for j in range(6):
			vertices.append(eye_points[j])
			vertices.append(eye_points[(j + 1) % 6])

	# Mouth line (for hunt animation - this will open)
	var mouth_h: float = HEIGHT_PROFILE[1] * FISH_HEIGHT * 0.3
	vertices.append(Vector3(head_x, 0, 0))
	vertices.append(Vector3(jaw_x, -mouth_h, 0))
	vertices.append(Vector3(head_x, 0, 0))
	vertices.append(Vector3(jaw_x, mouth_h * 0.5, 0))

	# Gill slits (2 diagonal lines on each side)
	var gill_h: float = HEIGHT_PROFILE[3] * FISH_HEIGHT * 0.4
	var gill_w: float = WIDTH_PROFILE[3] * FISH_WIDTH * 0.5
	for side in [-1.0, 1.0]:
		vertices.append(Vector3(gill_x - 1, gill_h * 0.6, gill_w * 0.8 * side))
		vertices.append(Vector3(gill_x + 1, -gill_h * 0.3, gill_w * 0.9 * side))
		vertices.append(Vector3(gill_x - 2, gill_h * 0.4, gill_w * 0.85 * side))
		vertices.append(Vector3(gill_x, -gill_h * 0.4, gill_w * 0.95 * side))

	# =========================================================================
	# DORSAL FIN (top fin - segments 4-8)
	# =========================================================================
	var dorsal_points: Array[Vector3] = []
	var dorsal_segments: Array[int] = [4, 5, 6, 7, 8]

	for seg_idx in dorsal_segments:
		var x: float = segment_positions[seg_idx].x
		var base_h: float = HEIGHT_PROFILE[seg_idx] * FISH_HEIGHT * 0.5
		dorsal_points.append(Vector3(x, base_h, 0))

	# Fin peak points (raised above body)
	var dorsal_peaks: Array[Vector3] = []
	var fin_heights: Array[float] = [4.0, 6.0, 7.0, 5.0, 3.0]
	for i in range(dorsal_segments.size()):
		var base_pt: Vector3 = dorsal_points[i]
		dorsal_peaks.append(Vector3(base_pt.x, base_pt.y + fin_heights[i], 0))

	# Connect base to peaks (fin rays)
	for i in range(dorsal_points.size()):
		vertices.append(dorsal_points[i])
		vertices.append(dorsal_peaks[i])

	# Connect peaks (fin edge)
	for i in range(dorsal_peaks.size() - 1):
		vertices.append(dorsal_peaks[i])
		vertices.append(dorsal_peaks[i + 1])

	# Leading and trailing edges
	vertices.append(dorsal_points[0])
	vertices.append(dorsal_peaks[0])
	vertices.append(dorsal_points[dorsal_points.size() - 1])
	vertices.append(dorsal_peaks[dorsal_peaks.size() - 1])

	# =========================================================================
	# CAUDAL FIN (tail fin - forked)
	# =========================================================================
	var tail_base_x: float = segment_positions[10].x
	var tail_tip_x: float = segment_positions[11].x
	var tail_h: float = HEIGHT_PROFILE[10] * FISH_HEIGHT * 0.5

	# Fork points
	var tail_fork_top := Vector3(tail_tip_x + 6, 8, 0)
	var tail_fork_bot := Vector3(tail_tip_x + 6, -8, 0)
	var tail_fork_mid := Vector3(tail_tip_x + 2, 0, 0)

	# Main tail rays
	vertices.append(Vector3(tail_base_x, tail_h, 0))
	vertices.append(tail_fork_top)
	vertices.append(Vector3(tail_base_x, -tail_h, 0))
	vertices.append(tail_fork_bot)
	vertices.append(Vector3(tail_base_x, 0, 0))
	vertices.append(tail_fork_mid)

	# Fork edges
	vertices.append(tail_fork_top)
	vertices.append(tail_fork_mid)
	vertices.append(tail_fork_bot)
	vertices.append(tail_fork_mid)

	# Intermediate rays
	vertices.append(Vector3(tail_base_x, tail_h * 0.5, 0))
	vertices.append(Vector3(tail_tip_x + 4, 5, 0))
	vertices.append(Vector3(tail_base_x, -tail_h * 0.5, 0))
	vertices.append(Vector3(tail_tip_x + 4, -5, 0))

	# Connect fork outer edge
	vertices.append(tail_fork_top)
	vertices.append(Vector3(tail_tip_x + 4, 5, 0))
	vertices.append(tail_fork_bot)
	vertices.append(Vector3(tail_tip_x + 4, -5, 0))

	# =========================================================================
	# PECTORAL FINS (side fins near gills - important for hunt animation)
	# =========================================================================
	var pec_x: float = segment_positions[3].x + 2
	var pec_y: float = -HEIGHT_PROFILE[3] * FISH_HEIGHT * 0.2
	var pec_w: float = WIDTH_PROFILE[3] * FISH_WIDTH * 0.5

	for side in [-1.0, 1.0]:
		var pec_base := Vector3(pec_x, pec_y, pec_w * side)
		var pec_tip := Vector3(pec_x + 8, pec_y - 3, (pec_w + 6) * side)
		var pec_back := Vector3(pec_x + 10, pec_y, (pec_w + 2) * side)

		# Fin outline
		vertices.append(pec_base)
		vertices.append(pec_tip)
		vertices.append(pec_tip)
		vertices.append(pec_back)
		vertices.append(pec_back)
		vertices.append(pec_base)

		# Fin rays
		var pec_mid := Vector3(pec_x + 5, pec_y - 1.5, (pec_w + 4) * side)
		vertices.append(pec_base)
		vertices.append(pec_mid)
		vertices.append(pec_mid)
		vertices.append(pec_tip)
		vertices.append(pec_mid)
		vertices.append(pec_back)

	# =========================================================================
	# ANAL FIN (bottom rear fin)
	# =========================================================================
	var anal_segments: Array[int] = [7, 8, 9]
	var anal_points: Array[Vector3] = []

	for seg_idx in anal_segments:
		var x: float = segment_positions[seg_idx].x
		var base_h: float = -HEIGHT_PROFILE[seg_idx] * FISH_HEIGHT * 0.5
		anal_points.append(Vector3(x, base_h, 0))

	var anal_peaks: Array[Vector3] = []
	var anal_depths: Array[float] = [3.0, 4.0, 2.5]
	for i in range(anal_segments.size()):
		var base_pt: Vector3 = anal_points[i]
		anal_peaks.append(Vector3(base_pt.x, base_pt.y - anal_depths[i], 0))

	# Fin rays
	for i in range(anal_points.size()):
		vertices.append(anal_points[i])
		vertices.append(anal_peaks[i])

	# Fin edge
	for i in range(anal_peaks.size() - 1):
		vertices.append(anal_peaks[i])
		vertices.append(anal_peaks[i + 1])

	# =========================================================================
	# PELVIC FINS (small fins on belly)
	# =========================================================================
	var pelv_x: float = segment_positions[5].x
	var pelv_y: float = -HEIGHT_PROFILE[5] * FISH_HEIGHT * 0.45
	var pelv_w: float = WIDTH_PROFILE[5] * FISH_WIDTH * 0.3

	for side in [-1.0, 1.0]:
		var pelv_base := Vector3(pelv_x, pelv_y, pelv_w * side)
		var pelv_tip := Vector3(pelv_x + 4, pelv_y - 2.5, (pelv_w + 2) * side)
		vertices.append(pelv_base)
		vertices.append(pelv_tip)

	# =========================================================================
	# CREATE MESH
	# =========================================================================
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices

	wireframe_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_LINES, arrays)

	# Create material - electric blue, unshaded, no glow
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
# PUBLIC API FOR FUTURE ANIMATION
# ============================================================================

## Get segment world position (for rigging/animation)
func get_segment_position(segment_index: int) -> Vector3:
	if segment_index < 0 or segment_index >= segment_positions.size():
		return Vector3.ZERO
	return global_transform * segment_positions[segment_index]


## Get total number of segments
func get_segment_count() -> int:
	return segment_positions.size()


## Get fish length
func get_fish_length() -> float:
	return FISH_LENGTH


## Get fish center (for positioning)
func get_center() -> Vector3:
	return global_position
