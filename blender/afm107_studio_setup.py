"""Before af_studio.py on afm107_dayz.blend: puts the magazine and the scope on the rifle.

  blender -b afm107_dayz.blend --python afm107_studio_setup.py --python af_studio.py -- <out> m107 <json> ...

Their LODs are exported round their own origins (the proxy points). The exporter turns every LOD 90
degrees about Z (working x, y, z -> -y, x, z), so the proxy points are turned the same way."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import afm107_detailed as model  # noqa: E402

for name, at in (("M107M_LOD_1", model.MAG_PROXY), ("M107S_LOD_1", model.SCOPE_CENTRE())):
    bpy.data.objects[name].location = (-at[1], at[0], at[2])
bpy.context.view_layer.update()
