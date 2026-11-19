"""Headless build of the AF P08 and its magazine: models -> (optional) DayZ export -> preview renders.

  blender -b --factory-startup --python afp08_run.py -- [tex_size] [nobake] [model]

  model   only build the models and render them with their procedural materials (fast check)
  nobake  export the p3d files without re-baking textures
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
model = importlib.import_module("afp08_detailed")
model.build()
model.build_magazine()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afp08_detailed.blend"))

scene = bpy.context.scene
world = bpy.data.worlds.new("P08_World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.63, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
scene.world = world

lod1 = mag1 = None
M = None
mag_at = Vector(model.MAG_AT)
if not model_only:
    t0 = time.time()
    exp = importlib.import_module("afp08_dayz_export")
    exp.ex.REBUILD = model.build          # distance LODs are reduced-detail rebuilds of the gun
    lod1 = exp.export(bake=bake, tex_size=size)
    M = exp.ex.export_matrix()
    for ob in bpy.data.collections["P08_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    exp.ex.REBUILD = model.build_magazine
    mag1 = exp.export_magazine(bake=bake, tex_size=max(1024, size // 4))
    for ob in bpy.data.collections["P08M_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    print("EXPORT_SECONDS %.1f" % (time.time() - t0))
    for cname in ("P08_Body", "P08_Moving", "P08M_Body", "P08M_Moving"):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = True
    for cname, keep in (("P08_DayZ", lod1), ("P08M_DayZ", mag1)):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = ob is not keep
    mag1.location = M @ mag_at          # show the magazine seated in the gun
else:
    for ob in bpy.data.collections["P08M_Body"].objects:
        ob.location = ob.location + mag_at


def W(p):
    return (M @ Vector(p)) if M is not None else Vector(p)


rig = bpy.data.collections.new("P08_Render")
scene.collection.children.link(rig)
cam = bpy.data.objects.new("P08_Render_Camera", bpy.data.cameras.new("P08_Render_Camera"))
cam.data.clip_start = 0.005
rig.objects.link(cam)
scene.camera = cam
for nm, loc, watts, sz in (("Key", (0.5, 0.45, 0.6), 22, 0.5), ("Fill", (0.55, -0.35, 0.2), 8, 0.7),
                           ("Rim", (-0.5, 0.2, 0.45), 20, 0.4), ("Front", (0.25, 0.75, 0.25), 10, 0.5)):
    ld = bpy.data.lights.new("P08_Render_" + nm, "AREA")
    ld.energy, ld.size = watts, sz
    lo = bpy.data.objects.new("P08_Render_" + nm, ld)
    lo.location = W(loc)
    lo.rotation_euler = (W((0, 0.09, 0.03)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    rig.objects.link(lo)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1800, 900
try:
    scene.eevee.taa_render_samples = 48
    scene.eevee.use_raytracing = True
except Exception as e:
    print("EEVEE_OPT", e)

views = {"side": ((0.62, 0.095, 0.02), (0, 0.095, 0.02), 80), "left": ((-0.62, 0.095, 0.02), (0, 0.095, 0.02), 80),
         "34": ((0.33, 0.40, 0.16), (0, 0.09, 0.02), 55), "left34": ((-0.33, 0.38, 0.14), (0, 0.09, 0.02), 55),
         "action": ((0.15, -0.10, 0.19), (0, 0.03, 0.07), 60), "action_left": ((-0.16, -0.08, 0.17), (0, 0.03, 0.07), 60),
         "grip": ((0.22, -0.16, 0.02), (0, 0.02, 0.0), 60), "muzzle": ((0.14, 0.36, 0.11), (0, 0.17, 0.065), 70),
         "sights": ((0.0, -0.2586, model.SIGHT_Z), (0, 0.8, model.SIGHT_Z), 30),
         "top": ((0.0, 0.09, 0.50), (0, 0.09, 0.05), 60), "below": ((0.10, 0.14, -0.26), (0, 0.07, 0.02), 50)}
prefix = "p08_model_" if model_only else "p08_"
for name, (loc, tgt, lens) in views.items():
    cam.location = W(loc)
    cam.data.lens = lens
    up = "X" if name == "top" else "Y"
    cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", up).to_euler()
    scene.render.filepath = os.path.join(REPO, "docs", "img", prefix + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)

gold = bpy.data.materials.get("P08_Body_DayZ_Gold")
if lod1 is not None and gold:
    default = list(lod1.data.materials)
    for k in range(len(default)):          # one preview material per texture set
        g = bpy.data.materials.get("P08_Body_DayZ_Gold" + ("" if k == 0 else "_%d" % k))
        if g:
            lod1.data.materials[k] = g
    for name in ("34", "grip"):
        loc, tgt, lens = views[name]
        cam.location = W(loc)
        cam.data.lens = lens
        cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(REPO, "docs", "img", "p08_gold_" + name + ".png")
        bpy.ops.render.render(write_still=True)
    for k, m in enumerate(default):
        lod1.data.materials[k] = m

if not model_only:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afp08_dayz.blend"))
    print("SAVED_DAYZ_BLEND")
