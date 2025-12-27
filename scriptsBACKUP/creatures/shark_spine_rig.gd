class_name SharkSpineRig
extends RefCounted
## ============================================================================
## DONK_TANK - Biomechanically Accurate Shark Spine Rigging System
##
## Based on peer-reviewed research on shark locomotion:
##   - Webb & Keyes (1982) - Swimming Kinematics of Sharks
##   - Wilga & Lauder (2012) - Biomechanics of Locomotion in Sharks
##   - Hoffmann et al. (2017) - Double Oscillation in Hammerheads
##   - Maia et al. (2012) - Pectoral Fin Kinematics During Turning
##
## KEY SCIENTIFIC PARAMETERS (from research):
##   - Tail beat frequency: 0.8-2.0 Hz (species dependent)
##   - Tail amplitude: 20-24% body length (peak-to-peak)
##   - Wavelength: 1.0-1.2 body lengths
##   - Strouhal number: 0.2-0.4 (optimal efficiency)
##   - Hammerhead head: oscillates at HIGHER frequency than body
##
## ANIMATION LAYERS:
##   1. Primary propulsive wave (carangiform undulation)
##   2. Double oscillation system (hammerhead head scanning)
##   3. Head counter-rotation (stabilization for sensing)
##   4. Turn response (C-curve body shape + banking)
##   5. Pitch response (climbing/diving via pectoral angle)
##   6. Breathing rhythm (subtle body pulse)
##
## PERFORMANCE: Pure math, PackedArrays, zero allocations in update
## ============================================================================


## ============================================================================
## SEGMENT DATA
## ============================================================================

## Number of segments this rig controls
var segment_count: int = 0

## Body positions for each segment (0 = nose, 1 = tail tip)
var segment_positions: PackedFloat32Array

## Computed rotations per segment (updated each frame)
var segment_yaw: PackedFloat32Array      # Y-axis rotation (lateral undulation)
var segment_pitch: PackedFloat32Array    # X-axis rotation (vertical undulation)
var segment_roll: PackedFloat32Array     # Z-axis rotation (banking)


## ============================================================================
## PRIMARY PROPULSIVE WAVE - Carangiform Locomotion
## Scientific basis: Webb & Keyes 1982, Nature Communications 2023
## ============================================================================

## Tail beat frequency in Hz (oscillations per second)
## Research: Blacktip 0.82 Hz, Bamboo 1.57-1.95 Hz, typical range 0.8-2.0 Hz
var tail_beat_frequency: float = 1.6

## Tail amplitude as fraction of body length (peak-to-peak / 2)
## Research: 20-24% peak-to-peak, so 10-12% single-side amplitude
var tail_amplitude: float = 0.11

## Wavelength as fraction of body length
## Research: 1.0-1.2 body lengths typical
var wavelength: float = 1.1

## Amplitude distribution power curve
## Higher = more tail-focused (research suggests 2.0-2.5 for sharks)
var amplitude_power: float = 2.3

## Minimum amplitude at head region (near zero for stability)
var head_min_amplitude: float = 0.008


## ============================================================================
## DOUBLE OSCILLATION SYSTEM - Hammerhead Specific
## Scientific basis: Hoffmann et al. 2017, Journal of Experimental Biology
## "The head is moving back and forth a lot faster than the rest of the body"
## ============================================================================

## Enable double oscillation (hammerhead feature)
var double_oscillation_enabled: bool = true

## Head oscillation frequency MULTIPLIER relative to body
## Research: "moving at a different rate" - typically 1.5-2.5x faster
var head_frequency_multiplier: float = 2.2

## Head oscillation amplitude (radians)
## Research: Subtle but detectable - "almost impossible to see with naked eye"
var head_scan_amplitude: float = 0.08

## Where head region ends (fraction of body)
## Hammerhead cephalofoil is roughly 14% of body length
var head_region_boundary: float = 0.15

## Head scan phase offset (creates sweeping motion)
var _head_scan_phase: float = 0.0


## ============================================================================
## HEAD STABILIZATION - Counter-Rotation
## Scientific basis: Fish maintain stable head for sensory organs
## ============================================================================

## How much to counter-rotate head against body wave (0-1)
## 1.0 = perfect stabilization, 0.0 = head follows body wave
var head_stabilization_strength: float = 0.85


## ============================================================================
## TURNING MECHANICS - Yaw Maneuvers
## Scientific basis: Maia et al. 2012, PMC7671128
## "Body bends into C-shape, inside pectoral fin protracted/depressed"
## ============================================================================

## Current turn input (-1 = hard left, +1 = hard right)
var turn_input: float = 0.0

## Smoothed turn value (for animation)
var _turn_smoothed: float = 0.0

## Turn smoothing speed
var turn_smooth_rate: float = 3.5

## Body C-curve amount during turns (radians at peak)
## Research: Significant body curvature observed during routine turns
var turn_body_curve_amount: float = 0.20

## Banking (roll) amount during turns (radians)
## Research: "banking (rolling of the body)" during maneuvers
var turn_bank_amount: float = 0.12

## Where body curves most during turn (0-1 along body)
## Research: Curvature peaks in mid-body region
var turn_curve_peak_position: float = 0.4


## ============================================================================
## PITCH MECHANICS - Climbing/Diving
## Scientific basis: Wilga & Lauder 2001, Journal of Experimental Biology
## "Pectoral fins rotated upward/downward to initiate rising/sinking"
## ============================================================================

## Current pitch input (-1 = dive, +1 = climb)
var pitch_input: float = 0.0

## Smoothed pitch value
var _pitch_smoothed: float = 0.0

## Pitch smoothing speed
var pitch_smooth_rate: float = 2.5

## Body pitch angle during climb/dive (radians)
## Research: "Body surface angle altered significantly during vertical maneuvering"
var pitch_body_angle: float = 0.15

## How pitch affects different body regions
## Front pitches more, tail follows
var pitch_front_multiplier: float = 1.5
var pitch_tail_multiplier: float = 0.4


## ============================================================================
## VERTICAL UNDULATION - Pitch Wave
## Subtle dorsoventral wave, phase-shifted from lateral
## ============================================================================

## Vertical wave amplitude (much smaller than lateral)
var vertical_wave_amplitude: float = 0.025

## Phase offset from lateral wave (typically ~90 degrees)
var vertical_phase_offset: float = PI * 0.5


## ============================================================================
## BREATHING / IDLE RHYTHM
## Subtle body pulse simulating gill pumping
## ============================================================================

## Breathing frequency (Hz)
var breath_frequency: float = 0.4

## Breathing amplitude (radians)
var breath_amplitude: float = 0.012


## ============================================================================
## SPEED MODULATION
## Research: "Tailbeat frequency and amplitude increase with speed"
## ============================================================================

## Current swim speed (0 = stopped, 1 = cruising, 2 = fast)
var swim_speed: float = 1.0

## How much speed affects frequency
## Research: Frequency increases linearly with speed above threshold
var speed_frequency_scale: float = 0.35

## How much speed affects amplitude
## Research: Amplitude also increases with speed
var speed_amplitude_scale: float = 0.30

## Minimum animation intensity when nearly stopped
var min_intensity: float = 0.35


## ============================================================================
## INTERNAL TIMING STATE
## ============================================================================

var _swim_time: float = 0.0
var _breath_time: float = 0.0
var _initialized: bool = false


## ============================================================================
## INITIALIZATION
## ============================================================================

## Setup the rig with segment body positions
## body_positions: Array of floats (0-1) for each segment along body
func setup(body_positions: Array) -> void:
	segment_count = body_positions.size()

	segment_positions.resize(segment_count)
	segment_yaw.resize(segment_count)
	segment_pitch.resize(segment_count)
	segment_roll.resize(segment_count)

	for i in range(segment_count):
		segment_positions[i] = float(body_positions[i])
		segment_yaw[i] = 0.0
		segment_pitch[i] = 0.0
		segment_roll[i] = 0.0

	_initialized = true


## ============================================================================
## MAIN UPDATE - Call every physics frame
## ============================================================================

func update(delta: float) -> void:
	if not _initialized or segment_count == 0:
		return

	# Advance timers
	_swim_time += delta
	_breath_time += delta

	# Smooth inputs
	_turn_smoothed = lerp(_turn_smoothed, turn_input, turn_smooth_rate * delta)
	_pitch_smoothed = lerp(_pitch_smoothed, pitch_input, pitch_smooth_rate * delta)

	# Calculate speed-modulated parameters
	var intensity: float = lerpf(min_intensity, 1.0, swim_speed)
	var current_frequency: float = tail_beat_frequency * (1.0 + (swim_speed - 1.0) * speed_frequency_scale)
	var current_amplitude: float = tail_amplitude * intensity * (1.0 + (swim_speed - 1.0) * speed_amplitude_scale)

	# Update head scan phase (independent timing for double oscillation)
	if double_oscillation_enabled:
		_head_scan_phase += delta * current_frequency * head_frequency_multiplier * TAU

	# Compute all segment rotations
	for i in range(segment_count):
		_compute_segment_rotation(i, current_frequency, current_amplitude, delta)


## ============================================================================
## SEGMENT ROTATION COMPUTATION
## ============================================================================

func _compute_segment_rotation(seg_index: int, frequency: float, amplitude: float, _delta: float) -> void:
	var t: float = segment_positions[seg_index]  # Body position 0-1

	# ==========================================================================
	# LAYER 1: PRIMARY PROPULSIVE WAVE (Carangiform undulation)
	# ==========================================================================

	# Amplitude envelope - exponential increase from head to tail
	# a(t) = a_min + (a_max - a_min) * t^power
	var amp_envelope: float = head_min_amplitude + (amplitude - head_min_amplitude) * pow(t, amplitude_power)

	# Phase at this body position (traveling wave head -> tail)
	# φ(t) = ωt - kt where k = 2π/λ (wave number)
	var wave_phase: float = _swim_time * frequency * TAU - t * (TAU / wavelength)

	# Lateral displacement at this point
	var lateral_displacement: float = sin(wave_phase) * amp_envelope

	# TANGENT-FOLLOWING: The key to realistic swimming
	# Each segment rotates to follow the LOCAL TANGENT of the spine curve
	# Tangent angle = atan(d(displacement)/d(position))
	# d/dt[A*sin(ωt - kt)] = -k*A*cos(ωt - kt)
	var wave_number: float = TAU / wavelength
	var tangent_slope: float = -wave_number * amp_envelope * cos(wave_phase)
	var tangent_yaw: float = atan(tangent_slope)

	# ==========================================================================
	# LAYER 2: DOUBLE OSCILLATION (Hammerhead head scanning)
	# ==========================================================================

	var head_scan_yaw: float = 0.0
	if double_oscillation_enabled and t < head_region_boundary:
		# Head scans at higher frequency than body wave
		# Amplitude strongest at tip, fades toward body
		var head_factor: float = 1.0 - (t / head_region_boundary)
		head_factor = pow(head_factor, 0.6)  # Smooth falloff
		head_scan_yaw = sin(_head_scan_phase) * head_scan_amplitude * head_factor

	# ==========================================================================
	# LAYER 3: HEAD STABILIZATION (Counter-rotation)
	# ==========================================================================

	var stabilization_yaw: float = 0.0
	if t < head_region_boundary:
		# Counter-rotate to stabilize head against body wave
		var stab_factor: float = 1.0 - (t / head_region_boundary)
		stab_factor = pow(stab_factor, 0.5)
		stabilization_yaw = -tangent_yaw * head_stabilization_strength * stab_factor

	# ==========================================================================
	# LAYER 4: TURN RESPONSE (C-curve body shape)
	# ==========================================================================

	# Body curves into turns with peak curvature at mid-body
	var turn_curve_factor: float = sin(t * PI)  # Peak at t=0.5
	# Shift peak toward front during aggressive turns
	var adjusted_t: float = t * (1.0 - abs(_turn_smoothed) * 0.3)
	turn_curve_factor = sin(adjusted_t * PI)
	# Front body initiates turn more
	turn_curve_factor *= 1.0 - t * 0.4

	var turn_yaw: float = _turn_smoothed * turn_body_curve_amount * turn_curve_factor

	# Banking: roll into the turn
	# More banking at front, less at tail
	var bank_factor: float = 1.0 - t * 0.7
	var turn_roll: float = _turn_smoothed * turn_bank_amount * bank_factor

	# ==========================================================================
	# LAYER 5: PITCH RESPONSE (Climbing/Diving)
	# ==========================================================================

	# Front body pitches more during climb/dive
	var pitch_factor: float = lerpf(pitch_front_multiplier, pitch_tail_multiplier, t)
	var pitch_rotation: float = _pitch_smoothed * pitch_body_angle * pitch_factor

	# ==========================================================================
	# LAYER 6: VERTICAL UNDULATION (Dorsoventral wave)
	# ==========================================================================

	# Smaller amplitude vertical wave, phase-shifted from lateral
	var vertical_phase: float = wave_phase + vertical_phase_offset
	var vertical_displacement: float = sin(vertical_phase) * amp_envelope * (vertical_wave_amplitude / tail_amplitude)
	var vertical_tangent: float = -wave_number * amp_envelope * cos(vertical_phase) * (vertical_wave_amplitude / tail_amplitude)
	var pitch_wave: float = atan(vertical_tangent) * 0.5

	# ==========================================================================
	# LAYER 7: BREATHING RHYTHM
	# ==========================================================================

	# Subtle body pulse, strongest at mid-body
	var breath_factor: float = 1.0 - abs(t - 0.5) * 2.0
	breath_factor = maxf(breath_factor, 0.0)
	var breath_pitch: float = sin(_breath_time * breath_frequency * TAU) * breath_amplitude * breath_factor

	# ==========================================================================
	# COMBINE ALL LAYERS
	# ==========================================================================

	segment_yaw[seg_index] = tangent_yaw + head_scan_yaw + stabilization_yaw + turn_yaw
	segment_pitch[seg_index] = pitch_rotation + pitch_wave + breath_pitch
	segment_roll[seg_index] = turn_roll


## ============================================================================
## PUBLIC GETTERS
## ============================================================================

func get_segment_yaw(index: int) -> float:
	if index < 0 or index >= segment_count:
		return 0.0
	return segment_yaw[index]


func get_segment_pitch(index: int) -> float:
	if index < 0 or index >= segment_count:
		return 0.0
	return segment_pitch[index]


func get_segment_roll(index: int) -> float:
	if index < 0 or index >= segment_count:
		return 0.0
	return segment_roll[index]


func get_segment_rotation(index: int) -> Vector3:
	if index < 0 or index >= segment_count:
		return Vector3.ZERO
	return Vector3(segment_pitch[index], segment_yaw[index], segment_roll[index])


func get_segment_count() -> int:
	return segment_count


## ============================================================================
## PUBLIC SETTERS
## ============================================================================

func set_speed(speed: float) -> void:
	swim_speed = clampf(speed, 0.0, 2.0)


func set_turn(turn: float) -> void:
	turn_input = clampf(turn, -1.0, 1.0)


func set_pitch(pitch: float) -> void:
	pitch_input = clampf(pitch, -1.0, 1.0)


## ============================================================================
## CONFIGURATION PRESETS
## ============================================================================

## Configure for Great Hammerhead (Sphyrna mokarran)
func configure_hammerhead() -> void:
	# Primary wave - based on hammerhead research
	tail_beat_frequency = 1.5
	tail_amplitude = 0.10
	wavelength = 1.15
	amplitude_power = 2.3
	head_min_amplitude = 0.006

	# Double oscillation - key hammerhead feature
	double_oscillation_enabled = true
	head_frequency_multiplier = 2.2
	head_scan_amplitude = 0.09
	head_region_boundary = 0.15

	# Strong head stabilization
	head_stabilization_strength = 0.88

	# Turn mechanics
	turn_body_curve_amount = 0.18
	turn_bank_amount = 0.10
	turn_curve_peak_position = 0.4

	# Pitch mechanics
	pitch_body_angle = 0.12

	# Vertical wave
	vertical_wave_amplitude = 0.02

	# Breathing
	breath_frequency = 0.35
	breath_amplitude = 0.010


## Configure for fast/aggressive swimming
func configure_aggressive() -> void:
	tail_beat_frequency = 2.2
	tail_amplitude = 0.14
	amplitude_power = 2.0
	turn_body_curve_amount = 0.28
	turn_bank_amount = 0.18
	head_scan_amplitude = 0.05  # Less scanning when focused


## Configure for slow cruising
func configure_cruise() -> void:
	tail_beat_frequency = 1.0
	tail_amplitude = 0.08
	amplitude_power = 2.5
	turn_body_curve_amount = 0.12
	turn_bank_amount = 0.06
	head_scan_amplitude = 0.12  # More scanning when relaxed


## Configure for idle/hovering
func configure_idle() -> void:
	tail_beat_frequency = 0.6
	tail_amplitude = 0.05
	amplitude_power = 2.8
	head_scan_amplitude = 0.15
	breath_amplitude = 0.018
