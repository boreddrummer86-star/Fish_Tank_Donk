class_name CreatureStateMachine
extends Node
## ============================================================================
## DONK_TANK - Creature State Machine
## Manages state transitions and updates for creatures.
## States are child nodes implementing CreatureStateBase.
## ============================================================================

## The creature this state machine controls
var creature: CreatureBase = null

## Initial state to start in (node name)
@export var initial_state: String = "Entrance"

## Current active state
var current_state: CreatureStateBase = null

## Dictionary of all available states (name -> state node)
var states: Dictionary = {}

## Signal emitted when state changes
signal state_changed(old_state: String, new_state: String)


func _ready() -> void:
	# Wait one frame for creature to be set up
	await get_tree().process_frame

	# Find creature if not set (parent should be CreatureBase)
	if creature == null:
		var parent := get_parent()
		if parent is CreatureBase:
			creature = parent as CreatureBase
		else:
			push_error("[StateMachine] Parent is not a CreatureBase!")
			return

	# Collect all state children
	for child in get_children():
		if child is CreatureStateBase:
			states[child.name] = child
			child.setup(creature, self)

	# Enter initial state
	if states.has(initial_state):
		_transition_to(initial_state)
	elif states.size() > 0:
		_transition_to(states.keys()[0])
	else:
		push_warning("[StateMachine] No states found for creature: ", creature.name)


func _physics_process(delta: float) -> void:
	if current_state == null:
		return

	# Update current state and check for transition
	var next_state: String = current_state.physics_update(delta)
	if next_state != "":
		_transition_to(next_state)


func _process(delta: float) -> void:
	if current_state == null:
		return

	# Frame update for visual effects
	var next_state: String = current_state.frame_update(delta)
	if next_state != "":
		_transition_to(next_state)


## Force transition to a specific state
func transition_to(state_name: String) -> void:
	_transition_to(state_name)


## Internal transition handler
func _transition_to(state_name: String) -> void:
	if not states.has(state_name):
		push_warning("[StateMachine] State not found: ", state_name)
		return

	var old_state_name: String = current_state.name if current_state else ""

	# Exit current state
	if current_state != null:
		current_state.exit()

	# Enter new state
	current_state = states[state_name]
	current_state.enter()

	state_changed.emit(old_state_name, state_name)


## Get current state name
func get_current_state_name() -> String:
	return current_state.name if current_state else ""
