class_name PatrolState
extends CreatureStateBase
## ============================================================================
## DONK_TANK - Patrol State
## AI-like waypoint navigation with natural movement variations.
## Occasionally transitions to Idle for rest periods.
## ============================================================================

## How many waypoints to visit before potentially resting
const MIN_WAYPOINTS: int = 2
const MAX_WAYPOINTS: int = 5

## Speed variation parameters
const SPEED_VAR_MIN: float = 0.75
const SPEED_VAR_MAX: float = 1.25
const SPEED_CHANGE_INTERVAL: float = 3.0

## State tracking
var waypoints_visited: int = 0
var total_waypoints: int = 0
var patrol_timer: float = 0.0

## Speed variation
var speed_var_timer: float = 0.0
var current_speed_target: float = 1.0
var current_speed_value: float = 1.0

## Slight roll during turns (organic feel)
var target_roll: float = 0.0
const ROLL_AMOUNT: float = 0.08
const ROLL_SPEED: float = 3.0


func enter() -> void:
	waypoints_visited = 0
	total_waypoints = randi_range(MIN_WAYPOINTS, MAX_WAYPOINTS)
	patrol_timer = 0.0
	speed_var_timer = 0.0
	current_speed_target = randf_range(SPEED_VAR_MIN, SPEED_VAR_MAX)
	current_speed_value = current_speed_target

	# Pick first waypoint
	_pick_new_waypoint()

	creature.set_swim_intensity(1.0)


func exit() -> void:
	# Reset roll
	creature.rotation.z = 0.0


func physics_update(delta: float) -> String:
	patrol_timer += delta
	speed_var_timer += delta

	# Update speed variation
	_update_speed_variation(delta)

	# Calculate turn amount for roll
	var turn_strength := _get_turn_strength()
	target_roll = turn_strength * ROLL_AMOUNT

	# Smoothly apply roll
	creature.rotation.z = lerp(creature.rotation.z, target_roll, ROLL_SPEED * delta)

	# Move toward waypoint
	creature.move_toward_target(delta)

	# Check if reached waypoint
	if creature.at_target(35.0):
		waypoints_visited += 1

		# Check if should rest
		if waypoints_visited >= total_waypoints:
			# Random chance to rest
			if randf() > 0.4:
				return "Idle"
			else:
				# Keep patrolling with new waypoint count
				waypoints_visited = 0
				total_waypoints = randi_range(MIN_WAYPOINTS, MAX_WAYPOINTS)

		_pick_new_waypoint()

	return ""


func _pick_new_waypoint() -> void:
	creature.target_position = creature.get_random_waypoint()


func _update_speed_variation(delta: float) -> void:
	if speed_var_timer >= SPEED_CHANGE_INTERVAL:
		speed_var_timer = 0.0
		current_speed_target = randf_range(SPEED_VAR_MIN, SPEED_VAR_MAX)

	# Smooth interpolation to target speed
	current_speed_value = lerp(current_speed_value, current_speed_target, delta * 0.5)
	creature.set_speed_multiplier(current_speed_value)


func _get_turn_strength() -> float:
	## Calculate how sharply we're turning (for roll animation)
	var to_target: Vector3 = (creature.target_position - creature.global_position).normalized()
	var forward: Vector3 = creature.get_forward()

	# Cross product Y gives turn direction (-1 to 1)
	var cross: Vector3 = forward.cross(to_target)
	return clamp(cross.y * 2.0, -1.0, 1.0)
