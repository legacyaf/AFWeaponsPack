"""
AF StG 44 - 7.62 mm assault rifle (Blender 4.2+ / tested on 5.3).

Fifth weapon of the AF Weapons Pack: the stamped-steel assault rifle of 1944, with its own
curved 30-round magazine and its own telescopic sight (two more small models, built by
build_magazine() and build_scope() below).

From this weapon on there is no AF logo. Instead "legacy was here" is scratched into the
receiver in small letters (scratch_image / the steel.stamp call in _build_gun).

It reuses the helpers of af7_vanguard_detailed.py and afm41_pathfinder_detailed.py, so
those files must sit next to this one.

FRAME
  The rifle borrows the vanilla AKM's animations, so it is modelled in the AKM's own frame,
  read out of dz\\weapons\\firearms\\AKM\\akm.p3d:
      working +Y (forward) = AKM -X      working +Z (up) = AKM +Y
      working +X (right)   = AKM +Z
  The AKM's centre line is 10.2 mm to the LEFT of its model origin (x = -0.0102). The rifle is
  built here on x = 0 and the export shifts it (empty 'Origin', ex.ORIGIN_EMPTY).
  Numbers taken from the vanilla model (converted to the working frame, centre line at x = 0):
      bore line            z = 0.0976        muzzle y = 0.4331, 'konec hlavne' y = 0.0252
      eye (iron sights)    y = -0.230, z = 0.150   (sight line 52 mm above the bore)
      receiver             y -0.154..0.095, z 0.069..0.133
      trigger pivot        y = -0.072, z = 0.0672; blade y -0.082..-0.057, z 0.033..0.067
      trigger guard        y -0.084..-0.032, bottom z = 0.030
      pistol grip          top y -0.144..-0.084 at z 0.060, bottom y -0.155..-0.117 at z -0.038
      magazine proxy       y = 0.0368, z = 0.0321, leaning 20.7 degrees
      bolt handle          right side, y = 0.075, z = 0.10; bolt travels about 10 cm back
      left hand            under the handguard, y 0.10..0.30, underside z = 0.075
      skeleton             magazine, trigger, bolt, firemode, mag_release, bullet (no parents)
  What differs from a real StG 44 because of that frame:
    - The cocking handle is on the right, where the AKM animation puts the hand (real: left).
    - It fires 7.62x39 (the AKM's ammunition) from its own magazine, not 7.92x33.
    - The selector and magazine catch do not move.

Run: afstg44_run.py (headless), or Scripting tab > Run Script, then afstg44_dayz_export.py.
"""

import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    raise RuntimeError("Save the .blend next to this script first.")


if _here() not in sys.path:
    sys.path.insert(0, _here())
import af7_vanguard_detailed as d  # noqa: E402  (shared helpers)
import afm41_pathfinder_detailed as m41  # noqa: E402  (loft, stamps, wear helpers)

for _ch, _strokes in (("S", [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3.1), (3, 3.1), (4, 2.2), (4, 1), (3, 0), (1, 0), (0, 1)]]),
                      ("T", [[(0, 6), (4, 6)], [(2, 6), (2, 0)]]),
                      ("G", [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2.8), (2.2, 2.8)]])):
    m41._GLYPHS.setdefault(_ch, _strokes)

PREFIX = "STG_"
MAG_PREFIX = "STGM_"
SCOPE_PREFIX = "STGS_"
X_OFFSET = -0.0102       # the AKM's centre line, applied by the export
BORE = 0.0976
SIGHT_Z = 0.150
MUZZLE_Y = 0.470
R_TOP = 0.0190           # radius of the receiver's rounded top
TOP_Z = BORE + 0.0220    # axis of that rounding (the gas piston and bolt carrier run here)
MAG_AT = (0.0, 0.0350, 0.0300)        # magazine proxy = the magazine model's own origin
SCOPE_AT = (0.0, -0.0500, 0.1690)     # scope proxy = the scope model's own origin (its tube axis)

# "legacy was here": hand-scratched lower-case letters on the same 4 x 6 grid as the stamps.
_SCRATCH = {
    "l": [[(2, 6), (2, 0)]],
    "e": [[(0, 2.2), (4, 2.2), (3.2, 4), (1, 4), (0, 2.8), (0, 1), (1, 0), (3.6, 0)]],
    "g": [[(4, 4), (1, 4), (0, 3), (0, 1.4), (1, 0.4), (4, 0.4)], [(4, 4), (4, -1.4), (3, -2.2), (0.6, -2.2)]],
    "a": [[(0.6, 4), (3, 4), (4, 3), (4, 0)], [(4, 2.2), (1, 2.2), (0, 1.4), (0, 0.8), (1, 0), (4, 0)]],
    "c": [[(4, 3.6), (3, 4), (1, 4), (0, 3), (0, 1), (1, 0), (3, 0), (4, 0.4)]],
    "y": [[(0, 4), (2, 0.2)], [(4, 4), (1.2, -2.2)]],
    "w": [[(0, 4), (1, 0), (2, 3), (3, 0), (4, 4)]],
    "s": [[(4, 3.6), (3, 4), (1, 4), (0, 3.2), (1, 2.2), (3, 1.8), (4, 1), (3, 0), (0.6, 0), (0, 0.4)]],
    "h": [[(0, 6), (0, 0)], [(0, 3), (1.2, 4), (3, 4), (4, 3), (4, 0)]],
    "r": [[(0, 4), (0, 0)], [(0, 2.6), (1.4, 4), (3.4, 4)]],
    " ": [],
}


def scratch_image(name, text, px=44, ss=2, seed=7):
    """Lettering scratched with a nail: thin, uneven strokes that wander off the line and overshoot
    their ends, every letter a little different in height and slant. White = scratched.
    Returns (image, width / height)."""
    rnd = random.Random(seed)
    cw, half = 5.4, 0.20
    Wd, Hd = len(text) * cw + 2.0, 6.0 + 2.4 + 2.6
    s = px * ss
    W, H = int(Wd * s) // ss * ss, int(Hd * s) // ss * ss
    yy, xx = np.mgrid[0:H, 0:W]
    xx = ((xx + 0.5) / s).astype(np.float32)
    yy = ((yy + 0.5) / s).astype(np.float32)
    dist = np.full((H, W), 1e9, dtype=np.float32)

    def seg(a, b, grow):
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        length = max(math.hypot(dx, dy), 1e-6)
        ax, ay, bx, by = ax - dx / length * grow, ay - dy / length * grow, bx + dx / length * grow, by + dy / length * grow
        dx, dy = bx - ax, by - ay
        t = np.clip(((xx - ax) * dx + (yy - ay) * dy) / max(dx * dx + dy * dy, 1e-9), 0.0, 1.0)
        np.minimum(dist, np.hypot(xx - ax - t * dx, yy - ay - t * dy), out=dist)

    for ci, ch in enumerate(text):
        ox = 1.0 + ci * cw + rnd.uniform(-0.25, 0.25)
        oy = 3.6 + rnd.uniform(-0.35, 0.35) + 0.012 * ci * cw      # the line climbs a little
        slant, size = rnd.uniform(-0.10, 0.16), rnd.uniform(0.88, 1.08)
        for poly in _SCRATCH[ch]:
            pts = [(ox + (x + slant * y) * size + rnd.uniform(-0.16, 0.16), oy + y * size + rnd.uniform(-0.16, 0.16))
                   for x, y in poly]
            for a, b in zip(pts, pts[1:]):
                seg(a, b, rnd.uniform(0.0, 0.35))
    mask = np.clip((half - dist) * px + 0.5, 0.0, 1.0)
    mask = mask.reshape(H // ss, ss, W // ss, ss).mean(axis=(1, 3))
    rgba = np.ones((H // ss, W // ss, 4), dtype=np.float32)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = mask
    img = bpy.data.images.get(PREFIX + "Scratch_" + name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(PREFIX + "Scratch_" + name, W // ss, H // ss, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba.ravel())
    try:
        img.filepath_raw = os.path.join(_here(), "textures", "afstg44_scratch_%s.png" % name.lower())
        img.file_format = "PNG"
        img.save()
        img.pack()
    except Exception as exc:
        print("Scratch image not saved to disk:", exc)
    return img, Wd / Hd


# ----------------------------------------------------------------------------
# Pressed-detail sheets. Sheet steel carries its detail as shallow pressings, not as separate
# parts: flutes, beads, spot welds, struck letters. They are drawn here once as a height map of
# each side of the rifle (the "high-poly" source) and projected onto the side faces, where the
# bake turns them into the normal map. Two masks are derived from the same heights, as a texture
# artist's generators do: where dirt settles (concave creases, recess floors) and where the
# finish rubs off (convex rims, tops of beads).
# ----------------------------------------------------------------------------

GUN_WINDOW = (-0.156, 0.012, 0.406, 0.124)      # side window of the rifle: y0, z0, width, height (m)
MAG_WINDOW = (-0.034, -0.188, 0.134, 0.226)     # side window of the magazine, in its own frame
SHEET_PX = 10000.0                              # pixels per metre
SHEET_HMAX = 0.0006                             # height at red = 1; red = 0 is a hole right through
_SHEET_GLYPHS = {"E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3.1), (3, 3.1)]],
                 "D": [[(0, 0), (0, 6), (2.4, 6), (4, 4.4), (4, 1.6), (2.4, 0), (0, 0)]]}


def _blur(a, passes):
    for _ in range(passes):
        a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0)) / 3.0
        a = (a + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 3.0
    return a


class _Pen:
    """Draws pressings into a height map of one side, seen square on (u along +Y, v along +Z)."""

    def __init__(self, window):
        y0, z0, w, h = window
        self.W, self.H = int(w * SHEET_PX), int(h * SHEET_PX)
        zz, yy = np.mgrid[0:self.H, 0:self.W]
        self.Y = (y0 + (yy + 0.5) / SHEET_PX).astype(np.float32)
        self.Z = (z0 + (zz + 0.5) / SHEET_PX).astype(np.float32)
        self.hm = np.zeros((self.H, self.W), dtype=np.float32)

    @staticmethod
    def ease(t):
        t = np.clip(t, 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def rbox(self, yc, zc, hy, hz, r):
        qy, qz = np.abs(self.Y - yc) - (hy - r), np.abs(self.Z - zc) - (hz - r)
        return np.hypot(np.maximum(qy, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qy, qz), 0) - r

    def seg(self, a, b):
        (ay, az), (by, bz) = a, b
        dy, dz = by - ay, bz - az
        t = np.clip(((self.Y - ay) * dy + (self.Z - az) * dz) / max(dy * dy + dz * dz, 1e-12), 0.0, 1.0)
        return np.hypot(self.Y - ay - t * dy, self.Z - az - t * dz)

    def press(self, sd, depth, slope):      # flat-floored pressing with sloping walls
        np.add(self.hm, depth * self.ease(0.5 - sd / slope), out=self.hm)

    def bead(self, dist, r, height):        # round-topped bead (height < 0: a round-bottomed flute)
        np.add(self.hm, height * 0.5 * (1.0 + np.cos(np.pi * np.clip(dist / r, 0.0, 1.0))), out=self.hm)

    def weld(self, y, z):                   # spot weld: a shallow dimple with a faint raised ring
        dist = np.hypot(self.Y - y, self.Z - z)
        np.add(self.hm, -0.00022 * self.ease(1.0 - dist / 0.0022)
               + 0.00006 * np.exp(-((dist - 0.0026) / 0.00060) ** 2), out=self.hm)

    def hole(self, y, z, r):                # a hole right through the sheet
        inside = self.ease(0.5 - (np.hypot(self.Y - y, self.Z - z) - r) / 0.0006)
        self.hm = (self.hm * (1.0 - inside) - SHEET_HMAX * inside).astype(np.float32)

    def image(self, name, file_name):
        """Red = height, green = rub mask (convex rims, bead tops), blue = dirt mask (creases)."""
        mm = _blur(self.hm * 1000.0, 1)
        lap = (np.roll(mm, 3, 0) + np.roll(mm, -3, 0) + np.roll(mm, 3, 1) + np.roll(mm, -3, 1) - 4.0 * mm)
        lap /= max(float(np.percentile(np.abs(lap), 99.7)), 1e-6)
        rub = np.clip(_blur(np.clip(-lap, 0, 1), 2) * 1.6 + 0.25 * np.clip(mm / 0.30, 0, 1), 0, 1)
        rub *= np.clip(1.0 + mm / 0.05, 0.0, 1.0)
        dirt = np.clip(_blur(np.clip(lap, 0, 1), 3) * 1.8 + 0.12 * np.clip(-mm / 0.30, 0, 1), 0, 1)
        rgba = np.ones((self.H, self.W, 4), dtype=np.float32)
        rgba[..., 0] = np.clip(0.5 + self.hm / (2.0 * SHEET_HMAX), 0, 1)
        rgba[..., 1] = rub
        rgba[..., 2] = dirt
        img = bpy.data.images.get(name)
        if img:
            bpy.data.images.remove(img)
        img = bpy.data.images.new(name, self.W, self.H, alpha=True)
        img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(rgba.ravel())
        try:
            img.filepath_raw = os.path.join(_here(), "textures", file_name)
            img.file_format = "PNG"
            img.save()
            img.pack()
        except Exception as exc:
            print("Detail sheet not saved to disk:", exc)
        return img


def detail_sheet(side):
    """The rifle's side (side +1 right, -1 left)."""
    pen = _Pen(GUN_WINDOW)
    right = side > 0
    # Receiver: a long stiffening flute pressed into the upper wall, the swage crease where the
    # pressing steps in, and a row of spot welds below it.
    y_a, y_b = (-0.140, -0.018) if right else (-0.140, 0.085)      # right: stops short of the ejection port
    pen.press(pen.rbox((y_a + y_b) / 2, 0.1070, (y_b - y_a) / 2, 0.0028, 0.0028), -0.00045, 0.0016)
    for y_a, y_b in (((-0.1490, 0.0000), (0.0640, 0.1040)) if right else ((-0.1490, 0.1040),)):   # not across the dust cover
        pen.bead(pen.seg((y_a, 0.0936), (y_b, 0.0936)), 0.0011, -0.00028)
    y = -0.1400
    while y < (-0.006 if right else 0.082):
        pen.weld(y, 0.0890)
        y += 0.0220
    # Trigger housing: a bead pressed round a long panel, welds along the top, the selector letter.
    pen.bead(np.abs(pen.rbox(-0.0480, 0.0550, 0.0280, 0.0050, 0.0025)), 0.0013, 0.00035)
    for y in (-0.0450, -0.0300, -0.0150):
        pen.weld(y, 0.0705)
    letter, size = ("D" if right else "E"), 0.0045 / 6.0
    dist = np.full((pen.H, pen.W), 1e9, dtype=np.float32)
    for poly in _SHEET_GLYPHS[letter]:
        pts = [((-0.0815 + gx * size) if right else (-0.0795 - gx * size), 0.0643 + gz * size) for gx, gz in poly]
        for a, b in zip(pts, pts[1:]):
            np.minimum(dist, pen.seg(a, b), out=dist)
    np.add(pen.hm, -0.00016 * pen.ease(1.5 - dist / 0.00030), out=pen.hm)
    # Magazine housing: a sunk panel either side of a pressed bead (left: clear of the catch).
    pen.press(pen.rbox(0.0185, 0.0440, 0.0115, 0.0210, 0.0030) if right else pen.rbox(0.0215, 0.0440, 0.0085, 0.0210, 0.0030),
              -0.00035, 0.0018)
    pen.press(pen.rbox(0.0555, 0.0440, 0.0115, 0.0210, 0.0030), -0.00035, 0.0018)
    pen.bead(pen.seg((0.0370, 0.0230), (0.0370, 0.0650)), 0.0017, 0.00040)
    # Handguard: the stamped shell round the barrel, with its row of cooling holes.
    for k in range(6):
        pen.hole(0.1320 + 0.0180 * k, 0.0945, 0.0026)
    if right:                                                     # dust cover: a rib down its length
        pen.bead(pen.seg((0.0110, 0.0925), (0.0530, 0.0925)), 0.0015, 0.00030)
    return pen.image(PREFIX + "Sheet_" + ("R" if right else "L"), "afstg44_sheet_%s.png" % ("r" if right else "l"))


def magazine_sheet():
    """The magazine's side (both sides alike): two long flutes pressed lengthwise, following the
    curve, as on the real magazine (ribs across the body are the AK's look)."""
    pen = _Pen(MAG_WINDOW)
    oy, oz = MAG_AT[1], MAG_AT[2]
    zw = pen.Z + oz                                              # the rifle's z
    t = (0.0640 - zw) / 0.2140
    centre = 0.0350 + 0.0650 * t * t - oy                        # _mag_centre, in the magazine's frame
    lean = np.sqrt(1.0 + (2.0 * 0.0650 * t / 0.2140) ** 2)       # the curve leans: measure across it
    ends = pen.ease((0.0050 - zw) / 0.0040) * pen.ease((zw + 0.1380) / 0.0040)   # below the housing .. above the floor plate
    for off in (-0.0115, 0.0115):
        dist = np.abs(pen.Y - centre - off) / lean
        np.add(pen.hm, -0.00042 * np.sqrt(np.clip(1.0 - (dist / 0.0024) ** 2, 0.0, 1.0)) * ends, out=pen.hm)
    for zw_weld in (-0.020, -0.060, -0.100):                     # spot welds down the rear spine
        tt = (0.0640 - zw_weld) / 0.2140
        pen.weld(0.0350 + 0.0650 * tt * tt - oy - 0.0235, zw_weld - oz)
    return pen.image(MAG_PREFIX + "Sheet", "afstg44_sheet_mag.png")


def _sheet(P, img, side, window, x_min):
    """Project a detail sheet onto the faces of one side. Returns (dirt, rub, hole) masks."""
    N = P.N
    y0, z0, w, h = window
    u = N.math("DIVIDE", N.math("SUBTRACT", P.py, y0), w)
    v = N.math("DIVIDE", N.math("SUBTRACT", P.pz, z0), h)
    uv = N.new("ShaderNodeCombineXYZ")
    P.nt.links.new(u, uv.inputs[0])
    P.nt.links.new(v, uv.inputs[1])
    tex = N.new("ShaderNodeTexImage", image=img, extension="CLIP", interpolation="Cubic")
    P.nt.links.new(uv.outputs[0], tex.inputs[0])
    sep = N.new("ShaderNodeSeparateColor")
    P.nt.links.new(tex.outputs["Color"], sep.inputs[0])
    gate = N.math("MULTIPLY", N.math("GREATER_THAN", N.math("MULTIPLY", P.px, float(side)), x_min),
                  N.math("GREATER_THAN", N.math("MULTIPLY", P.nx, float(side)), 0.55))
    gate = N.math("MULTIPLY", gate, tex.outputs["Alpha"])
    P.dent(N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", sep.outputs[0], 0.5), 2.0), gate), SHEET_HMAX)
    hole = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.04, sep.outputs[0]), 60.0, clamp=True), gate)
    return N.math("MULTIPLY", sep.outputs[2], gate), N.math("MULTIPLY", sep.outputs[1], gate), hole


# ----------------------------------------------------------------------------
# Finishes. Built the way a texture artist layers a used service rifle: base finish with its own
# mottling, then grime that settles in the corners (ambient occlusion), then wear that goes
# through the finish on edges and high points only, then polish and fine scratches only where
# hands and kit rub. Edge (bevel) and corner (AO) masks only exist in Cycles, i.e. in the bake.
# ----------------------------------------------------------------------------

def _set_metal(P, mask, value):
    sock = P._tap("METAL")
    src = sock.links[0].from_socket
    N = P.N
    P.nt.links.new(N.math("ADD", src, N.math("MULTIPLY", mask, N.math("SUBTRACT", value, src))), sock)


def _edge(P, radius, gain):
    """1 on convex edges (bevel normal against true normal), 0 on flats."""
    N = P.N
    bev = N.new("ShaderNodeBevel", samples=8)
    bev.inputs["Radius"].default_value = radius
    dot = N.new("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    P.nt.links.new(P.geo.outputs["Normal"], dot.inputs[0])
    P.nt.links.new(bev.outputs[0], dot.inputs[1])
    return N.math("MULTIPLY", N.math("SUBTRACT", 1.0, dot.outputs["Value"]), gain, clamp=True)


def _cavity(P, distance):
    """1 deep in corners and crevices, 0 in the open."""
    N = P.N
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.samples = 16
    ao.inputs["Distance"].default_value = distance
    return N.math("MULTIPLY", N.math("SUBTRACT", N.math("SUBTRACT", 1.0, ao.outputs["AO"]), 0.20), 2.0, clamp=True)


def _streaks(P, along, scale, cut):
    """Fine scratches running mostly along one axis (0 = x, 1 = y, 2 = z)."""
    N = P.N
    stretch = [scale, scale, scale]
    stretch[along] = scale / 40.0
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.25, 0.10, 0.15)
    mp.inputs["Scale"].default_value = stretch
    P.nt.links.new(P.geo.outputs["Position"], mp.inputs["Vector"])
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.0
    n.inputs["Detail"].default_value = 1.0
    P.nt.links.new(mp.outputs[0], n.inputs["Vector"])
    return N.math("MULTIPLY", N.math("SUBTRACT", n.outputs[0], cut), 14.0, clamp=True)


def _wipe(P, along, scale):
    """Soft streaks along one axis, 0..1 around 0.5: wipe marks, seen only in the gloss."""
    N = P.N
    stretch = [scale, scale, scale]
    stretch[along] = scale / 14.0
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.05, 0.03, 0.08)
    mp.inputs["Scale"].default_value = stretch
    P.nt.links.new(P.geo.outputs["Position"], mp.inputs["Vector"])
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.0
    n.inputs["Detail"].default_value = 2.0
    P.nt.links.new(mp.outputs[0], n.inputs["Vector"])
    return n.outputs[0]


# Where the rifle is handled, carried and knocked (centre, half sizes, strength), in the working frame.
# A professional finish places its wear by use, not by noise: the thumb on the selector and the
# magazine catch, the hand on the cocking handle, magazines going into the housing, the sling at its
# loops, the support hand under the handguard, clothing against the left side when slung on the back.
RIFLE_ZONES = (
    ((-0.0190, -0.1060, 0.0690), (0.0070, 0.0170, 0.0110), 1.00),   # selector lever: the thumb
    ((0.0220, 0.0750, 0.1210), (0.0090, 0.0180, 0.0110), 1.00),     # cocking handle and the slot behind it
    ((-0.0210, 0.0050, 0.0560), (0.0060, 0.0110, 0.0110), 0.90),    # magazine catch: the thumb
    ((0.0000, 0.0370, 0.0120), (0.0240, 0.0450, 0.0100), 0.80),     # mouth of the magazine housing
    ((0.0000, -0.0580, 0.0290), (0.0110, 0.0320, 0.0070), 0.90),    # bottom of the trigger guard
    ((-0.0175, 0.3510, 0.0936), (0.0120, 0.0150, 0.0130), 1.00),    # front sling loop: the sling
    ((-0.0190, -0.3300, 0.0800), (0.0070, 0.0280, 0.0150), 1.00),   # rear sling plate
    ((0.0000, 0.1750, 0.0800), (0.0200, 0.0700, 0.0120), 0.70),     # under the handguard: the support hand
    ((-0.0200, -0.0500, 0.1100), (0.0070, 0.0900, 0.0300), 0.35),   # left of the receiver: slung, against clothing
    ((0.0000, 0.4350, 0.1500), (0.0150, 0.0130, 0.0170), 0.80),     # front sight hood: snags on everything
)
MAG_ZONES = (
    ((0.0000, 0.0300, 0.0330), (0.0170, 0.0450, 0.0090), 1.00),     # feed lips: rounds and the magazine well
    ((0.0000, 0.0650, -0.1810), (0.0170, 0.0360, 0.0070), 1.00),    # floor plate: dropped, stood on its end
    ((0.0000, 0.0400, -0.0800), (0.0170, 0.0600, 0.0450), 0.30),    # the body: hands and pouches
)
SCOPE_ZONES = (
    ((0.0000, -0.0900, 0.0000), (0.0170, 0.0080, 0.0170), 0.80),    # eyepiece rim
    ((0.0000, 0.0850, 0.0000), (0.0170, 0.0060, 0.0170), 0.80),     # objective rim
    ((0.0000, 0.0010, 0.0260), (0.0100, 0.0100, 0.0050), 0.80),     # elevation drum: the fingers
)


def _spot(P, centre, half):
    """Soft ellipsoid: 1 at `centre`, fading to 0 at `half` (half sizes along x, y, z)."""
    N = P.N
    d = None
    for sock, c, h in zip((P.px, P.py, P.pz), centre, half):
        t = N.math("DIVIDE", N.math("SUBTRACT", sock, c), h)
        t = N.math("MULTIPLY", t, t)
        d = t if d is None else N.math("ADD", d, t)
    f = N.math("SUBTRACT", 1.0, d, clamp=True)
    return N.math("MULTIPLY", f, f)


def _phosphate(mat, muzzle_y, carried=True, sheets=(), zones=()):
    """Wartime phosphate (parkerized) finish on stamped and machined steel: matte grey-black with a
    faint green cast and cloudy mottling. Grime and a little rust in the corners, bare bright steel
    on worn edges, polish and scratches where it is handled, soot at the muzzle.
    carried=False (magazine, scope): no handling zones."""
    P = m41._Post(mat)
    N = P.N
    # 1. Mottled finish: cloudy lighter and darker patches, as a dipped coating comes out.
    cloud = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(7.0, 4.0), 0.42), 2.6, clamp=True)
    P.color(N.math("MULTIPLY", cloud, 0.85), (0.040, 0.041, 0.037))
    blot = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(32.0, 3.0), 0.56), 4.0, clamp=True)
    P.color(N.math("MULTIPLY", blot, 0.70), (0.0080, 0.0085, 0.0090))
    oily = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(9.0, 2.0), 0.50), 5.0, clamp=True)
    P.color(N.math("MULTIPLY", oily, 0.55), (0.0070, 0.0075, 0.0080))
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", cloud, 0.5), 0.10))
    # Gloss breakup, in the gloss only: oily patches and the long wipe marks of a rag. Flat, even
    # gloss is what makes a surface look computer-made in sunlight (the vanilla AKM's gloss map
    # varies about a third more than the first finish pass did).
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", P.noise(11.0, 3.0), 0.5), 0.85))
    P.rough(N.math("MULTIPLY", N.math("SUBTRACT", _wipe(P, 1, 55.0), 0.5), 0.42))
    # 2. Grime in the corners: dull brown-grey, rougher; a few rust specks deep in them.
    cav = _cavity(P, 0.010)
    grime = N.math("MULTIPLY", cav, N.math("ADD", 0.55, N.math("MULTIPLY", P.noise(60.0, 3.0), 0.6)), clamp=True)
    P.color(N.math("MULTIPLY", grime, 0.70), (0.022, 0.017, 0.012))
    P.rough(N.math("MULTIPLY", grime, 0.14))
    rust = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.12, P.cells(380.0)), 18.0, clamp=True), cav)
    P.color(N.math("MULTIPLY", rust, 0.85), (0.095, 0.040, 0.016))
    P.rough(N.math("MULTIPLY", rust, 0.25))
    P.dent(N.math("MULTIPLY", rust, -1.0), 0.00010)
    # Dry dust caught in the same corners, in patches: lighter than the finish, which is what lets a
    # dark gun show its shapes.
    dusty = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(19.0, 4.0), 0.48), 4.0, clamp=True)
    DUST = (0.060, 0.052, 0.042)
    # Bare steel: told by its shine (metal -> the specular map), not by a white line in the colour.
    BARE = (0.22, 0.22, 0.225)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", cav, dusty), 0.22), DUST)
    chip = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(48.0, 6.0), 0.40), 3.5, clamp=True)
    # Where the rifle is exposed to knocks and rubbing: a broad noise picks the worn stretches; on
    # the rifle itself the ends that always catch it are added by position (muzzle, butt plate,
    # mouth of the magazine housing).
    lt = lambda a, b: N.math("LESS_THAN", a, b)
    gt = lambda a, b: N.math("GREATER_THAN", a, b)
    exposed = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(5.0, 2.0), 0.36), 3.2, clamp=True)
    if carried:
        mouth = N.math("MULTIPLY", N.math("MULTIPLY", lt(P.pz, 0.020), gt(P.pz, 0.008)),
                       N.math("MULTIPLY", gt(P.py, 0.0), lt(P.py, 0.075)))
        exposed = N.math("MAXIMUM", exposed, N.math("MAXIMUM", N.math("MAXIMUM", gt(P.py, muzzle_y - 0.050), lt(P.py, -0.395)), mouth))
    # Use: the zones where hands, kit and the sling work the finish (RIFLE_ZONES etc.).
    handled = None
    for centre, half, k in zones:
        z = N.math("MULTIPLY", _spot(P, centre, tuple(h * 0.6 for h in half)), k)
        handled = z if handled is None else N.math("MAXIMUM", handled, z)
    if handled is not None:
        exposed = N.math("MAXIMUM", exposed, handled)
    # 2b. The pressed detail: dirt and dust in the pressings, finish rubbed off their rims.
    holes = []
    for img, side, window, x_min in sheets:
        dirt, rub, hole = _sheet(P, img, side, window, x_min)
        P.color(N.math("MULTIPLY", dirt, 0.60), (0.022, 0.017, 0.012))
        P.color(N.math("MULTIPLY", N.math("MULTIPLY", dirt, dusty), 0.30), DUST)
        P.rough(N.math("MULTIPLY", dirt, 0.14))
        P.color(N.math("MULTIPLY", N.math("MULTIPLY", rub, chip), 0.55), (0.050, 0.050, 0.049))
        worn = N.math("MULTIPLY", N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", rub, 0.35), 2.2, clamp=True), chip),
                      N.math("ADD", 0.25, N.math("MULTIPLY", exposed, 0.75)))
        P.color(N.math("MULTIPLY", worn, 0.8), BARE)
        P.rough(N.math("MULTIPLY", worn, -0.25))
        _set_metal(P, worn, 1.0)
        holes.append(hole)
    if carried:
        # 2c. Direction: the top of the rifle is handled and wiped (a little lighter and glossier),
        #     oil runs down and gathers along the bottom of the receiver and its seams (darker, glossy).
        sep = N.new("ShaderNodeSeparateXYZ")
        P.nt.links.new(P.geo.outputs["Normal"], sep.inputs[0])
        up = N.math("MULTIPLY", N.math("SUBTRACT", sep.outputs["Z"], 0.45), 2.5, clamp=True)
        broad = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(9.0, 2.0), 0.25), 2.0, clamp=True)
        top = N.math("MULTIPLY", up, broad)
        P.color(N.math("MULTIPLY", top, 0.22), (0.034, 0.034, 0.033))
        P.rough(N.math("MULTIPLY", top, -0.10))
        low = N.math("MULTIPLY", P.band(P.pz, 0.0930, 0.0120), lt(P.py, 0.105))
        oil = N.math("MULTIPLY", N.math("MAXIMUM", low, N.math("MULTIPLY", cav, 0.6)),
                     N.math("MULTIPLY", N.math("SUBTRACT", P.noise(7.0, 3.0), 0.30), 2.2, clamp=True))
        P.color(N.math("MULTIPLY", oil, 0.40), (0.0060, 0.0062, 0.0060))
        P.rough(N.math("MULTIPLY", oil, -0.16))
    # 3. Edge wear: finish rubbed thin round the edges, through to bright steel on the sharpest,
    #    broken up so it chips rather than running as a clean line.
    #    Not every edge: only where the rifle is exposed to knocks and rubbing. A broad noise picks
    #    the worn stretches, and the ends and corners that always catch it are added by position
    #    (muzzle, butt plate, mouth of the magazine housing).
    flake = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(48.0, 6.0), 0.30), 3.0, clamp=True)
    soft = N.math("MULTIPLY", N.math("MULTIPLY", _edge(P, 0.0024, 4.0), flake),
                  N.math("ADD", 0.45, N.math("MULTIPLY", exposed, 0.55)))
    P.color(N.math("MULTIPLY", soft, 0.70), (0.070, 0.069, 0.066))
    P.rough(N.math("MULTIPLY", soft, -0.10))
    bare = N.math("MULTIPLY", N.math("MULTIPLY", N.math("MULTIPLY", _edge(P, 0.0012, 9.0), flake), 1.0, clamp=True),
                  N.math("ADD", 0.25, N.math("MULTIPLY", exposed, 0.75)))
    P.color(bare, BARE)
    P.rough(N.math("MULTIPLY", bare, -0.30))
    _set_metal(P, bare, 1.0)
    if carried:
        # 4. Handling: grip straps, handguard, front of the magazine housing, cocking handle.
        grip = N.math("MULTIPLY", P.band(P.py, -0.125, 0.040), lt(P.pz, 0.072))
        guard = N.math("MULTIPLY", P.band(P.py, 0.175, 0.085), lt(P.pz, BORE + 0.004))
        well = N.math("MULTIPLY", N.math("MULTIPLY", gt(P.py, 0.060), lt(P.py, 0.078)), lt(P.pz, 0.078))
        cock = N.math("MULTIPLY", P.band(P.py, 0.075, 0.020), gt(P.px, 0.020))
        zone = N.math("MAXIMUM", N.math("MAXIMUM", grip, guard), N.math("MAXIMUM", well, cock))
        P.color(N.math("MULTIPLY", zone, 0.30), (0.034, 0.034, 0.033))
        P.rough(N.math("MULTIPLY", zone, -0.14))
        scr = N.math("MULTIPLY", N.math("MAXIMUM", _streaks(P, 1, 260.0, 0.70), _streaks(P, 2, 300.0, 0.72)), zone)
        P.color(N.math("MULTIPLY", scr, 0.40), (0.14, 0.14, 0.145))
        P.rough(N.math("MULTIPLY", scr, -0.12))
        P.dent(N.math("MULTIPLY", scr, -0.6), 0.00006)
    if handled is not None:
        # 4b. Use wear on the flats of the handled zones: the finish polished thin (a dark, oily
        #     sheen with steel showing through, i.e. part metal), broken up so it is never a clean
        #     disc, and scratches that run the way the hand or the sling moves.
        patchy = N.math("MULTIPLY", N.math("SUBTRACT", P.noise(26.0, 5.0), 0.30), 2.5, clamp=True)
        convex = _edge(P, 0.0040, 2.5)
        polish = N.math("MULTIPLY", N.math("MULTIPLY", handled, patchy), convex)
        P.rough(N.math("MULTIPLY", polish, -0.22))
        # Scratches only towards the middle of a zone (handled squared), few and long: a scatter.
        used = N.math("MULTIPLY", N.math("MAXIMUM", _streaks(P, 1, 120.0, 0.76), _streaks(P, 2, 130.0, 0.78)),
                      N.math("MULTIPLY", handled, handled))
        P.color(N.math("MULTIPLY", used, 0.30), BARE)
        P.rough(N.math("MULTIPLY", used, -0.20))
        _set_metal(P, N.math("MULTIPLY", used, 0.8), 1.0)
        P.dent(N.math("MULTIPLY", used, -0.8), 0.00005)
    # 5. A few long scratches anywhere, very faint (kit and slings), and soot at the muzzle.
    stray = N.math("MULTIPLY", _streaks(P, 1, 90.0, 0.78), 0.35)
    P.color(stray, (0.10, 0.10, 0.104))
    soot = N.math("MULTIPLY", P.band(P.py, muzzle_y, 0.030), 0.75)
    P.color(soot, (0.007, 0.0065, 0.006))
    P.rough(N.math("MULTIPLY", soot, 0.12))
    for hole in holes:           # holes last of all: the dark inside of the shell, under no other layer
        P.color(hole, (0.002, 0.002, 0.002))
        P.rough(N.math("MULTIPLY", hole, 0.40))
        _set_metal(P, hole, 0.0)
    return P


def _stock_wood(mat):
    """Oiled beech: darker and smoother where the cheek and hands rest, dents with dirt in them,
    edges rubbed back to lighter wood, grime in the corners. Kept off the gold floral skin."""
    P = m41._Post(mat)
    N = P.N
    plain = P.plain
    for scale, depth, gloss in ((420.0, 0.00010, 0.16), (1500.0, 0.00005, 0.08)):      # open grain, then pores
        grain = N.math("SUBTRACT", _wipe(P, 1, scale), 0.5)
        P.dent(N.math("MULTIPLY", grain, plain), depth)
        P.rough(N.math("MULTIPLY", N.math("MULTIPLY", grain, gloss), plain))
    # Beech's own figure: broad growth bands along the stock, and the ray flecks that mark beech out
    # from every other gunstock wood: small lens-shaped flecks, a little darker and denser, with their
    # own sheen (they catch the light differently from the grain round them).
    bands = N.math("MULTIPLY", N.math("SUBTRACT", _wipe(P, 1, 38.0), 0.5), 2.0)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", N.math("MAXIMUM", bands, 0.0), 0.55), plain), (0.050, 0.024, 0.014))
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", N.math("MAXIMUM", N.math("MULTIPLY", bands, -1.0), 0.0), 0.35), plain),
            (0.140, 0.074, 0.044))
    fleck = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.10, P.cells(520.0, (1.0, 0.22, 1.0))), 16.0, clamp=True),
                   N.math("MULTIPLY", N.math("SUBTRACT", P.noise(14.0, 2.0), 0.35), 3.0, clamp=True))
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", fleck, 0.65), plain), (0.062, 0.029, 0.016))
    P.rough(N.math("MULTIPLY", N.math("MULTIPLY", fleck, -0.18), plain))
    P.dent(N.math("MULTIPLY", fleck, 0.6), 0.00004)
    # Use: fine scratches across the grain on the sides (kit, the ground), lighter where they cut the oil.
    across = N.math("MULTIPLY", N.math("MAXIMUM", _streaks(P, 2, 160.0, 0.80), _streaks(P, 0, 180.0, 0.82)), plain)
    P.color(N.math("MULTIPLY", across, 0.12), (0.20, 0.11, 0.060))
    P.rough(N.math("MULTIPLY", across, 0.06))
    P.dent(N.math("MULTIPLY", across, -0.7), 0.00005)
    held = N.math("MULTIPLY", N.math("MAXIMUM", P.band(P.py, -0.19, 0.07), P.band(P.py, -0.125, 0.040)),
                  N.math("ADD", 0.45, N.math("MULTIPLY", P.noise(28.0, 4.0), 0.9)), clamp=True)
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", held, 0.45), plain), (0.030, 0.011, 0.005))
    P.rough(N.math("MULTIPLY", held, -0.14))
    ding = N.math("MULTIPLY", N.math("MULTIPLY", N.math("SUBTRACT", 0.085, P.cells(70.0, (1.0, 0.4, 1.0))), 14.0, clamp=True),
                  N.math("MULTIPLY", N.math("SUBTRACT", P.noise(9.0, 2.0), 0.45), 6.0, clamp=True))
    P.color(N.math("MULTIPLY", N.math("MULTIPLY", ding, 0.55), plain), (0.020, 0.008, 0.004))
    P.rough(N.math("MULTIPLY", ding, 0.10))
    P.dent(N.math("MULTIPLY", ding, -1.0), 0.0003)
    rub = N.math("MULTIPLY", N.math("MULTIPLY", _edge(P, 0.0025, 3.0),
                                    N.math("MULTIPLY", N.math("SUBTRACT", P.noise(30.0, 5.0), 0.35), 3.0, clamp=True)), plain)
    P.color(N.math("MULTIPLY", rub, 0.55), (0.25, 0.13, 0.060))
    P.rough(N.math("MULTIPLY", rub, 0.08))
    grime = N.math("MULTIPLY", _cavity(P, 0.012), plain)
    P.color(N.math("MULTIPLY", grime, 0.6), (0.030, 0.018, 0.010))
    return P


def _rake(bm, top=(-0.1140, 0.0580), axis=(-0.0220, -0.0970)):
    """Turn a part built along +Y (down the grip; +Z = forward) onto the grip line: local +Y runs
    from `top` along `axis` (down and back, the AKM's 77 degrees), local +Z points forward."""
    theta = math.atan2(axis[1], axis[0])
    c, s_ = math.cos(theta), math.sin(theta)
    for v in bm.verts:
        x, y, z = v.co
        v.co = (x, top[0] + y * c - z * s_, top[1] + y * s_ + z * c)


def _rivet(bm, y, z, side, face_x, r):
    """Domed rivet head on a side face at |x| = face_x."""
    prof = [(face_x - 0.0004, 0.0), (face_x - 0.0004, r), (face_x + 0.0003, r * 0.92), (face_x + 0.0008, r * 0.62),
            (face_x + 0.0010, 0.0)]
    if side < 0:
        prof = [(-x, rr) for x, rr in prof][::-1]
    d.bm_lathe(bm, prof, sides=10, axis="X", c=(y, z))


def _arc(centre, radius, a0, a1, steps):
    return [(centre[0] + radius * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             centre[1] + radius * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]


# 7.62x39 display round: (distance from the case head, radius)
ROUND_CASE = [(0.0, 0.0), (0.0, 0.00565), (0.0300, 0.0050), (0.0325, 0.0043), (0.0385, 0.0043), (0.0385, 0.0038)]
ROUND_SLUG = [(0.0385, 0.0039), (0.0470, 0.0037), (0.0530, 0.0022), (0.0560, 0.0)]


# ----------------------------------------------------------------------------
# Build: the rifle
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

    # Phosphate is a matte, slightly green-grey coating, not polished steel: rougher and less
    # metallic than blueing. Wear, grime and scratches are layered on by _phosphate().
    # Levels set against the vanilla AKM's maps (measured 2026-11-22: colour median 0.106, gloss 0.61,
    # specular 0.12): the first finish pass was 2.8 times too light and too dull in game sunlight.
    m_steel = d.material("Steel", (0.0135, 0.0142, 0.0135), rough=0.40, metal=0.35, bump=0.03, bump_scale=1100,
                         rough_var=0.06, machining=0.02)
    m_bolt = d.material("BoltSteel", (0.30, 0.30, 0.31), rough=0.32, metal=1.0, rough_var=0.08,
                        wear_rgb=(0.50, 0.50, 0.51), scratches=0.20, machining=0.28)
    # Oiled wartime beech: a deeper red-brown than raw beech.
    m_wood = m41.woodify(d.material("Beech", (0.091, 0.048, 0.031), rough=0.50, metal=0.0, bump=0.05, bump_scale=950,
                                    rough_var=0.14, scratches=0.08, skin_img=d.pattern_image()),
                         dark=(0.040, 0.020, 0.013), light=(0.114, 0.059, 0.036))
    steel = _phosphate(m_steel, MUZZLE_Y, zones=RIFLE_ZONES, sheets=[(detail_sheet(1), 1, GUN_WINDOW, 0.010),
                                                  (detail_sheet(-1), -1, GUN_WINDOW, 0.010)])
    _stock_wood(m_wood)
    # Struck letters are the finish's own colour; they read by their depth, and by the dust in them.
    lettering = (0.045, 0.040, 0.034)
    img, asp = m41.stamp_image("StgModel", ["AF STG 44"])
    steel.stamp(img, asp, -0.0550, 0.0050, -1, 0.0810, rgb=lettering, strength=0.5, depth=0.00035)
    img, asp = m41.stamp_image("StgSerial", ["No 5830"])
    steel.stamp(img, asp, 0.0500, 0.0046, -1, 0.0796, rgb=lettering, strength=0.5, depth=0.00035)
    # Scratched by hand on the right of the receiver, behind the ejection port: bright bare steel.
    img, asp = scratch_image("Legacy", "legacy was here")
    steel.stamp(img, asp, -0.1300, 0.0062, 1, 0.0790, rgb=(0.46, 0.46, 0.48), strength=0.85, depth=0.00012)

    # --- Receiver (stamped upper) ------------------------------------------------------------------
    # The real upper is one pressing: a round top over flat sides, with the sides stepped in along
    # their lower third (the swage line), and a rolled lower edge where the trigger housing meets it.
    top = _arc((0.0, TOP_Z), R_TOP, 0.0, 180.0, 12)
    right = [(0.0168, 0.0750), (0.0178, 0.0762), (0.0178, 0.0915), (0.0186, 0.0932), (R_TOP, 0.0952)]
    left = [(-x, z) for x, z in right[::-1]]
    bm = bmesh.new()
    d.bm_xsec(bm, right + top + left, -0.1500, 0.1050)
    recv = d.make("Receiver", bm, body, m_steel, "Stamped receiver. Open: ejection port (right), cocking slot (right).", bevel=0.0010)
    for nm, centre, size in (("Port", (R_TOP, 0.0320, BORE + 0.0090), (0.0200, 0.0560, 0.0180)),
                             ("Slot", (R_TOP, 0.0550, TOP_Z + 0.0020), (0.0140, 0.1250, 0.0075))):
        c = d.box("Receiver_%sCutter" % nm, cutters, None, centre, size, bevel=0, note="Boolean cutter.")
        d.cut(recv, c, nm)
    # Rear end cap of the receiver and the steel collar the stock is pinned into.
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.1730, 0.0), (-0.1730, 0.0160), (-0.1715, 0.0182), (-0.1600, 0.0190), (-0.1585, 0.0204),
                    (-0.1530, 0.0206), (-0.1515, 0.0198), (-0.1500, 0.0198), (-0.1500, 0.0)], sides=28, c=(0.0, TOP_Z - 0.0030))
    d.make("StockFerrule", bm, body, m_steel, "End cap of the receiver and the stock collar.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0218, 0.0), (-0.0218, 0.0030), (-0.0208, 0.0034), (0.0208, 0.0034), (0.0218, 0.0030), (0.0218, 0.0)],
               sides=14, axis="X", c=(-0.1640, TOP_Z - 0.0090))
    d.make("StockPin", bm, body, m_steel, "Push pin holding the stock collar to the receiver.")
    # Domed rivets along the receiver sides (the pressing is riveted to its inner rails).
    bm = bmesh.new()
    for y in (-0.1250, 0.0950):
        for side in (-1, 1):
            _rivet(bm, y, TOP_Z - 0.0020, side, R_TOP, 0.0014)
    d.make("Rivets", bm, body, m_steel, "Domed rivets on the receiver sides.")
    d.box("DustCover", body, m_steel, (0.0196, 0.0320, BORE - 0.0050), (0.0014, 0.0580, 0.0110), bevel=0.0005,
          note="Ejection port dust cover, sprung open.")

    # --- Bolt carrier and cocking handle (bone 'bolt') -------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0600, 0.0), (-0.0600, 0.0150), (0.0900, 0.0150), (0.0920, 0.0130), (0.0920, 0.0)], sides=24,
               c=(0.0, BORE + 0.0090))
    d.make("BoltCarrier", bm, moving, m_bolt, "Bolt carrier, seen through the ejection port. Bone 'bolt'.")
    bm = bmesh.new()
    d.bm_box(bm, (0.0205, 0.0750, TOP_Z + 0.0020), (0.0120, 0.0080, 0.0058))
    d.bm_lathe(bm, [(0.0255, 0.0040), (0.0275, 0.0062), (0.0370, 0.0062), (0.0390, 0.0044), (0.0390, 0.0)], sides=16, axis="X",
               c=(0.0750, TOP_Z + 0.0020))
    d.make("CockingHandle", bm, moving, m_steel, "Cocking handle on the right. Bone 'bolt'.", bevel=0.0005)

    # --- Trigger housing, grip, trigger ----------------------------------------------------------
    d.profile("TriggerHousing", body, m_steel,
              [(-0.1500, 0.0760), (0.0020, 0.0760), (0.0020, 0.0480), (-0.0300, 0.0440), (-0.0840, 0.0440), (-0.0900, 0.0560),
               (-0.1450, 0.0560), (-0.1500, 0.0620)], width=0.0300, bevel=0.0012, round=0.0030,
              note="Trigger housing under the receiver.")
    # Thin overlays (this lip, the magazine housing's rib and beads) are built only at the finer detail
    # levels: in the far LODs they would collapse into stray triangles.
    fine = d.EDGE_SEGMENTS >= 1
    if fine:
        bm = bmesh.new()
        for side in (-1, 1):       # rolled lip where the trigger housing closes against the receiver
            d.bm_box(bm, (side * 0.0158, -0.0740, 0.0748), (0.0016, 0.1520, 0.0030))
        d.make("HousingLip", bm, body, m_steel, "Rolled upper lip of the trigger housing.", bevel=0.0006)

    # Pistol grip: built along its own raked axis (top centre (y -0.114, z 0.058), 77 degrees down
    # and back, the AKM's grip line), then turned into place. Steel straps front and back, wooden
    # panels proud of the sides, one screw through both panels.
    def grip_part(name, mat, sections, power, note):
        bm = bmesh.new()
        m41.bm_loft(bm, sections, sides=32, power=power)
        _rake(bm)
        return d.make(name, bm, body, mat, note, 0.0, sharp=50.0)
    grip_part("GripFrame", m_steel,
              [(0.000, -0.0245, 0.0225, 0.0118), (0.012, -0.0205, 0.0195, 0.0122), (0.036, -0.0192, 0.0182, 0.0126),
               (0.062, -0.0186, 0.0176, 0.0124), (0.088, -0.0182, 0.0174, 0.0120), (0.0975, -0.0172, 0.0164, 0.0112),
               (0.1000, -0.0158, 0.0150, 0.0096)], 2.4, "Steel grip frame: front and back straps and the grip cap.")
    grip_part("GripPanels", m_wood,
                       [(0.006, -0.0170, 0.0150, 0.0128), (0.014, -0.0172, 0.0158, 0.0146), (0.036, -0.0166, 0.0152, 0.0154),
                        (0.062, -0.0160, 0.0148, 0.0152), (0.084, -0.0156, 0.0146, 0.0146), (0.090, -0.0150, 0.0140, 0.0130)],
                       3.2, "Wooden grip panels.")
    bm = bmesh.new()
    for side in (-1, 1):
        prof = [(0.0140, 0.0), (0.0140, 0.0034), (0.0158, 0.0034), (0.0162, 0.0028), (0.0162, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        d.bm_lathe(bm, prof, sides=12, axis="X", c=(0.047, -0.0008))
        d.bm_box(bm, (side * 0.0162, 0.047, -0.0008), (0.0005, 0.0050, 0.0009))
    _rake(bm)
    d.make("GripScrew", bm, body, m_steel, "Grip screw through both panels.")
    outer = [(-0.0850, 0.0450), (-0.0850, 0.0330), (-0.0800, 0.0285), (-0.0400, 0.0285), (-0.0320, 0.0340), (-0.0300, 0.0450)]
    inner = [(-0.0325, 0.0450), (-0.0345, 0.0350), (-0.0410, 0.0310), (-0.0790, 0.0310), (-0.0825, 0.0340), (-0.0825, 0.0450)]
    d.profile("TriggerGuard", body, m_steel, d.fillet(outer, 0.0030) + d.fillet(inner, 0.0025)[::1], width=0.0120,
              bevel=0.0010, segments=3, note="Trigger guard.")
    d.blade("Weapon_Trigger", moving, m_steel,
            [(-0.0720, 0.0690, 0.0080), (-0.0745, 0.0580, 0.0066), (-0.0750, 0.0480, 0.0054), (-0.0725, 0.0400, 0.0046),
             (-0.0685, 0.0350, 0.0038)], width=0.0062,
            note="Trigger: a curved, rounded blade. Bone 'trigger'; pivot at (y -0.072, z 0.0672).")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0152, 0.0050), (-0.0172, 0.0050), (-0.0180, 0.0040), (-0.0180, 0.0)], sides=16, axis="X", c=(-0.1100, 0.0680))
    d.bm_box(bm, (-0.0172, -0.1020, 0.0700), (0.0018, 0.0190, 0.0040), rot=(12.0, 0, 0))
    d.make("Selector", bm, body, m_steel, "Safety lever, left, above the grip.", bevel=0.0004)
    # Fire selector: a cross-bolt pushed through the housing from side to side, above the grip.
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0196, 0.0), (-0.0196, 0.0030), (-0.0188, 0.0040), (0.0188, 0.0040), (0.0196, 0.0030), (0.0196, 0.0)],
               sides=16, axis="X", c=(-0.0880, 0.0660))
    d.make("SelectorBolt", bm, body, m_steel, "Fire selector cross-bolt, pushed through from either side.")
    for nm, y, z, r in (("HingePin", -0.0050, 0.0560, 0.0030), ("SearPin", -0.0600, 0.0640, 0.0022)):
        bm = bmesh.new()
        d.bm_lathe(bm, [(-0.0156, 0.0), (-0.0156, r), (0.0156, r), (0.0156, 0.0)], sides=12, axis="X", c=(y, z))
        d.make(nm, bm, body, m_steel, "Cross pin through the trigger housing.")

    # --- Magazine well ------------------------------------------------------------------------------
    # The StG's long magazine housing reaches well below the receiver.
    well = d.box("MagWellCutter", cutters, None, (0.0, 0.0370, 0.0400), (0.0270, 0.0640, 0.0900), bevel=0,
                 note="Boolean cutter: magazine well.")
    housing = d.box("MagWell", body, m_steel, (0.0, 0.0370, 0.0450), (0.0340, 0.0720, 0.0640), bevel=0.0018,
                    note="Long magazine housing in front of the trigger guard.")
    d.cut(housing, well, "MagWell")
    bm = bmesh.new()
    d.bm_lathe(bm, [(-0.0170, 0.0050), (-0.0200, 0.0050), (-0.0212, 0.0040), (-0.0212, 0.0)], sides=16, axis="X", c=(0.0050, 0.0560))
    d.make("MagCatch", bm, body, m_steel, "Magazine catch button, left.")
    bm = bmesh.new()
    d.bm_box(bm, (0.0, 0.0370, 0.0145), (0.0376, 0.0756, 0.0030))        # flared lip round the mouth
    if fine:
        d.bm_box(bm, (0.0, 0.0735, 0.0450), (0.0120, 0.0030, 0.0600))    # stiffening rib down the front
    d.make("MagWellDetail", bm, body, m_steel, "Magazine housing: flared mouth, front rib.", bevel=0.0006)

    # --- Stock ----------------------------------------------------------------------------------------
    # The stock comes out of the collar at the collar's own size; its top carries the receiver's line
    # straight back and its belly runs in one straight line down to the toe. Slim, with flat-ish sides
    # and well rounded top and bottom.
    m41.loft("Stock", body, m_wood,
             [(-0.1520, 0.0700, 0.1350, 0.0160), (-0.1650, 0.0673, 0.1350, 0.0162), (-0.1900, 0.0620, 0.1344, 0.0166),
              (-0.2300, 0.0536, 0.1332, 0.0172), (-0.2800, 0.0432, 0.1316, 0.0178), (-0.3350, 0.0316, 0.1296, 0.0183),
              (-0.3800, 0.0222, 0.1278, 0.0185), (-0.4000, 0.0180, 0.1268, 0.0184)], power=2.15,
             note="Wooden stock. Sections are (y, bottom, top, half width).")
    m41.loft("ButtPlate", body, m_steel,
             [(-0.4000, 0.0170, 0.1276, 0.0189), (-0.4040, 0.0175, 0.1271, 0.0187), (-0.4060, 0.0200, 0.1246, 0.0175)],
             power=2.3, note="Steel butt plate.")
    # Trap door in the butt plate (cleaning kit), its hinge pin, and the two plate screws.
    bm = bmesh.new()
    d.bm_box(bm, (0.0, -0.4064, 0.0700), (0.0180, 0.0008, 0.0440))
    d.bm_lathe(bm, [(-0.0100, 0.0), (-0.0100, 0.0016), (0.0100, 0.0016), (0.0100, 0.0)], sides=10, axis="X", c=(-0.4064, 0.0930))
    for z in (0.0320, 0.1130):
        d.bm_lathe(bm, [(-0.4060, 0.0), (-0.4060, 0.0030), (-0.4066, 0.0026), (-0.4069, 0.0)], sides=12, axis="Y", c=(0.0, z))
    d.make("ButtTrap", bm, body, m_steel, "Butt plate trap door with its hinge, and the plate screws.", bevel=0.0003)
    bm = bmesh.new()
    m41.bm_torus(bm, (-0.0228, -0.3300, 0.0800), 0.0075, 0.0016, seg=16, sides=8)
    d.make("SlingLoopRear", bm, body, m_steel, "Rear sling loop on the left of the stock.")
    bm = bmesh.new()
    d.bm_box(bm, (-0.0187, -0.3300, 0.0800), (0.0014, 0.0300, 0.0110))
    for y in (-0.3420, -0.3180):
        d.bm_lathe(bm, [(-0.0194, 0.0), (-0.0194, 0.0018), (-0.0199, 0.0012), (-0.0201, 0.0)], sides=10, axis="X", c=(y, 0.0800))
    d.bm_box(bm, (-0.0199, -0.3300, 0.0800), (0.0020, 0.0060, 0.0040))
    d.make("SlingPlateRear", bm, body, m_steel, "Base plate of the rear sling loop, screwed to the stock.", bevel=0.0004)

    # --- Barrel, gas system, handguard ------------------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.1000, 0.0), (0.1000, 0.0105), (0.1200, 0.0092), (0.3300, 0.0080), (MUZZLE_Y - 0.0180, 0.0076),
                    (MUZZLE_Y - 0.0180, 0.0)], sides=24, c=(0.0, BORE))
    d.make("Barrel", bm, body, m_steel, "Barrel.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(MUZZLE_Y - 0.0180, 0.0040), (MUZZLE_Y - 0.0180, 0.0098), (MUZZLE_Y - 0.0020, 0.0098), (MUZZLE_Y, 0.0088),
                    (MUZZLE_Y, 0.0040)], sides=24, c=(0.0, BORE), closed=True, cap=False)
    for k in range(4):
        d.bm_lathe(bm, [(MUZZLE_Y - 0.0160 + 0.0032 * k, 0.0101), (MUZZLE_Y - 0.0146 + 0.0032 * k, 0.0101)], sides=24,
                   c=(0.0, BORE), cap=False)
    d.make("MuzzleNut", bm, body, m_steel, "Muzzle nut. Selection 'hide_barrel': hidden while a suppressor is fitted.")
    # As on the real rifle the gas cylinder lies bare on top of the barrel, from the receiver to the
    # gas block two thirds of the way along; the barrel runs on alone to the front sight.
    gz = BORE + 0.0180
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.1050, 0.0), (0.1050, 0.0095), (0.3380, 0.0095), (0.3380, 0.0)], sides=24, c=(0.0, gz))
    d.make("GasTube", bm, body, m_steel, "Gas cylinder lying on top of the barrel.")
    # Gas block: two rings, round the barrel and round the cylinder, joined by a web (a figure of
    # eight seen from the front), then the gas plug with its four spanner notches.
    bm = bmesh.new()
    for zc in (BORE, gz):
        d.bm_lathe(bm, [(0.3360, 0.0), (0.3360, 0.0098), (0.3375, 0.0112), (0.3645, 0.0112), (0.3660, 0.0098), (0.3660, 0.0)],
                   sides=28, c=(0.0, zc))
    d.bm_box(bm, (0.0, 0.3510, (BORE + gz) / 2), (0.0180, 0.0290, gz - BORE))
    d.make("GasBlock", bm, body, m_steel, "Gas block clamping barrel and cylinder.")
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.3660, 0.0), (0.3660, 0.0090), (0.3760, 0.0090), (0.3775, 0.0078), (0.3775, 0.0)], sides=24, c=(0.0, gz))
    nut = d.make("GasNut", bm, body, m_steel, "Gas plug.")
    bm = bmesh.new()
    for a in (45.0, 135.0, 225.0, 315.0):
        r = math.radians(a)
        d.bm_box(bm, (0.0095 * math.cos(r), 0.3740, gz + 0.0095 * math.sin(r)), (0.0040, 0.0080, 0.0040), rot=(0, a, 0))
    notch = d.make("GasNut_NotchCutter", bm, cutters, None, "Boolean cutter: spanner notches.")
    d.cut(nut, notch, "Notches")
    # The stacking rod: the gas plug runs out forward into a thin rod with a ball end, above the barrel.
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.3775, 0.0), (0.3775, 0.0036), (0.3800, 0.0022), (0.4080, 0.0022), (0.4094, 0.0033), (0.4120, 0.0039),
                    (0.4146, 0.0033), (0.4160, 0.0)], sides=12, c=(0.0, gz))
    d.make("StackingRod", bm, body, m_steel, "Stacking rod on the gas plug.")
    # Handguard: a stamped steel shell round the barrel only, from the receiver to short of the gas
    # block, with a row of cooling holes (drawn in the detail sheet). Its underside is at z 0.076,
    # where the AKM animation puts the left hand.
    def shell(grow):
        return (_arc((0.0, 0.0910), 0.0150 + grow, 180.0, 360.0, 14)
                + [(0.0150 + grow, 0.0990), (0.0100 + grow, 0.1075 + grow), (-0.0100 - grow, 0.1075 + grow), (-0.0150 - grow, 0.0990)])
    bm = bmesh.new()
    d.bm_xsec(bm, shell(0.0), 0.1040, 0.2450)
    d.make("Handguard", bm, body, m_steel, "Stamped steel handguard shell round the barrel.", bevel=0.0010)
    bm = bmesh.new()
    d.bm_xsec(bm, shell(0.0007), 0.2425, 0.2465)
    d.make("HandguardCap", bm, body, m_steel, "Front band of the handguard.", bevel=0.0005)
    bm = bmesh.new()
    m41.bm_torus(bm, (-0.0175, 0.3510, BORE - 0.0040), 0.0070, 0.0015, seg=16, sides=8)
    d.make("SlingLoopFront", bm, body, m_steel, "Front sling loop on the left of the gas block.")

    # --- Sights --------------------------------------------------------------------------------------
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.4250, 0.0075), (0.4262, 0.0102), (0.4440, 0.0102), (0.4452, 0.0075)], sides=24, c=(0.0, BORE), cap=False)
    # Tall base flaring out to the band, carrying a sheet-steel hood: a short tunnel over the post,
    # as on the real rifle (a thin ring on a stalk reads as an AK).
    d.bm_profile(bm, [(0.4255, BORE + 0.0085), (0.4445, BORE + 0.0085), (0.4425, BORE + 0.0150), (0.4400, SIGHT_Z - 0.0125),
                      (0.4300, SIGHT_Z - 0.0125), (0.4275, BORE + 0.0150)], 0.0095)
    d.make("FrontSightBase", bm, body, m_steel, "Front sight band and its tall base.", bevel=0.0007)
    bm = bmesh.new()
    d.bm_lathe(bm, [(0.4250, 0.0098), (0.4250, 0.0121), (0.4262, 0.0124), (0.4438, 0.0124), (0.4450, 0.0121), (0.4450, 0.0098)],
               sides=28, c=(0.0, SIGHT_Z - 0.0010), closed=True, cap=False)
    d.make("FrontSightHood", bm, body, m_steel, "Front sight hood: a short sheet-steel tunnel over the post.")
    d.box("FrontSightPost", body, m_steel, (0.0, 0.4350, SIGHT_Z - 0.0055), (0.0018, 0.0024, 0.0110), bevel=0.0002,
          note="Front sight post; its top is on the sight line.")
    top_z = TOP_Z + R_TOP
    d.profile("RearSightBase", body, m_steel,
              [(0.0200, top_z - 0.0030), (0.0950, top_z - 0.0030), (0.0950, top_z + 0.0030), (0.0300, top_z + 0.0060),
               (0.0200, top_z + 0.0060)], width=0.0180, bevel=0.0008, note="Tangent rear sight base.")
    d.profile("RearSightLeaf", body, m_steel,
              [(0.0260, top_z + 0.0060), (0.0900, top_z + 0.0030), (0.0900, top_z + 0.0048), (0.0260, top_z + 0.0082)],
              width=0.0110, bevel=0.0004, note="Tangent leaf.")
    # Notch shoulders on the sight line, level with the post's top, and a V 4.4 mm wide: the post shows
    # in it with light on both sides (the first notch, 2 mm higher and 2.8 mm wide, hid the post in game).
    z1, zn = SIGHT_Z, SIGHT_Z - 0.0021
    bm = bmesh.new()
    d.bm_xsec(bm, [(-0.0070, top_z + 0.0075), (0.0070, top_z + 0.0075), (0.0070, z1), (0.0022, z1), (0.0, zn), (-0.0022, z1),
                   (-0.0070, z1)], 0.0240, 0.0270)
    d.make("RearSightNotch", bm, body, m_steel, "V notch. The sight line runs along its shoulders.", bevel=0.0002)
    bm = bmesh.new()
    d.bm_box(bm, (0.0, 0.0600, top_z + 0.0052), (0.0170, 0.0080, 0.0050))
    for side in (-1, 1):
        prof = [(0.0085, 0.0), (0.0085, 0.0024), (0.0108, 0.0024), (0.0112, 0.0018), (0.0112, 0.0)]
        if side < 0:
            prof = [(-x, r) for x, r in prof][::-1]
        d.bm_lathe(bm, prof, sides=12, axis="X", c=(0.0600, top_z + 0.0052))
    d.make("RearSightSlider", bm, body, m_steel, "Range slider with its two release buttons.", bevel=0.0004)
    bm = bmesh.new()
    for k in range(8):                                   # range graduations along both edges of the leaf
        y = 0.0330 + 0.0072 * k
        zt = top_z + 0.0082 - (0.0082 - 0.0048) * (y - 0.0260) / (0.0900 - 0.0260)
        for side in (-1, 1):
            d.bm_box(bm, (side * 0.0049, y, zt + 0.00015), (0.0012, 0.0006, 0.0003))
    d.make("RearSightMarks", bm, body, m_steel, "Range graduations on the tangent leaf.")
    d.box("ScopeRail", body, m_steel, (0.0165, -0.0700, TOP_Z + 0.0165), (0.0050, 0.0900, 0.0070), bevel=0.0010,
          note="Scope mounting rail on the right of the receiver top.")

    # --- Origin shift, memory points, proxies ---------------------------------------------------------
    d.empty("Origin", memory, (-X_OFFSET, 0.0, 0.0), "Export origin: puts the rifle on the AKM's centre line (x = -0.0102).")
    d.empty("Mem_Muzzle", memory, (0, MUZZLE_Y, BORE), "'usti hlavne' - muzzle.")
    d.empty("Mem_BarrelEnd", memory, (0, 0.1100, BORE), "'konec hlavne' - with the muzzle sets the firing direction.")
    d.empty("Mem_Eye", memory, (0, -0.2300, SIGHT_Z), "'eye' - iron sight camera (the vanilla AKM's).")
    d.empty("Mem_CaseStart", memory, (0.0200, 0.0300, BORE + 0.0090), "'nabojnicestart' - where spent cases appear.")
    d.empty("Mem_CaseEnd", memory, (0.1200, -0.0400, BORE + 0.0300), "'nabojniceend' - direction spent cases fly.")

    d.empty("Proxy_Magazine", proxies, MAG_AT, "magazine proxy (slot magazine); the AF StG 44 magazine's origin.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Scope", proxies, SCOPE_AT, "scope proxy (slot weaponOpticsAFStG); the AF ZF4 scope's origin.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Suppressor", proxies, (0, MUZZLE_Y + 0.1356, BORE + 0.0035),
            "suppressor_545 proxy (slot weaponMuzzleAK); same offset from the muzzle as on the AKM.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Bottle", proxies, (0, MUZZLE_Y + 0.1115, BORE + 0.0044),
            "bottle_suppressor proxy (slot suppressorImpro); same offset from the muzzle as on the AKM.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Wrap1", proxies, (0, 0.2165, 0.1441), "ghillie_wrap proxy 1 (slot weaponWrap), as on the AKM.", kind="ARROWS", size=0.03)
    d.empty("Proxy_Wrap2", proxies, (0, 0.0246, 0.1422), "ghillie_wrap proxy 2, as on the AKM.", kind="ARROWS", size=0.03)


# ----------------------------------------------------------------------------
# Build: the magazine (its own model; origin = the rifle's magazine proxy)
# ----------------------------------------------------------------------------

def _mag_centre(z):
    """Centre line of the curved magazine, in the rifle's coordinates."""
    t = (0.0640 - z) / 0.2140
    return 0.0350 + 0.0650 * t * t


def build_magazine():
    d.PREFIX = MAG_PREFIX
    old_prefix, m41.PREFIX = m41.PREFIX, MAG_PREFIX
    try:
        d.clean()
        body = d.collection("Body")
        d.collection("Moving")
        m_steel = d.material("Steel", (0.0130, 0.0137, 0.0130), rough=0.42, metal=0.35, bump=0.04, bump_scale=1000,
                             rough_var=0.06)
        m_brass = d.material("Brass", (0.60, 0.38, 0.12), rough=0.30, metal=1.0, rough_var=0.06, scratches=0.25,
                             wear_rgb=(0.74, 0.55, 0.26))
        m_jacket = d.material("Jacket", (0.50, 0.24, 0.12), rough=0.34, metal=1.0, rough_var=0.05)
        sheet = magazine_sheet()
        _phosphate(m_steel, 9.0, carried=False, zones=MAG_ZONES,
                   sheets=[(sheet, 1, MAG_WINDOW, 0.008), (sheet, -1, MAG_WINDOW, 0.008)])
        oy, oz = MAG_AT[1], MAG_AT[2]
        half, top, bottom, n = 0.0285, 0.0640, -0.1500, 14
        zs = [top + (bottom - top) * k / n for k in range(n + 1)]
        front = [(_mag_centre(z) + half - oy, z - oz) for z in zs]
        rear = [(_mag_centre(z) - half - oy, z - oz) for z in zs]
        bm = bmesh.new()
        d.bm_profile(bm, front + rear[::-1], 0.0250)
        d.make("Body", bm, body, m_steel, "Curved magazine body.", bevel=0.0020, segments=2)
        zb = bottom - oz
        d.box("FloorPlate", body, m_steel, (0.0, _mag_centre(bottom) - oy, zb - 0.0018), (0.0285, 2 * half + 0.0040, 0.0040),
              bevel=0.0010, note="Floor plate.")
        bm = bmesh.new()
        d.bm_box(bm, (0.0, _mag_centre(bottom) - oy, zb - 0.0043), (0.0200, 2 * half - 0.0100, 0.0012))
        d.bm_lathe(bm, [(zb - 0.0062, 0.0), (zb - 0.0062, 0.0030), (zb - 0.0052, 0.0040), (zb - 0.0040, 0.0040)], sides=12, axis="Z",
                   c=(0.0, _mag_centre(bottom) - oy + 0.0120))
        d.make("FloorPlateLock", bm, body, m_steel, "Retaining plate and its catch button under the floor plate.", bevel=0.0004)
        base = (_mag_centre(top) - 0.0260 - oy, top - oz + 0.0010)
        for nm, mat, prof in (("Round", m_brass, ROUND_CASE), ("RoundSlug", m_jacket, ROUND_SLUG)):
            bm = bmesh.new()
            d.bm_lathe(bm, [(base[0] + y, r) for y, r in prof], sides=12, c=(0.0, base[1]), cap=False)
            d.make(nm, bm, body, mat, "Top round between the feed lips.")
    finally:
        m41.PREFIX = old_prefix


# ----------------------------------------------------------------------------
# Build: the scope (its own model; origin on the tube axis, at the rifle's scope proxy)
# ----------------------------------------------------------------------------

SCOPE_REAR, SCOPE_FRONT = -0.0900, 0.0850      # ends of the scope along its axis
SCOPE_EYE = -0.1550                            # 'eyescope': the eye, behind the eyepiece


def build_scope():
    d.PREFIX = SCOPE_PREFIX
    old_prefix, m41.PREFIX = m41.PREFIX, SCOPE_PREFIX
    try:
        d.clean()
        body = d.collection("Body")
        d.collection("Moving")
        memory = d.collection("Memory")
        m_steel = d.material("Steel", (0.010, 0.0105, 0.011), rough=0.40, metal=0.45, bump=0.03, bump_scale=1200,
                             rough_var=0.06, machining=0.03)
        _phosphate(m_steel, 9.0, carried=False, zones=SCOPE_ZONES)
        # Tube: hollow, so that the eye looks through it. Outside and inside walls in one closed lathe.
        m_black = d.material("Black", (0.004, 0.004, 0.004), rough=0.92, metal=0.0)
        bm = bmesh.new()
        d.bm_lathe(bm, [(SCOPE_REAR + 0.0010, 0.0119), (SCOPE_REAR, 0.0130), (SCOPE_REAR, 0.0150), (SCOPE_REAR + 0.0300, 0.0150),
                        (SCOPE_REAR + 0.0340, 0.0128), (0.0450, 0.0128), (0.0490, 0.0150), (SCOPE_FRONT, 0.0150),
                        (SCOPE_FRONT, 0.0138), (SCOPE_FRONT - 0.0010, 0.0127)], sides=28, c=(0.0, 0.0), cap=False)
        d.make("Tube", bm, body, m_steel, "Scope tube: eyepiece at the rear, objective at the front.")
        bm = bmesh.new()
        d.bm_lathe(bm, [(SCOPE_FRONT - 0.0010, 0.0126), (0.0500, 0.0126), (0.0440, 0.0108), (SCOPE_REAR + 0.0340, 0.0108),
                        (SCOPE_REAR + 0.0280, 0.0118), (SCOPE_REAR + 0.0010, 0.0118)], sides=28, c=(0.0, 0.0), cap=False)
        d.make("TubeInside", bm, body, m_black, "Blackened inside of the tube: the eye looks through it.")
        bm = bmesh.new()
        d.bm_lathe(bm, [(-0.0080, 0.0128), (-0.0080, 0.0170), (0.0100, 0.0170), (0.0100, 0.0128)], sides=24, c=(0.0, 0.0), cap=False)
        d.bm_lathe(bm, [(0.0170, 0.0), (0.0170, 0.0075), (0.0250, 0.0075), (0.0262, 0.0062), (0.0262, 0.0)], sides=20, axis="Z", c=(0.0, 0.0010))
        d.bm_lathe(bm, [(0.0170, 0.0), (0.0170, 0.0075), (0.0250, 0.0075), (0.0262, 0.0062), (0.0262, 0.0)], sides=20, axis="X", c=(0.0010, 0.0))
        d.make("Turrets", bm, body, m_steel, "Saddle with the elevation drum on top and the windage drum on the right.", bevel=0.0005)
        for nm, y in (("RingRear", -0.0380), ("RingFront", 0.0300)):
            bm = bmesh.new()
            d.bm_lathe(bm, [(y - 0.0060, 0.0128), (y - 0.0060, 0.0158), (y + 0.0060, 0.0158), (y + 0.0060, 0.0128)], sides=24,
                       c=(0.0, 0.0), cap=False)
            d.bm_box(bm, (0.0120, y, -0.0170), (0.0100, 0.0120, 0.0140))
            d.make(nm, bm, body, m_steel, "Mounting ring with its foot on the rifle's rail.", bevel=0.0006)
        d.box("MountBar", body, m_steel, (0.0150, -0.0040, -0.0235), (0.0080, 0.0900, 0.0050), bevel=0.0008,
              note="Mount bar that clamps to the rail on the receiver.")
        d.empty("Mem_EyeScope", memory, (0, SCOPE_EYE, 0.0), "'eyescope' - where the eye is when aiming through the scope.")
        d.empty("Mem_CameraDir", memory, (0, SCOPE_EYE + 0.5, 0.0), "'cameradir' - the eye looks from eyescope towards this point.")
    finally:
        m41.PREFIX = old_prefix


if __name__ == "__main__":
    build()
    build_magazine()
    build_scope()
    print("AF StG 44, its magazine and its scope built.")
