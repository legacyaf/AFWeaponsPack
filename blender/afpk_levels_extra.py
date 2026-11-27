"""blender -b --factory-startup --python blender/afpk_levels_extra.py

The PeaceKeeper's level steps that afstg44_levels.py does not cover, run once after a bake on the
sheets in blender/textures (afpk_after_bake.py runs it):

- Stock: its black parts are scaled to a colour median of 0.10, like the rifle's; the orange trim
  (coloured texels) is left alone.
- Gold sights: the colour is scaled to a deep gold (median 0.80, 0.48, 0.07) and the specular and
  gloss are raised to a strong, tight highlight (medians 0.93 and 0.90, half the baked variation
  kept). Tuned in game on 2026-11-27 with the gold material (afpk_gold.rvmat).
"""
import os

import bpy
import numpy as np

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")


def load(name):
    im = bpy.data.images.load(os.path.join(TEX, name), check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    return im, a.reshape(-1, 4)


def store(im, a):
    im.pixels.foreach_set(a.ravel())
    im.save()


im, a = load("afpk_stock_co.png")
rgb = a[:, :3]
chroma = rgb.max(1) - rgb.min(1)
lum = rgb.mean(1)
neutral = (chroma < 0.06) & (lum > 0.003)
k = 0.10 / np.median(lum[neutral])
rgb[neutral] *= k
store(im, a)
print("AFPK levels: stock scaled by %.3f, neutral median %.3f" % (k, float(np.median(rgb[neutral].mean(1)))))

im, a = load("afpk_gold_co.png")
used = a[:, :3].mean(1) > 0.003
med = np.median(a[used, :3], axis=0)
a[:, :3] = np.clip(a[:, :3] * (np.array((0.80, 0.48, 0.07), np.float32) / med), 0, 1)
store(im, a)
print("AFPK levels: gold colour", np.round(med, 3), "->", np.round(np.median(a[used, :3], axis=0), 3))

im, a = load("afpk_gold_smdi.png")
for ch, target in ((1, 0.93), (2, 0.90)):
    v = a[:, ch]
    a[:, ch] = np.clip(target + (v - np.median(v[used])) * 0.5, 0, 1)
store(im, a)
print("AFPK levels: gold specular/gloss medians", np.round(np.median(a[used, 1:3], axis=0), 3))
