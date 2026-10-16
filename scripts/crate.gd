class_name Crate
extends Node3D
## Upgrade gate: a wide barricade filling most of the lane, with a shot counter on its front panel.
## Each bullet hit decrements it; at 0 it bursts into a power-up.

const REWARD_INFO := {
	"soldier": {"label": "+1 SOLDIER", "color": Color(0.4, 0.9, 1.0)},
	"weapon": {"label": "NEW WEAPON", "color": Color(1.0, 0.4, 0.3)},
	"fire_rate": {"label": "FIRE RATE+", "color": Color(1.0, 0.7, 0.2)},
	"launcher": {"label": "LAUNCHER", "color": Color(1.0, 0.55, 0.1)},
	"heal": {"label": "+40 HP", "color": Color(0.4, 1.0, 0.45)},
	"shield": {"label": "SHIELD", "color": Color(0.5, 0.75, 1.0)},
	"nuke": {"label": "NUKE", "color": Color(1.0, 0.3, 0.1)},
}

var alive := true
var hit_radius := 1.7
var count := 10
var reward := "fire_rate"

var _model: Node3D
var _number: Label3D
var _title: Label3D
var _punch := 0.0
var _t := randf() * TAU

func _ready() -> void:
	_model = Globals.model("gate")
	add_child(_model)
	_number = Label3D.new()
	_number.font = Globals.font("bold")
	_number.font_size = 220
	_number.pixel_size = 0.005
	_number.outline_size = 44
	_number.outline_modulate = Color(0.05, 0.05, 0.05)
	_number.position = Vector3(0, 1.05, 0.55)
	# tilt the number toward the high-angle camera so it is not foreshortened
	if Globals.game and Globals.game.camera and Globals.game.camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		_number.rotation.x = -deg_to_rad(Globals.game.CAM_PITCH_DEG)
	_number.no_depth_test = true
	_number.render_priority = 1
	add_child(_number)
	_title = Label3D.new()
	_title.font = Globals.font("bold")
	_title.font_size = 84
	_title.pixel_size = 0.0085
	_title.outline_size = 20
	_title.outline_modulate = Color(0, 0, 0, 0.9)
	_title.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_title.position = Vector3(0, 2.4, 0)
	_title.no_depth_test = true
	add_child(_title)
	_refresh()

func configure(shots: int, reward_kind: String) -> void:
	count = shots
	reward = reward_kind
	if is_inside_tree():
		_refresh()

func _refresh() -> void:
	_number.text = str(count)
	var info: Dictionary = REWARD_INFO.get(reward, REWARD_INFO["fire_rate"])
	var label: String = info["label"]
	var game = Globals.game
	if game and game.player:
		if reward == "weapon":
			label = str(Weapons.tier(game.player.weapon_tier + 1)["name"])
		elif reward == "soldier":
			label = "+1 SOLDIER (x%d)" % (game.player.squad_size + 1)
	_title.text = label
	_title.modulate = info["color"]
	_number.modulate = Color.WHITE.lerp(info["color"], 0.3)

func _process(delta: float) -> void:
	_t += delta
	_punch = lerpf(_punch, 0.0, 1.0 - exp(-delta * 14.0))
	_model.scale = Vector3.ONE * (1.0 + _punch * 0.1)
	_title.position.y = 2.4 + sin(_t * 2.5) * 0.06
	var game = Globals.game
	if game == null or not game.is_playing():
		return
	if alive and global_position.z > game.player.global_position.z + 3.0:
		game.unregister_target(self)
		queue_free()

func hit(_dmg: float, pos: Vector3) -> void:
	if not alive:
		return
	count -= 1
	_punch = 1.0
	Sfx.play("crate_hit", -9.0, 0.15, 1.0, 0.03)
	FX.burst(get_parent(), pos, Color(0.55, 0.42, 0.22), 6, 0.07, 3.0, 0.4, 8.0, 45.0)
	if count <= 0:
		count = 0
		_refresh()
		_break()
	else:
		_refresh()

func _break() -> void:
	alive = false
	var game = Globals.game
	if game:
		game.unregister_target(self)
	Sfx.play("crate_break", -4.0, 0.1)
	var parent := get_parent()
	var c := global_position + Vector3(0, 0.7, 0)
	FX.burst(parent, c, Color(0.5, 0.4, 0.2), 34, 0.18, 7.0, 0.9, 10.0, 85.0)
	FX.burst(parent, c, Color(0.3, 0.35, 0.2), 18, 0.14, 5.0, 0.9, 10.0, 85.0)
	FX.flash(parent, c, Color(1.0, 0.9, 0.5), 0.9, 6.0, 0.12)
	FX.ring(parent, global_position, REWARD_INFO.get(reward, REWARD_INFO["fire_rate"])["color"], 3.0, 0.4)
	if game:
		game.add_score(25, global_position + Vector3(0, 1.6, 0))
		game.spawn_powerup(c, reward)
	queue_free()
