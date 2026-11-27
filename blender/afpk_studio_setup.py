"""Before af_studio.py on afpk_dayz.blend: puts the AF stock back on the rifle.

  blender -b afpk_dayz.blend --python afpk_studio_setup.py --python af_studio.py -- <out> pk <json> ...

The stock's LOD is exported in the stock slot's frame (afpk_detailed.STOCK_MATRIX); both LODs are also
turned 90 degrees about Z by the exporter. This undoes the slot frame for the picture only."""
import math

import bpy
from mathutils import Matrix, Vector

STOCK_ORIGIN = (0.0, -0.2897, 0.0715)
slot = Matrix.Rotation(math.radians(-90.0), 4, "X") @ Matrix.Translation(-Vector(STOCK_ORIGIN))
turn = Matrix(((0, -1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))      # working frame -> LOD frame
ob = bpy.data.objects["PKS_LOD_1"]
ob.matrix_world = turn @ slot.inverted() @ turn.inverted()
bpy.context.view_layer.update()
