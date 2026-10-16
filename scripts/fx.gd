class_name FX
extends RefCounted
## Static helpers for juicy one-shot effects: particle bursts, floating text, flashes.

static func _particle_mat(color: Color, speed: float, spread: float, gravity: float, scale_min: float, scale_max: float, up_bias: float = 0.5) -> ParticleProcessMaterial:
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, up_bias, 1.0 - up_bias)
	pm.spread = spread
	pm.initial_velocity_min = speed * 0.5
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -gravity, 0)
	pm.scale_min = scale_min
	pm.scale_max = scale_max
	pm.damping_min = 1.0
	pm.damping_max = 3.0
	pm.color = color
	pm.angular_velocity_min = -180
	pm.angular_velocity_max = 180
	var curve := Curve.new()
	curve.add_point(Vector2(0, 1))
	curve.add_point(Vector2(0.7, 0.9))
	curve.add_point(Vector2(1, 0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	return pm

static func burst(parent: Node, pos: Vector3, color: Color, count: int = 16, size: float = 0.12, speed: float = 5.0, lifetime: float = 0.6, gravity: float = 9.0, spread: float = 60.0, emissive: bool = false) -> void:
	var p := GPUParticles3D.new()
	p.one_shot = true
	p.emitting = false
	p.amount = count
	p.lifetime = lifetime
	p.explosiveness = 1.0
	p.randomness = 0.4
	p.local_coords = false
	p.process_material = _particle_mat(color, speed, spread, gravity, size * 0.6, size * 1.4)
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.vertex_color_use_as_albedo = true
	m.roughness = 0.8
	if emissive:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 2.0
	mesh.material = m
	p.draw_pass_1 = mesh
	p.position = pos
	parent.add_child(p)
	p.emitting = true
	var tree := parent.get_tree()
	if tree:
		tree.create_timer(lifetime + 0.3).timeout.connect(p.queue_free)

## Floating 3D text (e.g. damage numbers / "+25").
static func popup(parent: Node, pos: Vector3, text: String, color: Color = Color.WHITE, size: int = 96, rise: float = 1.2, time: float = 0.8) -> void:
	var l := Label3D.new()
	l.text = text
	l.font = Globals.font("bold")
	l.font_size = size
	# keep the on-screen size roughly constant: scale with distance to the camera
	var dist := 12.0
	if Globals.game and Globals.game.camera:
		if Globals.game.camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
			dist = Globals.game.camera.size * 0.45
		else:
			dist = clampf(Globals.game.camera.global_position.distance_to(pos), 4.0, 60.0)
	l.pixel_size = 0.0045 * (dist / 12.0)
	l.outline_size = int(size * 0.18)
	l.outline_modulate = Color(0, 0, 0, 0.85)
	l.modulate = color
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = pos
	parent.add_child(l)
	var tw := parent.create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "position:y", pos.y + rise, time).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "scale", Vector3.ONE * 1.25, 0.12).set_ease(Tween.EASE_OUT)
	tw.chain().tween_property(l, "modulate:a", 0.0, time * 0.4)
	tw.chain().tween_callback(l.queue_free)

## A short-lived glowing sphere + omni light (muzzle flash, impact flash).
static func flash(parent: Node, pos: Vector3, color: Color, radius: float = 0.25, light_energy: float = 4.0, time: float = 0.07) -> void:
	var n := Node3D.new()
	n.position = pos
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	sm.radial_segments = 10
	sm.rings = 6
	mi.mesh = sm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = 4.0
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	n.add_child(mi)
	var light := OmniLight3D.new()
	light.light_color = color
	light.light_energy = light_energy
	light.omni_range = 4.0
	light.shadow_enabled = false
	n.add_child(light)
	parent.add_child(n)
	var tw := parent.create_tween()
	tw.tween_property(n, "scale", Vector3.ONE * 0.2, time)
	tw.tween_callback(n.queue_free)

## Ring shockwave on the ground.
static func ring(parent: Node, pos: Vector3, color: Color, max_radius: float = 3.0, time: float = 0.4) -> void:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.9
	tm.outer_radius = 1.0
	tm.rings = 24
	tm.ring_segments = 6
	mi.mesh = tm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = m
	mi.position = pos + Vector3(0, 0.05, 0)
	mi.scale = Vector3.ONE * 0.2
	parent.add_child(mi)
	var tw := parent.create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3(max_radius, 1.0, max_radius), time).set_ease(Tween.EASE_OUT)
	tw.tween_property(m, "albedo_color:a", 0.0, time)
	tw.chain().tween_callback(mi.queue_free)
