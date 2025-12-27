class_name CreatureBase
extends Node3D
## ============================================================================
## DONK_TANK - Creature Base Class
## Manages state machine, swimming animation, and movement for all creatures.
## Extend this class for specific creature types (shark, fish, etc.)
## ============================================================================

## Tank boundaries (for patrol and avoidance)
const TANK_WIDTH: float = 720.0
const TANK_HEIGHT: float = 288.0
const TANK_DEPTH: float = 200.0
const SAND_Y: float = -78.0
const SURFACE_Y: float = 90.0

## Movement parameters
@export var base_speed: float = 35.0
@export var turn_speed: float = 2.0
@export var boundary_margin: float = 80.0

## Swimming animation parameters
@export var swim_frequency: float = 2.0      # Body waves per second
@export var swim_amplitude: float = 0.15     # Max lateral displacement
@export var swim_wavelength: float = 1.5     # Waves along body
@export var swim_intensity: float = 1.0      # Overall animation strength

## State machine reference
var state_machine: CreatureStateMachine = null

## Current movement
var velocity: Vector3 = Vector3.ZERO
var target_position: Vector3 = Vector3.ZERO
var current_speed: float = 0.0
var speed_multiplier: float = 1.0

## Swimming animation
var swim_time: float = 0.0

## Boundary avoidance
var tank_bounds: AABB


func _ready() -> void:
	# Calculate tank bounds
	tank_bounds = AABB(
		Vector3(-TANK_WIDTH / 2, SAND_Y, -TANK_DEPTH / 2),
		Vector3(TANK_WIDTH, TANK_HEIGHT + SAND_Y, TANK_DEPTH)
	)

	# Find or create state machine
	for child in get_children():
		if child is CreatureStateMachine:
			state_machine = child
			break

	current_speed = base_speed


func _physics_process(delta: float) -> void:
	# Update swimming animation time
	swim_time += delta * swim_frequency * current_speed / base_speed

	# Apply swimming animation if overridden in child class
	_update_swim_animation(delta)


## Override in child classes to apply swimming animation
func _update_swim_animation(_delta: float) -> void:
	pass


## Calculate boundary avoidance force
func get_boundary_avoidance(softness: float = 60.0) -> Vector3:
	var force := Vector3.ZERO
	var pos := global_position

	# Distance to each boundary
	var to_min := pos - tank_bounds.position
	var to_max := tank_bounds.end - pos

	# X boundaries (left/right walls)
	if to_min.x < softness:
		force.x += (softness - to_min.x) / softness
	if to_max.x < softness:
		force.x -= (softness - to_max.x) / softness

	# Y boundaries (floor/surface)
	if to_min.y < softness:
		force.y += (softness - to_min.y) / softness
	if to_max.y < softness:
		force.y -= (softness - to_max.y) / softness

	# Z boundaries (front/back glass)
	if to_min.z < softness:
		force.z += (softness - to_min.z) / softness
	if to_max.z < softness:
		force.z -= (softness - to_max.z) / softness

	return force


## Get a random waypoint within tank (biased toward center)
func get_random_waypoint() -> Vector3:
	var center := tank_bounds.get_center()
	var size := tank_bounds.size * 0.6  # Stay away from edges

	return Vector3(
		center.x + randf_range(-size.x / 2, size.x / 2),
		center.y + randf_range(-size.y / 2, size.y / 2),
		center.z + randf_range(-size.z / 2, size.z / 2)
	)


## Move toward target with smooth turning
func move_toward_target(delta: float) -> void:
	var direction := (target_position - global_position).normalized()

	# Add boundary avoidance
	var avoidance := get_boundary_avoidance()
	var final_direction := (direction + avoidance * 1.5).normalized()

	# Get current forward direction
	var current_forward := -transform.basis.z

	# Smooth turn toward target
	var new_forward := current_forward.slerp(final_direction, turn_speed * delta)

	# Apply rotation (look at target direction)
	if new_forward.length_squared() > 0.001:
		look_at(global_position + new_forward, Vector3.UP)

	# Move forward using effective speed (includes boost modifiers)
	global_position += new_forward * get_effective_speed() * delta


## Calculate distance to target
func distance_to_target() -> float:
	return global_position.distance_to(target_position)


## Check if at target (within threshold)
func at_target(threshold: float = 25.0) -> bool:
	return distance_to_target() < threshold


## Set swimming intensity (0-1, affects animation strength)
func set_swim_intensity(intensity: float) -> void:
	swim_intensity = clamp(intensity, 0.0, 2.0)


## Set speed multiplier (for state-based speed changes)
func set_speed_multiplier(mult: float) -> void:
	speed_multiplier = clamp(mult, 0.1, 3.0)


## Get additional speed modifier (override in child classes for boost effects)
## Returns 1.0 by default, child classes can return higher values during boost
func get_speed_modifier() -> float:
	return 1.0


## Get final effective speed (base * multiplier * modifier)
func get_effective_speed() -> float:
	return current_speed * speed_multiplier * get_speed_modifier()


## Get current facing direction
func get_forward() -> Vector3:
	return -transform.basis.z


## Get current velocity (direction * speed)
func get_velocity() -> Vector3:
	return get_forward() * get_effective_speed()
