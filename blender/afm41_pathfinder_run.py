"""Headless build of the AF M41: model -> (optional) DayZ export -> preview renders.

  blender -b --factory-startup --python afm41_pathfinder_run.py -- [tex_size] [nobake] [model]

  model   only build the model and render it with its procedural materials (fast check)
  nobake  export the p3d without re-baking textures
"""
import importlib
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
size = int(args[0]) if args and args[0].isdigit() else 2048
bake = "nobake" not in args
model_only = "model" in args

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
model = importlib.import_module("afm41_pathfinder_detailed")
model.build()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm41_pathfinder_detailed.blend"))

scene = bpy.context.scene
world = bpy.data.worlds.new("M41_World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.63, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
scene.world = world

lod1 = None
M = None
if not model_only:
    t0 = time.time()
    exp = importlib.import_module("afm41_pathfinder_dayz_export")
    lod1 = exp.export(bake=bake, tex_size=size)
    M = exp.ex.export_matrix()
    print("EXPORT_SECONDS %.1f" % (time.time() - t0))
    for ob in bpy.data.collections["M41_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    for cname in ("M41_Body", "M41_Moving"):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = True
    for ob in bpy.data.collections["M41_DayZ"].objects:
        ob.hide_render = ob is not lod1


def W(p):
    return (M @ Vector(p)) if M is not None else Vector(p)


rig = bpy.data.collections.new("M41_Render")
scene.collection.children.link(rig)
cam = bpy.data.objects.new("M41_Render_Camera", bpy.data.cameras.new("M41_Render_Camera"))
cam.data.clip_start = 0.01
rig.objects.link(cam)
scene.camera = cam
for nm, loc, watts, sz in (("Key", (1.2, 0.9, 1.3), 110, 1.0), ("Fill", (1.3, -0.9, 0.45), 40, 1.4),
                           ("Rim", (-1.1, 0.4, 0.9), 90, 0.8), ("Front", (0.6, 1.6, 0.5), 50, 1.0)):
    ld = bpy.data.lights.new("M41_Render_" + nm, "AREA")
    ld.energy, ld.size = watts, sz
    lo = bpy.data.objects.new("M41_Render_" + nm, ld)
    lo.location = W(loc)
    lo.rotation_euler = (W((0, 0.2, 0.09)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    rig.objects.link(lo)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1800, 900
try:
    scene.eevee.taa_render_samples = 48
    scene.eevee.use_raytracing = True
except Exception as e:
    print("EEVEE_OPT", e)

views = {"side": ((2.3, 0.21, 0.07), (0, 0.21, 0.07), 70), "34": ((1.25, 1.15, 0.50), (0, 0.22, 0.08), 50),
         "left": ((-1.25, 0.95, 0.35), (0, 0.20, 0.08), 50), "action": ((0.42, 0.16, 0.32), (0, 0.02, 0.10), 60),
         "butt": ((0.55, -0.52, 0.16), (0, -0.25, 0.05), 60), "muzzle": ((0.40, 0.95, 0.24), (0, 0.72, 0.11), 70),
         "sights": ((0.0, -0.1582, 0.1377), (0, 0.8, 0.1377), 30),
         "stamps": ((-0.30, 0.20, 0.30), (0, 0.045, 0.118), 110), "butt_left": ((-0.50, -0.46, 0.16), (0, -0.25, 0.05), 70)}
prefix = "m41_model_" if model_only else "m41_"
for name, (loc, tgt, lens) in views.items():
    cam.location = W(loc)
    cam.data.lens = lens
    cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(REPO, "docs", "img", prefix + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)

if model_only:   # bolt drawn back: the magazine well and the two display rounds
    for nm in ("M41_BoltBody", "M41_BoltHandle", "M41_BoltCocking"):
        bpy.data.objects[nm].location.y -= 0.085
    cam.location = Vector((0.22, 0.11, 0.34))
    cam.data.lens = 85
    cam.rotation_euler = (Vector((0, 0.025, 0.108)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(REPO, "docs", "img", "m41_model_open.png")
    bpy.ops.render.render(write_still=True)

gold = bpy.data.materials.get("M41_Body_DayZ_Gold")
if lod1 is not None and gold:
    default = list(lod1.data.materials)
    for k in range(len(default)):          # one preview material per texture set
        g = bpy.data.materials.get("M41_Body_DayZ_Gold" + ("" if k == 0 else "_%d" % k))
        if g:
            lod1.data.materials[k] = g
    for name in ("34", "action"):
        loc, tgt, lens = views[name]
        cam.location = W(loc)
        cam.data.lens = lens
        cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(REPO, "docs", "img", "m41_gold_" + name + ".png")
        bpy.ops.render.render(write_still=True)
    for k, m in enumerate(default):
        lod1.data.materials[k] = m

if not model_only:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm41_pathfinder_dayz.blend"))
    print("SAVED_DAYZ_BLEND")
