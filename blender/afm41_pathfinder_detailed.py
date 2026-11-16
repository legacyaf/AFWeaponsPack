"""
AF M41 "Pathfinder" - bolt-action sniper rifle (Blender 4.2+ / tested on 5.3).

Second weapon of the AF Weapons Pack. A full-length wood-stocked, turned-down-bolt
service rifle in the style of the early-1940s sniper conversions.

It reuses the helpers of af7_vanguard_detailed.py (materials, box / profile / lathe,
Boolean cuts), so that file must sit next to this one.

FRAME - this is the important part
  The rifle borrows the vanilla Mosin 91/30's animations, so it is modelled directly in
  the Mosin's own frame, read out of dz\\weapons\\firearms\\mosin9130\\mosin9130.p3d:
      working +Y (forward)  = Mosin -X        working +Z (up) = Mosin +Y
      working +X (right)    = Mosin +Z        origin          = Mosin origin
  Numbers taken from the vanilla model (converted to the working frame):
      bore line            z = 0.1161,  muzzle at y = 0.8305,  butt at y = -0.409
      bolt axis            z = 0.1147   (the bolt bones turn about this line)
      bolt handle          at y = 0.013, knob about 4 cm right and 2 cm below the axis
      trigger pivot        y = -0.0515, z = 0.0676
      iron-sight eye       y = -0.1582, z = 0.1377
      PU scope proxy       y = 0.0094,  z = 0.1245
  Keep those and the Mosin's bolt, reload and aiming animations line up.

Run: Scripting tab > Open > this file > Run Script, then afm41_pathfinder_dayz_export.py.
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

PREFIX = "M41_"
BORE = 0.1161        # bore line height (vanilla Mosin)
BOLT_Z = 0.1147      # bolt axis height (vanilla Mosin 'bolt_axis')
HANDLE_Y = 0.013     # bolt handle station (vanilla Mosin)
SIGHT_Z = 0.1377     # iron sight line (vanilla Mosin 'eye')

# AF plate on both sides of the butt: (y0, z0, width, height, |x| min, |x| max)
LOGO_BUTT = (-0.318, 0.031, 0.036, 0.018, 0.0222, 0.0232)


# ----------------------------------------------------------------------------
# Extra helpers for organic (wood) parts
# ----------------------------------------------------------------------------

def bm_loft(bm, sections, sides=28, power=2.6, cap=True):
    """Rounded body through cross-sections [(y, z_bottom, z_top, half_width), ...].
    Each section is a superellipse (power 2 = ellipse, higher = squarer)."""
    rings = []
    for y, zb, zt, hw in sections:
        zc, hh = (zb + zt) / 2.0, (zt - zb) / 2.0
        ring = []
        for k in range(sides):
            t = 2.0 * math.pi * (k + 0.5) / sides
            c, s = math.cos(t), math.sin(t)
            x = hw * math.copysign(abs(c) ** (2.0 / power), c)
            z = zc + hh * math.copysign(abs(s) ** (2.0 / power), s)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            f = bm.faces.new((A[i], A[j], B[j], B[i]))
            f.smooth = True
    if cap:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1][::-1])


def bm_torus(bm, centre, R, r, seg=18, sides=8, squash=1.0):
    """Ring lying in the X-Z plane (a sling loop seen from the side of the rifle).
    squash < 1 flattens it vertically into an oval."""
    cx, cy, cz = centre
    rings = []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        ring = []
        for j in range(sides):
            b = 2.0 * math.pi * j / sides
            rad = R + r * math.cos(b)
            ring.append(bm.verts.new((cx + rad * math.cos(a), cy + r * math.sin(b), cz + rad * math.sin(a) * squash)))
        rings.append(ring)
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(sides):
            k = (j + 1) % sides
            f = bm.faces.new((A[j], B[j], B[k], A[k]))
            f.smooth = True


def loft(name, col, mat, sections, note="", **kw):
    bm = bmesh.new()
    bm_loft(bm, sections, **kw)
    return d.make(name, bm, col, mat, note, 0.0, sharp=50.0)


def woodify(mat, dark, light):
    """Replace a material's flat base colour with wood grain running along the stock."""
    nt = mat.node_tree
    N = d._Nodes(nt)
    base = next(n for n in nt.nodes if n.type == "RGB")
    users = [l.to_socket for l in base.outputs[0].links]
    geo = N.new("ShaderNodeNewGeometry")

    def noise(scale, detail, distortion):
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale
        nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 1.0
        n.inputs["Detail"].default_value = detail
        if "Distortion" in n.inputs:
            n.inputs["Distortion"].default_value = distortion
        nt.links.new(mp.outputs[0], n.inputs["Vector"])
        return n.outputs[0]

    broad = N.math("MULTIPLY", N.math("SUBTRACT", noise((70.0, 2.2, 70.0), 8.0, 1.6), 0.30), 2.4, clamp=True)
    fine = N.math("MULTIPLY", N.math("SUBTRACT", noise((900.0, 9.0, 900.0), 3.0, 0.4), 0.52), 5.0, clamp=True)
    col = N.mix(broad, dark, light)
    col = N.mix(N.math("MULTIPLY", fine, 0.45), col, tuple(c * 0.45 for c in dark))
    for sock in users:
        nt.links.new(col, sock)
    return mat


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def build():
    d.PREFIX = PREFIX
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
    m_wood = woodify(d.material("Walnut", (0.20, 0.085, 0.035), rough=0.44, metal=0.0, bump=0.06, bump_scale=900,
                                rough_var=0.08, wear=0.45, wear_rgb=(0.36, 0.20, 0.09), scratches=0.30,
                                skin_img=d.pattern_image()),
                     dark=(0.070, 0.024, 0.010), light=(0.215, 0.080, 0.028))
    m_blue = d.material("BluedSteel", (0.022, 0.024, 0.030), rough=0.36, metal=1.0, bump=0.03, bump_scale=1200,
                        rough_var=0.10, wear=0.7, wear_rgb=(0.34, 0.34, 0.36), scratches=0.5, machining=0.07)
    m_bolt = d.material("BoltSteel", (0.42, 0.42, 0.43), rough=0.28, metal=1.0, rough_var=0.06,
                        wear_rgb=(0.60, 0.60, 0.61), scratches=0.35, machining=0.28)
    m_plate = d.material("Plate", (0.030, 0.032, 0.036), rough=0.46, metal=0.9, bump=0.04, bump_scale=900,
                         rough_var=0.06, wear=0.6, wear_rgb=(0.42, 0.43, 0.45), logo=LOGO_BUTT, logo_img=logo)

    # --- Stock (one piece of walnut, butt to nose cap) -------------------------
    stock_sections = [
        (-0.409, -0.043, 0.090, 0.0215),
        (-0.330, -0.020, 0.096, 0.0215),
        (-0.250, 0.003, 0.100, 0.0210),
        (-0.185, 0.022, 0.101, 0.0195),   # comb nose
        (-0.160, 0.030, 0.094, 0.0180),
        (-0.125, 0.040, 0.093, 0.0170),   # wrist
        (-0.090, 0.050, 0.099, 0.0175),
        (-0.060, 0.057, 0.104, 0.0190),
        (-0.030, 0.058, 0.106, 0.0205),
        (0.100, 0.058, 0.108, 0.0210),
        (0.160, 0.064, 0.108, 0.0200),
        (0.300, 0.070, 0.110, 0.0185),
        (0.560, 0.076, 0.112, 0.0170),
        (0.660, 0.080, 0.112, 0.0155),
    ]
    stock = loft("Stock", body, m_wood, stock_sections,
                 note="Walnut stock, straight wrist. Sections are (y, bottom, top, half width).")
    for side in (-1, 1):
        bm = bmesh.new()
        d.bm_lathe(bm, [(0.115, 0.0), (0.137, 0.0065), (0.275, 0.0065), (0.300, 0.0)], sides=12,
                   c=(side * 0.0238, 0.094))
        groove = d.make("Stock_GrooveCutter_%s" % ("R" if side > 0 else "L"), bm, cutters, None,
                        "Boolean cutter: finger groove along the fore-end.")
        d.cut(stock, groove, "Groove_%s" % ("R" if side > 0 else "L"))

    loft("Handguard", body, m_wood,
         [(0.238, 0.104, 0.1340, 0.0178), (0.250, 0.104, 0.1350, 0.0184), (0.400, 0.106, 0.1330, 0.0172),
          (0.560, 0.108, 0.1305, 0.0160), (0.648, 0.110, 0.1280, 0.0150)],
         power=2.2, note="Upper handguard over the barrel, from the rear sight to the nose cap.")

    # --- Barrel and receiver ---------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.098, 0.0150), (0.172, 0.0150), (0.178, 0.0126), (0.235, 0.0120), (0.420, 0.01073), (0.640, 0.00925), (0.672, 0.00905),
                    (0.826, 0.0082), (0.8305, 0.0077), (0.8305, 0.0040), (0.800, 0.0040), (0.800, 0.0)],
               sides=28, c=(0.0, BORE))
    d.make("Barrel", bm, body, m_blue, "Stepped, tapered barrel. Muzzle at y = 0.8305 like the vanilla rifle.")

    bm = bmesh.new()
    d.bm_lathe(bm, [(0.8305, 0.0078), (0.8322, 0.0072), (0.8322, 0.0042), (0.8305, 0.0042)],
               sides=28, c=(0.0, BORE), closed=True, cap=False)
    d.make("MuzzleCrown", bm, body, m_blue,
           "Muzzle crown. Selection 'hide_barrel': hidden while a muzzle attachment is fitted.")

    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.052, 0.0105), (-0.052, 0.0172), (-0.030, 0.0172), (-0.028, 0.0162), (0.052, 0.0162),
                    (0.054, 0.0178), (0.100, 0.0178), (0.100, 0.0105)],
               sides=32, c=(0.0, BORE), closed=True, cap=False)
    receiver = d.make("Receiver", bm, body, m_blue,
                      "Receiver: open-topped tube. The bolt handle travels back along the top slot.")
    for nm, centre, size in (("Slot", (0.0, -0.014, 0.135), (0.0175, 0.134, 0.022)),
                             ("Port", (0.014, 0.012, 0.1245), (0.020, 0.078, 0.020)),
                             ("HandleNotch", (0.014, HANDLE_Y, 0.112), (0.020, 0.019, 0.020))):
        c = d.box("Receiver_%sCutter" % nm, cutters, None, centre, size, bevel=0, note="Boolean cutter.")
        d.cut(receiver, c, nm)
    d.box("ReceiverTang", body, m_blue, (0.0, -0.076, 0.1020), (0.012, 0.046, 0.004), rot=(9.5, 0, 0), bevel=0.0008,
          note="Rear tang let into the wrist.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.060, 0.0181), (0.064, 0.0186), (0.092, 0.0186), (0.096, 0.0181)], sides=32, c=(0.0, BORE),
               closed=True, cap=False)
    d.make("ReceiverRing", bm, body, m_blue, "Raised receiver ring over the chamber.")

    # --- Bolt (three bones, as on the vanilla rifle) ---------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.030, 0.0), (-0.030, 0.0086), (0.086, 0.0086), (0.090, 0.0070), (0.090, 0.0)],
               sides=24, c=(0.0, BOLT_Z))
    for k in range(3):   # gas-escape / guide flutes read as dark lines
        d.bm_lathe(bm, [(0.030 + 0.012 * k, 0.0088), (0.0325 + 0.012 * k, 0.0088)], sides=24, c=(0.0, BOLT_Z), cap=False)
    d.make("BoltBody", bm, moving, m_bolt, "Bolt body. Bone 'boltbody'.")

    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.078, 0.0), (-0.078, 0.0085), (-0.076, 0.0108), (-0.066, 0.0108), (-0.064, 0.0090),
                    (-0.032, 0.0090), (-0.030, 0.0080), (-0.030, 0.0)], sides=24, c=(0.0, BOLT_Z))
    for k in range(4):
        d.bm_lathe(bm, [(-0.0750 + 0.0022 * k, 0.0111), (-0.0741 + 0.0022 * k, 0.0111)], sides=24, c=(0.0, BOLT_Z), cap=False)
    d.make("BoltCocking", bm, moving, m_blue, "Cocking piece at the back of the bolt. Bone 'boltbodys'.")

    bm = bmesh.new()
    d.bm_lathe(bm, [(HANDLE_Y - 0.0075, 0.0088), (HANDLE_Y - 0.0065, 0.0102), (HANDLE_Y + 0.0065, 0.0102),
                    (HANDLE_Y + 0.0075, 0.0088)], sides=24, c=(0.0, BOLT_Z), cap=False)
    arm = bmesh.new()
    d.bm_lathe(arm, [(0.006, 0.0046), (0.033, 0.0040), (0.0355, 0.0070), (0.040, 0.0100), (0.0455, 0.0108),
                     (0.0505, 0.0090), (0.053, 0.0050), (0.0535, 0.0)], sides=16, axis="X", c=(HANDLE_Y, BOLT_Z))
    bmesh.ops.rotate(arm, verts=arm.verts[:], cent=Vector((0.0, HANDLE_Y, BOLT_Z)),
                     matrix=Matrix.Rotation(math.radians(24.0), 3, "Y"))
    me = bpy.data.meshes.new("tmp_arm")
    arm.to_mesh(me)
    arm.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    d.make("BoltHandle", bm, moving, m_bolt, "Turned-down bolt handle and knob. Bone 'bolthandle'.")

    # --- Trigger group ---------------------------------------------------------
    d.profile("Weapon_Trigger", moving, m_blue,
              [(-0.0485, 0.0620), (-0.0545, 0.0620), (-0.0585, 0.0480), (-0.0570, 0.0370), (-0.0535, 0.0345),
               (-0.0530, 0.0470)],
              width=0.0058, bevel=0.0008, note="Trigger. Bone 'trigger'; pivot at (y -0.0515, z 0.0676).")
    d.profile("TriggerGuard", body, m_blue,
              [(-0.086, 0.0585), (-0.081, 0.0300), (-0.066, 0.0215), (-0.034, 0.0215), (-0.017, 0.0320), (-0.009, 0.0585),
               (-0.0125, 0.0585), (-0.0200, 0.0340), (-0.0355, 0.0247), (-0.0645, 0.0247), (-0.0780, 0.0322),
               (-0.0825, 0.0585)],
              width=0.012, bevel=0.0007, note="Trigger guard bow.")
    d.box("FloorPlate", body, m_blue, (0.0, 0.036, 0.0568), (0.0175, 0.108, 0.0042), bevel=0.0012,
          note="Flush magazine floor plate (internal 5-round magazine).")
    d.box("GuardTang", body, m_blue, (0.0, -0.062, 0.0575), (0.014, 0.090, 0.0035), bevel=0.0010,
          note="Trigger guard tang.")
    for y in (-0.098, 0.084):
        bm = bmesh.new()
        d.bm_lathe(bm, [(0.0540, 0.0), (0.0540, 0.0042), (0.0552, 0.0036), (0.0600, 0.0036)], sides=12, axis="Z", c=(0.0, y))
        d.bm_box(bm, (0.0, y, 0.0542), (0.0060, 0.0009, 0.0008))
        d.make("GuardScrew_%d" % (0 if y < 0 else 1), bm, body, m_blue, "Action screw.")

    # --- Sights ----------------------------------------------------------------
    d.box("RearSightBase", body, m_blue, (0.0, 0.2025, 0.1292), (0.0145, 0.066, 0.0062), bevel=0.0010,
          note="Rear sight base on the barrel.")
    d.box("RearSightLeaf", body, m_blue, (0.0, 0.2060, 0.1332), (0.0100, 0.052, 0.0022), rot=(-1.2, 0, 0),
          bevel=0.0005, note="Tangent leaf.")
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0080, 0.1310), (0.0080, 0.1310), (0.0080, 0.1392), (0.0013, 0.1392), (0.0013, 0.1366),
                   (-0.0013, 0.1366), (-0.0013, 0.1392), (-0.0080, 0.1392)], 0.1810, 0.1838)
    d.make("RearSightNotch", bm, body, m_blue, "Rear notch. The sight line (z = 0.1377) runs through it.", bevel=0.0003)
    d.box("RearSightSlider", body, m_blue, (0.0, 0.2150, 0.1348), (0.0165, 0.0080, 0.0036), bevel=0.0006,
          note="Range slider.")

    bm = bmesh.new()
    d.bm_lathe(bm, [(0.786, 0.0086), (0.788, 0.0108), (0.810, 0.0108), (0.812, 0.0086)], sides=24, c=(0.0, BORE),
               cap=False)
    d.make("FrontSightBand", bm, body, m_blue, "Front sight band.")
    d.box("FrontSightBlock", body, m_blue, (0.0, 0.799, 0.1285), (0.0070, 0.022, 0.0080), bevel=0.0010,
          note="Front sight block.")
    d.box("FrontSightPost", body, m_blue, (0.0, 0.799, 0.13485), (0.0018, 0.0026, 0.0057), bevel=0.0002,
          note="Front sight blade; top at the sight line.")
    for side in (-1, 1):
        d.box("FrontSightEar_%s" % ("R" if side > 0 else "L"), body, m_blue, (side * 0.0062, 0.799, 0.1338),
              (0.0013, 0.014, 0.0125), rot=(0, side * -12.0, 0), bevel=0.0005, note="Protective ear.")

    # --- Furniture and fittings ------------------------------------------------
    loft("MiddleBand", body, m_blue,
         [(0.4070, 0.0690, 0.1356, 0.0200), (0.4085, 0.0683, 0.1362, 0.0205), (0.4240, 0.0686, 0.1360, 0.0204),
          (0.4255, 0.0693, 0.1354, 0.0199)], power=3.2,
         note="Middle barrel band.")
    bm = bmesh.new()
    d.bm_box(bm, (0.0, 0.416, 0.0660), (0.0075, 0.011, 0.0070))
    d.bm_lathe(bm, [(-0.0058, 0.0), (-0.0058, 0.0021), (0.0058, 0.0021), (0.0058, 0.0)], sides=10, axis="X", c=(0.416, 0.0640))
    bm_torus(bm, (0.0, 0.416, 0.0555), 0.0105, 0.0016, squash=0.8)
    d.make("BandSwivel", bm, body, m_blue, "Sling swivel under the middle band.")
    loft("NoseCap", body, m_blue,
         [(0.6400, 0.0772, 0.1290, 0.0172), (0.6660, 0.0782, 0.1285, 0.0168), (0.6720, 0.0810, 0.1275, 0.0150)],
         power=2.3, note="Nose cap.")
    d.box("BayonetLug", body, m_blue, (0.0, 0.698, 0.0935), (0.0070, 0.052, 0.0065), bevel=0.0010,
          note="Bayonet lug under the barrel.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.660, 0.0028), (0.775, 0.0028), (0.777, 0.0040), (0.789, 0.0040), (0.791, 0.0030), (0.791, 0.0)],
               sides=12, c=(0.0, 0.1020))
    d.make("CleaningRod", bm, body, m_bolt, "Cleaning rod under the barrel.")
    loft("ButtPlate", body, m_blue,
         [(-0.4140, -0.0425, 0.0895, 0.0205), (-0.4125, -0.0438, 0.0908, 0.0220), (-0.4085, -0.0438, 0.0908, 0.0220)],
         note="Steel butt plate.")
    bm = bmesh.new()
    d.bm_box(bm, (0.0, -0.335, -0.0225), (0.016, 0.030, 0.0030), rot=(-16.5, 0, 0))
    d.bm_box(bm, (0.0, -0.335, -0.0260), (0.0070, 0.010, 0.0070), rot=(-16.5, 0, 0))
    bm_torus(bm, (0.0, -0.3365, -0.0355), 0.0100, 0.0016, squash=0.8)
    d.make("ButtSwivel", bm, body, m_blue, "Rear sling swivel.")
    for z in (0.066, -0.016):
        bm = bmesh.new()
        d.bm_lathe(bm, [(-0.4152, 0.0), (-0.4152, 0.0034), (-0.4142, 0.0042), (-0.4120, 0.0042)], sides=12, c=(0.0, z))
        d.bm_box(bm, (0.0, -0.4152, z), (0.0058, 0.0008, 0.0009))
        d.make("ButtScrew_%d" % (0 if z < 0 else 1), bm, body, m_blue, "Butt plate screw.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0179, 0.0), (-0.0179, 0.0026), (-0.0174, 0.0030), (0.0174, 0.0030), (0.0179, 0.0026), (0.0179, 0.0)],
               sides=10, axis="X", c=(0.655, 0.0930))
    d.make("NoseCapScrew", bm, body, m_blue, "Nose cap cross screw.")
    for side in (-1, 1):
        d.profile("RearSightWall_%s" % ("R" if side > 0 else "L"), body, m_blue,
                  [(0.1700, 0.1262), (0.2350, 0.1262), (0.2350, 0.1300), (0.1930, 0.1350), (0.1700, 0.1350)],
                  width=0.0020, x=side * 0.0066, bevel=0.0004, note="Rear sight side wall with the elevation ramp.")
    d.box("BoltStop", body, m_blue, (-0.0180, -0.040, 0.1120), (0.0040, 0.018, 0.0100), bevel=0.0010,
          note="Bolt stop on the left of the receiver.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.0530, 0.0), (0.0530, 0.0028), (0.0560, 0.0028)], sides=10, axis="Z", c=(0.0, -0.0125))
    d.make("FloorPlateCatch", bm, body, m_blue, "Floor plate release.")
    bm = bmesh.new()
    for k in range(3):   # reinforce rings where the barrel steps down
        d.bm_lathe(bm, [(0.1040 + 0.022 * k, 0.0150), (0.1048 + 0.022 * k, 0.0155), (0.1062 + 0.022 * k, 0.0155),
                        (0.1070 + 0.022 * k, 0.0150)], sides=28, c=(0.0, BORE), cap=False)
    d.make("BarrelRings", bm, body, m_blue, "Rings on the barrel reinforce.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0221, 0.0), (-0.0221, 0.0052), (-0.0214, 0.0058), (0.0214, 0.0058), (0.0221, 0.0052),
                    (0.0221, 0.0)], sides=16, axis="X", c=(0.078, 0.086))
    d.make("CrossBolt", bm, body, m_blue, "Recoil cross bolt through the stock.")
    for side in (-1, 1):
        bm = bmesh.new()
        prof = [(0.0185, 0.0), (0.0185, 0.0205), (0.0220, 0.0205), (0.0226, 0.0190), (0.0226, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        d.bm_lathe(bm, prof, sides=32, axis="X", c=(-0.300, 0.040))
        d.make("StockDisc_%s" % ("R" if side > 0 else "L"), bm, body, m_plate,
               "Unit disc let into the butt, carrying the AF logo.")

    # --- Memory points ---------------------------------------------------------
    d.empty("Mem_Muzzle", memory, (0, 0.8305, BORE), "'usti hlavne' - muzzle (vanilla position).")
    d.empty("Mem_BarrelEnd", memory, (0, 0.4225, BORE), "'konec hlavne' - with the muzzle sets the firing direction.")
    d.empty("Mem_Eye", memory, (0, -0.1582, SIGHT_Z), "'eye' - iron sight camera (vanilla position).")
    d.empty("Mem_EyeScope", memory, (0, -0.2637, 0.1672), "'eyescope' (vanilla position).")
    d.empty("Mem_CaseStart", memory, (0.010, 0.030, 0.128), "'nabojnicestart' - where spent cases appear.")
    d.empty("Mem_CaseEnd", memory, (0.080, 0.010, 0.170), "'nabojniceend' - direction spent cases fly.")

    # --- Attachment proxies (vanilla Mosin positions) --------------------------
    d.empty("Proxy_Optic", proxies, (0, 0.0094, 0.1245), "optic_puscope proxy (slot weaponOpticsMosin).", kind="ARROWS", size=0.03)
    d.empty("Proxy_Compensator", proxies, (0, 0.8311, 0.1162), "mosin_compensator proxy (slot weaponMuzzleMosin).", kind="ARROWS", size=0.03)
    d.empty("Proxy_Suppressor", proxies, (-0.0006, 0.8952, 0.1191), "bottle_suppressor proxy (slot suppressorImpro).", kind="ARROWS", size=0.03)
    d.empty("Proxy_Bayonet", proxies, (0, 0.7916, 0.1161), "bayonet_mosin proxy (slot weaponBayonetMosin).", kind="ARROWS", size=0.03)


if __name__ == "__main__":
    build()
    print("AF M41 Pathfinder detailed model built.")
