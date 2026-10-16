class_name Zombie
extends Node3D
## Shambling enemy walking toward the player (+Z). Steers sideways toward the player when close.
## Tiers (after each boss) recolour the horde and multiply HP. The boss is a giant variant that
## holds the road until killed.

const TIER_COLORS := [
	{"skin": Color(0.5, 0.65, 0.4), "eye": Color(0.1, 0.1, 0.1), "amount": 0.0, "name": "GREEN"},
	{"skin": Color(0.6, 0.3, 0.8), "eye": Color(0.9, 0.3, 1.0), "amount": 0.75, "name": "VIOLET"},
	{"skin": Color(0.85, 0.2, 0.15), "eye": Color(1.0, 0.6, 0.1), "amount": 0.8, "name": "CRIMSON"},
	{"skin": Color(0.15, 0.15, 0.2), "eye": Color(1.0, 0.25, 0.1), "amount": 0.85, "name": "ASH"},
	{"skin": Color(0.95, 0.8, 0.25), "eye": Color(0.3, 1.0, 1.0), "amount": 0.8, "name": "GOLD"},
	{"skin": Color(0.2, 0.9, 0.9), "eye": Color(1.0, 1.0, 1.0), "amount": 0.8, "name": "FROST"},
]

var alive := true
var hp := 20.0
var max_hp := 20.0
var speed := 1.8
var is_brute := false
var is_boss := false
var tier := 0
var hit_radius := 0.55
var contact_damage := 15.0
var score_value := 10
var lateral_speed := 1.6
var aggro_range := 11.0

var _rig: Rig
var _model: Node3D
var _t := randf() * 10.0
var _phase := randf() * TAU
var _limp := randf()
var _groan_timer := randf_range(1.0, 5.0)
var _hp_bar: Node3D
var _hp_fill: MeshInstance3D
var _attack_cd := 0.0
var _home_x := 0.0

func _ready() -> void:
	_model = Globals.model("boss" if is_boss else ("zombie_brute" if is_brute else "zombie"))
	add_child(_model)
	_model.rotation.y = PI    # face +Z (toward the player)
	_rig = Rig.new(_model)
	_rig.set_shadow(true)
	_home_x = position.x
	if is_boss:
		hit_radius = 2.1
		_apply_tier_colors(tier + 1, true)
	else:
		if is_brute:
			hit_radius = 0.95
			_build_hp_bar()
		_apply_tier_colors(tier, false)

func _apply_tier_colors(t: int, boss: bool) -> void:
	var c: Dictionary = TIER_COLORS[t % TIER_COLORS.size()]
	if t == 0 and not boss:
		return
	Globals.tint_meshes(_model, c["skin"], c["amount"], ["skin", "bossskin", "bskin", "zskin", "zhair"])
	Globals.tint_meshes(_model, c["eye"], 1.0, ["eye"], c["eye"], 3.0)
	Globals.tint_meshes(_model, c["skin"].darkened(0.4), c["amount"] * 0.6, ["shirt", "pants"])

func _build_hp_bar() -> void:
	_hp_bar = Node3D.new()
	_hp_bar.position = Vector3(0, 2.75, 0)
	var bg := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.3, 0.26, 0.05)
	bg.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.1, 0.1, 0.1, 0.85)
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	bg.material_override = m
	_hp_bar.add_child(bg)
	_hp_fill = MeshInstance3D.new()
	var fm := BoxMesh.new()
	fm.size = Vector3(1.2, 0.18, 0.06)
	_hp_fill.mesh = fm
	var m2 := StandardMaterial3D.new()
	m2.albedo_color = Color(0.9, 0.15, 0.1)
	m2.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_hp_fill.material_override = m2
	_hp_fill.position = Vector3(0, 0, 0.02)
	_hp_bar.add_child(_hp_fill)
	add_child(_hp_bar)

func _process(delta: float) -> void:
	var game = Globals.game
	if game == null:
		return
	_t += delta
	if not alive:
		return
	if not game.is_playing():
		_rig.shamble(_t * 0.4, _phase, _limp, is_brute or is_boss)
		return
	var player: Node3D = game.player
	var dz := global_position.z - player.global_position.z   # negative while ahead of the player
	if is_boss:
		_boss_update(delta, player, dz)
		return
	position.z += speed * delta
	if dz > -aggro_range:
		var dx := player.global_position.x - global_position.x
		var step := minf(absf(dx), lateral_speed * delta)
		position.x += signf(dx) * step
	if dz >= -0.9 and dz <= 1.2 and absf(player.global_position.x - global_position.x) < hit_radius + 0.8:
		_attack(player)
		return
	if dz > 6.0:
		game.unregister_target(self)
		queue_free()
		return
	var stride := speed / 1.6
	_rig.shamble(_t * stride, _phase, _limp, is_brute)
	_groan_timer -= delta
	if _groan_timer <= 0.0 and dz > -30.0:
		_groan_timer = randf_range(3.0, 9.0)
		if is_brute:
			Sfx.play("brute_roar", -8.0, 0.1, 1.0, 1.5)
		else:
			Sfx.play("zombie_groan_%d" % (randi() % 3), -14.0, 0.15, 1.0, 0.4)
	if _hp_bar:
		_hp_bar.look_at(game.camera.global_position, Vector3.UP, true)

func _boss_update(delta: float, player: Node3D, dz: float) -> void:
	# lumbers toward the player, swaying across the road so the squad has to track it
	var sway := sin(_t * 0.55) * 1.7
	position.x = lerpf(position.x, sway, 1.0 - exp(-delta * 1.5))
	if dz < -4.2:
		position.z += speed * delta
		_rig.shamble(_t * 0.5, _phase, 0.3, true)
	else:
		# in reach: pound the squad
		_rig.shamble(_t * 0.9, _phase, 0.3, true)
		_attack_cd -= delta
		if _attack_cd <= 0.0:
			_attack_cd = 1.4
			player.take_damage(contact_damage, global_position)
			Globals.game.camera_shake(0.6)
			FX.ring(get_parent(), Vector3(player.global_position.x, 0.05, player.global_position.z), Color(1, 0.3, 0.2, 0.8), 3.0, 0.3)
			Sfx.play("brute_roar", -3.0, 0.1, 0.7)
	_groan_timer -= delta
	if _groan_timer <= 0.0:
		_groan_timer = randf_range(2.5, 5.0)
		Sfx.play("brute_roar", -4.0, 0.08, 0.6)

func _attack(player: Node3D) -> void:
	player.take_damage(contact_damage, global_position)
	_die(true, false)

func hit(dmg: float, pos: Vector3) -> void:
	if not alive:
		return
	hp -= dmg
	Sfx.play("zombie_hit", -10.0, 0.2, 1.0, 0.03)
	var c: Dictionary = TIER_COLORS[(tier + (1 if is_boss else 0)) % TIER_COLORS.size()]
	var goo: Color = Color(0.35, 0.75, 0.2) if tier == 0 and not is_boss else c["skin"]
	FX.burst(get_parent(), pos, goo, 8, 0.09, 3.5, 0.45, 9.0, 50.0)
	_rig.flash(0.06)
	if not is_boss:
		position.z -= 0.12 if not is_brute else 0.03
	if _hp_fill:
		var f := clampf(hp / max_hp, 0.0, 1.0)
		_hp_fill.scale.x = maxf(f, 0.001)
		_hp_fill.position.x = -(1.0 - f) * 0.6
	if is_boss and Globals.game:
		Globals.game.hud.set_boss_hp(hp, max_hp)
	if hp <= 0.0:
		_die(false, true)

func _die(lunged: bool, give_score: bool) -> void:
	alive = false
	var game = Globals.game
	if game:
		game.unregister_target(self)
		if give_score:
			game.add_score(score_value, global_position + Vector3(0, 1.8, 0))
			game.on_zombie_killed(self)
	var parent := get_parent()
	var c: Dictionary = TIER_COLORS[(tier + (1 if is_boss else 0)) % TIER_COLORS.size()]
	var goo: Color = Color(0.35, 0.75, 0.2) if tier == 0 and not is_boss else c["skin"]
	if is_boss:
		Sfx.play("brute_roar", 0.0, 0.05, 0.5)
		Sfx.play("explosion", -2.0, 0.1, 0.8)
		for i in 4:
			FX.burst(parent, global_position + Vector3(randf_range(-1, 1), 1.5 + i * 0.8, randf_range(-1, 1)), goo, 40, 0.3, 9.0, 1.1, 8.0, 90.0)
		FX.flash(parent, global_position + Vector3(0, 2.5, 0), Color(1.0, 0.5, 0.3), 2.5, 10.0, 0.25)
		FX.ring(parent, global_position, Color(1, 0.4, 0.2, 0.9), 12.0, 0.7)
	else:
		Sfx.play("zombie_die", -8.0 if not is_brute else -4.0, 0.15, 0.7 if is_brute else 1.0)
		if give_score:
			FX.burst(parent, global_position + Vector3(0, 1.0, 0), goo, 22 if not is_brute else 40, 0.14, 6.0, 0.7, 10.0, 70.0)
	if _hp_bar:
		_hp_bar.visible = false
	var tw := create_tween()
	tw.set_parallel(true)
	var tip := 0.5 if lunged else -0.5
	var dur := 0.45 if not is_boss else 1.2
	tw.tween_property(_model, "rotation:x", PI * tip, dur).set_ease(Tween.EASE_IN)
	tw.tween_property(self, "position:z", position.z - (1.2 if not lunged else -0.3), 0.4).set_ease(Tween.EASE_OUT)
	tw.chain().tween_interval(0.5 if not is_boss else 1.5)
	tw.chain().tween_property(self, "position:y", -2.8 if not is_boss else -7.0, 0.7 if not is_boss else 1.5).set_ease(Tween.EASE_IN)
	tw.chain().tween_callback(queue_free)

func configure(difficulty: float, brute: bool, zombie_tier: int = 0) -> void:
	is_brute = brute
	tier = zombie_tier
	var d := difficulty
	var tier_mult := 1.0 + 0.75 * tier
	if brute:
		max_hp = (100.0 + d * 30.0) * tier_mult
		speed = 1.35 + minf(d * 0.1, 0.8) + 0.1 * tier
		contact_damage = 35.0
		score_value = 60
		lateral_speed = 1.2
		aggro_range = 14.0
	else:
		max_hp = (20.0 + d * 7.0) * tier_mult
		speed = randf_range(1.6, 2.3) + minf(d * 0.15, 1.3) + 0.12 * tier
		contact_damage = 15.0
		score_value = 10 + 5 * tier
		lateral_speed = 1.5 + minf(d * 0.1, 0.8)
	hp = max_hp

func configure_boss(zombie_tier: int, boss_hp: float) -> void:
	is_boss = true
	is_brute = true
	tier = zombie_tier
	max_hp = boss_hp
	hp = boss_hp
	speed = 1.5 + 0.1 * zombie_tier
	contact_damage = 20.0 + 4.0 * zombie_tier
	score_value = 500 + 250 * zombie_tier
	aggro_range = 0.0
