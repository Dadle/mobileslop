class_name HUD
extends CanvasLayer
## All 2D UI: HP bar, score, distance, weapon chips, popups, menu and game-over overlays.

signal start_pressed
signal retry_pressed

var _root: Control
var _score_label: Label
var _dist_label: Label
var _hp_bar: ProgressBar
var _hp_text: Label
var _chips: Label
var _timers: Label
var _tier_label: Label
var _boss_holder: Control
var _boss_bar: ProgressBar
var _boss_text: Label
var _popup: Label
var _vignette: ColorRect
var _menu: Control
var _game_over: Control
var _go_stats: Label
var _tap_label: Label
var _retry_label: Label
var _best_label: Label
var _mute_btn: Button
var _t := 0.0

func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)

	# ---- damage vignette
	_vignette = ColorRect.new()
	_vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_vignette.color = Color(0.9, 0.05, 0.05, 0.0)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_vignette)

	# ---- top bar
	var top := MarginContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.add_theme_constant_override("margin_left", 28)
	top.add_theme_constant_override("margin_right", 28)
	top.add_theme_constant_override("margin_top", 36)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(top)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 10)
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(vb)
	var hb := HBoxContainer.new()
	hb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(hb)
	_score_label = _label("0", 64, "bold", Color(1, 0.92, 0.4))
	_score_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(_score_label)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	right.add_theme_constant_override("separation", -6)
	hb.add_child(right)
	_dist_label = _label("0 m", 44, "bold", Color(1, 1, 1))
	_dist_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(_dist_label)
	_tier_label = _label("TIER 1", 26, "bold", Color(0.6, 1.0, 0.5))
	_tier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(_tier_label)
	# hp bar
	var hp_holder := Control.new()
	hp_holder.custom_minimum_size = Vector2(0, 40)
	hp_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(hp_holder)
	_hp_bar = ProgressBar.new()
	_hp_bar.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_hp_bar.show_percentage = false
	_hp_bar.min_value = 0
	_hp_bar.max_value = 100
	_hp_bar.value = 100
	_hp_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.08, 0.08, 0.1, 0.8)
	bg.set_corner_radius_all(12)
	bg.border_color = Color(1, 1, 1, 0.9)
	bg.set_border_width_all(3)
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color(0.85, 0.15, 0.15)
	fill.set_corner_radius_all(9)
	fill.set_content_margin_all(3)
	_hp_bar.add_theme_stylebox_override("background", bg)
	_hp_bar.add_theme_stylebox_override("fill", fill)
	hp_holder.add_child(_hp_bar)
	_hp_text = _label("HP 100", 26, "bold", Color.WHITE)
	_hp_text.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_hp_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hp_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hp_holder.add_child(_hp_text)
	_timers = _label("", 30, "bold", Color(0.5, 0.85, 1.0))
	_timers.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(_timers)
	# boss bar
	_boss_holder = Control.new()
	_boss_holder.custom_minimum_size = Vector2(0, 34)
	_boss_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_holder.visible = false
	vb.add_child(_boss_holder)
	_boss_bar = ProgressBar.new()
	_boss_bar.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_boss_bar.show_percentage = false
	_boss_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bbg := StyleBoxFlat.new()
	bbg.bg_color = Color(0.1, 0.02, 0.02, 0.85)
	bbg.set_corner_radius_all(10)
	bbg.border_color = Color(1, 0.4, 0.3, 0.9)
	bbg.set_border_width_all(3)
	var bfill := StyleBoxFlat.new()
	bfill.bg_color = Color(0.75, 0.1, 0.35)
	bfill.set_corner_radius_all(7)
	bfill.set_content_margin_all(3)
	_boss_bar.add_theme_stylebox_override("background", bbg)
	_boss_bar.add_theme_stylebox_override("fill", bfill)
	_boss_holder.add_child(_boss_bar)
	_boss_text = _label("BOSS", 22, "bold", Color.WHITE)
	_boss_text.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_boss_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boss_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_boss_holder.add_child(_boss_text)

	# ---- mute button
	_mute_btn = Button.new()
	_mute_btn.text = "SFX"
	_mute_btn.flat = true
	_mute_btn.add_theme_font_override("font", Globals.font("bold"))
	_mute_btn.add_theme_font_size_override("font_size", 26)
	_mute_btn.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_mute_btn.offset_left = -130
	_mute_btn.offset_right = -20
	_mute_btn.offset_top = -40
	_mute_btn.offset_bottom = 0
	_mute_btn.pressed.connect(func(): Sfx.toggle_mute(); _update_mute())
	_root.add_child(_mute_btn)
	_update_mute()

	# ---- bottom chips
	_chips = _label("", 30, "bold", Color(1, 1, 1, 0.95))
	_chips.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_chips.offset_top = -100
	_chips.offset_bottom = -50
	_chips.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(_chips)

	# ---- popup
	_popup = _label("", 72, "title", Color(1, 0.9, 0.3))
	_popup.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_popup.offset_top = 400
	_popup.offset_bottom = 520
	_popup.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_popup.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_popup.modulate.a = 0.0
	_root.add_child(_popup)

	# ---- menu overlay
	_menu = _overlay()
	var mv := VBoxContainer.new()
	mv.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mv.alignment = BoxContainer.ALIGNMENT_CENTER
	mv.add_theme_constant_override("separation", 14)
	mv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_menu.add_child(mv)
	var t1 := _label("LANE RUSH", 150, "title", Color(1, 0.85, 0.2))
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mv.add_child(t1)
	var t2 := _label("ZOMBIE ROAD", 70, "title", Color(0.55, 0.95, 0.45))
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mv.add_child(t2)
	mv.add_child(_spacer(40))
	var how := _label("Zombies pour down both lanes.\nUpgrade gates block the RIGHT lane:\nshoot one the number of times written on it\nto grab more soldiers, new guns, more bullets.\n\nEvery few dozen kills a BOSS blocks the road.\nKill it and the horde mutates: tougher, nastier.\n\nDrag / A-D to move.  You never stop shooting.", 28, "ui", Color(1, 1, 1, 0.92))
	how.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mv.add_child(how)
	mv.add_child(_spacer(40))
	_tap_label = _label("TAP TO START", 64, "title", Color.WHITE)
	_tap_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mv.add_child(_tap_label)
	_best_label = _label("", 30, "bold", Color(1, 0.92, 0.4))
	_best_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mv.add_child(_best_label)
	_root.add_child(_menu)

	# ---- game over overlay
	_game_over = _overlay()
	var gv := VBoxContainer.new()
	gv.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	gv.alignment = BoxContainer.ALIGNMENT_CENTER
	gv.add_theme_constant_override("separation", 18)
	gv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game_over.add_child(gv)
	var g1 := _label("YOU GOT EATEN", 110, "title", Color(1, 0.3, 0.25))
	g1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gv.add_child(g1)
	_go_stats = _label("", 40, "bold", Color.WHITE)
	_go_stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gv.add_child(_go_stats)
	gv.add_child(_spacer(30))
	var g2 := _label("TAP TO RETRY", 64, "title", Color.WHITE)
	_retry_label = g2
	g2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gv.add_child(g2)
	_game_over.visible = false
	_root.add_child(_game_over)

func _overlay() -> Control:
	var o := Control.new()
	o.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	o.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.02, 0.03, 0.06, 0.55)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	o.add_child(shade)
	return o

func _spacer(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c

func _label(text: String, size: int, font: String, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", Globals.font(font))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", int(size * 0.16))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func _update_mute() -> void:
	_mute_btn.text = "SFX ON" if Globals.sfx_on else "SFX OFF"
	_mute_btn.modulate = Color(1, 1, 1, 0.9) if Globals.sfx_on else Color(1, 0.5, 0.5, 0.9)

func _process(delta: float) -> void:
	_t += delta
	if _menu.visible:
		_tap_label.modulate.a = 0.55 + 0.45 * absf(sin(_t * 3.0))
	if _game_over.visible:
		_retry_label.modulate.a = 0.55 + 0.45 * absf(sin(_t * 3.0))

func show_menu(best_score: int, best_distance: int) -> void:
	_menu.visible = true
	_game_over.visible = false
	_best_label.text = "BEST  %d pts   •   %d m" % [best_score, best_distance] if best_score > 0 else ""

func show_playing() -> void:
	_menu.visible = false
	_game_over.visible = false

func show_game_over(score: int, distance: int, kills: int, crates: int, tier: int, best: int, new_best: bool) -> void:
	_game_over.visible = true
	_go_stats.text = "SCORE  %d%s\nDISTANCE  %d m     TIER  %d\nKILLS  %d     GATES  %d\nBEST  %d" % [score, "   NEW BEST!" if new_best else "", distance, tier + 1, kills, crates, best]

func set_score(v: int) -> void:
	_score_label.text = str(v)

func set_distance(m: float) -> void:
	_dist_label.text = "%d m" % int(m)

func set_hp(hp: float, max_hp: float) -> void:
	_hp_bar.max_value = max_hp
	_hp_bar.value = hp
	_hp_text.text = "HP %d" % int(ceil(hp))
	var fill: StyleBoxFlat = _hp_bar.get_theme_stylebox("fill")
	var f := hp / max_hp
	fill.bg_color = Color(0.85, 0.15, 0.15).lerp(Color(0.3, 0.85, 0.3), clampf((f - 0.3) / 0.7, 0.0, 1.0))

func set_stats(p: Node) -> void:
	var w: Dictionary = p.weapon()
	_chips.text = "%s    SQUAD x%d    %.1f shots/s" % [w["name"], p.squad_size, p.effective_fire_rate() * p.squad_size]

func set_tier(t: int) -> void:
	var c: Dictionary = Zombie.TIER_COLORS[t % Zombie.TIER_COLORS.size()]
	_tier_label.text = "TIER %d" % (t + 1)
	_tier_label.add_theme_color_override("font_color", (c["skin"] as Color).lightened(0.35) if t > 0 else Color(0.6, 1.0, 0.5))

func show_boss(name: String) -> void:
	_boss_holder.visible = true
	_boss_text.text = name

func hide_boss() -> void:
	_boss_holder.visible = false

func set_boss_hp(hp: float, max_hp: float) -> void:
	_boss_bar.max_value = max_hp
	_boss_bar.value = maxf(hp, 0.0)

func set_timers(p: Node) -> void:
	var parts: Array[String] = []
	var now: float = p.now()
	if p.launcher_until > now:
		parts.append("LAUNCHER %.0fs" % ceil(p.launcher_until - now))
	if p.shield_until > now:
		parts.append("SHIELD %.0fs" % ceil(p.shield_until - now))
	_timers.text = "   ".join(parts)

func show_popup(text: String, color: Color = Color(1, 0.9, 0.3)) -> void:
	_popup.text = text
	_popup.add_theme_color_override("font_color", color)
	_popup.pivot_offset = _popup.size * 0.5
	_popup.modulate.a = 1.0
	_popup.scale = Vector2.ONE * 0.4
	var tw := create_tween()
	tw.tween_property(_popup, "scale", Vector2.ONE * 1.1, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(_popup, "scale", Vector2.ONE, 0.15)
	tw.tween_interval(0.7)
	tw.tween_property(_popup, "modulate:a", 0.0, 0.35)

func damage_flash() -> void:
	_vignette.color.a = 0.35
	var tw := create_tween()
	tw.tween_property(_vignette, "color:a", 0.0, 0.4)
