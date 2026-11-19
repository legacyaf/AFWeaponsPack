"""Headless build of the AF-7: model -> DayZ export -> preview renders -> af7_vanguard_dayz.blend.

  blender -b --factory-startup --python af7_vanguard_run.py -- [tex_size] [nobake]

  nobake  export the p3d without re-baking textures (LOD 1 and its UVs are read back from the p3d)
"""
import os, runpy, sys, time, bpy
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
size = int(args[0]) if args and args[0].isdigit() else 2048
bake = "nobake" not in args

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
runpy.run_path(REPO + r"\blender\af7_vanguard_detailed.py", run_name="__main__")
bpy.ops.wm.save_as_mainfile(filepath=REPO + r"\blender\af7_vanguard_detailed.blend")

t0 = time.time()
ns = runpy.run_path(REPO + r"\blender\af7_vanguard_dayz_export.py", run_name="af7_export")
ns["__file__"] = REPO + r"\blender\af7_vanguard_dayz_export.py"
lod1 = ns["export"](bake=bake, tex_size=size)
print("EXPORT_SECONDS %.1f" % (time.time() - t0))
M = ns["export_matrix"]()

for ob in bpy.data.objects:
    if ob.type == "MESH":
        me = ob.data
        me.calc_loop_triangles()
        cols = [c.name for c in ob.users_collection]
        if cols and cols[0] == "AF7_DayZ":
            print("DAYZ|%s|verts=%d|tris=%d|groups=%s" % (ob.name, len(me.vertices), len(me.loop_triangles), [g.name for g in ob.vertex_groups]))

if bake:
    scene = bpy.context.scene
    # show only the baked LOD 1 (plus floor and lights)
    for cname in ("AF7_Body", "AF7_Moving", "AF7_Reference"):
        for ob in bpy.data.collections[cname].objects:
            ob.hide_render = True
            ob.hide_viewport = True
    for ob in bpy.data.collections["AF7_DayZ"].objects:
        ob.hide_render = ob is not lod1
        ob.hide_viewport = ob is not lod1
    for ob in bpy.data.collections["AF7_Render"].objects:
        ob.matrix_world = M @ ob.matrix_world
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    try:
        scene.eevee.taa_render_samples = 48
        scene.eevee.use_raytracing = True
    except Exception as e:
        print("EEVEE_OPT", e)
    cam = scene.camera
    target = M @ Vector((0.0, 0.085, -0.015))
    views = {"dayz_34": ((0.95, 0.52, 0.30), 42), "dayz_side": ((1.6, 0.085, 0.0), 60),
             "dayz_left": ((-0.9, 0.6, 0.15), 42), "dayz_logo": ((0.42, 0.02, 0.02), 70), "dayz_magwell": ((0.30, 0.30, -0.165), 85)}
    for name, (loc, lens) in views.items():
        cam.location = M @ Vector(loc)
        cam.data.lens = lens
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = REPO + "\\docs\\img\\" + name + ".png"
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)
    # one render per lower LOD, to check the decimation holds together
    loc, lens = views["dayz_34"]
    cam.location = M @ Vector(loc)
    cam.data.lens = lens
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    for n in (2, 3, 4):
        lo = bpy.data.objects.get("AF7_LOD_%d" % n)
        if not lo:
            continue
        lod1.hide_render = True
        lo.hide_render = False
        scene.render.filepath = REPO + "\\docs\\img\\dayz_lod%d.png" % n
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)
        lo.hide_render = True
        lod1.hide_render = False
    gold = bpy.data.materials.get("AF7_Body_DayZ_Gold")
    if gold:
        default = list(lod1.data.materials)
        for k in range(len(default)):          # one preview material per texture set
            g = bpy.data.materials.get("AF7_Body_DayZ_Gold" + ("" if k == 0 else "_%d" % k))
            if g:
                lod1.data.materials[k] = g
        for name in ("dayz_34", "dayz_side", "dayz_left"):
            loc, lens = views[name]
            cam.location = M @ Vector(loc)
            cam.data.lens = lens
            cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = REPO + "\\docs\\img\\" + name.replace("dayz_", "dayz_gold_") + ".png"
            bpy.ops.render.render(write_still=True)
            print("RENDERED", scene.render.filepath)
        for k, m in enumerate(default):
            lod1.data.materials[k] = m
    loc, lens = views["dayz_34"]
    cam.location = M @ Vector(loc)
    cam.data.lens = lens
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=REPO + r"\blender\af7_vanguard_dayz.blend")
    print("SAVED_DAYZ_BLEND")

