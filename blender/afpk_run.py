"""Headless build of The PeaceKeeper: models -> DayZ export (rifle, AF stock).

  blender -b --factory-startup --python afpk_run.py -- [tex_size] [nobake]

The previews are rendered by afpk_detailed.py itself; this script only builds and exports.
"""
import importlib
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
size = int(args[0]) if args and args[0].isdigit() else 4096
bake = "nobake" not in args

model = importlib.import_module("afpk_detailed")
model.build_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afpk_detailed.blend"))

t0 = time.time()
exp = importlib.import_module("afpk_dayz_export")
for rebuild, fn, prefix in ((model.build, exp.export, model.PREFIX),
                            (model.build_stock, exp.export_stock, model.STOCK_PREFIX)):
    exp.ex.REBUILD = rebuild
    fn(bake=bake, tex_size=size)
    for ob in bpy.data.collections[prefix + "DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
print("EXPORT_SECONDS %.1f" % (time.time() - t0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afpk_dayz.blend"))
