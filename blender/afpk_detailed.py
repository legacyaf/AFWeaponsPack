"""blender -b --factory-startup --python afpk_detailed.py -- <out folder>

The PeaceKeeper (AF modern battle rifle, our SCAR): the game model, built from the approved design
model (afpk_blockout.py, v2 with the sights at half height, owner 2026-11-26) and split for DayZ:

- the rifle (prefix PK_): everything on the vanilla SCAR-H's frame, with the moving parts on the
  vanilla bones (trigger, bolt, charging, firemode, boltrelease) and the vanilla proxies (magazine,
  stock, optic, light, improvised suppressor, wrap) where the probe measured them;
- the AF stock (prefix PKS_): its own item on the vanilla stock slot, built round the stock proxy
  point and turned the way the vanilla stocks are (docs/AF_SCAR.md).

Not exported (prefix PKR_): a stand-in for the vanilla 20-round magazine and the counter's "20", for
the previews only. The magazine is the game's own; the count is a texture swapped by script.

Texture sheets (afpk_dayz_export): the upper (set 0), the rails and muzzle, the polymer lower, the
small parts (steel, gold, orange, red), and the counter display on a set of its own so its texture
can be swapped by script.
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
import afpk_blockout as dm  # noqa: E402

PREFIX, STOCK_PREFIX, REF_PREFIX = "PK_", "PKS_", "PKR_"
BORE, MUZZLE, EYE, TRIGGER, MAG, BOLT = dm.BORE, dm.MUZZLE, dm.EYE, dm.TRIGGER, dm.MAG, dm.BOLT
FRONT_SIGHT, REAR, UP_TOP, RAIL_TOP, HALF, UP_FRONT = dm.FRONT_SIGHT, dm.REAR, dm.UP_TOP, dm.RAIL_TOP, dm.HALF, dm.UP_FRONT
PITCH, SLOT = dm.PITCH, dm.SLOT

# Where the probe found the vanilla attachments (working frame: x = z_dayz, y = -x_dayz, z = y_dayz).
STOCK_ORIGIN = (0.0, -0.2897, 0.0715)
PROXY_AT = {
    "Proxy_Magazine": (0.0, 0.0567, 0.0245),
    "Proxy_Stock": STOCK_ORIGIN,
    "Proxy_Optic": (0.0, -0.0162, 0.1363),
    "Proxy_Light": (0.0282, 0.2521, 0.0905),
    "Proxy_Suppressor": (0.0, 0.5117, 0.0886),
    "Proxy_Wrap": (0.0, 0.0747, 0.1465),
}

# Texture sheets: the parts given a copy of the anodised material, by sheet.
SHEET_PARTS = {
    "AnodisedRail": ("TopRail", "SideRailR", "SideRailL", "BottomRail", "Brake", "GasBlock"),
}


def zones(which):
    """Where the rifle is handled and knocked (centre, half sizes, strength): drives polish and wear."""
    if which == "stock":
        return (((0.0, 0.0, 0.0), (0.030, 0.030, 0.030), 0.2),)
    return (((0.0, -0.090, -0.015), (0.020, 0.040, 0.055), 0.9),       # pistol grip
            ((0.0, MAG[0], -0.005), (0.026, 0.050, 0.012), 0.9),         # magazine well mouth
            ((0.0, 0.140, 0.075), (0.030, 0.070, 0.025), 0.8),           # where the left hand holds
            ((-0.030, BOLT[0], BOLT[1]), (0.012, 0.020, 0.012), 1.0),     # charging handle
            ((0.0, 0.510, BORE), (0.016, 0.035, 0.016), 0.9),            # muzzle brake
            ((0.0, 0.10, RAIL_TOP), (0.012, 0.260, 0.004), 0.5),         # rail edges: optics, kit
            ((0.0, 0.250, 0.0905), (0.034, 0.090, 0.012), 0.5))          # side rails: lights, hands


def materials(which="rifle"):
    import afm41_pathfinder_detailed as m41
    import af_finish
    anod = d.material("Anodised", (0.028, 0.028, 0.030), rough=0.52, metal=0.35, bump=0.03, bump_scale=1100,
                      rough_var=0.08)
    old_prefix, m41.PREFIX = m41.PREFIX, d.PREFIX
    try:
        af_finish.worn(anod, MUZZLE if which == "rifle" else 9.0, zones(which), palette="anodized")
    finally:
        m41.PREFIX = old_prefix
    return {
        "anod": anod,
        "poly": d.material("Polymer", (0.022, 0.022, 0.023), rough=0.74, bump=0.20, bump_scale=600, rough_var=0.08,
                           scratches=0.15),
        "grip": d.material("GripPolymer", (0.022, 0.022, 0.023), rough=0.82, bump=0.20, bump_scale=600, stipple=0.8),
        "steel": d.material("Steel", (0.10, 0.10, 0.105), rough=0.32, metal=0.9, machining=0.3),
        "rubber": d.material("Rubber", (0.012, 0.012, 0.012), rough=0.90, bump=0.25, bump_scale=500, stipple=0.6),
        "orange": d.material("Orange", (0.75, 0.28, 0.04), rough=0.50, wear=0.25, wear_rgb=(0.10, 0.08, 0.06)),
        # Deeper and shinier (2026-11-27): the first gold baked pale and read cream, then khaki, in game.
        "gold": d.material("Gold", (0.72, 0.48, 0.12), rough=0.22, metal=1.0, wear=0.08, wear_rgb=(0.85, 0.62, 0.25)),
        "red": d.material("Red", (0.85, 0.03, 0.02), rough=0.40),
        "counter": d.material("Counter", (0.004, 0.004, 0.005), rough=0.08),
    }


def _helpers(cutc):
    def prof(name, col, mat, pts, width, x=0.0, bevel=0.0012, rnd=0.0, note=""):
        return d.profile(name, col, mat, pts, width, x=x, bevel=bevel, note=note, round=rnd)

    def xsec(name, col, mat, pts, y0, y1, bevel=0.0010, note=""):
        bm = bmesh.new()
        d.bm_xsec(bm, pts, y0, y1)
        return d.make(name, bm, col, mat, note, bevel)

    def lathe(name, col, mat, pr, sides=32, c=(0.0, BORE), axis="Y", bevel=0.0004, note=""):
        bm = bmesh.new()
        d.bm_lathe(bm, pr, sides=sides, c=c, axis=axis)
        return d.make(name, bm, col, mat, note or name, bevel)

    def cut(target, name, boxes):
        bm = bmesh.new()
        for c, s in boxes:
            d.bm_box(bm, c, s)
        d.cut(target, d.make(name, bm, cutc, None, "cutter", 0.0), name)

    return prof, xsec, lathe, cut


def split_sheets(src):
    for mname, parts in SHEET_PARTS.items():
        old = bpy.data.materials.get(d.PREFIX + mname)
        if old is not None:
            old.name = old.name + "_old"
        mat = src.copy()
        mat.name = d.PREFIX + mname
        for part in parts:
            for slot in bpy.data.objects[d.PREFIX + part].material_slots:
                if slot.material == src:
                    slot.material = mat


def harden(cols):
    for col in cols:
        for ob in col.objects:
            for m in ob.modifiers:
                if m.type == "BEVEL":
                    m.harden_normals = True
            if ob.type == "MESH" and ob.name[len(d.PREFIX):] in ("Upper", "UpperFront", "Lower", "StockBody"):
                ob.data.polygons.foreach_set("use_smooth", [False] * len(ob.data.polygons))


def build():
    """The rifle (prefix PK_)."""
    d.PREFIX = PREFIX
    d.CLEAN_TOPO = True
    d.clean()
    d.CUTS = True
    body = d.collection("Body")
    moving = d.collection("Moving")
    memory = d.collection("Memory")
    proxies = d.collection("Proxies")
    cutc = d.collection("Cutters")
    m = materials("rifle")
    anod, poly, grip, steel, orange, gold, red = (m[k] for k in ("anod", "poly", "grip", "steel", "orange", "gold", "red"))
    prof, xsec, lathe, cut = _helpers(cutc)

    # --- Upper receiver -----------------------------------------------------------------------
    upper = xsec("Upper", body, anod, [(-HALF + 0.0015, 0.0745), (HALF - 0.0015, 0.0745), (HALF - 0.0015, 0.0840),
                                       (HALF, 0.0855), (HALF, 0.1150), (HALF - 0.0055, UP_TOP),
                                       (-HALF + 0.0055, UP_TOP), (-HALF, 0.1150), (-HALF, 0.0855),
                                       (-HALF + 0.0015, 0.0840)], REAR, UP_FRONT, bevel=0.0012,
                 note="upper receiver")
    prof("UpperFront", body, anod, [(0.112, 0.0755), (0.124, 0.0600), (UP_FRONT - 0.004, 0.0600), (UP_FRONT, 0.0640),
                                    (UP_FRONT, 0.0755)], 2 * HALF, bevel=0.0012, note="upper, handguard section")
    cut(upper, "EjectPort", [((HALF, 0.029, 0.1075), (0.010, 0.066, 0.021))])
    prof("BrassDeflector", body, anod, [(-0.024, 0.0950), (-0.004, 0.0950), (-0.004, 0.1190), (-0.018, 0.1190)],
         0.0050, x=HALF + 0.0015, bevel=0.0012, rnd=0.003, note="brass deflector")
    cut(upper, "ChSlot", [((-HALF, 0.150, 0.1125), (0.008, 0.240, 0.0075))])
    rail = xsec("TopRail", body, anod, dm.rail_pts(0.0, UP_TOP, 0.0, 1.0), REAR + 0.003, UP_FRONT - 0.002,
                bevel=0.0005, note="top rail")
    n = int((UP_FRONT - REAR - 0.012) / PITCH)
    cut(rail, "TopSlots", [((0.0, REAR + 0.010 + k * PITCH, RAIL_TOP), (0.030, SLOT, 0.0076)) for k in range(n)])
    for side in (-1, 1):
        s = "R" if side > 0 else "L"
        r = xsec("SideRail" + s, body, anod, dm.rail_pts(side * HALF, 0.0905, side, 0.0), 0.212, 0.334, bevel=0.0005,
                 note="side rail")
        cut(r, "SideSlots" + s, [((side * (HALF + 0.0095), 0.218 + k * PITCH, 0.0905), (0.0076, SLOT, 0.030))
                                 for k in range(12)])
        bm = bmesh.new()
        for y in (0.222, 0.322):
            d.bm_lathe(bm, [(side * HALF, 0.0), (side * HALF, 0.0030), (side * (HALF + 0.0012), 0.0030),
                            (side * (HALF + 0.0016), 0.0022), (side * (HALF + 0.0016), 0.0)], sides=12, c=(y, 0.0705),
                       axis="X")
        d.make("RailScrews" + s, bm, body, steel, "rail screws", 0.0003)
        prof("Trim" + s, body, orange, [(REAR + 0.006, 0.0858), (0.200, 0.0858), (0.200, 0.0880), (REAR + 0.006, 0.0880)],
             0.0006, x=side * (HALF + 0.0003), bevel=0.0, note="orange trim line")
    brail = xsec("BottomRail", body, anod, dm.rail_pts(0.0, 0.0600, 0.0, -1.0), 0.212, 0.340, bevel=0.0005,
                 note="bottom rail")
    cut(brail, "BottomSlots", [((0.0, 0.218 + k * PITCH, 0.0505), (0.030, SLOT, 0.0076)) for k in range(12)])
    # Round counter: bezel and the display (its own texture set, swapped by script).
    prof("CounterBezel", body, anod, [(-0.124, 0.0925), (-0.086, 0.0925), (-0.086, 0.1150), (-0.124, 0.1150)],
         0.0016, x=-HALF - 0.0008, bevel=0.0006, rnd=0.002, note="round counter bezel")
    prof("CounterDisplay", body, m["counter"], [(-0.121, 0.0955), (-0.089, 0.0955), (-0.089, 0.1120),
                                                (-0.121, 0.1120)], 0.0008, x=-HALF - 0.0016, bevel=0.0002,
         note="round counter display (texture swapped by script)")
    # Gas block, regulator, barrel and the AF brake.
    prof("GasBlock", body, anod, [(UP_FRONT - 0.002, 0.0730), (UP_FRONT + 0.016, 0.0745), (UP_FRONT + 0.016, 0.1150),
                                  (UP_FRONT - 0.002, 0.1170)], 0.031, bevel=0.0015, rnd=0.004, note="gas block")
    bm = bmesh.new()
    d.bm_lathe(bm, [(UP_FRONT + 0.016, 0.0), (UP_FRONT + 0.016, 0.0088), (UP_FRONT + 0.027, 0.0088),
                    (UP_FRONT + 0.029, 0.0072), (UP_FRONT + 0.029, 0.0)], sides=32, c=(0.0, 0.1050))
    d.bm_profile(bm, [(UP_FRONT + 0.019, 0.1050), (UP_FRONT + 0.025, 0.1050), (UP_FRONT + 0.024, 0.1255),
                      (UP_FRONT + 0.020, 0.1255)], 0.0030)
    d.make("Regulator", bm, body, steel, "gas regulator and lever", 0.0005)
    lathe("Barrel", body, steel, [(UP_FRONT, 0.0), (UP_FRONT, 0.0100), (0.420, 0.0100), (0.428, 0.0093),
                                  (0.478, 0.0093), (0.478, 0.0)], note="barrel")
    brake = lathe("Brake", body, anod, [(0.476, 0.0), (0.476, 0.0108), (0.482, 0.0108), (0.4845, 0.0138),
                                        (MUZZLE - 0.006, 0.0138), (MUZZLE, 0.0118), (MUZZLE, 0.0)], note="AF muzzle brake")
    cut(brake, "BrakePorts", [((0.0, y, BORE), (0.040, 0.0075, 0.0130)) for y in (0.4955, 0.5105, 0.5255)] +
        [((0.0, y, BORE + 0.012), (0.0040, 0.0040, 0.010)) for y in (0.503, 0.518)] +
        [((0.0, MUZZLE, BORE), (0.0090, 0.012, 0.0090))])

    # --- Lower receiver ------------------------------------------------------------------------
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
    prof("Grip", body, grip, [(-0.056, 0.0400), (-0.050, 0.0120), (-0.053, -0.0060), (-0.060, -0.0180),
                              (-0.062, -0.0300), (-0.072, -0.0580), (-0.082, -0.0720), (-0.118, -0.0680),
                              (-0.121, -0.0560), (-0.110, -0.0200), (-0.104, 0.0100), (-0.106, 0.0280),
                              (-0.120, 0.0470)], 0.032, bevel=0.0030, rnd=0.007, note="pistol grip")
    bm = bmesh.new()
    for side in (-1, 1):
        d.bm_lathe(bm, [(side * 0.022, 0.0), (side * 0.022, 0.0060), (side * 0.0245, 0.0060), (side * 0.0250, 0.0045),
                        (side * 0.0250, 0.0)], sides=20, c=(-0.080, 0.0620), axis="X")
        d.bm_lathe(bm, [(side * 0.021, 0.0), (side * 0.021, 0.0048), (side * 0.0238, 0.0048), (side * 0.0243, 0.0036),
                        (side * 0.0243, 0.0)], sides=20, c=(0.003, 0.0460), axis="X")
        for y, z in ((-0.134, 0.0660), (0.100, 0.0660)):
            d.bm_lathe(bm, [(side * 0.021, 0.0), (side * 0.021, 0.0038), (side * 0.0228, 0.0038), (side * 0.0232, 0.0030),
                            (side * 0.0232, 0.0)], sides=16, c=(y, z), axis="X")
    d.make("LowerParts", bm, body, steel, "safety hubs, magazine release, takedown pins", 0.0004)

    # --- Moving parts, on the vanilla bones ----------------------------------------------------------
    d.blade("Trigger", moving, steel, [(TRIGGER[0], TRIGGER[1], 0.0060), (-0.0355, 0.0250, 0.0055),
                                       (-0.0325, 0.0170, 0.0050), (-0.0270, 0.0115, 0.0045)], 0.0060, note="trigger")
    prof("BoltCarrier", moving, steel, [(-0.003, 0.0975), (0.061, 0.0975), (0.061, 0.1175), (-0.003, 0.1175)], 0.002,
         x=HALF - 0.0045, bevel=0.0003, note="bolt carrier, seen in the port")
    bm = bmesh.new()
    d.bm_profile(bm, [(BOLT[0] - 0.0075, 0.1092), (BOLT[0] + 0.0075, 0.1092), (BOLT[0] + 0.0085, 0.1158),
                      (BOLT[0] - 0.0065, 0.1158)], 0.026, x=-HALF - 0.010)
    d.make("ChargingHandle", bm, moving, steel, "charging handle arm", 0.0008)
    lathe("ChargingKnob", moving, poly, [(-HALF - 0.020, 0.0), (-HALF - 0.020, 0.0060), (-HALF - 0.022, 0.0072),
                                         (-HALF - 0.033, 0.0072), (-HALF - 0.035, 0.0058), (-HALF - 0.035, 0.0)],
          sides=24, c=(BOLT[0] + 0.001, 0.1125), axis="X", note="charging handle knob")
    bm = bmesh.new()
    for side in (-1, 1):
        d.bm_profile(bm, [(-0.082, 0.0590), (-0.058, 0.0650), (-0.057, 0.0700), (-0.080, 0.0660)], 0.0022,
                     x=side * 0.0258)
    d.make("Safety", bm, moving, steel, "ambidextrous safety levers", 0.0006)
    prof("BoltRelease", moving, steel, [(-0.002, 0.0400), (0.010, 0.0430), (0.011, 0.0520), (-0.002, 0.0500)], 0.0025,
         x=-0.0232, bevel=0.0006, rnd=0.002, note="bolt release")

    # --- Gold sights, half height (owner), red tip on the front post ------------------------------
    bm = bmesh.new()
    d.bm_profile(bm, d.fillet([(-0.155, RAIL_TOP), (-0.127, RAIL_TOP), (-0.129, 0.1395), (-0.152, 0.1395)], 0.002), 0.026)
    # Ghost ring (owner 2026-11-27, after the first-person check): a thin ring with a 7 mm hole on a slim
    # stem, low slim ears. The 4 mm peephole in a 14 mm disc hid the front post and the target.
    for side in (-1, 1):
        d.bm_profile(bm, d.fillet([(-0.146, 0.1390), (-0.134, 0.1390), (-0.137, EYE[1] + 0.0035),
                                   (-0.143, EYE[1] + 0.0035)], 0.0015), 0.0020, x=side * 0.0098)
    d.bm_profile(bm, d.fillet([(-0.1425, 0.1390), (-0.1375, 0.1390), (-0.1385, EYE[1] - 0.0045),
                               (-0.1415, EYE[1] - 0.0045)], 0.0008), 0.0040)
    circ = lambda r: [(r * math.cos(2 * math.pi * i / 32), EYE[1] + r * math.sin(2 * math.pi * i / 32)) for i in range(32)]
    d.bm_tube(bm, circ(0.0052), circ(0.0035), -0.1415, -0.1385, zref=EYE[1])
    d.bm_lathe(bm, [(-0.013, 0.0), (-0.013, 0.0035), (-0.0155, 0.0035), (-0.016, 0.0025), (-0.016, 0.0)], sides=16,
               c=(-0.141, 0.1340), axis="X")
    d.make("RearSight", bm, body, gold, "rear sight (gold): base, ears, ghost ring", 0.0006)
    bm = bmesh.new()
    d.bm_profile(bm, d.fillet([(FRONT_SIGHT - 0.014, RAIL_TOP), (FRONT_SIGHT + 0.014, RAIL_TOP),
                               (FRONT_SIGHT + 0.012, 0.1400), (FRONT_SIGHT - 0.012, 0.1400)], 0.002), 0.026)
    for side in (-1, 1):
        d.bm_profile(bm, d.fillet([(FRONT_SIGHT - 0.010, 0.1395), (FRONT_SIGHT + 0.010, 0.1395),
                                   (FRONT_SIGHT + 0.004, EYE[1] + 0.002), (FRONT_SIGHT - 0.004, EYE[1] + 0.002)], 0.002),
                     0.0025, x=side * 0.0095)
    d.bm_profile(bm, d.fillet([(FRONT_SIGHT - 0.006, 0.1395), (FRONT_SIGHT + 0.006, 0.1395),
                               (FRONT_SIGHT + 0.003, 0.1445), (FRONT_SIGHT - 0.003, 0.1445)], 0.0015), 0.0070)
    d.bm_profile(bm, [(FRONT_SIGHT - 0.0016, 0.1440), (FRONT_SIGHT + 0.0016, 0.1440), (FRONT_SIGHT + 0.0016, EYE[1] - 0.0035),
                      (FRONT_SIGHT - 0.0016, EYE[1] - 0.0035)], 0.0022)
    d.make("FrontSight", bm, body, gold, "front sight (gold): base, ears, post", 0.0005)
    prof("FrontPostTip", body, red, [(FRONT_SIGHT - 0.0016, EYE[1] - 0.0035), (FRONT_SIGHT + 0.0016, EYE[1] - 0.0035),
                                     (FRONT_SIGHT + 0.0016, EYE[1]), (FRONT_SIGHT - 0.0016, EYE[1])], 0.0022,
         bevel=0.0003, note="front post tip (red)")

    split_sheets(anod)
    harden((body, moving))

    # --- Memory points (the vanilla SCAR-H's names, measured in game) and proxies -----------------
    for name, loc, note in (
            ("Mem_Muzzle", (0.0, 0.5423, 0.0887), "'usti hlavne'"),
            ("Mem_BarrelEnd", (0.0, 0.0741, 0.0888), "'konec hlavne'"),
            ("Mem_Eye", (0.0, -0.19, EYE[1]), "'eye': on our lowered sight line (owner), 48 mm behind the aperture so the ring shows"),
            ("Mem_EyeScope", (0.0, -0.1465, 0.1716), "'eyescope'"),
            ("Mem_CaseStart", (0.0225, 0.0037, 0.0968), "'nabojnicestart'"),
            ("Mem_CaseEnd", (0.0870, -0.0621, 0.1224), "'nabojniceend'"),
            ("Mem_TriggerAxis", (-0.0200, -0.0361, 0.0367), "'trigger_axis'"),
            ("Mem_BoltAxis", (0.0, BOLT[0], BOLT[1]), "'bolt_axis'"),
            ("Mem_FrontSightAxis", (0.0100, 0.3043, 0.1320), "'frontsight_axis'"),
            ("Mem_MagOutAxis", (0.0, 0.0432, -0.0199), "'magout_axis'"),
            ("Mem_InvView", (0.3724, 0.2032, 0.0565), "'invview'"),
            ("Mem_CeCenter", (-0.0041, 0.2032, 0.0565), "'ce_center'")):
        d.empty(name, memory, loc, note)
    for name, loc in PROXY_AT.items():
        d.empty(name, proxies, loc, name, kind="ARROWS", size=0.03)


def build_stock():
    """The AF stock (prefix PKS_), built in the rifle's frame and then turned into the stock slot's frame."""
    d.PREFIX = STOCK_PREFIX
    d.CLEAN_TOPO = False         # the clean caps broke the filleted stock outlines and its cut (2026-11-26)
    d.clean()
    d.CUTS = True
    body = d.collection("Body")
    d.collection("Moving")
    cutc = d.collection("Cutters")
    m = materials("stock")
    anod, poly, steel, orange = m["anod"], m["poly"], m["steel"], m["orange"]
    prof, xsec, lathe, cut = _helpers(cutc)
    prof("Hinge", body, anod, [(REAR - 0.020, 0.0780), (REAR, 0.0760), (REAR, UP_TOP), (REAR - 0.020, 0.1200)], 0.046,
         bevel=0.0015, rnd=0.003, note="stock hinge block")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.078, 0.0), (0.078, 0.0055), (0.120, 0.0055), (0.120, 0.0)], sides=20, c=(0.0215, REAR - 0.006),
               axis="Z")
    d.bm_lathe(bm, [(-0.0230, 0.0), (-0.0230, 0.0070), (-0.0270, 0.0070), (-0.0275, 0.0055), (-0.0275, 0.0)], sides=24,
               c=(REAR - 0.010, 0.0920), axis="X")
    d.bm_profile(bm, d.fillet([(-0.306, 0.0770), (-0.288, 0.0790), (-0.288, 0.0860), (-0.306, 0.0850)], 0.002), 0.014)
    d.make("StockSteel", bm, body, steel, "hinge pin, sling cup, length latch", 0.0006)
    stock = prof("StockBody", body, poly, [(REAR - 0.020, 0.1215), (-0.270, 0.1230), (-0.426, 0.1255), (-0.426, -0.0040),
                                           (-0.406, -0.0040), (-0.330, 0.0600), (-0.300, 0.0720), (REAR - 0.020, 0.0760)],
                 0.040, bevel=0.0025, rnd=0.006, note="stock body")
    hole = d.profile("StockHoleCut", cutc, None, [(-0.326, 0.0980), (-0.410, 0.0980), (-0.410, 0.0120)], 0.060,
                     bevel=0.0, round=0.008)
    d.cut(stock, hole, "StockHole")
    prof("CheekRiser", body, poly, [(-0.262, 0.1200), (-0.408, 0.1225), (-0.408, 0.1385), (-0.280, 0.1360)], 0.036,
         bevel=0.0025, rnd=0.006, note="cheek riser")
    bm = bmesh.new()
    for side in (-1, 1):
        d.bm_profile(bm, [(-0.180, 0.1120), (-0.420, 0.1150), (-0.420, 0.1172), (-0.180, 0.1142)], 0.0006,
                     x=side * 0.0203)
    d.make("StockTrim", bm, body, orange, "orange trim", 0.0)
    prof("ButtPad", body, m["rubber"], [(-0.425, -0.0090), (-0.444, -0.0070), (-0.448, 0.0030), (-0.448, 0.1250),
                                        (-0.444, 0.1340), (-0.425, 0.1340)], 0.044, bevel=0.0020, rnd=0.004,
         note="butt pad")
    harden((body,))
    to_stock_frame(True)


def STOCK_MATRIX():
    """Rifle working frame -> the stock slot's frame: about the slot point, turned -90 degrees about X
    (the vanilla stocks' up axis points backwards along the rifle)."""
    return Matrix.Rotation(math.radians(-90.0), 4, "X") @ Matrix.Translation(-Vector(STOCK_ORIGIN))


def to_stock_frame(on):
    mat = STOCK_MATRIX() if on else STOCK_MATRIX().inverted()
    bpy.context.view_layer.update()          # matrix_world is stale until the scene is evaluated
    for cname in ("Body", "Cutters"):
        col = bpy.data.collections.get(STOCK_PREFIX + cname)
        for ob in col.objects:
            ob.matrix_world = mat @ ob.matrix_world
    bpy.context.view_layer.update()


def build_reference():
    """Previews only (prefix PKR_): the vanilla magazine's stand-in and the counter's "20"."""
    d.PREFIX = REF_PREFIX
    d.CLEAN_TOPO = False
    d.clean()
    ref = d.collection("Reference")
    magmat = d.material("RefMagazine", (0.030, 0.030, 0.032), rough=0.55, metal=0.5)
    d.profile("RefMagazine", ref, magmat, [(MAG[0] - 0.0345, 0.0400), (MAG[0] + 0.0385, 0.0400), (MAG[0] + 0.0400, -0.0100),
                                          (MAG[0] + 0.0480, -0.0800), (MAG[0] + 0.0540, -0.1150), (MAG[0] - 0.0170, -0.1220),
                                          (MAG[0] - 0.0250, -0.0850), (MAG[0] - 0.0330, -0.0100)], 0.0285, bevel=0.0012,
              round=0.003)
    d.profile("RefMagFloor", ref, magmat, [(MAG[0] - 0.0200, -0.1160), (MAG[0] + 0.0580, -0.1110), (MAG[0] + 0.0590, -0.1250),
                                          (MAG[0] - 0.0190, -0.1310)], 0.0320, bevel=0.0015, round=0.002)
    cu = bpy.data.curves.new(REF_PREFIX + "Digits", "FONT")
    cu.body = "20"
    cu.size = 0.0135
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = 0.00008
    txt = bpy.data.objects.new(REF_PREFIX + "Digits", cu)
    txt.matrix_world = Matrix(((0, 0, -1, -HALF - 0.0022), (-1, 0, 0, -0.105), (0, 1, 0, 0.1037), (0, 0, 0, 1)))
    cu.materials.append(dm.emissive("Digits", (1.0, 0.42, 0.04), 6.0))
    ref.objects.link(txt)


def build_all():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    build()
    build_stock()
    build_reference()


def render(out):
    """Studio previews of the whole rifle, the stock turned back onto the rifle."""
    to_stock_frame(False)
    try:
        for ob in bpy.data.objects:            # the design model's render frames every PK_ part: show all three
            if ob.name.startswith((STOCK_PREFIX, REF_PREFIX)) and not any(c.name.endswith("Cutters") for c in ob.users_collection):
                ob["af_preview"] = True
        old = dm.PREFIX
        dm.PREFIX = "PK"                        # matches PK_, PKS_ and PKR_
        dm.render(out, "pk_model")
        dm.PREFIX = old
    finally:
        to_stock_frame(True)


STARTED = 0.0

if __name__ == "__main__":
    import time
    STARTED = time.time()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afpk_detailed.blend"))
    render(os.path.abspath(args[0]) if args else os.path.join(os.path.dirname(HERE), "docs", "img"))
