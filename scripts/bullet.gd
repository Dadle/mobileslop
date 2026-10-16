class_name Bullet
extends Node3D
## Projectile. Visuals come from the weapon table; hits are a cheap swept test against Game.targets.
## Launcher rounds explode with splash damage.

var velocity := Vector3(0, 0, -48.0)
var damage := 10.0
var life := 1.5
var pierce := 0
var splash := 0.0
var _prev: Vector3
var _w: Dictionary
var _hit_ids := {}

static var _mesh_cache := {}
static var _mat_cache := {}

func setup(w: Dictionary, dmg: float) -> void:
	_w = w
	damage = dmg
	pierce = int(w.get("pierce", 0))
	splash = float(w.get("splash", 0.0))
	life = 2.2 if splash > 0.0 else 1.5

func _ready() -> void:
	var id: String = _w.get("id", "rifle")
	if not _mesh_cache.has(id):
		var size: Vector2 = _w.get("size", Vector2(0.07, 1.0))
		var m := CapsuleMesh.new()
		m.radius = size.x
		m.height = size.y
		m.radial_segments = 8
		m.rings = 3
		_mesh_cache[id] = m
		var mat := StandardMaterial3D.new()
		mat.albedo_color = _w.get("color", Color.YELLOW)
		mat.emission_enabled = true
		mat.emission = _w.get("emission", Color.ORANGE)
		mat.emission_energy_multiplier = 5.0 if splash <= 0.0 else 2.0
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if splash <= 0.0 else BaseMaterial3D.SHADING_MODE_PER_PIXEL
		_mat_cache[id] = mat
	var mi := MeshInstance3D.new()
	mi.mesh = _mesh_cache[id]
	mi.material_override = _mat_cache[id]
	mi.rotation.x = PI * 0.5
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	if splash > 0.0:
		var light := OmniLight3D.new()
		light.light_color = Color(1.0, 0.5, 0.15)
		light.light_energy = 1.5
		light.omni_range = 3.0
		light.shadow_enabled = false
		add_child(light)
		var tip := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.12
		sm.height = 0.24
		tip.mesh = sm
		var tm := StandardMaterial3D.new()
		tm.albedo_color = Color(1.0, 0.5, 0.1)
		tm.emission_enabled = true
		tm.emission = Color(1.0, 0.45, 0.1)
		tm.emission_energy_multiplier = 6.0
		tm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		tip.material_override = tm
		tip.position = Vector3(0, 0, 0.4)
		add_child(tip)
	_prev = global_position
	# aim the mesh along the velocity
	if velocity.length() > 0.01:
		look_at(global_position + velocity, Vector3.UP)

func _physics_process(delta: float) -> void:
	var game = Globals.game
	if game == null or not game.is_playing():
		return
	life -= delta
	if life <= 0.0:
		if splash > 0.0:
			_explode(global_position)
		queue_free()
		return
	_prev = global_position
	global_position += velocity * delta
	var z_lo := global_position.z - 0.3
	var z_hi := _prev.z + 0.3
	for t in game.targets:
		if not is_instance_valid(t) or not t.alive:
			continue
		if _hit_ids.has(t.get_instance_id()):
			continue
		var tp: Vector3 = t.global_position
		if tp.z < z_lo or tp.z > z_hi:
			continue
		if absf(tp.x - global_position.x) > t.hit_radius:
			continue
		var hit_pos := Vector3(global_position.x, global_position.y, tp.z)
		if splash > 0.0:
			_explode(hit_pos)
			queue_free()
			return
		_hit_ids[t.get_instance_id()] = true
		t.hit(damage, hit_pos)
		if pierce > 0:
			pierce -= 1
			continue
		queue_free()
		return

func _explode(pos: Vector3) -> void:
	var game = Globals.game
	var parent := get_parent()
	FX.flash(parent, pos, Color(1.0, 0.7, 0.3), 1.3, 8.0, 0.14)
	FX.burst(parent, pos, Color(1.0, 0.55, 0.15), 30, 0.22, 9.0, 0.6, 6.0, 90.0, true)
	FX.burst(parent, pos, Color(0.25, 0.22, 0.2), 22, 0.3, 5.0, 1.1, 2.0, 90.0)
	FX.ring(parent, Vector3(pos.x, 0.05, pos.z), Color(1.0, 0.6, 0.2, 0.9), splash * 1.3, 0.35)
	Sfx.play("explosion", -5.0, 0.12, 1.0, 0.05)
	if game:
		game.camera_shake(0.3)
		for t in game.targets.duplicate():
			if not is_instance_valid(t) or not t.alive:
				continue
			var tp: Vector3 = t.global_position
			var d2 := Vector2(tp.x - pos.x, tp.z - pos.z).length()
			if d2 <= splash + t.hit_radius:
				t.hit(damage, Vector3(tp.x, 1.0, tp.z))
