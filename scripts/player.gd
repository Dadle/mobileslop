class_name Player
extends Node3D
## The squad: 1-5 soldiers running in formation, auto-firing the current weapon. Upgrades are all visual:
## more soldiers, a new gun + ammo per damage tier, more bullets per second, and a timed splash launcher.

signal died
signal hp_changed(hp: float, max_hp: float)
signal stats_changed

const LATERAL_SPEED := 9.0
const BASE_FIRE_RATE := 5.0
const MAX_FIRE_RATE := 12.0
const MAX_SQUAD := 5
const FORMATION := [Vector2(0, 0), Vector2(-0.8, 0.9), Vector2(0.8, 0.9), Vector2(-0.42, 1.8), Vector2(0.42, 1.8)]

var max_hp := 100.0
var hp := 100.0
var fire_rate := BASE_FIRE_RATE      # shots per second per soldier
var weapon_tier := 0
var squad_size := 1
var launcher_until := 0.0
var shield_until := 0.0

var input_axis := 0.0        # -1..1 from keys / autopilot
var drag_dx := 0.0           # accumulated touch drag in world units
var running := false
var speed_scale := 1.0
var alive := true

var _soldiers: Array = []    # [{node, rig, weapon_root, weapon_rest, muzzle, accum, recoil}]
var _anim_t := 0.0
var _vx := 0.0
var _shield_mesh: MeshInstance3D
var _shield_mat: StandardMaterial3D
var _step_phase := 0.0
var _invuln_until := 0.0
var _bullet_parent: Node
var _death_tween: Tween
var _current_weapon_id := ""

func _ready() -> void:
	_shield_mesh = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 1.25
	sm.height = 2.5
	_shield_mesh.mesh = sm
	_shield_mat = StandardMaterial3D.new()
	_shield_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_shield_mat.albedo_color = Color(0.3, 0.7, 1.0, 0.12)
	_shield_mat.emission_enabled = true
	_shield_mat.emission = Color(0.3, 0.7, 1.0)
	_shield_mat.emission_energy_multiplier = 1.2
	_shield_mat.rim_enabled = true
	_shield_mat.rim = 1.0
	_shield_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_shield_mesh.material_override = _shield_mat
	_shield_mesh.position = Vector3(0, 1.1, 0.6)
	_shield_mesh.visible = false
	_shield_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_shield_mesh)
	_set_squad(1)

func setup(bullet_parent: Node) -> void:
	_bullet_parent = bullet_parent

func reset_run() -> void:
	max_hp = 100.0
	hp = max_hp
	fire_rate = BASE_FIRE_RATE
	weapon_tier = 0
	launcher_until = 0.0
	shield_until = 0.0
	alive = true
	running = false
	speed_scale = 1.0
	if _death_tween and _death_tween.is_valid():
		_death_tween.kill()
	position.x = 0.0
	_vx = 0.0
	drag_dx = 0.0
	input_axis = 0.0
	rotation = Vector3.ZERO
	_set_squad(1)
	_refresh_weapons()
	hp_changed.emit(hp, max_hp)
	stats_changed.emit()

func now() -> float:
	return Time.get_ticks_msec() / 1000.0

func is_shielded() -> bool:
	return now() < shield_until

func is_launcher() -> bool:
	return now() < launcher_until

func weapon() -> Dictionary:
	return Weapons.LAUNCHER if is_launcher() else Weapons.tier(weapon_tier)

func weapon_damage() -> float:
	var base: float = Weapons.tier(weapon_tier)["damage"]
	return base * float(Weapons.LAUNCHER["damage_mult"]) if is_launcher() else base

func effective_fire_rate() -> float:
	return fire_rate * (float(Weapons.LAUNCHER["rate_mult"]) if is_launcher() else 1.0)

## Rough sustained damage per second (used to size bosses and crates).
func dps() -> float:
	return Weapons.tier(weapon_tier)["damage"] * fire_rate * squad_size

func shots_per_second() -> float:
	return fire_rate * squad_size

# ------------------------------------------------------------------ squad / weapon visuals
func _set_squad(n: int) -> void:
	squad_size = clampi(n, 1, MAX_SQUAD)
	while _soldiers.size() > squad_size:
		var s: Dictionary = _soldiers.pop_back()
		s["node"].queue_free()
	while _soldiers.size() < squad_size:
		var idx := _soldiers.size()
		var model := Globals.model("soldier")
		var off: Vector2 = FORMATION[idx]
		model.position = Vector3(off.x, 0, off.y)
		add_child(model)
		var rig := Rig.new(model)
		rig.set_shadow(true)
		_soldiers.append({"node": model, "rig": rig, "weapon_root": null, "weapon_rest": Transform3D(), "muzzle": null,
			"accum": float(idx) / float(MAX_SQUAD), "recoil": 0.0, "phase": randf() * 0.3})
		_attach_weapon(_soldiers[idx], weapon())
		if idx > 0 and is_inside_tree():
			FX.flash(_bullet_parent if _bullet_parent else self, global_position + Vector3(off.x, 1.0, off.y), Color(0.5, 0.9, 1.0), 0.6, 4.0, 0.15)
	_current_weapon_id = weapon()["id"]

func _attach_weapon(s: Dictionary, w: Dictionary) -> void:
	var res := Weapons.attach(s["node"], w)
	s["weapon_root"] = res["root"]
	s["muzzle"] = res["muzzle"]
	if res["root"]:
		s["weapon_rest"] = (res["root"] as Node3D).transform

func _refresh_weapons() -> void:
	var w := weapon()
	if w["id"] == _current_weapon_id:
		return
	_current_weapon_id = w["id"]
	for s in _soldiers:
		_attach_weapon(s, w)

# ------------------------------------------------------------------ frame
func _process(delta: float) -> void:
	_anim_t += delta
	var game = Globals.game
	var playing: bool = game != null and game.is_playing()
	_refresh_weapons()   # handles the launcher timing out
	if playing and alive:
		var target_v := input_axis * LATERAL_SPEED
		_vx = lerpf(_vx, target_v, 1.0 - exp(-delta * 14.0))
		var dx := _vx * delta + drag_dx
		drag_dx = 0.0
		position.x = clampf(position.x + dx, -Globals.ROAD_HALF_WIDTH, Globals.ROAD_HALF_WIDTH)
		position.z -= Globals.RUN_SPEED * speed_scale * delta
		var lean_target := clampf(-dx / maxf(delta, 0.0001) * 0.045, -0.35, 0.35)
		var stride_rate := Globals.RUN_SPEED / 3.4
		var amp := clampf(speed_scale, 0.0, 1.0)
		for s in _soldiers:
			var model: Node3D = s["node"]
			model.rotation.z = lerpf(model.rotation.z, lean_target, 1.0 - exp(-delta * 10.0))
			model.rotation.y = lerpf(model.rotation.y, lean_target * 0.6, 1.0 - exp(-delta * 10.0))
			var rig: Rig = s["rig"]
			if amp > 0.05:
				rig.run_cycle(_anim_t * stride_rate + s["phase"], amp)
			else:
				rig.idle(_anim_t + s["phase"] * 7.0)
		var sp := fmod(_anim_t * stride_rate, 1.0)
		if amp > 0.3 and (sp < 0.5) != (_step_phase < 0.5):
			Sfx.play("footstep_%d" % (randi() % 2), -14.0 + 2.0 * squad_size, 0.15)
		_step_phase = sp
		# auto fire: every soldier has its own accumulator so shots interleave
		var rate := effective_fire_rate()
		for i in _soldiers.size():
			var s: Dictionary = _soldiers[i]
			s["accum"] += delta * rate
			if s["accum"] >= 1.0:
				s["accum"] -= 1.0
				_fire(s, i)
	else:
		for s in _soldiers:
			var model: Node3D = s["node"]
			(s["rig"] as Rig).idle(_anim_t + s["phase"] * 7.0)
			model.rotation.z = lerpf(model.rotation.z, 0.0, delta * 8.0)
	# recoil decay
	for s in _soldiers:
		s["recoil"] = lerpf(s["recoil"], 0.0, 1.0 - exp(-delta * 18.0))
		var wr: Node3D = s["weapon_root"]
		if wr and is_instance_valid(wr):
			var rest: Transform3D = s["weapon_rest"]
			var r: float = s["recoil"]
			wr.transform = Transform3D(rest.basis * Basis.from_euler(Vector3(-r * 0.22, 0, 0)), rest.origin + Vector3(0, 0, r * 0.1))
	# shield visuals
	var shielded := is_shielded()
	_shield_mesh.visible = shielded
	if shielded:
		var remaining := shield_until - now()
		var pulse := 0.12 + 0.05 * sin(_anim_t * 12.0)
		if remaining < 1.5:
			pulse *= 0.5 + 0.5 * absf(sin(_anim_t * 25.0))
		_shield_mat.albedo_color.a = pulse
		_shield_mesh.rotation.y += delta * 1.5

func _fire(s: Dictionary, index: int) -> void:
	if _bullet_parent == null:
		return
	var w := weapon()
	var muzzle: Node3D = s["muzzle"]
	var model: Node3D = s["node"]
	var origin: Vector3 = muzzle.global_position if muzzle and is_instance_valid(muzzle) else model.global_position + Vector3(0.1, 1.3, -0.8)
	var b := Bullet.new()
	b.setup(w, weapon_damage())
	# side soldiers converge their fire toward the leader's line ~22 m ahead
	var off: Vector2 = FORMATION[index]
	var speed: float = w["speed"]
	b.velocity = Vector3(-off.x * speed / 22.0, 0, -speed)
	_bullet_parent.add_child(b)
	b.global_position = origin
	s["recoil"] = 1.0
	FX.flash(_bullet_parent, origin + Vector3(0, 0, -0.15), w["flash"], 0.16 * float(w["scale"]), 3.0, 0.05)
	Sfx.play(w["sfx"], w["sfx_db"] + 1.5 * (squad_size - 1), 0.12, 1.0, 0.04)

# ------------------------------------------------------------------ damage / upgrades
func take_damage(amount: float, _source_pos: Vector3) -> void:
	if not alive:
		return
	if is_shielded() or now() < _invuln_until:
		FX.ring(_bullet_parent, global_position, Color(0.4, 0.8, 1.0, 0.8), 2.0, 0.3)
		return
	hp = maxf(0.0, hp - amount)
	_invuln_until = now() + 0.25
	hp_changed.emit(hp, max_hp)
	Sfx.play("player_hurt", -2.0, 0.1)
	FX.burst(_bullet_parent, global_position + Vector3(0, 1.2, 0), Color(0.9, 0.1, 0.1), 14, 0.1, 4.0, 0.5)
	if Globals.game:
		Globals.game.camera_shake(0.5)
		Globals.game.hud.damage_flash()
	for s in _soldiers:
		(s["rig"] as Rig).flash(0.1)
	if hp <= 0.0:
		alive = false
		running = false
		died.emit()
		_death_tween = create_tween()
		_death_tween.set_parallel(true)
		for s in _soldiers:
			_death_tween.tween_property(s["node"], "rotation:x", -PI * 0.5, 0.5).set_ease(Tween.EASE_IN)

func heal(amount: float) -> void:
	hp = minf(max_hp, hp + amount)
	hp_changed.emit(hp, max_hp)

func apply_powerup(kind: String) -> String:
	var label := ""
	match kind:
		"soldier":
			_set_squad(squad_size + 1)
			label = "+1 SOLDIER  (x%d)" % squad_size
		"weapon":
			weapon_tier = mini(Weapons.MAX_TIER, weapon_tier + 1)
			_current_weapon_id = ""
			_refresh_weapons()
			label = str(Weapons.tier(weapon_tier)["name"]) + "!"
		"fire_rate":
			fire_rate = minf(MAX_FIRE_RATE, fire_rate + 1.5)
			label = "FIRE RATE UP!"
		"launcher":
			launcher_until = maxf(launcher_until, now()) + 18.0
			_refresh_weapons()
			label = "LAUNCHER!"
		"heal":
			heal(40.0)
			label = "+40 HP"
		"shield":
			shield_until = maxf(shield_until, now()) + 7.0
			label = "SHIELD!"
		"nuke":
			label = "NUKE!"
	stats_changed.emit()
	return label
