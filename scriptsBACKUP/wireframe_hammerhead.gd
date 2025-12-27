extends Node3D
class_name WireframeHammerhead
## ============================================================================
## WIREFRAME HAMMERHEAD SHARK - Electric Blue Neon Outline
## Anatomically accurate Sphyrna mokarran (Great Hammerhead)
##
## BONE STRUCTURE (for animation rigging):
##   - cephalofoil: The iconic hammer-shaped head (segments 0-3)
##   - head_base: Connection point hammer to body (segment 3)
##   - spine_1 through spine_6: Main body segments (4-9)
##   - tail_peduncle: Narrow tail base (segment 10)
##   - caudal_fin: Asymmetric crescent tail (segment 11)
##   - dorsal_primary: Large first dorsal (attached spine_2-3)
##   - dorsal_secondary: Small second dorsal (attached spine_5-6)
##   - pectoral_L/R: Large swept-back side fins (attached spine_1)
##   - pelvic_L/R: Small belly fins (attached spine_4)
##   - anal_fin: Small bottom fin (attached spine_5)
##
## ANIMATION TARGETS:
##   - Swimming: Powerful S-wave, minimal head movement, strong tail thrust
##   - Hunting: Head sweep side-to-side (electroreception scanning)
##   - Cruising: Slow undulation, pectorals slightly angled
## ============================================================================

# Hammerhead dimensions (units) - larger than the generic fish
const SHARK_LENGTH: float = 70.0
const SHARK_HEIGHT: float = 18.0  # Body height at thickest
const SHARK_WIDTH: float = 12.0   # Body width at thickest
const HAMMER_WIDTH: float = 25.0  # Cephalofoil span
const HAMMER_DEPTH: float = 8.0   # Hammer front-to-back

# Segment positions along length (0.0 = hammer front, 1.0 = tail tip)
const SEGMENTS: Array[float] = [
	0.0,    # 0: Hammer front edge (center)
	0.04,   # 1: Hammer mid-section
	0.08,   # 2: Hammer back edge / eye line
	0.14,   # 3: Head base (where hammer meets body)
	0.22,   # 4: Body start (gill area)
	0.32,   # 5: Body front (dorsal start)
	0.44,   # 6: Body center (thickest point)
	0.56,   # 7: Body mid-back
	0.68,   # 8: Body rear
	0.80,   # 9: Body end (dorsal 2 area)
	0.90,   # 10: Tail peduncle (narrow)
	1.0     # 11: Tail tip
]

# Height profile at each segment (multiplier of SHARK_HEIGHT)
const HEIGHT_PROFILE: Array[float] = [
	0.25,   # 0: Hammer front (flattened)
	0.30,   # 1: Hammer mid
	0.35,   # 2: Hammer back
	0.55,   # 3: Head base
	0.75,   # 4: Body start
	0.95,   # 5: Body front
	1.0,    # 6: Thickest
	0.90,   # 7: Mid-back
	0.70,   # 8: Rear
	0.50,   # 9: Body end
	0.25,   # 10: Peduncle (very narrow)
	0.0     # 11: Tail tip
]

# Width profile at each segment (multiplier of SHARK_WIDTH)
const WIDTH_PROFILE: Array[float] = [
	0.15,   # 0: Hammer front (thin vertically)
	0.20,   # 1: Hammer mid
	0.25,   # 2: Hammer back
	0.60,   # 3: Head base (transition)
	0.85,   # 4: Body start
	1.0,    # 5: Body front (widest)
	1.0,    # 6: Thickest
	0.85,   # 7: Mid-back
	0.65,   # 8: Rear
	0.45,   # 9: Body end
	0.20,   # 10: Peduncle
	0.05    # 11: Tail tip
]

# Electric blue color - same as the fish
const WIRE_COLOR: Color = Color(0.0, 0.85, 1.0, 1.0)

# Mesh components
var mesh_instance: MeshInstance3D
var wireframe_mesh: ArrayMesh

# Segment positions (for animation access)
var segment_positions: Array[Vector3] = []

# Key anatomical points for animation
var hammer_left_eye: Vector3
var hammer_right_eye: Vector3
var dorsal_peak: Vector3
var tail_fork_top: Vector3
var tail_fork_bottom: Vector3


func _ready() -> void:
	_create_wireframe_mesh()


func _create_wireframe_mesh() -> void:
	wireframe_mesh = ArrayMesh.new()
	var vertices: PackedVector3Array = PackedVector3Array()

	# Calculate all segment center positions
	segment_positions.clear()
	for i in range(SEGMENTS.size()):
		var x: float = (SEGMENTS[i] - 0.5) * SHARK_LENGTH  # Center shark at origin
		segment_positions.append(Vector3(x, 0, 0))

	# =========================================================================
	# CEPHALOFOIL (HAMMER HEAD) - The iconic T-shaped head
	# This is what makes a hammerhead a hammerhead
	# =========================================================================
	var hammer_front_x: float = segment_positions[0].x
	var hammer_mid_x: float = segment_positions[1].x
	var hammer_back_x: float = segment_positions[2].x
	var head_base_x: float = segment_positions[3].x

	# The hammer is a flattened T-shape viewed from above
	# Front edge curves slightly forward in center
	var hw: float = HAMMER_WIDTH * 0.5  # Half width
	var hd: float = HAMMER_DEPTH

	# Hammer outline - top view (looking down)
	# Front edge (curved forward in center)
	var hammer_outline_top: Array[Vector3] = []
	var hammer_outline_bot: Array[Vector3] = []
	var hammer_h: float = HEIGHT_PROFILE[1] * SHARK_HEIGHT * 0.5

	# Create hammer shape with proper curvature
	# Left tip
	hammer_outline_top.append(Vector3(hammer_mid_x, hammer_h * 0.6, -hw))
	hammer_outline_bot.append(Vector3(hammer_mid_x, -hammer_h * 0.4, -hw))

	# Left front corner
	hammer_outline_top.append(Vector3(hammer_front_x - 1, hammer_h * 0.5, -hw * 0.85))
	hammer_outline_bot.append(Vector3(hammer_front_x - 1, -hammer_h * 0.3, -hw * 0.85))

	# Center front (slightly forward)
	hammer_outline_top.append(Vector3(hammer_front_x - 2.5, hammer_h * 0.4, 0))
	hammer_outline_bot.append(Vector3(hammer_front_x - 2.5, -hammer_h * 0.3, 0))

	# Right front corner
	hammer_outline_top.append(Vector3(hammer_front_x - 1, hammer_h * 0.5, hw * 0.85))
	hammer_outline_bot.append(Vector3(hammer_front_x - 1, -hammer_h * 0.3, hw * 0.85))

	# Right tip
	hammer_outline_top.append(Vector3(hammer_mid_x, hammer_h * 0.6, hw))
	hammer_outline_bot.append(Vector3(hammer_mid_x, -hammer_h * 0.4, hw))

	# Draw hammer front edge (top)
	for i in range(hammer_outline_top.size() - 1):
		vertices.append(hammer_outline_top[i])
		vertices.append(hammer_outline_top[i + 1])

	# Draw hammer front edge (bottom)
	for i in range(hammer_outline_bot.size() - 1):
		vertices.append(hammer_outline_bot[i])
		vertices.append(hammer_outline_bot[i + 1])

	# Connect top to bottom at tips and center
	for i in range(hammer_outline_top.size()):
		vertices.append(hammer_outline_top[i])
		vertices.append(hammer_outline_bot[i])

	# Hammer back edge (where it narrows to head)
	var hammer_back_top_l := Vector3(hammer_back_x, hammer_h * 0.7, -hw * 0.7)
	var hammer_back_top_r := Vector3(hammer_back_x, hammer_h * 0.7, hw * 0.7)
	var hammer_back_bot_l := Vector3(hammer_back_x, -hammer_h * 0.5, -hw * 0.7)
	var hammer_back_bot_r := Vector3(hammer_back_x, -hammer_h * 0.5, hw * 0.7)

	# Connect tips to back
	vertices.append(hammer_outline_top[0])  # Left tip top
	vertices.append(hammer_back_top_l)
	vertices.append(hammer_outline_top[4])  # Right tip top
	vertices.append(hammer_back_top_r)
	vertices.append(hammer_outline_bot[0])  # Left tip bottom
	vertices.append(hammer_back_bot_l)
	vertices.append(hammer_outline_bot[4])  # Right tip bottom
	vertices.append(hammer_back_bot_r)

	# Back edge line
	vertices.append(hammer_back_top_l)
	vertices.append(hammer_back_top_r)
	vertices.append(hammer_back_bot_l)
	vertices.append(hammer_back_bot_r)
	vertices.append(hammer_back_top_l)
	vertices.append(hammer_back_bot_l)
	vertices.append(hammer_back_top_r)
	vertices.append(hammer_back_bot_r)

	# =========================================================================
	# EYES - At the tips of the hammer (hammerhead's 360° vision)
	# =========================================================================
	var eye_radius: float = 1.8
	hammer_left_eye = Vector3(hammer_mid_x + 1, 0, -hw + 1)
	hammer_right_eye = Vector3(hammer_mid_x + 1, 0, hw - 1)

	for eye_pos in [hammer_left_eye, hammer_right_eye]:
		var eye_points: Array[Vector3] = []
		for angle_idx in range(8):
			var angle: float = angle_idx * PI / 4.0
			var ey: float = cos(angle) * eye_radius
			var ez: float = sin(angle) * eye_radius * 0.6
			eye_points.append(eye_pos + Vector3(0, ey, ez))
		for j in range(8):
			vertices.append(eye_points[j])
			vertices.append(eye_points[(j + 1) % 8])

	# =========================================================================
	# BODY CROSS-SECTION RIBS (segments 3-10)
	# Torpedo-shaped body, more streamlined than the generic fish
	# =========================================================================
	for i in range(3, SEGMENTS.size() - 1):  # Start from head base
		var x: float = segment_positions[i].x
		var h: float = HEIGHT_PROFILE[i] * SHARK_HEIGHT * 0.5
		var w: float = WIDTH_PROFILE[i] * SHARK_WIDTH * 0.5

		if h < 1.5:
			continue

		# 8-point cross-section (octagon) for smooth body
		var rib_points: Array[Vector3] = []
		for angle_idx in range(8):
			var angle: float = angle_idx * PI / 4.0
			var y: float = cos(angle) * h
			var z: float = sin(angle) * w
			rib_points.append(Vector3(x, y, z))

		for j in range(8):
			vertices.append(rib_points[j])
			vertices.append(rib_points[(j + 1) % 8])

	# =========================================================================
	# LONGITUDINAL SPINE LINES (connect body ribs)
	# =========================================================================
	# Top spine
	for i in range(3, SEGMENTS.size() - 1):
		var x1: float = segment_positions[i].x
		var x2: float = segment_positions[i + 1].x
		var h1: float = HEIGHT_PROFILE[i] * SHARK_HEIGHT * 0.5
		var h2: float = HEIGHT_PROFILE[i + 1] * SHARK_HEIGHT * 0.5
		vertices.append(Vector3(x1, h1, 0))
		vertices.append(Vector3(x2, h2, 0))

	# Bottom spine
	for i in range(3, SEGMENTS.size() - 1):
		var x1: float = segment_positions[i].x
		var x2: float = segment_positions[i + 1].x
		var h1: float = HEIGHT_PROFILE[i] * SHARK_HEIGHT * 0.5
		var h2: float = HEIGHT_PROFILE[i + 1] * SHARK_HEIGHT * 0.5
		vertices.append(Vector3(x1, -h1, 0))
		vertices.append(Vector3(x2, -h2, 0))

	# Side spines
	for side in [-1.0, 1.0]:
		for i in range(3, SEGMENTS.size() - 1):
			var x1: float = segment_positions[i].x
			var x2: float = segment_positions[i + 1].x
			var w1: float = WIDTH_PROFILE[i] * SHARK_WIDTH * 0.5 * side
			var w2: float = WIDTH_PROFILE[i + 1] * SHARK_WIDTH * 0.5 * side
			vertices.append(Vector3(x1, 0, w1))
			vertices.append(Vector3(x2, 0, w2))

	# Connect hammer back to body start
	var body_start_h: float = HEIGHT_PROFILE[4] * SHARK_HEIGHT * 0.5
	var body_start_w: float = WIDTH_PROFILE[4] * SHARK_WIDTH * 0.5
	var body_start_x: float = segment_positions[4].x

	# Transition lines from hammer to body
	vertices.append(hammer_back_top_l)
	vertices.append(Vector3(body_start_x, body_start_h * 0.7, -body_start_w * 0.7))
	vertices.append(hammer_back_top_r)
	vertices.append(Vector3(body_start_x, body_start_h * 0.7, body_start_w * 0.7))
	vertices.append(hammer_back_bot_l)
	vertices.append(Vector3(body_start_x, -body_start_h * 0.5, -body_start_w * 0.7))
	vertices.append(hammer_back_bot_r)
	vertices.append(Vector3(body_start_x, -body_start_h * 0.5, body_start_w * 0.7))

	# =========================================================================
	# GILL SLITS - 5 per side (diagnostic feature of sharks)
	# =========================================================================
	var gill_x_start: float = segment_positions[4].x - 2
	var gill_spacing: float = 2.5
	var gill_h: float = HEIGHT_PROFILE[4] * SHARK_HEIGHT * 0.35
	var gill_w: float = WIDTH_PROFILE[4] * SHARK_WIDTH * 0.48

	for side in [-1.0, 1.0]:
		for g in range(5):
			var gx: float = gill_x_start + g * gill_spacing
			var top_pt := Vector3(gx, gill_h * 0.8, gill_w * side)
			var bot_pt := Vector3(gx + 0.8, -gill_h * 0.6, (gill_w + 0.3) * side)
			vertices.append(top_pt)
			vertices.append(bot_pt)

	# =========================================================================
	# PRIMARY DORSAL FIN - Large, iconic shark fin (segments 5-7)
	# =========================================================================
	var dorsal1_segments: Array[int] = [5, 6, 7]
	var dorsal1_base: Array[Vector3] = []

	for seg_idx in dorsal1_segments:
		var x: float = segment_positions[seg_idx].x
		var base_h: float = HEIGHT_PROFILE[seg_idx] * SHARK_HEIGHT * 0.5
		dorsal1_base.append(Vector3(x, base_h, 0))

	# Tall, swept-back dorsal fin
	var dorsal1_peak := Vector3(segment_positions[5].x + 4, dorsal1_base[0].y + 14, 0)
	dorsal_peak = dorsal1_peak  # Store for animation
	var dorsal1_back := Vector3(segment_positions[7].x, dorsal1_base[2].y + 2, 0)

	# Leading edge (front of fin)
	vertices.append(dorsal1_base[0])
	vertices.append(dorsal1_peak)

	# Trailing edge (back curve)
	vertices.append(dorsal1_peak)
	vertices.append(dorsal1_back)
	vertices.append(dorsal1_back)
	vertices.append(dorsal1_base[2])

	# Fin membrane lines
	vertices.append(dorsal1_base[1])
	vertices.append(Vector3(dorsal1_peak.x + 2, dorsal1_peak.y - 4, 0))

	# =========================================================================
	# SECONDARY DORSAL FIN - Much smaller (segments 8-9)
	# =========================================================================
	var dorsal2_x: float = segment_positions[9].x
	var dorsal2_base_h: float = HEIGHT_PROFILE[9] * SHARK_HEIGHT * 0.5
	var dorsal2_base := Vector3(dorsal2_x - 2, dorsal2_base_h, 0)
	var dorsal2_peak := Vector3(dorsal2_x, dorsal2_base_h + 3.5, 0)
	var dorsal2_back := Vector3(dorsal2_x + 2, dorsal2_base_h + 0.5, 0)

	vertices.append(dorsal2_base)
	vertices.append(dorsal2_peak)
	vertices.append(dorsal2_peak)
	vertices.append(dorsal2_back)
	vertices.append(dorsal2_back)
	vertices.append(Vector3(dorsal2_x + 2, dorsal2_base_h, 0))

	# =========================================================================
	# CAUDAL FIN - Asymmetric crescent (heterocercal-like)
	# Upper lobe larger than lower - characteristic of sharks
	# =========================================================================
	var tail_base_x: float = segment_positions[10].x
	var tail_tip_x: float = segment_positions[11].x
	var tail_h: float = HEIGHT_PROFILE[10] * SHARK_HEIGHT * 0.5

	# Upper lobe (larger, extends further back)
	tail_fork_top = Vector3(tail_tip_x + 10, 12, 0)
	# Lower lobe (smaller)
	tail_fork_bottom = Vector3(tail_tip_x + 6, -8, 0)
	# Notch point
	var tail_notch := Vector3(tail_tip_x + 4, 0, 0)

	# Main tail structure
	vertices.append(Vector3(tail_base_x, tail_h, 0))
	vertices.append(tail_fork_top)
	vertices.append(Vector3(tail_base_x, -tail_h, 0))
	vertices.append(tail_fork_bottom)
	vertices.append(Vector3(tail_base_x, 0, 0))
	vertices.append(tail_notch)

	# Crescent curves
	vertices.append(tail_fork_top)
	vertices.append(tail_notch)
	vertices.append(tail_fork_bottom)
	vertices.append(tail_notch)

	# Intermediate rays
	vertices.append(Vector3(tail_base_x, tail_h * 0.6, 0))
	vertices.append(Vector3(tail_tip_x + 7, 7, 0))
	vertices.append(Vector3(tail_base_x, -tail_h * 0.6, 0))
	vertices.append(Vector3(tail_tip_x + 5, -5, 0))

	# Upper lobe curve detail
	vertices.append(tail_fork_top)
	vertices.append(Vector3(tail_tip_x + 7, 7, 0))
	vertices.append(tail_fork_bottom)
	vertices.append(Vector3(tail_tip_x + 5, -5, 0))

	# Keels on tail peduncle (stabilizers)
	var keel_x: float = segment_positions[10].x
	for side in [-1.0, 1.0]:
		var keel_start := Vector3(keel_x - 3, 0, tail_h * 0.8 * side)
		var keel_end := Vector3(keel_x + 3, 0, tail_h * 0.6 * side)
		vertices.append(keel_start)
		vertices.append(keel_end)

	# =========================================================================
	# PECTORAL FINS - Large, swept-back (segment 4-5 area)
	# Hammerheads have notably large pectorals
	# =========================================================================
	var pec_x: float = segment_positions[5].x
	var pec_y: float = -HEIGHT_PROFILE[5] * SHARK_HEIGHT * 0.35
	var pec_w: float = WIDTH_PROFILE[5] * SHARK_WIDTH * 0.5

	for side in [-1.0, 1.0]:
		var pec_base := Vector3(pec_x, pec_y, pec_w * side)
		var pec_tip := Vector3(pec_x + 14, pec_y - 5, (pec_w + 10) * side)
		var pec_back := Vector3(pec_x + 16, pec_y - 1, (pec_w + 4) * side)
		var pec_inner := Vector3(pec_x + 8, pec_y, pec_w * 0.8 * side)

		# Fin outline
		vertices.append(pec_base)
		vertices.append(pec_tip)
		vertices.append(pec_tip)
		vertices.append(pec_back)
		vertices.append(pec_back)
		vertices.append(pec_inner)
		vertices.append(pec_inner)
		vertices.append(pec_base)

		# Fin rays
		var pec_mid := Vector3(pec_x + 7, pec_y - 2, (pec_w + 5) * side)
		vertices.append(pec_base)
		vertices.append(pec_mid)
		vertices.append(pec_mid)
		vertices.append(pec_tip)
		vertices.append(pec_mid)
		vertices.append(pec_back)

	# =========================================================================
	# PELVIC FINS - Small fins on belly (segment 7 area)
	# =========================================================================
	var pelv_x: float = segment_positions[7].x
	var pelv_y: float = -HEIGHT_PROFILE[7] * SHARK_HEIGHT * 0.48
	var pelv_w: float = WIDTH_PROFILE[7] * SHARK_WIDTH * 0.35

	for side in [-1.0, 1.0]:
		var pelv_base := Vector3(pelv_x, pelv_y, pelv_w * side)
		var pelv_tip := Vector3(pelv_x + 5, pelv_y - 2, (pelv_w + 3) * side)
		var pelv_back := Vector3(pelv_x + 6, pelv_y, (pelv_w + 1) * side)

		vertices.append(pelv_base)
		vertices.append(pelv_tip)
		vertices.append(pelv_tip)
		vertices.append(pelv_back)
		vertices.append(pelv_back)
		vertices.append(pelv_base)

	# =========================================================================
	# ANAL FIN - Small bottom fin (segment 8 area)
	# =========================================================================
	var anal_x: float = segment_positions[8].x
	var anal_y: float = -HEIGHT_PROFILE[8] * SHARK_HEIGHT * 0.5
	var anal_base := Vector3(anal_x, anal_y, 0)
	var anal_tip := Vector3(anal_x + 2, anal_y - 3, 0)
	var anal_back := Vector3(anal_x + 4, anal_y - 0.5, 0)

	vertices.append(anal_base)
	vertices.append(anal_tip)
	vertices.append(anal_tip)
	vertices.append(anal_back)
	vertices.append(anal_back)
	vertices.append(Vector3(anal_x + 4, anal_y, 0))

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
# PUBLIC API FOR ANIMATION
# ============================================================================

## Get segment world position (for rigging/animation)
func get_segment_position(segment_index: int) -> Vector3:
	if segment_index < 0 or segment_index >= segment_positions.size():
		return Vector3.ZERO
	return global_transform * segment_positions[segment_index]


## Get total number of segments
func get_segment_count() -> int:
	return segment_positions.size()


## Get shark length
func get_shark_length() -> float:
	return SHARK_LENGTH


## Get hammer width
func get_hammer_width() -> float:
	return HAMMER_WIDTH


## Get center position
func get_center() -> Vector3:
	return global_position


## Get left eye position (for hunt animation targeting)
func get_left_eye() -> Vector3:
	return global_transform * hammer_left_eye


## Get right eye position
func get_right_eye() -> Vector3:
	return global_transform * hammer_right_eye


## Get dorsal peak (for silhouette tracking)
func get_dorsal_peak() -> Vector3:
	return global_transform * dorsal_peak
