class_name CreatureStateBase
extends Node
## ============================================================================
## DONK_TANK - Abstract Creature State Base Class
## All creature states inherit from this class.
## Provides standard callbacks for state lifecycle and updates.
## ============================================================================

## Reference to the creature this state belongs to
var creature: CreatureBase = null

## Reference to the state machine
var state_machine: CreatureStateMachine = null


## Called when entering this state
func enter() -> void:
	pass


## Called when exiting this state
func exit() -> void:
	pass


## Called every physics frame while this state is active
## Returns the next state name if transitioning, empty string otherwise
func physics_update(delta: float) -> String:
	return ""


## Called every frame while this state is active
## Returns the next state name if transitioning, empty string otherwise
func frame_update(delta: float) -> String:
	return ""


## Setup references - called by state machine on initialization
func setup(p_creature: CreatureBase, p_state_machine: CreatureStateMachine) -> void:
	creature = p_creature
	state_machine = p_state_machine
