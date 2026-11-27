"""blender -b blender/afpk_dayz.blend --python blender/afpk_finish_pass.py [-- sheet ...]

The PeaceKeeper's finish pass (owner 2026-11-27: "pro grade"). No bake: it works on the baked sheets,
using afpk_texmap to know where each texel sits on the rifle. Reads the sheets as they stand after
the bake and the levels pass from blender/textures/afpk_prefinish (made from blender/textures the
first time; delete that folder after a new bake and levels pass) and writes blender/textures. Run it
as often as needed: it always starts from the prefinish copy.

1. Polymer (lower, grip, stock): the baked shine was almost one value (specular 0.04 to 0.07), so the
   parts read as flat black slabs. They get a satin spread: broad patches polished by handling,
   rubbed edges, duller hollows.
2. Stipple: a grid of small raised points on the grip's sides, front and back and on the butt pad,
   written into the normal map, with their tops a little rubbed.
3. Markings on the lower receiver, engraved and paint-filled as on service rifles: the fire-mode
   marks by the selector on both sides (S, 1, 3, A), the model name, calibre and a serial on the
   left of the magazine well, the calibre on the right. Our own names only.
4. Wear by use, on every sheet: edges rubbed to a dull grey where hands, magazines and gear touch
   (rail edges, magazine well mouth, charging handle, ejection port, muzzle, grip, butt), faint
   scuffs along the flats there, a little dust in the hollows. Light: dusty, not bright metal lines.
The orange trim, the red tip, the gold sights and the counter are not touched.
"""
import os
import shutil
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import af_pad  # noqa: E402
import afpk_texmap as tm  # noqa: E402

TEX = os.path.join(HERE, "textures")
SRC = os.path.join(TEX, "afpk_prefinish")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ALL = ("afpk_body", "afpk_front", "afpk_lower", "afpk_parts", "afpk_stock")
SHEETS = [a for a in ARGS if a in ALL] or list(ALL)
SUFFIXES = ("co", "smdi", "nohq", "as")
POLYMER_PARTS = ("Lower", "Grip", "GripCap", "MagFlare", "TriggerGuard", "ChargingKnob", "StockBody", "CheekRiser",
                 "ButtPad")
SKIP_PARTS = ("TrimL", "TrimR", "FrontPostTip", "StockTrim", "CounterBezel")     # painted or lit: left as baked


# ----------------------------------------------------------------------------------- images

def load(folder, name):
    im = bpy.data.images.load(os.path.join(folder, name), check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)


def save(name, a, colourspace):
    h, w = a.shape[:2]
    im = bpy.data.images.new("afpk_tmp_" + name, w, h, alpha=True, float_buffer=False)
    im.colorspace_settings.name = colourspace
    im.pixels.foreach_set(np.ascontiguousarray(a, dtype=np.float32).ravel())
    im.filepath_raw = os.path.join(TEX, name)
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def blur(a, r):
    """Box blur of a 2D array, radius r texels, twice (close to a Gaussian)."""
    for _ in range(2):
        for axis in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if k == axis else (0, 0) for k in (0, 1)], mode="edge"), axis=axis, dtype=np.float64)
            n = a.shape[axis]
            hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
            lo = np.take(c, np.arange(0, n), axis=axis)
            a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ----------------------------------------------------------------------------------- noise

def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 362437) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 65535.0


def noise(p, scale, seed=0):
    """Value noise in 0..1 at points p (N, 3), `scale` cells per metre per axis (a number or three)."""
    out = np.empty(len(p), dtype=np.float32)
    sc = np.broadcast_to(np.asarray(scale, dtype=np.float64), (3,))
    for a in range(0, len(p), 1500000):
        q = p[a:a + 1500000].astype(np.float64) * sc + 1000.0
        i = np.floor(q).astype(np.int64)
        f = (q - i).astype(np.float32)
        f = f * f * (3.0 - 2.0 * f)
        acc = np.zeros(len(q), dtype=np.float32)
        for dx in (0, 1):
            wx = f[:, 0] if dx else 1.0 - f[:, 0]
            for dy in (0, 1):
                wy = f[:, 1] if dy else 1.0 - f[:, 1]
                for dz in (0, 1):
                    wz = f[:, 2] if dz else 1.0 - f[:, 2]
                    acc += wx * wy * wz * _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
        out[a:a + 1500000] = acc
    return out


def fbm(p, scale, seed=0, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * noise(p, np.asarray(scale) * (2.0 ** o), seed + 17 * o)
        norm += amp
        amp *= 0.5
    return total / norm


# ----------------------------------------------------------------------------------- where things are

# Working frame: x right, y forward (muzzle +), z up. ((centre), (half sizes), strength): where the rifle is
# handled and knocked. Soft-edged boxes; the strongest one at a point counts.
RIFLE_ZONES = (
    ((0.0, 0.10, 0.130), (0.030, 0.290, 0.008), 0.80),      # top rail, its whole length: optics, slings, gear
    ((0.0, 0.058, -0.004), (0.030, 0.060, 0.016), 1.00),    # magazine well mouth: magazines going in
    ((0.0, 0.058, 0.030), (0.030, 0.055, 0.030), 0.55),     # magazine well sides: the supporting hand
    ((0.0, 0.50, 0.089), (0.020, 0.050, 0.020), 0.90),      # muzzle brake
    ((-0.030, 0.2415, 0.1125), (0.016, 0.070, 0.014), 0.90),  # charging handle and its slot (left)
    ((0.026, 0.030, 0.108), (0.008, 0.050, 0.016), 0.85),   # ejection port and brass deflector (right)
    ((0.0, -0.105, -0.010), (0.030, 0.050, 0.075), 0.75),   # pistol grip
    ((0.0, -0.045, 0.010), (0.020, 0.050, 0.022), 0.70),    # trigger guard
    ((0.0, 0.250, 0.062), (0.032, 0.110, 0.022), 0.75),     # handguard, side and bottom rails: the forward hand
    ((0.0, -0.150, 0.095), (0.030, 0.014, 0.035), 0.70),    # rear of the receiver, at the stock
    ((0.0, -0.081, 0.063), (0.032, 0.016, 0.014), 0.80),    # selector, both sides: the thumb
)
# The stock, in its own frame as exported: x across, y up, z back (the butt at +z).
STOCK_ZONES = (
    ((0.0, 0.0, 0.150), (0.030, 0.085, 0.022), 1.00),       # butt pad: set down on it, shouldered
    ((0.0, 0.055, 0.020), (0.030, 0.016, 0.110), 0.85),     # comb and cheek riser: the cheek
    ((0.0, -0.065, 0.040), (0.030, 0.018, 0.110), 0.70),    # toe line
    ((0.0, 0.0, -0.110), (0.030, 0.050, 0.020), 0.60),      # hinge end
)
BASE_EXPOSURE = 0.30


def exposure(pos, zones):
    """0..1: how much use a point sees."""
    e = np.full(len(pos), BASE_EXPOSURE, dtype=np.float32)
    for c, h, s in zones:
        d = np.abs(pos - np.asarray(c, dtype=np.float32)) / np.asarray(h, dtype=np.float32)
        box = 1.0 - smooth(d.max(axis=1), 0.75, 1.25)
        e = np.maximum(e, BASE_EXPOSURE + (s - BASE_EXPOSURE) * box)
    return e


# ----------------------------------------------------------------------------------- markings

# Stroke glyphs, 4 wide and 6 tall. Each glyph is a list of polylines.
_O = [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]
GLYPHS = {
    "A": [[(0, 0), (2, 6), (4, 0)], [(0.8, 2.2), (3.2, 2.2)]],
    "C": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "D": [[(0, 0), (0, 6), (2.6, 6), (4, 4.6), (4, 1.4), (2.6, 0), (0, 0)]],
    "E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3.1), (3, 3.1)]],
    "F": [[(4, 6), (0, 6), (0, 0)], [(0, 3.1), (3, 3.1)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 6), (0, 2.6)], [(1.5, 3.7), (4, 0)]],
    "L": [[(0, 6), (0, 0), (4, 0)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "O": [_O],
    "P": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 3.8), (3, 2.8), (0, 2.8)]],
    "R": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 3.8), (3, 2.8), (0, 2.8)], [(2.2, 2.8), (4, 0)]],
    "S": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3.1), (3, 2.9), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "T": [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    "X": [[(0, 0), (4, 6)], [(0, 6), (4, 0)]],
    "0": [_O],
    "1": [[(1, 5), (2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "2": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 3.8), (0, 0), (4, 0)]],
    "3": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3.1), (1.5, 3.1)], [(3, 3.1), (4, 2.2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "5": [[(4, 6), (0, 6), (0, 3.4), (3, 3.4), (4, 2.4), (4, 1), (3, 0), (0, 0)]],
    "6": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2.4), (3, 3.4), (0, 3.4)]],
    "7": [[(0, 6), (4, 6), (1.5, 0)]],
    ".": [[(1.8, 0), (2.2, 0), (2.2, 0.4), (1.8, 0.4), (1.8, 0)]],
    "-": [[(0.8, 3), (3.2, 3)]],
    " ": [],
}
# (text, y of the first letter, z of the baseline, letter height): on the lower receiver, read from that side,
# inside the recessed panels on the magazine well (y 0.021 to 0.095, z 0.004 to 0.038).
# Left side: the text runs towards -y (the muzzle is to the reader's left). Right side: towards +y.
SELECTOR = (-0.081, 0.063)                      # the selector's hub (y, z)
MARKS_LEFT = [
    ("AF PEACEKEEPER", 0.0915, 0.0300, 0.0042),
    ("CAL 7.62X51", 0.0915, 0.0215, 0.0032),
    ("SER AF 001127", 0.0915, 0.0145, 0.0028),
]
MARKS_RIGHT = [
    ("CAL 7.62X51", 0.0245, 0.0215, 0.0032),
]
# Fire-mode marks on an arc below the selector (angle from forward, down is negative), both sides.
MODE_MARKS = (("S", -152.0), ("1", -112.0), ("3", -68.0), ("A", -28.0))
MODE_RADIUS, MODE_HEIGHT = 0.0165, 0.0030
PAINT = np.array((0.62, 0.62, 0.60), dtype=np.float32)       # paint fill, a little dirty
ENGRAVE_DEPTH = 0.00012


def _strokes(side):
    """Line segments ((y0, z0), (y1, z1), half width) of every mark on one side of the lower."""
    segs = []

    def write(text, y_start, z_base, height, centred=False):
        size = height / 6.0
        adv = 5.6 * size
        direction = 1.0 if side > 0 else -1.0
        if centred:
            y_start = y_start - direction * (2.0 * size)
        for k, ch in enumerate(text):
            for poly in GLYPHS[ch]:
                pts = [(y_start + direction * (k * adv + gx * size), z_base + gz * size) for gx, gz in poly]
                for a, b in zip(pts, pts[1:]):
                    segs.append((a, b, 0.085 * height))

    for text, y, z, h in (MARKS_RIGHT if side > 0 else MARKS_LEFT):
        write(text, y, z, h)
    for ch, ang in MODE_MARKS:
        a = np.radians(ang)
        write(ch, SELECTOR[0] + MODE_RADIUS * np.cos(a), SELECTOR[1] + MODE_RADIUS * np.sin(a) - MODE_HEIGHT / 2,
              MODE_HEIGHT, centred=True)
    return segs


def markings(sm, co, smdi, nohq):
    """Engraved, paint-filled marks on the flat sides of the lower receiver."""
    nrm = sm.per_texel(sm.normal)
    lower = sm.part_mask("Lower")
    done = 0
    for side in (-1, 1):
        face = lower & (nrm[..., 0] * side > 0.92)
        if not face.any():
            continue
        for (a, b, hw) in _strokes(side):
            a, b = np.asarray(a), np.asarray(b)
            lo, hi = np.minimum(a, b) - 3 * hw, np.maximum(a, b) + 3 * hw
            pos = sm.pos
            m = face & (pos[..., 1] > lo[0]) & (pos[..., 1] < hi[0]) & (pos[..., 2] > lo[1]) & (pos[..., 2] < hi[1])
            if not m.any():
                continue
            q = pos[m][:, 1:3].astype(np.float64)
            ab = b - a
            t = np.clip(((q - a) @ ab) / max(ab @ ab, 1e-18), 0.0, 1.0)
            near = a + t[:, None] * ab
            delta = q - near
            dist = np.linalg.norm(delta, axis=1)
            fill = (1.0 - smooth(dist, hw * 0.75, hw * 1.15)).astype(np.float32)
            # A shallow V groove: the wall slopes down towards the stroke's centre line.
            wall = ((dist > hw * 0.15) & (dist < hw * 1.3)).astype(np.float32)
            slope = ENGRAVE_DEPTH / hw * wall                    # height rises going outwards
            grad = np.zeros((len(q), 3), dtype=np.float32)
            grad[:, 1:3] = (delta / np.maximum(dist, 1e-9)[:, None] * slope[:, None]).astype(np.float32)
            _add_slope(sm, nohq, m, grad)
            c = co[m]
            c[:, :3] = c[:, :3] * (1.0 - fill[:, None]) + PAINT * fill[:, None]
            co[m] = c
            s = smdi[m]
            s[:, 1] = s[:, 1] * (1.0 - fill) + 0.05 * fill      # paint: dull
            s[:, 2] = s[:, 2] * (1.0 - fill) + 0.25 * fill
            smdi[m] = s
            done += 1
    return done


def _add_slope(sm, nohq, m, grad):
    """Tilt the normal map on texels m for a height field whose gradient (3D, per texel, metres per metre)
    is `grad`. The map is DirectX style: red along +u, green along -v."""
    tri = sm.tri[m]
    st = (grad * sm.du[tri]).sum(axis=1)
    sb = (grad * sm.dv[tri]).sum(axis=1)
    n = nohq[m][:, :3] * 2.0 - 1.0
    n[:, 1] = -n[:, 1]                              # to +v up
    nz = np.maximum(n[:, 2], 0.2)
    n[:, 0] = n[:, 0] / nz - st
    n[:, 1] = n[:, 1] / nz - sb
    n[:, 2] = 1.0
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    n[:, 1] = -n[:, 1]
    out = nohq[m]
    out[:, :3] = n * 0.5 + 0.5
    nohq[m] = out


# ----------------------------------------------------------------------------------- stipple

STIPPLE_PITCH = 0.0016          # centre to centre
STIPPLE_RADIUS = 0.00058
STIPPLE_HEIGHT = 0.00022


def stipple(sm, co, smdi, nohq, amb, where):
    """Raised points on a triangular grid, laid out in the plane each face mostly lies in."""
    if not where.any():
        return 0
    pos = sm.pos[where].astype(np.float64)
    nrm = sm.per_texel(sm.normal)[where]
    axis = np.abs(nrm).argmax(axis=1)                         # the axis the face looks along
    ia = np.where(axis == 0, 1, 0)                            # the two axes of its plane
    ib = np.where(axis == 2, 1, 2)
    idx = np.arange(len(pos))
    a, b = pos[idx, ia], pos[idx, ib]
    row = np.round(b / (STIPPLE_PITCH * 0.866))
    best = np.full(len(pos), 1e9)
    da, db = np.zeros(len(pos)), np.zeros(len(pos))
    for dr in (-1, 0, 1):
        r = row + dr
        cb = r * STIPPLE_PITCH * 0.866
        off = np.where(np.mod(r, 2) == 0, 0.0, 0.5) * STIPPLE_PITCH
        ca = np.round((a - off) / STIPPLE_PITCH) * STIPPLE_PITCH + off
        d = np.hypot(a - ca, b - cb)
        take = d < best
        best = np.where(take, d, best)
        da = np.where(take, a - ca, da)
        db = np.where(take, b - cb, db)
    t = np.clip(best / STIPPLE_RADIUS, 0.0, 1.0)
    height = (1.0 - t * t) ** 2                               # 1 on the point's top, 0 between points
    dh = -4.0 * t * (1.0 - t * t) / STIPPLE_RADIUS * STIPPLE_HEIGHT     # d(height)/d(distance)
    grad = np.zeros((len(pos), 3), dtype=np.float32)
    inv = 1.0 / np.maximum(best, 1e-9)
    grad[idx, ia] = (dh * da * inv).astype(np.float32)
    grad[idx, ib] = (dh * db * inv).astype(np.float32)
    _add_slope(sm, nohq, where, grad)
    h = height.astype(np.float32)
    c = co[where]
    c[:, :3] *= (0.86 + 0.26 * h)[:, None]                    # tops catch light and rub, the gaps hold dirt
    co[where] = c
    s = smdi[where]
    s[:, 1] = np.clip(s[:, 1] * (0.75 + 0.9 * h), 0, 1)
    s[:, 2] = np.clip(s[:, 2] * (0.80 + 0.5 * h), 0, 1)
    smdi[where] = s
    am = amb[where]
    am[:, 1] = np.clip(am[:, 1] * (0.80 + 0.20 * h), 0, 1)
    amb[where] = am
    return int(where.sum())


# ----------------------------------------------------------------------------------- one sheet

def edges(nohq, mask):
    """0..1 where the bake rounded an edge: the tangent-space normal leans there."""
    n = nohq[..., :2] * 2.0 - 1.0
    lean = np.hypot(n[..., 0], n[..., 1])
    e = smooth(lean, 0.10, 0.38) * mask
    wide = blur(e, 3) / np.maximum(blur(mask.astype(np.float32), 3), 0.05)
    return np.clip(np.maximum(e, wide * 1.6), 0.0, 1.0) * mask


def stats(tag, a, m):
    v = a[m]
    return "%s %.3f/%.3f/%.3f" % (tag, *np.percentile(v, [5, 50, 95]))


def run(name):
    maps = {s: load(SRC, "%s_%s.png" % (name, s)) for s in SUFFIXES}
    co, smdi, nohq, amb = maps["co"], maps["smdi"], maps["nohq"], maps["as"]
    size = co.shape[0]
    sm = tm.sheet(name, size)
    mask = sm.mask
    stock = name == "afpk_stock"
    zones = STOCK_ZONES if stock else RIFLE_ZONES
    lum = lambda: co[..., :3].mean(axis=2)
    before = "%s | %s | %s" % (stats("colour", lum(), mask), stats("spec", smdi[..., 1], mask), stats("gloss", smdi[..., 2], mask))

    skip = sm.part_mask(*SKIP_PARTS)
    work = mask & ~skip
    polymer = sm.part_mask(*POLYMER_PARTS) & work
    metal = work & ~polymer
    P = sm.pos[work]
    expo = np.zeros(mask.shape, np.float32)
    expo[work] = exposure(P, zones)
    broad = np.zeros(mask.shape, np.float32)
    broad[work] = fbm(P, 28.0, seed=3)                          # patches a few centimetres across
    fine = np.zeros(mask.shape, np.float32)
    fine[work] = fbm(P, 420.0, seed=9, octaves=2)               # a couple of millimetres
    streak = np.zeros(mask.shape, np.float32)
    streak[work] = noise(P, (900.0, 55.0, 900.0), seed=5) * 0.65 + noise(P, (2200.0, 140.0, 2200.0), seed=6) * 0.35
    ao = np.clip((amb[..., 1] - 0.30) / 0.70, 0.0, 1.0)         # the exporter's AO_FLOOR is 0.30
    edge = edges(nohq, mask)

    # 1. Polymer: a satin spread.
    if polymer.any():
        handled = smooth(broad, 0.35, 0.75) * (0.35 + 0.65 * expo)
        spec = 0.035 + 0.060 * handled + 0.030 * (fine - 0.5) + 0.02 * (ao - 0.6)
        gloss = 0.22 + 0.20 * handled + 0.06 * (fine - 0.5)
        smdi[..., 1][polymer] = np.clip(spec, 0.015, 1.0)[polymer]
        smdi[..., 2][polymer] = np.clip(gloss, 0.10, 1.0)[polymer]
        # Moulded polymer is not one flat black either: a faint mottle.
        tone = (0.93 + 0.14 * broad + 0.08 * (fine - 0.5))[polymer]
        c = co[polymer]
        c[:, :3] *= tone[:, None]
        co[polymer] = c

    # 2. Stipple.
    nrm = sm.per_texel(sm.normal)
    grip = sm.part_mask("Grip") & (np.abs(nrm[..., 2]) < 0.75) & (sm.pos[..., 2] < 0.020) & (sm.pos[..., 2] > -0.074)
    pad = sm.part_mask("ButtPad") & (nrm[..., 2] > 0.6) if stock else np.zeros(mask.shape, bool)
    n_st = stipple(sm, co, smdi, nohq, amb, grip | pad)

    # 3. Markings.
    n_mk = markings(sm, co, smdi, nohq) if name == "afpk_lower" else 0

    # 4. Wear by use.
    rub = edge * (0.30 + 0.70 * expo) * (0.55 + 0.75 * fine)
    rub = smooth(rub, 0.22, 0.70)
    scuff = smooth(streak, 0.70, 0.88) * smooth(expo, 0.45, 0.85) * (0.4 + 0.6 * broad) * (1.0 - edge)
    dust = (1.0 - ao) * (0.5 + 0.5 * broad)
    for part, rub_rgb, rub_k, rub_spec, rub_gloss, scuff_k in (
            (metal, (0.30, 0.30, 0.31), 0.62, 0.42, 0.62, 0.060),      # anodised aluminium and steel: dull silver-grey
            (polymer, (0.150, 0.150, 0.150), 0.55, 0.16, 0.46, 0.035)):  # polymer: burnished, paler
        if not part.any():
            continue
        r = (rub * rub_k)[part]
        sc = scuff[part]
        d = dust[part]
        c = co[part]
        rgb = c[:, :3]
        rgb = rgb * (1.0 - r[:, None]) + np.asarray(rub_rgb, np.float32) * r[:, None]
        rgb = rgb + scuff_k * sc[:, None]
        rgb = rgb * (1.0 - 0.22 * d[:, None]) + np.asarray((0.105, 0.098, 0.085), np.float32) * (0.22 * d[:, None])
        c[:, :3] = np.clip(rgb, 0.0, 1.0)
        co[part] = c
        s = smdi[part]
        s[:, 1] = np.clip(s[:, 1] * (1.0 - r) + rub_spec * r + 0.05 * sc - 0.02 * d, 0.0, 1.0)
        s[:, 2] = np.clip(s[:, 2] * (1.0 - r) + rub_gloss * r + 0.04 * sc - 0.06 * d, 0.0, 1.0)
        smdi[part] = s

    after = "%s | %s | %s" % (stats("colour", lum(), mask), stats("spec", smdi[..., 1], mask), stats("gloss", smdi[..., 2], mask))
    print("AFPK finish %-11s before: %s" % (name, before))
    print("AFPK finish %-11s after:  %s" % (name, after))
    print("AFPK finish %-11s texel %.2f mm, stipple texels %d, mark strokes %d, rubbed %.1f%%, parts %s" % (
        name, float(np.median(sm.texel)) * 1000.0, n_st, n_mk, 100.0 * float((rub[work] > 0.3).mean()), ",".join(sm.parts)))
    save("%s_co.png" % name, af_pad.pad(co, mask), "sRGB")
    save("%s_smdi.png" % name, af_pad.pad(smdi, mask), "Non-Color")
    save("%s_as.png" % name, af_pad.pad(amb, mask), "Non-Color")
    save("%s_nohq.png" % name, nohq, "Non-Color")


def main():
    if not os.path.isdir(SRC):
        os.makedirs(SRC)
        for name in ALL:
            for s in SUFFIXES:
                shutil.copy2(os.path.join(TEX, "%s_%s.png" % (name, s)), SRC)
        print("AFPK finish: made", SRC)
    for name in SHEETS:
        run(name)


main()
