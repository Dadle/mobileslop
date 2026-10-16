class_name World
extends Node3D
## Streams road segments + side props ahead of the player and asks the game to populate each new chunk.

const SEGMENT_COUNT := 9
const BUILDINGS := ["building_a", "building_b", "building_c"]
const SIDEWALK_PROPS := ["barrier", "sandbag", "car_wreck", "tree_dead", "barrier", "sandbag"]

var segments: Array[Node3D] = []
var _frontier_z := 0.0       # far (most negative) end of the streamed road
var _seg_len := Globals.SEGMENT_LENGTH
var _rng := RandomNumberGenerator.new()
var _spawned_chunks := 0

func _ready() -> void:
	_build()

func _build() -> void:
	for s in segments:
		remove_child(s)
		s.queue_free()
	segments.clear()
	_rng.seed = randi()
	# one segment behind the player (near end at +20), the rest ahead
	var z := _seg_len
	for i in SEGMENT_COUNT:
		var seg := _make_segment()
		add_child(seg)
		_place_segment(seg, z, i >= 2)   # first two segments (behind + first ahead) get no enemies
		z -= _seg_len
	_frontier_z = z + _seg_len   # near z of the next segment to place

func reset() -> void:
	_spawned_chunks = 0
	_build()

func _make_segment() -> Node3D:
	var seg := Node3D.new()
	segments.append(seg)
	var road := Globals.model("road_segment")
	road.name = "Road"
	seg.add_child(road)
	var props := Node3D.new()
	props.name = "Props"
	seg.add_child(props)
	return seg

## near_z is the segment's +Z edge; the segment extends to near_z - 20.
func _place_segment(seg: Node3D, near_z: float, populate: bool) -> void:
	seg.position = Vector3(0, 0, near_z)
	seg.set_meta("near_z", near_z)
	_decorate(seg)
	if populate and Globals.game:
		_spawned_chunks += 1
		Globals.game.populate_chunk(near_z, near_z - _seg_len, _spawned_chunks)

func _decorate(seg: Node3D) -> void:
	var props: Node3D = seg.get_node("Props")
	for c in props.get_children():
		c.queue_free()
	# buildings: two per side, inner row and a taller outer row for skyline depth
	for side: float in [-1.0, 1.0]:
		for slot: int in [0, 1]:
			var zc := -4.0 - 10.0 * slot + _rng.randf_range(-0.6, 0.6)
			var b := Globals.model(BUILDINGS[_rng.randi() % BUILDINGS.size()])
			b.position = Vector3(side * (10.2 + _rng.randf_range(0.0, 1.5)), 0, zc)
			b.rotation.y = (PI * 0.5) * float(_rng.randi() % 4)
			props.add_child(b)
			var b2 := Globals.model(BUILDINGS[_rng.randi() % BUILDINGS.size()])
			b2.position = Vector3(side * (19.0 + _rng.randf_range(0.0, 2.0)), 0, zc + _rng.randf_range(-3.0, 3.0))
			b2.rotation.y = (PI * 0.5) * float(_rng.randi() % 4)
			b2.scale = Vector3(1.0, _rng.randf_range(1.1, 1.6), 1.0)
			props.add_child(b2)
	# lamp posts alternate sides every 10 m
	for i in 2:
		var side := -1.0 if (i + int(absf(seg.position.z / _seg_len))) % 2 == 0 else 1.0
		var lamp := Globals.model("lamp_post")
		lamp.position = Vector3(side * 5.3, 0, -3.0 - 10.0 * i)
		lamp.rotation.y = PI * 0.5 if side < 0 else -PI * 0.5
		props.add_child(lamp)
	# sidewalk clutter
	var n := _rng.randi_range(1, 3)
	for i in n:
		var side := -1.0 if _rng.randf() < 0.5 else 1.0
		var prop := Globals.model(SIDEWALK_PROPS[_rng.randi() % SIDEWALK_PROPS.size()])
		prop.position = Vector3(side * _rng.randf_range(4.8, 5.4), 0.15, _rng.randf_range(-19.0, -1.0))
		prop.rotation.y = _rng.randf_range(-0.3, 0.3) + (0.0 if _rng.randf() < 0.5 else PI)
		props.add_child(prop)

func update_streaming(player_z: float) -> void:
	# recycle segments that are far behind the player
	var recycled := true
	while recycled:
		recycled = false
		for seg in segments:
			var near_z: float = seg.get_meta("near_z")
			if near_z - _seg_len > player_z + 2.0 * _seg_len:
				_place_segment(seg, _frontier_z, true)
				_frontier_z -= _seg_len
				recycled = true
				break
