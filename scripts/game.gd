extends Node3D
## Main game controller: builds the scene, runs the state machine, spawns enemies/gates, bosses, scoring, autopilot.

enum State { MENU, PLAYING, GAME_OVER }

# Camera: high-angle orthographic "isometric" view down the road. Set ORTHO=false for the old perspective cam.
const CAM_ORTHO := true
const CAM_PITCH_DEG := 48.0
const CAM_YAW_DEG := 0.0
const CAM_SIZE := 21.0
const CAM_DIST := 45.0
const CAM_LOOK := Vector3(0, 0.0, -8.0)
const CAM_OFFSET_PERSP := Vector3(0, 4.1, 5.0)
const CAM_LOOK_PERSP := Vector3(0, 0.9, -7.0)

var state: State = State.MENU
var player: Player
var world: World
var camera: Camera3D
var camera_rig: Node3D
var hud: HUD
var entities: Node3D
var targets: Array = []
var sun: DirectionalLight3D

var score := 0
var distance := 0.0
var kills := 0
var crates_cleared := 0
var difficulty := 0.0
var tier := 0                 # increases after every boss: horde recolours and toughens
var kills_since_boss := 0
var next_boss_kills := 28
var boss: Zombie = null
var boss_active := false
var _boss_minion_t := 0.0
var _start_z := 0.0
var _trauma := 0.0
var _shake_t := 0.0
var _noise := FastNoiseLite.new()
var _death_time := 0.0
var _rng := RandomNumberGenerator.new()
var _run_t := 0.0
var _last_milestone := 0
var _speed_target := 1.0
var _cam_base := Vector3.ZERO

# autopilot
var _ap_timer := 0.0
var _shot_timer := 0.0
var _shot_idx := 0
var _total_t := 0.0
var _ap_runs := 0

func _ready() -> void:
	Globals.game = self
	_rng.randomize()
	_noise.seed = 1337
	_noise.frequency = 1.5
	_build_environment()
	entities = Node3D.new()
	entities.name = "Entities"
	add_child(entities)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	player.setup(entities)
	player.hp_changed.connect(func(hp, mx): hud.set_hp(hp, mx))
	player.stats_changed.connect(func(): hud.set_stats(player))
	player.died.connect(_on_player_died)
	world = World.new()
	world.name = "World"
	add_child(world)
	_build_camera()
	hud = HUD.new()
	hud.name = "HUD"
	add_child(hud)
	_enter_menu()

func is_playing() -> bool:
	return state == State.PLAYING

# ------------------------------------------------------------------ scene setup
func _build_environment() -> void:
	var env := Environment.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.25, 0.42, 0.75)
	sky_mat.sky_horizon_color = Color(0.93, 0.72, 0.55)
	sky_mat.ground_bottom_color = Color(0.25, 0.2, 0.18)
	sky_mat.ground_horizon_color = Color(0.85, 0.65, 0.5)
	sky_mat.sun_angle_max = 25.0
	sky_mat.sun_curve = 0.1
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.ambient_light_energy = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.tonemap_white = 1.0
	env.ssao_enabled = true
	env.ssao_radius = 1.5
	env.ssao_intensity = 2.5
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.fog_enabled = true
	env.fog_light_color = Color(0.86, 0.72, 0.6)
	env.fog_density = 0.006 if CAM_ORTHO else 0.012
	env.fog_sky_affect = 0.25
	env.fog_aerial_perspective = 0.6
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.06
	env.adjustment_saturation = 1.15
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	sun = DirectionalLight3D.new()
	sun.light_color = Color(1.0, 0.92, 0.8)
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 110.0
	sun.directional_shadow_split_1 = 0.1
	sun.directional_shadow_split_2 = 0.25
	sun.directional_shadow_split_3 = 0.5
	sun.directional_shadow_fade_start = 0.9
	sun.shadow_bias = 0.03
	sun.shadow_normal_bias = 1.5
	sun.rotation_degrees = Vector3(-62.0, 160.0, 0.0)
	add_child(sun)

func _build_camera() -> void:
	camera_rig = Node3D.new()
	camera_rig.name = "CameraRig"
	add_child(camera_rig)
	camera = Camera3D.new()
	camera.near = 0.3
	camera.far = 400.0
	camera_rig.add_child(camera)
	if CAM_ORTHO:
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = CAM_SIZE
		var pitch := deg_to_rad(CAM_PITCH_DEG)
		var yaw := deg_to_rad(CAM_YAW_DEG)
		var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
		_cam_base = CAM_LOOK + dir * CAM_DIST
		camera.position = _cam_base
		camera.look_at_from_position(_cam_base, CAM_LOOK, Vector3.UP)
	else:
		camera.fov = 62.0
		_cam_base = CAM_OFFSET_PERSP
		camera.position = _cam_base
		camera.look_at_from_position(_cam_base, CAM_LOOK_PERSP, Vector3.UP)
	camera.current = true

# ------------------------------------------------------------------ state machine
func _enter_menu() -> void:
	state = State.MENU
	_reset_world()
	hud.show_menu(Globals.best_score, Globals.best_distance)
	Sfx.play_music("menu_loop")

func _reset_world() -> void:
	for t in targets:
		if is_instance_valid(t):
			t.queue_free()
	targets.clear()
	for c in entities.get_children():
		c.queue_free()
	boss = null
	boss_active = false
	tier = 0
	kills_since_boss = 0
	next_boss_kills = 28
	player.position = Vector3.ZERO
	player.reset_run()
	score = 0
	distance = 0.0
	kills = 0
	crates_cleared = 0
	difficulty = 0.0
	_start_z = 0.0
	_run_t = 0.0
	_last_milestone = 0
	_speed_target = 1.0
	world.reset()
	hud.set_score(0)
	hud.set_distance(0)
	hud.set_tier(0)
	hud.hide_boss()
	hud.set_stats(player)
	hud.set_timers(player)
	_update_camera(1.0, true)

func start_run() -> void:
	if state == State.PLAYING:
		return
	_reset_world()
	state = State.PLAYING
	player.running = true
	hud.show_playing()
	Sfx.play("tap_start", -4.0, 0.0)
	Sfx.play_music("music_loop")

func _on_player_died() -> void:
	state = State.GAME_OVER
	_death_time = Time.get_ticks_msec() / 1000.0
	_ap_timer = 0.0
	camera_shake(1.0)
	Sfx.stop_music()
	Sfx.play("game_over", -2.0, 0.0)
	Globals.runs += 1
	var new_best := score > Globals.best_score
	if new_best:
		Globals.best_score = score
	Globals.best_distance = maxi(Globals.best_distance, int(distance))
	Globals.save()
	hud.show_game_over(score, int(distance), kills, crates_cleared, tier, Globals.best_score, new_best)
	print("[run] score=%d distance=%dm kills=%d gates=%d tier=%d difficulty=%.2f squad=%d weapon=%d rate=%.1f" % [score, int(distance), kills, crates_cleared, tier, difficulty, player.squad_size, player.weapon_tier, player.fire_rate])

func _retry() -> void:
	start_run()

# ------------------------------------------------------------------ frame loop
func _process(delta: float) -> void:
	_total_t += delta
	if Globals.autopilot:
		_autopilot(delta)
	else:
		if state == State.PLAYING:
			player.input_axis = Input.get_axis("move_left", "move_right")
	if state == State.PLAYING:
		_run_t += delta
		_speed_target = 0.0 if boss_active else 1.0
		var ramp := clampf(_run_t / 1.2, 0.15, 1.0)
		player.speed_scale = lerpf(player.speed_scale, _speed_target * ramp, 1.0 - exp(-delta * 3.0))
		distance = _start_z - player.position.z
		difficulty = maxf(0.0, (distance - 25.0) / 100.0)
		var milestone := int(distance / 100.0)
		if milestone > _last_milestone:
			_last_milestone = milestone
			hud.show_popup("%d m" % (milestone * 100), Color(1, 1, 1))
			Sfx.play("tap_start", -6.0, 0.0)
		world.update_streaming(player.position.z)
		hud.set_distance(distance)
		hud.set_timers(player)
		_check_boss(delta)
	_update_camera(delta, false)

func _update_camera(delta: float, snap: bool) -> void:
	var target := Vector3(player.position.x * (0.3 if CAM_ORTHO else 0.45), 0.0, player.position.z)
	if snap:
		camera_rig.position = target
	else:
		camera_rig.position.z = target.z
		camera_rig.position.x = lerpf(camera_rig.position.x, target.x, 1.0 - exp(-delta * 6.0))
	_trauma = maxf(0.0, _trauma - delta * 1.8)
	_shake_t += delta * 40.0
	var s := _trauma * _trauma
	var ox := _noise.get_noise_2d(_shake_t, 0.0) * 0.45 * s
	var oy := _noise.get_noise_2d(0.0, _shake_t) * 0.3 * s
	var rz := _noise.get_noise_2d(_shake_t, 100.0) * 0.025 * s
	camera.position = _cam_base + Vector3(ox, oy, 0)
	camera.rotation.z = rz
	if state == State.PLAYING and not CAM_ORTHO:
		camera.position.y += sin(_run_t * 7.5) * 0.03 * player.speed_scale

func camera_shake(amount: float) -> void:
	_trauma = minf(1.0, _trauma + amount)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("mute"):
		Sfx.toggle_mute()
		hud._update_mute()
	if event is InputEventScreenTouch and event.pressed:
		_tap()
	elif event.is_action_pressed("confirm"):
		_tap()
	elif event is InputEventScreenDrag and state == State.PLAYING:
		var vp_w := float(get_viewport().get_visible_rect().size.x)
		player.drag_dx += event.relative.x * (Globals.ROAD_HALF_WIDTH * 2.0 / vp_w) * 1.6

func _tap() -> void:
	match state:
		State.MENU:
			start_run()
		State.GAME_OVER:
			if Time.get_ticks_msec() / 1000.0 - _death_time > 0.8:
				_retry()

# ------------------------------------------------------------------ spawning
func register_target(t: Node) -> void:
	targets.append(t)

func unregister_target(t: Node) -> void:
	targets.erase(t)

## Called by World for every new 20 m chunk. near_z > far_z (we run toward -Z). Both lanes get zombies;
## the right lane also gets an upgrade gate.
func populate_chunk(near_z: float, far_z: float, chunk_index: int) -> void:
	var d := difficulty
	var zombie_x := Globals.LANE_ZOMBIE_X
	var bonus_x := Globals.LANE_BONUS_X
	var n := clampi(int(3.0 + d * 1.3 + _rng.randf() * 2.0), 2, 12)
	var brute_chance := 0.0 if d < 0.7 else clampf(0.08 + d * 0.04, 0.0, 0.35)
	for i in n:
		var z := _rng.randf_range(far_z + 1.0, near_z - 1.0)
		var brute := _rng.randf() < brute_chance
		var lane_x := zombie_x if _rng.randf() < 0.6 else bonus_x
		_spawn_zombie(Vector3(lane_x + _rng.randf_range(-0.9, 0.9), 0, z), brute, d)
	if chunk_index % 5 == 0 and d > 0.5:
		var z := _rng.randf_range(far_z + 2.0, near_z - 6.0)
		for i in 4:
			_spawn_zombie(Vector3(zombie_x + _rng.randf_range(-1.0, 1.0), 0, z - i * 1.3), false, d)
	if _rng.randf() < 0.9:
		var z := _rng.randf_range(far_z + 3.0, near_z - 3.0)
		_spawn_gate(Vector3(bonus_x, 0, z), d)

func _spawn_zombie(pos: Vector3, brute: bool, d: float) -> Zombie:
	var z := Zombie.new()
	z.configure(d, brute, tier)
	entities.add_child(z)
	z.position = pos
	register_target(z)
	return z

func _pick_reward() -> String:
	var p := player
	var w := {
		"soldier": 3.0 if p.squad_size < Player.MAX_SQUAD else 0.0,
		"weapon": 2.6 if p.weapon_tier < Weapons.MAX_TIER else 0.0,
		"fire_rate": 2.6 if p.fire_rate < Player.MAX_FIRE_RATE else 0.0,
		"launcher": 1.4 if not p.is_launcher() else 0.0,
		"heal": 1.0 + (2.5 if p.hp < p.max_hp * 0.5 else 0.0),
		"shield": 1.0,
		"nuke": 0.5 + difficulty * 0.15,
	}
	var total := 0.0
	for k in w:
		total += w[k]
	var r := _rng.randf() * total
	for k in w:
		r -= w[k]
		if r <= 0.0:
			return k
	return "fire_rate"

func _spawn_gate(pos: Vector3, d: float) -> void:
	var c := Crate.new()
	var reward := _pick_reward()
	# shots the squad could land while the gate is on screen (~6 s), then take a slice of that
	var budget := player.shots_per_second() * 6.0
	var frac := _rng.randf_range(0.3, 0.6)
	match reward:
		"soldier", "weapon":
			frac += 0.15
		"heal", "shield":
			frac -= 0.1
	var shots := clampi(int(round(budget * frac * (1.0 + d * 0.05))), 4, 150)
	c.configure(shots, reward)
	entities.add_child(c)
	c.position = pos
	register_target(c)

func spawn_powerup(pos: Vector3, kind: String) -> void:
	var p := Powerup.new()
	p.kind = kind
	entities.add_child(p)
	p.global_position = pos
	crates_cleared += 1

# ------------------------------------------------------------------ boss encounters
func _check_boss(delta: float) -> void:
	if boss_active:
		if boss == null or not is_instance_valid(boss):
			_end_boss()
			return
		_boss_minion_t -= delta
		if _boss_minion_t <= 0.0:
			_boss_minion_t = 4.0
			for i in 2:
				var lane_x: float = Globals.LANE_ZOMBIE_X if _rng.randf() < 0.5 else Globals.LANE_BONUS_X
				_spawn_zombie(Vector3(lane_x + _rng.randf_range(-0.8, 0.8), 0, player.position.z - 27.0 + _rng.randf_range(-3, 3)), false, difficulty)
		return
	if kills_since_boss >= next_boss_kills:
		_start_boss()

func _start_boss() -> void:
	boss_active = true
	_boss_minion_t = 3.0
	var b := Zombie.new()
	# boss HP ≈ what the squad can deal in ~16 s (+ per tier), so upgrades matter
	var boss_hp := maxf(500.0, player.dps() * (15.0 + 3.0 * tier)) * (1.0 + 0.1 * tier)
	b.configure_boss(tier, boss_hp)
	entities.add_child(b)
	b.position = Vector3(0, 0, player.position.z - 29.0)
	register_target(b)
	boss = b
	hud.show_boss("TIER %d BOSS" % (tier + 1))
	hud.set_boss_hp(boss_hp, boss_hp)
	hud.show_popup("BOSS INCOMING!", Color(1, 0.3, 0.25))
	Sfx.play("boss_alarm", -3.0, 0.0)
	Sfx.play("brute_roar", -2.0, 0.05, 0.55)
	camera_shake(0.6)

func _end_boss() -> void:
	boss_active = false
	boss = null
	kills_since_boss = 0
	tier += 1
	next_boss_kills = 28 + 14 * tier
	hud.hide_boss()
	hud.set_tier(tier)
	var tier_name: String = Zombie.TIER_COLORS[tier % Zombie.TIER_COLORS.size()]["name"]
	hud.show_popup("TIER %d  •  %s HORDE" % [tier + 1, tier_name], Zombie.TIER_COLORS[tier % Zombie.TIER_COLORS.size()]["skin"].lightened(0.3))
	player.heal(25.0)
	Sfx.play("powerup", 0.0, 0.0)

# ------------------------------------------------------------------ events
func add_score(points: int, pos: Vector3) -> void:
	if state != State.PLAYING:
		return
	score += points
	hud.set_score(score)
	FX.popup(entities, pos, "+%d" % points, Color(1, 0.92, 0.4), 80, 1.0, 0.7)

func on_zombie_killed(z: Node) -> void:
	kills += 1
	if z.is_boss:
		camera_shake(1.0)
		_end_boss()
		return
	kills_since_boss += 1
	camera_shake(0.12 if not z.is_brute else 0.4)

func on_powerup(kind: String, label: String) -> void:
	var info: Dictionary = Crate.REWARD_INFO.get(kind, {})
	var color: Color = info.get("color", Color(1, 0.9, 0.3))
	hud.show_popup(label, color)
	FX.ring(entities, player.global_position, color, 3.0, 0.45)
	match kind:
		"nuke":
			Sfx.play("nuke", 0.0, 0.05)
			camera_shake(0.9)
			FX.ring(entities, player.global_position, Color(1, 0.6, 0.2), 20.0, 0.8)
			for t in targets.duplicate():
				if is_instance_valid(t) and t is Zombie and t.alive and not t.is_boss and t.global_position.z > player.global_position.z - 70.0:
					t.hit(99999.0, t.global_position + Vector3(0, 1, 0))
			if boss and is_instance_valid(boss) and boss.alive:
				boss.hit(boss.max_hp * 0.15, boss.global_position + Vector3(0, 2, 0))
		"heal":
			Sfx.play("heal", -2.0, 0.0)
		"shield":
			Sfx.play("shield_on", -2.0, 0.0)
		"launcher":
			Sfx.play("launcher", -2.0, 0.0)
			Sfx.play("powerup", -4.0, 0.02)
		_:
			Sfx.play("powerup", -2.0, 0.02)
	hud.set_stats(player)

# ------------------------------------------------------------------ autopilot (automated playtest + screenshots)
func _autopilot(delta: float) -> void:
	_ap_timer += delta
	_shot_timer += delta
	if Globals.duration > 0.0 and _total_t >= Globals.duration:
		print("[autopilot] done: runs=%d" % _ap_runs)
		get_tree().quit()
		return
	if Globals.shots_dir != "" and _shot_timer >= Globals.shot_interval:
		_shot_timer = 0.0
		_screenshot()
	match state:
		State.MENU:
			if _ap_timer > 1.0:
				_ap_timer = 0.0
				_ap_runs += 1
				if Globals.shots_dir != "":
					_screenshot()
				start_run()
		State.GAME_OVER:
			if _ap_timer > 2.0:
				_ap_timer = 0.0
				_ap_runs += 1
				if Globals.shots_dir != "":
					_screenshot()
				_retry()
		State.PLAYING:
			_bot_steer()

func _bot_steer() -> void:
	var pz := player.position.z
	var best_z: Node = null
	var best_c: Node = null
	for t in targets:
		if not is_instance_valid(t) or not t.alive:
			continue
		var dz: float = pz - t.global_position.z    # positive when ahead
		if dz < -0.5:
			continue
		if t is Zombie and dz < 22.0 and (best_z == null or dz < pz - (best_z as Node3D).global_position.z):
			best_z = t
		if t is Crate and dz < 45.0 and (best_c == null or dz < pz - (best_c as Node3D).global_position.z):
			best_c = t
	var target_x := 0.0
	var dz_z: float = 999.0 if best_z == null else pz - (best_z as Node3D).global_position.z
	# a "decent player" heuristic: shoot zombies that are close, otherwise invest in the nearest gate
	var gate_dz: float = 999.0 if best_c == null else pz - (best_c as Node3D).global_position.z
	var danger := dz_z < (7.0 if player.hp > 50.0 else 13.0)
	if boss_active and boss and is_instance_valid(boss) and boss.alive and (best_z == null or dz_z > 8.0):
		target_x = boss.global_position.x
	elif best_z != null and (danger or best_c == null or gate_dz > 34.0):
		target_x = (best_z as Node3D).global_position.x
	elif best_c != null:
		target_x = (best_c as Node3D).global_position.x
	var diff := target_x - player.position.x
	player.input_axis = clampf(diff * 2.5, -1.0, 1.0) if absf(diff) > 0.08 else 0.0

func _screenshot() -> void:
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	DirAccess.make_dir_recursive_absolute(Globals.shots_dir)
	var path := "%s/shot_%03d.png" % [Globals.shots_dir, _shot_idx]
	_shot_idx += 1
	var err := img.save_png(path)
	print("[autopilot] screenshot %s (%s) state=%d score=%d dist=%dm hp=%d fps=%d targets=%d tier=%d boss=%s squad=%d weapon=%d rate=%.1f" % [path, error_string(err), state, score, int(distance), int(player.hp), int(Engine.get_frames_per_second()), targets.size(), tier, str(boss_active), player.squad_size, player.weapon_tier, player.fire_rate])
