class_name Weapons
extends RefCounted
## Weapon tiers (damage upgrades = a new gun with new ammunition) + the timed splash launcher.

const TIERS := [
	{"id": "rifle", "name": "RIFLE", "model": "weapon_rifle", "damage": 10.0, "speed": 48.0, "pierce": 0,
		"color": Color(1.0, 0.85, 0.35), "emission": Color(1.0, 0.7, 0.2), "size": Vector2(0.07, 1.0), "sfx": "gunshot", "sfx_db": -8.0,
		"flash": Color(1.0, 0.8, 0.4), "tint": Color(0.2, 0.2, 0.22), "scale": 1.0},
	{"id": "assault", "name": "ASSAULT RIFLE", "model": "weapon_assault", "damage": 17.0, "speed": 50.0, "pierce": 0,
		"color": Color(1.0, 0.55, 0.15), "emission": Color(1.0, 0.4, 0.1), "size": Vector2(0.095, 1.25), "sfx": "gunshot_heavy", "sfx_db": -7.0,
		"flash": Color(1.0, 0.6, 0.3), "tint": Color(0.55, 0.2, 0.08), "scale": 1.1},
	{"id": "plasma", "name": "PLASMA RIFLE", "model": "weapon_plasma", "damage": 27.0, "speed": 42.0, "pierce": 0,
		"color": Color(0.45, 0.95, 1.0), "emission": Color(0.2, 0.8, 1.0), "size": Vector2(0.15, 0.85), "sfx": "plasma", "sfx_db": -6.0,
		"flash": Color(0.4, 0.9, 1.0), "tint": Color(0.1, 0.6, 0.8), "scale": 1.2},
	{"id": "rail", "name": "RAILGUN", "model": "weapon_rail", "damage": 42.0, "speed": 75.0, "pierce": 2,
		"color": Color(0.85, 0.5, 1.0), "emission": Color(0.7, 0.3, 1.0), "size": Vector2(0.08, 2.6), "sfx": "rail", "sfx_db": -5.0,
		"flash": Color(0.8, 0.5, 1.0), "tint": Color(0.45, 0.15, 0.7), "scale": 1.3},
]

const LAUNCHER := {"id": "launcher", "name": "LAUNCHER", "model": "weapon_launcher", "damage_mult": 3.2, "rate_mult": 0.28,
	"splash": 2.9, "speed": 30.0, "color": Color(0.35, 0.35, 0.35), "emission": Color(1.0, 0.45, 0.1), "size": Vector2(0.16, 0.75),
	"sfx": "launcher", "sfx_db": -4.0, "flash": Color(1.0, 0.6, 0.2), "tint": Color(0.2, 0.3, 0.12), "scale": 1.2}

const MAX_TIER := 3

static func tier(i: int) -> Dictionary:
	return TIERS[clampi(i, 0, MAX_TIER)]

## Replace the soldier's built-in rifle with the weapon model for `w` (a TIERS entry or LAUNCHER).
## Returns the muzzle node to fire from. Falls back to tinting the built-in gun when the model is missing.
static func attach(soldier_model: Node3D, w: Dictionary) -> Dictionary:
	var gun := Globals.find_node(soldier_model, "Gun") as Node3D
	if gun == null:
		return {"root": null, "muzzle": null}
	# remove a previously attached weapon
	var old := gun.get_parent().get_node_or_null("Weapon")
	if old:
		old.queue_free()
		old.name = "WeaponOld"
	var path := "res://assets/models/%s.glb" % w["model"]
	if ResourceLoader.exists(path):
		var inst := Globals.model(w["model"])
		inst.name = "Weapon"
		inst.transform = gun.transform
		inst.scale = Vector3.ONE * float(w["scale"])
		gun.get_parent().add_child(inst)
		gun.visible = false
		_glow_materials(inst)
		return {"root": inst, "muzzle": Globals.find_node(inst, "Muzzle")}
	# fallback: keep the stock rifle, tint it and scale it a bit
	gun.visible = true
	Globals.tint_meshes(gun, w["tint"], 0.7, [], w["emission"], 0.6 if w["id"] != "rifle" else 0.0)
	gun.scale = Vector3.ONE * float(w["scale"])
	return {"root": gun, "muzzle": Globals.find_node(gun, "Muzzle")}

static func _glow_materials(root: Node) -> void:
	for mi in Globals.all_mesh_instances(root):
		var mesh: Mesh = mi.mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var src := mesh.surface_get_material(i)
			if src is BaseMaterial3D and String(src.resource_name).begins_with("MAT_glow"):
				var m: StandardMaterial3D = src.duplicate()
				m.emission_enabled = true
				m.emission = m.albedo_color
				m.emission_energy_multiplier = 3.5
				mi.set_surface_override_material(i, m)
