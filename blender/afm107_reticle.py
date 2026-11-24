"""blender -b --python afm107_reticle.py -- <out folder>

The AF M107A1 scope's reticle, drawn from scratch (no game or scope maker's reticle is copied):

- thin black crosshair lines with heavy black posts towards the edge;
- a red illuminated outline round the thin centre lines and a small red centre dot;
- holdover marks below the centre for 300 to 1000 m, each labelled in hundreds of metres;
- mil hash marks along the horizontal line.

Writes:
  afm107_reticle_ca.png  the reticle alone on a transparent background (becomes the game's _ca.paa)
  m107_reticle_preview.png  the reticle over a plain landscape inside the scope's round view, with the
                            range readout as it will appear in game (the number comes from a script)
"""
import os
import sys

import bpy
import numpy as np

N = 1024
RED = (0.95, 0.06, 0.04)
BLACK = (0.0, 0.0, 0.0)

# 5 x 7 bitmap glyphs for the labels and the range readout.
GLYPHS = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10101", "10101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    " ": ["00000"] * 7,
}


def blank(c=0.0, a=0.0):
    img = np.zeros((N, N, 4), dtype=np.float32)
    img[..., :3] = c
    img[..., 3] = a
    return img


def paint(img, mask, rgb, alpha=1.0):
    m = np.clip(mask, 0, 1)[..., None] * alpha
    img[..., :3] = img[..., :3] * (1 - m) + np.array(rgb, dtype=np.float32) * m
    img[..., 3:] = np.maximum(img[..., 3:], m)


yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
C = (N - 1) / 2.0
X, Yv = xx - C, C - yy                    # centred, y up


def rect(x0, x1, y0, y1, soft=0.8):
    """Anti-aliased rectangle in centred pixel coordinates."""
    def edge(v, a, b):
        return np.clip(v - a + soft, 0, 1) * np.clip(b - v + soft, 0, 1)
    return edge(X, x0, x1) * edge(Yv, y0, y1)


def disc(cx, cy, r):
    return np.clip(r - np.hypot(X - cx, Yv - cy) + 0.8, 0, 1)


def text(img, s, x, y, scale, rgb):
    """Bitmap text with its top-left corner at centred coords (x, y)."""
    cx = x
    for ch in s:
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    paint(img, rect(cx + c * scale, cx + (c + 1) * scale, y - (r + 1) * scale, y - r * scale, 0.5), rgb)
        cx += 6 * scale


def reticle():
    img = blank()
    thin, post = 1.6, 7.0
    gap = 60.0                            # thin lines run this far from the centre ...
    reach = 300.0                         # ... then the heavy posts start, out to the edge
    # red illuminated outline round the thin lines (drawn first, wider, under the black)
    for a in (rect(-reach, reach, -thin - 2.4, thin + 2.4), rect(-thin - 2.4, thin + 2.4, -reach, reach)):
        paint(img, a, RED, 0.9)
    paint(img, rect(-reach, reach, -thin, thin), BLACK)
    paint(img, rect(-thin, thin, -reach, reach), BLACK)
    for x0, x1, y0, y1 in ((reach, 520, -post, post), (-520, -reach, -post, post), (-post, post, reach, 520),
                           (-post, post, -520, -reach)):
        paint(img, rect(x0, x1, y0, y1), BLACK)
    # centre: clear gap with a red dot
    paint(img, disc(0, 0, 4.0), RED)
    # mil hashes along the horizontal line, every 30 px (= 1 mil at the reticle's scale)
    for k in range(1, 10):
        for s in (-1, 1):
            h = 9.0 if k % 5 == 0 else 5.5
            paint(img, rect(s * k * 30 - 1.0, s * k * 30 + 1.0, -h, h), BLACK)
    # holdover marks below the centre for 300 .. 1000 m, labelled in hundreds of metres
    drops = {3: 14, 4: 30, 5: 50, 6: 76, 7: 108, 8: 146, 9: 192, 10: 246}
    for hundreds, dy in drops.items():
        w = 10 + hundreds * 2.2
        paint(img, rect(-w, w, -dy - 1.2, -dy + 1.2), BLACK)
        paint(img, rect(-w - 1.8, w + 1.8, -dy - 3.0, -dy + 3.0), RED, 0.55)
        text(img, str(hundreds), w + 6, -dy + 7, 2, BLACK)
    # The round view: opaque black outside a circle with a soft dark rim (the scope tube), because the
    # game's own optics mask does not draw under a scripted view. The HUD fills the screen's sides black.
    r = np.hypot(X, Yv)
    edge = np.clip((r - 0.455 * N) / (0.035 * N), 0, 1)
    paint(img, edge, BLACK)
    return img


def black():
    img = blank(0.0, 1.0)
    return img


def preview(ret):
    img = blank(0.0, 1.0)
    sky = np.clip(0.55 + Yv / (N * 1.4), 0, 1)
    land = Yv < -40 + 25 * np.sin(X / 90.0)
    img[..., 0] = np.where(land, 0.20 + 0.04 * np.sin(X / 13.0), 0.45 * sky + 0.20)
    img[..., 1] = np.where(land, 0.24 + 0.03 * np.sin(Yv / 9.0), 0.60 * sky + 0.25)
    img[..., 2] = np.where(land, 0.14, 0.85 * sky + 0.10)
    a = ret[..., 3:]
    img[..., :3] = img[..., :3] * (1 - a) + ret[..., :3] * a
    vign = np.clip((np.hypot(X, Yv) - 455) / 40.0, 0, 1)          # round view, dark tube edge
    img[..., :3] *= (1 - vign)[..., None]
    # range readout, bottom of the view: red, as the script will draw it
    paint(img, rect(-96, 96, -436, -394), (0.02, 0.0, 0.0), 0.65)
    text(img, "RNG 0350m", -88, -400, 3, RED)
    text(img, "6x", 380, 420, 3, RED)
    img[..., 3] = 1.0
    return img


def save(img, path):
    im = bpy.data.images.new(os.path.basename(path), N, N, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(img[::-1]).ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    print("SAVED", path)


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(os.path.abspath(__file__))
    ret = reticle()
    save(ret, os.path.join(out, "afm107_reticle_ca.png"))
    save(black(), os.path.join(out, "afm107_black_ca.png"))
    save(preview(ret), os.path.join(out, "m107_reticle_preview.png"))
