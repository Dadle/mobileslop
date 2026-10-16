class_name Rig
extends RefCounted
## Procedural animation helper for the part-based characters (see tools/blender/ASSET_SPEC.md).

const PART_NAMES := ["Hips", "Torso", "Head", "ArmL", "ArmR", "LegL", "LegR", "Gun", "Muzzle"]

var root: Node3D
var parts := {}
var rest := {}
var meshes: Array = []
var _flash_mat: StandardMaterial3D

func _init(model_root: Node3D) -> void:
	root = model_root
	_collect(model_root)
	meshes = Globals.all_mesh_instances(model_root)
	_flash_mat = StandardMaterial3D.new()
	_flash_mat.albedo_color = Color(1, 1, 1, 1)
	_flash_mat.emission_enabled = true
	_flash_mat.emission = Color(1, 0.9, 0.8)
	_flash_mat.emission_energy_multiplier = 2.5
	_flash_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_flash_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_flash_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD

func _collect(n: Node) -> void:
	for c in n.get_children():
		if c is Node3D and PART_NAMES.has(String(c.name)):
			parts[String(c.name)] = c
			rest[String(c.name)] = (c as Node3D).transform
		_collect(c)

func has(p: String) -> bool:
	return parts.has(p)

func part(p: String) -> Node3D:
	return parts.get(p)

## Pose a part relative to its rest transform: euler (radians, XYZ) and a positional offset.
func pose(p: String, euler: Vector3, offset: Vector3 = Vector3.ZERO) -> void:
	var n: Node3D = parts.get(p)
	if n == null:
		return
	var r: Transform3D = rest[p]
	n.transform = Transform3D(r.basis * Basis.from_euler(euler), r.origin + offset)

func reset_pose() -> void:
	for p in parts:
		(parts[p] as Node3D).transform = rest[p]

## Heroic run cycle. t in cycles (1.0 = one full stride), amp 0..1 blends from idle to full run.
func run_cycle(t: float, amp: float = 1.0) -> void:
	var w := t * TAU
	var leg := sin(w) * 0.75 * amp
	pose("LegL", Vector3(leg, 0, 0))
	pose("LegR", Vector3(-leg, 0, 0))
	var bob := absf(sin(w)) * 0.07 * amp
	pose("Hips", Vector3(-0.12 * amp, 0, sin(w) * 0.03 * amp), Vector3(0, bob, 0))
	pose("Torso", Vector3(-0.06 * amp, sin(w) * 0.05 * amp, 0))
	pose("Head", Vector3(0.12 * amp, -sin(w) * 0.03 * amp, 0))
	pose("ArmL", Vector3(sin(w * 2.0) * 0.04 * amp, 0, 0), Vector3(0, -absf(sin(w)) * 0.01, 0))
	pose("ArmR", Vector3(sin(w * 2.0) * 0.04 * amp, 0, 0))

## Idle breathing pose.
func idle(t: float) -> void:
	pose("Torso", Vector3(sin(t * 2.0) * 0.02, 0, 0))
	pose("Head", Vector3(sin(t * 1.3) * 0.04, sin(t * 0.7) * 0.1, 0))
	pose("ArmL", Vector3(sin(t * 2.0) * 0.02, 0, 0))
	pose("ArmR", Vector3(sin(t * 2.0) * 0.02, 0, 0))
	pose("LegL", Vector3.ZERO)
	pose("LegR", Vector3.ZERO)
	pose("Hips", Vector3.ZERO)

## Zombie shamble. phase offsets individuals; limp 0..1 makes it more lopsided.
func shamble(t: float, phase: float, limp: float = 0.5, brute: bool = false) -> void:
	var w := t * TAU + phase
	var stride := 0.45 if not brute else 0.35
	var leg_l := sin(w) * stride
	var leg_r := -sin(w) * stride * (1.0 - limp * 0.45)
	pose("LegL", Vector3(leg_l, 0, 0.05 * limp))
	pose("LegR", Vector3(leg_r, 0, -0.08 * limp))
	pose("Hips", Vector3(-0.18, 0, sin(w) * 0.07), Vector3(0, absf(sin(w)) * 0.04 - 0.03, 0))
	pose("Torso", Vector3(-0.25 - 0.1 * limp, sin(w * 0.5) * 0.12, sin(w) * 0.12))
	pose("Head", Vector3(0.35 + sin(w * 0.5) * 0.1, sin(w * 0.37 + phase) * 0.35, 0.25 * sin(w * 0.5)))
	pose("ArmL", Vector3(sin(w + 1.0) * 0.15 - 0.1 * limp, 0, sin(w * 0.7) * 0.1))
	pose("ArmR", Vector3(sin(w + 2.3) * 0.15, 0, -sin(w * 0.9) * 0.1))

## Brief white flash on hit (uses material_overlay so shared materials stay intact).
func flash(duration: float = 0.07) -> void:
	for m in meshes:
		if is_instance_valid(m):
			m.material_overlay = _flash_mat
	var tree := root.get_tree()
	if tree == null:
		return
	await tree.create_timer(duration).timeout
	for m in meshes:
		if is_instance_valid(m):
			m.material_overlay = null

func set_shadow(enabled: bool) -> void:
	for m in meshes:
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if enabled else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
