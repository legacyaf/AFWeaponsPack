"""blender -b --python afstg44_levels.py -- <source folder> [texture sets]

Levels pass on the StG 44's baked steel maps (owner's go-ahead, 2026-11-23). Reads the maps of the
last bake from <source folder> (the PNGs as committed in 79037a3) and writes the result into
blender/textures. No bake: the same surface, given the spread of shine and colour that the vanilla
AKM's maps have and ours did not. Measured on the AKM's maps (texels with colour above 0.03):
specular p5/p50/p95 0.00/0.18/0.95, gloss 0.43/0.62/0.90; ours were 0.075/0.114/0.180 and
0.44/0.59/0.76, which in game read as an even dark matte beside the AKM.

1. Specular. A shine score (specular and gloss, both ranked, dimmed by the ambient shadow) is
   mapped onto the AKM's spread: the bare and rubbed edges and the oily, polished patches the bake
   already marks get the high values, corners and dusty flats the low ones.
2. Gloss. The top half is stretched so the rubbed parts reach about 0.9; the lower half is kept.
3. Colour. The cavities are darkened by the ambient shadow; the median is then put back, so the
   overall brightness in sun stays as calibrated.
The wood and the gold skin are left as baked."""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = ARGS[0] if ARGS else OUT
# Further arguments name the texture sets (default: the StG 44's). The AF M107A1 uses the same
# pass: afm107_body afm107_mag afm107_scope. Run it once per bake: it writes over its source
# when <source folder> is blender/textures.
MATTE = "--matte" in ARGS
ARGS = [a for a in ARGS if a != "--matte"]
BASES = ARGS[1:] or ["afstg44_body", "afstg44_mag", "afzf4"]
AO_FLOOR = 0.30                      # as written by the exporter (afstg44_dayz_export: ex.AO_FLOOR)
# Target specular at these percentiles of the shine score (the AKM's spread, a little tempered at
# the very top: 0.80 rather than 0.95, as ours is a phosphate finish, not blued steel).
SPEC_PCT = (0, 5, 50, 80, 95, 100)
SPEC_VAL = (0.0, 0.03, 0.18, 0.34, 0.72, 0.80)
GLOSS_TOP = 0.90                     # where the 95th percentile of the gloss goes
# --matte: a ceramic coat (the AF M107A1's Cerakote) is matte; the AKM's spread made it read as polished
# grey steel in sunlight (in game 2026-11-23). Lower shine, worn edges still the brightest.
COLOUR_MEDIAN = None                 # None: keep the baked median
if MATTE:
    SPEC_VAL = (0.0, 0.02, 0.08, 0.14, 0.32, 0.45)
    GLOSS_TOP = 0.62
    # Darker coat (2026-11-24): at a median of 0.144 the Cerakote still read mid-grey in noon sun; the
    # owner's reference rifles are near-black. About 30% darker, the cavity contrast kept.
    COLOUR_MEDIAN = 0.10


def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    return im, a.reshape(h, w, 4)


def save(im, a, path):
    im.pixels.foreach_set(np.ascontiguousarray(np.clip(a, 0.0, 1.0)).ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()


def rank(x):
    """0..1 by rank (percentile of each texel)."""
    flat = x.ravel()
    order = np.argsort(flat, kind="stable")
    r = np.empty_like(order, dtype=np.float32)
    r[order] = np.linspace(0.0, 1.0, flat.size, dtype=np.float32)
    return r.reshape(x.shape)


def stats(tag, co, sm):
    v = co[..., :3].mean(-1)
    print("LEVELS %-28s colour p5/p50/p95 %.3f %.3f %.3f | spec %.3f %.3f %.3f | gloss %.3f %.3f %.3f" % (
        (tag,) + tuple(np.percentile(v, [5, 50, 95])) + tuple(np.percentile(sm[..., 1], [5, 50, 95]))
        + tuple(np.percentile(sm[..., 2], [5, 50, 95]))))


for base in BASES:
    im_co, co = load(os.path.join(SRC, base + "_co.png"))
    im_sm, sm = load(os.path.join(SRC, base + "_smdi.png"))
    _im_as, amb = load(os.path.join(SRC, base + "_as.png"))
    stats(base + " before", co, sm)
    ao = np.clip((amb[..., 1] - AO_FLOOR) / (1.0 - AO_FLOOR), 0.0, 1.0)

    # 1. Specular
    score = (0.55 * rank(sm[..., 1]) + 0.45 * rank(sm[..., 2])) * (0.35 + 0.65 * ao)
    pct = np.percentile(score, SPEC_PCT)
    sm[..., 1] = np.interp(score, pct, SPEC_VAL)

    # 2. Gloss: stretch the upper half
    g = sm[..., 2]
    g50, g95 = np.percentile(g, [50, 95])
    up = g > g50
    g[up] = g50 + (g[up] - g50) * (GLOSS_TOP - g50) / max(g95 - g50, 1e-3)
    sm[..., 2] = np.clip(g, 0.0, 1.0)

    # 3. Colour: mid-scale contrast, darker cavities, median kept
    rgb = co[..., :3]
    med = float(np.median(rgb.mean(-1)))
    # (A mid-scale contrast step, blurring the sheet, was tried and dropped: the blur crosses the
    # borders of the UV islands and left rectangular light patches on the receiver and housing.)
    rgb = rgb * (0.62 + 0.38 * ao)[..., None]
    rgb *= (COLOUR_MEDIAN or med) / max(float(np.median(rgb.mean(-1))), 1e-4)
    co[..., :3] = rgb

    stats(base + " after", co, sm)
    save(im_co, co, os.path.join(OUT, base + "_co.png"))
    save(im_sm, sm, os.path.join(OUT, base + "_smdi.png"))
print("LEVELS done")
