"""Studio renders of an exported AF weapon (its game-ready LOD 1 with the baked maps), product-shot style.

  blender -b <weapon>_dayz.blend --python af_studio.py -- <out folder> <tag> <json {object: [set, ...]}> [samples]

A dark seamless backdrop (a curved cyclorama), a three-point setup of large soft area lights (key,
rim, fill) over a dim studio world, AgX colour, and these shots: hero three-quarter, side profile, rear
three-quarter, top, and close-ups with a shallow depth of field. Material slot k of each object shows
texture set k; the maps are read as the game reads them: colour x ambient, gloss to roughness,
specular as a metal/specular blend, the normal map with DayZ's green flipped.
Writes <tag>_studio_<shot>.png."""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT, TAG, OBJS = args[0], args[1], json.loads(args[2])
SAMPLES = int(args[3]) if len(args) > 3 else 256
ONLY = set(args[4].split(",")) if len(args) > 4 else None     # render only these shots (tests)
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures") + os.sep
sc = bpy.context.scene
for ob in sc.objects:
    ob.hide_render = ob.name not in OBJS


def material(base):
    m = bpy.data.materials.new("Studio_" + base)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N["Principled BSDF"]

    def tex(suffix, colour):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(T + base + suffix, check_existing=True)
        t.interpolation = "Cubic"
        if not colour:
            t.image.colorspace_settings.name = "Non-Color"
        return t
    co, nh, sm, ao = tex("_co.png", True), tex("_nohq.png", False), tex("_smdi.png", False), tex("_as.png", False)
    sep_ao = N.new("ShaderNodeSeparateColor")
    L.new(ao.outputs[0], sep_ao.inputs[0])
    mix = N.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    L.new(co.outputs[0], mix.inputs[6])
    L.new(sep_ao.outputs[1], mix.inputs[7])
    L.new(mix.outputs[2], bsdf.inputs["Base Color"])
    sep = N.new("ShaderNodeSeparateColor")
    L.new(sm.outputs[0], sep.inputs[0])
    rough = N.new("ShaderNodeMath")
    rough.operation = "SUBTRACT"
    rough.inputs[0].default_value = 1.0
    L.new(sep.outputs[2], rough.inputs[1])
    L.new(rough.outputs[0], bsdf.inputs["Roughness"])
    # DayZ's specular map: bright where the surface is bare or polished metal.
    metal = N.new("ShaderNodeMapRange")
    metal.inputs["From Min"].default_value = 0.10
    metal.inputs["From Max"].default_value = 0.60
    L.new(sep.outputs[1], metal.inputs["Value"])
    L.new(metal.outputs["Result"], bsdf.inputs["Metallic"])
    sn = N.new("ShaderNodeSeparateColor")
    L.new(nh.outputs[0], sn.inputs[0])
    flip = N.new("ShaderNodeMath")
    flip.operation = "SUBTRACT"
    flip.inputs[0].default_value = 1.0
    L.new(sn.outputs[1], flip.inputs[1])
    cb = N.new("ShaderNodeCombineColor")
    L.new(sn.outputs[0], cb.inputs[0])
    L.new(flip.outputs[0], cb.inputs[1])
    L.new(sn.outputs[2], cb.inputs[2])
    nm = N.new("ShaderNodeNormalMap")
    L.new(cb.outputs[0], nm.inputs["Color"])
    L.new(nm.outputs[0], bsdf.inputs["Normal"])
    return m


lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for name, sets in OBJS.items():
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("STUDIO missing", name)
        continue
    ob.hide_render = False
    for k in range(len(ob.data.materials)):
        ob.data.materials[k] = material(sets[min(k, len(sets) - 1)])
    for c in ob.bound_box:
        v = ob.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, v))
        hi = Vector(map(max, hi, v))
ctr, size = (lo + hi) / 2, hi - lo
ax = max(range(3), key=lambda i: size[i])
side = [i for i in range(3) if i not in (ax, 2)][0]
Lg = size[ax]


def vec(a, s, z):
    v = [0.0, 0.0, 0.0]
    v[ax], v[side], v[2] = a, s, z
    return Vector(v)


# Backdrop: a floor that curves up into a wall behind the weapon (no horizon line).
import bmesh
bm = bmesh.new()
floor_z = lo.z - 0.002
R, W, D = 0.6 * Lg, 6.0 * Lg, 3.0 * Lg
rows = []
for k in range(25):
    if k <= 8:
        sv, z = -D + k * (D / 8), floor_z            # flat floor towards the camera ... to the curve's start
    else:
        a = (k - 8) / 16 * math.pi / 2
        sv, z = R * math.sin(a), floor_z + R * (1 - math.cos(a))
    if k == 24:
        pass
    rows.append((sv, z))
rows.append((R, floor_z + 2.5 * Lg))
verts = []
for sv, z in rows:
    verts.append([bm.verts.new(ctr + vec(-W / 2, 0, 0) + vec(0, -sv - 0.3 * Lg, 0) + Vector((0, 0, z - ctr.z))),
                  bm.verts.new(ctr + vec(W / 2, 0, 0) + vec(0, -sv - 0.3 * Lg, 0) + Vector((0, 0, z - ctr.z)))])
for a, b in zip(verts, verts[1:]):
    bm.faces.new((a[0], a[1], b[1], b[0]))
me = bpy.data.meshes.new("StudioBackdrop")
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
back = bpy.data.objects.new("StudioBackdrop", me)
sc.collection.objects.link(back)
bmat = bpy.data.materials.new("StudioBackdrop")
bmat.use_nodes = True
bb = bmat.node_tree.nodes["Principled BSDF"]
bb.inputs["Base Color"].default_value = (0.018, 0.019, 0.021, 1)
bb.inputs["Roughness"].default_value = 0.55
me.materials.append(bmat)

# Lights: key (large soft box above front-left), rim (behind, opposite side), fill (low, front-right).


def area(name, loc, energy, size_m, colour=(1, 1, 1)):
    li = bpy.data.lights.new(name, "AREA")
    li.energy, li.size, li.color = energy, size_m, colour
    li.shape = "RECTANGLE"
    li.size_y = size_m * 0.5
    ob = bpy.data.objects.new(name, li)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (ctr - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


scale = Lg / 1.2
area("Key", ctr + vec(-0.35 * Lg, 0.85 * Lg, 0.95 * Lg), 95 * scale ** 2, 1.4 * Lg, (1.0, 0.97, 0.93))
area("Rim", ctr + vec(0.55 * Lg, -0.9 * Lg, 0.55 * Lg), 130 * scale ** 2, 0.9 * Lg, (0.85, 0.92, 1.0))
area("Fill", ctr + vec(0.5 * Lg, 1.1 * Lg, 0.05 * Lg), 18 * scale ** 2, 1.6 * Lg, (0.95, 0.97, 1.0))
area("Top", ctr + vec(0.0, 0.0, 1.4 * Lg), 25 * scale ** 2, 2.0 * Lg)
w = sc.world or bpy.data.worlds.new("Studio")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.020, 0.022, 0.026, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.35

cam = bpy.data.objects.new("StudioCam", bpy.data.cameras.new("StudioCam"))
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = "CYCLES"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 2400, 1350
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass


def shot(tag, loc, target, lens, dof=None):
    if ONLY and tag not in ONLY:
        return
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = dof is not None
    if dof:
        cam.data.dof.focus_distance = (target - loc).length
        cam.data.dof.aperture_fstop = dof
    sc.render.filepath = os.path.join(OUT, "%s_studio_%s.png" % (TAG, tag))
    bpy.ops.render.render(write_still=True)
    print("STUDIO rendered", sc.render.filepath)


aim = ctr + vec(0.0, 0.0, -0.05 * size[2])
shot("hero", ctr + vec(0.80 * Lg, 1.45 * Lg, 0.42 * Lg), aim, 60)
shot("side", ctr + vec(0.0, 2.2 * Lg, 0.04 * Lg), aim, 60)
shot("rear34", ctr + vec(-0.95 * Lg, 1.35 * Lg, 0.48 * Lg), aim, 60)
shot("top", ctr + vec(0.0, 0.30 * Lg, 2.1 * Lg), aim, 60)
for name, (fa, fz, dist, lens, fstop) in {"close_action": (-0.05, 0.05, 0.55, 85, 5.6),
                                          "close_front": (0.38, 0.0, 0.50, 85, 5.6),
                                          "close_rear": (-0.32, 0.0, 0.50, 85, 5.6)}.items():
    tgt = ctr + vec(fa * Lg, 0.0, fz * size[2])
    shot(name, tgt + vec(0.10 * Lg, dist * Lg, 0.10 * Lg), tgt, lens, fstop)
