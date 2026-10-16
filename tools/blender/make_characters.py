"""Soldier / Zombie / Zombie brute: split-part characters for procedural animation in Godot."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import Part, V, mat, srgb, make_object, make_empty
from mathutils import Matrix

ONLY = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []


def rot_about(p, pivot, ax, deg):
    """Rotate world point p about `pivot` around axis ax by deg degrees."""
    R = Matrix.Rotation(math.radians(deg), 4, ax)
    return V(pivot) + R @ (V(p) - V(pivot))


def limb(part, pts, w, d, m, joint_m=None, bevel=0.01, taper=1.0):
    """Chain of bars through pts with joint cubes at interior points."""
    for i in range(len(pts) - 1):
        f = 1.0 if i == 0 else taper
        part.bar(pts[i], pts[i + 1], w * f, d * f, m, bevel=bevel, extend=0.01)
    for i in range(1, len(pts) - 1):
        part.box(pts[i], (w * 0.96, d * 0.96, w * 0.96), joint_m or m, bevel=bevel)


# ------------------------------------------------------------------ generic humanoid
def build_humanoid(root_name, P):
    """P: dict of dimensions / colours / pose. Returns root empty."""
    root = make_empty(root_name, (0, 0, 0), size=0.3)
    hipz = P["hip_z"]
    lean = P.get("lean", 0.0)             # torso forward lean (deg, +ve = forward)
    hip_piv = V((0, 0, hipz))

    # ---------- hips
    hp = Part()
    hw, hd = P["hip_w"], P["hip_d"]
    hp.box((0, 0, hipz - 0.05), (hw, hd, 0.16), P["m_pants"], bevel=0.015)
    hp.box((0, 0, hipz + 0.025), (hw + 0.03, hd + 0.03, 0.06), P["m_belt"], bevel=0.008)
    hp.box((0, hd * 0.5 + 0.02, hipz + 0.025), (0.07, 0.02, 0.05), P["m_metal"])  # buckle
    hips = make_object("Hips", hp, hip_piv, root)

    # ---------- torso (built upright then leaned about the hip pivot)
    tw, td, th = P["torso_w"], P["torso_d"], P["torso_h"]
    tp = Part()
    tp.box((0, 0, hipz + th * 0.5), (tw, td, th), P["m_shirt"], bevel=0.02)
    neck_z = hipz + th
    shoulder = (tw * 0.5 + P["arm_w"] * 0.35, 0.0, neck_z - 0.06)
    if P.get("vest"):
        vw, vd = tw + 0.04, td + 0.08
        tp.box((0, 0, hipz + th * 0.5 - 0.02), (vw, vd, th * 0.78), P["m_vest"], bevel=0.015)
        # pouches on the front (+Y)
        for x in (-0.15, 0.0, 0.15):
            tp.box((x, vd * 0.5 + 0.035, hipz + th * 0.28), (0.12, 0.08, 0.13), P["m_vest_dark"], bevel=0.01)
        tp.box((0, vd * 0.5 + 0.02, hipz + th * 0.62), (0.16, 0.04, 0.08), P["m_vest_dark"], bevel=0.006)  # radio
        # shoulder straps / pads
        for sx in (-1, 1):
            tp.box((sx * (tw * 0.5 - 0.02), 0, neck_z - 0.02), (0.17, td + 0.02, 0.07), P["m_shirt_dark"], bevel=0.01)
    if P.get("torn"):
        # torn shirt: ragged hem + skin showing through
        tp.box((0.06, td * 0.5 - 0.005, hipz + th * 0.3), (0.16, 0.03, 0.12), P["m_skin"])
        tp.box((-0.14, td * 0.5 - 0.005, hipz + th * 0.12), (0.10, 0.03, 0.09), P["m_skin"])
        tp.box((-0.1, -td * 0.5 + 0.005, hipz + th * 0.55), (0.12, 0.03, 0.10), P["m_skin"])
        tp.box((tw * 0.5 - 0.005, 0.02, hipz + th * 0.2), (0.03, 0.08, 0.10), P["m_skin"])
        for sx in (-1, 1):   # short sleeves
            tp.box((sx * (tw * 0.5 + 0.02), 0, neck_z - 0.07), (0.16, td * 0.9, 0.10), P["m_shirt"], bevel=0.01)
    # neck
    tp.cyl((0, 0, neck_z + 0.02), P["neck_r"], 0.1, P["m_skin"], segs=8)
    if lean:
        R = Matrix.Rotation(math.radians(-lean), 4, "X")
        import bmesh
        bmesh.ops.translate(tp.bm, vec=-hip_piv, verts=tp.bm.verts[:])
        bmesh.ops.transform(tp.bm, matrix=R, verts=tp.bm.verts[:])
        bmesh.ops.translate(tp.bm, vec=hip_piv, verts=tp.bm.verts[:])
    torso = make_object("Torso", tp, hip_piv, root)
    torso.parent = hips
    torso.matrix_parent_inverse = Matrix.Identity(4)
    torso.location = (0, 0, 0)

    neck = rot_about((0, 0, neck_z + 0.04), hip_piv, "X", -lean)
    shL = rot_about((-shoulder[0], shoulder[1], shoulder[2]), hip_piv, "X", -lean)
    shR = rot_about(shoulder, hip_piv, "X", -lean)

    # ---------- head
    head = P["head"](P, neck, torso)

    # ---------- arms
    P["arms"](P, shL, shR, torso)

    # ---------- legs
    lw, ld = P["leg_w"], P["leg_d"]
    for name, sx in (("LegL", -1), ("LegR", 1)):
        hx = sx * P["hip_x"]
        lg = Part()
        knee = (hx, 0.02, hipz * 0.52)
        ankle = (hx, 0.0, 0.11)
        limb(lg, [(hx, 0, hipz), knee, ankle], lw, ld, P["m_pants"], bevel=0.012, taper=0.88)
        if P.get("kneepad"):
            lg.box((hx, ld * 0.5 + 0.0, hipz * 0.52), (lw * 0.8, 0.05, 0.12), P["m_vest_dark"], bevel=0.01)
        bw, bl, bh = lw + 0.03, ld + 0.14, 0.13
        lg.box((hx, 0.05, bh * 0.5), (bw, bl, bh), P["m_boot"], bevel=0.02)
        lg.box((hx, 0.0, bh + 0.03), (lw * 0.9, ld * 0.9, 0.06), P["m_boot"], bevel=0.01)  # ankle cuff
        make_object(name, lg, (hx, 0, hipz), hips)
    return root


# ------------------------------------------------------------------ heads
def head_soldier(P, neck, torso):
    hp = Part()
    nz = neck.z
    hs = P["head_s"]
    hp.box((0, 0.01, nz + hs * 0.5), (hs, hs * 0.92, hs), P["m_skin"], bevel=0.02)
    fy = 0.01 + hs * 0.46
    for sx in (-1, 1):   # eyes
        hp.box((sx * hs * 0.2, fy, nz + hs * 0.56), (0.05, 0.025, 0.045), P["m_eye"])
        hp.box((sx * hs * 0.2, fy, nz + hs * 0.65), (0.07, 0.02, 0.02), P["m_hair"])  # brows
    hp.box((0, fy + 0.01, nz + hs * 0.42), (0.05, 0.04, 0.06), P["m_skin"])            # nose
    hp.box((0, fy, nz + hs * 0.22), (0.10, 0.015, 0.025), P["m_mouth"])                 # mouth
    # helmet: dome box + brim + strap
    hp.box((0, 0, nz + hs * 0.98), (hs + 0.07, hs * 0.92 + 0.07, hs * 0.5), P["m_helmet"], bevel=0.04)
    hp.box((0, 0.01, nz + hs * 0.75), (hs + 0.11, hs * 0.92 + 0.12, 0.035), P["m_helmet"], bevel=0.01)
    hp.box((0, 0, nz + hs * 0.88), (hs + 0.075, hs * 0.92 + 0.075, 0.05), P["m_helmet_band"])
    for sx in (-1, 1):   # chin strap
        hp.box((sx * (hs * 0.5 + 0.005), 0.0, nz + hs * 0.4), (0.012, 0.03, hs * 0.7), P["m_belt"])
    return make_object("Head", hp, neck, torso)


def head_zombie(P, neck, torso):
    hp = Part()
    nz = neck.z
    hs = P["head_s"]
    tilt = P.get("head_tilt", 10)
    cz = nz + hs * 0.52
    # skull (slightly forward-tilted)
    R = Matrix.Rotation(math.radians(-tilt), 4, "X")
    c = V((0, 0.02, cz))
    hp.box(c, (hs, hs * 0.95, hs * 0.82), P["m_skin"], bevel=0.02, rot=R)
    fy = hs * 0.47
    def fp(x, y, z):  # face-local -> world (tilt about head centre)
        return c + R @ V((x, y, z))
    for sx in (-1, 1):   # hollow eyes
        hp.box(fp(sx * hs * 0.21, fy, hs * 0.14), (0.07, 0.03, 0.06), P["m_eye"], rot=R)
    hp.box(fp(0, fy + 0.005, hs * 0.02), (0.04, 0.03, 0.05), P["m_skin_dark"], rot=R)  # nose
    # slack jaw: dark mouth cavity + hanging lower jaw
    hp.box(fp(0, fy - 0.03, -hs * 0.34), (hs * 0.55, hs * 0.5, hs * 0.14), P["m_mouth"], rot=R)
    hp.box(fp(0, fy - 0.1, -hs * 0.52), (hs * 0.62, hs * 0.62, hs * 0.16), P["m_skin"], bevel=0.015, rot=R)
    # patchy hair
    hp.box(fp(0.04, -0.03, hs * 0.44), (hs * 0.7, hs * 0.6, 0.05), P["m_hair"], rot=R)
    hp.box(fp(-0.1, 0.06, hs * 0.42), (hs * 0.3, hs * 0.3, 0.04), P["m_hair"], rot=R)
    if P.get("brute"):
        for sx in (-1, 1):  # jaw tusks / brow ridge for the brute
            hp.box(fp(sx * hs * 0.21, fy, hs * 0.24), (0.11, 0.04, 0.035), P["m_skin_dark"], rot=R)
    return make_object("Head", hp, neck, torso)


# ------------------------------------------------------------------ arms
def arms_soldier(P, shL, shR, torso):
    aw, ad = P["arm_w"], P["arm_d"]
    # right arm (+X): grips the rifle pistol grip
    eR = (shR.x + 0.03, shR.y + 0.2, shR.z - 0.22)
    hR = V((0.13, shR.y + 0.44, shR.z - 0.15))
    ap = Part()
    limb(ap, [shR, eR, hR], aw, ad, P["m_shirt"], taper=0.9)
    ap.box(hR, (0.13, 0.12, 0.15), P["m_glove"], bevel=0.02)
    armR = make_object("ArmR", ap, shR, torso)
    # left arm (-X): supports the handguard
    eL = (shL.x + 0.02, shL.y + 0.28, shL.z - 0.2)
    hL = V((0.10, shL.y + 0.76, shR.z - 0.12))
    ap = Part()
    limb(ap, [shL, eL, hL], aw, ad, P["m_shirt"], taper=0.9)
    ap.box(hL, (0.13, 0.14, 0.14), P["m_glove"], bevel=0.02)
    make_object("ArmL", ap, shL, torso)
    # rifle (child of right arm, origin at the right hand). Barrel runs along +Y.
    gx, gz = 0.13, hR.z + 0.08
    y0 = hR.y
    gp = Part()
    gp.box((gx, y0 + 0.05, gz), (0.07, 0.36, 0.09), P["m_gun"], bevel=0.01)             # receiver
    gp.box((gx, y0 + 0.31, gz - 0.005), (0.065, 0.22, 0.075), P["m_gun_dark"], bevel=0.008)  # handguard
    gp.cyl((gx, y0 + 0.51, gz + 0.012), 0.018, 0.22, P["m_gun"], axis="Y", segs=8)      # barrel
    gp.cyl((gx, y0 + 0.60, gz + 0.012), 0.027, 0.06, P["m_gun_dark"], axis="Y", segs=8) # muzzle brake
    gp.box((gx, y0 + 0.40, gz + 0.06), (0.014, 0.02, 0.04), P["m_gun"])                 # front sight
    gp.box((gx, y0 + 0.0, gz + 0.065), (0.035, 0.10, 0.035), P["m_gun_dark"], bevel=0.005)  # rear sight / rail
    gp.box((gx, y0 - 0.0, gz - 0.09), (0.045, 0.065, 0.12), P["m_gun_dark"], bevel=0.006)   # pistol grip (in hand)
    gp.box((gx, y0 + 0.14, gz - 0.115), (0.045, 0.075, 0.17), P["m_gun"], bevel=0.006,
           rot=Matrix.Rotation(math.radians(-12), 4, "X"))                                # magazine
    gp.box((gx, y0 - 0.23, gz - 0.01), (0.055, 0.22, 0.10), P["m_stock"], bevel=0.012)   # stock
    gp.box((gx, y0 - 0.34, gz - 0.02), (0.06, 0.04, 0.14), P["m_stock"], bevel=0.008)    # butt plate
    gun = make_object("Gun", gp, hR, armR)
    muzzle_tip = V((gx, y0 + 0.63, gz + 0.012))
    make_empty("Muzzle", muzzle_tip, gun, size=0.08)
    return gun


def arms_zombie(P, shL, shR, torso):
    aw, ad = P["arm_w"], P["arm_d"]
    L = P["arm_len"]
    for name, sh, sx in (("ArmL", shL, -1), ("ArmR", shR, 1)):
        spread = P.get("arm_spread", 0.02)
        elbow = (sh.x + sx * spread, sh.y + L * 0.5, sh.z - 0.03)
        hand = V((sh.x + sx * spread * 1.6, sh.y + L, sh.z - 0.02))
        ap = Part()
        limb(ap, [sh, elbow, hand], aw, ad, P["m_skin"], taper=0.9)
        if P.get("sleeve_m"):
            ap.box((sh.x, sh.y + 0.0, sh.z - 0.0), (aw + 0.03, ad + 0.03, 0.13), P["sleeve_m"], bevel=0.01,
                   rot=Matrix.Rotation(math.radians(90), 4, "X"))
        hs = P["hand_s"]
        ap.box(hand + V((0, hs * 0.3, 0)), (hs, hs * 1.1, hs * 0.55), P["m_skin"], bevel=0.015)
        # fingers: three stubby boxes curling down
        for i, fx in enumerate((-0.3, 0.0, 0.3)):
            ap.box(hand + V((fx * hs, hs * 0.85, -hs * 0.12)), (hs * 0.22, hs * 0.3, hs * 0.22), P["m_skin"], bevel=0.005)
        make_object(name, ap, sh, torso)


# ------------------------------------------------------------------ palettes
def soldier_params():
    return dict(
        hip_z=0.95, hip_w=0.44, hip_d=0.28, hip_x=0.13,
        torso_w=0.50, torso_d=0.30, torso_h=0.50, neck_r=0.07,
        arm_w=0.15, arm_d=0.15, leg_w=0.19, leg_d=0.21, head_s=0.30,
        vest=True, kneepad=True, lean=0.0,
        head=head_soldier, arms=arms_soldier,
        m_skin=mat("MAT_skin", srgb(240, 190, 150)),
        m_shirt=mat("MAT_uniform", srgb(112, 142, 72)),
        m_shirt_dark=mat("MAT_uniform_dark", srgb(82, 106, 54)),
        m_pants=mat("MAT_uniform", srgb(112, 142, 72)),
        m_vest=mat("MAT_vest", srgb(210, 178, 120)),
        m_vest_dark=mat("MAT_vest_dark", srgb(160, 132, 84)),
        m_belt=mat("MAT_leather", srgb(72, 50, 34)),
        m_boot=mat("MAT_boot", srgb(42, 36, 34)),
        m_glove=mat("MAT_leather", srgb(72, 50, 34)),
        m_helmet=mat("MAT_helmet", srgb(92, 118, 60)),
        m_helmet_band=mat("MAT_uniform_dark", srgb(82, 106, 54)),
        m_eye=mat("MAT_eye", srgb(28, 24, 30)),
        m_hair=mat("MAT_hair", srgb(60, 42, 30)),
        m_mouth=mat("MAT_mouth", srgb(150, 90, 80)),
        m_metal=mat("MAT_metal", srgb(150, 150, 155), rough=0.4, metal=0.8),
        m_gun=mat("MAT_gun", srgb(58, 60, 66), rough=0.5, metal=0.6),
        m_gun_dark=mat("MAT_gun_dark", srgb(34, 36, 40), rough=0.5, metal=0.6),
        m_stock=mat("MAT_stock", srgb(92, 66, 44)),
    )


def zombie_params():
    return dict(
        hip_z=0.93, hip_w=0.40, hip_d=0.26, hip_x=0.12,
        torso_w=0.46, torso_d=0.28, torso_h=0.50, neck_r=0.06,
        arm_w=0.13, arm_d=0.13, arm_len=0.62, hand_s=0.14, leg_w=0.17, leg_d=0.19, head_s=0.30,
        torn=True, lean=16.0, head_tilt=12,
        head=head_zombie, arms=arms_zombie,
        m_skin=mat("MAT_zskin", srgb(150, 178, 132)),
        m_skin_dark=mat("MAT_zskin_dark", srgb(104, 126, 92)),
        m_shirt=mat("MAT_zshirt", srgb(70, 110, 170)),
        m_pants=mat("MAT_zpants", srgb(116, 86, 58)),
        m_belt=mat("MAT_leather", srgb(60, 42, 30)),
        m_boot=mat("MAT_boot", srgb(48, 42, 40)),
        m_eye=mat("MAT_eye", srgb(20, 18, 22)),
        m_hair=mat("MAT_zhair", srgb(44, 38, 36)),
        m_mouth=mat("MAT_mouth_dark", srgb(40, 24, 30)),
        m_metal=mat("MAT_metal", srgb(150, 150, 155), rough=0.4, metal=0.8),
        sleeve_m=None,
    )


def brute_params():
    p = zombie_params()
    p.update(
        hip_z=1.22, hip_w=0.72, hip_d=0.42, hip_x=0.22,
        torso_w=1.00, torso_d=0.56, torso_h=0.74, neck_r=0.11,
        arm_w=0.26, arm_d=0.26, arm_len=0.95, arm_spread=0.06, hand_s=0.26,
        leg_w=0.30, leg_d=0.32, head_s=0.38, lean=12.0, head_tilt=8, brute=True,
        m_skin=mat("MAT_bskin", srgb(96, 118, 86)),
        m_skin_dark=mat("MAT_bskin_dark", srgb(68, 86, 60)),
        m_shirt=mat("MAT_zshirt", srgb(52, 76, 120)),
        m_pants=mat("MAT_zpants", srgb(86, 62, 44)),
        m_eye=mat("MAT_eye_red", srgb(230, 40, 30), rough=0.4),
    )
    return p


BUILDERS = {
    "soldier": ("Soldier", soldier_params, (1.0, 1.1, 0.5)),
    "zombie": ("Zombie", zombie_params, (1.0, 1.1, 0.5)),
    "zombie_brute": ("Zombie", brute_params, (1.0, 1.1, 0.5)),
}


def build(key):
    root_name, params, view = BUILDERS[key]
    lp.reset_scene()
    root = build_humanoid(root_name, params())
    lp.export_glb(f"{key}.glb", [root])
    lp.dump_tree(root)
    lp.render_preview(f"{key}.png", view=view, lens=50)


def lineup():
    lp.reset_scene()
    xs = {"soldier": -1.6, "zombie": 0.2, "zombie_brute": 2.2}
    for key, x in xs.items():
        root_name, params, _ = BUILDERS[key]
        root = build_humanoid(root_name + "_" + key, params())
        root.location.x = x
    lp.render_preview("characters_lineup.png", view=(0.35, 1.0, 0.45), lens=50, zoom=0.95)


if __name__ == "__main__":
    keys = ONLY or list(BUILDERS) + ["lineup"]
    for k in keys:
        if k == "lineup":
            lineup()
        else:
            build(k)
