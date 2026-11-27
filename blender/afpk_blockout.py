"""blender -b --factory-startup --python afpk_blockout.py -- <out folder>

The PeaceKeeper (AF modern battle rifle, our SCAR): design model, version 2. It replaces the plain-box
blockout, which the owner rejected (2026-11-26: "make a better more realistic version, use military
weapon variants for reference").

The shape follows the military SCAR-H family (the US SOCOM Mk 17 and the FN service rifle): a tall,
flat-sided aluminium upper with a full-length top rail, short side rails and a bottom rail at the front,
the gas regulator just ahead of the upper, a polymer lower with the magazine well, an A2-type grip and a
wide trigger guard, the reciprocating charging handle forward on the left, and the side-folding stock
with its comb, cheek riser, lightening cut and rubber pad. Our own parts: the AF muzzle brake, the gold
folding sights with the red-tipped post, the orange trim line, the round counter on the left.

It is a design model for judging the look (it still uses Boolean cuts); the game model is rebuilt from
it in clean topology (af_topo), as docs/AF_SCAR.md says.

Built in the vanilla SCAR-H's frame, measured in game on 2026-11-26 (docs/AF_SCAR.md): +Y forward,
+Z up, +X to the right; metres; y = -x_dayz, z = y_dayz. Bore z 0.0887, muzzle y 0.5423, iron-sight
eye (y -0.147, z 0.172), trigger pivot (y -0.0361, z 0.0367), magazine origin (y 0.0567, z 0.0245),
charging handle on the bolt axis (y 0.2415, z 0.1175), front sight slot y 0.3044 on the rail
(z 0.1314), stock slot (y -0.2897, z 0.0715), receiver rear y -0.158.

The magazine shown is a stand-in for the vanilla 20-round magazine (the game's own model, which our
rifle takes); it is not exported.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import af7_vanguard_detailed as d  # noqa: E402

PREFIX = "PK_"
BORE = 0.0887
MUZZLE = 0.5423
EYE = (-0.147, 0.1515)            # sight line: owner 2026-11-26 halved the sight height (vanilla eye z 0.172)
TRIGGER = (-0.0361, 0.0367)
MAG = (0.0567, 0.0245)
BOLT = (0.2415, 0.1175)
FRONT_SIGHT = 0.3044
REAR = -0.158                      # rear face of the vanilla receiver
UP_TOP = 0.1215                    # top of the upper's body, under the rail
RAIL_TOP = 0.131                   # top of the rail (the vanilla front-sight slot sits here)
HALF = 0.0245                      # half width of the upper
UP_FRONT = 0.356                   # front face of the upper
PITCH, SLOT = 0.01001, 0.00523     # rail slot pitch and width (MIL-STD-1913)


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(PREFIX + name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1.0)
    p.inputs["Emission Color"].default_value = (*rgb, 1.0)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.4
    return m


def rail_pts(bx, bz, ox, oz):
    """MIL-STD-1913 rail section [(x, z)], its base centred on (bx, bz), facing the unit direction (ox, oz)."""
    tx, tz = -oz, ox
    sec = [(-0.0095, 0.0), (0.0095, 0.0), (0.0106, 0.003), (0.0106, 0.0062), (0.0086, 0.0095),
           (-0.0086, 0.0095), (-0.0106, 0.0062), (-0.0106, 0.003)]
    return [(bx + u * tx + v * ox, bz + u * tz + v * oz) for u, v in sec]


def build():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    d.PREFIX = PREFIX
    d.clean()
    body = d.collection("Body")
    stockc = d.collection("Stock")
    ref = d.collection("Reference")
    cutc = d.collection("Cutters")
    anod = d.material("Anodised", (0.028, 0.028, 0.030), rough=0.52, metal=0.35, bump=0.15, rough_var=0.15,
                      wear=0.35, wear_rgb=(0.30, 0.30, 0.31))
    poly = d.material("Polymer", (0.022, 0.022, 0.023), rough=0.72, bump=0.25, rough_var=0.10, wear=0.15,
                      wear_rgb=(0.08, 0.08, 0.08))
    grip_mat = d.material("GripPolymer", (0.022, 0.022, 0.023), rough=0.80, stipple=0.8)
    steel = d.material("Steel", (0.035, 0.035, 0.037), rough=0.38, metal=0.9, wear=0.4, wear_rgb=(0.45, 0.45, 0.46))
    rubber = d.material("Rubber", (0.015, 0.015, 0.015), rough=0.9)
    orange = d.material("Orange", (0.75, 0.28, 0.04), rough=0.5, wear=0.25, wear_rgb=(0.10, 0.08, 0.06))
    gold = d.material("Gold", (0.80, 0.56, 0.20), rough=0.32, metal=1.0, wear=0.3, wear_rgb=(0.9, 0.75, 0.45))
    red = emissive("Red", (0.85, 0.03, 0.02), 0.6)
    glass = d.material("Glass", (0.004, 0.004, 0.005), rough=0.08)
    digit = emissive("Digits", (1.0, 0.42, 0.04), 6.0)
    magmat = d.material("RefMagazine", (0.030, 0.030, 0.032), rough=0.55, metal=0.5, wear=0.3,
                        wear_rgb=(0.30, 0.30, 0.31))

    def prof(name, col, mat, pts, width, x=0.0, bevel=0.0012, rnd=0.0, note=""):
        return d.profile(name, col, mat, pts, width, x=x, bevel=bevel, note=note, round=rnd)

    def xsec(name, col, mat, pts, y0, y1, bevel=0.0010, note=""):
        bm = bmesh.new()
        d.bm_xsec(bm, pts, y0, y1)
        return d.make(name, bm, col, mat, note, bevel)

    def lathe(name, col, mat, pr, sides=32, c=(0.0, BORE), axis="Y", bevel=0.0004):
        bm = bmesh.new()
        d.bm_lathe(bm, pr, sides=sides, c=c, axis=axis)
        return d.make(name, bm, col, mat, name, bevel)

    def cutter(name, boxes):
        bm = bmesh.new()
        for c, s in boxes:
            d.bm_box(bm, c, s)
        return d.make(name, bm, cutc, None, "cutter", 0.0)

    def cut(target, name, boxes):
        d.cut(target, cutter(name, boxes), name)

    # ---- Upper receiver: flat-sided aluminium extrusion, chamfered shoulders under the rail. ----
    upper = xsec("Upper", body, anod, [(-HALF + 0.0015, 0.0745), (HALF - 0.0015, 0.0745), (HALF - 0.0015, 0.0840),
                                       (HALF, 0.0855), (HALF, 0.1150), (HALF - 0.0055, UP_TOP),
                                       (-HALF + 0.0055, UP_TOP), (-HALF, 0.1150), (-HALF, 0.0855),
                                       (-HALF + 0.0015, 0.0840)], REAR, UP_FRONT, bevel=0.0012,
                 note="upper receiver")
    # Forward of the magazine well it deepens round the barrel and piston (the handguard).
    front = prof("UpperFront", body, anod, [(0.112, 0.0755), (0.124, 0.0600), (UP_FRONT - 0.004, 0.0600),
                                            (UP_FRONT, 0.0640), (UP_FRONT, 0.0755)], 2 * HALF, bevel=0.0012,
                 note="upper, handguard section")
    # Ejection port (right) with the bolt carrier showing, the brass deflector behind it.
    cut(upper, "EjectPort", [((HALF, 0.029, 0.1075), (0.010, 0.066, 0.021))])
    prof("BoltCarrier", body, steel, [(-0.003, 0.0975), (0.061, 0.0975), (0.061, 0.1175), (-0.003, 0.1175)], 0.002,
         x=HALF - 0.0045, bevel=0.0003, note="bolt carrier (in the port)")
    prof("BrassDeflector", body, anod, [(-0.024, 0.0950), (-0.004, 0.0950), (-0.004, 0.1190), (-0.018, 0.1190)],
         0.0050, x=HALF + 0.0015, bevel=0.0012, rnd=0.003, note="brass deflector")
    # Charging-handle slot along the left side, and the handle on the bolt axis.
    cut(upper, "ChSlot", [((-HALF, 0.150, 0.1125), (0.008, 0.240, 0.0075))])
    prof("ChargingArm", body, steel, [(BOLT[0] - 0.0075, 0.1092), (BOLT[0] + 0.0075, 0.1092),
                                     (BOLT[0] + 0.0085, 0.1158), (BOLT[0] - 0.0065, 0.1158)], 0.026,
         x=-HALF - 0.010, bevel=0.0008, note="charging handle arm")
    lathe("ChargingKnob", body, poly, [(-HALF - 0.020, 0.0), (-HALF - 0.020, 0.0060), (-HALF - 0.022, 0.0072),
                                       (-HALF - 0.033, 0.0072), (-HALF - 0.035, 0.0058), (-HALF - 0.035, 0.0)],
          sides=24, c=(BOLT[0] + 0.001, 0.1125), axis="X")
    # Top rail, full length, slotted.
    rail = xsec("TopRail", body, anod, rail_pts(0.0, UP_TOP, 0.0, 1.0), REAR + 0.003, UP_FRONT - 0.002,
                bevel=0.0005, note="top rail")
    n = int((UP_FRONT - REAR - 0.012) / PITCH)
    cut(rail, "TopSlots", [((0.0, REAR + 0.010 + k * PITCH, RAIL_TOP), (0.030, SLOT, 0.0076)) for k in range(n)])
    # Side rails (3 and 9 o'clock) and the bottom rail at the front.
    for side in (-1, 1):
        r = xsec("SideRail" + ("R" if side > 0 else "L"), body, anod, rail_pts(side * HALF, 0.0905, side, 0.0),
                 0.212, 0.334, bevel=0.0005, note="side rail")
        cut(r, "SideSlots" + ("R" if side > 0 else "L"),
            [((side * (HALF + 0.0095), 0.218 + k * PITCH, 0.0905), (0.0076, SLOT, 0.030)) for k in range(12)])
        for y in (0.222, 0.322):
            lathe("RailScrew%s%d" % ("R" if side > 0 else "L", int(y * 1000)), body, steel,
                  [(side * HALF, 0.0), (side * HALF, 0.0030), (side * (HALF + 0.0012), 0.0030),
                   (side * (HALF + 0.0016), 0.0022), (side * (HALF + 0.0016), 0.0)], sides=12, c=(y, 0.0705), axis="X")
    brail = xsec("BottomRail", body, anod, rail_pts(0.0, 0.0600, 0.0, -1.0), 0.212, 0.340, bevel=0.0005,
                 note="bottom rail")
    cut(brail, "BottomSlots", [((0.0, 0.218 + k * PITCH, 0.0505), (0.030, SLOT, 0.0076)) for k in range(12)])
    # Orange trim: a fine accent line along both sides, just above the upper's bottom edge.
    for side in (-1, 1):
        prof("Trim" + ("R" if side > 0 else "L"), body, orange, [(REAR + 0.006, 0.0858), (0.200, 0.0858),
                                                                 (0.200, 0.0880), (REAR + 0.006, 0.0880)],
             0.0006, x=side * (HALF + 0.0003), bevel=0.0)
    # Round counter, left side at the rear: bezel, dark glass and the glowing count.
    prof("CounterBezel", body, anod, [(-0.124, 0.0925), (-0.086, 0.0925), (-0.086, 0.1150), (-0.124, 0.1150)],
         0.0016, x=-HALF - 0.0008, bevel=0.0006, rnd=0.002, note="round counter bezel")
    prof("CounterGlass", body, glass, [(-0.121, 0.0955), (-0.089, 0.0955), (-0.089, 0.1120), (-0.121, 0.1120)],
         0.0008, x=-HALF - 0.0016, bevel=0.0002, rnd=0.0012, note="round counter display")
    cu = bpy.data.curves.new(PREFIX + "Digits", "FONT")
    cu.body = "20"
    cu.size = 0.0135
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = 0.00008
    txt = bpy.data.objects.new(PREFIX + "Digits", cu)
    txt.matrix_world = Matrix(((0, 0, -1, -HALF - 0.0022), (-1, 0, 0, -0.105), (0, 1, 0, 0.1037), (0, 0, 0, 1)))
    cu.materials.append(digit)
    body.objects.link(txt)
    # Front of the upper: gas block round barrel and piston, the regulator with its lever.
    prof("GasBlock", body, anod, [(UP_FRONT - 0.002, 0.0730), (UP_FRONT + 0.016, 0.0745), (UP_FRONT + 0.016, 0.1150),
                                  (UP_FRONT - 0.002, 0.1170)], 0.031, bevel=0.0015, rnd=0.004, note="gas block")
    lathe("Regulator", body, steel, [(UP_FRONT + 0.016, 0.0), (UP_FRONT + 0.016, 0.0088), (UP_FRONT + 0.027, 0.0088),
                                     (UP_FRONT + 0.029, 0.0072), (UP_FRONT + 0.029, 0.0)], c=(0.0, 0.1050))
    prof("RegulatorLever", body, steel, [(UP_FRONT + 0.019, 0.1050), (UP_FRONT + 0.025, 0.1050),
                                         (UP_FRONT + 0.024, 0.1255), (UP_FRONT + 0.020, 0.1255)], 0.0030,
         x=0.0, bevel=0.0006)
    # Barrel and the AF muzzle brake (three side ports a side, two top ports).
    lathe("Barrel", body, steel, [(UP_FRONT, 0.0), (UP_FRONT, 0.0100), (0.420, 0.0100), (0.428, 0.0093),
                                  (0.478, 0.0093), (0.478, 0.0)])
    brake = lathe("Brake", body, anod, [(0.476, 0.0), (0.476, 0.0108), (0.482, 0.0108), (0.4845, 0.0138),
                                        (MUZZLE - 0.006, 0.0138), (MUZZLE, 0.0118), (MUZZLE, 0.0)], sides=32)
    cut(brake, "BrakePorts", [((0.0, y, BORE), (0.040, 0.0075, 0.0130)) for y in (0.4955, 0.5105, 0.5255)] +
        [((0.0, y, BORE + 0.012), (0.0040, 0.0040, 0.010)) for y in (0.503, 0.518)] +
        [((0.0, MUZZLE, BORE), (0.0090, 0.012, 0.0090))])
    # ---- Lower receiver (polymer): magazine well, front extension under the handguard, rear tang. ----
    lower = prof("Lower", body, poly, [(REAR + 0.003, 0.0750), (0.112, 0.0750), (0.124, 0.0610), (0.206, 0.0610),
                                       (0.206, 0.0530), (0.188, 0.0470), (0.140, 0.0345), (0.110, 0.0230),
                                       (0.108, -0.0060), (0.104, -0.0100), (0.012, -0.0130), (0.009, -0.0080),
                                       (0.010, 0.0310), (-0.056, 0.0320), (-0.063, 0.0365), (-0.112, 0.0440),
                                       (-0.140, 0.0560), (REAR + 0.003, 0.0620)], 0.044, bevel=0.0018, rnd=0.004,
                 note="lower receiver")
    cut(lower, "MagWell", [((0.0, MAG[0] + 0.0010, 0.0), (0.0300, 0.0800, 0.060))])
    prof("TriggerGuard", body, poly, [(0.010, 0.0315), (0.010, 0.0080), (0.000, 0.0020), (-0.040, 0.0020),
                                      (-0.053, 0.0100), (-0.059, 0.0320), (-0.050, 0.0320), (-0.046, 0.0150),
                                      (-0.038, 0.0095), (-0.002, 0.0095), (0.004, 0.0135), (0.004, 0.0315)], 0.016,
         bevel=0.0015, note="trigger guard")
    d.blade("Trigger", body, steel, [(TRIGGER[0], TRIGGER[1], 0.0060), (-0.0355, 0.0250, 0.0055),
                                     (-0.0325, 0.0170, 0.0050), (-0.0270, 0.0115, 0.0045)], 0.0060, note="trigger")
    prof("Grip", body, grip_mat, [(-0.056, 0.0400), (-0.050, 0.0120), (-0.053, -0.0060), (-0.060, -0.0180),
                                  (-0.062, -0.0300), (-0.072, -0.0580), (-0.082, -0.0720), (-0.118, -0.0680),
                                  (-0.121, -0.0560), (-0.110, -0.0200), (-0.104, 0.0100), (-0.106, 0.0280),
                                  (-0.120, 0.0470)], 0.032, bevel=0.0030, rnd=0.007, note="pistol grip")
    # Controls: ambidextrous safety, bolt release (left), magazine release, takedown pins.
    for side in (-1, 1):
        s = "R" if side > 0 else "L"
        lathe("SafetyHub" + s, body, steel, [(side * 0.022, 0.0), (side * 0.022, 0.0060), (side * 0.0245, 0.0060),
                                            (side * 0.0250, 0.0045), (side * 0.0250, 0.0)], sides=20,
              c=(-0.080, 0.0620), axis="X")
        prof("SafetyLever" + s, body, steel, [(-0.082, 0.0590), (-0.058, 0.0650), (-0.057, 0.0700), (-0.080, 0.0660)],
             0.0022, x=side * 0.0258, bevel=0.0006, rnd=0.002)
        lathe("MagRelease" + s, body, steel, [(side * 0.021, 0.0), (side * 0.021, 0.0048), (side * 0.0238, 0.0048),
                                             (side * 0.0243, 0.0036), (side * 0.0243, 0.0)], sides=20,
              c=(0.003, 0.0460), axis="X")
        for y, z in ((-0.134, 0.0660), (0.100, 0.0660)):
            lathe("Pin%s%d" % (s, int(y * 1000)), body, steel,
                  [(side * 0.021, 0.0), (side * 0.021, 0.0038), (side * 0.0228, 0.0038), (side * 0.0232, 0.0030),
                   (side * 0.0232, 0.0)], sides=16, c=(y, z), axis="X")
    prof("BoltRelease", body, steel, [(-0.002, 0.0400), (0.010, 0.0430), (0.011, 0.0520), (-0.002, 0.0500)], 0.0025,
         x=-0.0232, bevel=0.0006, rnd=0.002, note="bolt release")
    # ---- Front and rear gold folding sights (our pattern), red tip on the front post. ----
    prof("RearSightBase", body, gold, [(-0.155, RAIL_TOP), (-0.127, RAIL_TOP), (-0.129, 0.1395), (-0.152, 0.1395)],
         0.026, bevel=0.0010, rnd=0.002, note="rear sight base (gold)")
    lathe("RearSightScrew", body, gold, [(-0.013, 0.0), (-0.013, 0.0035), (-0.0155, 0.0035), (-0.016, 0.0025),
                                         (-0.016, 0.0)], sides=16, c=(-0.141, 0.1340), axis="X")
    for side in (-1, 1):
        prof("RearEar" + ("R" if side > 0 else "L"), body, gold,
             [(-0.149, 0.1390), (-0.131, 0.1390), (-0.136, EYE[1] + 0.005), (-0.144, EYE[1] + 0.005)], 0.0025,
             x=side * 0.0105, bevel=0.0007, rnd=0.002)
    prof("RearLeaf", body, gold, [(-0.144, 0.1390), (-0.136, 0.1390), (-0.137, EYE[1] - 0.004), (-0.143, EYE[1] - 0.004)],
         0.010, bevel=0.0006, rnd=0.0015)
    circ = lambda r: [(r * math.cos(2 * math.pi * i / 32), EYE[1] + r * math.sin(2 * math.pi * i / 32)) for i in range(32)]
    bm = bmesh.new()
    d.bm_tube(bm, circ(0.0068), circ(0.0019), -0.1425, -0.1375, zref=EYE[1])
    d.make("RearAperture", bm, body, gold, "rear sight aperture (gold)", 0.0004)
    prof("FrontSightBase", body, gold, [(FRONT_SIGHT - 0.014, RAIL_TOP), (FRONT_SIGHT + 0.014, RAIL_TOP),
                                        (FRONT_SIGHT + 0.012, 0.1400), (FRONT_SIGHT - 0.012, 0.1400)], 0.026,
         bevel=0.0010, rnd=0.002, note="front sight base (gold)")
    for side in (-1, 1):
        prof("FrontEar" + ("R" if side > 0 else "L"), body, gold,
             [(FRONT_SIGHT - 0.010, 0.1395), (FRONT_SIGHT + 0.010, 0.1395), (FRONT_SIGHT + 0.004, EYE[1] + 0.002),
              (FRONT_SIGHT - 0.004, EYE[1] + 0.002)], 0.0025, x=side * 0.0095, bevel=0.0007, rnd=0.002)
    prof("FrontTower", body, gold, [(FRONT_SIGHT - 0.006, 0.1395), (FRONT_SIGHT + 0.006, 0.1395),
                                    (FRONT_SIGHT + 0.003, 0.1445), (FRONT_SIGHT - 0.003, 0.1445)], 0.0070,
         bevel=0.0006, rnd=0.0015)
    prof("FrontPost", body, gold, [(FRONT_SIGHT - 0.0016, 0.1440), (FRONT_SIGHT + 0.0016, 0.1440),
                                   (FRONT_SIGHT + 0.0016, EYE[1] - 0.0035), (FRONT_SIGHT - 0.0016, EYE[1] - 0.0035)],
         0.0022, bevel=0.0003, note="front post (gold)")
    prof("FrontPostTip", body, red, [(FRONT_SIGHT - 0.0016, EYE[1] - 0.0035), (FRONT_SIGHT + 0.0016, EYE[1] - 0.0035),
                                     (FRONT_SIGHT + 0.0016, EYE[1]), (FRONT_SIGHT - 0.0016, EYE[1])], 0.0022,
         bevel=0.0003, note="front post tip (red)")
    # ---- The AF stock: side-folding hinge, comb with cheek riser, lightening cut, rubber pad. ----
    prof("StockHinge", stockc, anod, [(REAR - 0.020, 0.0780), (REAR, 0.0760), (REAR, UP_TOP), (REAR - 0.020, 0.1200)],
         0.046, bevel=0.0015, rnd=0.003, note="stock hinge block")
    lathe("HingeBarrel", stockc, steel, [(0.078, 0.0), (0.078, 0.0055), (0.120, 0.0055), (0.120, 0.0)], sides=20,
          c=(0.0215, REAR - 0.006), axis="Z")
    lathe("SlingCup", stockc, steel, [(-0.0230, 0.0), (-0.0230, 0.0070), (-0.0270, 0.0070), (-0.0275, 0.0055),
                                      (-0.0275, 0.0)], sides=24, c=(REAR - 0.010, 0.0920), axis="X")
    stock = prof("StockBody", stockc, poly, [(REAR - 0.020, 0.1215), (-0.270, 0.1230), (-0.426, 0.1255),
                                             (-0.426, -0.0040), (-0.406, -0.0040), (-0.330, 0.0600),
                                             (-0.300, 0.0720), (REAR - 0.020, 0.0760)], 0.040, bevel=0.0025,
                 rnd=0.006, note="stock body")
    hole = prof("StockHoleCut", cutc, None, [(-0.326, 0.0980), (-0.410, 0.0980), (-0.410, 0.0120)], 0.060, bevel=0.0,
                rnd=0.008)
    d.cut(stock, hole, "StockHole")
    prof("CheekRiser", stockc, poly, [(-0.262, 0.1200), (-0.408, 0.1225), (-0.408, 0.1385), (-0.280, 0.1360)], 0.036,
         bevel=0.0025, rnd=0.006, note="cheek riser")
    prof("StockLatch", stockc, steel, [(-0.306, 0.0770), (-0.288, 0.0790), (-0.288, 0.0860), (-0.306, 0.0850)], 0.014,
         bevel=0.0008, rnd=0.002, note="length latch")
    for side in (-1, 1):
        prof("StockTrim" + ("R" if side > 0 else "L"), stockc, orange,
             [(-0.180, 0.1120), (-0.420, 0.1150), (-0.420, 0.1172), (-0.180, 0.1142)], 0.0006,
             x=side * 0.0203, bevel=0.0)
    prof("ButtPad", stockc, rubber, [(-0.425, -0.0090), (-0.444, -0.0070), (-0.448, 0.0030), (-0.448, 0.1250),
                                     (-0.444, 0.1340), (-0.425, 0.1340)], 0.044, bevel=0.0020, rnd=0.004,
         note="butt pad")
    # ---- Stand-in for the vanilla magazine (not ours, not exported). ----
    prof("RefMagazine", ref, magmat, [(MAG[0] - 0.0345, 0.0400), (MAG[0] + 0.0385, 0.0400), (MAG[0] + 0.0400, -0.0100),
                                      (MAG[0] + 0.0480, -0.0800), (MAG[0] + 0.0540, -0.1150), (MAG[0] - 0.0170, -0.1220),
                                      (MAG[0] - 0.0250, -0.0850), (MAG[0] - 0.0330, -0.0100)], 0.0285, bevel=0.0012,
         rnd=0.003, note="vanilla magazine (stand-in)")
    for side in (-1, 1):
        for k, z in enumerate((-0.030, -0.070)):
            prof("RefMagRib%s%d" % ("R" if side > 0 else "L", k), ref, magmat,
                 [(MAG[0] - 0.024, z), (MAG[0] + 0.040 + 0.1 * (-0.010 - z) * 0.9, z),
                  (MAG[0] + 0.040 + 0.1 * (-0.010 - z) * 0.9, z + 0.004), (MAG[0] - 0.024, z + 0.004)], 0.0020,
                 x=side * 0.0148, bevel=0.0006)
    prof("RefMagFloor", ref, magmat, [(MAG[0] - 0.0200, -0.1160), (MAG[0] + 0.0580, -0.1110), (MAG[0] + 0.0590, -0.1250),
                                      (MAG[0] - 0.0190, -0.1310)], 0.0320, bevel=0.0015, rnd=0.002)


def harden():
    """Hardened normals on bevelled parts, so long flat faces next to a chamfer or a cut shade flat."""
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            if m.type == "BEVEL":
                m.harden_normals = True
        if ob.type == "MESH" and ob.name in (PREFIX + "Upper", PREFIX + "UpperFront", PREFIX + "Lower", PREFIX + "StockBody"):
            ob.data.polygons.foreach_set("use_smooth", [False] * len(ob.data.polygons))


def render(out, tag="pk_v2"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    world = bpy.data.worlds.new("PK_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.20, 0.21, 0.22, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = world
    for name, loc, energy, size in (("Top", (0.0, 0.05, 1.3), 40.0, 2.0), ("KeyR", (1.1, -0.4, 0.7), 26.0, 1.0),
                                    ("KeyL", (-1.1, 0.4, 0.7), 20.0, 1.0), ("Rim", (0.0, 1.4, 0.4), 16.0, 0.8)):
        lt = bpy.data.lights.new("PK_" + name, "AREA")
        lt.energy, lt.size = energy, size
        ob = bpy.data.objects.new("PK_" + name, lt)
        ob.location = loc
        ob.rotation_euler = (Vector((0, 0.05, 0.08)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(ob)
    cam = bpy.data.objects.new("PK_Cam", bpy.data.cameras.new("PK_Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    obs = [o for o in bpy.data.objects if o.type in ("MESH", "FONT") and o.name.startswith(PREFIX) and not o.hide_render]
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    os.makedirs(out, exist_ok=True)
    views = (("right", Vector((1, 0, 0)), True), ("left", Vector((-1, 0, 0)), True),
             ("front34", Vector((1.0, 0.55, 0.18)), False), ("rear34", Vector((-1.0, -0.6, 0.30)), False))
    for name, direction, ortho in views:
        direction.normalize()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        cam.data.clip_start = 0.01
        if ortho:
            cam.data.ortho_scale = (hi.y - lo.y) * 1.06
            cam.location = centre + direction * 3.0
        else:
            cam.data.lens = 50
            cam.location = centre + direction * 1.55
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, "%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)
    cam.data.type = "PERSP"
    cam.data.lens = 50
    cam.data.clip_start = 0.005          # the aperture is only a few centimetres from the eye
    cam.location = Vector((0.0, EYE[0] - 0.05, EYE[1]))
    cam.rotation_euler = (Vector((0.0, 0.30, EYE[1])) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, tag + "_shooter.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build()
    harden()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afpk_blockout.blend"))
    out = os.path.abspath(args[0]) if args else os.path.join(os.path.dirname(HERE), "docs", "img")
    render(out)
