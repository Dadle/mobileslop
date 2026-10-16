extends Node
## Autoload "Globals": shared constants, save data, model loading (with placeholders), cmdline args.

const LANE_ZOMBIE_X := -2.0
const LANE_BONUS_X := 2.0
const ROAD_HALF_WIDTH := 3.0       # how far the player may move sideways
const RUN_SPEED := 6.5             # m/s forward
const SEGMENT_LENGTH := 20.0

var game: Node = null              # set by game.gd
var best_score := 0
var best_distance := 0
var runs := 0
var sfx_on := true

# command line / autopilot
var autopilot := false
var shots_dir := ""
var duration := 0.0
var shot_interval := 3.0

var _models := {}
var _font_cache := {}

func _ready() -> void:
	_parse_args()
	_load_save()

func _parse_args() -> void:
	var args := OS.get_cmdline_user_args()
	var i := 0
	while i < args.size():
		var a: String = args[i]
		match a:
			"--autopilot":
				autopilot = true
			"--shots-dir":
				i += 1
				shots_dir = args[i]
			"--duration":
				i += 1
				duration = float(args[i])
			"--shot-interval":
				i += 1
				shot_interval = float(args[i])
		i += 1

func _load_save() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("user://save.cfg") == OK:
		best_score = cfg.get_value("stats", "best_score", 0)
		best_distance = cfg.get_value("stats", "best_distance", 0)
		runs = cfg.get_value("stats", "runs", 0)
		sfx_on = cfg.get_value("settings", "sfx_on", true)

func save() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("stats", "best_score", best_score)
	cfg.set_value("stats", "best_distance", best_distance)
	cfg.set_value("stats", "runs", runs)
	cfg.set_value("settings", "sfx_on", sfx_on)
	cfg.save("user://save.cfg")

func font(which: String) -> Font:
	if _font_cache.has(which):
		return _font_cache[which]
	var path: String = {
		"title": "res://assets/fonts/Bangers-Regular.ttf",
		"bold": "res://assets/fonts/LilitaOne-Regular.ttf",
		"ui": "res://assets/fonts/Rubik-Variable.ttf",
	}.get(which, "res://assets/fonts/LilitaOne-Regular.ttf")
	var f: Font = load(path) if ResourceLoader.exists(path) else ThemeDB.fallback_font
	if which == "ui" and f is FontFile:
		var fv := FontVariation.new()
		fv.base_font = f
		fv.variation_opentype = {"wght": 700}
		f = fv
	_font_cache[which] = f
	return f

## Instantiates a GLB model from assets/models/<name>.glb. Falls back to a blocky placeholder
## with the same part hierarchy so the game is playable before art exists.
func model(name: String) -> Node3D:
	var path := "res://assets/models/%s.glb" % name
	if not _models.has(path):
		_models[path] = load(path) if ResourceLoader.exists(path) else null
	var scene: PackedScene = _models[path]
	if scene != null:
		var inst := scene.instantiate() as Node3D
		return inst
	return _placeholder(name)

func _mat(c: Color, metallic := 0.0, rough := 0.7) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metallic
	m.roughness = rough
	return m

func _box(parent: Node3D, pname: String, size: Vector3, origin: Vector3, center_offset: Vector3, c: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = pname
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = _mat(c)
	# mesh is centered on the node; shift geometry so the node origin acts as the pivot
	var holder := Node3D.new()
	holder.name = pname
	holder.position = origin
	parent.add_child(holder)
	mi.name = pname + "Mesh"
	mi.position = center_offset
	holder.add_child(mi)
	return mi

func _placeholder(name: String) -> Node3D:
	var root := Node3D.new()
	root.name = name
	match name:
		"soldier", "zombie", "zombie_brute":
			var s := 1.0 if name != "zombie_brute" else 1.35
			var skin := Color(0.85, 0.65, 0.5) if name == "soldier" else Color(0.45, 0.6, 0.42)
			var cloth := Color(0.33, 0.42, 0.24) if name == "soldier" else Color(0.3, 0.3, 0.45)
			var r := Node3D.new()
			r.name = "Soldier" if name == "soldier" else "Zombie"
			r.scale = Vector3.ONE * s
			root.add_child(r)
			var hips := Node3D.new()
			hips.name = "Hips"
			hips.position = Vector3(0, 0.95, 0)
			r.add_child(hips)
			var hm := _box(hips, "HipsGeo", Vector3(0.42, 0.18, 0.26), Vector3.ZERO, Vector3(0, -0.05, 0), cloth.darkened(0.2))
			var torso := Node3D.new()
			torso.name = "Torso"
			torso.position = Vector3(0, 0.02, 0)
			hips.add_child(torso)
			_box(torso, "TorsoGeo", Vector3(0.5, 0.55, 0.3), Vector3.ZERO, Vector3(0, 0.28, 0), cloth)
			var head := Node3D.new()
			head.name = "Head"
			head.position = Vector3(0, 0.58, 0)
			torso.add_child(head)
			_box(head, "HeadGeo", Vector3(0.32, 0.32, 0.32), Vector3.ZERO, Vector3(0, 0.18, 0), skin)
			for side in ["L", "R"]:
				var sx := -1.0 if side == "L" else 1.0
				var arm := Node3D.new()
				arm.name = "Arm" + side
				arm.position = Vector3(sx * 0.32, 0.5, 0)
				torso.add_child(arm)
				if name == "soldier":
					_box(arm, "ArmGeo", Vector3(0.14, 0.14, 0.55), Vector3.ZERO, Vector3(0, -0.05, -0.25), cloth)
				else:
					_box(arm, "ArmGeo", Vector3(0.14, 0.14, 0.6), Vector3.ZERO, Vector3(0, 0, -0.3), skin)
				var leg := Node3D.new()
				leg.name = "Leg" + side
				leg.position = Vector3(sx * 0.12, 0, 0)
				hips.add_child(leg)
				_box(leg, "LegGeo", Vector3(0.18, 0.9, 0.2), Vector3.ZERO, Vector3(0, -0.47, 0), cloth.darkened(0.35))
				if name == "soldier" and side == "R":
					var gun := Node3D.new()
					gun.name = "Gun"
					gun.position = Vector3(-0.12, -0.08, -0.35)
					arm.add_child(gun)
					_box(gun, "GunGeo", Vector3(0.08, 0.14, 0.7), Vector3.ZERO, Vector3(0, 0, -0.2), Color(0.15, 0.15, 0.17))
					var muzzle := Node3D.new()
					muzzle.name = "Muzzle"
					muzzle.position = Vector3(0, 0.02, -0.6)
					gun.add_child(muzzle)
		"crate":
			var r := Node3D.new()
			r.name = "Crate"
			root.add_child(r)
			_box(r, "CrateGeo", Vector3(1, 1, 1), Vector3.ZERO, Vector3(0, 0.5, 0), Color(0.42, 0.48, 0.25))
		"gate":
			var r := Node3D.new()
			r.name = "Gate"
			root.add_child(r)
			_box(r, "GateGeo", Vector3(3.4, 1.5, 0.7), Vector3.ZERO, Vector3(0, 0.75, 0), Color(0.42, 0.48, 0.25))
			_box(r, "Panel", Vector3(1.3, 1.0, 0.04), Vector3.ZERO, Vector3(0, 0.8, 0.36), Color(0.6, 0.65, 0.4))
		"boss":
			var b := _placeholder("zombie_brute")
			b.scale = Vector3.ONE * 2.1
			return b
		"powerup":
			var r := Node3D.new()
			r.name = "Powerup"
			root.add_child(r)
			var mi := MeshInstance3D.new()
			var cm := CapsuleMesh.new()
			cm.radius = 0.22
			cm.height = 0.7
			mi.mesh = cm
			mi.material_override = _mat(Color(1.0, 0.8, 0.2), 0.8, 0.3)
			mi.position = Vector3(0, 0.6, 0)
			r.add_child(mi)
		"road_segment":
			var mi := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(8, 0.2, SEGMENT_LENGTH)
			mi.mesh = bm
			mi.material_override = _mat(Color(0.22, 0.22, 0.24))
			mi.position = Vector3(0, -0.1, SEGMENT_LENGTH * 0.5)
			root.add_child(mi)
			for sx in [-1.0, 1.0]:
				var sw := MeshInstance3D.new()
				var sb := BoxMesh.new()
				sb.size = Vector3(2, 0.3, SEGMENT_LENGTH)
				sw.mesh = sb
				sw.material_override = _mat(Color(0.55, 0.55, 0.52))
				sw.position = Vector3(sx * 5.0, 0.0, SEGMENT_LENGTH * 0.5)
				root.add_child(sw)
		"building_a", "building_b", "building_c":
			var h: float = {"building_a": 10.0, "building_b": 16.0, "building_c": 24.0}[name]
			var c: Color = {"building_a": Color(0.55, 0.3, 0.25), "building_b": Color(0.5, 0.5, 0.52), "building_c": Color(0.6, 0.55, 0.45)}[name]
			_box(root, "Bldg", Vector3(8, h, 8), Vector3.ZERO, Vector3(0, h * 0.5, 0), c)
		"car_wreck":
			_box(root, "Car", Vector3(2, 1.2, 4.5), Vector3.ZERO, Vector3(0, 0.6, 0), Color(0.5, 0.3, 0.2))
		"barrier":
			_box(root, "Barrier", Vector3(2, 0.9, 0.5), Vector3.ZERO, Vector3(0, 0.45, 0), Color(0.6, 0.6, 0.58))
		"lamp_post":
			_box(root, "Post", Vector3(0.2, 6, 0.2), Vector3.ZERO, Vector3(0, 3, 0), Color(0.3, 0.3, 0.32))
		"tree_dead":
			_box(root, "Trunk", Vector3(0.4, 5, 0.4), Vector3.ZERO, Vector3(0, 2.5, 0), Color(0.25, 0.18, 0.12))
		"sandbag":
			_box(root, "Bags", Vector3(2, 0.8, 0.6), Vector3.ZERO, Vector3(0, 0.4, 0), Color(0.7, 0.6, 0.4))
		_:
			_box(root, "Unknown", Vector3.ONE, Vector3.ZERO, Vector3(0, 0.5, 0), Color.MAGENTA)
	return root

## Find a descendant by name (recursive).
static func find_node(n: Node, nm: String) -> Node:
	if n.name == nm:
		return n
	for c in n.get_children():
		var r := find_node(c, nm)
		if r != null:
			return r
	return null

static var _tint_cache := {}

## Tints a model's materials (duplicated per tint key so shared GLB materials stay intact).
## only_materials: list of substrings; when non-empty only material names containing one of them are tinted.
static func tint_meshes(root: Node, tint: Color, amount: float, only_materials: Array = [], emission: Color = Color.BLACK, emission_energy: float = 0.0) -> void:
	for mi in all_mesh_instances(root):
		var mesh: Mesh = mi.mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var src: Material = mi.get_surface_override_material(i)
			if src == null:
				src = mesh.surface_get_material(i)
			if src == null or not (src is BaseMaterial3D):
				continue
			var nm := String(src.resource_name)
			if only_materials.size() > 0:
				var ok := false
				for sub in only_materials:
					if nm.contains(sub):
						ok = true
						break
				if not ok:
					continue
			var key := "%s|%s|%s|%.2f|%s|%.1f" % [src.get_instance_id(), nm, tint.to_html(), amount, emission.to_html(), emission_energy]
			if not _tint_cache.has(key):
				var m: StandardMaterial3D = src.duplicate()
				m.albedo_color = m.albedo_color.lerp(tint, amount)
				if emission_energy > 0.0:
					m.emission_enabled = true
					m.emission = emission
					m.emission_energy_multiplier = emission_energy
				_tint_cache[key] = m
			mi.set_surface_override_material(i, _tint_cache[key])

static func all_mesh_instances(n: Node, out: Array = []) -> Array:
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		all_mesh_instances(c, out)
	return out
