"""Re-import every exported GLB into an empty scene and print its object tree
(names, parents, world origins, bbox dims, tri counts) to check against ASSET_SPEC.md."""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import lp

files = sorted(glob.glob(os.path.join(lp.MODEL_DIR, "*.glb")))
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    objs = list(bpy.context.scene.objects)
    roots = [o for o in objs if o.parent is None]
    print(f"=== {os.path.basename(f)}  ({os.path.getsize(f) // 1024} KB, {lp.tri_count(objs)} tris, "
          f"{len(objs)} objects, materials: {sorted(m.name for m in bpy.data.materials)})")
    for r in roots:
        lp.dump_tree(r)
