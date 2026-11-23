"""blender -b --python afstg44_fix_holes.py

One-off repair of the 2026-11-23 bake: darkens the handguard's cooling holes in the baked body
colour maps. In that bake the handling and scratch layers were painted over the holes, so they
came out mid grey (colour 0.067 against the steel's 0.118). afstg44_detailed.py now paints holes
last, so a fresh bake does not need this script. Running it twice darkens them twice: run once.

The holes are found in the bake itself: the only body texels with the metal set to 0 (specular
below the steel's 0.123) AND the gloss pulled right down (below 0.45). The gloss test matters:
the insides of the boolean cuts (ejection port, magazine well) also have low specular but keep a
high gloss, and must not be touched."""
import bpy
import numpy as np

T = "C:\\GithubRepo\\AFWeaponPack\\AFWeaponsPack-main\\blender\\textures\\"


def load(name):
    im = bpy.data.images.load(T + name)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    return im, a.reshape(h, w, 4)


_im, sm = load("afstg44_body_smdi.png")
m = np.clip((0.123 - sm[..., 1]) / (0.123 - 0.060), 0.0, 1.0) * np.clip((0.45 - sm[..., 2]) / 0.15, 0.0, 1.0)
print("HOLEFIX texels", int((m > 0.5).sum()))
for name in ("afstg44_body_co.png", "afstg44_body_gold_co.png"):
    im, co = load(name)
    before = float(np.median(co[..., :3].mean(-1)[m > 0.5]))
    co[..., :3] *= (1.0 - 0.85 * m)[..., None]
    im.pixels.foreach_set(co.ravel())
    im.filepath_raw = T + name
    im.file_format = "PNG"
    im.save()
    print("HOLEFIX", name, "hole colour %.3f -> %.3f" % (before, float(np.median(co[..., :3].mean(-1)[m > 0.5]))))
