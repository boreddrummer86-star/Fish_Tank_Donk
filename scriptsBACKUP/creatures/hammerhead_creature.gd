class_name HammerheadCreature
extends CreatureBase
## ============================================================================
## DONK_TANK - Hammerhead Shark Creature
##
## Complete creature with:
##   - Segmented wireframe mesh for proper articulation
##   - Spine-based rigging for realistic swimming animation
##   - State machine for AI behavior (Entrance → Idle ↔ Patrol)
##   - Natural speed variation (like real animal)
##   - Boost system (speed bursts every minute)
##
## SWIMMING SYSTEM:
##   Uses SharkSpineRig for biomechanically accurate animation:
##   - Traveling wave from head to tail
##   - Tangent-following segments (smooth S-curve)
##   - Head stabilization for stable sensing
##   - Hammerhead scanning behavior
##   - Natural turn response with banking
##
## PERFORMANCE: Pure math operations = guaranteed 60fps
## ============================================================================

## Hammerhead-specific parameters
const SHARK_LENGTH: float = 70.0
const SHARK_SPEED: float = 35.0

## Segmented mesh instance
var hammerhead: SegmentedHammerhead = null

## Spine-based rig for swimming animation
var spine_rig: SharkSpineRig = null

## Smoothed turn value for animation
var _anim_turn: float = 0.0
const TURN_SMOOTH_SPEED: float = 4.0

## ============================================================================
## SPEED VARIATION SYSTEM - Natural stroke variation like real animals
## ============================================================================

## Speed variation range (multiplier applied to base speed)
const SPEED_VAR_MIN: float = 0.85
const SPEED_VAR_MAX: float = 1.20
const SPEED_VAR_INTERVAL: float = 1.5  # Seconds between speed changes
const SPEED_VAR_SMOOTHING: float = 2.5  # How fast to transition

var _speed_var_timer: float = 0.0
var _speed_var_target: float = 1.0
var _speed_var_current: float = 1.0

## ============================================================================
## BOOST SYSTEM - Speed burst every 60 seconds for 5 seconds
## ============================================================================

const BOOST_COOLDOWN: float = 60.0  # Seconds between boosts
const BOOST_DURATION: float = 5.0   # How long boost lasts
const BOOST_MULTIPLIER: float = 2.0 # Speed multiplier during boost

var _boost_timer: float = 0.0       # Counts up to BOOST_COOLDOWN
var _boost_active: bool = false
var _boost_remaining: float = 0.0   # Countdown during boost
var _is_boosting: bool = false


func _ready() -> void:
	# Set hammerhead-specific parameters
	base_speed = SHARK_SPEED
	turn_speed = 2.2

	# Create segmented hammerhead mesh
	hammerhead = SegmentedHammerhead.new()
	hammerhead.name = "Mesh"
	add_child(hammerhead)

	# Create and configure spine rig
	_setup_spine_rig()

	# Create state machine with states
	_setup_state_machine()

	# Call parent ready (sets up tank bounds)
	super._ready()


## Handle input for color cycling (Key 2)
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_2:
			# Cycle to next neon color
			if hammerhead:
				hammerhead.cycle_color_random()
				get_viewport().set_input_as_handled()


func _setup_spine_rig() -> void:
	# Create the spine rig
	spine_rig = SharkSpineRig.new()

	# Configure for hammerhead
	spine_rig.configure_hammerhead()

	# Wait for mesh to be ready, then setup rig with segment positions
	await get_tree().process_frame

	if hammerhead:
		spine_rig.setup(hammerhead.get_segment_body_positions())


func _setup_state_machine() -> void:
	# Create state machine
	var fsm := CreatureStateMachine.new()
	fsm.name = "StateMachine"
	fsm.creature = self
	fsm.initial_state = "Entrance"

	# Create states
	var entrance := EntranceState.new()
	entrance.name = "Entrance"

	var idle := IdleState.new()
	idle.name = "Idle"

	var patrol := PatrolState.new()
	patrol.name = "Patrol"

	# Add states to state machine
	fsm.add_child(entrance)
	fsm.add_child(idle)
	fsm.add_child(patrol)

	# Add state machine to creature
	add_child(fsm)
	state_machine = fsm


func _physics_process(delta: float) -> void:
	super._physics_process(delta)

	# Update speed variation (natural rhythm)
	_update_speed_variation(delta)

	# Update boost system
	_update_boost_system(delta)

	# Update spine rig animation
	if spine_rig and hammerhead:
		# Calculate turn factor for animation (yaw)
		var turn_factor: float = _calculate_turn_factor()

		# Calculate pitch factor for animation (climb/dive)
		var pitch_factor: float = _calculate_pitch_factor()

		# Smooth the turn for animation
		_anim_turn = lerp(_anim_turn, turn_factor, TURN_SMOOTH_SPEED * delta)

		# Calculate final speed with variation and boost
		var final_speed: float = _get_effective_speed()

		# Update rig parameters
		spine_rig.set_speed(final_speed)
		spine_rig.set_turn(_anim_turn)
		spine_rig.set_pitch(pitch_factor)

		# Run rig update
		spine_rig.update(delta)

		# Apply computed rotations to mesh segments
		hammerhead.apply_rig_rotations(spine_rig)


## ============================================================================
## SPEED VARIATION - Natural variation like real animals
## ============================================================================

func _update_speed_variation(delta: float) -> void:
	_speed_var_timer += delta

	if _speed_var_timer >= SPEED_VAR_INTERVAL:
		_speed_var_timer = 0.0

		# Pick new target speed variation
		# Sometimes faster strokes, sometimes slower (like real swimming)
		_speed_var_target = randf_range(SPEED_VAR_MIN, SPEED_VAR_MAX)

		# Occasionally do a quick burst stroke
		if randf() > 0.85:
			_speed_var_target = SPEED_VAR_MAX * 1.1  # Extra fast stroke

	# Smooth transition to target
	_speed_var_current = lerpf(_speed_var_current, _speed_var_target, SPEED_VAR_SMOOTHING * delta)


## ============================================================================
## BOOST SYSTEM - Every 60 seconds, 5 second burst at 2x speed
## ============================================================================

func _update_boost_system(delta: float) -> void:
	if _is_boosting:
		# Currently in boost mode
		_boost_remaining -= delta

		if _boost_remaining <= 0:
			# Boost finished
			_is_boosting = false
			_boost_timer = 0.0

			# Return to normal swim mode
			if spine_rig:
				spine_rig.configure_hammerhead()
	else:
		# Counting up to next boost
		_boost_timer += delta

		if _boost_timer >= BOOST_COOLDOWN:
			# TRIGGER BOOST!
			_is_boosting = true
			_boost_remaining = BOOST_DURATION

			# Switch to aggressive swim mode during boost
			if spine_rig:
				spine_rig.configure_aggressive()


## Get effective speed multiplier (combines base, variation, and boost)
func _get_effective_speed() -> float:
	var effective: float = speed_multiplier * _speed_var_current

	if _is_boosting:
		effective *= BOOST_MULTIPLIER

	return effective


## Check if currently boosting
func is_boosting() -> bool:
	return _is_boosting


## Get time until next boost
func get_boost_countdown() -> float:
	if _is_boosting:
		return 0.0
	return BOOST_COOLDOWN - _boost_timer


## Get remaining boost time
func get_boost_remaining() -> float:
	return _boost_remaining if _is_boosting else 0.0


## Override base class speed modifier to include variation and boost
func get_speed_modifier() -> float:
	var modifier: float = _speed_var_current
	if _is_boosting:
		modifier *= BOOST_MULTIPLIER
	return modifier


## Calculate turn factor based on movement direction (yaw)
func _calculate_turn_factor() -> float:
	if target_position == Vector3.ZERO:
		return 0.0

	var to_target: Vector3 = (target_position - global_position).normalized()
	var forward: Vector3 = get_forward()

	# Cross product Y gives turn direction
	var cross: Vector3 = forward.cross(to_target)
	return clampf(cross.y * 3.0, -1.0, 1.0)


## Calculate pitch factor based on vertical movement (climb/dive)
func _calculate_pitch_factor() -> float:
	if target_position == Vector3.ZERO:
		return 0.0

	var to_target: Vector3 = target_position - global_position
	var horizontal_dist: float = Vector2(to_target.x, to_target.z).length()

	# Avoid division by zero
	if horizontal_dist < 1.0:
		return 0.0

	# Calculate vertical angle to target
	var vertical_angle: float = atan2(to_target.y, horizontal_dist)

	# Scale to -1 to 1 range (±45 degrees = full pitch)
	return clampf(vertical_angle / (PI * 0.25), -1.0, 1.0)


## Override to control rig idle mode
func set_swim_intensity(intensity: float) -> void:
	super.set_swim_intensity(intensity)

	if spine_rig:
		# Reduce animation when idle
		spine_rig.swim_speed = intensity


## Set swimming to aggressive mode
func set_aggressive_swim() -> void:
	if spine_rig:
		spine_rig.configure_aggressive()


## Set swimming to cruise mode
func set_cruise_swim() -> void:
	if spine_rig:
		spine_rig.configure_cruise()


## Set swimming to normal hammerhead mode
func set_normal_swim() -> void:
	if spine_rig:
		spine_rig.configure_hammerhead()


## Get shark length
func get_shark_length() -> float:
	return SHARK_LENGTH


## Get hammerhead mesh reference
func get_mesh() -> SegmentedHammerhead:
	return hammerhead


## Get spine rig reference (for advanced control)
func get_spine_rig() -> SharkSpineRig:
	return spine_rig


## ============================================================================
## COLOR CONTROL API
## ============================================================================

## Cycle to next random neon color
func cycle_color() -> void:
	if hammerhead:
		hammerhead.cycle_color_random()


## Set color by palette index (0-11)
func set_color_index(index: int) -> void:
	if hammerhead:
		hammerhead.set_color_by_index(index)


## Set a custom color directly
func set_color(color: Color) -> void:
	if hammerhead:
		hammerhead.set_color(color)


## Get current color
func get_color() -> Color:
	if hammerhead:
		return hammerhead.get_color()
	return Color.WHITE


## Get current color name
func get_color_name() -> String:
	if hammerhead:
		return hammerhead.get_color_name()
	return "Unknown"
