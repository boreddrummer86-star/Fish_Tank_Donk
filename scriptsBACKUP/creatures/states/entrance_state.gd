class_name EntranceState
extends CreatureStateBase
## ============================================================================
## DONK_TANK - GRAND CINEMATIC ENTRANCE v2
##
## A spectacular 5-second showcase entrance for the hammerhead shark.
##
## ORIENTATION REFERENCE (VERIFIED BY TESTING):
##   The mesh faces +Z at rotation.y = 0 (opposite of Godot convention)
##   get_forward() = -transform.basis.z (but visual differs!)
##
##   rotation.y = 0     → VISUAL faces +Z (TOWARD camera)
##   rotation.y = PI    → VISUAL faces -Z (away from camera)
##   rotation.y = PI/2  → VISUAL faces +X (right from camera view)
##   rotation.y = -PI/2 → VISUAL faces -X (left from camera view)
##
##   To visually face direction (dx, dz): rotation.y = atan2(dx, dz)
##   (NO +PI offset needed for this mesh!)
##
## TANK LAYOUT:
##   Camera at Z=288, looking at origin
##   Tank X: -360 to +360 (width 720)
##   Tank Z: -100 to +100 (depth 200)
##   Tank Y: -78 (sand) to +90 (surface)
##
## THE GRAND ENTRANCE:
##   Phase 1 (0-1.5s): THE APPROACH
##     - Spawn at back center, tiny, head facing camera
##     - Swim TOWARD camera while veering LEFT
##     - Growing from tiny to medium
##
##   Phase 2 (1.5-3.5s): THE SHOWCASE SWEEP
##     - At LEFT side of tank, now MASSIVE (1.5x scale)
##     - Slow majestic sweep from LEFT to RIGHT
##     - Full display across the entire tank width
##
##   Phase 3 (3.5-5.0s): THE ARC & SETTLE
##     - Curve around in an elegant arc
##     - Scale down to normal (1.0x)
##     - Position for smooth transition to patrol
##
## ============================================================================

## Timing
const TOTAL_DURATION: float = 5.0
const PHASE_1_END: float = 1.5      # Approach complete
const PHASE_2_END: float = 3.5      # Showcase sweep complete
const SCALE_DOWN_START: float = 3.5 # Begin settling to normal size

## Scale - GO BIG!
const START_SCALE: float = 0.15     # Tiny distant shark
const MEDIUM_SCALE: float = 1.0     # After approach
const PEAK_SCALE: float = 1.5       # MASSIVE showcase size
const FINAL_SCALE: float = 1.0      # Normal patrol size

## Phase 1: Approach (back center → left side, toward camera)
const SPAWN_POS: Vector3 = Vector3(0, 15, -80)         # Back center of tank
const APPROACH_END: Vector3 = Vector3(-250, 25, 40)    # Left side, toward camera

## Phase 2: Showcase Sweep (left → right across tank)
const SWEEP_START: Vector3 = Vector3(-250, 25, 40)     # Left side
const SWEEP_MID: Vector3 = Vector3(0, 30, 60)          # Center, closest to camera
const SWEEP_END: Vector3 = Vector3(250, 20, 30)        # Right side

## Phase 3: Arc and Settle (curve back toward patrol area)
const ARC_START: Vector3 = Vector3(250, 20, 30)        # End of sweep (right side)
const ARC_MID: Vector3 = Vector3(180, 10, -20)         # Curving back
const ARC_END: Vector3 = Vector3(80, 0, -40)           # Final patrol position

## State
var elapsed: float = 0.0
var current_phase: int = 1
var prev_position: Vector3 = Vector3.ZERO


func enter() -> void:
	elapsed = 0.0
	current_phase = 1

	# Spawn position: back center of tank
	creature.global_position = SPAWN_POS
	prev_position = SPAWN_POS

	# Face the camera: rotation.y = 0 means visual faces +Z (toward camera)
	creature.rotation = Vector3.ZERO
	# Slight angle toward left since we'll veer that way
	creature.rotation.y = -0.3

	# Start tiny
	creature.scale = Vector3.ONE * START_SCALE

	# Calm swimming animation
	creature.set_swim_intensity(0.6)
	creature.set_speed_multiplier(0.4)

	print("[ENTRANCE] Shark summoned! Beginning grand entrance...")


func exit() -> void:
	# Ensure clean exit state
	creature.scale = Vector3.ONE * FINAL_SCALE
	creature.rotation.x = 0
	creature.rotation.z = 0
	creature.set_swim_intensity(1.0)
	creature.set_speed_multiplier(1.0)
	print("[ENTRANCE] Entrance complete. Transitioning to patrol.")


func physics_update(delta: float) -> String:
	elapsed += delta

	# Determine phase
	if elapsed < PHASE_1_END:
		current_phase = 1
		_update_phase_1_approach(delta)
	elif elapsed < PHASE_2_END:
		current_phase = 2
		_update_phase_2_sweep(delta)
	else:
		current_phase = 3
		_update_phase_3_arc(delta)

	# Update scale throughout
	_update_scale()

	# Always face movement direction (visual orientation)
	_face_movement_direction(delta)

	# Set target for spine rig animation
	creature.target_position = creature.global_position + _get_visual_forward() * 50.0

	# Complete entrance
	if elapsed >= TOTAL_DURATION:
		return "Idle"

	return ""


## ============================================================================
## PHASE 1: THE APPROACH
## Swim toward camera while veering left, growing from tiny
## ============================================================================
func _update_phase_1_approach(delta: float) -> void:
	var t: float = elapsed / PHASE_1_END

	# Ease-out for smooth acceleration feel
	var ease_t: float = 1.0 - pow(1.0 - t, 2)

	# Store previous position for direction calculation
	prev_position = creature.global_position

	# Smooth curve from spawn to left side
	# Use quadratic bezier for gentle curve
	var mid_point: Vector3 = Vector3(-120, 20, -10)  # Control point
	creature.global_position = _quadratic_bezier(SPAWN_POS, mid_point, APPROACH_END, ease_t)

	# Slight swimming motion (up/down bob)
	creature.global_position.y += sin(elapsed * 4.0) * 2.0

	# Increase swim intensity as shark gets closer
	creature.set_swim_intensity(0.6 + ease_t * 0.3)


## ============================================================================
## PHASE 2: THE SHOWCASE SWEEP
## Majestic sweep from left to right - the money shot!
## ============================================================================
func _update_phase_2_sweep(delta: float) -> void:
	var phase_time: float = elapsed - PHASE_1_END
	var phase_duration: float = PHASE_2_END - PHASE_1_END
	var t: float = phase_time / phase_duration

	# Very smooth easing for majestic feel
	var ease_t: float = t * t * (3.0 - 2.0 * t)  # Smoothstep

	# Store previous for direction calculation
	prev_position = creature.global_position

	# Quadratic bezier through the sweep points
	creature.global_position = _quadratic_bezier(SWEEP_START, SWEEP_MID, SWEEP_END, ease_t)

	# Gentle wave motion
	creature.global_position.y += sin(elapsed * 3.0) * 3.0

	# Elegant banking during the sweep (leaning into the turn)
	var bank_amount: float = sin(ease_t * PI) * -0.12  # Bank right as we move right
	creature.rotation.z = lerpf(creature.rotation.z, bank_amount, 4.0 * delta)

	# Full swim intensity during showcase
	creature.set_swim_intensity(1.0)
	creature.set_speed_multiplier(0.6)  # Slow majestic pace


## ============================================================================
## PHASE 3: THE ARC & SETTLE
## Curve back around, scale down, prepare for patrol
## ============================================================================
func _update_phase_3_arc(delta: float) -> void:
	var phase_time: float = elapsed - PHASE_2_END
	var phase_duration: float = TOTAL_DURATION - PHASE_2_END
	var t: float = clampf(phase_time / phase_duration, 0.0, 1.0)

	# Ease-out for gentle settling
	var ease_t: float = 1.0 - pow(1.0 - t, 2.5)

	# Store previous for direction
	prev_position = creature.global_position

	# Arc curve back toward center
	creature.global_position = _quadratic_bezier(ARC_START, ARC_MID, ARC_END, ease_t)

	# Reduce banking smoothly
	creature.rotation.z = lerpf(creature.rotation.z, 0.0, 3.0 * delta)
	creature.rotation.x = lerpf(creature.rotation.x, 0.0, 3.0 * delta)

	# Return to normal swim parameters
	creature.set_swim_intensity(lerpf(1.0, 1.0, ease_t))
	creature.set_speed_multiplier(lerpf(0.6, 1.0, ease_t))


## ============================================================================
## ORIENTATION: Face movement direction (VISUAL facing)
## VERIFIED: rotation.y = atan2(dx, dz) for this mesh (NO +PI offset!)
## ============================================================================
func _face_movement_direction(delta: float) -> void:
	var move_dir: Vector3 = creature.global_position - prev_position

	# Only rotate if we're actually moving
	if move_dir.length_squared() < 0.0001:
		return

	move_dir = move_dir.normalized()

	# CORRECT FORMULA FOR THIS MESH: atan2(x, z) - NO PI OFFSET
	# The mesh visual faces +Z at rotation.y = 0
	var target_yaw: float = atan2(move_dir.x, move_dir.z)

	# Smooth rotation toward movement direction
	var current_yaw: float = creature.rotation.y
	var yaw_diff: float = _angle_difference(current_yaw, target_yaw)

	# Faster rotation during phase 1, slower during showcase
	var rot_speed: float = 6.0 if current_phase == 1 else 4.0
	creature.rotation.y += yaw_diff * rot_speed * delta


## Get visual forward direction (what the mesh appears to face)
## This differs from get_forward() because mesh orientation differs from Godot convention
func _get_visual_forward() -> Vector3:
	# The mesh faces +Z at rotation.y = 0, so visual forward is +basis.z
	return creature.transform.basis.z


## ============================================================================
## SCALE ANIMATION - GO BIG!
## ============================================================================
func _update_scale() -> void:
	var target_scale: float

	if elapsed < PHASE_1_END:
		# Phase 1: Grow from tiny to medium
		var t: float = elapsed / PHASE_1_END
		var ease_t: float = 1.0 - pow(1.0 - t, 2)
		target_scale = lerpf(START_SCALE, MEDIUM_SCALE, ease_t)

	elif elapsed < PHASE_2_END:
		# Phase 2: MASSIVE showcase size
		var phase_t: float = (elapsed - PHASE_1_END) / (PHASE_2_END - PHASE_1_END)
		# Quick scale up at start, hold peak
		if phase_t < 0.2:
			target_scale = lerpf(MEDIUM_SCALE, PEAK_SCALE, phase_t / 0.2)
		else:
			target_scale = PEAK_SCALE

	else:
		# Phase 3: Settle to normal
		var t: float = (elapsed - PHASE_2_END) / (TOTAL_DURATION - PHASE_2_END)
		var ease_t: float = 1.0 - pow(1.0 - t, 2)
		target_scale = lerpf(PEAK_SCALE, FINAL_SCALE, ease_t)

	creature.scale = Vector3.ONE * target_scale


## ============================================================================
## MATH HELPERS
## ============================================================================

## Quadratic Bezier interpolation (3 control points)
func _quadratic_bezier(p0: Vector3, p1: Vector3, p2: Vector3, t: float) -> Vector3:
	var u: float = 1.0 - t
	return u * u * p0 + 2.0 * u * t * p1 + t * t * p2


## Get shortest angle difference (handles wrapping)
func _angle_difference(from_angle: float, to_angle: float) -> float:
	var diff: float = fmod(to_angle - from_angle + PI, TAU) - PI
	if diff < -PI:
		diff += TAU
	return diff
