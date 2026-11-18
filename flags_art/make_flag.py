import bpy, numpy as np, sys
src, dst = sys.argv[sys.argv.index("--")+1:]
img = bpy.data.images.load(src)
w, h = img.size
a = np.empty(w*h*4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4)[::-1].copy()   # top row first
print("SIZE", w, h)
sx, sy = w / 2000.0, h / 1500.0
# number plate: blur it out (the flag is seen by everyone on the server)
x0, x1, y0, y1 = int(596*sx), int(668*sx), int(800*sy), int(862*sy)
a[y0:y1, x0:x1, :3] = a[y0:y1, x0:x1, :3].mean(axis=(0, 1))
# 2:1 crop holding the jet and the whole truck
cx0, cx1, cy0 = int(110*sx), int(1910*sx), int(165*sy)
cw = cx1 - cx0; ch = cw // 2
c = a[cy0:cy0+ch, cx0:cx1].copy()
# a little more punch, and a soft dark edge so it reads as printed cloth
rgb = c[..., :3]
rgb = np.clip((rgb - 0.5) * 1.08 + 0.5, 0, 1)
yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
d = np.sqrt(((xx / cw - 0.5) * 2) ** 2 + ((yy / ch - 0.5) * 2) ** 2)
vig = 1.0 - 0.22 * np.clip((d - 0.75) / 0.65, 0, 1) ** 1.5
c[..., :3] = rgb * vig[..., None]; c[..., 3] = 1.0
out = bpy.data.images.new("flag", cw, ch, alpha=False)
out.pixels.foreach_set(c[::-1].ravel()); out.scale(1024, 512)
out.filepath_raw = dst; out.file_format = "PNG"; out.save()
print("SAVED", dst, cw, ch)
