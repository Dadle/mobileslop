extends Node
## Autoload "Sfx": pooled one-shot sound playback with pitch variation + looping music.

const POOL_SIZE := 20
var _players: Array[AudioStreamPlayer] = []
var _streams := {}
var _last_play := {}
var music: AudioStreamPlayer
var _current_music := ""

func _ready() -> void:
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	music = AudioStreamPlayer.new()
	music.volume_db = -10.0
	add_child(music)
	_apply_mute()

func _stream(n: String) -> AudioStream:
	if not _streams.has(n):
		var path := "res://assets/audio/%s.wav" % n
		_streams[n] = load(path) if ResourceLoader.exists(path) else null
	return _streams[n]

## Play a one-shot. min_interval throttles spammy sounds (seconds).
func play(n: String, vol_db := 0.0, pitch_var := 0.08, pitch := 1.0, min_interval := 0.0) -> void:
	var s := _stream(n)
	if s == null:
		return
	var now := Time.get_ticks_msec() / 1000.0
	if min_interval > 0.0 and _last_play.has(n) and now - _last_play[n] < min_interval:
		return
	_last_play[n] = now
	var chosen: AudioStreamPlayer = null
	for p in _players:
		if not p.playing:
			chosen = p
			break
	if chosen == null:
		chosen = _players[randi() % POOL_SIZE]
	chosen.stream = s
	chosen.volume_db = vol_db
	chosen.pitch_scale = pitch * randf_range(1.0 - pitch_var, 1.0 + pitch_var)
	chosen.play()

func play_music(n: String) -> void:
	if _current_music == n and music.playing:
		return
	var s := _stream(n)
	if s == null:
		return
	if s is AudioStreamWAV:
		var w := s as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		var bytes_per_sample := 2 if w.format == AudioStreamWAV.FORMAT_16_BITS else 1
		var channels := 2 if w.stereo else 1
		w.loop_end = int(w.data.size() / (bytes_per_sample * channels))
	_current_music = n
	music.stream = s
	music.play()

func stop_music() -> void:
	music.stop()
	_current_music = ""

func toggle_mute() -> void:
	Globals.sfx_on = not Globals.sfx_on
	Globals.save()
	_apply_mute()

func _apply_mute() -> void:
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), not Globals.sfx_on)
