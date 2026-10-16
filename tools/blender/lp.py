"""Shared low-poly helpers for the Lane Rush asset generators (Blender 5.x, headless).

Conventions (see ASSET_SPEC.md): 1 BU = 1 m, +Y forward, +Z up, origin at ground.
Geometry is built in WORLD coordinates with a `Part`, then turned into an object whose
origin (pivot) is placed at the requested world point; the mesh verts are made local to
that pivot, so Godot can rotate the part around its joint.
"""
import os
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(ROOT, "assets", "models")
PREVIEW_DIR = os.environ.get(
    "PREVIEW_DIR",
    os.path.join(ROOT, ".previews"),
)

V = Vector


# --------------------------------------------------------------------------- scene / materials
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    return sc


def mat(name, rgb, rough=0.7, metal=0.0):
    """Principled BSDF material, base colour only. Cached by name within the scene."""
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    # viewport / Workbench display
    m.diffuse_color = (*rgb, 1.0)
    m.roughness = rough
    m.metallic = min(metal, 0.35)   # Workbench previews only: full metallic renders near-black
    return m


def srgb(r, g, b):
    """Convert 0-255 sRGB to linear floats (what Principled base colour expects)."""
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# --------------------------------------------------------------------------- geometry builder
def _rot_z_to(direction):
    d = V(direction)
    if d.length < 1e-9:
        return Matrix.Identity(4)
    return V((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()


class Part:
    """Accumulates primitives (in world coords) into one bmesh with per-face materials."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    # -- internal
    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _commit(self, tbm, m, smooth=False, bevel=0.0, matrix=None):
        if bevel > 0:
            bmesh.ops.bevel(
                tbm, geom=tbm.verts[:] + tbm.edges[:] + tbm.faces[:], offset=bevel,
                offset_type="OFFSET", segments=1, profile=0.5, affect="EDGES",
                clamp_overlap=True, loop_slide=True,
            )
        if matrix is not None:
            bmesh.ops.transform(tbm, matrix=matrix, verts=tbm.verts[:])
        bmesh.ops.recalc_face_normals(tbm, faces=tbm.faces[:])
        mi = self._mi(m)
        for f in tbm.faces:
            f.material_index = mi
            f.smooth = smooth
        tmp = bpy.data.meshes.new("_tmp")
        tbm.to_mesh(tmp)
        tbm.free()
        self.bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)

    # -- primitives
    def box(self, center, size, m, bevel=0.0, rot=None, smooth=False):
        """Axis-aligned box (optionally rotated by Matrix `rot` about its centre)."""
        tbm = bmesh.new()
        bmesh.ops.create_cube(tbm, size=1.0)
        sx, sy, sz = size
        bmesh.ops.scale(tbm, vec=(sx, sy, sz), verts=tbm.verts[:])
        M = Matrix.Translation(V(center)) @ (rot if rot is not None else Matrix.Identity(4))
        self._commit(tbm, m, smooth=smooth, bevel=bevel, matrix=M)
        return self

    def bar(self, a, b, w, d, m, bevel=0.0, extend=0.0, smooth=False):
        """Box of cross-section w (x) by d (y) running from point a to point b."""
        a, b = V(a), V(b)
        dirv = b - a
        L = dirv.length + 2 * extend
        tbm = bmesh.new()
        bmesh.ops.create_cube(tbm, size=1.0)
        bmesh.ops.scale(tbm, vec=(w, d, L), verts=tbm.verts[:])
        M = Matrix.Translation((a + b) * 0.5) @ _rot_z_to(dirv)
        self._commit(tbm, m, smooth=smooth, bevel=bevel, matrix=M)
        return self

    def cyl(self, center, r, h, m, axis="Z", segs=12, r2=None, smooth=True, bevel=0.0):
        """Cylinder / truncated cone of radius r (bottom) and r2 (top) along `axis`."""
        tbm = bmesh.new()
        bmesh.ops.create_cone(
            tbm, cap_ends=True, cap_tris=False, segments=segs,
            radius1=r, radius2=(r if r2 is None else r2), depth=h,
        )
        if axis == "X":
            R = Matrix.Rotation(math.radians(90), 4, "Y")
        elif axis == "Y":
            R = Matrix.Rotation(math.radians(-90), 4, "X")
        elif isinstance(axis, (tuple, list, Vector)):
            R = _rot_z_to(axis)
        else:
            R = Matrix.Identity(4)
        M = Matrix.Translation(V(center)) @ R
        self._commit(tbm, m, smooth=smooth, bevel=bevel, matrix=M)
        return self

    def sphere(self, center, r, m, segs=10, rings=6, scale=(1, 1, 1), smooth=True):
        tbm = bmesh.new()
        bmesh.ops.create_uvsphere(tbm, u_segments=segs, v_segments=rings, radius=r)
        bmesh.ops.scale(tbm, vec=scale, verts=tbm.verts[:])
        self._commit(tbm, m, smooth=smooth, matrix=Matrix.Translation(V(center)))
        return self

    def prism(self, profile, axis, a0, a1, m, offset=(0, 0, 0), bevel=0.0, smooth=False):
        """Extrude a closed 2D polygon along `axis` ('X','Y' or 'Z') from a0 to a1.
        profile: list of (u, v) where (u, v) are the other two axes in right-handed order:
        axis X -> (y, z); axis Y -> (z, x); axis Z -> (x, y)."""
        tbm = bmesh.new()
        def to3(u, v, t):
            if axis == "X":
                return V((t, u, v))
            if axis == "Y":
                return V((v, t, u))
            return V((u, v, t))
        v0 = [tbm.verts.new(to3(u, v, a0)) for (u, v) in profile]
        v1 = [tbm.verts.new(to3(u, v, a1)) for (u, v) in profile]
        n = len(profile)
        tbm.faces.new(v0[::-1])
        tbm.faces.new(v1)
        for i in range(n):
            j = (i + 1) % n
            tbm.faces.new((v0[i], v0[j], v1[j], v1[i]))
        self._commit(tbm, m, smooth=smooth, bevel=bevel, matrix=Matrix.Translation(V(offset)))
        return self

    def face_quad(self, center, size, normal, m):
        """A single quad (2 tris) of size (w, h) facing `normal` ('+X','-X','+Y','-Y','+Z','-Z').
        Cheap decal for windows / markings; w runs along the face's horizontal axis."""
        w, h = size
        sign = 1 if normal[0] == "+" else -1
        ax = normal[1]
        c = V(center)
        if ax == "X":
            u, v = V((0, 1, 0)), V((0, 0, 1))
        elif ax == "Y":
            u, v = V((1, 0, 0)), V((0, 0, 1))
        else:
            u, v = V((1, 0, 0)), V((0, 1, 0))
        n = {"X": V((1, 0, 0)), "Y": V((0, 1, 0)), "Z": V((0, 0, 1))}[ax] * sign
        tbm = bmesh.new()
        pts = [c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2, c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2]
        f = tbm.faces.new([tbm.verts.new(q) for q in pts])
        tbm.faces.ensure_lookup_table()
        if f.normal.dot(n) < 0:
            bmesh.ops.reverse_faces(tbm, faces=[f])
        mi = self._mi(m)
        for fc in tbm.faces:
            fc.material_index = mi
            fc.smooth = False
        tmp = bpy.data.meshes.new("_tmp")
        tbm.to_mesh(tmp)
        tbm.free()
        self.bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        return self


# --------------------------------------------------------------------------- objects
def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def world_loc(ob):
    p, o = V((0, 0, 0)), ob
    while o is not None:
        p += o.location
        o = o.parent
    return p


def _parent(ob, parent, pivot):
    pivot = V(pivot)
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = pivot - world_loc(parent)
    else:
        ob.location = pivot


def make_object(name, part, pivot=(0, 0, 0), parent=None):
    """Turn a Part into a mesh object whose origin sits at world point `pivot`."""
    bm = part.bm
    bmesh.ops.translate(bm, vec=-V(pivot), verts=bm.verts[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in part.mats:
        me.materials.append(m)
    me.validate()
    ob = _link(bpy.data.objects.new(name, me))
    _parent(ob, parent, pivot)
    return ob


def make_empty(name, pivot=(0, 0, 0), parent=None, size=0.1):
    ob = _link(bpy.data.objects.new(name, None))
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = size
    _parent(ob, parent, pivot)
    return ob


def descendants(root):
    out = [root]
    for c in root.children:
        out += descendants(c)
    return out


def tri_count(objs):
    n = 0
    for ob in objs:
        if ob.type == "MESH":
            n += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return n


# --------------------------------------------------------------------------- export
def export_glb(filename, roots):
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, filename)
    objs = []
    for r in roots:
        objs += descendants(r)
    bpy.context.view_layer.update()
    for ob in bpy.context.scene.objects:
        ob.select_set(ob in objs)
    bpy.context.view_layer.objects.active = roots[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", export_yup=True, export_apply=True,
        use_selection=True, export_animations=False, export_skins=False, export_morph=False,
        export_lights=False, export_cameras=False, export_extras=False,
    )
    print(f"[export] {path}  tris={tri_count(objs)}  size={os.path.getsize(path)//1024} KB")
    return path


# --------------------------------------------------------------------------- preview render
def _bbox(objs):
    lo = V((1e9, 1e9, 1e9))
    hi = V((-1e9, -1e9, -1e9))
    bpy.context.view_layer.update()
    for ob in objs:
        if ob.type != "MESH":
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ V(c)
            lo = V((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = V((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def render_preview(filename, view=(-1.0, -1.3, 0.75), size=512, ground=True, zoom=1.0, lens=45,
                   objs=None, look_at=None, outline=True, dist=None):
    """Workbench 3/4 render of the current scene's meshes to PREVIEW_DIR/filename."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    sc = bpy.context.scene
    if objs is None:
        objs = [o for o in sc.objects if o.type == "MESH"]
    lo, hi = _bbox(objs)
    center = (lo + hi) * 0.5
    if look_at is not None:
        center = V(look_at)
    radius = max((hi - lo).length * 0.5, 0.5)

    if ground:
        gp = Part()
        g = max((hi - lo).x, (hi - lo).y) * 4 + 10
        gp.box((center.x, center.y, -0.055), (g, g, 0.1), mat("_ground", (0.62, 0.62, 0.60)))
        make_object("_ground", gp)

    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lens
    cam_d.clip_end = 1000
    cam = _link(bpy.data.objects.new("cam", cam_d))
    fov = 2 * math.atan(cam_d.sensor_width / (2 * cam_d.lens))
    if dist is None:
        dist = radius / math.sin(fov / 2) * 1.08 * zoom
    d = V(view).normalized()
    cam.location = center + d * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = True
    sh.shadow_intensity = 0.3
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.curvature_ridge_factor = 0.5
    sh.curvature_valley_factor = 0.6
    sh.show_object_outline = outline
    sh.object_outline_color = (0.12, 0.12, 0.12)
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.80, 0.80, 0.80)
    sc.display.render_aa = "8"
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    w.color = (0.80, 0.80, 0.80)
    sc.world = w
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.55
    sc.view_settings.gamma = 1.05
    sc.render.filepath = os.path.join(PREVIEW_DIR, filename)
    bpy.ops.render.render(write_still=True)
    print(f"[preview] {sc.render.filepath}")
    return sc.render.filepath


def dump_tree(root, indent=0):
    """Print name / type / world origin / bbox dims for a hierarchy."""
    bpy.context.view_layer.update()
    wl = root.matrix_world.translation
    if root.type == "MESH":
        lo, hi = _bbox([root])
        dims = hi - lo
        info = f"mesh tris={tri_count([root])} dims=({dims.x:.2f},{dims.y:.2f},{dims.z:.2f}) z=[{lo.z:.2f},{hi.z:.2f}]"
    else:
        info = "empty"
    print("  " * indent + f"{root.name:<10} parent={root.parent.name if root.parent else '-':<8} "
          f"origin=({wl.x:.2f},{wl.y:.2f},{wl.z:.2f}) {info}")
    for c in root.children:
        dump_tree(c, indent + 1)
