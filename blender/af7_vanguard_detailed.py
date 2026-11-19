"""
AF-7 "Vanguard" - detailed model for Blender (4.2 LTS or newer, tested on 5.3).

The realistic follow-up to af7_vanguard_blockout.py: shaped parts, crisp single
chamfers (the angular "Vanguard" look), a hollow slotted handguard, a real
Picatinny rail, hex muzzle brake, skeleton stock, the orange-and-black AF logo
on both sides of the magazine well and the stock, and procedural PBR materials.

HOW TO USE
  1. Open Blender. Scripting tab > Open > this file > Run Script (play button).
  2. Switch the viewport to Material Preview or Rendered (Z key).
  3. When you're happy, run af7_vanguard_dayz_export.py to build the DayZ files
     (LODs, UVs, baked textures, af7_vanguard.p3d).

WARNING: running this deletes every object whose name starts with AF7_
(including the old blockout and any DayZ LODs) and rebuilds from scratch.

LAYOUT (working frame, same as the blockout)
  - Meters, about 0.89 m long, pointing forward along +Y, up is +Z, trigger at 0,0,0.
  - The export script moves/rotates everything into the vanilla M4 frame for DayZ.
  - Collections:
      AF7_Body        static parts
      AF7_Moving      animated parts - keep separate
      AF7_Memory      memory-point empties
      AF7_Proxies     attachment-proxy empties
      AF7_Reference   reference only (magazine, hand size)        - never exported
      AF7_Cutters     hidden Boolean cutters                       - never exported
      AF7_Render      camera, lights, floor for preview renders   - never exported
"""

import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector

PREFIX = "AF7_"
BORE = 0.055  # height of the barrel centre line above the trigger

# Logo placements: (y0, z0, width, height, |x| min, |x| max) in the working frame.
LOGO_MAGWELL = (0.050, -0.027, 0.060, 0.030, 0.0138, 0.0149)   # floor of the recessed panel
LOGO_STOCK = (-0.300, 0.040, 0.048, 0.024, 0.0160, 0.0180)     # printed flat on the stock

ORANGE = (1.0, 0.42, 0.02)


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    return os.path.expanduser("~")


# ----------------------------------------------------------------------------
# AF logo (drawn in code so there is no external art dependency)
# ----------------------------------------------------------------------------

def _inside(px, py, poly):
    res = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if y1 == y2:
            continue
        res ^= ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1)
    return res


def _chamfer_rect(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def logo_image(width=1024, height=512, ss=3):
    """Black chamfered plate, orange border, orange 'AF'. Returns a packed Blender image."""
    W, H = width * ss, height * ss
    py, px = np.mgrid[0:H, 0:W]
    px = (px + 0.5) / H          # 0..2 across
    py = (py + 0.5) / H          # 0..1 up

    plate = _inside(px, py, _chamfer_rect(0.0, 0.0, 2.0, 1.0, 0.13))
    border = _inside(px, py, _chamfer_rect(0.045, 0.045, 1.955, 0.955, 0.115)) & \
        ~_inside(px, py, _chamfer_rect(0.085, 0.085, 1.915, 0.915, 0.10))

    def letter_space(bx, by, bw, bh, shear):
        return (px - bx - shear * (py - by)) / bw, (py - by) / bh

    lx, ly = letter_space(0.34, 0.21, 0.60, 0.58, 0.16)
    a = _inside(lx, ly, [(0, 0), (0.36, 1), (0.64, 1), (1, 0)]) & \
        ~_inside(lx, ly, [(0.391, 0.42), (0.609, 0.42), (0.5, 0.722)]) & \
        ~_inside(lx, ly, [(0.24, 0), (0.76, 0), (0.674, 0.24), (0.326, 0.24)])
    lx, ly = letter_space(1.06, 0.21, 0.50, 0.58, 0.16)
    f = _inside(lx, ly, [(0, 0), (0.28, 0), (0.28, 1), (0, 1)]) | \
        _inside(lx, ly, [(0, 0.76), (1.0, 0.76), (0.92, 1), (0, 1)]) | \
        _inside(lx, ly, [(0, 0.38), (0.78, 0.38), (0.72, 0.60), (0, 0.60)])
    orange = (border | a | f) & plate

    rgba = np.zeros((H, W, 4), dtype=np.float32)
    rgba[..., 0:3] = 0.012
    rgba[orange, 0], rgba[orange, 1], rgba[orange, 2] = ORANGE
    rgba[..., 3] = plate
    rgba = rgba.reshape(height, ss, width, ss, 4).mean(axis=(1, 3))

    img = bpy.data.images.get(PREFIX + "Logo")
    if img and (img.size[0] != width or img.size[1] != height):
        bpy.data.images.remove(img)
        img = None
    if not img:
        img = bpy.data.images.new(PREFIX + "Logo", width, height, alpha=True)
    img.pixels.foreach_set(rgba.ravel())
    tex_dir = os.path.join(_here(), "textures")
    try:
        os.makedirs(tex_dir, exist_ok=True)
        img.filepath_raw = os.path.join(tex_dir, "af_logo.png")
        img.file_format = "PNG"
        img.save()
    except Exception as exc:  # read-only folder etc. - the packed copy still works
        print("AF logo not saved to disk:", exc)
    try:
        img.pack()
    except Exception:
        pass
    return img


def pattern_image():
    """Gold floral pattern mask (white = gold), lifted from the old AF R700 chassis texture
    and made seamless. Lives in blender/textures/af_gold_floral.png. None if the file is missing."""
    path = os.path.join(_here(), "textures", "af_gold_floral.png")
    img = bpy.data.images.get(PREFIX + "GoldFloral")
    if img:
        return img
    if not os.path.isfile(path):
        print("Gold floral pattern not found (%s) - the gold skin is skipped." % path)
        return None
    img = bpy.data.images.load(path)
    img.name = PREFIX + "GoldFloral"
    img.colorspace_settings.name = "Non-Color"
    try:
        img.pack()
    except Exception:
        pass
    return img


# Gold skin: colours measured from the R700 texture (linear RGB), one pattern tile = 0.18 m.
GOLD_SKIN = {"gold": (0.50, 0.18, 0.0005), "dark": (0.005, 0.005, 0.004), "scale": 1.0 / 0.18}


# ----------------------------------------------------------------------------
# Scene / material helpers
# ----------------------------------------------------------------------------

def clean():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PREFIX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for col in list(bpy.data.collections):
        if col.name.startswith(PREFIX):
            bpy.data.collections.remove(col)
    for store in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
        for block in list(store):
            if block.users == 0:
                store.remove(block)


def collection(name):
    col = bpy.data.collections.new(PREFIX + name)
    bpy.context.scene.collection.children.link(col)
    return col


class _Nodes:
    """Tiny node-building helper: sockets or plain numbers both work as inputs."""

    def __init__(self, nt):
        self.nt = nt

    def new(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def feed(self, sock, value):
        if hasattr(value, "is_linked"):
            self.nt.links.new(value, sock)
        else:
            sock.default_value = value

    def math(self, op, a, b=None, clamp=False):
        n = self.new("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.feed(n.inputs[0], a)
        if b is not None:
            self.feed(n.inputs[1], b)
        return n.outputs[0]

    def mix(self, fac, a, b):
        n = self.new("ShaderNodeMix", data_type="RGBA")
        ins = [s for s in n.inputs if s.enabled]
        outs = [s for s in n.outputs if s.enabled]
        if len(ins) != 3:
            ins, outs = [n.inputs[0], n.inputs[6], n.inputs[7]], [n.outputs[2]]
        for sock, val in zip(ins, (fac, a, b)):
            if not hasattr(val, "is_linked") and not isinstance(val, (int, float)):
                val = (*val, 1.0)
            self.feed(sock, val)
        return outs[0]


def material(name, rgb, rough=0.5, metal=0.0, bump=0.0, bump_scale=600.0, rough_var=0.0,
             wear=0.0, wear_rgb=(0.5, 0.5, 0.5), logo=None, logo_img=None, skin_img=None,
             scratches=0.0, machining=0.0, stipple=0.0):
    """Principled material: micro-bump, roughness variation, bevelled-edge shading and
    edge wear (both Cycles/bake only), optional AF logo projected from the sides.
    The reroutes AF7_COLOR / AF7_ROUGH / AF7_METAL are what the DayZ export bakes.
    With skin_img, the Value node AF7_SKIN switches the surface between the normal
    finish (0) and gold floral on black (1)."""
    mat = bpy.data.materials.get(PREFIX + name) or bpy.data.materials.new(PREFIX + name)
    try:
        mat.use_nodes = True
    except Exception:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    N = _Nodes(nt)
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    coord = N.new("ShaderNodeTexCoord")
    geo = N.new("ShaderNodeNewGeometry")

    color = N.new("ShaderNodeRGB")
    color.outputs[0].default_value = (*rgb, 1.0)
    color = color.outputs[0]
    rough_s = rough
    metal_s = metal

    if rough_var:
        n1 = N.new("ShaderNodeTexNoise")
        n1.inputs["Scale"].default_value = 18.0
        n1.inputs["Detail"].default_value = 6.0
        nt.links.new(coord.outputs["Object"], n1.inputs["Vector"])
        rng = N.new("ShaderNodeMapRange")
        rng.inputs[1].default_value, rng.inputs[2].default_value = 0.3, 0.7
        rng.inputs[3].default_value = max(0.02, rough - rough_var)
        rng.inputs[4].default_value = min(1.0, rough + rough_var)
        nt.links.new(n1.outputs[0], rng.inputs[0])
        rough_s = rng.outputs[0]

    if skin_img:
        sk = N.new("ShaderNodeValue")
        sk.name = sk.label = PREFIX + "SKIN"
        sk.outputs[0].default_value = 0.0
        sk = sk.outputs[0]
        sc = N.new("ShaderNodeVectorMath", operation="SCALE")
        nt.links.new(geo.outputs["Position"], sc.inputs[0])
        sc.inputs["Scale"].default_value = GOLD_SKIN["scale"]
        ptex = N.new("ShaderNodeTexImage", image=skin_img, projection="BOX")
        ptex.projection_blend = 0.05
        nt.links.new(sc.outputs[0], ptex.inputs[0])
        gold = ptex.outputs["Color"]                      # 1 on the gold ornament, 0 on black
        color = N.mix(sk, color, N.mix(gold, GOLD_SKIN["dark"], GOLD_SKIN["gold"]))
        keep = N.math("SUBTRACT", 1.0, sk)
        metal_s = N.math("ADD", N.math("MULTIPLY", keep, metal_s), N.math("MULTIPLY", sk, gold))
        skin_rough = N.math("SUBTRACT", 0.46, N.math("MULTIPLY", gold, 0.22))
        rough_s = N.math("ADD", N.math("MULTIPLY", keep, rough_s), N.math("MULTIPLY", sk, skin_rough))
        skin_sock = sk
    else:
        skin_sock = None

    if wear:
        bev = N.new("ShaderNodeBevel", samples=6)
        bev.inputs["Radius"].default_value = 0.0010
        dot = N.new("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        nt.links.new(geo.outputs["Normal"], dot.inputs[0])
        nt.links.new(bev.outputs[0], dot.inputs[1])
        edge = N.math("MULTIPLY", N.math("SUBTRACT", 1.0, dot.outputs["Value"]), 5.0, clamp=True)
        n3 = N.new("ShaderNodeTexNoise")
        n3.inputs["Scale"].default_value = 45.0
        n3.inputs["Detail"].default_value = 6.0
        nt.links.new(geo.outputs["Position"], n3.inputs["Vector"])
        patch = N.math("MULTIPLY", N.math("SUBTRACT", n3.outputs[0], 0.50), 6.0, clamp=True)
        mask = N.math("MULTIPLY", N.math("MULTIPLY", edge, patch), wear, clamp=True)
        if skin_sock is not None:     # the ornament reads better with much lighter wear
            mask = N.math("MULTIPLY", mask, N.math("SUBTRACT", 1.0, N.math("MULTIPLY", skin_sock, 0.7)))
        color = N.mix(mask, color, wear_rgb)
        rough_s = N.math("SUBTRACT", rough_s, N.math("MULTIPLY", mask, 0.15), clamp=True)

    # Surface imperfections. `heights` collects everything that goes into the normal map.
    heights = []
    if scratches:
        # Two sets of long, hair-thin streaks at different angles along the sides of the rifle.
        smask = None
        for rot, scale in (((0.45, 0.20, 0.30), (320.0, 20.0, 320.0)), ((-0.70, -0.25, 0.55), (320.0, 320.0, 24.0)),
                           ((1.10, 0.35, -0.40), (26.0, 320.0, 320.0))):
            # Rotate first, then stretch: the stretch then follows the rotated axes, so the
            # streaks run at an angle instead of dead straight along the rifle.
            turn = N.new("ShaderNodeMapping")
            turn.inputs["Rotation"].default_value = rot
            nt.links.new(geo.outputs["Position"], turn.inputs["Vector"])
            mp = N.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = scale
            nt.links.new(turn.outputs[0], mp.inputs["Vector"])
            ns = N.new("ShaderNodeTexNoise")
            ns.inputs["Scale"].default_value = 1.0
            ns.inputs["Detail"].default_value = 2.0
            nt.links.new(mp.outputs[0], ns.inputs["Vector"])
            streak = N.math("MULTIPLY", N.math("SUBTRACT", ns.outputs[0], 0.72), 14.0, clamp=True)
            smask = streak if smask is None else N.math("MAXIMUM", smask, streak)
        smask = N.math("MULTIPLY", smask, scratches, clamp=True)
        if skin_sock is not None:
            smask = N.math("MULTIPLY", smask, N.math("SUBTRACT", 1.0, N.math("MULTIPLY", skin_sock, 0.6)))
        color = N.mix(N.math("MULTIPLY", smask, 0.55), color, wear_rgb)
        rough_s = N.math("ADD", rough_s, N.math("MULTIPLY", smask, 0.10), clamp=True)
        heights.append(N.math("MULTIPLY", smask, -0.5))
    if machining:
        # Fine turning marks running around the bore axis (barrel, pins, bolt).
        wave = N.new("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
        wave.inputs["Scale"].default_value = 1400.0
        wave.inputs["Distortion"].default_value = 0.0
        nt.links.new(geo.outputs["Position"], wave.inputs["Vector"])
        heights.append(N.math("MULTIPLY", wave.outputs[0], machining))
    if stipple:
        # Moulded grip texture on polymer and rubber.
        vor = N.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 2600.0
        nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
        heights.append(N.math("MULTIPLY", vor.outputs[0], stipple))

    if logo and logo_img:
        y0, z0, w, h, xmin, xmax = logo
        xyz = N.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], xyz.inputs[0])
        nrm = N.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Normal"], nrm.inputs[0])
        px, py, pz = xyz.outputs
        u_right = N.math("DIVIDE", N.math("SUBTRACT", py, y0), w)
        is_left = N.math("LESS_THAN", px, 0.0)
        # mirror u on the left side so the letters read correctly from both sides
        u = N.math("ADD", u_right, N.math("MULTIPLY", is_left, N.math("SUBTRACT", 1.0, N.math("MULTIPLY", u_right, 2.0))))
        v = N.math("DIVIDE", N.math("SUBTRACT", pz, z0), h)
        uv = N.new("ShaderNodeCombineXYZ")
        nt.links.new(u, uv.inputs[0])
        nt.links.new(v, uv.inputs[1])
        tex = N.new("ShaderNodeTexImage", image=logo_img, extension="CLIP", interpolation="Cubic")
        nt.links.new(uv.outputs[0], tex.inputs[0])
        ax = N.math("ABSOLUTE", px)
        mask = N.math("MULTIPLY", tex.outputs["Alpha"], N.math("GREATER_THAN", ax, xmin))
        mask = N.math("MULTIPLY", mask, N.math("LESS_THAN", ax, xmax))
        mask = N.math("MULTIPLY", mask, N.math("GREATER_THAN", N.math("ABSOLUTE", nrm.outputs[0]), 0.9))
        color = N.mix(mask, color, tex.outputs["Color"])
        inv = N.math("SUBTRACT", 1.0, mask)
        metal_s = N.math("MULTIPLY", inv, metal_s)
        rough_s = N.math("ADD", N.math("MULTIPLY", inv, rough_s), N.math("MULTIPLY", mask, 0.42))

    # Named taps for the export bake
    taps = {}
    for tap, src in (("COLOR", color), ("ROUGH", rough_s), ("METAL", metal_s)):
        if not hasattr(src, "is_linked"):
            val = N.new("ShaderNodeValue")
            val.outputs[0].default_value = src
            src = val.outputs[0]
        rr = N.new("NodeReroute")
        rr.name = rr.label = PREFIX + tap
        nt.links.new(src, rr.inputs[0])
        taps[tap] = rr.outputs[0]
    nt.links.new(taps["COLOR"], bsdf.inputs["Base Color"])
    nt.links.new(taps["ROUGH"], bsdf.inputs["Roughness"])
    nt.links.new(taps["METAL"], bsdf.inputs["Metallic"])

    # Normal: rounded-edge shading (Cycles) + fine grain
    bevn = N.new("ShaderNodeBevel", samples=6)
    bevn.inputs["Radius"].default_value = 0.0007
    normal = bevn.outputs[0]
    if bump:
        n2 = N.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = bump_scale
        n2.inputs["Detail"].default_value = 3.0
        nt.links.new(coord.outputs["Object"], n2.inputs["Vector"])
        heights.append(N.math("MULTIPLY", n2.outputs[0], bump * 2.67))
    if heights:
        total = heights[0]
        for hgt in heights[1:]:
            total = N.math("ADD", total, hgt)
        bmp = N.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = 1.0
        if "Distance" in bmp.inputs:
            bmp.inputs["Distance"].default_value = 0.00015
        nt.links.new(total, bmp.inputs["Height"])
        nt.links.new(normal, bmp.inputs["Normal"])
        normal = bmp.outputs[0]
    nt.links.new(normal, bsdf.inputs["Normal"])

    for i, n in enumerate(nt.nodes):
        n.location = (-220 * (len(nt.nodes) - i), -40 * (i % 7))
    mat.diffuse_color = (*rgb, 1.0)
    mat.metallic = metal
    mat.roughness = rough
    return mat


def empty(name, col, loc, note, kind="PLAIN_AXES", size=0.015):
    ob = bpy.data.objects.new(PREFIX + name, None)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    ob.location = loc
    ob["dayz"] = note
    col.objects.link(ob)
    return ob


# ----------------------------------------------------------------------------
# Geometry helpers (all write into a bmesh, so parts can be combined freely)
# ----------------------------------------------------------------------------

def bm_box(bm, center, size, rot=(0, 0, 0)):
    """Box; center/size in meters, rot in degrees (X, Y, Z)."""
    R = Euler([math.radians(a) for a in rot], "XYZ").to_matrix()
    c = Vector(center)
    v = []
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                p = R @ Vector((dx * size[0] / 2, dy * size[1] / 2, dz * size[2] / 2))
                v.append(bm.verts.new(c + p))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])


def bm_profile(bm, pts, width, x=0.0):
    """Side profile [(y, z), ...] extruded across the gun (along X)."""
    a = [bm.verts.new((x - width / 2, y, z)) for y, z in pts]
    b = [bm.verts.new((x + width / 2, y, z)) for y, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))


def bm_xsec(bm, pts, y0, y1):
    """Cross-section [(x, z), ...] extruded along the bore (Y)."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))


def bm_tube(bm, outer, inner, y0, y1, shear=0.0, zref=BORE):
    """Hollow cross-section along Y. `shear` slants the front face (top further forward)."""
    def ring(pts, y, sh):
        return [bm.verts.new((x, y + sh * (z - zref), z)) for x, z in pts]
    oa, ob_ = ring(outer, y0, 0.0), ring(outer, y1, shear)
    ia, ib = ring(inner, y0, 0.0), ring(inner, y1, shear)
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((oa[i], oa[j], ob_[j], ob_[i]))
        bm.faces.new((ia[i], ib[i], ib[j], ia[j]))
        bm.faces.new((oa[i], ia[i], ia[j], oa[j]))
        bm.faces.new((ob_[i], ob_[j], ib[j], ib[i]))


# Round parts with ROUND_MIN_SIDES or more sides get ROUND_DETAIL times the sides they ask for,
# up to ROUND_MAX_SIDES (0.9.0: 1.5 from 16 sides; 0.10.0: 2.0 from 10 sides, so pins, screws and
# knobs are round in outline too). Faceted parts (hex, octagon: smooth=False or fewer sides)
# are left alone.
ROUND_DETAIL = 2.0
ROUND_MIN_SIDES = 10
ROUND_MAX_SIDES = 64


def round_sides(sides, smooth=True):
    if smooth and sides >= ROUND_MIN_SIDES:
        if ROUND_DETAIL >= 1.0:
            return max(sides, min(ROUND_MAX_SIDES, int(round(sides * ROUND_DETAIL))))
        return max(4, int(round(sides * ROUND_DETAIL)))        # reduced-detail build for a distance LOD
    return sides


# Detail levels. FULL is the model as designed. The others rebuild the same weapon with fewer
# sides on round parts, plainer edges and, at the far end, no Boolean cuts, and are used by the
# DayZ export for the distance LODs: a part built coarse is clean, where the same part decimated
# from full detail comes out jagged (slotted handguards and tubes above all).
#   (name, ROUND_DETAIL, EDGE_SEGMENTS, FILLET_STEP in degrees (0 = corners as drawn), CUTS)
FULL = ("full", 2.0, 3, 15.0, True)
DETAIL_LEVELS = (("medium", 1.0, 1, 30.0, True), ("low", 0.5, 0, 0.0, True), ("far", 0.34, 0, 0.0, False),
                 ("minimal", 0.2, 0, 0.0, False))
FILLET_STEP = 15.0
CUTS = True


def set_detail(level):
    global ROUND_DETAIL, EDGE_SEGMENTS, FILLET_STEP, CUTS
    _name, ROUND_DETAIL, EDGE_SEGMENTS, FILLET_STEP, CUTS = level


# Rounded edges (0.10.0). A chamfer this wide or wider is cut in EDGE_SEGMENTS steps instead of
# one flat face, so it reads as a rounded edge in outline; narrower ones get fewer steps, because
# nobody can see the difference and every step costs triangles on every rib and screw.
EDGE_SEGMENTS = 3
EDGE_STEPS = ((0.0015, 3), (0.0007, 2))     # (minimum chamfer width in metres, steps)


def edge_segments(width, asked=1):
    if EDGE_SEGMENTS <= 1:
        return EDGE_SEGMENTS
    for limit, steps in EDGE_STEPS:
        if width >= limit:
            return max(asked, min(steps, EDGE_SEGMENTS))
    return asked


def fillet(pts, radius, step_deg=None):
    """Round the corners of a closed outline [(a, b), ...]. Each corner is replaced by a curve
    that starts `radius` before it and ends `radius` after it (less on short edges)."""
    step_deg = FILLET_STEP if step_deg is None else step_deg
    if not radius or not step_deg:
        return list(pts)
    out, n = [], len(pts)
    for i in range(n):
        p, a, b = Vector(pts[i]), Vector(pts[i - 1]), Vector(pts[(i + 1) % n])
        u, v = a - p, b - p
        lu, lv = u.length, v.length
        if lu < 1e-9 or lv < 1e-9:
            out.append(tuple(p))
            continue
        turn = math.pi - u.angle(v)
        cut_len = min(radius, 0.45 * lu, 0.45 * lv)
        steps = int(math.ceil(math.degrees(turn) / step_deg))
        if steps < 2 or cut_len < 1e-5:
            out.append(tuple(p))
            continue
        start, end = p + u * (cut_len / lu), p + v * (cut_len / lv)
        for k in range(steps + 1):
            t = k / steps
            q = start * (1 - t) ** 2 + p * (2 * t * (1 - t)) + end * t ** 2
            out.append((q.x, q.y))
    return out


def bm_lathe(bm, prof, sides=16, axis="Y", c=(0.0, BORE), closed=False, cap=True, smooth=True):
    """Revolve [(pos, radius), ...] around an axis.
    axis "Y": c = (x, z)   axis "X": c = (y, z)   axis "Z": c = (x, y)
    radius 0 makes a centre point; closed=True joins the last ring to the first.
    smooth=False keeps the facets (hex / octagon parts)."""
    def P(pos, r, t):
        a, b = r * math.cos(t), r * math.sin(t)
        if axis == "Y":
            return (c[0] + a, pos, c[1] + b)
        if axis == "X":
            return (pos, c[0] + a, c[1] + b)
        return (c[0] + a, c[1] + b, pos)
    sides = round_sides(sides, smooth)
    ang = [2 * math.pi * (i + 0.5) / sides for i in range(sides)]
    rings = []
    for pos, r in prof:
        if r <= 1e-7:
            rings.append([bm.verts.new(P(pos, 0.0, 0.0))])
        else:
            rings.append([bm.verts.new(P(pos, r, t)) for t in ang])
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    for A, B in pairs:
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(A) == 1:
                f = bm.faces.new((A[0], B[i], B[j]))
            elif len(B) == 1:
                f = bm.faces.new((A[i], A[j], B[0]))
            else:
                f = bm.faces.new((A[i], A[j], B[j], B[i]))
            f.smooth = smooth
    if cap and not closed:
        for R in (rings[0], rings[-1]):
            if len(R) > 1:
                bm.faces.new(R)


def make(name, bm, col, mat, note="", bevel=0.0, segments=1, sharp=35.0):
    """Turn a bmesh into an object: origin at its centre, crisp single chamfers.
    Chamfers are driven by edge bevel weights set here, so edges created later by
    Boolean cuts (slots, ports, panels) stay razor sharp."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    centre = (lo + hi) / 2
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=-centre)
    if bevel:
        layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
        limit = math.radians(30)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > limit:
                e[layer] = 1.0
    me = bpy.data.meshes.new(PREFIX + name)
    bm.to_mesh(me)
    bm.free()
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(sharp))
    ob = bpy.data.objects.new(PREFIX + name, me)
    ob.location = centre
    col.objects.link(ob)
    if mat:
        me.materials.append(mat)
    ob["dayz"] = note
    if bevel and edge_segments(bevel, segments) > 0:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = edge_segments(bevel, segments)
        mod.limit_method = "WEIGHT"
    return ob


def box(name, col, mat, center, size, rot=(0, 0, 0), bevel=0.0008, note="", **kw):
    bm = bmesh.new()
    bm_box(bm, center, size, rot)
    return make(name, bm, col, mat, note, bevel, **kw)


def profile(name, col, mat, pts, width, x=0.0, bevel=0.002, note="", round=0.0, **kw):
    """round: corner radius of the side outline (see fillet). 0 keeps the corners as drawn."""
    bm = bmesh.new()
    bm_profile(bm, fillet(pts, round), width, x)
    return make(name, bm, col, mat, note, bevel, **kw)


def blade(name, col, mat, spine, width, note="", bevel=None):
    """A curved, rounded blade (a trigger): `spine` is [(y, z, thickness), ...] along its centre line
    from the root to the tip. The centre line is a smooth curve through those points, the outline
    follows it at half the thickness on each side, and the edges are rounded right round, so the
    part has no flat faces or corners. Detail levels: fewer steps along the curve, plainer edges."""
    steps = max(1, min(4, int(round(60.0 / FILLET_STEP)))) if FILLET_STEP else 1
    P = [Vector((y, z, th)) for y, z, th in spine]
    ext = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    pts = []
    for i in range(1, len(ext) - 2):
        a, b, c, e = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(steps):
            t = k / steps
            pts.append(0.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - e) * t * t + (3 * b - a - 3 * c + e) * t ** 3))
    pts.append(P[-1])
    front, rear = [], []
    for i, p in enumerate(pts):
        q0, q1 = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tan = Vector((q1.x - q0.x, q1.y - q0.y))
        tan.normalize()
        n = Vector((-tan.y, tan.x))
        front.append((p.x + n.x * p.z / 2, p.y + n.y * p.z / 2))
        rear.append((p.x - n.x * p.z / 2, p.y - n.y * p.z / 2))
    tip = pts[-1]
    tan = Vector((tip.x - pts[-2].x, tip.y - pts[-2].y))
    tan.normalize()
    outline = front + [(tip.x + tan.x * tip.z * 0.5, tip.y + tan.y * tip.z * 0.5)] + rear[::-1]
    bm = bmesh.new()
    bm_profile(bm, outline, width)
    thin = min(th for _y, _z, th in spine)
    return make(name, bm, col, mat, note, min(width, thin) * 0.36 if bevel is None else bevel, segments=3, sharp=60.0)

def lathe(name, col, mat, prof, note="", bevel=0.0, **kw):
    bm = bmesh.new()
    bm_lathe(bm, prof, **kw)
    return make(name, bm, col, mat, note, bevel)


def cut(target, cutter, name):
    """Boolean-subtract `cutter` from `target`, keeping the Bevel last."""
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    cutter.hide_viewport = True
    if not CUTS:
        return
    boo = target.modifiers.new(name, "BOOLEAN")
    boo.operation = "DIFFERENCE"
    boo.solver = "EXACT"
    boo.object = cutter
    n_bool = sum(1 for m in target.modifiers if m.type == "BOOLEAN")
    target.modifiers.move(len(target.modifiers) - 1, n_bool - 1)


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def build():
    clean()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    body = collection("Body")
    moving = collection("Moving")
    memory = collection("Memory")
    proxies = collection("Proxies")
    ref = collection("Reference")
    cutters = collection("Cutters")
    render = collection("Render")

    logo = logo_image()

    # Two-tone: dark anodised receivers and steel, flat-dark-earth furniture.
    m_anod = material("Anodized", (0.030, 0.032, 0.036), rough=0.46, metal=0.9, bump=0.04, bump_scale=900,
                      rough_var=0.08, wear=0.75, wear_rgb=(0.42, 0.43, 0.45), logo=LOGO_MAGWELL, logo_img=logo,
                      scratches=0.6)
    m_steel = material("Steel", (0.050, 0.050, 0.055), rough=0.36, metal=1.0, bump=0.03, bump_scale=1200,
                       rough_var=0.10, wear=0.6, wear_rgb=(0.30, 0.30, 0.31), scratches=0.5, machining=0.25)
    m_bolt = material("BoltSteel", (0.30, 0.30, 0.31), rough=0.30, metal=1.0, rough_var=0.06,
                      wear_rgb=(0.55, 0.55, 0.56), scratches=0.4, machining=0.30)
    floral = pattern_image()
    m_cera = material("FDE_Cerakote", (0.40, 0.31, 0.19), rough=0.52, metal=0.0, bump=0.05, bump_scale=1400,
                      rough_var=0.06, wear=0.7, wear_rgb=(0.16, 0.15, 0.14), skin_img=floral, scratches=0.35)
    m_poly = material("FDE_Polymer", (0.36, 0.28, 0.17), rough=0.66, metal=0.0, bump=0.18, bump_scale=700,
                      rough_var=0.05, wear=0.5, wear_rgb=(0.50, 0.41, 0.28), logo=LOGO_STOCK, logo_img=logo,
                      skin_img=floral, scratches=0.2, stipple=0.5)
    m_rubber = material("Rubber", (0.018, 0.018, 0.018), rough=0.88, bump=0.25, bump_scale=500, stipple=0.6)
    m_mag = material("MagPolymer", (0.045, 0.045, 0.048), rough=0.58, bump=0.15, bump_scale=700)
    m_floor = material("Floor", (0.30, 0.31, 0.33), rough=0.75)
    m_ref = material("Reference", (0.2, 0.35, 0.6), rough=0.6)

    # --- Upper receiver ------------------------------------------------------
    upper = profile("UpperReceiver", body, m_anod,
                    [(-0.100, 0.036), (-0.100, 0.066), (-0.087, 0.079), (0.122, 0.079),
                     (0.122, 0.040), (0.118, 0.036)],
                    width=0.034, bevel=0.003, round=0.0025,
                    note="Upper receiver. Flat sides, big single chamfers, real ejection-port pocket on the right.")
    port = box("UpperReceiver_PortCutter", cutters, None, (0.018, 0.035, 0.058), (0.024, 0.062, 0.015), bevel=0,
               note="Boolean cutter for the ejection port.")
    cut(upper, port, "EjectionPort")
    # Raised angular armour panels (layered, hard-edged detail)
    bm = bmesh.new()
    bm_profile(bm, [(-0.072, 0.047), (0.084, 0.047), (0.104, 0.062), (0.104, 0.071), (-0.058, 0.071), (-0.072, 0.060)],
               width=0.0016, x=-0.0176)
    bm_profile(bm, [(0.076, 0.045), (0.104, 0.045), (0.114, 0.055), (0.114, 0.071), (0.076, 0.071)],
               width=0.0016, x=0.0176)
    make("UpperPanels", bm, body, m_anod, bevel=0.0007,
         note="Raised side panels on the upper receiver (static detail).")
    box("BrassDeflector", body, m_anod, (0.0185, -0.011, 0.058), (0.007, 0.016, 0.016), bevel=0.003,
        note="Brass deflector behind the ejection port.")
    bm = bmesh.new()
    bm_box(bm, (0.0185, 0.035, 0.0415), (0.0018, 0.066, 0.0135))
    bm_lathe(bm, [(0.000, 0.0015), (0.070, 0.0015)], sides=8, axis="Y", c=(0.0182, 0.0492))
    make("DustCover", bm, body, m_anod, bevel=0.0004,
         note="Dust cover, shown open (hanging below the ejection port).")

    # --- Lower receiver (with magazine well and recessed AF logo panels) ------
    lower = profile("LowerReceiver", body, m_anod,
                    [(-0.100, 0.036), (0.119, 0.036), (0.122, 0.028), (0.126, 0.022), (0.123, -0.030), (0.116, -0.038),
                     (0.040, -0.033), (0.034, -0.027), (0.031, 0.004), (-0.088, 0.004), (-0.100, 0.016)],
                    width=0.030, bevel=0.0025, round=0.0025,
                    note="Lower receiver + magazine well. The AF logo sits in the recessed panel on each side.")
    y0, z0, w, h = LOGO_MAGWELL[:4]
    panel = [(y0 + 0.004, z0), (y0 + w - 0.004, z0), (y0 + w, z0 + 0.004), (y0 + w, z0 + h - 0.004),
             (y0 + w - 0.004, z0 + h), (y0 + 0.004, z0 + h), (y0, z0 + h - 0.004), (y0, z0 + 0.004)]
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_profile(bm, panel, width=0.0056, x=sx * 0.0172)
    cut(lower, make("LowerReceiver_LogoCutter", bm, cutters, None, note="Boolean cutter - logo panels."), "LogoPanels")
    # Open magazine well: a real cavity for the magazine to slide into, so there is a dark
    # gap around it instead of the magazine sinking into a solid block.
    # The well is 8.9 cm long with a 7.9 cm opening: measured in game, a STANAG is wider at
    # the mouth of the well than its nominal 6.5 cm because of how steeply it rakes forward.
    cut(lower, box("LowerReceiver_MagwellCutter", cutters, None, (0, 0.0785, -0.0395), (0.027, 0.079, 0.022), bevel=0,
                   note="Boolean cutter - magazine well opening."), "MagwellOpening")
    # Flared lip around the opening (follows the slope of the magazine well's bottom edge).
    bm = bmesh.new()
    for sx in (-1, 1):
        bm_box(bm, (sx * 0.0158, 0.0785, -0.0342), (0.0045, 0.092, 0.011), rot=(-3.8, 0, 0))
    bm_box(bm, (0, 0.1222, -0.0371), (0.036, 0.0045, 0.011), rot=(-3.8, 0, 0))
    bm_box(bm, (0, 0.0348, -0.0313), (0.036, 0.0045, 0.011), rot=(-3.8, 0, 0))
    make("MagwellFlare", bm, body, m_anod, bevel=0.0012,
         note="Flared lip around the magazine well opening.")
    profile("TriggerGuard", body, m_anod,
            [(0.034, -0.027), (0.034, -0.032), (-0.014, -0.032), (-0.032, -0.018),
             (-0.029, -0.014), (-0.012, -0.027)],
            width=0.014, bevel=0.001, round=0.004, note="Trigger guard.")

    # Pins and small controls
    bm = bmesh.new()
    for y, z, r in ((0.105, 0.028, 0.0035), (-0.084, 0.028, 0.0035), (0.000, 0.016, 0.0021), (0.016, 0.027, 0.0021)):
        bm_lathe(bm, [(-0.0158, r * 0.8), (-0.0162, r), (0.0162, r), (0.0158, r * 0.8)],
                 sides=16, axis="X", c=(y, z))
    make("ReceiverPins", bm, body, m_steel, note="Pivot, takedown, trigger and hammer pins (static detail).")
    box("BoltCatch", body, m_steel, (-0.0165, 0.036, 0.036), (0.004, 0.012, 0.022), bevel=0.001,
        note="Bolt catch paddle, left side. Static for now (vanilla bone: boltrelease).")

    # --- Pistol grip ---------------------------------------------------------
    profile("PistolGrip", body, m_poly,
            [(-0.026, 0.006), (-0.031, -0.016), (-0.052, -0.094), (-0.060, -0.100), (-0.092, -0.094),
             (-0.094, -0.086), (-0.076, -0.028), (-0.084, -0.008), (-0.088, 0.006), (-0.070, 0.010)],
            width=0.030, bevel=0.005, round=0.008,
            note="Pistol grip. The right hand holds here - angle kept close to an M4 grip.")

    # --- Handguard: hollow, slanted nose, M-LOK style slots -------------------
    hg_outer = [(0.012, 0.079), (0.023, 0.067), (0.023, 0.041), (0.012, 0.029),
                (-0.012, 0.029), (-0.023, 0.041), (-0.023, 0.067), (-0.012, 0.079)]
    hg_inner = [(x * 0.85, 0.054 + (z - 0.054) * 0.85) for x, z in hg_outer]
    bm = bmesh.new()
    bm_tube(bm, hg_outer, hg_inner, 0.122, 0.445, shear=0.35)
    hg = make("Handguard", bm, body, m_cera, bevel=0.0009,
              note="Free-float handguard. Hollow, so the barrel and gas block show through the slots. The left hand holds here.")
    slot_y = [0.165 + i * 0.047 for i in range(6)]
    bm = bmesh.new()
    for y in slot_y:
        bm_box(bm, (0, y, BORE), (0.080, 0.032, 0.007))
    cut(hg, make("Handguard_SlotCutter_Side", bm, cutters, None, note="Boolean cutter - side slots."), "SlotsSide")
    bm = bmesh.new()
    for y in slot_y:
        bm_box(bm, (0, y, 0.034), (0.007, 0.032, 0.016))
    cut(hg, make("Handguard_SlotCutter_Bottom", bm, cutters, None, note="Boolean cutter - bottom slots."), "SlotsBottom")
    for tag, a in (("DiagA", 45), ("DiagB", -45)):
        bm = bmesh.new()
        for y in slot_y[:-1]:
            bm_box(bm, (0, y + 0.0235, 0.054), (0.090, 0.022, 0.005), rot=(0, a, 0))
        cut(hg, make("Handguard_SlotCutter_" + tag, bm, cutters, None, note="Boolean cutter - diagonal lightening cuts."),
            "Slots" + tag)

    # --- Picatinny rail (receiver + handguard, one continuous top rail) -------
    bm = bmesh.new()
    bm_xsec(bm, [(-0.0078, 0.079), (0.0078, 0.079), (0.0078, 0.0829), (0.0106, 0.0855),
                 (-0.0106, 0.0855), (-0.0078, 0.0829)], -0.094, 0.449)
    tooth = [(0.0106, 0.0855), (0.0106, 0.0859), (0.0080, 0.0885),
             (-0.0080, 0.0885), (-0.0106, 0.0859), (-0.0106, 0.0855)]
    for i in range(54):
        y = -0.090 + i * 0.010
        bm_xsec(bm, tooth, y, y + 0.0048)
    make("TopRail", bm, body, m_anod,
         note="Picatinny rail with real slot profile. Optics sit on it.")

    # --- Barrel, gas system, hex muzzle brake ---------------------------------
    lathe("Barrel", body, m_steel,
          [(0.118, 0.0120), (0.190, 0.0120), (0.196, 0.0095), (0.470, 0.0095), (0.474, 0.0085), (0.486, 0.0085)],
          sides=32, note="Barrel (14.5 in), stepped profile. Mostly hidden by the handguard.")
    bm = bmesh.new()
    bm_lathe(bm, [(0.326, 0.0130), (0.328, 0.0145), (0.354, 0.0145), (0.356, 0.0130)], sides=24)
    bm_box(bm, (0, 0.341, BORE + 0.0150), (0.012, 0.026, 0.008))
    bm_lathe(bm, [(0.122, 0.0025), (0.345, 0.0025)], sides=12, c=(0.0, BORE + 0.0155))
    make("GasBlock", bm, body, m_steel, note="Low-profile gas block + gas tube, visible through the handguard slots.")

    brake = lathe("MuzzleBrake", body, m_steel,
                  [(0.468, 0.0110), (0.471, 0.0130), (0.479, 0.0130), (0.482, 0.0150), (0.525, 0.0150),
                   (0.530, 0.0128), (0.530, 0.0040), (0.489, 0.0040), (0.489, 0.0)],
                  sides=6, smooth=False,
                  note="Hex muzzle brake with ports and an open bore. This is the hide_barrel selection (hidden when a suppressor is attached).")
    bm = bmesh.new()
    for y in (0.494, 0.506, 0.518):
        bm_box(bm, (0, y, BORE), (0.060, 0.0065, 0.011))
    cut(brake, make("MuzzleBrake_PortCutter", bm, cutters, None, note="Boolean cutter - brake ports."), "Ports")

    # --- Backup sights (low, deployed; line up with AF7_Mem_Eye at z = 0.097) --
    bm = bmesh.new()
    bm_box(bm, (0, 0.43, 0.0885), (0.026, 0.022, 0.008))
    for sx in (-1, 1):
        bm_box(bm, (sx * 0.0075, 0.43, 0.0975), (0.0022, 0.012, 0.011))
    bm_lathe(bm, [(0.092, 0.0012), (0.097, 0.0008)], sides=12, axis="Z", c=(0.0, 0.43))
    make("FrontSight", bm, body, m_steel, bevel=0.0006,
         note="Front backup sight: post between two protective ears. Post tip = sight line.")
    bm = bmesh.new()
    bm_box(bm, (0, -0.075, 0.0885), (0.026, 0.022, 0.008))
    for sx in (-1, 1):
        bm_box(bm, (sx * 0.0078, -0.075, 0.0965), (0.0030, 0.006, 0.009))
    bm_lathe(bm, [(-0.0765, 0.0036), (-0.0765, 0.0060), (-0.0735, 0.0060), (-0.0735, 0.0036)],
             sides=24, c=(0.0, 0.097), closed=True)
    bm_lathe(bm, [(0.0128, 0.0030), (0.0134, 0.0038), (0.0172, 0.0038), (0.0178, 0.0030)], sides=10, axis="X", c=(-0.075, 0.0895), smooth=False)
    make("RearSight", bm, body, m_steel, bevel=0.0005,
         note="Rear backup sight with a real aperture ring.")

    # --- Buffer tube + skeleton stock -----------------------------------------
    bm = bmesh.new()
    bm_lathe(bm, [(-0.098, 0.0148), (-0.296, 0.0148), (-0.300, 0.0125)], sides=32)
    bm_lathe(bm, [(-0.116, 0.0150), (-0.115, 0.0165), (-0.104, 0.0165), (-0.103, 0.0150)], sides=12, smooth=False)
    bm_box(bm, (0, -0.1015, 0.050), (0.030, 0.003, 0.040))
    make("BufferTube", bm, body, m_anod, note="Buffer tube with castle nut and end plate.")

    stock = profile("StockBody", body, m_poly,
                    [(-0.158, 0.072), (-0.164, 0.077), (-0.338, 0.077), (-0.342, 0.072), (-0.342, -0.052),
                     (-0.336, -0.058), (-0.322, -0.058), (-0.200, 0.026), (-0.162, 0.030), (-0.158, 0.036)],
                    width=0.034, bevel=0.004, round=0.004,
                    note="Skeleton stock: one body wrapped around the buffer tube with a triangular cutout. AF logo on both sides.")
    cut(stock, profile("StockBody_Cutter", cutters, None,
                       [(-0.236, 0.022), (-0.322, 0.022), (-0.326, 0.018), (-0.326, -0.036), (-0.320, -0.038)],
                       width=0.060, bevel=0, round=0.005, note="Boolean cutter - stock cutout."), "Cutout")
    box("StockCheek", body, m_poly, (0, -0.250, 0.0795), (0.040, 0.105, 0.009), bevel=0.003,
        note="Cheek rest (where the face sits when aiming).")
    box("StockLatch", body, m_poly, (0, -0.184, 0.0255), (0.014, 0.030, 0.008), rot=(-6, 0, 0), bevel=0.002,
        note="Stock adjustment latch (static detail).")
    lathe("StockQD", body, m_steel,
          [(-0.0176, 0.0045), (-0.0180, 0.0062), (0.0180, 0.0062), (0.0176, 0.0045)],
          sides=20, axis="X", c=(-0.318, 0.058), note="QD sling socket (static detail).")
    profile("ButtPad", body, m_rubber,
            [(-0.342, 0.078), (-0.352, 0.078), (-0.357, 0.070), (-0.357, -0.050), (-0.352, -0.059), (-0.342, -0.059)],
            width=0.036, bevel=0.003, round=0.004, note="Rubber butt pad. Rear end of the rifle.")

    # --- Detail pass: real geometry for the small mechanical features ----------
    # Forward assist: housing on the right rear of the upper, with its plunger.
    bm = bmesh.new()
    bm_box(bm, (0.0185, -0.044, 0.047), (0.007, 0.030, 0.013))
    bm_lathe(bm, [(-0.064, 0.0030), (-0.062, 0.0046), (-0.056, 0.0046), (-0.055, 0.0036), (-0.050, 0.0036)],
             sides=12, axis="Y", c=(0.0195, 0.047))
    make("ForwardAssist", bm, body, m_anod, bevel=0.0015,
         note="Forward assist housing and plunger (static detail).")

    # Grip: raised horizontal ribs on both sides.
    bm = bmesh.new()
    for i in range(7):
        z = -0.035 - i * 0.008
        y_front = -0.031 + (z + 0.016) * (0.021 / 0.078)
        y_back = -0.076 + (z + 0.028) * (0.018 / 0.058)
        for sx in (-1, 1):
            bm_box(bm, (sx * 0.0153, (y_front + y_back) / 2, z), (0.0012, (y_front - y_back) - 0.014, 0.0028))
    make("GripRibs", bm, body, m_poly, note="Raised grip ribs (static detail).")

    # Butt pad: horizontal ribs across the rear face.
    bm = bmesh.new()
    for i in range(9):
        bm_box(bm, (0, -0.3575, -0.040 + i * 0.0125), (0.030, 0.0014, 0.0045))
    make("ButtPadRibs", bm, body, m_rubber, note="Butt pad ribs (static detail).")

    # Handguard: hex screw heads at each end, both sides.
    bm = bmesh.new()
    for y in (0.133, 0.432):
        for z in (0.047, 0.062):
            for sx in (-1, 1):
                bm_lathe(bm, [(sx * 0.0226, 0.0027), (sx * 0.0240, 0.0027), (sx * 0.0240, 0.0013), (sx * 0.0232, 0.0013)],
                         sides=6, axis="X", c=(y, z), smooth=False)
    make("HandguardScrews", bm, body, m_steel, note="Handguard screw heads (static detail).")

    # Bolt catch: ridged thumb pad.
    bm = bmesh.new()
    for i in range(4):
        bm_box(bm, (-0.0188, 0.036, 0.0425 - i * 0.0032), (0.0009, 0.010, 0.0015))
    make("BoltCatchRibs", bm, body, m_steel, note="Bolt catch thumb-pad ridges (static detail).")

    # Magazine release: guard fence around the button.
    bm = bmesh.new()
    bm_box(bm, (0.0158, 0.022, 0.0175), (0.0030, 0.016, 0.0014))
    bm_box(bm, (0.0158, 0.022, 0.0065), (0.0030, 0.016, 0.0014))
    bm_box(bm, (0.0158, 0.0295, 0.012), (0.0030, 0.0014, 0.0124))
    make("MagReleaseFence", bm, body, m_anod, note="Fence around the magazine release (static detail).")

    # Castle nut notches and a rear sling plate loop.
    bm = bmesh.new()
    for k in range(6):
        a = math.radians(30 + k * 60)
        bm_box(bm, (0.0168 * math.cos(a), -0.1095, BORE + 0.0168 * math.sin(a)), (0.0030, 0.0070, 0.0030),
               rot=(0, -math.degrees(a), 0))
    bm_lathe(bm, [(-0.0036, 0.0058), (-0.0036, 0.0082), (0.0036, 0.0082), (0.0036, 0.0058)],
             sides=16, axis="Y", c=(-0.0200, 0.040), closed=True)
    make("ReceiverEndDetail", bm, body, m_steel, bevel=0,
         note="Castle nut lugs and sling loop on the end plate (static detail).")

    # --- Moving parts (separate objects = separate animated selections) -------
    # DayZ selection names come from the vanilla M4 model; see af7_vanguard_dayz_export.py.
    blade("Weapon_Trigger", moving, m_steel,
          [(0.0010, 0.0065, 0.0062), (0.0028, -0.0030, 0.0058), (0.0070, -0.0120, 0.0048), (0.0098, -0.0205, 0.0038)],
          width=0.006,
          note="Trigger: a curved, rounded blade. Exported as the 'trigger' selection (vanilla M4 bone). Rotates when firing.")
    bm = bmesh.new()
    bm_box(bm, (0, -0.109, 0.0745), (0.046, 0.012, 0.007))
    bm_box(bm, (0, -0.096, 0.0745), (0.012, 0.020, 0.006))
    bm_box(bm, (-0.0215, -0.1045, 0.0745), (0.0055, 0.0170, 0.0052))
    for cx in (0.012, 0.0155, 0.019):
        for sx in (-1, 1):
            bm_box(bm, (sx * cx, -0.109, 0.0784), (0.0016, 0.0100, 0.0012))
    make("ChargingHandle", bm, moving, m_anod, bevel=0.0012,
         note="Exported as the 'charging' selection (vanilla M4 bone). Pulled back to chamber.")
    bm = bmesh.new()
    bm_lathe(bm, [(0.006, 0.0050), (0.008, 0.0062), (0.062, 0.0062), (0.064, 0.0050)], sides=14, axis="Y", c=(0.0095, 0.058))
    for i in range(7):
        bm_box(bm, (0.0155, 0.040 + i * 0.0032, 0.058), (0.0012, 0.0016, 0.0080))
    bm_box(bm, (0.0150, 0.020, 0.058), (0.0016, 0.012, 0.0040))
    make("Weapon_Bolt", bm, moving, m_bolt,
         note="Exported as the 'bolt' selection (vanilla M4 bone). Carrier with forward-assist serrations, inside the ejection-port pocket.")
    box("MagRelease", moving, m_steel, (0.0165, 0.022, 0.012), (0.004, 0.012, 0.009), bevel=0.001,
        note="Mag release button, right side. Exported static.")
    bm = bmesh.new()
    bm_lathe(bm, [(-0.0185, 0.0040), (-0.0190, 0.0050), (-0.0150, 0.0050)], sides=16, axis="X", c=(-0.02, 0.03))
    bm_box(bm, (-0.0180, -0.030, 0.031), (0.0025, 0.020, 0.005))
    make("Safety", bm, moving, m_steel, bevel=0.0005,
         note="Safety selector, left side. Exported static (vanilla bone would be 'firemode').")

    # --- Memory points --------------------------------------------------------
    empty("Mem_Muzzle", memory, (0, 0.53, BORE),
          "'usti hlavne' (confirmed in the vanilla M4 model) - muzzle end. Bullets and muzzle flash start here.")
    empty("Mem_BarrelEnd", memory, (0, 0.43, BORE),
          "'konec hlavne' (confirmed) - a point behind the muzzle; with the muzzle it sets the firing direction.")
    # 7.5 cm behind the rear aperture. Tested in game: at 3.5 cm the camera's near plane cut the
    # rear sight down to a thin bar; at this distance the whole 7 mm peep is in view. Aim blur
    # is switched off in config.cpp, which was what made the original 8.5 cm position unusable.
    empty("Mem_Eye", memory, (0, -0.150, 0.097),
          "'eye' (confirmed) - camera position for iron sights. Must line up with rear + front sight.")
    empty("Mem_CaseStart", memory, (0.017, 0.035, BORE),
          "'nabojnicestart' (confirmed) - where spent cases appear.")
    empty("Mem_CaseEnd", memory, (0.09, 0.02, 0.085),
          "'nabojniceend' (confirmed) - direction spent cases fly.")

    # --- Attachment proxies ----------------------------------------------------
    empty("Proxy_Optic", proxies, (0, 0.0464, 0.0885),
          "optic_acog proxy (slot weaponOptics). Same spot along the rail as on the vanilla M4.", kind="ARROWS", size=0.03)
    # y = 0.086: measured in game, the STANAG's body is centred about 1 cm behind this point,
    # so the point sits 1 cm ahead of the well's centre to put the magazine in the middle.
    empty("Proxy_Magazine", proxies, (0, 0.086, -0.0105),
          "magazine_stanag30 proxy. This point becomes the model origin in DayZ, exactly like the vanilla M4.", kind="ARROWS", size=0.03)
    # The vanilla suppressor's body reaches about 9 cm behind this point (measured in game),
    # so it sits 3.5 cm ahead of the muzzle: the suppressor then starts just past the
    # handguard and leaves some barrel showing, instead of running into the handguard.
    empty("Proxy_Muzzle", proxies, (0, 0.565, BORE),
          "suppressor_556 proxy (slot weaponMuzzleM4).", kind="ARROWS", size=0.03)
    empty("Proxy_Light", proxies, (0.023, 0.36, BORE),
          "weaponlight_universal proxy (slot weaponFlashlight), right side of the handguard.", kind="ARROWS", size=0.03)

    # --- Reference (don't export) ---------------------------------------------
    profile("Ref_STANAG_Mag", ref, m_mag,
            [(0.047, 0.020), (0.107, 0.020), (0.105, -0.060), (0.110, -0.110), (0.121, -0.150),
             (0.064, -0.166), (0.052, -0.110), (0.045, -0.060)],
            width=0.022, bevel=0.002,
            note="REFERENCE ONLY (shown so previews look complete). DayZ shows the real mag via the proxy.")
    hand = box("Ref_HandSize", ref, m_ref, (0.03, -0.045, -0.05), (0.02, 0.09, 0.10), rot=(-20, 0, 0), bevel=0.01,
               note="REFERENCE ONLY. Roughly the size of a gloved hand around the grip.")
    hand.display_type = "WIRE"
    hand.hide_render = True
    hand.hide_viewport = True

    # --- Preview render rig (don't export) -------------------------------------
    target = Vector((0.0, 0.085, -0.015))

    def aim(ob):
        ob.rotation_euler = (target - ob.location).to_track_quat("-Z", "Y").to_euler()

    cam = bpy.data.objects.new(PREFIX + "Render_Camera", bpy.data.cameras.new(PREFIX + "Render_Camera"))
    cam.data.lens = 42
    cam.data.clip_start = 0.01
    cam.location = (0.95, 0.52, 0.30)
    aim(cam)
    render.objects.link(cam)
    scene.camera = cam
    for nm, loc, watts, size in (("Key", (0.9, 0.9, 1.1), 55, 0.8),
                                 ("Fill", (1.1, -0.9, 0.35), 18, 1.2),
                                 ("Rim", (-0.9, 0.2, 0.8), 45, 0.6)):
        ld = bpy.data.lights.new(PREFIX + "Render_" + nm, "AREA")
        ld.energy = watts
        ld.size = size
        lo = bpy.data.objects.new(PREFIX + "Render_" + nm, ld)
        lo.location = loc
        aim(lo)
        render.objects.link(lo)
    box("Render_Floor", render, m_floor, (0, 0.085, -0.186), (60, 60, 0.01), bevel=0,
        note="Floor for preview renders. DON'T export.")

    world = bpy.data.worlds.get(PREFIX + "World") or bpy.data.worlds.new(PREFIX + "World")
    try:
        world.use_nodes = True
    except Exception:
        pass
    world.node_tree.nodes.clear()
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.55, 0.58, 0.63, 1.0)
    bg.inputs[1].default_value = 0.45
    wo = world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(bg.outputs[0], wo.inputs[0])
    scene.world = world

    # Viewport niceties (only when run inside the Blender UI)
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"
                    space.clip_start = 0.001


if __name__ == "__main__":
    build()
    print("AF-7 Vanguard detailed model built.")
