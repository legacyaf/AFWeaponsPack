"""blender -b --python afstg44_pad_maps.py
Edge-pads the StG 44 sheets of the 2026-11-23 bake in place (see af_pad.py). The exporter does
this itself from now on (EDGE_PAD); this applies it to that bake without another hour of baking.
Run once: after padding no texel is black, so a second run finds nothing to fill."""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import af_pad

T = os.path.join(HERE, "textures")
for base in ("afstg44_body", "afstg44_wood", "afstg44_mag", "afzf4"):
    valid = None
    for suffix in ("co", "gold_co", "smdi", "gold_smdi", "as"):
        path = os.path.join(T, "%s_%s.png" % (base, suffix))
        if not os.path.exists(path):
            continue
        im = bpy.data.images.load(path)
        w, h = im.size
        a = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)
        if valid is None:
            valid = a[..., :3].max(-1) > 0.0
            print("PAD %s unused %.1f%%" % (base, 100 * (1 - valid.mean())))
        out = af_pad.pad(a, valid)
        out[..., 3] = 1
        assert np.array_equal(out[valid], a[valid])
        im.pixels.foreach_set(out.ravel())
        im.filepath_raw = path
        im.file_format = "PNG"
        im.save()
        print("PAD wrote", os.path.basename(path))
