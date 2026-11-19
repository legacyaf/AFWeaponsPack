"""Headless build of the AF StG 44, its magazine and its scope: models -> (optional) DayZ export -> preview renders.

  blender -b --factory-startup --python afstg44_run.py -- [tex_size] [nobake] [model]

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
model = importlib.import_module("afstg44_detailed")
model.build()
model.build_magazine()
model.build_scope()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afstg44_detailed.blend"))

scene = bpy.context.scene
world = bpy.data.worlds.new("STG_World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.63, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
scene.world = world

lod1 = mag1 = scope1 = None
M = None
mag_at = Vector(model.MAG_AT)
scope_at = Vector(model.SCOPE_AT)
if not model_only:
    t0 = time.time()
    exp = importlib.import_module("afstg44_dayz_export")
    exp.ex.REBUILD = model.build          # distance LODs are reduced-detail rebuilds of the gun
    lod1 = exp.export(bake=bake, tex_size=size)
    M = exp.ex.export_matrix()
    for ob in bpy.data.collections["STG_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    exp.ex.REBUILD = model.build_magazine
    mag1 = exp.export_magazine(bake=bake, tex_size=max(1024, size // 2))
    for ob in bpy.data.collections["STGM_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    exp.ex.REBUILD = model.build_scope
    scope1 = exp.export_scope(bake=bake, tex_size=max(1024, size // 4))
    for ob in bpy.data.collections["STGS_DayZ"].objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(ob.data.vertices), len(ob.data.loop_triangles),
                                                          [g.name for g in ob.vertex_groups]))
    print("EXPORT_SECONDS %.1f" % (time.time() - t0))
    for cname in ("STG_Body", "STG_Moving", "STGM_Body", "STGM_Moving", "STGS_Body", "STGS_Moving"):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = True
    for cname, keep in (("STG_DayZ", lod1), ("STGM_DayZ", mag1), ("STGS_DayZ", scope1)):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = ob is not keep
    exp._gun_tables()
    M = exp.ex.export_matrix()          # the rifle's matrix again (the scope export set its own)
    origin = M @ Vector((0.0, 0.0, 0.0))
    mag1.location = M @ mag_at - origin          # show the magazine and the scope on the rifle
    scope1.location = M @ scope_at - origin
else:
    for ob in bpy.data.collections["STGM_Body"].objects:
        ob.location = ob.location + mag_at
    for ob in bpy.data.collections["STGS_Body"].objects:
        ob.location = ob.location + scope_at


def W(p):
    return (M @ Vector(p)) if M is not None else Vector(p)


rig = bpy.data.collections.new("STG_Render")
scene.collection.children.link(rig)
cam = bpy.data.objects.new("STG_Render_Camera", bpy.data.cameras.new("STG_Render_Camera"))
cam.data.clip_start = 0.01
rig.objects.link(cam)
scene.camera = cam
for nm, loc, watts, sz in (("Key", (1.0, 0.7, 1.1), 80, 1.0), ("Fill", (1.1, -0.8, 0.35), 30, 1.4),
                           ("Rim", (-1.0, 0.3, 0.8), 70, 0.8), ("Front", (0.5, 1.3, 0.4), 36, 1.0)):
    ld = bpy.data.lights.new("STG_Render_" + nm, "AREA")
    ld.energy, ld.size = watts, sz
    lo = bpy.data.objects.new("STG_Render_" + nm, ld)
    lo.location = W(loc)
    lo.rotation_euler = (W((0, 0.0, 0.03)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    rig.objects.link(lo)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1800, 900
try:
    scene.eevee.taa_render_samples = 48
    scene.eevee.use_raytracing = True
except Exception as e:
    print("EEVEE_OPT", e)

views = {"side": ((1.9, 0.005, 0.0), (0, 0.005, 0.0), 80), "left": ((-1.9, 0.005, 0.0), (0, 0.005, 0.0), 80),
         "34": ((0.95, 0.95, 0.42), (0, 0.03, 0.0), 55), "left34": ((-0.95, 0.85, 0.36), (0, 0.03, 0.0), 55),
         "action": ((0.34, 0.20, 0.30), (0, 0.04, 0.06), 60), "action_left": ((-0.36, 0.16, 0.26), (0, 0.02, 0.06), 60),
         "grip": ((0.42, -0.28, 0.10), (0, -0.06, 0.01), 60), "muzzle": ((0.30, 0.62, 0.20), (0, 0.33, 0.07), 70),
         "sights": ((0.0, -0.2300, model.SIGHT_Z), (0, 0.8, model.SIGHT_Z), 30),
         "scope": ((0.0, model.SCOPE_AT[1] + model.SCOPE_EYE, model.SCOPE_AT[2]), (0, 0.8, model.SCOPE_AT[2]), 30),
         "scope34": ((0.30, -0.36, 0.30), (0, -0.04, 0.15), 70),
         "top": ((0.0, 0.0, 1.3), (0, 0.0, 0.05), 60), "below": ((0.25, 0.15, -0.55), (0, 0.03, 0.02), 50)}
prefix = "stg_model_" if model_only else "stg_"
for name, (loc, tgt, lens) in views.items():
    cam.location = W(loc)
    cam.data.lens = lens
    up = "X" if name == "top" else "Y"
    cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", up).to_euler()
    scene.render.filepath = os.path.join(REPO, "docs", "img", prefix + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)

gold = bpy.data.materials.get("STG_Body_DayZ_Gold")
if lod1 is not None and gold:
    default = list(lod1.data.materials)
    for k in range(len(default)):          # one preview material per texture set
        g = bpy.data.materials.get("STG_Body_DayZ_Gold" + ("" if k == 0 else "_%d" % k))
        if g:
            lod1.data.materials[k] = g
    for name in ("34", "grip"):
        loc, tgt, lens = views[name]
        cam.location = W(loc)
        cam.data.lens = lens
        cam.rotation_euler = (W(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(REPO, "docs", "img", "stg_gold_" + name + ".png")
        bpy.ops.render.render(write_still=True)
    for k, m in enumerate(default):
        lod1.data.materials[k] = m

if not model_only:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afstg44_dayz.blend"))
    print("SAVED_DAYZ_BLEND")
