class_name BubbleSystem
extends Node3D
## ============================================================================
## DONK_TANK - AAA MultiMesh Bubble System
##
## Production-quality underwater bubbles using MultiMeshInstance3D for
## GPU-efficient batched rendering. Features:
##
##   - 3 depth layers (far, mid, near) with parallax
##   - Natural motion: rise, drift, wobble, scale pulsing
##   - Spawn vents along sand floor + random scattered
##   - Object pooling with free-list (zero per-frame allocations)
##   - Custom fresnel/rim shader for glass-like appearance
##   - 300-800 bubbles at stable 60 FPS
##
## ============================================================================

## Total bubble count (distributed across layers)
@export var bubble_count: int = 400

## Per-layer distribution (must sum to 1.0)
@export var layer_distribution: Vector3 = Vector3(0.4, 0.35, 0.25)  # far, mid, near

## Tank boundaries
const TANK_X_MIN: float = -340.0
const TANK_X_MAX: float = 340.0
const TANK_Z_FAR: float = -90.0   # Far layer Z
const TANK_Z_MID: float = -20.0   # Mid layer Z
const TANK_Z_NEAR: float = 50.0   # Near layer Z
const SAND_Y: float = -78.0
const SURFACE_Y: float = 100.0

## Layer configuration
const LAYERS: Array[Dictionary] = [
	{  # Far layer (index 0) - small, slow, faded
		"z_range": Vector2(-90.0, -50.0),
		"size_range": Vector2(1.5, 3.0),
		"speed_range": Vector2(18.0, 30.0),
		"alpha": 0.25,
		"drift_mult": 0.6
	},
	{  # Mid layer (index 1) - medium, normal
		"z_range": Vector2(-50.0, 10.0),
		"size_range": Vector2(2.5, 5.0),
		"speed_range": Vector2(25.0, 45.0),
		"alpha": 0.45,
		"drift_mult": 1.0
	},
	{  # Near layer (index 2) - large, fast, vivid
		"z_range": Vector2(10.0, 60.0),
		"size_range": Vector2(4.0, 8.0),
		"speed_range": Vector2(35.0, 60.0),
		"alpha": 0.65,
		"drift_mult": 1.3
	}
]

## Motion parameters
@export var rise_speed_base: float = 35.0
@export var drift_amplitude: float = 12.0
@export var drift_frequency: float = 0.8
@export var wobble_amplitude: float = 0.15
@export var wobble_frequency: float = 2.5
@export var pulse_amplitude: float = 0.08
@export var pulse_frequency: float = 1.8

## Spawn vent positions (X coordinates along sand)
var spawn_vents: Array[float] = []
@export var vent_count: int = 6
@export var vent_spawn_rate: float = 0.3  # Bubbles per second per vent
@export var random_spawn_rate: float = 0.5  # Random bubbles per second

## Debug options
@export var debug_logging: bool = false
@export var show_vent_positions: bool = false

## Internal state
var multimesh_instance: MultiMeshInstance3D
var multimesh: MultiMesh
var bubble_mesh: SphereMesh
var bubble_material: ShaderMaterial

## Bubble data arrays (pooled, no per-frame allocations)
var bubble_positions: PackedVector3Array
var bubble_velocities: PackedVector3Array
var bubble_phases: PackedFloat32Array
var bubble_sizes: PackedFloat32Array
var bubble_alphas: PackedFloat32Array
var bubble_layers: PackedInt32Array
var bubble_active: PackedInt32Array  # 1 = active, 0 = pooled

## Free list for pooling
var free_indices: Array[int] = []
var active_count: int = 0

## Timing
var _spawn_timer: float = 0.0
var _perf_timer: float = 0.0
var _frame_count: int = 0


func _ready() -> void:
	_setup_spawn_vents()
	_create_multimesh()
	_initialize_bubble_pool()
	_spawn_initial_bubbles()

	if debug_logging:
		print("[BUBBLES] System initialized with ", bubble_count, " bubble capacity")
		print("[BUBBLES] Layers: Far=", int(bubble_count * layer_distribution.x),
			  " Mid=", int(bubble_count * layer_distribution.y),
			  " Near=", int(bubble_count * layer_distribution.z))


func _setup_spawn_vents() -> void:
	spawn_vents.clear()
	var spacing: float = (TANK_X_MAX - TANK_X_MIN) / float(vent_count + 1)
	for i in range(vent_count):
		var x: float = TANK_X_MIN + spacing * (i + 1)
		# Add slight randomness to vent positions
		x += randf_range(-spacing * 0.2, spacing * 0.2)
		spawn_vents.append(x)

	if debug_logging:
		print("[BUBBLES] Spawn vents at X: ", spawn_vents)


func _create_multimesh() -> void:
	# Create low-poly sphere mesh for bubbles
	bubble_mesh = SphereMesh.new()
	bubble_mesh.radius = 1.0
	bubble_mesh.height = 2.0
	bubble_mesh.radial_segments = 8  # Low poly but smooth enough
	bubble_mesh.rings = 4

	# Load custom shader
	var shader: Shader = load("res://shaders/bubble_multimesh.gdshader")
	if shader == null:
		push_error("[BUBBLES] Failed to load bubble_multimesh.gdshader!")
		return

	bubble_material = ShaderMaterial.new()
	bubble_material.shader = shader

	# Create MultiMesh
	multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_custom_data = true  # For per-instance phase, size, alpha, layer
	multimesh.mesh = bubble_mesh
	multimesh.instance_count = bubble_count

	# Create MultiMeshInstance3D
	multimesh_instance = MultiMeshInstance3D.new()
	multimesh_instance.name = "BubbleMultiMesh"
	multimesh_instance.multimesh = multimesh
	multimesh_instance.material_override = bubble_material
	multimesh_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	add_child(multimesh_instance)


func _initialize_bubble_pool() -> void:
	# Pre-allocate all arrays
	bubble_positions.resize(bubble_count)
	bubble_velocities.resize(bubble_count)
	bubble_phases.resize(bubble_count)
	bubble_sizes.resize(bubble_count)
	bubble_alphas.resize(bubble_count)
	bubble_layers.resize(bubble_count)
	bubble_active.resize(bubble_count)

	# Initialize all as inactive (pooled)
	for i in range(bubble_count):
		bubble_active[i] = 0
		free_indices.append(i)

		# Hide inactive bubbles below the scene
		var hidden_transform := Transform3D.IDENTITY
		hidden_transform.origin = Vector3(0, -1000, 0)
		hidden_transform = hidden_transform.scaled(Vector3(0.01, 0.01, 0.01))
		multimesh.set_instance_transform(i, hidden_transform)

	active_count = 0


func _spawn_initial_bubbles() -> void:
	# Spawn bubbles distributed across the water column
	var target_count: int = int(bubble_count * 0.7)  # Start with 70% capacity

	for i in range(target_count):
		var layer: int = _pick_random_layer()
		var layer_config: Dictionary = LAYERS[layer]

		# Random position throughout water column
		var pos := Vector3(
			randf_range(TANK_X_MIN, TANK_X_MAX),
			randf_range(SAND_Y + 10, SURFACE_Y - 10),  # Distributed vertically
			randf_range(layer_config["z_range"].x, layer_config["z_range"].y)
		)

		_spawn_bubble_at(pos, layer)


func _pick_random_layer() -> int:
	var roll: float = randf()
	if roll < layer_distribution.x:
		return 0  # Far
	elif roll < layer_distribution.x + layer_distribution.y:
		return 1  # Mid
	else:
		return 2  # Near


func _spawn_bubble_at(pos: Vector3, layer: int) -> int:
	if free_indices.is_empty():
		return -1  # Pool exhausted

	var idx: int = free_indices.pop_back()
	var layer_config: Dictionary = LAYERS[layer]

	# Initialize bubble data
	bubble_positions[idx] = pos
	bubble_phases[idx] = randf() * TAU * 10.0  # Random phase offset
	bubble_sizes[idx] = randf_range(layer_config["size_range"].x, layer_config["size_range"].y)
	bubble_alphas[idx] = layer_config["alpha"] * randf_range(0.8, 1.2)
	bubble_layers[idx] = layer

	# Calculate rise velocity
	var rise_speed: float = randf_range(
		layer_config["speed_range"].x,
		layer_config["speed_range"].y
	)
	bubble_velocities[idx] = Vector3(0, rise_speed, 0)

	bubble_active[idx] = 1
	active_count += 1

	# Update MultiMesh instance
	_update_bubble_transform(idx)

	return idx


func _recycle_bubble(idx: int) -> void:
	if bubble_active[idx] == 0:
		return

	bubble_active[idx] = 0
	active_count -= 1
	free_indices.append(idx)

	# Hide the instance
	var hidden_transform := Transform3D.IDENTITY
	hidden_transform.origin = Vector3(0, -1000, 0)
	hidden_transform = hidden_transform.scaled(Vector3(0.01, 0.01, 0.01))
	multimesh.set_instance_transform(idx, hidden_transform)


func _update_bubble_transform(idx: int) -> void:
	var pos: Vector3 = bubble_positions[idx]
	var size: float = bubble_sizes[idx]
	var phase: float = bubble_phases[idx]
	var alpha: float = bubble_alphas[idx]
	var layer: int = bubble_layers[idx]

	# Build transform with scale
	var t := Transform3D.IDENTITY
	t.origin = pos
	t = t.scaled(Vector3(size, size, size))

	multimesh.set_instance_transform(idx, t)

	# Set custom data: phase, size, alpha, layer
	var custom := Color(phase, size, alpha, float(layer))
	multimesh.set_instance_custom_data(idx, custom)


func _physics_process(delta: float) -> void:
	_update_bubbles(delta)
	_spawn_new_bubbles(delta)

	if debug_logging:
		_update_perf_stats(delta)


func _update_bubbles(delta: float) -> void:
	var time: float = Time.get_ticks_msec() * 0.001

	for idx in range(bubble_count):
		if bubble_active[idx] == 0:
			continue

		var pos: Vector3 = bubble_positions[idx]
		var vel: Vector3 = bubble_velocities[idx]
		var phase: float = bubble_phases[idx]
		var layer: int = bubble_layers[idx]
		var layer_config: Dictionary = LAYERS[layer]

		# Buoyancy rise
		pos.y += vel.y * delta

		# Horizontal drift (sine wave)
		var drift_mult: float = layer_config["drift_mult"]
		var drift: float = sin(time * drift_frequency + phase) * drift_amplitude * drift_mult * delta
		pos.x += drift

		# Slight Z wobble for depth variation
		var z_wobble: float = sin(time * wobble_frequency * 0.5 + phase * 2.0) * 2.0 * delta
		pos.z += z_wobble

		# Keep Z within layer bounds
		pos.z = clamp(pos.z, layer_config["z_range"].x, layer_config["z_range"].y)

		# Wrap X position
		if pos.x < TANK_X_MIN:
			pos.x = TANK_X_MAX
		elif pos.x > TANK_X_MAX:
			pos.x = TANK_X_MIN

		# Check if bubble reached surface
		if pos.y > SURFACE_Y:
			_recycle_bubble(idx)
			continue

		# Update position
		bubble_positions[idx] = pos

		# Apply wobble to size (pulsing)
		var base_size: float = bubble_sizes[idx]
		var pulse: float = 1.0 + sin(time * pulse_frequency + phase) * pulse_amplitude
		var wobble_scale: float = 1.0 + sin(time * wobble_frequency + phase * 1.5) * wobble_amplitude

		# Build transform
		var size: float = base_size * pulse * wobble_scale
		var t := Transform3D.IDENTITY
		t.origin = pos
		t = t.scaled(Vector3(size, size * 1.1, size))  # Slightly taller than wide

		multimesh.set_instance_transform(idx, t)


func _spawn_new_bubbles(delta: float) -> void:
	_spawn_timer += delta

	# Spawn from vents
	var vent_interval: float = 1.0 / (vent_spawn_rate * vent_count)
	while _spawn_timer > vent_interval and active_count < bubble_count:
		_spawn_timer -= vent_interval

		# Pick random vent
		var vent_x: float = spawn_vents[randi() % spawn_vents.size()]
		var layer: int = _pick_random_layer()
		var layer_config: Dictionary = LAYERS[layer]

		var pos := Vector3(
			vent_x + randf_range(-15, 15),
			SAND_Y + randf_range(5, 15),
			randf_range(layer_config["z_range"].x, layer_config["z_range"].y)
		)

		_spawn_bubble_at(pos, layer)

	# Spawn random scattered bubbles
	if randf() < random_spawn_rate * delta and active_count < bubble_count:
		var layer: int = _pick_random_layer()
		var layer_config: Dictionary = LAYERS[layer]

		var pos := Vector3(
			randf_range(TANK_X_MIN, TANK_X_MAX),
			SAND_Y + randf_range(5, 20),
			randf_range(layer_config["z_range"].x, layer_config["z_range"].y)
		)

		_spawn_bubble_at(pos, layer)


func _update_perf_stats(delta: float) -> void:
	_frame_count += 1
	_perf_timer += delta

	if _perf_timer >= 5.0:
		var avg_fps: float = _frame_count / _perf_timer
		print("[BUBBLES] Active: ", active_count, "/", bubble_count,
			  " | Pooled: ", free_indices.size(),
			  " | Avg FPS: %.1f" % avg_fps)
		_frame_count = 0
		_perf_timer = 0.0


## ============================================================================
## PUBLIC API
## ============================================================================

## Get current active bubble count
func get_active_count() -> int:
	return active_count


## Set bubble density (0.0 to 1.0)
func set_density(density: float) -> void:
	density = clamp(density, 0.0, 1.0)
	var target: int = int(bubble_count * density)

	# Add or remove bubbles to reach target
	while active_count < target:
		var layer: int = _pick_random_layer()
		var layer_config: Dictionary = LAYERS[layer]
		var pos := Vector3(
			randf_range(TANK_X_MIN, TANK_X_MAX),
			randf_range(SAND_Y + 10, SURFACE_Y - 10),
			randf_range(layer_config["z_range"].x, layer_config["z_range"].y)
		)
		if _spawn_bubble_at(pos, layer) == -1:
			break

	while active_count > target:
		# Find an active bubble to recycle
		for idx in range(bubble_count):
			if bubble_active[idx] == 1:
				_recycle_bubble(idx)
				break


## Burst of bubbles at position (for effects)
func spawn_burst(pos: Vector3, count: int = 10) -> void:
	for i in range(count):
		if active_count >= bubble_count:
			break

		var layer: int = 1  # Mid layer for bursts
		var offset := Vector3(
			randf_range(-20, 20),
			randf_range(-5, 15),
			randf_range(-10, 10)
		)

		_spawn_bubble_at(pos + offset, layer)
