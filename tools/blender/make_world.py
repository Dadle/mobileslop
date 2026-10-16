"""World set dressing: road segment, buildings, car wreck, barrier, lamp post, dead tree, sandbags."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import Part, V, mat, srgb, make_object, make_empty
from mathutils import Matrix

ONLY = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []


# ------------------------------------------------------------------ road
def build_road(root_name="RoadSegment"):
    asphalt = mat("MAT_asphalt", srgb(72, 72, 78), rough=0.9)
    asphalt_dark = mat("MAT_asphalt_dark", srgb(46, 46, 52), rough=0.9)
    line = mat("MAT_line", srgb(240, 200, 60), rough=0.8)
    curb = mat("MAT_curb", srgb(150, 150, 146), rough=0.85)
    walk = mat("MAT_sidewalk", srgb(176, 174, 166), rough=0.85)
    walk_dark = mat("MAT_sidewalk_dark", srgb(150, 148, 140), rough=0.85)
    p = Part()
    p.box((0, 10, -0.1), (8.0, 20.0, 0.2), asphalt)                       # slab, top at z=0
    for i in range(5):                                                    # dashed centre line, period 4 m
        p.box((0, 1.0 + 4 * i + 1.0, 0.004), (0.18, 2.0, 0.008), line)
    for sx in (-1, 1):                                                    # curbs + sidewalks (top z=0.15)
        p.box((sx * 4.15, 10, -0.025), (0.3, 20.0, 0.35), curb)
        p.box((sx * 5.15, 10, -0.025), (1.7, 20.0, 0.35), walk)
        for j in range(10):                                               # paving joints every 2 m
            p.box((sx * 5.15, 1.0 + 2 * j, 0.151), (1.7, 0.04, 0.004), walk_dark)
    rnd = random.Random(7)
    for k in range(7):                                                    # cracks (thin dark strips)
        x = rnd.uniform(-3.4, 3.4); y = rnd.uniform(1.5, 18.5)
        L = rnd.uniform(0.8, 2.2); ang = rnd.uniform(-0.5, 0.5)
        p.box((x, y, 0.003), (0.05, L, 0.006), asphalt_dark, rot=Matrix.Rotation(ang, 4, "Z"))
        p.box((x + 0.15 * math.cos(ang), y + L * 0.5 * math.cos(ang), 0.003), (0.05, L * 0.5, 0.006), asphalt_dark,
              rot=Matrix.Rotation(ang - 0.9, 4, "Z"))
    for (x, y, w, h) in ((-2.2, 4.5, 1.2, 1.6), (1.8, 12.0, 1.5, 1.1), (2.6, 16.5, 0.9, 0.9), (-1.0, 8.8, 0.8, 1.3)):
        p.box((x, y, 0.002), (w, h, 0.004), asphalt_dark)                 # patches
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ buildings
def build_building(variant):
    cfg = {
        "a": dict(h=10.0, wall=srgb(150, 78, 60), trim=srgb(110, 56, 44), floors=3, name="MAT_brick"),
        "b": dict(h=16.0, wall=srgb(136, 138, 134), trim=srgb(104, 106, 102), floors=5, name="MAT_concrete"),
        "c": dict(h=24.0, wall=srgb(196, 176, 140), trim=srgb(150, 132, 100), floors=7, name="MAT_beige"),
    }[variant]
    wall = mat(cfg["name"], cfg["wall"], rough=0.9)
    trim = mat(cfg["name"] + "_trim", cfg["trim"], rough=0.9)
    glass = mat("MAT_window", srgb(28, 34, 44), rough=0.5)
    board = mat("MAT_plank", srgb(140, 108, 70), rough=0.85)
    roof = mat("MAT_roof", srgb(70, 70, 72), rough=0.9)
    rnd = random.Random({"a": 1, "b": 2, "c": 3}[variant])
    H = cfg["h"]; S = 8.0; hs = S * 0.5
    p = Part()
    p.box((0, 0, H * 0.5), (S, S, H), wall)
    p.box((0, 0, H + 0.2), (S + 0.3, S + 0.3, 0.4), trim)                 # parapet
    p.box((0, 0, H + 0.4), (S - 0.6, S - 0.6, 0.02), roof)
    p.box((1.8, -1.5, H + 0.85), (1.6, 1.2, 0.9), trim)                   # rooftop unit
    p.cyl((-2.0, 2.0, H + 1.0), 0.35, 1.2, trim, segs=8)                  # water tank / vent
    # ground-floor plinth band
    p.box((0, 0, 0.6), (S + 0.1, S + 0.1, 1.2), trim)
    # windows on all four faces; front door on -X
    fh = (H - 1.2) / cfg["floors"]
    cols = (-2.4, 0.0, 2.4)
    for face in range(4):
        for fl in range(cfg["floors"]):
            z = 1.2 + fh * (fl + 0.55)
            for ci, c in enumerate(cols):
                if face == 2 and fl == 0 and ci == 1:
                    continue  # door goes here (-X face)
                w, h = 1.2, min(1.6, fh * 0.6)
                boarded = rnd.random() < 0.3
                def place(size, m, d=0.0, solid=False):
                    if solid:   # boards are real boxes (they stick out)
                        if face == 0:   p.box((c, hs + d, z), (size[0], 0.06, size[1]), m)
                        elif face == 1: p.box((c, -hs - d, z), (size[0], 0.06, size[1]), m)
                        elif face == 2: p.box((-hs - d, c, z), (0.06, size[0], size[1]), m)
                        else:           p.box((hs + d, c, z), (0.06, size[0], size[1]), m)
                        return
                    if face == 0:   p.face_quad((c, hs + d, z), size, "+Y", m)
                    elif face == 1: p.face_quad((c, -hs - d, z), size, "-Y", m)
                    elif face == 2: p.face_quad((-hs - d, c, z), size, "-X", m)
                    else:           p.face_quad((hs + d, c, z), size, "+X", m)
                place((w + 0.3, h + 0.3), trim, 0.01)       # sill/frame (decal)
                place((w, h), glass, 0.02)                   # dark inset (decal)
                if boarded:                                   # nailed planks
                    place((w + 0.2, 0.2), board, 0.04, solid=True)
                    place((0.2, h + 0.1), board, 0.05, solid=True)
    # door on -X face
    p.box((-hs - 0.03, 0, 1.1), (0.08, 1.6, 2.2), trim)
    p.box((-hs - 0.07, 0, 1.0), (0.05, 1.2, 2.0), glass)
    p.box((-hs - 0.25, 0, 0.1), (0.5, 2.4, 0.2), trim)  # step
    # rubble / damage: a chunk missing from one top corner (dark inset) and some debris boxes
    p.box((hs - 0.4, hs - 0.4, H - 0.6), (1.2, 1.2, 1.4), glass)
    for i in range(4):
        p.box((rnd.uniform(-hs, hs), -hs - rnd.uniform(0.3, 0.9), 0.15), (0.5, 0.4, 0.3), trim,
              rot=Matrix.Rotation(rnd.uniform(0, 1.0), 4, "Z"))
    return make_object(f"Building{variant.upper()}", p, (0, 0, 0))


# ------------------------------------------------------------------ car wreck
def build_car(root_name="CarWreck"):
    body = mat("MAT_car_rust", srgb(178, 86, 40), rough=0.85)
    burnt = mat("MAT_car_burnt", srgb(62, 58, 56), rough=0.9)
    glass = mat("MAT_window", srgb(28, 34, 44), rough=0.5)
    tyre = mat("MAT_tyre", srgb(30, 30, 32), rough=0.9)
    p = Part()
    # body (long axis along Y), sits on simple wheels; slightly sunken rear
    p.box((0, 0, 0.55), (1.9, 4.4, 0.6), body, bevel=0.05)
    p.box((0, 0.3, 1.1), (1.7, 2.2, 0.55), burnt, bevel=0.06)             # cabin (burnt)
    p.box((0, 1.6, 0.9), (1.75, 1.5, 0.12), burnt, bevel=0.03)             # scorched bonnet
    p.box((0, -1.9, 0.9), (1.7, 0.6, 0.1), body, bevel=0.02)               # boot lid
    # windows (dark) front / back / sides
    p.box((0, 1.42, 1.15), (1.4, 0.06, 0.4), glass, rot=Matrix.Rotation(math.radians(30), 4, "X"))
    p.box((0, -0.82, 1.15), (1.4, 0.06, 0.4), glass, rot=Matrix.Rotation(math.radians(-30), 4, "X"))
    for sx in (-1, 1):
        p.box((sx * 0.87, 0.3, 1.15), (0.04, 1.8, 0.35), glass)
    # bumpers, crumpled front corner
    p.box((0, 2.2, 0.4), (1.9, 0.15, 0.25), burnt, bevel=0.02)
    p.box((0, -2.25, 0.4), (1.9, 0.15, 0.25), burnt, bevel=0.02)
    p.box((0.75, 1.95, 0.7), (0.5, 0.5, 0.45), burnt, rot=Matrix.Rotation(0.5, 4, "Z"), bevel=0.02)
    # wheels (cylinders along X), missing one rear wheel -> rests on a brake drum
    for (x, y) in ((-0.95, 1.4), (0.95, 1.4), (0.95, -1.4)):
        p.cyl((x, y, 0.32), 0.32, 0.22, tyre, axis="X", segs=10)
        p.cyl((x, y, 0.32), 0.17, 0.24, burnt, axis="X", segs=10)
    p.cyl((-0.95, -1.4, 0.32), 0.16, 0.2, burnt, axis="X", segs=10)
    # open burnt-out door
    p.box((-1.15, -0.1, 0.65), (0.08, 1.0, 0.7), body, rot=Matrix.Rotation(-0.9, 4, "Z"), bevel=0.02)
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ barrier
def build_barrier(root_name="Barrier"):
    conc = mat("MAT_concrete", srgb(150, 150, 146), rough=0.9)
    yellow = mat("MAT_stripe_yellow", srgb(240, 190, 40), rough=0.7)
    black = mat("MAT_stripe_black", srgb(30, 30, 32), rough=0.7)
    p = Part()
    # jersey profile in (y, z); extruded along X from -1 to 1
    prof = [(-0.32, 0.0), (0.32, 0.0), (0.32, 0.1), (0.22, 0.1), (0.13, 0.55),
            (-0.13, 0.55), (-0.22, 0.1), (-0.32, 0.1)]
    p.prism(prof, "X", -1.0, 1.0, conc)
    # striped cap: alternating yellow / black segments along X
    top = [(-0.13, 0.55), (0.13, 0.55), (0.11, 0.8), (-0.11, 0.8)]
    n = 8
    for i in range(n):
        x0 = -1.0 + 2.0 * i / n
        p.prism(top, "X", x0, x0 + 2.0 / n, yellow if i % 2 == 0 else black)
    # lifting slots
    for sx in (-1, 1):
        p.box((sx * 0.6, 0, 0.3), (0.3, 0.5, 0.12), black)
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ lamp post
def build_lamp(root_name="LampPost"):
    grey = mat("MAT_post", srgb(96, 100, 104), rough=0.6, metal=0.3)
    lamp = mat("MAT_lamp", srgb(255, 236, 160), rough=0.2)
    p = Part()
    p.cyl((0, 0, 0.2), 0.22, 0.4, grey, segs=10)                          # base
    p.cyl((0, 0, 3.0), 0.1, 5.6, grey, segs=8, r2=0.07)                   # pole, tapers
    p.cyl((0.2, 0, 5.8), 0.07, 0.6, grey, axis=(1, 0, 0.6), segs=8)      # bend
    p.box((0.9, 0, 5.95), (1.2, 0.1, 0.1), grey, bevel=0.01)              # arm
    p.box((1.35, 0, 5.88), (0.7, 0.35, 0.2), grey, bevel=0.02)            # head
    p.box((1.35, 0, 5.77), (0.55, 0.25, 0.04), lamp)                      # light panel (underside)
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ dead tree
def build_tree(root_name="TreeDead"):
    bark = mat("MAT_bark", srgb(62, 44, 32), rough=0.95)
    p = Part()
    rnd = random.Random(11)
    p.cyl((0, 0, 1.6), 0.28, 3.2, bark, segs=7, r2=0.16, smooth=False)    # trunk
    p.cyl((0, 0, 3.6), 0.16, 0.9, bark, segs=7, r2=0.11, smooth=False)
    p.cyl((0, 0, 0.1), 0.42, 0.2, bark, segs=7, r2=0.3, smooth=False)     # root flare
    def branch(a, d, L, w, depth):
        b = V(a) + V(d).normalized() * L
        p.bar(a, b, w, w, bark, extend=0.02)
        if depth > 0:
            for k in range(2):
                nd = V(d) + V((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(0.3, 1.0)))
                branch(b, nd, L * 0.62, w * 0.6, depth - 1)
    branch((0, 0, 4.0), (0.0, 0.0, 1.0), 1.0, 0.15, 3)
    branch((0.1, 0.0, 3.1), (1.0, 0.2, 0.9), 1.3, 0.15, 3)
    branch((-0.1, 0.05, 2.5), (-1.0, 0.3, 0.8), 1.2, 0.14, 3)
    branch((0.0, -0.1, 3.5), (0.2, -1.0, 0.7), 1.1, 0.12, 2)
    branch((0.0, 0.12, 1.9), (0.4, 0.9, 0.3), 0.8, 0.10, 2)
    branch((0.05, -0.1, 1.3), (-0.5, -0.8, 0.5), 0.6, 0.08, 1)
    import bmesh
    bmesh.ops.scale(p.bm, vec=(0.8, 0.8, 0.8), verts=p.bm.verts[:])   # ~5 m tall
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ sandbags
def build_sandbag(root_name="Sandbag"):
    tan = mat("MAT_sand", srgb(196, 172, 122), rough=0.95)
    tan2 = mat("MAT_sand_dark", srgb(172, 150, 104), rough=0.95)
    p = Part()
    rnd = random.Random(5)
    rows = 4
    bw, bd, bh = 0.52, 0.34, 0.2
    for r in range(rows):
        n = 4 if r % 2 == 0 else 3
        off = 0.0 if r % 2 == 0 else bw * 0.5
        for i in range(n):
            x = -1.0 + bw * 0.5 + i * bw + off + rnd.uniform(-0.02, 0.02)
            if abs(x) > 1.0 - bw * 0.45:
                continue
            y = rnd.uniform(-0.03, 0.03)
            p.box((x, y, bh * 0.5 + r * bh), (bw * 0.98, bd, bh), tan if (i + r) % 2 == 0 else tan2,
                  bevel=0.06, rot=Matrix.Rotation(rnd.uniform(-0.08, 0.08), 4, "Z"))
    return make_object(root_name, p, (0, 0, 0))


BUILDERS = {
    "road_segment": (build_road, (-0.9, -1.1, 0.9), 30),
    "building_a": (lambda: build_building("a"), (-1.2, -1.0, 0.7), 40),
    "building_b": (lambda: build_building("b"), (-1.2, -1.0, 0.7), 40),
    "building_c": (lambda: build_building("c"), (-1.2, -1.0, 0.7), 40),
    "car_wreck": (build_car, (-1.0, -1.3, 0.6), 50),
    "barrier": (build_barrier, (-1.0, -1.3, 0.6), 50),
    "lamp_post": (build_lamp, (-1.0, -1.3, 0.5), 50),
    "tree_dead": (build_tree, (-1.0, -1.3, 0.4), 50),
    "sandbag": (build_sandbag, (-1.0, -1.3, 0.7), 50),
    "crate": (None, (-1.0, -1.3, 0.75), 50),
}


def street():
    """Composite scene for judging proportions: road + buildings + props."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_props, make_characters
    lp.reset_scene()
    build_road()
    r2 = build_road(); r2.location.y = 20
    for v, (x, y) in (("a", (10, 4)), ("b", (10, 14)), ("c", (10, 26)), ("c", (-10, 4)), ("a", (-10, 14)), ("b", (-10, 26))):
        b = build_building(v); b.location = (x, y, 0)
        if x < 0:
            b.rotation_euler.z = math.pi  # door towards the road
    for y in (3, 15, 27):
        l = build_lamp(); l.location = (5.4, y, 0)
        l.rotation_euler.z = math.pi  # arm towards road (-X)
    c = build_car(); c.location = (-2.5, 9, 0); c.rotation_euler.z = 0.35
    b = build_barrier(); b.location = (2.5, 14, 0)
    t = build_tree(); t.location = (-5.2, 17, 0)
    s = build_sandbag(); s.location = (-2.0, 22, 0)
    cr = make_props.build_crate(); cr.location = (2.0, 7, 0)
    pu = make_props.build_powerup(); pu.location = (-2.0, 5, 0)
    so = make_characters.build_humanoid("Soldier", make_characters.soldier_params()); so.location = (0, 1.5, 0)
    z = make_characters.build_humanoid("Zombie", make_characters.zombie_params()); z.location = (-2, 12, 0)
    z.rotation_euler.z = math.pi
    zb = make_characters.build_humanoid("Zombie", make_characters.brute_params()); zb.location = (2, 19, 0)
    zb.rotation_euler.z = math.pi
    lp.render_preview("street.png", view=(0.35, -1.0, 0.75), lens=35, look_at=(0, 11, 0.5), dist=26)


if __name__ == "__main__":
    keys = ONLY or [k for k in BUILDERS if BUILDERS[k][0]] + ["street"]
    for key in keys:
        if key == "street":
            street(); continue
        fn, view, lens = BUILDERS[key]
        lp.reset_scene()
        root = fn()
        lp.export_glb(f"{key}.glb", [root])
        lp.dump_tree(root)
        lp.render_preview(f"{key}.png", view=view, lens=lens)
