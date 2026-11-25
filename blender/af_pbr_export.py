"""Standard PBR texture set from the DayZ maps of an AF weapon, for portfolios and other engines.

  blender -b --factory-startup --python af_pbr_export.py -- <out folder> <texture set> [set ...]

For each set (blender/textures/<set>_co.png, _smdi.png, _nohq.png, _as.png) it writes:
  <set>_BaseColor.png      the colour map (sRGB)
  <set>_Roughness.png      1 - gloss (smdi blue)
  <set>_Metallic.png       from the specular (smdi green): bare and polished metal 1, coatings 0
  <set>_AO.png             ambient occlusion (as green)
  <set>_Normal_DirectX.png the tangent normal map as DayZ stores it (green down)
  <set>_Normal_OpenGL.png  green flipped (Blender, Unity)
"""
import os
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
OUT, SETS = args[0], args[1:]
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
os.makedirs(OUT, exist_ok=True)


def load(path, colour=False):
    im = bpy.data.images.load(path)
    if not colour:
        im.colorspace_settings.name = "Non-Color"
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)


def save(name, rgb, colour=False):
    h, w = rgb.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    if not colour:
        im.colorspace_settings.name = "Non-Color"
    a = np.ones((h, w, 4), dtype=np.float32)
    a[..., :3] = rgb if rgb.ndim == 3 else rgb[..., None]
    im.pixels.foreach_set(np.ascontiguousarray(np.clip(a, 0, 1)).ravel())
    im.filepath_raw = os.path.join(OUT, name + ".png")
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    print("PBR wrote", name)


for s in SETS:
    co = load(os.path.join(SRC, s + "_co.png"), colour=True)
    sm = load(os.path.join(SRC, s + "_smdi.png"))
    nh = load(os.path.join(SRC, s + "_nohq.png"))
    ao = load(os.path.join(SRC, s + "_as.png"))
    save(s + "_BaseColor", co[..., :3], colour=True)
    save(s + "_Roughness", 1.0 - sm[..., 2])
    save(s + "_Metallic", np.clip((sm[..., 1] - 0.10) / 0.50, 0.0, 1.0))
    save(s + "_AO", ao[..., 1])
    save(s + "_Normal_DirectX", nh[..., :3])
    gl = nh[..., :3].copy()
    gl[..., 1] = 1.0 - gl[..., 1]
    save(s + "_Normal_OpenGL", gl)
