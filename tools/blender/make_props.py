"""Gameplay props: numbered supply crate and the floating powerup."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import Part, V, mat, srgb, make_object, make_empty
from mathutils import Matrix

ONLY = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []


def build_crate(root_name="Crate"):
    """1 m cube, z 0..1, olive wood, metal edge frame, lighter number panel on the -Y face."""
    wood = mat("MAT_wood", srgb(96, 112, 58))
    wood_dark = mat("MAT_wood_dark", srgb(72, 86, 44))
    metal = mat("MAT_metal", srgb(120, 124, 128), rough=0.45, metal=0.7)
    panel = mat("MAT_panel", srgb(150, 166, 96), rough=0.6)
    p = Part()
    p.box((0, 0, 0.5), (0.96, 0.96, 0.96), wood, bevel=0.01)
    # plank grooves on the +Y / ±X sides (darker thin strips)
    for z in (0.33, 0.66):
        p.box((0, 0.48, z), (0.9, 0.02, 0.02), wood_dark)
        for sx in (-1, 1):
            p.box((sx * 0.48, 0, z), (0.02, 0.9, 0.02), wood_dark)
    # metal frame: 12 edges
    t = 0.07
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * 0.48, sy * 0.48, 0.5), (t, t, 1.0), metal, bevel=0.01)          # vertical
        for sz in (0.035, 0.965):
            p.box((sx * 0.48, 0, sz), (t, 1.0, t), metal, bevel=0.01)                      # along Y
    for sy in (-1, 1):
        for sz in (0.035, 0.965):
            p.box((0, sy * 0.48, sz), (1.0, t, t), metal, bevel=0.01)                      # along X
    # corner rivets on the front
    for sx in (-1, 1):
        for sz in (0.14, 0.86):
            p.box((sx * 0.40, -0.505, sz), (0.04, 0.02, 0.04), metal)
    # number panel on the -Y face (towards the player)
    p.box((0, -0.49, 0.5), (0.70, 0.03, 0.70), panel)
    return make_object(root_name, p, (0, 0, 0))


def build_powerup(root_name="Powerup"):
    gold = mat("MAT_gold", srgb(255, 214, 70), rough=0.3, metal=0.8)
    gold_dark = mat("MAT_gold_dark", srgb(236, 160, 30), rough=0.35, metal=0.8)
    root = make_empty(root_name, (0, 0, 0), size=0.2)
    p = Part()
    ro, ri, n = 0.32, 0.14, 5
    # 5-point star standing upright in the XZ plane (one point up), extruded along Y
    prof_zx = []
    for i in range(n * 2):
        a = math.pi / 2 + i * math.pi / n
        r = ro if i % 2 == 0 else ri
        prof_zx.append((r * math.sin(a), r * math.cos(a)))      # (z, x) for a Y-axis prism
    p.prism(prof_zx, "Y", -0.07, 0.07, gold, offset=(0, 0, 0.6))
    # chunky ring + core gem for silhouette depth
    p.cyl((0, 0, 0.6), 0.12, 0.2, gold_dark, axis="Y", segs=10, smooth=False)
    p.sphere((0, 0, 0.6), 0.09, gold, segs=10, rings=6)
    make_object("Star", p, (0, 0, 0.6), root)
    return root


BUILDERS = {
    "crate": (build_crate, (-1.0, -1.3, 0.75)),
    "powerup": (build_powerup, (-1.0, -1.3, 0.5)),
}

if __name__ == "__main__":
    for key in (ONLY or list(BUILDERS)):
        fn, view = BUILDERS[key]
        lp.reset_scene()
        root = fn()
        lp.export_glb(f"{key}.glb", [root])
        lp.dump_tree(root)
        lp.render_preview(f"{key}.png", view=view, lens=50)
