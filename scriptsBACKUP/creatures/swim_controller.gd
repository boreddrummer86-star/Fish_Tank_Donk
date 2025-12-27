class_name SwimController
extends Node
## ============================================================================
## DONK_TANK - Modular Swimming Animation Controller
##
## Handles realistic fish/shark swimming through segment-based animation.
## Based on biomechanical research:
##   - Carangiform locomotion: wave propagates head→tail with increasing amplitude
##   - Phase offset between segments creates traveling wave illusion
##   - Speed affects frequency and amplitude
##   - Hammerhead-specific: head oscillates independently (electroreception)
##
## PERFORMANCE: Pure math operations, no mesh rebuilding = guaranteed 60fps
## ============================================================================

## The creature this controller animates
var creature: Node3D = null

## Segments to animate (populated by setup)
## Each segment: { node: Node3D, body_position: float, base_rotation: Vector3 }
var segments: Array[Dictionary] = []

## ============================================================================
## BODY WAVE PARAMETERS (Carangiform Swimming)
## ============================================================================

## Base frequency (waves per second) - affected by speed
@export var base_frequency: float = 1.8

## Maximum lateral amplitude (radians) at tail
@export var max_amplitude: float = 0.35

## How many wave cycles fit along body (wavelength)
@export var wave_cycles: float = 1.2

## Power curve for amplitude falloff (higher = more tail-focused)
@export var amplitude_power: float = 2.0

## ============================================================================
## HEAD OSCILLATION (Hammerhead-specific)
## ============================================================================

## Enable independent head movement
@export var head_oscillation_enabled: bool = true

## Head oscillation frequency multiplier (faster than body)
@export var head_frequency_mult: float = 2.2

## Head oscillation amplitude (radians)
@export var head_amplitude: float = 0.08

## Where head ends (0-1 along body)
@export var head_boundary: float = 0.15

## ============================================================================
## TAIL THRUST ENHANCEMENT
## ============================================================================

## Extra amplitude boost for tail
@export var tail_thrust_mult: float = 1.4

## Where tail begins (0-1 along body)
@export var tail_boundary: float = 0.75

## ============================================================================
## SPEED MODULATION
## ============================================================================

## Current speed multiplier (0-2, affects animation intensity)
var speed_factor: float = 1.0

## Minimum animation when nearly stopped
@export var min_intensity: float = 0.3

## How much speed affects frequency
@export var speed_freq_influence: float = 0.4

## How much speed affects amplitude
@export var speed_amp_influence: float = 0.6

## ============================================================================
## SECONDARY MOTION (Realism)
## ============================================================================

## Subtle vertical undulation
@export var dorsal_undulation: float = 0.08

## Roll during turns
@export var turn_roll_amount: float = 0.12

## Current turn intensity (-1 to 1)
var turn_factor: float = 0.0

## ============================================================================
## IDLE MICRO-MOVEMENTS
## ============================================================================

## Enable idle-specific behaviors
var idle_mode: bool = false

## Idle breathing simulation (subtle body pulse)
@export var idle_breath_frequency: float = 0.4
@export var idle_breath_amplitude: float = 0.02

## Idle drift sway
@export var idle_sway_frequency: float = 0.15
@export var idle_sway_amplitude: float = 0.04

## Random head scanning in idle
var _idle_scan_timer: float = 0.0
var _idle_scan_target: float = 0.0
var _idle_scan_current: float = 0.0

## ============================================================================
## INTERNAL STATE
## ============================================================================

var _swim_time: float = 0.0
var _initialized: bool = false


func _ready() -> void:
	# Find creature (parent or grandparent)
	creature = get_parent()
	if creature == null:
		push_error("[SwimController] No parent creature found!")


## Setup segments for animation
## Call this after creating the creature's mesh/structure
## segments_data: Array of { node: Node3D, body_position: float (0=head, 1=tail) }
func setup_segments(segments_data: Array) -> void:
	segments.clear()
	for data in segments_data:
		if data.has("node") and data.has("body_position"):
			var seg: Dictionary = {
				"node": data.node,
				"body_position": clamp(data.body_position, 0.0, 1.0),
				"base_rotation": data.node.rotation if data.node else Vector3.ZERO
			}
			segments.append(seg)

	_initialized = segments.size() > 0
	if not _initialized:
		push_warning("[SwimController] No segments configured!")


## Main update - call from _physics_process for consistent timing
func update_swim(delta: float) -> void:
	if not _initialized:
		return

	_swim_time += delta

	# Calculate current animation parameters based on speed
	var intensity: float = lerp(min_intensity, 1.0, speed_factor)
	var current_freq: float = base_frequency * (1.0 + (speed_factor - 1.0) * speed_freq_influence)
	var current_amp: float = max_amplitude * intensity * (1.0 + (speed_factor - 1.0) * speed_amp_influence)

	# Update each segment
	for seg in segments:
		_update_segment(seg, current_freq, current_amp, delta)

	# Update idle behaviors if active
	if idle_mode:
		_update_idle_behaviors(delta)


## Update a single segment's rotation
func _update_segment(seg: Dictionary, freq: float, amp: float, delta: float) -> void:
	var node: Node3D = seg.node
	if node == null:
		return

	var body_pos: float = seg.body_position
	var base_rot: Vector3 = seg.base_rotation

	# === MAIN BODY WAVE ===
	# Amplitude increases from head to tail (power curve)
	var amp_mask: float = pow(body_pos, amplitude_power)

	# Tail gets extra thrust
	if body_pos > tail_boundary:
		var tail_factor: float = (body_pos - tail_boundary) / (1.0 - tail_boundary)
		amp_mask *= lerp(1.0, tail_thrust_mult, tail_factor)

	# Phase offset creates traveling wave (head leads)
	var phase: float = body_pos * wave_cycles * TAU

	# Calculate lateral (yaw) rotation
	var wave: float = sin(_swim_time * freq * TAU + phase)
	var yaw_offset: float = wave * amp * amp_mask

	# === HEAD OSCILLATION (Hammerhead electroreception scanning) ===
	var head_offset: float = 0.0
	if head_oscillation_enabled and body_pos < head_boundary:
		# Inverse mask: strongest at tip
		var head_mask: float = 1.0 - (body_pos / head_boundary)
		head_mask = pow(head_mask, 0.7)

		# Head oscillates at different frequency
		var head_wave: float = sin(_swim_time * freq * head_frequency_mult * TAU)
		head_offset = head_wave * head_amplitude * head_mask

		# Add idle scanning if active
		if idle_mode:
			head_offset += _idle_scan_current * head_mask

	# === DORSAL UNDULATION (Vertical wave, phase-shifted) ===
	var pitch_wave: float = sin(_swim_time * freq * TAU + phase + PI * 0.5)
	var pitch_offset: float = pitch_wave * dorsal_undulation * amp_mask * 0.5

	# === TURN ROLL ===
	var roll_offset: float = turn_factor * turn_roll_amount * (1.0 - body_pos * 0.5)

	# === IDLE BREATHING (subtle body pulse via pitch) ===
	var breath_offset: float = 0.0
	if idle_mode:
		var breath_wave: float = sin(_swim_time * idle_breath_frequency * TAU)
		breath_offset = breath_wave * idle_breath_amplitude * (1.0 - abs(body_pos - 0.5) * 2.0)

	# === APPLY COMBINED ROTATION ===
	node.rotation = Vector3(
		base_rot.x + pitch_offset + breath_offset,
		base_rot.y + yaw_offset + head_offset,
		base_rot.z + roll_offset
	)


## Update idle-specific behaviors
func _update_idle_behaviors(delta: float) -> void:
	# Random head scanning (look around periodically)
	_idle_scan_timer -= delta
	if _idle_scan_timer <= 0:
		# Pick new scan target
		_idle_scan_target = randf_range(-0.15, 0.15)
		_idle_scan_timer = randf_range(2.0, 5.0)

	# Smooth interpolation to scan target
	_idle_scan_current = lerp(_idle_scan_current, _idle_scan_target, delta * 0.8)


## Set speed factor (affects animation intensity)
func set_speed(factor: float) -> void:
	speed_factor = clamp(factor, 0.0, 2.0)


## Set turn factor for roll (-1 = left, 1 = right)
func set_turn(factor: float) -> void:
	turn_factor = clamp(factor, -1.0, 1.0)


## Enable/disable idle mode
func set_idle_mode(enabled: bool) -> void:
	idle_mode = enabled
	if enabled:
		_idle_scan_timer = randf_range(0.5, 2.0)
		_idle_scan_current = 0.0


## Get current swim time (for external sync)
func get_swim_time() -> float:
	return _swim_time
