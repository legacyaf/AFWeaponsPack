"""Headless build of the AF M107A1: models -> DayZ export (rifle, magazine, scope).

  blender -b --factory-startup --python afm107_run.py -- [tex_size] [nobake]

The previews are rendered by afm107_detailed.py itself; this script only builds and exports.
"""
import importlib
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
size = int(args[0]) if args and args[0].isdigit() else 2048
bake = "nobake" not in args

model = importlib.import_module("afm107_detailed")
model.build_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm107_detailed.blend"))

t0 = time.time()
exp = importlib.import_module("afm107_dayz_export")
for rebuild, fn, kw, prefix in ((model.build, exp.export, dict(tex_size=size), "M107_"),
                                (model.build_magazine, exp.export_magazine, dict(tex_size=max(1024, size // 2)), "M107M_"),
                                (model.build_scope_model, exp.export_scope, dict(tex_size=max(1024, size // 2)), "M107S_")):
    exp.ex.REBUILD = rebuild
    fn(bake=bake, **kw)
    for ob in bpy.data.collections[prefix + "DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
print("EXPORT_SECONDS %.1f" % (time.time() - t0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm107_dayz.blend"))
