class_name JellyfishCreature
extends CreatureBase
## ============================================================================
## DONK_TANK - Jellyfish Creature
##
## Complete creature with:
##   - Segmented wireframe mesh for bloop animation
##   - State machine for behavior (Entrance → Idle ↔ Bloop)
##   - Pulsing propulsion animation (like Mario Blooper)
##   - Bloop triggers every 30 seconds (3x bloops)
##
## MOVEMENT STYLE:
##   Jellyfish don't swim like fish - they pulse/bloop:
##   - Contract bell to push water down
##   - Drift upward from thrust
##   - Relax and slowly sink
##   - Tentacles trail behind motion
##
## PERFORMANCE: Pure math operations = guaranteed 60fps
## ============================================================================

## Jellyfish-specific parameters
const JELLY_SIZE: float = 18.0
const JELLY_SPEED: float = 15.0  # Slower than shark

## Bloop animation timing
const BLOOP_COOLDOWN: float = 30.0  # Bloop every 30 seconds
const BLOOP_COUNT: int = 3          # "bloop bloop bloop"

## Segmented mesh instance
var jellyfish: SegmentedJellyfish = null

## Bloop timer
var _bloop_timer: float = 0.0
var _is_blooping: bool = false

## Drift physics
var _drift_velocity: Vector3 = Vector3.ZERO
const DRIFT_GRAVITY: float = 8.0    # Slow sink
const DRIFT_DAMPING: float = 0.98   # Water resistance
const BLOOP_THRUST: float = 25.0    # Upward push per bloop


func _ready() -> void:
	# Set jellyfish-specific parameters
	base_speed = JELLY_SPEED
	turn_speed = 1.0  # Slow, floaty turning

	# Create segmented jellyfish mesh
	jellyfish = SegmentedJellyfish.new()
	jellyfish.name = "Mesh"
	add_child(jellyfish)

	# Create state machine with states
	_setup_state_machine()

	# Call parent ready (sets up tank bounds)
	super._ready()


## Handle input for color cycling (Key 2 also cycles jellyfish if pressed)
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_2:
			# Cycle to next neon color
			if jellyfish:
				jellyfish.cycle_color_random()
				get_viewport().set_input_as_handled()


func _setup_state_machine() -> void:
	# Create state machine
	var fsm := CreatureStateMachine.new()
	fsm.name = "StateMachine"
	fsm.creature = self
	fsm.initial_state = "Entrance"

	# Create states
	var entrance := JellyfishEntranceState.new()
	entrance.name = "Entrance"

	var idle := JellyfishIdleState.new()
	idle.name = "Idle"

	var bloop := JellyfishBloopState.new()
	bloop.name = "Bloop"

	# Add states to state machine
	fsm.add_child(entrance)
	fsm.add_child(idle)
	fsm.add_child(bloop)

	# Add state machine to creature
	add_child(fsm)
	state_machine = fsm


func _physics_process(delta: float) -> void:
	super._physics_process(delta)

	# Update bloop timer
	_update_bloop_timer(delta)

	# Update bloop animation if active
	if jellyfish and jellyfish.is_currently_blooping():
		jellyfish.update_bloop(delta)

	# Apply drift physics
	_update_drift_physics(delta)


## ============================================================================
## BLOOP TIMER - Triggers every 30 seconds
## ============================================================================

func _update_bloop_timer(delta: float) -> void:
	if _is_blooping:
		return  # Don't count during bloop

	_bloop_timer += delta

	if _bloop_timer >= BLOOP_COOLDOWN:
		trigger_bloop()


## Trigger the bloop animation
func trigger_bloop() -> void:
	if _is_blooping:
		return

	_is_blooping = true
	_bloop_timer = 0.0

	# Tell state machine to switch to bloop state
	if state_machine:
		state_machine.transition_to("Bloop")


## Called when bloop animation completes
func on_bloop_complete() -> void:
	_is_blooping = false


## Check if currently blooping
func is_blooping() -> bool:
	return _is_blooping


## Get time until next bloop
func get_bloop_countdown() -> float:
	return BLOOP_COOLDOWN - _bloop_timer


## ============================================================================
## DRIFT PHYSICS - Jellyfish float and sink
## ============================================================================

func _update_drift_physics(delta: float) -> void:
	# Apply gravity (slow sink)
	_drift_velocity.y -= DRIFT_GRAVITY * delta

	# Apply damping (water resistance)
	_drift_velocity *= DRIFT_DAMPING

	# Apply velocity to position
	global_position += _drift_velocity * delta

	# Clamp to tank bounds
	var margin: float = 30.0
	global_position.x = clampf(global_position.x, -TANK_WIDTH / 2 + margin, TANK_WIDTH / 2 - margin)
	global_position.y = clampf(global_position.y, SAND_Y + 40, SURFACE_Y - 20)
	global_position.z = clampf(global_position.z, -TANK_DEPTH / 2 + margin, TANK_DEPTH / 2 - margin)


## Apply upward thrust from bloop
func apply_bloop_thrust() -> void:
	_drift_velocity.y += BLOOP_THRUST

	# Small random horizontal drift
	_drift_velocity.x += randf_range(-3.0, 3.0)
	_drift_velocity.z += randf_range(-3.0, 3.0)


## Apply gentle drift force
func apply_drift(force: Vector3) -> void:
	_drift_velocity += force


## Get drift velocity
func get_drift_velocity() -> Vector3:
	return _drift_velocity


## ============================================================================
## PUBLIC API
## ============================================================================

## Get jellyfish size
func get_jelly_size() -> float:
	return JELLY_SIZE


## Get jellyfish mesh reference
func get_mesh() -> SegmentedJellyfish:
	return jellyfish


## Start bloop animation on mesh
func start_bloop_animation(count: int = 3) -> void:
	if jellyfish:
		jellyfish.start_bloop(count)


## Check if mesh is currently animating bloop
func is_bloop_animating() -> bool:
	if jellyfish:
		return jellyfish.is_currently_blooping()
	return false


## ============================================================================
## COLOR CONTROL API
## ============================================================================

## Cycle to next random neon color
func cycle_color() -> void:
	if jellyfish:
		jellyfish.cycle_color_random()


## Set color by palette index
func set_color_index(index: int) -> void:
	if jellyfish:
		jellyfish.set_color_by_index(index)


## Set a custom color directly
func set_color(color: Color) -> void:
	if jellyfish:
		jellyfish.set_color(color)


## Get current color
func get_color() -> Color:
	if jellyfish:
		return jellyfish.get_color()
	return Color.WHITE


## Get current color name
func get_color_name() -> String:
	if jellyfish:
		return jellyfish.get_color_name()
	return "Unknown"
