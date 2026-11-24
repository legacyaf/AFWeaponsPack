"""blender -b --factory-startup --python afm107_detailed.py -- <out folder>

AF M107A1, modelled in real geometry to the working blueprint (afm107_blueprint.py, rev 4):
openings are cut (Boolean), not painted; parts are rounded and chamfered as made.

- Upper receiver: one pressing, hollow at the front (the handguard), with 2 x 8 lightening holes cut
  through both walls, the ejection window cut in the right side with the bolt carrier inside it,
  the rail on top, ribbed cheek plates on both sides.
- Barrel: fluted, running from inside the receiver to the brake; the brake has two port chambers cut
  through it and a bore through its front.
- Lower: butt and recoil pad, the stock's upright with the monopod, the open rear-grip loop, the
  trigger housing, pistol grip with finger grooves, the angled magazine-well plate.
- Magazine: steel box with raised ribs and witness holes.
- Bipod yoke (no legs: owner), lock pins with their rings, rear sight, front sight, charging handle, safety.

Working frame as the other AF weapons: +Y forward, +Z up, +X right; metres; y = 0 at the trigger,
the bore at z = BORE. Renders: side, three-quarter front (as the owner's reference), rear, and a
close-up of the action.
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
P = bp.PARTS
fx = bp.fx
# The vanilla SVD's frame (measured in game, docs/M107.md): the M107A1's trigger pivot sits on the
# SVD's trigger_axis, so the SVD's hand animations close on its grip.
SVD_TRIGGER = (-0.0819, 0.0645)                     # working y, z of the SVD's trigger_axis
X_TRIGGER = (P["trigger"][0][0] + P["trigger"][1][0]) / 2     # blueprint x of the trigger pivot (its top)
Z_TRIGGER = P["trigger"][0][1]                       # blueprint z of the pivot (mm below the bore)
BORE = SVD_TRIGGER[1] - Z_TRIGGER / 1000.0           # 0.1525: 52 mm above the SVD's bore


def Y(x_mm):
    return (x_mm - X_TRIGGER) / 1000.0 + SVD_TRIGGER[0]


def Zm(z_mm):
    return BORE + z_mm / 1000.0


def side_pts(v):
    if isinstance(v, tuple):
        x0, x1, z0, z1 = v
        v = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    return [(Y(x), Zm(z)) for x, z in v]


def bbox(v):
    if isinstance(v, tuple):
        return v
    xs, zs = [p[0] for p in v], [p[1] for p in v]
    return min(xs), max(xs), min(zs), max(zs)


def lathe(name, col, mat, prof_mm, sides=32, closed=False, cap=True, bevel=0.0, note=""):
    """prof_mm: [(x_mm along the bore, radius_mm), ...] round the bore."""
    bm = bmesh.new()
    d.bm_lathe(bm, [(Y(x), r / 1000.0) for x, r in prof_mm], sides=sides, c=(0.0, BORE), closed=closed, cap=cap)
    return d.make(name, bm, col, mat, note, bevel)


def ring(bm, centre, radius, tube, seg=24, sides=8):
    """A ring standing in the YZ plane (seen round from the side), e.g. a lock-pin pull ring."""
    cx, cy, cz = centre
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ry, rz = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((cx + tube * math.sin(2 * math.pi * j / sides),
                                    cy + (radius + tube * math.cos(2 * math.pi * j / sides)) * ry,
                                    cz + (radius + tube * math.cos(2 * math.pi * j / sides)) * rz)) for j in range(sides)])
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for j in range(sides):
            bm.faces.new((a[j], a[(j + 1) % sides], b[(j + 1) % sides], b[j]))


MAG_PREFIX, SCOPE_PREFIX = "M107M_", "M107S_"
# The magazine model's origin is the SVD's magazine proxy point, so the SVD's reload animations hold
# it where they expect; the scope model's origin is the middle of its tube.
MAG_PROXY = (0.0, 0.0542, 0.0409)


def materials():
    return {"steel": d.material("Cerakote", (0.028, 0.029, 0.030), rough=0.50, metal=0.25, bump=0.02, bump_scale=900),
            "bare": d.material("Steel", (0.10, 0.10, 0.105), rough=0.30, metal=0.9),
            "dark": d.material("Inside", (0.006, 0.006, 0.007), rough=0.7),
            "rubber": d.material("Rubber", (0.010, 0.010, 0.010), rough=0.92),
            "poly": d.material("Polymer", (0.020, 0.020, 0.021), rough=0.75, bump=0.06, bump_scale=1400)}


def smooth(cols):
    """Clean shading on the big faces left by the Boolean cuts: area-weighted normals, edges kept sharp."""
    for col in cols:
        for ob in col.objects:
            if ob.type == "MESH":
                for face in ob.data.polygons:
                    face.use_smooth = True
                mod = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
                mod.mode = "FACE_AREA"
                mod.weight = 50
                mod.keep_sharp = True


def offset(col, v):
    for ob in col.objects:
        ob.location = (ob.location[0] - v[0], ob.location[1] - v[1], ob.location[2] - v[2])


def build():
    """The rifle (prefix M107_): everything but the magazine and the scope, which are models of their own."""
    d.PREFIX = PREFIX
    d.clean()
    d.CUTS = True
    body = d.collection("Body")
    moving = d.collection("Moving")
    memory = d.collection("Memory")
    proxies = d.collection("Proxies")
    cutters = d.collection("Cutters")
    m = materials()
    steel, bare, dark, rubber, poly = m["steel"], m["bare"], m["dark"], m["rubber"], m["poly"]

    # --- Upper receiver ----------------------------------------------------------------------
    up = d.profile("UpperReceiver", body, steel, side_pts(P["upper"]), 0.076, bevel=0.0018, round=0.004,
                   note="Upper receiver: one pressing, the handguard at its front.")
    # The receiver narrows to the handguard's width over its last 60 mm, so the two meet flush.
    bm = bmesh.new()
    ya, yb = Y(fx(500.0)), Y(fx(560.0)) + 0.002
    for side in (-1, 1):
        plan = [(side * 0.0381, ya), (side * 0.070, ya), (side * 0.070, yb), (side * 0.0321, yb)]
        lo_, hi_ = BORE - 0.08, BORE + 0.08
        vb = [bm.verts.new((x, y, lo_)) for x, y in plan]
        vt = [bm.verts.new((x, y, hi_)) for x, y in plan]
        if side < 0:
            vb, vt = vb[::-1], vt[::-1]
        bm.faces.new(vb[::-1])
        bm.faces.new(vt)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    d.cut(up, d.make("BlendCutter", bm, cutters, None, "Taper into the handguard.", 0.0), "Blend")
    hg = d.profile("Handguard", body, steel, side_pts(P["handguard"]), 0.064, bevel=0.0015, round=0.003,
                   note="Handguard: narrower than the receiver, squared off at the front.")
    x_hg0, x_hg1 = fx(565.0), fx(880.0)
    c = d.box("HandguardBoreCutter", cutters, None, (0.0, (Y(x_hg0) + Y(x_hg1)) / 2, Zm(5.0)),
              (0.052, Y(x_hg1) - Y(x_hg0), 0.066), bevel=0, note="Hollow handguard.")
    d.cut(hg, c, "HandguardBore")
    bm = bmesh.new()
    for zr in bp.HOLE_ROWS:
        for xh in bp.HOLES_X:
            pts = [(xh - 11, zr), (xh - 5, zr + 6.5), (xh + 11, zr + 6.5), (xh + 5, zr - 6.5), (xh - 5, zr - 6.5)]
            d.bm_profile(bm, [(Y(x), Zm(z)) for x, z in d.fillet(pts, 2.0)], 0.12)
    c = d.make("HoleCutter", bm, cutters, None, "Lightening holes.", 0.0)
    d.cut(hg, c, "Holes")
    wx0, wx1, wz0, wz1 = P["window"]
    c = d.box("WindowCutter", cutters, None, (0.030, (Y(wx0) + Y(wx1)) / 2, (Zm(wz0) + Zm(wz1)) / 2),
              (0.030, Y(wx1) - Y(wx0), Zm(wz1) - Zm(wz0)), bevel=0, note="Ejection window, right.")
    d.cut(up, c, "Window")
    lathe("BoltCarrier", moving, bare, [(wx0 - 20, 0), (wx0 - 20, 17), (wx1 + 20, 17), (wx1 + 20, 0)], sides=24, bevel=0.0006,
          note="Bolt carrier, seen through the window.")
    # Rail: M1913 section along the top, cross slots every 10 mm.
    rx0, rx1, rz0, rz1 = P["rail"]
    zb, zt = Zm(rz0), Zm(rz1)
    sec = [(-0.0106, zb), (0.0106, zb), (0.0106, zb + 0.004), (0.0078, zb + 0.0062), (0.0106, zt - 0.0030),
           (0.0106, zt), (-0.0106, zt), (-0.0106, zt - 0.0030), (-0.0078, zb + 0.0062), (-0.0106, zb + 0.004)]
    bm = bmesh.new()
    d.bm_xsec(bm, sec, Y(rx0), Y(rx1))
    rail = d.make("Rail", bm, body, steel, "M1913 rail on its 27 MOA base.", 0.0006)
    bm = bmesh.new()
    x = rx0 + 8
    while x < rx1 - 6:
        d.bm_box(bm, (0.0, Y(x), zt - 0.0015), (0.030, 0.0053, 0.0034))
        x += 10.0
    d.cut(rail, d.make("RailSlotCutter", bm, cutters, None, "Rail slots.", 0.0), "Slots")
    # Cheek plates: raised ribbed panels on both sides.
    for side in (-1, 1):
        cp = d.profile("CheekPlate" + ("R" if side > 0 else "L"), body, poly, side_pts(P["cheek"]), 0.004,
                       x=side * 0.0395, bevel=0.0008, round=0.003, note="Ribbed cheek plate.")
        bm = bmesh.new()
        x0c, x1c, z0c, z1c = bbox(P["cheek"])
        for k in range(9):
            xx = x0c + 18 + k * (x1c - x0c - 30) / 8
            d.bm_box(bm, (side * 0.0418, Y(xx), (Zm(z0c) + Zm(z1c)) / 2), (0.0022, 0.0024, Zm(z1c) - Zm(z0c) - 0.008))
        d.cut(cp, d.make("CheekRibCutter", bm, cutters, None, "", 0.0), "Ribs")
    d.profile("RearSight", body, steel, side_pts(P["rear_sight"]), 0.020, bevel=0.0010, note="Rear sight base.")
    d.box("RearSightAperture", body, steel, (0.0, Y(78), Zm(52)), (0.012, 0.006, 0.016), bevel=0.0008)
    d.box("FrontSight", body, steel, (0.0, Y(fx(880.0)), Zm(70)), (0.010, 0.008, 0.020), bevel=0.0008,
          note="Folding front sight, raised.")

    # --- Barrel and brake -----------------------------------------------------------------------
    cx0, cx1, _, _ = P["barrel_collar"]
    lathe("BarrelCollar", body, steel, [(cx0, 0), (cx0, 20), (cx0 + 4, 23.5), (cx1 - 6, 23.5), (cx1 - 6, 19),
                                        (cx1 - 3, 19), (cx1 - 3, 22), (cx1, 22), (cx1, 0)], sides=32, bevel=0.0005,
          note="Barrel bushing at the front of the upper receiver.")
    bx0, bx1 = fx(560.0), P["barrel"][1][0]
    barrel = lathe("Barrel", body, steel, [(bx0, 0), (bx0, 13), (cx1, 13), (cx1 + 8, 11), (bx1, 10), (bx1, 0)], sides=36,
                   bevel=0.0004, note="Fluted barrel.")
    bm = bmesh.new()
    for k in range(6):                                   # six flutes
        a = 2 * math.pi * k / 6
        y0, y1 = Y(cx1 + 30), Y(bx1 - 40)
        d.bm_box(bm, (0.0112 * math.sin(a), (y0 + y1) / 2, BORE + 0.0112 * math.cos(a)), (0.0042, y1 - y0, 0.0042),
                 rot=(0, -math.degrees(a), 0))
    d.cut(barrel, d.make("FluteCutter", bm, cutters, None, "", 0.0), "Flutes")
    kx0, kx1, _, _ = P["brake"]
    brake = lathe("Brake", body, steel, [(kx0, 9), (kx0, 24), (kx0 + 4, 28), (kx1 - 6, 28), (kx1, 25), (kx1, 9)],
                  sides=40, closed=True, cap=False, bevel=0.0006, note="Muzzle brake, bore through it.")
    bm = bmesh.new()
    for k in range(2):
        xp = kx0 + 16 + 40 * k
        d.bm_box(bm, (0.0, Y(xp + 13), BORE), (0.080, 0.026, 0.036))
    d.cut(brake, d.make("BrakePortCutter", bm, cutters, None, "Port chambers.", 0.0), "Ports")
    lathe("BrakeBaffle", body, dark, [(kx0 + 8, 0), (kx0 + 8, 23), (kx0 + 12, 23), (kx0 + 12, 0)], sides=24)

    # --- Lower receiver, stock, grips ----------------------------------------------------------
    d.profile("Butt", body, steel, side_pts(P["butt"]), 0.052, bevel=0.0020, round=0.006, note="Butt.")
    bx_0, bx_1, bz_0, bz_1 = bbox(P["butt"])
    d.box("RecoilPad", body, rubber, (0.0, Y(bx_0 - 4), (Zm(bz_0) + Zm(bz_1)) / 2), (0.054, 0.012, Zm(bz_1) - Zm(bz_0) - 0.010),
          bevel=0.0035, note="Recoil pad.")
    d.profile("StockPost", body, steel, side_pts(P["stock_post"]), 0.048, bevel=0.0018, round=0.004)
    rg = d.profile("RearGrip", body, poly, side_pts(P["rear_grip"]), 0.036, bevel=0.0018, round=0.008, note="Rear grip loop.")
    bm = bmesh.new()
    d.bm_profile(bm, [(Y(x), Zm(z)) for x, z in d.fillet(P["rear_grip_hole"], 6.0)], 0.2)
    d.cut(rg, d.make("RearGripHoleCutter", bm, cutters, None, "", 0.0), "Hole")
    d.profile("LowerReceiver", body, steel, side_pts(P["lower"]), 0.050, bevel=0.0018, round=0.004)
    d.profile("MagWellPlate", body, steel, side_pts(P["shroud"]), 0.072, bevel=0.0020, round=0.004,
              note="Angled magazine-well plate.")
    grip = d.profile("PistolGrip", body, poly, side_pts(P["grip"]), 0.032, bevel=0.0030, round=0.008, note="Pistol grip.")
    gx0, gx1, gz0, gz1 = bbox(P["grip"])
    bm = bmesh.new()
    for k in range(3):                                   # finger grooves on the front strap
        zz = gz1 - 35 - 28 * k
        xf = gx1 - 8 - (gz1 - zz) * 0.20
        d.bm_lathe(bm, [(-0.03, 0.0), (-0.03, 0.0075), (0.03, 0.0075), (0.03, 0.0)], sides=16, axis="X", c=(Y(xf + 6), Zm(zz)))
    d.cut(grip, d.make("GripGrooveCutter", bm, cutters, None, "", 0.0), "Grooves")
    d.profile("Weapon_Trigger", moving, bare, side_pts(P["trigger"]), 0.006, bevel=0.0010, round=0.002,
              note="Trigger. Bone 'trigger'.")
    d.box("Safety", body, steel, (-0.026, Y(fx(300.0)), Zm(-55)), (0.004, 0.020, 0.008), bevel=0.0008, note="Safety, left.")
    d.box("ChargingHandle", body, steel, (0.044, Y(fx(520.0)), Zm(-10)), (0.014, 0.014, 0.018), bevel=0.0020,
          note="Charging handle, right.")

    # --- Monopod, bipod, lock pins ------------------------------------------------------------------
    # (Monopod under the stock removed, owner 2026-11-23.)
    d.profile("BipodYoke", body, steel, side_pts(P["bipod_yoke"]), 0.044, bevel=0.0018, round=0.004)
    # (Folded bipod legs under the barrel removed, owner 2026-11-23.)
    bm = bmesh.new()
    for x, z, r in (bp.MID_PIN, bp.REAR_PIN):
        ring(bm, (0.040, Y(x), Zm(z)), r / 1000.0, 0.0016)
        d.bm_lathe(bm, [(-0.040, 0.0), (-0.040, 0.0035), (0.042, 0.0035), (0.042, 0.0)], sides=12, axis="X", c=(Y(x), Zm(z + r)))
        d.bm_lathe(bm, [(0.037, 0.0), (0.037, 0.0050), (0.042, 0.0050), (0.042, 0.0)], sides=12, axis="X", c=(Y(x), Zm(z + r)))
    d.make("LockPins", bm, body, bare, "Mid and rear lock pins with their pull rings.", 0.0)
    smooth((body, moving))

    # --- Memory points (SVD names) and proxies ---------------------------------------------------
    sx0 = fx(SCOPE_X0)
    d.empty("Mem_Muzzle", memory, (0.0, Y(fx(1443.0)), BORE), "'usti hlavne' - muzzle (front of the brake).")
    d.empty("Mem_BarrelEnd", memory, (0.0, Y(fx(905.0)), BORE), "'konec hlavne' - with the muzzle, the firing line.")
    d.empty("Mem_Eye", memory, (0.0, Y(40.0), Zm(60.0)), "'eye' - iron sights, behind the rear sight.")
    d.empty("Mem_CaseStart", memory, (0.020, Y(fx(400.0)), BORE), "'nabojnicestart' - cases leave the window...")
    d.empty("Mem_CaseEnd", memory, (0.120, Y(fx(380.0)), BORE + 0.030), "'nabojniceend' - ...to the right.")
    d.empty("Mem_TriggerAxis", memory, (0.0, SVD_TRIGGER[0], SVD_TRIGGER[1]), "'trigger_axis' - trigger pivot.")
    d.empty("Mem_BoltAxis", memory, (0.0, Y(fx(400.0)), BORE), "'bolt_axis'.")
    d.empty("Mem_MagAxis", memory, (0.0, 0.0965, 0.1052), "'magazine_axis' - the SVD's, for its reload.")
    d.empty("Mem_MagAxis2", memory, (0.0, 0.0902, 0.0319), "'magazine_axis2'.")
    d.empty("Proxy_Magazine", proxies, MAG_PROXY, "magazine proxy: the AF M107A1 magazine's origin.", kind="ARROWS",
            size=0.03)
    d.empty("Proxy_Scope", proxies, SCOPE_CENTRE(), "scope proxy (slot weaponOpticsAFM107): the scope's origin.",
            kind="ARROWS", size=0.03)


def build_magazine():
    """The magazine (prefix M107M_), built round the SVD's magazine proxy point."""
    d.PREFIX = MAG_PREFIX
    d.clean()
    d.CUTS = True
    body = d.collection("Body")
    d.collection("Moving")
    cutters = d.collection("Cutters")
    steel = materials()["steel"]
    # --- Magazine ---------------------------------------------------------------------------------
    mx0, mx1, mz0, mz1 = P["mag"]
    mag = d.box("Magazine", body, steel, (0.0, (Y(mx0) + Y(mx1)) / 2, (Zm(mz0) + Zm(mz1)) / 2),
                (0.060, Y(mx1) - Y(mx0), Zm(mz1) - Zm(mz0)), bevel=0.0025, note="10-round magazine, sized to the well.")
    bm = bmesh.new()
    for k in range(5):                                   # witness holes, right side
        d.bm_lathe(bm, [(0.025, 0.0), (0.025, 0.0032), (0.040, 0.0032), (0.040, 0.0)], sides=12, axis="X",
                   c=(Y(mx0 + 18 + 27 * k), Zm(mz0 + 20)))
    d.cut(mag, d.make("WitnessCutter", bm, cutters, None, "", 0.0), "Witness")
    bm = bmesh.new()
    for side in (-1, 1):
        for xr in bp.MAG_RIBS:
            d.bm_box(bm, (side * 0.0305, Y(xr), (Zm(mz0 + 30) + Zm(mz1 - 4)) / 2), (0.0020, 0.0040, Zm(mz1 - 4) - Zm(mz0 + 30)))
    d.make("MagRibs", bm, body, steel, "Raised ribs.", 0.0006)
    d.box("MagFloorPlate", body, steel, (0.0, (Y(mx0) + Y(mx1)) / 2, Zm(mz0) - 0.002), (0.064, Y(mx1) - Y(mx0) + 0.004, 0.005),
          bevel=0.0012)

    smooth((body,))
    offset(body, MAG_PROXY)


def SCOPE_CENTRE():
    return (0.0, Y(fx(SCOPE_X0 + 190.0)), Zm(SCOPE_AXIS))


def build_scope_model():
    """The built-in scope (prefix M107S_), built round the middle of its tube."""
    d.PREFIX = SCOPE_PREFIX
    d.clean()
    d.CUTS = True
    body = d.collection("Body")
    d.collection("Moving")
    memory = d.collection("Memory")
    m = materials()
    build_scope(body, m["steel"], m["dark"], m["rubber"])
    smooth((body,))
    offset(body, SCOPE_CENTRE())
    # The view through the scope is drawn by script (reticle, zoom and range readout over a round
    # mask), so the camera sits just ahead of the objective, where no part of the scope is in view.
    d.empty("Mem_EyeScope", memory, (0.0, 0.205, 0.0), "'eyescope' - aiming camera, ahead of the objective.")
    d.empty("Mem_CameraDir", memory, (0.0, 0.705, 0.0), "'cameradir' - straight along the scope.")


# --- Built-in scope (owner: "a built in hunting scope, 6x - 12x, red crosshair, meter counter") ----
SCOPE_X0 = 250.0              # rear of the eyepiece, mm along the blueprint (before the stretch)
SCOPE_LEN = 380.0
SCOPE_AXIS = 92.0             # scope axis, mm above the bore (rail top 61 + rings)


def build_scope(body, steel, dark, rubber):
    """A modern variable scope: 44 mm eyepiece, 30 mm tube, 56 mm objective; elevation (top), windage
    (right) and parallax (left) turrets with an illumination knob; two rings clamped to the rail."""
    x0 = fx(SCOPE_X0)
    zc = Zm(SCOPE_AXIS)

    def sl(name, prof, mat=steel, sides=40, closed=False, cap=True, bevel=0.0005):
        bm = bmesh.new()
        d.bm_lathe(bm, [(Y(x0 + a), r / 1000.0) for a, r in prof], sides=sides, c=(0.0, zc), closed=closed, cap=cap)
        return d.make(name, bm, body, mat, name, bevel)

    sl("ScopeEyepiece", [(0, 18), (0, 22), (6, 22.5), (60, 22.5), (66, 21), (78, 19), (92, 15.2), (98, 15.2), (98, 0)])
    sl("ScopeEyepieceRing", [(18, 22.5), (18, 23.6), (44, 23.6), (44, 22.5)], mat=rubber, closed=True, cap=False)
    sl("ScopeTube", [(96, 15.0), (260, 15.0), (262, 0)], sides=36)
    sl("ScopeObjective", [(258, 15.2), (270, 15.2), (300, 27.0), (310, 28.5), (372, 28.5), (380, 27.5), (380, 0)], sides=44)
    sl("ScopeObjectiveRing", [(352, 28.5), (352, 29.3), (366, 29.3), (366, 28.5)], closed=True, cap=False)
    sl("ScopeLensRear", [(0.5, 0), (0.5, 17.5)], mat=dark, cap=False, sides=32)
    sl("ScopeLensFront", [(379.5, 0), (379.5, 26.0)], mat=dark, cap=False, sides=40)
    # Turret saddle and the three turrets.
    ym = Y(x0 + 178)
    d.box("ScopeSaddle", body, steel, (0.0, ym, zc), (0.036, 0.050, 0.036), bevel=0.004)
    bm = bmesh.new()
    d.bm_lathe(bm, [(zc + 0.017, 0.0), (zc + 0.017, 0.0115), (zc + 0.030, 0.0115), (zc + 0.032, 0.0105), (zc + 0.032, 0.0)],
               sides=32, axis="Z", c=(0.0, ym))
    d.make("ScopeElevation", bm, body, steel, "Elevation turret.", 0.0005)
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.017, 0.0), (0.017, 0.0115), (0.030, 0.0115), (0.032, 0.0105), (0.032, 0.0)], sides=32, axis="X",
               c=(ym, zc))
    d.make("ScopeWindage", bm, body, steel, "Windage turret, right.", 0.0005)
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.017, 0.0), (-0.017, 0.0125), (-0.030, 0.0125), (-0.030, 0.0)], sides=32, axis="X", c=(ym, zc))
    d.bm_lathe(bm, [(-0.030, 0.0), (-0.030, 0.0080), (-0.038, 0.0080), (-0.039, 0.0070), (-0.039, 0.0)], sides=24,
               axis="X", c=(ym, zc))
    d.make("ScopeParallax", bm, body, steel, "Parallax turret, left, with the illumination knob on it.", 0.0005)
    bm = bmesh.new()
    for k in range(24):                                  # knurling on the elevation cap
        a = 2 * math.pi * k / 24
        d.bm_box(bm, (0.0118 * math.sin(a), ym + 0.0118 * math.cos(a), zc + 0.025), (0.0016, 0.0016, 0.010),
                 rot=(0, 0, -math.degrees(a)))
    d.make("ScopeKnurl", bm, body, steel, "", 0.0)
    # Rings: clamp round the tube, foot on the rail.
    for xr in (118.0, 232.0):
        y = Y(x0 + xr)
        bm = bmesh.new()
        d.bm_lathe(bm, [(y - 0.009, 0.0152), (y - 0.009, 0.0205), (y + 0.009, 0.0205), (y + 0.009, 0.0152)], sides=32,
                   c=(0.0, zc), closed=True, cap=False)
        d.bm_box(bm, (0.0, y, (Zm(61) + zc - 0.012) / 2), (0.028, 0.018, zc - 0.012 - Zm(61)))
        d.bm_box(bm, (0.0, y, Zm(61) + 0.003), (0.036, 0.018, 0.008))
        d.bm_lathe(bm, [(0.018, 0.0), (0.018, 0.0045), (0.026, 0.0045), (0.026, 0.0)], sides=12, axis="X",
                   c=(y, Zm(61) + 0.004))
        d.make("ScopeRing", bm, body, steel, "Scope ring on the rail, with its clamp nut.", 0.0006)


def render(out):
    sc = bpy.context.scene
    # Ray traced (Cycles), owner 2026-11-23: real reflections, shadows and occlusion in the previews.
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    world = bpy.data.worlds.new("M107_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.92, 0.93, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = world
    for rot, energy in (((50, 10, 35), 3.5), ((60, -20, -140), 1.5)):
        sun = bpy.data.objects.new("M107_Sun", bpy.data.lights.new("M107_Sun", "SUN"))
        sun.data.energy = energy
        sun.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("M107_Cam", bpy.data.cameras.new("M107_Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(("M107_", "M107M_", "M107S_"))
           and not o.hide_render and not any(c.name.endswith("Cutters") for c in o.users_collection)]
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in obs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    action = Vector((0.0, Y(fx(420.0)), Zm(-40)))
    os.makedirs(out, exist_ok=True)
    views = (("side", centre, Vector((1, 0, 0)), True, 3.0, (hi.y - lo.y) * 1.08),
             ("front34", centre, Vector((1.0, 0.55, 0.18)), False, 2.3, 50),
             ("rear34", centre, Vector((-1.0, -0.6, 0.30)), False, 2.3, 50),
             ("action", action, Vector((1.0, 0.35, 0.25)), False, 0.75, 50),
             ("scope", Vector((0.0, Y(fx(SCOPE_X0 + 190)), Zm(SCOPE_AXIS - 10))), Vector((1.0, 0.25, 0.45)), False, 0.75, 50))
    for name, target, direction, ortho, dist, lens in views:
        direction = direction.normalized()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = lens
        else:
            cam.data.lens = lens
        cam.location = target + direction * dist
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, "m107_model_%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sc.render.filepath)


def build_all():
    for ob in list(bpy.data.objects):            # the factory scene's cube, camera and light
        bpy.data.objects.remove(ob, do_unlink=True)
    build()
    build_magazine()
    build_scope_model()


def assemble(on=True):
    """Previews: the magazine and scope moved onto their proxies (on=False puts them back)."""
    k = 1 if on else -1
    for prefix, at in ((MAG_PREFIX, MAG_PROXY), (SCOPE_PREFIX, SCOPE_CENTRE())):
        col = bpy.data.collections.get(prefix + "Body")
        for ob in col.objects:
            ob.location = tuple(ob.location[i] + k * at[i] for i in range(3))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "afm107_detailed.blend"))
    assemble(True)
    render(args[0] if args else os.path.join(os.path.dirname(HERE), "docs", "img"))
