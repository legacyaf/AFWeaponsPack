"""blender -b blender/afpk_dayz.blend --python blender/afpk_counter.py

The PeaceKeeper's round-counter textures: 0 to 21 and "--" (no magazine), drawn as orange seven-segment
digits on the baked display sheet (blender/textures/afpk_counter_co.png). AF_PeaceKeeper.c swaps the
display's texture (camo4) to the one for the rounds left.

The digits are placed by the display face's own UVs in LOD 1 (the face of the camo4 part that looks
out to the left), so they land on the face whatever the packing. Writes blender/textures/
afpk_count_<n>_co.png and afpk_count_none_co.png; convert them to .paa into source/AF_Weapons/afpk/data.
"""
import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
ORANGE = np.array((1.0, 0.46, 0.06))
#   aaa
#  f   b
#   ggg
#  e   c
#   ddd
SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
            "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}


def display_face():
    """The display's outer face in LOD 1: its UVs and its corners in the working frame (y forward, z up)."""
    ob = bpy.data.objects["PK_LOD_1"]
    me = ob.data
    gi = ob.vertex_groups["camo4"].index
    in_group = {v.index for v in me.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)}
    uv = me.uv_layers.active.data
    best = []
    for p in me.polygons:
        if not all(v in in_group for v in p.vertices):
            continue
        # LOD meshes are the working frame turned 90 degrees about Z: X = -y, Y = x, Z = z.
        if p.normal.y < -0.9:                  # facing working -x: out to the left
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                best.append(((-co.x, co.z), tuple(uv[li].uv)))
    if not best:
        raise RuntimeError("no outward display face found in camo4")
    return best


def fit(pairs):
    """Affine map working (y, z) -> uv, least squares."""
    a = np.array([[y, z, 1.0] for (y, z), _ in pairs])
    b = np.array([uvv for _, uvv in pairs])
    m, *_ = np.linalg.lstsq(a, b, rcond=None)
    return m                                   # uv = [y z 1] @ m


def seg_mask(ch, h, v):
    """Pixels (h, v in 0..1 across one digit cell, v up) lit for character ch."""
    t = 0.16                                   # stroke thickness, of the cell height
    w = 0.62                                   # digit width, of the cell
    x0, x1 = (1 - w) / 2, (1 + w) / 2
    lit = np.zeros(h.shape, bool)
    for s in SEGMENTS.get(ch, ""):
        if s == "a":
            m = (h > x0 + t * 0.3) & (h < x1 - t * 0.3) & (v > 1 - t) & (v <= 1.0)
        elif s == "g":
            m = (h > x0 + t * 0.3) & (h < x1 - t * 0.3) & (abs(v - 0.5) < t / 2)
        elif s == "d":
            m = (h > x0 + t * 0.3) & (h < x1 - t * 0.3) & (v >= 0.0) & (v < t)
        elif s in "fe":
            lo, hi = (0.5, 1.0) if s == "f" else (0.0, 0.5)
            m = (h > x0) & (h < x0 + t * 0.62) & (v > lo + t * 0.25) & (v < hi - t * 0.25)
        else:                                  # b, c
            lo, hi = (0.5, 1.0) if s == "b" else (0.0, 0.5)
            m = (h > x1 - t * 0.62) & (h < x1) & (v > lo + t * 0.25) & (v < hi - t * 0.25)
        lit |= m
    return lit


def main():
    pairs = display_face()
    m = fit(pairs)
    ys = [p[0][0] for p in pairs]
    zs = [p[0][1] for p in pairs]
    y0, y1, z0, z1 = min(ys), max(ys), min(zs), max(zs)
    base = bpy.data.images.load(os.path.join(TEX, "afpk_counter_co.png"))
    W, H = base.size
    px = np.array(base.pixels[:]).reshape(H, W, 4)
    # Pixels of the face: the uv rectangle's pixels, mapped back to (y, z) on the face.
    A = m[:2].T                                 # uv = A @ (y, z) + c
    c = m[2]
    Ainv = np.linalg.inv(A)
    uvs = np.array([uvv for _, uvv in pairs])
    u0, v0 = uvs.min(0)
    u1, v1 = uvs.max(0)
    i0, i1 = int(u0 * W) - 2, int(u1 * W) + 3
    j0, j1 = int(v0 * H) - 2, int(v1 * H) + 3
    ii, jj = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1))
    uvp = np.stack([(ii + 0.5) / W, (jj + 0.5) / H], -1) - c
    yz = uvp @ Ainv.T
    py, pz = yz[..., 0], yz[..., 1]
    # Two digit cells, read from the front of the rifle to the back (as seen from the left), with a margin.
    margin_y, margin_z = 0.0035, 0.0025
    cell_w = (y1 - y0 - 2 * margin_y) / 2
    cell_h = z1 - z0 - 2 * margin_z
    v = (pz - z0 - margin_z) / cell_h
    for n in list(range(0, 22)) + [None]:
        text = "--" if n is None else "%2d" % n
        img = px.copy()
        lit = np.zeros(py.shape, bool)
        for k, ch in enumerate(text):
            h = (y1 - margin_y - k * cell_w - py) / cell_w     # 0 at the cell's front edge
            inside = (h >= 0) & (h <= 1) & (v >= 0) & (v <= 1)
            lit |= inside & seg_mask(ch, h, v)
        block = img[j0:j1, i0:i1]
        block[..., :3][lit] = ORANGE
        name = "afpk_count_%s_co.png" % ("none" if n is None else str(n))
        out = bpy.data.images.new(name, W, H, alpha=True)
        out.pixels = img.ravel()
        out.filepath_raw = os.path.join(TEX, name)
        out.file_format = "PNG"
        out.save()
        bpy.data.images.remove(out)
        print("WROTE", name)


main()
