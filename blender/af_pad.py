"""Edge padding for baked texture sheets ("push-pull" fill).

The texels no face uses are black in a colour map. The game's smaller mip levels average them
into the edges of the UV islands, which shows as dark seam lines at a distance. pad() fills
every unused texel with the colour of the nearest islands, so each mip level averages like
with like. Used texels are not changed."""
import numpy as np


def pad(img, valid):
    """img: (H, W, C) float array, H and W powers of two. valid: (H, W) bool, True on used texels."""
    w = valid.astype(np.float32)
    c = img.astype(np.float32) * w[..., None]
    levels = [(c, w)]
    while c.shape[0] > 1 and c.shape[1] > 1:
        c = c[0::2, 0::2] + c[1::2, 0::2] + c[0::2, 1::2] + c[1::2, 1::2]
        w = w[0::2, 0::2] + w[1::2, 0::2] + w[0::2, 1::2] + w[1::2, 1::2]
        levels.append((c, w))
    c, w = levels[-1]
    fill = c / np.maximum(w, 1e-6)[..., None]
    for c, w in reversed(levels[:-1]):
        up = np.repeat(np.repeat(fill, 2, axis=0), 2, axis=1)
        fill = np.where((w > 0)[..., None], c / np.maximum(w, 1e-6)[..., None], up)
    out = np.where(valid[..., None], img, fill)
    return out.astype(img.dtype)
