"""
AF MP40 - 9 mm submachine gun (Blender 4.2+ / tested on 5.3).

Third weapon of the AF Weapons Pack: the tube-receiver, under-folding-stock submachine gun
of the early 1940s, with its own 32-round stick magazine (a second small model, built by
build_magazine() below).

It reuses the helpers of af7_vanguard_detailed.py and afm41_pathfinder_detailed.py, so
those files must sit next to this one.

FRAME
  The gun borrows the vanilla UMP-45's animations, so it is modelled in the UMP's own frame,
  read out of dz\\weapons\\firearms\\UMP45\\ump.p3d:
      working +Y (forward) = UMP -X      working +Z (up) = UMP +Y
      working +X (right)   = UMP +Z      origin          = UMP origin
  Numbers taken from the vanilla model (converted to the working frame):
      bore line            z = 0.0724
      trigger pivot        y = -0.0501, z = 0.0292   (blade y -0.058..-0.043, z -0.008..0.026)
      pistol grip          top y -0.115..-0.070 at z 0.02, bottom y -0.150..-0.100 at z -0.073
      magazine proxy       y = 0.0708, z = -0.0385, leaning 13 degrees (bottom forward);
                           at the height the hand takes it, its centre is at y = 0.085
      left hand            under the handguard, y 0.11..0.23, underside at z = 0.045
      charging handle      left side, travels about 7 cm back
      butt                 y = -0.42
      eye                  y = -0.2741 (z 0.1364 on the UMP; here on the MP40's own sight line)
  What differs from a real MP40 because of that frame: the lower frame between the trigger
  guard and the magazine housing is about 4 cm shorter, so that the right hand, the trigger
  and the magazine all sit where the UMP's animations expect them. The resting bar under
  the barrel starts right in front of the barrel nut, where the left hand closes.

Run: afmp40_run.py (headless), or Scripting tab > Run Script, then afmp40_dayz_export.py.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    raise RuntimeError("Save the .blend next to this script first.")


if _here() not in sys.path:
    sys.path.insert(0, _here())
import af7_vanguard_detailed as d  # noqa: E402  (shared helpers)
import afm41_pathfinder_detailed as m41  # noqa: E402  (loft, stamps, wear helpers)

m41._GLYPHS.setdefault("P", [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]])   # stamp letter the M41 did not need

PREFIX = "MP40_"
MAG_PREFIX = "MP40M_"
BORE = 0.0724            # bore line height (vanilla UMP)
R_TUBE = 0.0185          # receiver tube radius
SIGHT_Z = BORE + 0.027   # sight line
MUZZLE_Y = 0.403
MAG_Y = 0.085            # magazine centre line
MAG_Z = -0.0505          # magazine centre (the magazine model's own origin)
MAG_HALF = (0.0118, 0.0178, 0.1025)   # magazine half size: across, front-back, height

# AF plate on both sides of the lower frame: (y0, z0, width, height, |x| min, |x| max)
LOGO_FRAME = (-0.006, 0.0300, 0.040, 0.020, 0.0150, 0.0190)


def _weather_steel(mat, muzzle_y):
    """Worn phosphate / blue: brown patches, thin finish at the muzzle and under the frame, rust specks."""
    P = m41._Post(mat)
    N = P.N
    plum = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(24.0, 5.0), 0.53), 4.0, clamp=True)
    P.color(N.math("MULTIPLY", plum, 0.35), (0.055, 0.032, 0.024))
    P.rough(N.math("MULTIPLY", plum, 0.08))
    zone = N.math("GREATER_THAN", P.py, muzzle_y - 0.05)
    thin = N.math("MULTIPLY", zone, N.math("MULTIPLY", N.math("SUBTRACT", P.noise(75.0, 6.0), 0.47), 5.0, clamp=True))
    P.color(N.math("MULTIPLY", thin, 0.5), (0.30, 0.30, 0.32))
    P.rough(N.math("MULTIPLY", thin, -0.06))
    speck = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.13, P.cells(420.0)), 22.0, clamp=True),
                   N.math("MULTIPLY", N.math("SUBTRACT", P.noise(14.0, 2.0), 0.57), 8.0, clamp=True))
    P.color(N.math("MULTIPLY", speck, 0.8), (0.090, 0.038, 0.016))
    P.rough(N.math("MULTIPLY", speck, 0.25))
    P.dent(N.math("MULTIPLY", speck, -1.0), 0.00012)
    return P


def _mottle(mat):
    """Bakelite: darker and redder clouds in the pressed resin, and polish where it is held."""
    P = m41._Post(mat)
    N = P.N
    cloud = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(110.0, 5.0), 0.46), 3.5, clamp=True)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", cloud, 0.55), P.plain), (0.010, 0.005, 0.003))
    fleck = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(520.0, 3.0), 0.60), 6.0, clamp=True)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", fleck, 0.35), P.plain), (0.085, 0.032, 0.014))
    held = P.band(P.pz, -0.02, 0.07)
    P.rough(N.math("MULTIPLY", held, -0.06))
    return P


# 9x19 display round: (distance from the case head, radius)
ROUND_CASE = [(0.0, 0.0), (0.0, 0.00495), (0.0190, 0.00483), (0.0190, 0.0044)]
ROUND_SLUG = [(0.0190, 0.0045), (0.0250, 0.0042), (0.0283, 0.0027), (0.0296, 0.0)]


# ----------------------------------------------------------------------------
# Build: the gun
# ----------------------------------------------------------------------------

def build():
    d.PREFIX = PREFIX
    old_prefix, m41.PREFIX = m41.PREFIX, PREFIX
    try:
        _build_gun()
    finally:
        m41.PREFIX = old_prefix


def _build_gun():
    d.clean()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    body = d.collection("Body")
    moving = d.collection("Moving")
    memory = d.collection("Memory")
    proxies = d.collection("Proxies")
    cutters = d.collection("Cutters")

    logo = d.logo_image()
    m_steel = d.material("Steel", (0.026, 0.028, 0.033), rough=0.40, metal=1.0, bump=0.035, bump_scale=1100,
                         rough_var=0.10, wear=0.75, wear_rgb=(0.36, 0.36, 0.38), scratches=0.5, machining=0.05)
    m_bolt = d.material("BoltSteel", (0.40, 0.40, 0.41), rough=0.27, metal=1.0, rough_var=0.06,
                        wear_rgb=(0.60, 0.60, 0.61), scratches=0.35, machining=0.28)
    m_bake = d.material("Bakelite", (0.036, 0.014, 0.007), rough=0.36, metal=0.0, bump=0.035, bump_scale=1400,
                        rough_var=0.08, wear=0.30, wear_rgb=(0.11, 0.048, 0.022), scratches=0.30, stipple=0.02,
                        logo=LOGO_FRAME, logo_img=logo, skin_img=d.pattern_image())
    steel = _weather_steel(m_steel, MUZZLE_Y)
    _mottle(m_bake)
    lettering = (0.12, 0.12, 0.125)
    img, asp = m41.stamp_image("MP40Model", ["AF MP40", "1942"])
    steel.stamp(img, asp, -0.142, 0.0105, -1, R_TUBE * math.radians(38.0), wrap=(R_TUBE, BORE), rgb=lettering)
    img, asp = m41.stamp_image("MP40Serial", ["No 4127"])
    steel.stamp(img, asp, -0.136, 0.0050, 1, R_TUBE * math.radians(48.0), wrap=(R_TUBE, BORE), rgb=lettering)

    # --- Receiver tube ---------------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.170, 0.0150), (-0.170, R_TUBE), (0.118, R_TUBE), (0.118, 0.0150)], sides=32, c=(0.0, BORE),
               closed=True, cap=False)
    tube = d.make("Receiver", bm, body, m_steel, "Receiver tube. Open: cocking slot (left), ejection port (top right), magazine well.")
    well = d.box("MagWellCutter", cutters, None, (0.0, MAG_Y, 0.030), (0.0252, 0.0372, 0.075), bevel=0,
                 note="Boolean cutter: magazine well through the housing and the bottom of the tube.")
    for nm, centre, size in (("Slot", (-R_TUBE, 0.020, BORE + 0.004), (0.014, 0.165, 0.0085)),
                             ("SafetyNotch", (-R_TUBE, -0.0560, BORE + 0.0105), (0.014, 0.0125, 0.0150)),
                             ("Port", (0.0125, 0.070, BORE + 0.0125), (0.025, 0.050, 0.025))):
        c = d.box("Receiver_%sCutter" % nm, cutters, None, centre, size, bevel=0, note="Boolean cutter.")
        d.cut(tube, c, nm)
    d.cut(tube, well, "MagWell")

    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.1870, 0.0), (-0.1870, 0.0150), (-0.1850, 0.0182), (-0.1820, 0.0196), (-0.1700, 0.0196),
                    (-0.1685, 0.0186), (-0.1685, 0.0)], sides=32, c=(0.0, BORE))
    for k in range(5):   # gripping rings on the cap
        d.bm_lathe(bm, [(-0.1810 + 0.0022 * k, 0.0199), (-0.1800 + 0.0022 * k, 0.0199)], sides=32, c=(0.0, BORE), cap=False)
    d.make("EndCap", bm, body, m_steel, "Receiver end cap.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.169, 0.0), (-0.169, 0.0088), (-0.060, 0.0088), (-0.060, 0.0070), (0.004, 0.0070), (0.004, 0.0)],
               sides=16, c=(0.0, BORE))
    d.make("SpringTube", bm, body, m_bolt, "Telescoping recoil spring tube, seen through the cocking slot.")

    # --- Bolt and cocking handle ----------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.004, 0.0), (0.004, 0.0146), (0.104, 0.0146), (0.106, 0.0125), (0.106, 0.0)], sides=24, c=(0.0, BORE))
    for y in (0.030, 0.034):
        d.bm_lathe(bm, [(y, 0.0148), (y + 0.0016, 0.0148)], sides=24, c=(0.0, BORE), cap=False)
    d.make("Bolt", bm, moving, m_bolt, "Bolt, seen through the ejection port. Bone 'bolt'.")
    bm = bmesh.new()
    d.bm_box(bm, (-0.0225, 0.090, BORE + 0.004), (0.019, 0.0085, 0.0068))
    d.bm_lathe(bm, [(-0.0300, 0.0042), (-0.0325, 0.0068), (-0.0400, 0.0068), (-0.0425, 0.0045), (-0.0425, 0.0)],
               sides=16, axis="X", c=(0.090, BORE + 0.004))
    d.make("CockingHandle", bm, moving, m_steel, "Cocking handle in the slot on the left. Bone 'charging'.", bevel=0.0006)

    # --- Barrel group ----------------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.110, 0.0), (0.110, 0.0188), (0.118, 0.0196), (0.134, 0.0196), (0.138, 0.0166), (0.150, 0.0152),
                    (0.154, 0.0108), (0.154, 0.0)], sides=32, c=(0.0, BORE))
    for k in range(6):
        d.bm_lathe(bm, [(0.1195 + 0.0024 * k, 0.0199), (0.1206 + 0.0024 * k, 0.0199)], sides=32, c=(0.0, BORE), cap=False)
    d.make("BarrelNut", bm, body, m_steel, "Barrel nut at the front of the receiver.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.150, 0.0), (0.150, 0.0098), (0.300, 0.0092), (0.386, 0.0088), (0.386, 0.0)], sides=24, c=(0.0, BORE))
    d.make("Barrel", bm, body, m_steel, "Barrel.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.386, 0.0046), (0.386, 0.0100), (0.4010, 0.0100), (MUZZLE_Y, 0.0090), (MUZZLE_Y, 0.0046)],
               sides=24, c=(0.0, BORE), closed=True, cap=False)
    for k in range(4):
        d.bm_lathe(bm, [(0.3885 + 0.0030 * k, 0.0103), (0.3900 + 0.0030 * k, 0.0103)], sides=24, c=(0.0, BORE), cap=False)
    d.make("MuzzleNut", bm, body, m_steel, "Muzzle nut. Selection 'hide_barrel': hidden while a suppressor is fitted.")

    # Resting bar under the barrel; the left hand closes on its rear end and on the barrel nut.
    d.profile("RestingBar", body, m_bake,
              [(0.158, BORE - 0.0085), (0.326, BORE - 0.0080), (0.330, BORE - 0.0120), (0.330, BORE - 0.0330),
               (0.322, BORE - 0.0345), (0.314, BORE - 0.0270), (0.166, BORE - 0.0270), (0.158, BORE - 0.0200)],
              width=0.0130, bevel=0.0022, round=0.004, note="Resting bar under the barrel, with its hook at the front.")
    for y in (0.176, 0.300):
        bm = bmesh.new()
        d.bm_lathe(bm, [(y - 0.005, 0.0096), (y - 0.004, 0.0112), (y + 0.004, 0.0112), (y + 0.005, 0.0096)], sides=24,
                   c=(0.0, BORE), cap=False)
        d.bm_lathe(bm, [(-0.0072, 0.0), (-0.0072, 0.0020), (0.0072, 0.0020), (0.0072, 0.0)], sides=10, axis="X",
                   c=(y, BORE - 0.0150))
        d.make("BarBand_%d" % (0 if y < 0.2 else 1), bm, body, m_steel, "Band and pin holding the resting bar.")

    # --- Sights ----------------------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.3610, 0.0089), (0.3625, 0.0116), (0.3815, 0.0116), (0.3830, 0.0089)], sides=24, c=(0.0, BORE), cap=False)
    d.bm_box(bm, (0.0, 0.372, BORE + 0.0140), (0.0085, 0.0170, 0.0080))
    d.make("FrontSightBase", bm, body, m_steel, "Front sight band and block.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.3650, 0.0086), (0.3650, 0.0100), (0.3790, 0.0100), (0.3790, 0.0086)], sides=24,
               c=(0.0, BORE + 0.0265), closed=True, cap=False)
    d.make("FrontSightHood", bm, body, m_steel, "Front sight hood.")
    d.box("FrontSightPost", body, m_steel, (0.0, 0.372, SIGHT_Z - 0.0050), (0.0016, 0.0022, 0.0100), bevel=0.0002,
          note="Front sight blade; its top is on the sight line.")

    d.box("RearSightBase", body, m_steel, (0.0, 0.0300, BORE + 0.0195), (0.0170, 0.0280, 0.0060), bevel=0.0008,
          note="Rear sight base on the receiver.")
    z0, z1, zn = BORE + 0.0215, SIGHT_Z + 0.0042, SIGHT_Z - 0.0014
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0072, z0), (0.0072, z0), (0.0072, z1), (0.0012, z1), (0.0012, zn), (-0.0012, zn),
                   (-0.0012, z1), (-0.0072, z1)], 0.0375, 0.0400)
    d.make("RearSightNotch", bm, body, m_steel, "Fixed 100 m notch. The sight line runs through it.", bevel=0.0003)
    d.box("RearSightLeaf", body, m_steel, (0.0, 0.0265, BORE + 0.0237), (0.0125, 0.0150, 0.0022), bevel=0.0004,
          note="200 m leaf, folded down.")
    for side in (-1, 1):
        d.box("RearSightEar_%s" % ("R" if side > 0 else "L"), body, m_steel, (side * 0.0078, 0.0330, BORE + 0.0250),
              (0.0014, 0.0200, 0.0080), bevel=0.0004, note="Rear sight side wall.")

    # --- Lower frame, grip, trigger -------------------------------------------
    m41.loft("LowerFrame", body, m_bake,
             [(-0.150, 0.0300, 0.0600, 0.0165), (-0.110, 0.0262, 0.0600, 0.0170), (-0.070, 0.0262, 0.0600, 0.0170),
              (-0.015, 0.0240, 0.0600, 0.0172), (0.020, 0.0205, 0.0600, 0.0176), (0.0585, 0.0235, 0.0600, 0.0176)],
             power=3.4, note="Bakelite lower frame under the receiver. Sections are (y, bottom, top, half width).")
    d.box("FrameFlange", body, m_steel, (0.0, -0.0500, 0.0575), (0.0375, 0.2200, 0.0042), bevel=0.0010,
          note="Steel flange where the lower frame meets the receiver tube.")
    d.box("FrameRear", body, m_steel, (0.0, -0.1590, 0.0440), (0.0350, 0.0200, 0.0330), bevel=0.0025,
          note="Rear frame block carrying the stock pivot.")
    d.box("ReceiverLock", body, m_steel, (0.0, -0.1500, 0.0235), (0.0120, 0.0140, 0.0090), bevel=0.0012,
          note="Receiver lock under the rear of the frame.")

    d.profile("GripFrame", body, m_steel,
              [(-0.0720, 0.0300), (-0.1220, 0.0300), (-0.1310, 0.0000), (-0.1445, -0.0350), (-0.1595, -0.0670),
               (-0.1545, -0.0780), (-0.1090, -0.0780), (-0.1005, -0.0670), (-0.0905, -0.0300), (-0.0785, 0.0050)], width=0.0125, bevel=0.0020, round=0.008, note="Steel grip frame (front and back straps).")
    d.profile("GripPanels", body, m_bake,
              [(-0.0760, 0.0280), (-0.1190, 0.0280), (-0.1275, 0.0000), (-0.1410, -0.0350), (-0.1555, -0.0660),
               (-0.1520, -0.0745), (-0.1110, -0.0745), (-0.1045, -0.0660), (-0.0945, -0.0300), (-0.0825, 0.0050)], width=0.0310, bevel=0.0045, segments=3, round=0.008, note="Bakelite grip panels.")
    for side in (-1, 1):
        bm = bmesh.new()
        prof = [(0.0150, 0.0), (0.0150, 0.0042), (0.0160, 0.0042), (0.0164, 0.0034), (0.0164, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        d.bm_lathe(bm, prof, sides=12, axis="X", c=(-0.1180, -0.0250))
        d.bm_box(bm, (side * 0.0164, -0.1180, -0.0250), (0.0006, 0.0060, 0.0009))
        d.make("GripScrew_%s" % ("R" if side > 0 else "L"), bm, body, m_steel, "Grip screw.")

    outer = [(-0.0745, 0.0270), (-0.0735, 0.0040), (-0.0700, -0.0085), (-0.0620, -0.0150), (-0.0480, -0.0165),
             (-0.0300, -0.0160), (-0.0170, -0.0115), (-0.0075, -0.0020), (-0.0020, 0.0110), (-0.0010, 0.0245)]
    inner = [(-0.0042, 0.0245), (-0.0050, 0.0115), (-0.0100, 0.0000), (-0.0185, -0.0088), (-0.0305, -0.0130),
             (-0.0480, -0.0135), (-0.0608, -0.0122), (-0.0675, -0.0070), (-0.0705, 0.0045), (-0.0713, 0.0270)]
    d.profile("TriggerGuard", body, m_steel, outer + inner, width=0.0125, bevel=0.0007, round=0.004, note="Trigger guard.")
    d.profile("Weapon_Trigger", moving, m_steel,
              [(-0.0455, 0.0270), (-0.0540, 0.0270), (-0.0582, 0.0100), (-0.0566, -0.0035), (-0.0528, -0.0062),
               (-0.0522, 0.0085)], width=0.0060, bevel=0.0008, round=0.003,
              note="Trigger. Bone 'trigger'; pivot at (y -0.0501, z 0.0292).")
    for nm, y, z, r in (("TriggerPin", -0.0501, 0.0340, 0.0026), ("FramePin", 0.0400, 0.0420, 0.0030),
                        ("SearPin", -0.0900, 0.0440, 0.0026)):
        bm = bmesh.new()
        d.bm_lathe(bm, [(-0.0180, 0.0), (-0.0180, r), (0.0180, r), (0.0180, 0.0)], sides=10, axis="X", c=(y, z))
        d.make(nm, bm, body, m_steel, "Cross pin through the lower frame.")

    # --- Magazine housing ------------------------------------------------------
    housing = d.box("MagHousing", body, m_steel, (0.0, MAG_Y, 0.0360), (0.0330, 0.0470, 0.0470), bevel=0.0020,
                    note="Magazine housing under the receiver.")
    d.cut(housing, well, "MagWell")
    bm = bmesh.new()
    for side in (-1, 1):
        for k in range(5):
            d.bm_box(bm, (side * 0.0167, MAG_Y - 0.0150 + 0.0075 * k, 0.0345), (0.0012, 0.0030, 0.0360))
    d.make("MagHousingRibs", bm, body, m_steel, "Stiffening ribs pressed into the magazine housing.", bevel=0.0005)
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0165, 0.0058), (-0.0200, 0.0058), (-0.0215, 0.0048), (-0.0215, 0.0)], sides=16, axis="X",
               c=(0.0560, 0.0400))
    for k in range(3):
        d.bm_lathe(bm, [(-0.0178 - 0.0011 * k, 0.0061), (-0.0184 - 0.0011 * k, 0.0061)], sides=16, axis="X",
                   c=(0.0560, 0.0400), cap=False)
    d.make("MagRelease", bm, body, m_steel, "Magazine release button on the left of the housing.")

    # --- Folding stock, drawn out ---------------------------------------------
    piv, hinge = (-0.1590, 0.0400), (-0.3800, 0.0270)
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0218, 0.0), (-0.0218, 0.0120), (-0.0205, 0.0135), (0.0205, 0.0135), (0.0218, 0.0120), (0.0218, 0.0)],
               sides=24, axis="X", c=piv)
    d.bm_lathe(bm, [(-0.0218, 0.0070), (-0.0250, 0.0070), (-0.0262, 0.0060), (-0.0262, 0.0)], sides=16, axis="X", c=piv)
    d.make("StockPivot", bm, body, m_steel, "Stock pivot with its release button on the left.")
    length = math.hypot(hinge[0] - piv[0], hinge[1] - piv[1])
    slope = math.degrees(math.atan2(hinge[1] - piv[1], hinge[0] - piv[0]))    # about 177 degrees
    mid = ((piv[0] + hinge[0]) / 2.0, (piv[1] + hinge[1]) / 2.0)
    for side in (-1, 1):
        d.box("StockStrut_%s" % ("R" if side > 0 else "L"), body, m_steel, (side * 0.0200, mid[0], mid[1]),
              (0.0036, length + 0.016, 0.0115), rot=(slope - 180.0, 0, 0), bevel=0.0012, note="Stock strut.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0225, 0.0), (-0.0225, 0.0052), (0.0225, 0.0052), (0.0225, 0.0)], sides=12, axis="X", c=hinge)
    d.make("ButtHinge", bm, body, m_steel, "Butt plate hinge.")
    m41.loft("ButtPlate", body, m_steel,
             [(-0.3895, -0.0660, 0.0380, 0.0190), (-0.3875, -0.0680, 0.0400, 0.0205), (-0.3835, -0.0680, 0.0400, 0.0205),
              (-0.3820, -0.0660, 0.0380, 0.0190)], power=2.5, note="Butt plate, swung down.")
    bm = bmesh.new()
    for z in (-0.045, -0.025, -0.005, 0.015):
        d.bm_box(bm, (0.0, -0.3900, z), (0.0300, 0.0012, 0.0030))
    d.make("ButtPlateRibs", bm, body, m_steel, "Grip ribs on the butt plate.", bevel=0.0004)

    # --- Memory points ---------------------------------------------------------
    d.empty("Mem_Muzzle", memory, (0, MUZZLE_Y, BORE), "'usti hlavne' - muzzle.")
    d.empty("Mem_BarrelEnd", memory, (0, 0.200, BORE), "'konec hlavne' - with the muzzle sets the firing direction.")
    d.empty("Mem_Eye", memory, (0, -0.2741, SIGHT_Z), "'eye' - iron sight camera (vanilla distance, this gun's sight line).")
    d.empty("Mem_CaseStart", memory, (0.012, 0.070, BORE + 0.014), "'nabojnicestart' - where spent cases appear.")
    d.empty("Mem_CaseEnd", memory, (0.095, 0.052, BORE + 0.060), "'nabojniceend' - direction spent cases fly.")

    # --- Attachment proxies ----------------------------------------------------
    d.empty("Proxy_Magazine", proxies, (0, MAG_Y, MAG_Z), "magazine proxy (slot magazine); the AF MP40 magazine's origin.",
            kind="ARROWS", size=0.03)
    d.empty("Proxy_Suppressor", proxies, (0, MUZZLE_Y + 0.0689, BORE + 0.0028),
            "suppressor_45acp proxy (slot pistolMuzzle); same offset from the muzzle as on the UMP.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Wrap", proxies, (0.0002, 0.0495, BORE + 0.0260), "ghillie_wrap proxy (slot weaponWrap).",
            kind="ARROWS", size=0.03)


# ----------------------------------------------------------------------------
# Build: the magazine (its own model, origin at its centre)
# ----------------------------------------------------------------------------

def build_magazine():
    d.PREFIX = MAG_PREFIX
    old_prefix, m41.PREFIX = m41.PREFIX, MAG_PREFIX
    try:
        d.clean()
        body = d.collection("Body")
        d.collection("Moving")
        hx, hy, hz = MAG_HALF
        m_steel = d.material("Steel", (0.024, 0.026, 0.031), rough=0.42, metal=1.0, bump=0.035, bump_scale=1100,
                             rough_var=0.10, wear=0.85, wear_rgb=(0.38, 0.38, 0.40), scratches=0.6)
        m_brass = d.material("Brass", (0.60, 0.38, 0.12), rough=0.30, metal=1.0, rough_var=0.06, scratches=0.25,
                             wear_rgb=(0.74, 0.55, 0.26))
        m_jacket = d.material("Jacket", (0.50, 0.24, 0.12), rough=0.34, metal=1.0, rough_var=0.05)
        steel = _weather_steel(m_steel, 9.0)
        img, asp = m41.stamp_image("MP40Mag", ["AF MP40"])
        steel.stamp(img, asp, -0.0125, 0.0042, 1, -0.0900, rgb=(0.12, 0.12, 0.125))

        d.box("Body", body, m_steel, (0.0, 0.0, 0.0020), (2 * hx, 2 * hy, 2 * hz - 0.0040), bevel=0.0022, segments=2,
              note="Magazine body.")
        bm = bmesh.new()
        for side in (-1, 1):
            d.bm_box(bm, (side * hx, 0.0020, -0.0080), (0.0014, 0.0085, 0.1500))
        d.bm_box(bm, (0.0, -hy, -0.0080), (0.0090, 0.0012, 0.1700))
        d.make("Ribs", bm, body, m_steel, "Long ribs pressed into the sides and the spine.", bevel=0.0006)
        d.box("FloorPlate", body, m_steel, (0.0, 0.0, -hz + 0.0020), (2 * hx + 0.0030, 2 * hy + 0.0036, 0.0042),
              bevel=0.0010, note="Floor plate.")
        d.box("FloorCatch", body, m_steel, (0.0, 0.0040, -hz - 0.0004), (0.0060, 0.0080, 0.0012), bevel=0.0004,
              note="Floor plate catch.")
        for side in (-1, 1):
            d.box("Lip_%s" % ("R" if side > 0 else "L"), body, m_steel, (side * 0.0078, -0.0020, hz + 0.0018),
                  (0.0075, 0.0300, 0.0016), rot=(0, side * 24.0, 0), bevel=0.0004, note="Feed lip.")
        base = (-0.0165, hz + 0.0002)
        for nm, mat, prof in (("Round", m_brass, ROUND_CASE), ("RoundSlug", m_jacket, ROUND_SLUG)):
            bm = bmesh.new()
            d.bm_lathe(bm, [(base[0] + y, r) for y, r in prof], sides=12, c=(0.0, base[1]), cap=False)
            d.make(nm, bm, body, mat, "Top round between the feed lips.")
    finally:
        m41.PREFIX = old_prefix


if __name__ == "__main__":
    build()
    build_magazine()
    print("AF MP40 and its magazine built.")
