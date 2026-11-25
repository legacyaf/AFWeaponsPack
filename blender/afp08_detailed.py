"""
AF P08 - 9 mm toggle-lock pistol (Blender 4.2+ / tested on 5.3).

Fourth weapon of the AF Weapons Pack and its first pistol: the long-raked, toggle-locked
service pistol of the first half of the 20th century, with its own 8-round magazine (a second
small model, built by build_magazine() below).

It reuses the helpers of af7_vanguard_detailed.py and afm41_pathfinder_detailed.py, so
those files must sit next to this one.

FRAME
  The pistol borrows the vanilla P1's animations, so it is modelled in the P1's own frame,
  read out of dz\\weapons\\pistols\\p1\\p1.p3d:
      working +Y (forward) = P1 -X      working +Z (up) = P1 +Y
      working +X (right)   = P1 +Z      origin          = P1 origin
  Numbers taken from the vanilla model (converted to the working frame):
      barrel axis          z = 0.069 (the P1's 'usti hlavne' is 6 mm above its own barrel)
      muzzle               y = 0.2035        slide rear y = 0.005, hammer back to y = -0.021
      sight line (eye)     z = 0.0838, eye at y = -0.2586
      trigger pivot        y = 0.079, z = 0.043; blade y 0.073..0.092, z 0.014..0.041
      trigger guard        inside y 0.062..0.107, bottom z = 0.011
      grip                 back strap y 0.008 at z 0.045 to y -0.006 at z -0.025 (14 degrees);
                           front strap y 0.064 at z 0.015 to y 0.046 at z -0.045 (16 degrees);
                           bottom z = -0.045, magazine floor to z = -0.052; tang y = -0.008, z = 0.049
      magazine travel      along a line raked 13 degrees ('magazine_axis')
      skeleton             magazine, trigger, recoil; slide, hammer, bolt, slide_catch, bullet (children of recoil).
                           The P1's slide is on the bone 'bolt', its frame on 'recoil'.
  What differs from a real P08 because of that frame:
    - The grip is raked 21 degrees instead of 35, so that the hand posed for the P1 still closes on it.
    - The vanilla animations slide the bone 'bolt' straight back. Only the breechblock rides on it:
      the breech opens, but the toggle stays flat instead of folding up.
    - The magazine is drawn out along the P1's 13 degree line, so it passes through the front of the
      grip for a few frames during a reload.

Run: afp08_run.py (headless), or Scripting tab > Run Script, then afp08_dayz_export.py.
"""

import math
import os
import sys

import bmesh
import bpy


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    raise RuntimeError("Save the .blend next to this script first.")


if _here() not in sys.path:
    sys.path.insert(0, _here())
import af7_vanguard_detailed as d  # noqa: E402  (shared helpers)
import afm41_pathfinder_detailed as m41  # noqa: E402  (loft, stamps, wear helpers)

m41._GLYPHS.setdefault("P", [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]])

PREFIX = "P08_"
MAG_PREFIX = "P08M_"
BORE = 0.0690            # barrel axis (the vanilla P1's)
SIGHT_Z = 0.0838         # sight line (the vanilla P1's eye height)
MUZZLE_Y = 0.2050
RAKE = math.radians(21.0)   # 27 was tried first: the fingers closed 2-3 cm in front of the grip (in-game test, 0.11.0)
T = math.tan(RAKE)
GRIP_TOP, GRIP_BOTTOM = 0.036, -0.050
MAG_AT = (0.0, 0.0332, 0.0)          # magazine proxy = the magazine model's own origin
MAG_HALF_Y = 0.0164                  # magazine half depth measured along the bore
MAG_TOP, MAG_BOTTOM = 0.050, -0.050  # magazine body, in the pistol's z

# AF medallion on both grip panels: (y0, z0, width, height, |x| min, |x| max)
LOGO_GRIP = (0.0060, -0.0190, 0.0220, 0.0110, 0.0120, 0.0175)


def back(z):
    """Back strap line."""
    return 0.006 - T * (0.040 - z)


def front(z):
    """Front strap line."""
    return 0.062 - T * (0.026 - z)


def mag_centre(z):
    """Centre line of the magazine in the grip (pistol coordinates)."""
    return MAG_AT[1] + T * z


def _grip_wood(mat):
    """Walnut grip panels: checkered all over the sides, darkened and polished by the hand."""
    P = m41._Post(mat)
    N = P.N
    pitch = 0.0012
    tri = []
    for sign in (1.0, -1.0):
        along = N.math("ADD", N.math("MULTIPLY", P.py, 0.5 / pitch), N.math("MULTIPLY", P.pz, sign * 0.866 / pitch))
        tri.append(N.math("MULTIPLY", N.math("ABSOLUTE", N.math("SUBTRACT", N.math("FRACT", along), 0.5)), 2.0))
    diamonds = N.math("MINIMUM", tri[0], tri[1])                 # 0 in the grooves, 1 on the points
    side = N.math("GREATER_THAN", N.math("ABSOLUTE", P.nx), 0.62)
    P.dent(N.math("MULTIPLY", side, N.math("SUBTRACT", diamonds, 1.0)), 0.00040)
    grooves = N.math("MULTIPLY", side, N.math("SUBTRACT", 1.0, diamonds))
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", grooves, 0.55), P.plain), (0.020, 0.008, 0.004))
    P.rough(N.math("MULTIPLY", side, 0.06))
    held = N.math("MULTIPLY", N.math("ADD", 0.35, N.math("MULTIPLY", P.noise(40.0, 4.0), 0.9)), 0.8, clamp=True)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", held, 0.40), P.plain), (0.030, 0.011, 0.005))
    P.rough(N.math("MULTIPLY", held, -0.08))
    return P


def _blue(mat):
    """Rust blue with holster wear: thin and bright on the muzzle, the high edges of the frame and the straps."""
    P = m41._Post(mat)
    N = P.N
    plum = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(30.0, 5.0), 0.54), 4.0, clamp=True)
    P.color(N.math("MULTIPLY", plum, 0.30), (0.050, 0.030, 0.024))
    P.rough(N.math("MULTIPLY", plum, 0.07))
    zone = N.math("MAXIMUM", N.math("GREATER_THAN", P.py, MUZZLE_Y - 0.022), N.math("MULTIPLY", N.math("LESS_THAN", P.pz, 0.0150), 0.6))
    thin = N.math("MULTIPLY", zone, N.math("MULTIPLY", N.math("SUBTRACT", P.noise(85.0, 6.0), 0.52), 5.0, clamp=True))
    P.color(N.math("MULTIPLY", thin, 0.35), (0.26, 0.26, 0.28))
    P.rough(N.math("MULTIPLY", thin, -0.06))
    speck = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.12, P.cells(520.0)), 22.0, clamp=True),
                   N.math("MULTIPLY", N.math("SUBTRACT", P.noise(16.0, 2.0), 0.58), 8.0, clamp=True))
    P.color(N.math("MULTIPLY", speck, 0.8), (0.090, 0.038, 0.016))
    P.rough(N.math("MULTIPLY", speck, 0.25))
    P.dent(N.math("MULTIPLY", speck, -1.0), 0.00010)
    return P


# 9x19 display round: (distance from the case head, radius)
ROUND_CASE = [(0.0, 0.0), (0.0, 0.00495), (0.0190, 0.00483), (0.0190, 0.0044)]
ROUND_SLUG = [(0.0190, 0.0045), (0.0250, 0.0042), (0.0283, 0.0027), (0.0296, 0.0)]


def _arc(centre, radius, a0, a1, steps):
    return [(centre[0] + radius * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             centre[1] + radius * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]


# ----------------------------------------------------------------------------
# Build: the pistol
# ----------------------------------------------------------------------------

def build():
    d.CLEAN_TOPO = True          # quad caps and modelled openings (owner 2026-11-24)
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
    # Quality pass (owner 2026-11-24): the StG 44's worn-finish layers replace the older edge wear.
    m_blue = d.material("BluedSteel", (0.020, 0.022, 0.029), rough=0.33, metal=1.0, bump=0.025, bump_scale=1400,
                        rough_var=0.09, machining=0.06)
    import af_finish
    af_finish.worn(m_blue, 0.205, (
        ((0.0, 0.016, 0.076), (0.019, 0.010, 0.010), 1.0),       # toggle knobs
        ((0.0, 0.020, 0.000), (0.012, 0.045, 0.045), 0.5),       # grip frame: the hand
        ((0.0, 0.083, 0.022), (0.005, 0.016, 0.014), 0.8),       # trigger guard
        ((0.0, 0.195, 0.070), (0.010, 0.012, 0.012), 0.8)),      # muzzle and front sight
        palette="blued")
    m_straw = d.material("Straw", (0.50, 0.33, 0.10), rough=0.30, metal=1.0, rough_var=0.06, wear=0.35,
                         wear_rgb=(0.62, 0.55, 0.42), scratches=0.30, machining=0.10)
    m_wood = m41.woodify(d.material("Walnut", (0.19, 0.080, 0.033), rough=0.46, metal=0.0, bump=0.05, bump_scale=1000,
                                    rough_var=0.08, wear=0.35, wear_rgb=(0.34, 0.19, 0.085), scratches=0.25,
                                    logo=LOGO_GRIP, logo_img=logo, skin_img=d.pattern_image()),
                         dark=(0.066, 0.023, 0.010), light=(0.205, 0.076, 0.027))
    steel = _blue(m_blue)
    _grip_wood(m_wood)
    lettering = (0.11, 0.11, 0.115)
    img, asp = m41.stamp_image("P08Model", ["AF P08"])
    steel.stamp(img, asp, 0.0300, 0.0042, -1, 0.0625, rgb=lettering)
    img, asp = m41.stamp_image("P08Serial", ["No 2741"])
    steel.stamp(img, asp, 0.0800, 0.0030, -1, 0.0505, rgb=lettering)
    img, asp = m41.stamp_image("P08Year", ["1917"])
    steel.stamp(img, asp, 0.0660, 0.0030, 1, 0.0630, rgb=lettering)

    # --- Barrel and front sight -------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.1010, 0.0), (0.1010, 0.0096), (0.1085, 0.0096), (0.1105, 0.0082), (0.1880, 0.0066),
                    (MUZZLE_Y - 0.0006, 0.0064), (MUZZLE_Y, 0.0058), (MUZZLE_Y, 0.0046), (MUZZLE_Y - 0.0070, 0.0045),
                    (MUZZLE_Y - 0.0070, 0.0)], sides=24, c=(0.0, BORE))
    d.make("Barrel", bm, body, m_blue, "Tapered barrel with its flange at the receiver.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.1885, 0.0062), (0.1895, 0.0077), (0.2000, 0.0076), (0.2010, 0.0062)], sides=24, c=(0.0, BORE), cap=False)
    d.bm_xsec(bm, [(-0.0036, BORE + 0.0050), (0.0036, BORE + 0.0050), (0.0026, BORE + 0.0108), (-0.0026, BORE + 0.0108)],
              0.1895, 0.2000)
    d.make("FrontSightBand", bm, body, m_blue, "Front sight band and dovetail block.", bevel=0.0004)
    d.profile("FrontSightBlade", body, m_blue,
              [(0.1905, BORE + 0.0100), (0.1990, BORE + 0.0100), (0.1975, SIGHT_Z), (0.1935, SIGHT_Z)], width=0.0016,
              bevel=0.0002, note="Front sight blade; its top is on the sight line.")

    # --- Receiver (barrel extension): chamber ring and the fork the breechblock runs in -------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.0850, 0.0), (0.0850, 0.0126), (0.0995, 0.0126), (0.1020, 0.0104), (0.1020, 0.0)], sides=32, c=(0.0, BORE))
    d.make("ChamberRing", bm, body, m_blue, "Chamber ring at the front of the receiver.")
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0118, 0.0550), (0.0118, 0.0550), (0.0118, 0.0750), (0.0090, 0.0795), (-0.0090, 0.0795),
                   (-0.0118, 0.0750)], -0.0105, 0.0880)
    # The open top of the fork: loop cuts round it, the cells pushed down 10.5 mm (no Boolean).
    import af_topo
    af_topo.openings(bm, "Z", [(-0.0086, 0.0086, -0.0065, 0.0875)], depth=0.0105, sign=1, weight=0.5)
    af_topo.tidy(bm)
    fork = d.make("Receiver", bm, body, m_blue, "Receiver fork. Open on top: the breechblock and toggle lie in it.", bevel=0.0008)

    # --- Breechblock (the only part on the bone 'bolt') ---------------------------
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0078, 0.0600), (0.0078, 0.0600), (0.0078, 0.0764), (0.0060, 0.0790), (-0.0060, 0.0790),
                   (-0.0078, 0.0764)], 0.0520, 0.0868)
    d.make("BreechBlock", bm, moving, m_blue, "Breechblock. Bone 'bolt': slides back under the toggle.", bevel=0.0006)
    d.box("Extractor", moving, m_blue, (0.0, 0.0730, 0.0794), (0.0042, 0.0250, 0.0014), bevel=0.0004,
          note="Extractor on top of the breechblock. Bone 'bolt'.")

    # --- Toggle: fixed, lying flat ---------------------------------------------------
    bm = bmesh.new()
    d.bm_profile(bm, d.fillet([(0.0245, 0.0730), (0.0590, 0.0745), (0.0600, 0.0790), (0.0570, 0.0812), (0.0245, 0.0812)], 0.0012),
                 0.0164)
    d.bm_box(bm, (0.0, 0.0200, 0.0771), (0.0100, 0.0100, 0.0082))
    d.make("ToggleFrontLink", bm, body, m_blue, "Front toggle link, with its tongue in the fork of the rear link.", bevel=0.0007)
    bm = bmesh.new()
    d.bm_profile(bm, [(-0.0105, 0.0700), (0.0150, 0.0700), (0.0150, 0.0815), (-0.0080, 0.0815), (-0.0105, 0.0790)], 0.0216)
    for side in (-1, 1):
        d.bm_profile(bm, [(0.0150, 0.0700), (0.0235, 0.0700), (0.0245, 0.0760), (0.0225, 0.0815), (0.0150, 0.0815)], 0.0052,
                     x=side * 0.0082)
    d.make("ToggleRearLink", bm, body, m_blue, "Rear toggle link: solid at the axle, forked round the front link's tongue.",
           bevel=0.0007)
    for side in (-1, 1):
        bm = bmesh.new()
        prof = [(0.0108, 0.0), (0.0108, 0.0096), (0.0178, 0.0096), (0.0192, 0.0084), (0.0192, 0.0050), (0.0180, 0.0036),
                (0.0180, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        d.bm_lathe(bm, prof, sides=32, axis="X", c=(0.0160, 0.0765))
        for k in range(4):   # gripping grooves round the rim
            x0 = side * (0.0118 + 0.0016 * k)
            ring = [(x0, 0.0099), (x0 + side * 0.0008, 0.0099)]
            d.bm_lathe(bm, ring if side > 0 else ring[::-1], sides=32, axis="X", c=(0.0160, 0.0765), cap=False)
        d.make("ToggleKnob_%s" % ("R" if side > 0 else "L"), bm, body, m_blue, "Toggle knob.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0152, 0.0), (-0.0152, 0.0032), (0.0152, 0.0032), (0.0152, 0.0)], sides=12, axis="X", c=(-0.0058, 0.0745))
    d.make("ToggleAxle", bm, body, m_blue, "Toggle axle through the rear of the frame.")
    z1, zn = SIGHT_Z + 0.0014, SIGHT_Z - 0.0012
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0055, 0.0810), (0.0055, 0.0810), (0.0055, z1), (0.0013, z1), (0.0, zn), (-0.0013, z1), (-0.0055, z1)],
              -0.0100, -0.0070)
    d.make("RearSight", bm, body, m_blue, "V notch on the rear toggle link. The sight line runs through it.", bevel=0.0002)

    # --- Frame -------------------------------------------------------------------------
    bm = bmesh.new()
    d.bm_profile(bm, d.fillet([(-0.0140, 0.0560), (0.1060, 0.0560), (0.1085, 0.0500), (0.1050, 0.0390), (0.0980, 0.0350),
                               (0.0660, 0.0350), (0.0625, 0.0340), (front(GRIP_BOTTOM), GRIP_BOTTOM), (back(GRIP_BOTTOM), GRIP_BOTTOM),
                               (back(0.0400), 0.0400), (-0.0080, 0.0470), (-0.0140, 0.0500)], 0.0030), 0.0230)
    # The magazine well: a pocket up the grip along its 21 degree rake, from the bottom to just under
    # the rails (loop cuts round its mouth, the cells pushed up the rake; no Boolean).
    import af_topo
    half = MAG_HALF_Y + 0.0005 / math.cos(RAKE)
    rise = -0.0100 + 0.0625 * math.cos(RAKE) - GRIP_BOTTOM
    af_topo.openings(bm, "Z", [(-0.0071, 0.0071, mag_centre(GRIP_BOTTOM) - half, mag_centre(GRIP_BOTTOM) + half)],
                     depth=rise, sign=-1, weight=0.4, vec=(0.0, T * rise, rise))
    af_topo.tidy(bm)
    frame = d.make("Frame", bm, body, m_blue,
                   "Frame and grip in one piece: rails, trigger housing, tang, straps raked 21 degrees; magazine well.", 0.0012)
    for side in (-1, 1):
        d.profile("FrameEar_%s" % ("R" if side > 0 else "L"), body, m_blue,
                  [(-0.0145, 0.0555), (0.0140, 0.0555), (0.0100, 0.0630), (-0.0030, 0.0690), (-0.0125, 0.0690),
                   (-0.0145, 0.0660)], width=0.0032, x=side * 0.0134, bevel=0.0007, round=0.0020,
                  note="Frame ear carrying the toggle axle; the knob rests on its ramp.")
    d.box("SidePlate", body, m_blue, (-0.0118, 0.0850, 0.0455), (0.0014, 0.0340, 0.0150), bevel=0.0005,
          note="Trigger side plate, left.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0118, 0.0044), (-0.0138, 0.0044), (-0.0144, 0.0036), (-0.0144, 0.0)], sides=16, axis="X", c=(0.1010, 0.0490))
    d.bm_box(bm, (-0.0132, 0.0975, 0.0450), (0.0016, 0.0046, 0.0095), rot=(-40.0, 0, 0))
    d.make("TakedownLever", bm, body, m_straw, "Take-down lever, left front.", bevel=0.0003)
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0118, 0.0034), (-0.0136, 0.0034), (-0.0140, 0.0028), (-0.0140, 0.0)], sides=12, axis="X", c=(0.0030, 0.0500))
    d.bm_box(bm, (-0.0130, -0.0030, 0.0520), (0.0016, 0.0046, 0.0105), rot=(62.0, 0, 0))
    d.make("SafetyLever", bm, body, m_straw, "Safety lever, left rear.", bevel=0.0003)
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0100, 0.0036), (-0.0134, 0.0036), (-0.0140, 0.0030), (-0.0140, 0.0)], sides=16, axis="X", c=(0.0665, 0.0405))
    for k in range(2):
        d.bm_lathe(bm, [(-0.0122 - 0.0008 * k * 1.6, 0.0038), (-0.0128 - 0.0008 * k * 1.6, 0.0038)], sides=16, axis="X",
                   c=(0.0665, 0.0405), cap=False)
    d.make("MagRelease", bm, body, m_straw, "Magazine release button, left, behind the trigger.")
    for nm, y, z, r in (("TriggerPin", 0.0790, 0.0430, 0.0018), ("FramePin", 0.0300, 0.0480, 0.0020)):
        bm = bmesh.new()
        d.bm_lathe(bm, [(-0.0120, 0.0), (-0.0120, r), (0.0120, r), (0.0120, 0.0)], sides=10, axis="X", c=(y, z))
        d.make(nm, bm, body, m_blue, "Cross pin through the frame.")

    # --- Grip ----------------------------------------------------------------------------
    d.profile("GripPanels", body, m_wood,
              [(front(0.0460) - 0.0050, 0.0460), (back(0.0460) + 0.0045, 0.0460), (back(-0.0465) + 0.0040, -0.0465),
               (front(-0.0465) - 0.0045, -0.0465)], width=0.0310, bevel=0.0040, segments=3, round=0.0050,
              note="Checkered walnut grip panels.")
    for side in (-1, 1):
        bm = bmesh.new()
        prof = [(0.0148, 0.0), (0.0148, 0.0030), (0.0157, 0.0030), (0.0160, 0.0024), (0.0160, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        centre = ((front(-0.0300) + back(-0.0300)) / 2.0, -0.0300)
        d.bm_lathe(bm, prof, sides=12, axis="X", c=centre)
        d.bm_box(bm, (side * 0.0161, centre[0], centre[1]), (0.0005, 0.0046, 0.0008))
        d.make("GripScrew_%s" % ("R" if side > 0 else "L"), bm, body, m_blue, "Grip screw.")
    d.box("StockLug", body, m_blue, (0.0, back(-0.0400) - 0.0010, -0.0400), (0.0100, 0.0050, 0.0120),
          rot=(-math.degrees(RAKE), 0, 0), bevel=0.0010, note="Stock lug on the back strap.")

    # --- Trigger and guard -----------------------------------------------------------
    gc, r_out, r_in = (0.0830, 0.0230), 0.0165, 0.0138
    d.profile("TriggerGuard", body, m_blue, _arc(gc, r_out, 125.0, 415.0, 28) + _arc(gc, r_in, 415.0, 125.0, 28),
              width=0.0096, bevel=0.0012, segments=3, note="Round trigger guard, edges rounded.")
    d.blade("Weapon_Trigger", moving, m_straw,
            [(0.0790, 0.0415, 0.0090), (0.0784, 0.0335, 0.0064), (0.0794, 0.0255, 0.0050), (0.0828, 0.0188, 0.0044),
             (0.0884, 0.0146, 0.0036)], width=0.0062,
            note="Trigger: a curved, rounded blade. Bone 'trigger'; pivot at (y 0.079, z 0.043).")
    # --- Memory points -------------------------------------------------------------------
    d.empty("Mem_Muzzle", memory, (0, MUZZLE_Y, BORE), "'usti hlavne' - muzzle.")
    d.empty("Mem_BarrelEnd", memory, (0, 0.1050, BORE), "'konec hlavne' - with the muzzle sets the firing direction.")
    d.empty("Mem_Eye", memory, (0, -0.2586, SIGHT_Z), "'eye' - iron sight camera (the vanilla P1's).")
    d.empty("Mem_CaseStart", memory, (0.0020, 0.0700, BORE + 0.0130), "'nabojnicestart' - where spent cases appear.")
    d.empty("Mem_CaseEnd", memory, (0.0200, 0.0560, BORE + 0.0600), "'nabojniceend' - cases fly up and back.")

    # --- Attachment proxies ----------------------------------------------------------------
    d.empty("Proxy_Magazine", proxies, MAG_AT, "magazine proxy (slot magazine); the AF P08 magazine's origin.",
            kind="ARROWS", size=0.02)
    d.empty("Proxy_Bottle", proxies, (0, MUZZLE_Y + 0.0560, BORE - 0.0003),
            "bottle_suppressor proxy (slot suppressorImpro); same offset from the barrel as on the P1.", kind="ARROWS", size=0.02)
    d.empty("Proxy_Suppressor", proxies, (0, MUZZLE_Y + 0.0896, BORE + 0.0001),
            "suppressor_45acp proxy (slot pistolMuzzle); same offset from the barrel as on the P1.", kind="ARROWS", size=0.02)


# ----------------------------------------------------------------------------
# Build: the magazine (its own model; origin = the pistol's magazine proxy)
# ----------------------------------------------------------------------------

def build_magazine():
    d.PREFIX = MAG_PREFIX
    old_prefix, m41.PREFIX = m41.PREFIX, MAG_PREFIX
    try:
        d.clean()
        body = d.collection("Body")
        d.collection("Moving")
        m_tin = d.material("Tin", (0.30, 0.30, 0.31), rough=0.34, metal=1.0, bump=0.02, bump_scale=1300, rough_var=0.08,
                           wear=0.5, wear_rgb=(0.50, 0.50, 0.51), scratches=0.6, machining=0.08)
        m_base = m41.woodify(d.material("Base", (0.17, 0.070, 0.030), rough=0.50, metal=0.0, bump=0.05, bump_scale=1000,
                                        rough_var=0.08, wear=0.35, wear_rgb=(0.32, 0.18, 0.08), scratches=0.3),
                             dark=(0.060, 0.021, 0.009), light=(0.19, 0.070, 0.025))
        m_brass = d.material("Brass", (0.60, 0.38, 0.12), rough=0.30, metal=1.0, rough_var=0.06, scratches=0.25,
                             wear_rgb=(0.74, 0.55, 0.26))
        m_jacket = d.material("Jacket", (0.50, 0.24, 0.12), rough=0.34, metal=1.0, rough_var=0.05)
        tin = m41._Post(m_tin)
        img, asp = m41.stamp_image("P08Mag", ["2741"])
        tin.stamp(img, asp, -0.0220, 0.0034, 1, -0.0380, rgb=(0.10, 0.10, 0.105))

        def c(z):   # the magazine's centre line, in its own coordinates
            return T * z

        h = MAG_HALF_Y
        d.profile("Body", body, m_tin,
                  [(c(MAG_TOP) - h, MAG_TOP), (c(MAG_TOP) + h, MAG_TOP), (c(MAG_BOTTOM) + h, MAG_BOTTOM),
                   (c(MAG_BOTTOM) - h, MAG_BOTTOM)], width=0.0128, bevel=0.0016, segments=2, note="Magazine body.")
        bm = bmesh.new()
        for side in (-1, 1):
            d.bm_box(bm, (side * 0.0064, c(-0.004) + 0.0040, -0.0040), (0.0009, 0.0050, 0.0800), rot=(-math.degrees(RAKE), 0, 0))
        d.make("Ribs", bm, body, m_tin, "Long ribs pressed into the sides.", bevel=0.0004)
        zb = MAG_BOTTOM
        d.profile("BasePlug", body, m_base,
                  [(c(zb) - h - 0.0014, zb), (c(zb) + h + 0.0014, zb), (c(zb - 0.0080) + h - 0.0010, zb - 0.0080),
                   (c(zb - 0.0080) - h - 0.0030, zb - 0.0080)], width=0.0150, bevel=0.0014, round=0.0020,
                  note="Wooden base plug.")
        for side in (-1, 1):
            bm = bmesh.new()
            prof = [(0.0075, 0.0), (0.0075, 0.0058), (0.0112, 0.0058), (0.0120, 0.0048), (0.0120, 0.0)]
            if side < 0:
                prof = [(-x, r) for x, r in prof][::-1]
            d.bm_lathe(bm, prof, sides=20, axis="X", c=(c(zb - 0.0040) - 0.0010, zb - 0.0042))
            d.make("BaseKnob_%s" % ("R" if side > 0 else "L"), bm, body, m_base, "Round grip knob on the base plug.")
        bm = bmesh.new()
        d.bm_lathe(bm, [(0.0064, 0.0), (0.0064, 0.0030), (0.0086, 0.0030), (0.0090, 0.0024), (0.0090, 0.0)], sides=12, axis="X",
                   c=(c(0.0150) + 0.0040, 0.0150))
        d.make("FollowerButton", bm, body, m_tin, "Follower button on the right side.")
        base = (c(MAG_TOP) - 0.0148, MAG_TOP + 0.0020)
        for nm, mat, prof in (("Round", m_brass, ROUND_CASE), ("RoundSlug", m_jacket, ROUND_SLUG)):
            bm = bmesh.new()
            d.bm_lathe(bm, [(base[0] + y, r) for y, r in prof], sides=12, c=(0.0, base[1]), cap=False)
            d.make(nm, bm, body, mat, "Top round between the feed lips.")
    finally:
        m41.PREFIX = old_prefix


if __name__ == "__main__":
    build()
    build_magazine()
    print("AF P08 and its magazine built.")
