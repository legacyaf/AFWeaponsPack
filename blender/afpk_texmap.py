"""Where every texel of The PeaceKeeper's sheets sits on the rifle.

For a texture pass that works on the baked sheets (afpk_finish_pass.py) each texel has to know its
place on the model: wear belongs on the rail's edges, stipple on the grip, a marking on one flat of
the receiver. This module draws LOD 1's triangles into the UV square of each sheet and returns, per
texel, the triangle it belongs to and its position in the working frame (x right, y forward, z up,
metres; the frame afpk_detailed.py builds in). Per triangle it keeps the face normal, the two
directions in which u and v grow across the face (for writing into the tangent-space normal map)
and the source part's name.

Run inside Blender with blender/afpk_dayz.blend open (it holds PK_LOD_1 and PKS_LOD_1).
"""
import zlib

import bpy
import numpy as np


class SheetMap:
    """tri: (H, W) int32, -1 where no face covers the texel. pos: (H, W, 3) float32, working frame.
    Row 0 is the bottom row of the image, as in Blender's pixel order."""

    def __init__(self, size):
        self.size = size
        self.tri = np.full((size, size), -1, dtype=np.int32)
        self.pos = np.zeros((size, size, 3), dtype=np.float32)
        self.normal = None      # (T, 3) face normals, working frame
        self.du = None          # (T, 3) unit direction on the face in which u grows
        self.dv = None          # (T, 3) unit direction on the face in which v grows (image up)
        self.part = None        # (T,) index into self.parts
        self.parts = []         # part names (afpk_detailed object names without the prefix)
        self.texel = None       # (T,) metres per texel on that face

    @property
    def mask(self):
        return self.tri >= 0

    def per_texel(self, per_tri):
        """A per-triangle array spread over the sheet (texels without a face get the first triangle's value)."""
        return per_tri[np.clip(self.tri, 0, None)]

    def part_mask(self, *names):
        idx = [self.parts.index(n) for n in names if n in self.parts]
        if not idx:
            return np.zeros(self.tri.shape, bool)
        return self.mask & np.isin(self.per_texel(self.part), idx)


def _to_working(co, stock):
    """LOD meshes are the working frame turned 90 degrees about Z: X = -y, Y = x, Z = z. The stock's
    LOD is in the stock slot's frame (afpk_detailed.to_stock_frame: x across, y up the rifle, z back)."""
    co = np.asarray(co, dtype=np.float64)
    out = np.empty_like(co)
    out[:, 0] = co[:, 1]
    out[:, 1] = -co[:, 0]
    out[:, 2] = co[:, 2]
    return out


def build(object_name, material_index, size, part_names):
    """SheetMap of one sheet: the faces of `object_name` that use material slot `material_index`."""
    ob = bpy.data.objects[object_name]
    me = ob.data
    uv = me.uv_layers.active.data
    attr = me.attributes.get("af7_part")
    by_hash = {zlib.crc32(n.encode("utf-8")) & 0x7FFFFFFF: n for n in part_names}
    verts = _to_working([v.co for v in me.vertices], object_name.startswith("PKS_"))
    sm = SheetMap(size)
    normals, dus, dvs, parts, texels = [], [], [], [], []
    me.calc_loop_triangles()
    for lt in me.loop_triangles:
        p = me.polygons[lt.polygon_index]
        if p.material_index != material_index:
            continue
        P = verts[list(lt.vertices)]
        U = np.array([uv[li].uv[:] for li in lt.loops], dtype=np.float64) * size - 0.5     # texel centres at integers
        e1, e2 = P[1] - P[0], P[2] - P[0]
        n = np.cross(e1, e2)
        area = np.linalg.norm(n)
        d1, d2 = U[1] - U[0], U[2] - U[0]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        if area < 1e-14 or abs(det) < 1e-9:
            continue
        n /= area
        # Position is affine in (u, v) on the face: dP/du and dP/dv, per texel.
        dPdu = (e1 * d2[1] - e2 * d1[1]) / det
        dPdv = (e2 * d1[0] - e1 * d2[0]) / det
        tid = len(normals)
        # Blender's polygon normal decides the outward side (the triangle's winding in UV may be mirrored).
        pn = _to_working([p.normal], False)[0]
        if np.dot(pn, n) < 0:
            n = -n
        normals.append(n)
        lu, lv = np.linalg.norm(dPdu), np.linalg.norm(dPdv)
        dus.append(dPdu / max(lu, 1e-12))
        dvs.append(dPdv / max(lv, 1e-12))
        texels.append(0.5 * (lu + lv))
        name = by_hash.get(attr.data[lt.polygon_index].value, "?") if attr else "?"
        if name not in sm.parts:
            sm.parts.append(name)
        parts.append(sm.parts.index(name))
        # Rasterise, with a one-texel skirt so neighbouring faces leave no uncovered seam texels.
        x0, x1 = int(np.floor(U[:, 0].min())) - 1, int(np.ceil(U[:, 0].max())) + 1
        y0, y1 = int(np.floor(U[:, 1].min())) - 1, int(np.ceil(U[:, 1].max())) + 1
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        qx, qy = xs - U[0, 0], ys - U[0, 1]
        b1 = (qx * d2[1] - qy * d2[0]) / det
        b2 = (qy * d1[0] - qx * d1[1]) / det
        b0 = 1.0 - b1 - b2
        inside = (b0 >= 0) & (b1 >= 0) & (b2 >= 0)
        # The skirt: texels just outside, only where nothing has been written yet.
        tol = 1.2 / max(np.sqrt(abs(det)), 1e-6)
        near = (b0 >= -tol) & (b1 >= -tol) & (b2 >= -tol) & ~inside
        block_tri = sm.tri[y0:y1 + 1, x0:x1 + 1]
        write = inside | (near & (block_tri < 0))
        if not write.any():
            continue
        pos = P[0] + b1[..., None] * e1 + b2[..., None] * e2
        block_tri[write] = tid
        sm.pos[y0:y1 + 1, x0:x1 + 1][write] = pos[write]
    sm.normal = np.array(normals, dtype=np.float32)
    sm.du = np.array(dus, dtype=np.float32)
    sm.dv = np.array(dvs, dtype=np.float32)
    sm.part = np.array(parts, dtype=np.int32)
    sm.texel = np.array(texels, dtype=np.float32)
    return sm


def part_names():
    """Names of the source parts (objects PK_* / PKS_* that are not LODs, memory points or proxies)."""
    out = []
    for o in bpy.data.objects:
        for prefix in ("PKS_", "PK_"):
            if o.name.startswith(prefix):
                short = o.name[len(prefix):]
                if not short.startswith(("LOD_", "Mem_", "Proxy_")):
                    out.append(short)
                break
    return out


# sheet name -> (object, material slot)
SHEETS = {
    "afpk_body": ("PK_LOD_1", 0),
    "afpk_front": ("PK_LOD_1", 1),
    "afpk_lower": ("PK_LOD_1", 2),
    "afpk_parts": ("PK_LOD_1", 3),
    "afpk_counter": ("PK_LOD_1", 4),
    "afpk_gold": ("PK_LOD_1", 5),
    "afpk_stock": ("PKS_LOD_1", 0),
}


def sheet(name, size):
    ob, slot = SHEETS[name]
    return build(ob, slot, size, part_names())
