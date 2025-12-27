extends Node3D
## ============================================================================
## DONK_TANK - ROBUST 60FPS CONTROLLER
## Based on PLAN.md research:
## - Physics interpolation enabled (smooth movement)
## - Delta smoothing enabled (no micro-stutters)
## - Mobile renderer (faster than Forward+)
## - Shader warmup on startup
## - GPU verification
## ============================================================================

# Tank dimensions (2:1 aspect ratio matches 1440x720)
const TANK_WIDTH: float = 720.0
const TANK_HEIGHT: float = 288.0
const TANK_DEPTH: float = 200.0
const SAND_Y: float = -78.0
const SURFACE_Y: float = 90.0

# Performance settings
const PEBBLE_COUNT: int = 15
const TARGET_FPS: float = 60.0
const FRAME_BUDGET_MS: float = 16.666

# Cached node references (avoid per-frame lookups)
@onready var camera: Camera3D = $Camera3D
@onready var sand_floor: MeshInstance3D = $SandFloor
@onready var bubble_system: BubbleSystem = $BubbleSystem
@onready var pebble_container: Node3D = $Pebbles
@onready var creature_container: Node3D = $Creatures

# Creature preload (compile-time, not runtime)
const HammerheadCreatureScene = preload("res://scripts/creatures/hammerhead_creature.gd")
var shark_list: Array[HammerheadCreature] = []

# Frame timing (minimal overhead)
var _frame_count: int = 0
var _fps_timer: float = 0.0
var _current_fps: int = 60
var _worst_fps: int = 60
var _startup_complete: bool = false

# GPU info cache
var _gpu_name: String = ""
var _is_dedicated_gpu: bool = false


func _ready() -> void:
	# Lock to 60 FPS
	Engine.max_fps = 60
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)

	# Phase 7: GPU Verification
	_verify_gpu()

	# Phase 6: Shader warmup
	_warmup_shaders()

	# Setup scene
	_setup_camera()
	_create_pebbles()

	# No initial shark - press 1 to summon sharks!
	# Tank starts empty, waiting for player input

	# Mark startup complete after a few frames
	await get_tree().create_timer(0.1).timeout
	_startup_complete = true

	_print_startup_summary()


func _verify_gpu() -> void:
	print("=" .repeat(50))
	print(" DONK_TANK - GPU VERIFICATION")
	print("=" .repeat(50))

	_gpu_name = RenderingServer.get_video_adapter_name()
	var vendor: String = RenderingServer.get_video_adapter_vendor()
	var renderer: String = ProjectSettings.get_setting(
		"rendering/renderer/rendering_method", "unknown"
	)

	print(" GPU: ", _gpu_name)
	print(" Vendor: ", vendor)
	print(" Renderer: ", renderer)

	# Check for dedicated GPU
	var gpu_lower: String = _gpu_name.to_lower()
	var vendor_lower: String = vendor.to_lower()

	_is_dedicated_gpu = (
		gpu_lower.contains("nvidia") or
		gpu_lower.contains("geforce") or
		gpu_lower.contains("rtx") or
		gpu_lower.contains("gtx") or
		gpu_lower.contains("radeon") or
		gpu_lower.contains("rx ") or
		vendor_lower.contains("nvidia") or
		vendor_lower.contains("amd")
	)

	if _is_dedicated_gpu:
		print(" [OK] Dedicated GPU detected!")
	else:
		print(" [WARNING] May be using INTEGRATED GPU!")
		print(" ")
		print(" TO FIX ON WINDOWS:")
		print("   1. Settings > System > Display > Graphics")
		print("   2. Click 'Browse', find Godot.exe")
		print("   3. Set to 'High Performance'")
		print(" ")

	# Check physics interpolation
	var phys_interp: bool = ProjectSettings.get_setting(
		"physics/common/physics_interpolation", false
	)
	print(" Physics Interpolation: ", "ENABLED" if phys_interp else "DISABLED")

	# Check delta smoothing
	var delta_smooth: bool = ProjectSettings.get_setting(
		"application/run/delta_smoothing", false
	)
	print(" Delta Smoothing: ", "ENABLED" if delta_smooth else "DISABLED")

	print("=" .repeat(50))


func _warmup_shaders() -> void:
	print("[WARMUP] Compiling shaders...")

	# Force GPU sync to compile all pending shaders
	RenderingServer.force_sync()

	# Wait for 2 frames to ensure shaders are compiled
	await get_tree().process_frame
	await get_tree().process_frame

	print("[WARMUP] Shaders ready!")


func _setup_camera() -> void:
	camera.position = Vector3(0, 0, 288)
	camera.look_at(Vector3.ZERO)


func _print_startup_summary() -> void:
	print("")
	print("[READY] Donk Tank initialized!")
	var bubble_count: int = bubble_system.get_active_count() if bubble_system else 0
	print("  Active Bubbles: ", bubble_count, " (MultiMesh system)")
	print("  Pebbles: ", pebble_container.get_child_count())
	print("  Sharks: ", shark_list.size(), " (tank starts empty)")
	print("")
	print("  CONTROLS:")
	print("    [1] Summon a shark (dramatic entrance)")
	print("    [2] Cycle shark colors (11 neon colors)")
	print("    [F1] Performance report")
	print("=" .repeat(50))
	print("")


## ============================================================================
## PHYSICS PROCESS - Fixed 60 TPS, interpolated for smooth rendering
## Creatures now manage their own movement via state machines
## ============================================================================
func _physics_process(_delta: float) -> void:
	# Clean up invalid sharks from list
	for i in range(shark_list.size() - 1, -1, -1):
		if not is_instance_valid(shark_list[i]):
			shark_list.remove_at(i)


## ============================================================================
## PROCESS - Rendering frame, minimal work here
## ============================================================================
func _process(delta: float) -> void:
	_update_fps_counter(delta)


func _update_fps_counter(delta: float) -> void:
	_frame_count += 1
	_fps_timer += delta

	if _fps_timer >= 1.0:
		_current_fps = _frame_count

		# Track worst FPS after startup
		if _startup_complete and _current_fps < _worst_fps:
			_worst_fps = _current_fps

		# Only log if performance drops
		if _startup_complete and _current_fps < 55:
			var frame_ms: float = 1000.0 / max(_current_fps, 1)
			print("[PERF] FPS: ", _current_fps, " (", "%.1f" % frame_ms, "ms)")

		_frame_count = 0
		_fps_timer = 0.0


## ============================================================================
## INPUT - Shark spawning
## ============================================================================
func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1:
				_spawn_shark()
				print("[SPAWN] Shark added! Total: ", shark_list.size())
			KEY_F1:
				_print_performance_report()


func _print_performance_report() -> void:
	print("")
	print("=" .repeat(50))
	print(" PERFORMANCE REPORT")
	print("=" .repeat(50))
	print(" GPU: ", _gpu_name)
	print(" Dedicated: ", _is_dedicated_gpu)
	print(" Current FPS: ", _current_fps)
	print(" Worst FPS: ", _worst_fps)
	var active_bubbles: int = bubble_system.get_active_count() if bubble_system else 0
	print(" Active Bubbles: ", active_bubbles)
	print(" Sharks: ", shark_list.size())
	print(" Pebbles: ", pebble_container.get_child_count())
	print("=" .repeat(50))
	print("")


## ============================================================================
## SHARK SPAWNING - Now uses HammerheadCreature with full state machine
## ============================================================================
func _spawn_shark() -> void:
	var shark := HammerheadCreatureScene.new()

	# The HammerheadCreature handles its own spawning via EntranceState
	# It will swim in from off-screen with proper animation

	# Randomize base speed slightly
	shark.base_speed = randf_range(30.0, 42.0)

	creature_container.add_child(shark)
	shark_list.append(shark)


## ============================================================================
## PEBBLES - Static decoration (created once, never updated)
## ============================================================================
func _create_pebbles() -> void:
	# Reuse single mesh for all pebbles (memory efficient)
	var pebble_mesh := SphereMesh.new()
	pebble_mesh.radius = 1.0
	pebble_mesh.height = 2.0
	pebble_mesh.radial_segments = 3  # Minimal geometry
	pebble_mesh.rings = 2

	# Color palette
	var colors: Array[Color] = [
		Color(0.38, 0.32, 0.26),
		Color(0.45, 0.38, 0.30),
		Color(0.50, 0.43, 0.35),
		Color(0.32, 0.26, 0.20)
	]

	for i in range(PEBBLE_COUNT):
		var pebble := MeshInstance3D.new()
		pebble.mesh = pebble_mesh

		# Flatten spheres into pebble shapes
		var s: float = randf_range(1.2, 3.0)
		pebble.scale = Vector3(s * 0.55, s * 0.25, s * 0.5)

		# Position on sand
		pebble.position = Vector3(
			randf_range(-TANK_WIDTH * 0.55, TANK_WIDTH * 0.55),
			SAND_Y + randf_range(1, 4),
			randf_range(-TANK_DEPTH * 0.6, TANK_DEPTH * 0.6)
		)
		pebble.rotation = Vector3(randf() * TAU, randf() * TAU, randf() * TAU)

		# Unshaded material (fastest)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = colors[randi() % colors.size()]
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		pebble.material_override = mat

		pebble_container.add_child(pebble)
