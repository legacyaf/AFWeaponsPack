"""blender -b --factory-startup --python afm107_blockout.py -- <out folder>

AF M107A1 blockout: every part of the working blueprint (afm107_blueprint.py, rev 4) as a plain
solid, at its measured size and place, so the proportions can be judged in 3D before any detail
goes on. The blueprint is the single source of the numbers: this script reads its PARTS table.

Working frame as the other AF weapons: +Y forward, +Z up, +X to the right; metres. y = 0 at the
trigger, the bore at z = BORE. Renders: a right side view (orthographic), a three-quarter view
from the front right like the owner's reference picture, and one from the rear left.
"""
import importlib.util
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import af7_vanguard_detailed as d  # noqa: E402

spec = importlib.util.spec_from_file_location("afm107_blueprint", os.path.join(HERE, "afm107_blueprint.py"))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

PREFIX = "M107_"
BORE = 0.100
X_TRIGGER = bp.PARTS["trigger"][0][0]          # mm along the blueprint where y = 0


def Y(x_mm):
    return (x_mm - X_TRIGGER) / 1000.0


def Zm(z_mm):
    return BORE + z_mm / 1000.0


def side_pts(v):
    if isinstance(v, tuple):
        x0, x1, z0, z1 = v
        v = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    return [(Y(x), Zm(z)) for x, z in v]


def build():
    for ob in list(bpy.data.objects):            # the factory scene's cube, camera and light
        bpy.data.objects.remove(ob, do_unlink=True)
    d.PREFIX = PREFIX
    d.clean()
    body = d.collection("Body")
    steel = d.material("Cerakote", (0.030, 0.031, 0.032), rough=0.55, metal=0.2)
    dark = d.material("Dark", (0.008, 0.008, 0.009), rough=0.7)
    rubber = d.material("Rubber", (0.012, 0.012, 0.012), rough=0.9)
    P = bp.PARTS
    W = {"upper": 0.076, "rail": 0.0212, "rear_sight": 0.020, "butt": 0.052, "stock_post": 0.050,
         "rear_grip": 0.040, "lower": 0.050, "shroud": 0.072, "mag": 0.064, "grip": 0.032, "trigger": 0.006,
         "bipod_yoke": 0.040}
    for name, width in W.items():
        mat = rubber if name == "butt" else steel
        d.profile(name.title().replace("_", ""), body, mat, side_pts(P[name]), width, bevel=0.0015, note=name)
    for side in (-1, 1):                                     # cheek plates, both sides
        d.profile("CheekPlate%s" % ("R" if side > 0 else "L"), body, steel, side_pts(P["cheek"]), 0.004,
                  x=side * 0.039, bevel=0.0010, note="ribbed cheek plate")
        d.profile("Window%s" % ("R" if side > 0 else "L"), body, dark, side_pts(P["window"]), 0.002,
                  x=side * 0.0385, bevel=0.0, note="receiver window (bolt carrier)")
        for zr in bp.HOLE_ROWS:                              # handguard holes, shown dark
            for xh in bp.HOLES_X:
                pts = [(xh - 10, zr), (xh - 4, zr + 6), (xh + 10, zr + 6), (xh + 4, zr - 6), (xh - 4, zr - 6)]
                d.profile("Hole", body, dark, [(Y(x), Zm(z)) for x, z in pts], 0.002, x=side * 0.0385, bevel=0.0)
        for xl in (bp.fx(1090.0),):                          # bipod legs, folded under the barrel
            d.profile("BipodLeg%s" % ("R" if side > 0 else "L"), body, steel, side_pts(P["bipod_leg"]), 0.014,
                      x=side * 0.012, bevel=0.0015)
    # Round parts
    def lathe(name, x0, x1, r, mat, sides=24, cz=BORE, cx=0.0):
        bm = bmesh.new()
        d.bm_lathe(bm, [(Y(x0), 0.0), (Y(x0), r), (Y(x1), r), (Y(x1), 0.0)], sides=sides, c=(cx, cz))
        d.make(name, bm, body, mat, name, 0.0008)
    c = P["barrel_collar"]
    lathe("BarrelCollar", c[0], c[1], 0.0235, steel)
    b = P["barrel"]
    lathe("Barrel", b[0][0], b[1][0], 0.011, steel)
    br = P["brake"]
    lathe("Brake", br[0], br[1], 0.028, steel)
    m = P["monopod"]
    bm = bmesh.new()
    d.bm_lathe(bm, [(Zm(m[2]), 0.0), (Zm(m[2]), 0.007), (Zm(m[3]), 0.007), (Zm(m[3]), 0.0)], sides=16, axis="Z",
               c=(0.0, Y((m[0] + m[1]) / 2)))
    d.make("Monopod", bm, body, steel, "monopod", 0.0005)
    f = P["monopod_foot"]
    bm = bmesh.new()
    d.bm_lathe(bm, [(Zm(f[2]), 0.0), (Zm(f[2]), 0.020), (Zm(f[3]), 0.020), (Zm(f[3]), 0.0)], sides=20, axis="Z",
               c=(0.0, Y((f[0] + f[1]) / 2)))
    d.make("MonopodFoot", bm, body, rubber, "monopod foot", 0.0008)
    for name, (x, z, r) in (("MidLockRing", bp.MID_PIN), ("RearLockRing", bp.REAR_PIN)):
        bm = bmesh.new()
        import afm41_pathfinder_detailed as m41
        m41.bm_torus(bm, (0.040, Y(x), Zm(z)), r / 1000.0, 0.0018, seg=20, sides=6)
        d.make(name, bm, body, steel, "lock pin ring", 0.0)


def render(out):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    world = bpy.data.worlds.new("M107_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.93, 0.93, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = world
    sun = bpy.data.objects.new("M107_Sun", bpy.data.lights.new("M107_Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("M107_Cam", bpy.data.cameras.new("M107_Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(PREFIX)]
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in obs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    os.makedirs(out, exist_ok=True)
    views = (("side", Vector((1, 0, 0)), True, 0.0), ("front34", Vector((1.0, 0.55, 0.18)), False, 0.0),
             ("rear34", Vector((-1.0, -0.6, 0.30)), False, 0.0))
    for name, direction, ortho, _ in views:
        direction.normalize()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = (hi.y - lo.y) * 1.08
            cam.location = centre + direction * 3.0
        else:
            cam.data.lens = 50
            cam.location = centre + direction * 2.3
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, "m107_blockout_%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm107_blockout.blend"))
    render(args[0] if args else os.path.join(os.path.dirname(HERE), "docs", "img"))
