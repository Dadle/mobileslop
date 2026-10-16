"""Upgrade-system assets: the lane-wide supply gate, five interchangeable hand-held weapons and the boss zombie."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import Part, V, mat, srgb, make_object, make_empty
from make_characters import build_humanoid, zombie_params, limb, rot_about
from mathutils import Matrix

ONLY = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []


# ------------------------------------------------------------------ gate
def build_gate(root_name="Gate"):
    """3.4 m wide x 0.7 m deep x 1.5 m tall barricade: metal cage frame, central crate stack with the
    number panel on the -Y face (front-most surface at y=-0.35), sandbag + crate / barrel wings."""
    wood = mat("MAT_wood", srgb(96, 112, 58))
    wood_dark = mat("MAT_wood_dark", srgb(72, 86, 44))
    metal = mat("MAT_metal", srgb(120, 124, 128), rough=0.45, metal=0.7)
    metal_dark = mat("MAT_metal_dark", srgb(70, 72, 76), rough=0.5, metal=0.6)
    panel = mat("MAT_panel", srgb(150, 166, 96), rough=0.6)
    bag = mat("MAT_sandbag", srgb(196, 170, 118), rough=0.9)
    bag_dark = mat("MAT_sandbag_dark", srgb(168, 144, 96), rough=0.9)
    barrel = mat("MAT_barrel", srgb(70, 88, 52), rough=0.6, metal=0.3)
    hz_y = mat("MAT_hazard_yellow", srgb(240, 200, 40), rough=0.6)
    hz_k = mat("MAT_hazard_black", srgb(32, 32, 34), rough=0.6)
    p = Part()
    W, D, H = 3.4, 0.7, 1.5
    hw, hd = W * 0.5, D * 0.5

    # ---- central crate stack (x -0.75..0.75, y -0.33..0.33, z 0..1.4) carrying the panel
    cw, cd, ch = 1.5, 0.66, 1.4
    p.box((0, 0, ch * 0.5), (cw, cd, ch), wood, bevel=0.012)
    for z in (0.35, 0.7, 1.05):                                        # plank grooves (sides + back)
        p.box((0, cd * 0.5, z), (cw - 0.1, 0.02, 0.02), wood_dark)
        for sx in (-1, 1):
            p.box((sx * cw * 0.5, 0, z), (0.02, cd - 0.08, 0.02), wood_dark)
    t = 0.07
    for sx in (-1, 1):                                                 # metal edge frame of the crate
        for sy in (-1, 1):
            p.box((sx * (cw * 0.5 - 0.01), sy * 0.30, ch * 0.5), (t, t, ch), metal)
        p.box((sx * (cw * 0.5 - 0.01), 0, ch - 0.035), (t, cd - 0.05, t), metal)
        p.box((sx * (cw * 0.5 - 0.01), 0, 0.035), (t, cd - 0.05, t), metal)
    for sy in (-1, 1):
        p.box((0, sy * 0.30, ch - 0.035), (cw, t, t), metal)
        p.box((0, sy * 0.30, 0.035), (cw, t, t), metal)
    for sx in (-1, 1):                                                 # rivets beside the panel
        for z in (0.45, 0.8, 1.15):
            p.box((sx * 0.70, -0.335, z), (0.045, 0.012, 0.045), metal)
    # number panel on the -Y face: 1.3 x 1.0, centred z=0.8, FRONT FACE AT y=-0.35
    p.box((0, -0.35 + 0.015, 0.8), (1.3, 0.03, 1.0), panel)

    # ---- wings: sandbag stacks x 0.8..1.7 (both sides), three courses, staggered
    for sx in (-1, 1):
        for row in range(3):
            z = 0.13 + row * 0.25
            off = 0.0 if row % 2 == 0 else 0.22
            for i in range(2):
                x = sx * (1.02 + off + i * 0.44)
                if abs(x) + 0.21 > hw:
                    continue
                for j, y in enumerate((-0.17, 0.17)):
                    p.box((x, y, z), (0.42, 0.32, 0.26), bag if (i + j + row) % 2 else bag_dark,
                          bevel=0.06, smooth=True)
            if off:                                                    # half bag closing the stagger
                p.box((sx * 0.98, 0, z), (0.34, 0.6, 0.26), bag_dark, bevel=0.06, smooth=True)
    # left wing: small crate on the bags; right wing: two barrels
    Rz = Matrix.Rotation(math.radians(8), 4, "Z")
    cc = V((-1.25, 0.0, 0.78 + 0.27))
    p.box(cc, (0.66, 0.6, 0.54), wood, bevel=0.012, rot=Rz)
    for sy in (-1, 1):                                                 # strap bands, rotated with the crate
        p.box(cc + Rz @ V((0, sy * 0.28, 0)), (0.6, 0.05, 0.05), metal, rot=Rz)
    for (bx, by) in ((1.12, -0.12), (1.45, 0.12)):
        p.cyl((bx, by, 0.78 + 0.31), 0.19, 0.62, barrel, segs=10, smooth=True)
        p.cyl((bx, by, 0.78 + 0.31), 0.2, 0.06, metal_dark, segs=10, smooth=True)
        p.cyl((bx, by, 0.78 + 0.61), 0.2, 0.025, metal_dark, segs=10, smooth=True)

    # ---- outer metal cage: four corner posts, two inner posts, top rails
    pt = 0.09
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * (hw - pt * 0.5), sy * (hd - pt * 0.5 - 0.02), H * 0.5), (pt, pt, H), metal_dark)
        p.box((sx * 0.82, 0.30, 0.72), (pt, pt, H - 0.06), metal_dark)                       # inner rear posts
        p.box((sx * (hw - pt * 0.5), 0, H - pt * 0.5), (pt, D - 0.04, pt), metal_dark)       # top side bars
        p.box((sx * (hw - 0.03), 0, 0.03), (0.06, D - 0.04, 0.06), metal_dark)                # foot plate
    for sy in (-1, 1):
        p.box((0, sy * (hd - pt * 0.5 - 0.02), H - pt * 0.5), (W, pt, pt), metal_dark)   # top rails
    # hazard stripes on the front top rail (sit on the rail's front face, y > -0.35)
    n = 14
    for i in range(n):
        x = -hw + 0.08 + (i + 0.5) * (W - 0.16) / n
        p.box((x, -(hd - 0.02) - 0.004, H - pt * 0.5), ((W - 0.16) / n, 0.008, pt * 0.8), hz_y if i % 2 else hz_k)
    # diagonal braces on the wings' back
    for sx in (-1, 1):
        p.bar((sx * 0.9, 0.31, 0.1), (sx * (hw - 0.08), 0.31, H - 0.12), 0.05, 0.05, metal_dark)
    return make_object(root_name, p, (0, 0, 0))


# ------------------------------------------------------------------ weapons
# Gun-local frame: origin = right-hand grip point (same as the soldier's Gun pivot), barrel along +Y.
GZ = 0.08           # receiver centre line height above the grip point (matches make_characters rifle)
M_GUN = lambda: mat("MAT_gun", srgb(58, 60, 66), rough=0.5, metal=0.6)
M_GUN_DARK = lambda: mat("MAT_gun_dark", srgb(34, 36, 40), rough=0.5, metal=0.6)
M_STOCK = lambda: mat("MAT_stock", srgb(92, 66, 44))


def grip(gp, m, size=(0.045, 0.065, 0.12)):
    """Pistol grip exactly where the soldier's right hand is."""
    gp.box((0, 0, GZ - 0.09), size, m, bevel=0.006)


def rifle_stock(gp, m, y0=-0.23, w=0.055, L=0.22, h=0.10):
    gp.box((0, y0, GZ - 0.01), (w, L, h), m, bevel=0.012)
    gp.box((0, y0 - L * 0.5, GZ - 0.02), (w + 0.005, 0.04, h + 0.04), m, bevel=0.008)


def build_rifle(root_name="Gun"):
    """1:1 copy of the soldier's rifle geometry (make_characters.arms_soldier) in gun-local space."""
    gun, dark, stock = M_GUN(), M_GUN_DARK(), M_STOCK()
    gp = Part()
    gp.box((0, 0.05, GZ), (0.07, 0.36, 0.09), gun, bevel=0.01)
    gp.box((0, 0.31, GZ - 0.005), (0.065, 0.22, 0.075), dark, bevel=0.008)
    gp.cyl((0, 0.51, GZ + 0.012), 0.018, 0.22, gun, axis="Y", segs=8)
    gp.cyl((0, 0.60, GZ + 0.012), 0.027, 0.06, dark, axis="Y", segs=8)
    gp.box((0, 0.40, GZ + 0.06), (0.014, 0.02, 0.04), gun)
    gp.box((0, 0.0, GZ + 0.065), (0.035, 0.10, 0.035), dark, bevel=0.005)
    grip(gp, dark)
    gp.box((0, 0.14, GZ - 0.115), (0.045, 0.075, 0.17), gun, bevel=0.006, rot=Matrix.Rotation(math.radians(-12), 4, "X"))
    gp.box((0, -0.23, GZ - 0.01), (0.055, 0.22, 0.10), stock, bevel=0.012)
    gp.box((0, -0.34, GZ - 0.02), (0.06, 0.04, 0.14), stock, bevel=0.008)
    ob = make_object(root_name, gp, (0, 0, 0))
    make_empty("Muzzle", (0, 0.63, GZ + 0.012), ob, size=0.08)
    return ob


def build_assault(root_name="Gun"):
    gun, dark = M_GUN(), M_GUN_DARK()
    acc = mat("MAT_accent_orange", srgb(236, 110, 40), rough=0.55)
    poly = mat("MAT_polymer", srgb(48, 50, 54), rough=0.7)
    gp = Part()
    bz = GZ + 0.012
    gp.box((0, 0.06, GZ), (0.08, 0.40, 0.10), gun, bevel=0.01)                  # receiver
    gp.box((0, 0.33, GZ), (0.075, 0.26, 0.09), dark, bevel=0.008)               # handguard (longer)
    for sx in (-1, 1):                                                           # side accent plates
        gp.box((sx * 0.042, 0.04, GZ + 0.005), (0.008, 0.26, 0.05), acc)
        gp.box((sx * 0.040, 0.33, GZ - 0.005), (0.008, 0.18, 0.03), acc)
    gp.box((0, 0.49, bz), (0.06, 0.08, 0.07), dark, bevel=0.006)                 # gas block (abuts handguard)
    gp.cyl((0, 0.60, bz), 0.02, 0.26, gun, axis="Y", segs=8)                     # barrel 0.47..0.73
    gp.cyl((0, 0.73, bz), 0.032, 0.08, dark, axis="Y", segs=8)                   # muzzle brake
    for y in (0.715, 0.745):                                                     # brake slots
        gp.box((0, y, bz + 0.02), (0.07, 0.012, 0.02), acc)
    gp.box((0, 0.44, GZ + 0.065), (0.014, 0.024, 0.045), gun)                    # front sight
    gp.box((0, -0.02, GZ + 0.07), (0.04, 0.16, 0.045), dark, bevel=0.005)        # carry rail / sight
    gp.box((0, 0.05, GZ + 0.105), (0.03, 0.08, 0.025), acc)                      # red-dot housing
    gp.box((0, 0.34, GZ - 0.085), (0.04, 0.05, 0.09), poly, bevel=0.006,
           rot=Matrix.Rotation(math.radians(10), 4, "X"))                        # fore-grip
    grip(gp, poly)
    gp.box((0, 0.15, GZ - 0.135), (0.05, 0.09, 0.22), gun, bevel=0.006,
           rot=Matrix.Rotation(math.radians(-14), 4, "X"))                       # big magazine
    gp.box((0, 0.15, GZ - 0.235), (0.054, 0.095, 0.03), acc,
           rot=Matrix.Rotation(math.radians(-14), 4, "X"))                       # magazine base plate
    rifle_stock(gp, poly, y0=-0.23, w=0.06, L=0.22, h=0.11)
    gp.box((0, -0.22, GZ + 0.045), (0.062, 0.14, 0.02), acc)                     # stock accent
    ob = make_object(root_name, gp, (0, 0, 0))
    make_empty("Muzzle", (0, 0.77, bz), ob, size=0.08)
    return ob


def build_plasma(root_name="Gun"):
    body = mat("MAT_plasma_body", srgb(226, 228, 232), rough=0.45)
    grey = mat("MAT_plasma_grey", srgb(120, 124, 132), rough=0.55, metal=0.3)
    dark = M_GUN_DARK()
    glow = mat("MAT_glow_cyan", srgb(40, 240, 255), rough=0.3)
    gp = Part()
    bz = GZ + 0.012
    gp.box((0, 0.08, GZ + 0.005), (0.09, 0.42, 0.11), body, bevel=0.015)        # white body
    gp.box((0, 0.08, GZ - 0.03), (0.07, 0.40, 0.05), grey, bevel=0.008)          # grey underbody
    gp.box((0, 0.36, bz), (0.07, 0.22, 0.08), grey, bevel=0.01)                  # shroud / handguard
    gp.cyl((0, 0.54, bz), 0.028, 0.18, body, axis="Y", segs=10)                  # barrel
    gp.cyl((0, 0.66, bz), 0.03, 0.10, grey, axis="Y", segs=10, r2=0.058)         # flared muzzle
    gp.cyl((0, 0.705, bz), 0.045, 0.012, glow, axis="Y", segs=10)                # glowing muzzle core
    for sx in (-1, 1):                                                           # side energy cells
        for y in (-0.02, 0.06, 0.14):
            gp.box((sx * 0.047, y, GZ + 0.01), (0.008, 0.05, 0.05), glow)
    gp.box((0, 0.20, GZ + 0.062), (0.03, 0.50, 0.012), glow)                     # top glow strip
    gp.box((0, 0.26, GZ + 0.075), (0.05, 0.14, 0.03), grey, bevel=0.005)         # top sight block
    gp.box((0, 0.42, GZ + 0.06), (0.012, 0.03, 0.04), dark)                      # front sight
    gp.cyl((0, 0.10, GZ - 0.12), 0.05, 0.10, grey, axis="Y", segs=10)            # power canister under body
    gp.cyl((0, 0.10, GZ - 0.12), 0.052, 0.03, glow, axis="Y", segs=10)
    grip(gp, dark)
    gp.box((0, -0.22, GZ - 0.01), (0.06, 0.20, 0.09), body, bevel=0.012)         # stock
    gp.box((0, -0.33, GZ - 0.03), (0.062, 0.04, 0.13), grey, bevel=0.008)
    gp.box((0, -0.22, GZ - 0.065), (0.04, 0.16, 0.03), grey)                     # stock underside
    ob = make_object(root_name, gp, (0, 0, 0))
    make_empty("Muzzle", (0, 0.711, bz), ob, size=0.08)
    return ob


def build_rail(root_name="Gun"):
    gun, dark = M_GUN(), M_GUN_DARK()
    steel = mat("MAT_rail_steel", srgb(150, 156, 170), rough=0.35, metal=0.8)
    glow = mat("MAT_glow_violet", srgb(200, 60, 255), rough=0.3)
    stock_m = mat("MAT_rail_stock", srgb(40, 42, 50), rough=0.6)
    gp = Part()
    bz = GZ + 0.02
    gp.box((0, 0.04, GZ), (0.08, 0.40, 0.11), gun, bevel=0.01)                   # receiver
    gp.box((0, 0.30, GZ - 0.01), (0.07, 0.20, 0.08), dark, bevel=0.008)          # handguard
    gp.box((0, 0.56, bz), (0.07, 0.56, 0.02), dark)                              # rail spine
    for sx in (-1, 1):                                                           # two parallel rails
        gp.box((sx * 0.03, 0.58, bz + 0.01), (0.014, 0.60, 0.034), steel)
    gp.box((0, 0.875, bz + 0.004), (0.075, 0.03, 0.05), dark)                   # end cap
    for y in (0.36, 0.48, 0.60, 0.72):                                           # glowing coil rings
        gp.cyl((0, y, bz + 0.006), 0.05, 0.04, glow, axis="Y", segs=8, smooth=False)
    gp.cyl((0, 0.04, GZ + 0.085), 0.025, 0.26, dark, axis="Y", segs=8)           # scope tube
    gp.box((0, 0.04, GZ + 0.06), (0.02, 0.12, 0.03), dark)                       # scope mount
    gp.cyl((0, 0.17, GZ + 0.085), 0.026, 0.01, glow, axis="Y", segs=8)           # lens glow
    for sx in (-1, 1):                                                           # capacitor banks
        gp.box((sx * 0.05, 0.02, GZ - 0.01), (0.02, 0.22, 0.06), dark)
        gp.box((sx * 0.062, 0.02, GZ - 0.01), (0.004, 0.16, 0.02), glow)
    grip(gp, dark)
    gp.box((0, 0.14, GZ - 0.11), (0.045, 0.08, 0.14), gun, bevel=0.006,
           rot=Matrix.Rotation(math.radians(-8), 4, "X"))                        # cell magazine
    gp.box((0, -0.22, GZ - 0.015), (0.075, 0.26, 0.14), stock_m, bevel=0.014)    # heavy stock
    gp.box((0, -0.36, GZ - 0.03), (0.08, 0.05, 0.18), dark, bevel=0.01)          # butt plate
    gp.box((0, -0.16, GZ - 0.10), (0.05, 0.10, 0.05), dark)                      # stock underhook
    ob = make_object(root_name, gp, (0, 0, 0))
    make_empty("Muzzle", (0, 0.89, bz + 0.004), ob, size=0.08)
    return ob


def build_launcher(root_name="Gun"):
    green = mat("MAT_launcher", srgb(62, 84, 50), rough=0.6, metal=0.2)
    green_dark = mat("MAT_launcher_dark", srgb(40, 56, 34), rough=0.65, metal=0.2)
    dark = M_GUN_DARK()
    hz_y = mat("MAT_hazard_yellow", srgb(240, 200, 40), rough=0.6)
    hz_k = mat("MAT_hazard_black", srgb(32, 32, 34), rough=0.6)
    gp = Part()
    bz = GZ + 0.02
    R = 0.06
    gp.cyl((0, 0.30, bz), R, 0.60, green, axis="Y", segs=10)                     # main tube  y 0.0..0.60
    gp.cyl((0, 0.615, bz), R + 0.012, 0.05, green_dark, axis="Y", segs=10)       # muzzle ring  (tip y=0.64)
    gp.cyl((0, 0.635, bz), R - 0.015, 0.012, dark, axis="Y", segs=10)            # bore (dark disc at the tip)
    gp.cyl((0, -0.06, bz), R + 0.01, 0.06, green_dark, axis="Y", segs=10)        # breech ring
    for y in (0.45, 0.51):                                                       # hazard stripes
        gp.cyl((0, y, bz), R + 0.006, 0.025, hz_y, axis="Y", segs=10)
    gp.cyl((0, 0.48, bz), R + 0.006, 0.025, hz_k, axis="Y", segs=10)
    gp.box((0, 0.02, GZ - 0.03), (0.08, 0.28, 0.06), green_dark)                 # receiver under tube
    gp.cyl((0, 0.14, GZ - 0.10), 0.095, 0.085, green, axis="X", segs=10)         # drum magazine
    gp.cyl((0, 0.14, GZ - 0.10), 0.07, 0.095, green_dark, axis="X", segs=10)
    gp.cyl((0, 0.14, GZ - 0.10), 0.03, 0.10, hz_y, axis="X", segs=8)             # drum hub
    gp.box((0, 0.34, GZ - 0.045), (0.04, 0.05, 0.08), dark,
           rot=Matrix.Rotation(math.radians(10), 4, "X"))                        # fore-grip
    gp.box((0, 0.10, bz + 0.085), (0.03, 0.18, 0.02), green_dark)                # carry handle
    for y in (0.02, 0.18):
        gp.box((0, y, bz + 0.07), (0.02, 0.02, 0.03), green_dark)
    gp.box((0, 0.46, bz + 0.07), (0.012, 0.03, 0.04), dark)                      # front sight
    gp.box((0, 0.0, bz + 0.072), (0.02, 0.04, 0.025), dark)                      # rear sight
    grip(gp, dark, size=(0.05, 0.07, 0.12))
    gp.box((0, -0.22, GZ - 0.01), (0.07, 0.22, 0.12), green_dark, bevel=0.012)   # stock
    gp.box((0, -0.34, GZ - 0.02), (0.075, 0.04, 0.16), dark)                     # butt pad
    gp.box((0, -0.20, GZ + 0.055), (0.072, 0.10, 0.012), hz_y)                   # stripe on stock
    ob = make_object(root_name, gp, (0, 0, 0))
    make_empty("Muzzle", (0, 0.64, bz), ob, size=0.08)
    return ob


WEAPONS = {
    "weapon_rifle": build_rifle,
    "weapon_assault": build_assault,
    "weapon_plasma": build_plasma,
    "weapon_rail": build_rail,
    "weapon_launcher": build_launcher,
}


# ------------------------------------------------------------------ boss
def build_boss(root_name="Boss"):
    """5 m mutant super-zombie. Same part names / pivots as zombie.glb so the zombie animation drives it."""
    skin = mat("MAT_bossskin", srgb(94, 80, 108))
    skin_dark = mat("MAT_bossskin_dark", srgb(62, 52, 74))
    bone = mat("MAT_bone", srgb(224, 212, 178), rough=0.6)
    eye = mat("MAT_eye_red", srgb(255, 36, 24), rough=0.35)
    socket = mat("MAT_eye", srgb(20, 16, 22))
    pants = mat("MAT_bosspants", srgb(44, 38, 46), rough=0.9)
    leather = mat("MAT_leather", srgb(60, 42, 30))
    metal = mat("MAT_metal", srgb(150, 150, 155), rough=0.4, metal=0.8)
    mouth = mat("MAT_mouth_dark", srgb(40, 20, 26))

    root = make_empty(root_name, (0, 0, 0), size=0.5)
    hipz = 2.30
    hw, hd, hx = 1.28, 0.84, 0.42
    tw, td, th = 2.15, 1.30, 1.66
    lean = 24.0
    aw, L, hs_hand = 0.50, 2.55, 0.52
    lw, ld = 0.58, 0.62
    hs = 0.80
    hip_piv = V((0, 0, hipz))

    def chain(part, pts, size=0.11, m=metal):
        """Chain of alternating link boxes through pts (world coords)."""
        n = len(pts) - 1
        for i in range(n):
            a, b = V(pts[i]), V(pts[i + 1])
            part.bar(a, b, size * 0.45, size * 0.9 if i % 2 else size * 0.45, m, extend=0.0)

    # ---------- hips: pelvis + belt + hanging chain + ragged pant hem
    hp = Part()
    hp.box((0, 0, hipz - 0.22), (hw, hd, 0.56), pants, bevel=0.05)
    hp.box((0, 0, hipz + 0.06), (hw + 0.08, hd + 0.08, 0.16), leather, bevel=0.02)
    hp.box((0, hd * 0.5 + 0.06, hipz + 0.06), (0.22, 0.05, 0.14), metal)        # buckle
    for sx in (-1, 1):                                                           # ragged hem flaps
        hp.box((sx * hw * 0.3, hd * 0.5 - 0.02, hipz - 0.58), (0.32, 0.08, 0.26), pants, bevel=0.02)
        hp.box((sx * (hw * 0.5 - 0.02), -0.1, hipz - 0.55), (0.08, 0.3, 0.2), pants, bevel=0.02)
    pts = [(math.cos(math.pi * (1 - t)) * hw * 0.5, hd * 0.5 + 0.1, hipz - 0.05 - 0.45 * math.sin(math.pi * t))
           for t in [i / 8 for i in range(9)]]
    chain(hp, pts)                                                               # sagging belt chain
    hips = make_object("Hips", hp, hip_piv, root)

    # ---------- torso (upright, then leaned about the hip pivot)
    tp = Part()
    neck_z = hipz + th
    tp.box((0, 0.05, hipz + th * 0.5), (tw, td, th), skin, bevel=0.07)           # massive chest
    tp.box((0, td * 0.5 - 0.15, hipz + th * 0.26), (tw * 0.78, 0.55, 0.75), skin, bevel=0.1, smooth=True)  # gut
    tp.box((0, -td * 0.5 - 0.05, hipz + th * 0.62), (tw * 0.9, 0.5, th * 0.5), skin, bevel=0.1)          # hump
    for sx in (-1, 1):                                                           # trapezius slabs
        tp.box((sx * tw * 0.32, 0, neck_z - 0.1), (tw * 0.34, td * 0.8, 0.3), skin, bevel=0.06)
    # exposed ribs down the front
    tp.box((0, td * 0.5 + 0.04, hipz + th * 0.7), (0.16, 0.08, th * 0.42), bone, bevel=0.015)   # sternum
    for k, fz in enumerate((0.56, 0.66, 0.76, 0.86)):
        for sx in (-1, 1):
            tp.box((sx * tw * 0.2, td * 0.5 + 0.035, hipz + th * fz), (tw * 0.34, 0.07, 0.1), bone, bevel=0.015,
                   rot=Matrix.Rotation(math.radians(sx * 14), 4, "Y"))
    # bone armour plates + spikes on the shoulders
    for sx in (-1, 1):
        sxp = sx * (tw * 0.5 - 0.02)
        tp.box((sxp, 0, neck_z + 0.08), (0.78, 0.95, 0.32), bone, bevel=0.06)
        tp.box((sxp * 1.08, 0, neck_z - 0.1), (0.5, 0.8, 0.25), bone, bevel=0.05)
        tp.cyl((sxp + sx * 0.08, -0.1, neck_z + 0.5), 0.15, 0.85, bone, axis=(sx * 0.45, -0.15, 1.0), segs=8, r2=0.0)
        tp.cyl((sxp - sx * 0.12, 0.25, neck_z + 0.42), 0.11, 0.6, bone, axis=(sx * 0.25, 0.3, 1.0), segs=8, r2=0.0)
    # back plates + spine spikes
    for fz, w in ((0.3, 0.55), (0.52, 0.62), (0.74, 0.66), (0.94, 0.55)):
        tp.box((0, -td * 0.5 - 0.22, hipz + th * fz), (tw * w, 0.16, th * 0.17), bone, bevel=0.04)
    for fz, h in ((0.34, 0.75), (0.56, 0.95), (0.78, 1.0), (0.98, 0.85)):
        tp.cyl((0, -td * 0.5 - 0.3, hipz + th * fz + 0.1), 0.14, h, bone, axis=(0, -0.55, 1.0), segs=8, r2=0.0)
    # neck + iron collar with a chain down the chest
    tp.cyl((0, 0.05, neck_z + 0.08), 0.3, 0.36, skin, segs=10)
    tp.cyl((0, 0.05, neck_z + 0.1), 0.45, 0.16, metal, segs=12, smooth=False)
    for a in (-0.6, 0.0, 0.6):
        tp.cyl((0.45 * math.sin(a), 0.05 + 0.45 * math.cos(a), neck_z + 0.1), 0.05, 0.2, metal,
               axis=(math.sin(a), math.cos(a), 0), segs=6, r2=0.0)
    chain(tp, [(0.1, td * 0.5 + 0.5, neck_z - 0.02), (0.2, td * 0.5 + 0.12, neck_z - 0.35),
               (0.32, td * 0.5 + 0.1, neck_z - 0.7), (0.42, td * 0.5 + 0.12, neck_z - 1.0)], size=0.12)
    import bmesh
    R = Matrix.Rotation(math.radians(-lean), 4, "X")
    bmesh.ops.translate(tp.bm, vec=-hip_piv, verts=tp.bm.verts[:])
    bmesh.ops.transform(tp.bm, matrix=R, verts=tp.bm.verts[:])
    bmesh.ops.translate(tp.bm, vec=hip_piv, verts=tp.bm.verts[:])
    torso = make_object("Torso", tp, hip_piv, root)
    torso.parent = hips
    torso.matrix_parent_inverse = Matrix.Identity(4)
    torso.location = (0, 0, 0)

    shoulder = (tw * 0.5 + aw * 0.3, 0.05, neck_z - 0.12)
    neck = rot_about((0, 0.05, neck_z + 0.2), hip_piv, "X", -lean)
    shL = rot_about((-shoulder[0], shoulder[1], shoulder[2]), hip_piv, "X", -lean)
    shR = rot_about(shoulder, hip_piv, "X", -lean)

    # ---------- head
    hp = Part()
    tilt = 10
    Rh = Matrix.Rotation(math.radians(-tilt), 4, "X")
    c = neck + V((0, 0.06, hs * 0.5))
    def fp(x, y, z):
        return c + Rh @ V((x, y, z))
    hp.box(c, (hs, hs * 0.98, hs * 0.86), skin, bevel=0.04, rot=Rh)
    fy = hs * 0.49
    hp.box(fp(0, fy - 0.02, hs * 0.27), (hs * 0.92, 0.12, 0.16), skin_dark, bevel=0.02, rot=Rh)   # brow ridge
    for sx in (-1, 1):                                                           # sunken sockets + glowing eyes
        hp.box(fp(sx * hs * 0.24, fy - 0.01, hs * 0.12), (0.26, 0.06, 0.2), socket, rot=Rh)
        hp.box(fp(sx * hs * 0.24, fy + 0.03, hs * 0.12), (0.19, 0.06, 0.13), eye, rot=Rh)
    hp.box(fp(0, fy + 0.01, -hs * 0.02), (0.08, 0.05, 0.1), skin_dark, rot=Rh)   # nose
    hp.box(fp(0, fy - 0.03, -hs * 0.33), (hs * 0.6, hs * 0.5, hs * 0.16), mouth, rot=Rh)      # mouth cavity
    hp.box(fp(0, fy - 0.1, -hs * 0.5), (hs * 0.7, hs * 0.66, hs * 0.18), skin, bevel=0.03, rot=Rh)  # jaw
    for sx in (-1, 1):                                                           # tusks
        hp.cyl(fp(sx * hs * 0.26, fy + 0.02, -hs * 0.28), 0.045, 0.26, bone, axis=(0, 0.15, 1), segs=6, r2=0.0)
    for sx in (-1, 1):                                                           # horns
        hp.cyl(fp(sx * hs * 0.3, -hs * 0.2, hs * 0.5), 0.09, 0.38, bone, axis=(sx * 0.3, -0.45, 1), segs=7, r2=0.0)
    head = make_object("Head", hp, neck, torso)

    # ---------- arms: long, raised forward, bone spurs, claws, shackle + chain on the right
    for name, sh, sx in (("ArmL", shL, -1), ("ArmR", shR, 1)):
        spread = 0.12
        elbow = V((sh.x + sx * spread, sh.y + L * 0.48, sh.z - 0.12))
        hand = V((sh.x + sx * spread * 1.6, sh.y + L, sh.z - 0.08))
        ap = Part()
        limb(ap, [sh, elbow, hand], aw, aw, skin, bevel=0.03, taper=0.86)
        ap.box((sh + elbow) * 0.5 + V((0, 0, 0.04)), (aw * 1.2, L * 0.3, aw * 1.15), skin, bevel=0.08, smooth=True)  # bicep
        for k, t in enumerate((0.18, 0.32)):                                     # bone spurs on the upper arm
            p0 = sh.lerp(elbow, t)
            ap.cyl(p0 + V((sx * aw * 0.4, 0, 0.1)), 0.08 - 0.02 * k, 0.4 - 0.08 * k, bone,
                   axis=(sx * 1.0, -0.2, 0.7), segs=6, r2=0.0)
        hsz = hs_hand
        ap.box(hand + V((0, hsz * 0.3, 0)), (hsz, hsz * 1.1, hsz * 0.55), skin, bevel=0.03)
        for fx in (-0.32, 0.0, 0.32):                                            # fingers + bone claws
            fb = hand + V((fx * hsz, hsz * 0.85, -hsz * 0.1))
            ap.box(fb, (hsz * 0.22, hsz * 0.32, hsz * 0.22), skin, bevel=0.01)
            ap.cyl(fb + V((0, hsz * 0.3, -0.04)), 0.045, 0.3, bone, axis=(0, 1.0, -0.35), segs=6, r2=0.0)
        if sx == 1:                                                              # shackle + trailing chain
            wrist = hand - V((0, 0.12, 0))
            ap.cyl(wrist, aw * 0.5, 0.14, metal, axis="Y", segs=10, smooth=False)
            chain(ap, [wrist + V((0, -0.05, -aw * 0.45)), wrist + V((0, -0.25, -aw * 0.45 - 0.3)),
                       wrist + V((0, -0.5, -aw * 0.45 - 0.55))], size=0.12)
        make_object(name, ap, sh, torso)

    # ---------- legs: pant-covered thigh, bare shin, huge clawed feet
    for name, sx in (("LegL", -1), ("LegR", 1)):
        x = sx * hx
        lg = Part()
        hip = V((x, 0, hipz)); knee = V((x, 0.1, hipz * 0.5)); ankle = V((x, 0.0, 0.3))
        lg.bar(hip, knee, lw, ld, pants, bevel=0.03, extend=0.02)
        lg.box(knee, (lw * 0.98, ld * 0.98, lw * 0.98), pants, bevel=0.03)
        lg.box(knee - V((0, 0, 0.22)), (lw * 1.05, ld * 1.05, 0.18), pants, bevel=0.02)   # torn cuff
        lg.box(knee + V((sx * lw * 0.3, ld * 0.3, -0.38)), (0.2, 0.2, 0.2), pants, bevel=0.02)  # hanging shred
        lg.bar(knee, ankle, lw * 0.88, ld * 0.88, skin, bevel=0.03, extend=0.02)
        lg.cyl(knee + V((0, ld * 0.5, 0)), 0.07, 0.3, bone, axis=(0, 1, 0.3), segs=6, r2=0.0)  # knee spur
        lg.box((x, 0.16, 0.19), (lw + 0.12, ld + 0.5, 0.38), skin, bevel=0.05)              # foot
        for fx in (-0.33, 0.0, 0.33):
            lg.cyl((x + fx * (lw + 0.1), 0.16 + (ld + 0.5) * 0.5, 0.12), 0.06, 0.26, bone,
                   axis=(0, 1, -0.15), segs=6, r2=0.0)
        make_object(name, lg, hip, hips)
    return root


# ------------------------------------------------------------------ previews / main
def preview_weapon(filename, build, view=(-1.0, 0.9, 0.55)):
    """Weapon render with a floor slab below the gun and a red marker ball on the Muzzle empty."""
    lp.reset_scene()
    gun = build()
    mark = Part()
    muzzle = [c for c in gun.children if c.name == "Muzzle"][0]
    mark.sphere(lp.world_loc(muzzle), 0.014, mat("_muzzle_marker", srgb(255, 30, 30)), segs=8, rings=5)
    make_object("_muzzle_marker", mark)
    floor = Part()
    floor.box((0, 0.2, -0.3), (3, 3, 0.1), mat("_ground", (0.62, 0.62, 0.60)))
    make_object("_ground", floor)
    lp.render_preview(filename, view=view, lens=60, ground=False, objs=[gun], zoom=1.05)


def weapons_lineup():
    lp.reset_scene()
    guns = []
    for i, (key, fn) in enumerate(WEAPONS.items()):
        g = fn()
        g.name = key
        g.location.x = -0.5 + i * 0.25
        g.location.z = 0.3
        guns.append(g)
        mark = Part()
        muzzle = [c for c in g.children if c.name.startswith("Muzzle")][0]
        bpy.context.view_layer.update()
        mark.sphere(muzzle.matrix_world.translation, 0.014, mat("_muzzle_marker", srgb(255, 30, 30)), segs=8, rings=5)
        make_object("_mark_" + key, mark)
    lp.render_preview("weapons_lineup.png", view=(-0.55, 1.0, 0.75), lens=50, ground=True, objs=guns, zoom=0.95)


def boss_vs_zombie():
    lp.reset_scene()
    boss = build_boss("Boss")
    boss.location.x = 1.6
    z = build_humanoid("Zombie_ref", zombie_params())
    z.location.x = -1.6
    lp.render_preview("boss_vs_zombie.png", view=(0.45, 1.0, 0.45), lens=50, zoom=0.95)


import bpy  # noqa: E402  (after lp so that the factory reset helpers exist)

if __name__ == "__main__":
    keys = ONLY or ["gate"] + list(WEAPONS) + ["boss", "weapons_lineup", "boss_vs_zombie"]
    for k in keys:
        if k == "gate":
            lp.reset_scene()
            root = build_gate()
            lp.export_glb("gate.glb", [root])
            lp.dump_tree(root)
            lp.render_preview("gate.png", view=(-1.0, -1.3, 0.75), lens=50)
        elif k in WEAPONS:
            lp.reset_scene()
            root = WEAPONS[k]()
            lp.export_glb(f"{k}.glb", [root])
            lp.dump_tree(root)
            preview_weapon(f"{k}.png", WEAPONS[k])
        elif k == "boss":
            lp.reset_scene()
            root = build_boss()
            lp.export_glb("boss.glb", [root])
            lp.dump_tree(root)
            lp.render_preview("boss.png", view=(1.0, 1.1, 0.5), lens=50)
        elif k == "weapons_lineup":
            weapons_lineup()
        elif k == "boss_vs_zombie":
            boss_vs_zombie()
