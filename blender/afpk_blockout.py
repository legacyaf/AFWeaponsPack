"""blender -b --factory-startup --python afpk_blockout.py -- <out folder>

The PeaceKeeper (AF modern battle rifle, our SCAR): blockout. Every main part as a plain solid at its
size and place, so the proportions can be judged in 3D before any detail goes on (docs/AF_SCAR.md).

Built straight in the vanilla SCAR-H's frame, measured in game on 2026-11-26 (docs/AF_SCAR.md), in the
working frame of the other AF weapons: +Y forward, +Z up, +X to the right; metres; y = -x_dayz,
z = y_dayz. So the vanilla hand animations, magazine and stock slot fit without any offset:
  bore z 0.0887, barrel end y 0.0741, muzzle y 0.5423, iron-sight eye (y -0.147, z 0.172),
  trigger pivot (y -0.0361, z 0.0367), magazine origin (y 0.0567, z 0.0245),
  stock-slot origin (y -0.2897, z 0.0715), left hand y 0.136, right index finger y -0.082.

Parts: the upper (aluminium) running forward into the handguard, the polymer lower with its magazine
well and pistol grip, barrel, gas block and our muzzle brake, the rail, the gold iron sights with the
red-tipped front post, the orange trim line, the round-counter window, the charging handle, and the
AF stock (a separate item in game, on the vanilla stock slot). The vanilla 20-round magazine is shown
as a grey reference box only (it is the game's own model, not ours). Renders: right side
(orthographic), three-quarter front right, three-quarter rear left, and the shooter's view.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import af7_vanguard_detailed as d  # noqa: E402

PREFIX = "PK_"
BORE = 0.0887
BARREL_END = 0.0741
MUZZLE = 0.5423
EYE = (-0.147, 0.172)
TRIGGER = (-0.0361, 0.0367)
MAG = (0.0567, 0.0245)
STOCK_SLOT = (-0.2897, 0.0715)
REAR = -0.158                      # rear face of the vanilla receiver (its collision box)
RAIL_TOP = 0.148                   # top of the rail; the aperture sits above it on the eye line


def build():
    for ob in list(bpy.data.objects):            # the factory scene's cube, camera and light
        bpy.data.objects.remove(ob, do_unlink=True)
    d.PREFIX = PREFIX
    d.clean()
    body = d.collection("Body")
    stockc = d.collection("Stock")
    ref = d.collection("Reference")
    black = d.material("MatteBlack", (0.022, 0.022, 0.024), rough=0.62, metal=0.25)
    polymer = d.material("Polymer", (0.018, 0.018, 0.019), rough=0.78)
    steel = d.material("Steel", (0.030, 0.030, 0.032), rough=0.45, metal=0.9)
    orange = d.material("Orange", (0.75, 0.30, 0.05), rough=0.55)
    gold = d.material("Gold", (0.83, 0.58, 0.20), rough=0.28, metal=1.0)
    red = d.material("Red", (0.70, 0.02, 0.02), rough=0.4)
    glow = d.material("Counter", (1.0, 0.45, 0.05), rough=0.3)
    grey = d.material("Reference", (0.35, 0.35, 0.36), rough=0.8)

    def prof(name, col, mat, pts, width, x=0.0, bevel=0.0015, note=""):
        return d.profile(name, col, mat, pts, width, x=x, bevel=bevel, note=note)

    def lathe(name, col, mat, prof_, sides=24, c=(0.0, BORE), axis="Y", bevel=0.0006):
        bm = bmesh.new()
        d.bm_lathe(bm, prof_, sides=sides, c=c, axis=axis)
        return d.make(name, bm, col, mat, name, bevel)

    # Upper receiver: one aluminium extrusion from the rear plate to the front of the handguard. The rear
    # part is the receiver (z 0.068 to the rail base); forward of the magazine well it deepens into the
    # handguard, which the left hand holds (y about 0.136).
    prof("Upper", body, black, [(REAR, 0.068), (0.090, 0.068), (0.118, 0.050), (0.300, 0.050), (0.318, 0.062),
                                (0.318, 0.136), (REAR, 0.136)], 0.050, bevel=0.0025, note="upper receiver")
    # AF-pattern handguard slots (shown dark): three long slots each side, angled at the front like the AF-7's.
    for side in (-1, 1):
        for k, y0 in enumerate((0.140, 0.195, 0.250)):
            prof("Slot%s%d" % ("R" if side > 0 else "L", k), body, polymer,
                 [(y0, 0.066), (y0 + 0.040, 0.066), (y0 + 0.046, 0.076), (y0 + 0.006, 0.076)], 0.002,
                 x=side * 0.0252, bevel=0.0)
    # Rail on top, full length, with a raised mid section (a plain box here).
    prof("Rail", body, black, [(REAR + 0.004, 0.136), (0.316, 0.136), (0.316, RAIL_TOP), (REAR + 0.004, RAIL_TOP)],
         0.0212, bevel=0.0008, note="Picatinny rail")
    # Lower receiver (polymer): trigger housing and magazine well. The well's mouth is round the vanilla
    # magazine's origin (y 0.0567), so the game's magazine sits in it.
    prof("Lower", body, polymer, [(REAR + 0.006, 0.068), (REAR + 0.006, 0.030), (-0.060, 0.022), (0.012, 0.022),
                                  (0.016, -0.004), (0.100, -0.004), (0.104, 0.068)], 0.046, bevel=0.0022,
         note="lower receiver")
    # Pistol grip, raked back about 18 degrees, under the trigger.
    prof("Grip", body, polymer, [(-0.052, 0.024), (-0.020, 0.024), (-0.044, -0.070), (-0.060, -0.084),
                                 (-0.084, -0.080), (-0.080, -0.060)], 0.030, bevel=0.003, note="pistol grip")
    # Trigger guard and trigger (pivot on the vanilla trigger_axis).
    prof("TriggerGuard", body, polymer, [(-0.050, 0.022), (0.014, 0.022), (0.014, 0.000), (0.008, -0.004),
                                         (-0.034, -0.006), (-0.040, 0.004), (-0.044, 0.016), (-0.032, 0.016),
                                         (-0.032, 0.006), (0.004, 0.006), (0.004, 0.016), (-0.050, 0.016)],
         0.010, bevel=0.0008, note="trigger guard")
    prof("Trigger", body, steel, [(TRIGGER[0] - 0.003, TRIGGER[1]), (TRIGGER[0] + 0.003, TRIGGER[1]),
                                  (TRIGGER[0] + 0.001, 0.008), (TRIGGER[0] - 0.006, 0.010)], 0.006, bevel=0.0006,
         note="trigger")
    # Orange trim: the AF accent line along both sides where the upper meets the lower, painted in the
    # finished rifle (here a thin strip so it shows).
    for side in (-1, 1):
        prof("Trim%s" % ("R" if side > 0 else "L"), body, orange,
             [(REAR + 0.004, 0.069), (0.300, 0.069), (0.300, 0.0745), (REAR + 0.004, 0.0745)], 0.0012,
             x=side * 0.0254, bevel=0.0)
    # Round counter: a small window on the left, at the rear of the upper above the grip, where the shooter
    # glances down at it and other players see it.
    prof("CounterBezel", body, black, [(-0.118, 0.098), (-0.070, 0.098), (-0.070, 0.124), (-0.118, 0.124)], 0.004,
         x=-0.0262, bevel=0.0008, note="round counter bezel")
    prof("CounterDisplay", body, glow, [(-0.114, 0.102), (-0.074, 0.102), (-0.074, 0.120), (-0.114, 0.120)], 0.002,
         x=-0.0282, bevel=0.0, note="round counter display")
    # Charging handle, left side, forward (it rides with the bolt carrier).
    prof("ChargingHandle", body, steel, [(0.150, 0.104), (0.172, 0.104), (0.168, 0.122), (0.154, 0.122)], 0.020,
         x=-0.035, bevel=0.002, note="charging handle")
    # Ejection port, right side (dark).
    prof("EjectionPort", body, polymer, [(-0.020, 0.090), (0.060, 0.090), (0.060, 0.118), (-0.020, 0.118)], 0.002,
         x=0.0252, bevel=0.0)
    # Barrel, gas block, our muzzle brake.
    lathe("Barrel", body, steel, [(BARREL_END, 0.0), (BARREL_END, 0.0105), (0.300, 0.0105), (0.300, 0.0095),
                                  (0.478, 0.0095), (0.478, 0.0)], sides=24)
    lathe("GasBlock", body, black, [(0.322, 0.0), (0.322, 0.0150), (0.352, 0.0150), (0.352, 0.0)], sides=24)
    lathe("Brake", body, black, [(0.478, 0.0), (0.478, 0.0135), (0.488, 0.0145), (MUZZLE - 0.004, 0.0145),
                                 (MUZZLE, 0.0130), (MUZZLE, 0.0)], sides=8)
    # Gold iron sights: rear aperture on the eye line, front post with a red tip.
    # Rear sight: a base on the rail, two protective ears, and the aperture ring on the eye line, so the
    # eye looks through it at the front post.
    prof("RearSightBase", body, gold, [(-0.140, RAIL_TOP), (-0.112, RAIL_TOP), (-0.116, 0.160), (-0.136, 0.160)],
         0.022, bevel=0.0010, note="rear sight base (gold)")
    for side in (-1, 1):
        prof("RearEar%s" % ("R" if side > 0 else "L"), body, gold,
             [(-0.134, 0.160), (-0.118, 0.160), (-0.120, EYE[1] + 0.010), (-0.132, EYE[1] + 0.010)], 0.003,
             x=side * 0.0095, bevel=0.0006)
    circ = lambda r: [(r * math.cos(2 * math.pi * i / 20), EYE[1] + r * math.sin(2 * math.pi * i / 20)) for i in range(20)]
    bm = bmesh.new()
    d.bm_tube(bm, circ(0.0060), circ(0.0022), -0.129, -0.123, zref=EYE[1])
    d.make("RearAperture", bm, body, gold, "rear sight aperture (gold)", 0.0004)
    prof("RearPost", body, gold, [(-0.129, 0.160), (-0.123, 0.160), (-0.123, EYE[1] - 0.005), (-0.129, EYE[1] - 0.005)],
         0.004, bevel=0.0003)
    prof("FrontSightBase", body, gold, [(0.290, RAIL_TOP), (0.314, RAIL_TOP), (0.312, 0.160), (0.292, 0.160)], 0.022,
         bevel=0.0010, note="front sight base (gold)")
    for side in (-1, 1):
        prof("FrontEar%s" % ("R" if side > 0 else "L"), body, gold,
             [(0.294, 0.160), (0.310, 0.160), (0.308, 0.176), (0.296, 0.176)], 0.003, x=side * 0.009, bevel=0.0006)
    prof("FrontPost", body, gold, [(0.300, 0.160), (0.304, 0.160), (0.304, 0.168), (0.300, 0.168)], 0.003,
         bevel=0.0003, note="front post (gold)")
    prof("FrontPostTip", body, red, [(0.300, 0.168), (0.304, 0.168), (0.304, EYE[1]), (0.300, EYE[1])], 0.003,
         bevel=0.0003, note="front post tip (red)")
    # The AF stock: a separate item on the vanilla stock slot (origin y -0.2897, z 0.0715). Folding hinge
    # block on the receiver's rear plate, a skeleton frame with an orange-trimmed cheek riser, butt pad.
    prof("StockHinge", stockc, black, [(REAR - 0.022, 0.074), (REAR, 0.074), (REAR, 0.134), (REAR - 0.022, 0.134)],
         0.046, bevel=0.0020, note="stock hinge block")
    prof("StockFrame", stockc, polymer, [(REAR - 0.022, 0.134), (-0.392, 0.140), (-0.398, 0.010), (-0.360, 0.010),
                                         (-0.300, 0.070), (REAR - 0.022, 0.082)], 0.036, bevel=0.003,
         note="stock frame")
    prof("CheekRiser", stockc, black, [(-0.250, 0.140), (-0.380, 0.145), (-0.380, 0.152), (-0.256, 0.148)], 0.034,
         bevel=0.002, note="cheek riser")
    for side in (-1, 1):
        prof("StockTrim%s" % ("R" if side > 0 else "L"), stockc, orange,
             [(-0.200, 0.118), (-0.380, 0.124), (-0.380, 0.128), (-0.200, 0.122)], 0.0012, x=side * 0.0186, bevel=0.0)
    prof("ButtPad", stockc, polymer, [(-0.398, 0.004), (-0.412, 0.004), (-0.412, 0.148), (-0.398, 0.148)], 0.040,
         bevel=0.003, note="butt pad")
    # Reference only: the vanilla 20-round magazine's bulk, from its origin down and forward.
    prof("RefMagazine", ref, grey, [(MAG[0] - 0.036, MAG[1] + 0.020), (MAG[0] + 0.036, MAG[1] + 0.020),
                                    (MAG[0] + 0.050, MAG[1] - 0.120), (MAG[0] - 0.026, MAG[1] - 0.120)], 0.030,
         bevel=0.002, note="vanilla magazine (reference)")


def render(out):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    world = bpy.data.worlds.new("PK_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.93, 0.93, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = world
    sun = bpy.data.objects.new("PK_Sun", bpy.data.lights.new("PK_Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("PK_Cam", bpy.data.cameras.new("PK_Cam"))
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
    views = (("side", Vector((1, 0, 0)), True), ("front34", Vector((1.0, 0.55, 0.18)), False),
             ("rear34", Vector((-1.0, -0.6, 0.30)), False))
    for name, direction, ortho in views:
        direction.normalize()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = (hi.y - lo.y) * 1.08
            cam.location = centre + direction * 3.0
        else:
            cam.data.lens = 50
            cam.location = centre + direction * 1.7
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, "pk_blockout_%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)
    # The shooter's view: from the measured eye point, a little back and up, down the sights.
    cam.data.type = "PERSP"
    cam.data.lens = 50
    cam.data.clip_start = 0.005          # the aperture is only 8 cm from the eye
    cam.location = Vector((0.0, EYE[0] - 0.06, EYE[1]))
    cam.rotation_euler = (Vector((0.0, 0.30, EYE[1])) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, "pk_blockout_shooter.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afpk_blockout.blend"))
    out = os.path.abspath(args[0]) if args else os.path.join(os.path.dirname(HERE), "docs", "img")
    render(out)
