class_name Powerup
extends Node3D
## Golden pickup that pops out of a cleared crate and homes in on the player.

var kind := "fire_rate"
var _model: Node3D
var _t := 0.0
var _state := 0   # 0 pop, 1 fly, 2 done
var _vel := Vector3.ZERO
var _light: OmniLight3D

func _ready() -> void:
	_model = Globals.model("powerup")
	add_child(_model)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.85, 0.3)
	_light.light_energy = 2.0
	_light.omni_range = 4.0
	_light.position = Vector3(0, 0.6, 0)
	_light.shadow_enabled = false
	add_child(_light)
	_vel = Vector3(randf_range(-1.0, 1.0), 5.5, 1.5)
	scale = Vector3.ONE * 0.2
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3.ONE * 1.3, 0.25).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)

func _process(delta: float) -> void:
	_t += delta
	_model.rotation.y += delta * 5.0
	var game = Globals.game
	if game == null:
		return
	var player: Node3D = game.player
	var target: Vector3 = player.global_position + Vector3(0, 1.1, 0)
	match _state:
		0:
			_vel.y -= 12.0 * delta
			global_position += _vel * delta
			if _t > 0.45:
				_state = 1
		1:
			var to := target - global_position
			var d := to.length()
			var spd := 14.0 + _t * 20.0
			if d < spd * delta + 0.3:
				_collect(player)
				return
			global_position += to.normalized() * spd * delta
		_:
			pass

func _collect(player: Node) -> void:
	_state = 2
	var label: String = player.apply_powerup(kind)
	var game = Globals.game
	if game:
		game.on_powerup(kind, label)
	queue_free()
