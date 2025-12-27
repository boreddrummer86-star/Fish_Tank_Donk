class_name IdleState
extends CreatureStateBase
## ============================================================================
## DONK_TANK - Shark Idle State (Forward Cruise Mode)
##
## CRITICAL: Sharks CANNOT float backwards - they must ALWAYS move forward!
## (Ram ventilation - water must pass over gills for oxygen)
##
## Realistic idle behavior:
##   - Slow forward cruise (minimum forward velocity always maintained)
##   - Gentle lazy arcs/curves (not random drift)
##   - Occasional yaw changes (looking around while moving forward)
##   - Subtle depth adjustments
##   - Swimming animation at reduced intensity
##
## Transitions to Patrol after random duration.
## ============================================================================

## Duration range for idle (seconds)
const IDLE_MIN_DURATION: float = 4.0
const IDLE_MAX_DURATION: float = 10.0

## Forward cruise parameters - ALWAYS moving forward
const IDLE_CRUISE_SPEED: float = 0.35  # Fraction of base speed (slow cruise)
const MIN_FORWARD_SPEED: float = 0.25  # Never slower than this

## Gentle turn parameters (lazy arcs)
const TURN_INTERVAL_MIN: float = 3.0
const TURN_INTERVAL_MAX: float = 7.0
const TURN_RATE_MAX: float = 0.3  # Radians per second (gentle turns)
const TURN_SMOOTHING: float = 2.0

## Depth adjustment (slow climb/dive during cruise)
const DEPTH_CHANGE_INTERVAL: float = 5.0
const PITCH_RATE_MAX: float = 0.15  # Radians per second
const PITCH_SMOOTHING: float = 1.5
const PREFERRED_DEPTH_MIN: float = -40.0
const PREFERRED_DEPTH_MAX: float = 30.0

## State
var idle_duration: float = 0.0
var elapsed_time: float = 0.0

## Turn state (lazy arcs)
var turn_timer: float = 0.0
var target_turn_rate: float = 0.0
var current_turn_rate: float = 0.0

## Pitch state (gentle depth changes)
var depth_timer: float = 0.0
var target_pitch_rate: float = 0.0
var current_pitch_rate: float = 0.0
var target_depth: float = 0.0


func enter() -> void:
	elapsed_time = 0.0

	# Random idle duration
	idle_duration = randf_range(IDLE_MIN_DURATION, IDLE_MAX_DURATION)

	# Initialize turn with random timer
	turn_timer = randf_range(1.0, TURN_INTERVAL_MIN)
	target_turn_rate = 0.0
	current_turn_rate = 0.0

	# Initialize depth
	depth_timer = randf_range(1.0, DEPTH_CHANGE_INTERVAL * 0.5)
	target_depth = creature.global_position.y
	target_pitch_rate = 0.0
	current_pitch_rate = 0.0

	# Slow cruise speed, reduced swim intensity
	creature.set_speed_multiplier(IDLE_CRUISE_SPEED)
	creature.set_swim_intensity(0.5)


func exit() -> void:
	# Restore normal speed and intensity
	creature.set_speed_multiplier(1.0)
	creature.set_swim_intensity(1.0)


func physics_update(delta: float) -> String:
	elapsed_time += delta

	# Update turn behavior (lazy arcs)
	_update_turning(delta)

	# Update depth/pitch behavior
	_update_depth(delta)

	# ALWAYS move forward - this is critical for sharks
	_move_forward(delta)

	# Transition to patrol after duration
	if elapsed_time >= idle_duration:
		return "Patrol"

	return ""


func _update_turning(delta: float) -> void:
	turn_timer -= delta

	if turn_timer <= 0:
		# Pick new turn direction (lazy arc)
		turn_timer = randf_range(TURN_INTERVAL_MIN, TURN_INTERVAL_MAX)

		# Random turn rate - sometimes straight, sometimes gentle curve
		if randf() > 0.3:
			target_turn_rate = randf_range(-TURN_RATE_MAX, TURN_RATE_MAX)
		else:
			target_turn_rate = 0.0  # Straight for a bit

		# Check if near boundary - turn away from walls
		var boundary_force: Vector3 = creature.get_boundary_avoidance(100.0)
		if boundary_force.length() > 0.1:
			# Turn away from boundary
			var forward: Vector3 = creature.get_forward()
			var cross: Vector3 = forward.cross(boundary_force)
			target_turn_rate = clampf(cross.y * 2.0, -TURN_RATE_MAX * 2, TURN_RATE_MAX * 2)

	# Smooth turn rate
	current_turn_rate = lerpf(current_turn_rate, target_turn_rate, TURN_SMOOTHING * delta)


func _update_depth(delta: float) -> void:
	depth_timer -= delta

	if depth_timer <= 0:
		depth_timer = randf_range(DEPTH_CHANGE_INTERVAL * 0.5, DEPTH_CHANGE_INTERVAL)

		# Pick a comfortable target depth
		target_depth = randf_range(PREFERRED_DEPTH_MIN, PREFERRED_DEPTH_MAX)

		# Clamp to tank bounds
		target_depth = clampf(target_depth, CreatureBase.SAND_Y + 30, CreatureBase.SURFACE_Y - 20)

	# Calculate pitch needed to reach target depth
	var depth_diff: float = target_depth - creature.global_position.y
	var desired_pitch: float = clampf(depth_diff * 0.02, -PITCH_RATE_MAX, PITCH_RATE_MAX)

	# Smooth pitch rate
	current_pitch_rate = lerpf(current_pitch_rate, desired_pitch, PITCH_SMOOTHING * delta)


func _move_forward(delta: float) -> void:
	# Get current forward direction
	var forward: Vector3 = creature.get_forward()

	# Apply yaw rotation (turning)
	creature.rotation.y += current_turn_rate * delta

	# Apply pitch rotation (climbing/diving)
	creature.rotation.x = lerpf(creature.rotation.x, -current_pitch_rate * 3.0, delta * 2.0)

	# Get new forward after rotation
	forward = creature.get_forward()

	# Calculate speed using effective speed (includes boost modifiers)
	# Always maintain minimum forward speed - sharks cannot stop!
	var effective_speed: float = creature.get_effective_speed()
	var min_speed: float = creature.base_speed * MIN_FORWARD_SPEED
	var cruise_speed: float = maxf(effective_speed, min_speed)

	# ALWAYS move forward - sharks cannot go backwards
	creature.global_position += forward * cruise_speed * delta

	# Set target position for animation system (point ahead in current direction)
	creature.target_position = creature.global_position + forward * 50.0

	# Enforce tank boundaries with soft clamping
	var pos: Vector3 = creature.global_position
	var margin: float = 40.0
	pos.x = clampf(pos.x, -CreatureBase.TANK_WIDTH / 2 + margin, CreatureBase.TANK_WIDTH / 2 - margin)
	pos.y = clampf(pos.y, CreatureBase.SAND_Y + 25, CreatureBase.SURFACE_Y - 15)
	pos.z = clampf(pos.z, -CreatureBase.TANK_DEPTH / 2 + margin, CreatureBase.TANK_DEPTH / 2 - margin)
	creature.global_position = pos
