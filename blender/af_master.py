"""Save the high-detail master of an AF weapon as its own .blend: the model rebuilt at the bake's detail
level (twice the sides on round parts, edges rounded in up to six steps, fillets every 7.5 degrees),
with its modifier stack live (bevels, weighted normals), its materials and collections as built.
This is the source the game model's normal and ambient maps are baked from.

  blender -b --factory-startup --python af_master.py -- <detailed module> <build function> [build function ...]

Writes blender/masters/<detailed module>_master.blend.
"""
import importlib
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:]
mod, fns = args[0], args[1:] or ["build"]
import af7_vanguard_detailed as d  # noqa: E402

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
d.set_detail(("high", 4.0, 6, 7.5, True))
d.EDGE_STEPS = ((0.0010, 6), (0.0005, 4), (0.0002, 2))
m = importlib.import_module(mod)
for fn in fns:
    getattr(m, fn)()
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type == "MESH" and not ob.hide_render:
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ob.evaluated_get(dg).to_mesh_clear()
os.makedirs(os.path.join(HERE, "masters"), exist_ok=True)
path = os.path.join(HERE, "masters", mod + "_master.blend")
bpy.ops.wm.save_as_mainfile(filepath=path)
print("MASTER saved %s: %d objects, about %d triangles after modifiers" % (path, len(bpy.data.objects), tris))
