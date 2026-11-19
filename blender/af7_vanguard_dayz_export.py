"""
AF-7 "Vanguard" - DayZ export (Blender 4.2+ / tested on 5.3).

Run this AFTER af7_vanguard_detailed.py, in the same Blender file
(Scripting tab > Open > this file > Run Script). Baking takes a few minutes.

WHAT IT MAKES
  blender/textures/af7_body_co.png, _nohq.png, _smdi.png, _as.png   (4096 px, logo + edge wear baked in)
  source/AF_Weapons/af7_vanguard/af7_vanguard.p3d                    (all LODs, selections, proxies, memory points)
  blender/export/af7_vanguard_lod1.fbx                               (fallback for Object Builder's FBX import)
  A new collection AF7_DayZ holding every LOD as a Blender object.

  Convert the four PNGs to .paa with DayZ Tools > ImageToPAA and put them in
  source/AF_Weapons/af7_vanguard/data/ (see docs/GUIDE.md).

EVERYTHING HERE FOLLOWS THE VANILLA M4 MODEL (dz\\weapons\\firearms\\m4\\m4a1.p3d):
  - Frame: the M4 points along -X in the p3d, +Y is up, and its origin is the
    magazine proxy. The script moves the Vanguard into that frame, using the
    AF7_Proxy_Magazine empty as the origin, so the M4 animations line up.
  - Selections: the M4's skeleton bones are called bolt, trigger, magazine,
    charging ... (not Weapon_Bolt). model.cfg uses the same names in the same order.
  - Proxy names and orientations are copied from the M4.
  - LODs: 1 to 7, View Pilot (1st person), Geometry, Memory, View Geometry, Fire Geometry.
"""

import math
import os
import struct
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

PREFIX = "AF7_"
TEX_SIZE = 4096
SAMPLES = {"EMIT": 12, "NORMAL": 24, "AO": 48}

MOD_DIR = "af_weapons\\af7_vanguard"
P3D_TEXTURE = MOD_DIR + "\\data\\af7_body_co.paa"
P3D_MATERIAL = MOD_DIR + "\\data\\af7_body.rvmat"
FIRE_MATERIAL = "dz\\data\\data\\penetration\\metalplate.rvmat"   # same as the vanilla M4 fire geometry
MASS_KG = 3.2
PROXY_SIZE = 0.05

# Per-weapon settings. Another weapon's export script imports this module and overrides these
# (and the tables below); see afm41_pathfinder_dayz_export.py.
TEX_NAME = "af7_body"                    # textures are written as <TEX_NAME>_co.png ...
P3D_FOLDER = "af7_vanguard"              # folder under source/AF_Weapons
P3D_FILE = "af7_vanguard"                # p3d and fbx file name
ORIGIN_EMPTY = "Proxy_Magazine"          # empty that becomes the p3d origin (None = working origin)
# Resolution LODs after LOD 1: (resolution, triangles as a share of LOD 1, smallest part kept in metres).
# LODs 2-4 are generous, for close range. LODs 5-7 are for distance: loose parts smaller than the
# given size (screws, pins, ribs, rounds) are dropped, because out there they are under a pixel,
# and what is left is decimated piece by piece (see decimated()).
LOD_RATIOS = ((2.0, 0.75, 0.0), (3.0, 0.5, 0.0), (4.0, 0.36, 0.0),
              (5.0, 0.22, 0.012), (6.0, 0.12, 0.022), (7.0, 0.06, 0.035))
LOD_PIECE_MIN = 6      # a loose piece is never decimated below this many triangles
UV_MARGIN = 0.0016     # gap added around every UV island (about 6 px at 4096)
UV_MAX_LENGTH = 0.40   # parts longer than this (metres, along the rifle) are unwrapped in several lengths
# _smdi levels for the standard finish: specular = SPEC_BASE + SPEC_METAL * metal,
# gloss = (1 - rough) * GLOSS_SCALE, colour map multiplied by CO_SCALE.
SPEC_BASE, SPEC_METAL, GLOSS_SCALE, CO_SCALE = 0.05, 0.12, 0.75, 0.85

# Texture sets to bake: (file suffix, value of the AF7_SKIN node). The gold skin shares the
# normal and ambient-shadow maps; it only gets its own _co and _smdi (af7_body_gold_co.png ...).
SKINS = (("", 0.0), ("_gold", 1.0))

# Texture sets. Every rifle has the set TEX_NAME. EXTRA_SETS adds more, each with its own
# 0..1 UV layout and its own files: ((texture name, (material names without the prefix, ...)), ...).
# Faces whose material is not named in any extra set stay in set 0. The selections are
# 'camo' for set 0 and 'camo1', 'camo2' ... for the others; parts in HIDE_BARREL must be in set 0.
# The value here is the AF-7's: receiver and steel in af7_body, handguard, grip, stock and butt pad
# in af7_furn. Every other weapon's export script sets its own (see afm41_pathfinder_dayz_export.py).
EXTRA_SETS = (("af7_furn", ("FDE_Cerakote", "FDE_Polymer", "Rubber")),)

# Blender object (without AF7_) -> named selection. Names are the vanilla M4 skeleton bones.
# Safety ('firemode') and BoltCatch ('boltrelease') stay static: those bones rotate around
# the M4's own pivots, which the Vanguard's parts don't share.
SELECTIONS = {"Weapon_Trigger": "trigger", "Weapon_Bolt": "bolt", "ChargingHandle": "charging"}
HIDE_BARREL = ("MuzzleBrake",)

# Texture space per part, relative to 1.0. More for what sits in front of the player's eyes
# in first person, less for parts that are mostly covered or tiny.
UV_PRIORITY = {
    "UpperReceiver": 1.5, "LowerReceiver": 1.5, "UpperPanels": 1.5, "TopRail": 1.4, "RearSight": 1.5,
    "FrontSight": 1.4, "Weapon_Bolt": 1.5, "ChargingHandle": 1.5, "DustCover": 1.4, "ForwardAssist": 1.4,
    "BrassDeflector": 1.4, "Safety": 1.3, "MagRelease": 1.3, "BoltCatch": 1.3,
    "Barrel": 0.6, "GasBlock": 0.5, "BufferTube": 0.7, "ReceiverPins": 0.8, "HandguardScrews": 0.8,
    "ButtPadRibs": 0.7, "GripRibs": 0.8, "ReceiverEndDetail": 0.7, "StockQD": 0.7, "StockLatch": 0.8,
}

# Memory points: empty -> selection name (all present in the vanilla M4 memory LOD)
MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
          "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend"}

# Proxies: empty -> (p3d path, up axis, dir axis, extra selections). Axes are in p3d space and
# are the vanilla M4's own proxy orientations, so each attachment sits the way it does on the M4.
PROXIES = {
    "Proxy_Magazine": ("\\dz\\weapons\\attachments\\magazine\\magazine_stanag30", (0, 1, 0), (0, 0, 1), ("magazine",)),
    "Proxy_Optic": ("\\dz\\weapons\\attachments\\optics\\optic_acog", (1, 0, 0), (0, 0, -1), ()),
    "Proxy_Muzzle": ("\\dz\\weapons\\attachments\\muzzle\\suppressor_556", (1, 0, 0), (0, 0, 1), ()),
    "Proxy_Light": ("\\dz\\weapons\\attachments\\light\\weaponlight_universal", (0, 1, 0), (0, 0, 1), ()),
}

# Collision boxes in the working frame: (min xyz, max xyz). Four convex components, like the M4.
GEOMETRY = [((-0.017, -0.100, 0.004), (0.017, 0.122, 0.088)),     # receiver + rail
            ((-0.023, 0.122, 0.029), (0.023, 0.530, 0.088)),      # handguard + barrel
            ((-0.018, -0.357, -0.059), (0.018, -0.100, 0.084)),   # stock
            ((-0.016, -0.094, -0.100), (0.016, -0.026, 0.004))]   # pistol grip

LOD_GEOMETRY, LOD_MEMORY, LOD_VIEWGEO, LOD_FIREGEO, LOD_VIEW_PILOT = 1e13, 1e15, 6e15, 7e15, 1100.0


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    raise RuntimeError("Save the .blend next to this script first.")


def texture_sets():
    return [(TEX_NAME, None)] + [(name, tuple(mats)) for name, mats in EXTRA_SETS]


def set_of_material(mat):
    """Texture set of a material: its 'af_set' property if it has one (baked preview materials),
    otherwise looked up by name in EXTRA_SETS."""
    if mat is None:
        return 0
    if "af_set" in mat:
        return int(mat["af_set"])
    short = mat.name[len(PREFIX):] if mat.name.startswith(PREFIX) else mat.name
    for k, (_name, names) in enumerate(texture_sets()):
        if names and short in names:
            return k
    return 0


def camo_name(k):
    return "camo" if k == 0 else "camo%d" % k


def set_texture(k):
    return P3D_TEXTURE if k == 0 else "%s\\data\\%s_co.paa" % (MOD_DIR, texture_sets()[k][0])


def set_rvmat(k):
    return P3D_MATERIAL if k == 0 else "%s\\data\\%s.rvmat" % (MOD_DIR, texture_sets()[k][0])


def poly_sets(me):
    mats = [set_of_material(m) for m in me.materials] or [0]
    return [mats[min(p.material_index, len(mats) - 1)] for p in me.polygons]


def export_matrix():
    """Working frame (+Y forward, trigger origin) -> vanilla M4 frame, expressed in Blender axes
    (-X forward, +Z up, magazine proxy at the origin)."""
    if not ORIGIN_EMPTY:
        return Matrix.Rotation(math.radians(90), 4, "Z")
    mag = bpy.data.objects.get(PREFIX + ORIGIN_EMPTY)
    origin = mag.location.copy() if mag else Vector((0, 0.075, -0.0105))
    return Matrix.Rotation(math.radians(90), 4, "Z") @ Matrix.Translation(-origin)


def P(v):
    """Blender (x, y, z) -> p3d (x, z, y)."""
    return (v[0], v[2], v[1])


# ----------------------------------------------------------------------------
# Mesh building
# ----------------------------------------------------------------------------

def dayz_collection():
    col = bpy.data.collections.get(PREFIX + "DayZ")
    if col:
        for ob in list(col.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        col = bpy.data.collections.new(PREFIX + "DayZ")
        bpy.context.scene.collection.children.link(col)
    return col


def source_objects():
    obs = []
    for cname in ("Body", "Moving"):
        col = bpy.data.collections.get(PREFIX + cname)
        if not col:
            raise RuntimeError("Run af7_vanguard_detailed.py first (collection %s%s is missing)." % (PREFIX, cname))
        obs += [o for o in col.objects if o.type == "MESH"]
    return sorted(obs, key=lambda o: o.name)


def remove_hidden_faces(bm, dl, moving_groups):
    """Delete triangles that sit entirely inside another static part (touching faces where
    parts meet, the buried ends of ribs and screws, and so on). Nobody can ever see them,
    and removing them frees texture space for the faces that are seen.

    Parts that move or can be hidden (trigger, bolt, charging handle, muzzle brake) are left
    whole and never count as cover, because what they hide can come into view."""
    from mathutils.bvhtree import BVHTree

    def is_moving(face):
        return any(g in v[dl] for v in face.verts for g in moving_groups)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    static = [f for f in bm.faces if not is_moving(f)]
    tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in static])
    dirs = [Vector(d).normalized() for d in ((0.31, 0.74, 0.60), (-0.67, 0.21, -0.71), (0.52, -0.63, 0.57))]

    def inside(point):
        """Point-in-solid by counting surface crossings along three rays (majority vote)."""
        votes = 0
        for d in dirs:
            origin, hits = point, 0
            for _ in range(96):
                loc = tree.ray_cast(origin, d)[0]
                if loc is None:
                    break
                hits += 1
                origin = loc + d * 1e-5
            votes += hits % 2
        return votes >= 2

    doomed = []
    for f in static:
        n = f.normal
        if n.length < 0.5:
            continue
        centre = f.calc_center_median()
        samples = [centre] + [centre.lerp(v.co, 0.6) for v in f.verts]
        # Long triangles (a barrel segment, a stock flank) can be covered at one end and in
        # plain view at the other, so they get a grid of samples about every 1.5 cm.
        a, b, c = (v.co for v in f.verts)
        longest = max((a - b).length, (b - c).length, (c - a).length)
        k = min(24, int(longest / 0.015))
        if k >= 3:
            for i in range(k + 1):
                for j in range(k + 1 - i):
                    u, w = (i + 0.25) / (k + 1.0), (j + 0.25) / (k + 1.0)
                    samples.append(a + (b - a) * u + (c - a) * w)
        if all(inside(p + n * 5e-5) for p in samples):
            doomed.append(f)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    return len(doomed)


def build_lod1(col, M):
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    dl = bm.verts.layers.deform.verify()
    uv_prio = bm.faces.layers.float.new("af7_uv_priority")
    groups, mats = [], []

    def gidx(name):
        if name not in groups:
            groups.append(name)
        return groups.index(name)

    for ob in source_objects():
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(M @ ob.matrix_world)
        short = ob.name[len(PREFIX):]
        names = [SELECTIONS[short]] if short in SELECTIONS else []
        part_set = set_of_material(me.materials[0]) if len(me.materials) else 0
        names.append("hide_barrel" if short in HIDE_BARREL else camo_name(part_set))
        idx = [gidx(n) for n in names]
        nv, nf = len(bm.verts), len(bm.faces)
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        for v in bm.verts[nv:]:
            for i in idx:
                v[dl][i] = 1.0
        src = list(me.materials)
        priority = UV_PRIORITY.get(short, 1.0)
        for f in bm.faces[nf:]:
            m = src[f.material_index] if src else None
            if m not in mats:
                mats.append(m)
            f.material_index = mats.index(m)
            f[uv_prio] = priority
        bpy.data.meshes.remove(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    moving = {groups.index(g) for g in list(SELECTIONS.values()) + ["hide_barrel"] if g in groups}
    removed = remove_hidden_faces(bm, dl, moving)
    print("AF7 removed %d hidden triangles (%d left)" % (removed, len(bm.faces)))
    me = bpy.data.meshes.new(PREFIX + "LOD_1")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(35))
    ob = bpy.data.objects.new(PREFIX + "LOD_1", me)
    col.objects.link(ob)
    for g in groups:
        ob.vertex_groups.new(name=g)
    ob["dayz"] = "Resolution LOD 1 (full detail). Vertex groups = named selections."
    return ob


def activate(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def unwrap(ob):
    activate(ob)
    if not ob.data.uv_layers:
        ob.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Texel priority: parts the player looks at get more texture space, parts that are
    # mostly hidden get less. Every UV island belongs to one part, so scaling a part's UVs
    # about the origin keeps its islands intact; the repack then lays them out again.
    me = ob.data
    prio = me.attributes.get("af7_uv_priority")
    uv = me.uv_layers.active.data
    if prio is not None:
        for poly in me.polygons:
            s = prio.data[poly.index].value or 1.0
            if s != 1.0:
                for li in poly.loop_indices:
                    uv[li].uv = uv[li].uv * s

    # Long parts (stock, barrel, handguard) unwrap into strips as long as the rifle, and one such
    # strip sets the scale for the whole layout. Cut every part longer than UV_MAX_LENGTH into
    # equal lengths: faces in different lengths are moved apart in UV space, which splits the
    # islands there, and the packer then places the pieces separately.
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    seen = set()
    for start in bm.verts:
        if start.index in seen:
            continue
        seen.add(start.index)
        part, stack = [start], [start]
        while stack:
            for e in stack.pop().link_edges:
                for o in e.verts:
                    if o.index not in seen:
                        seen.add(o.index)
                        part.append(o)
                        stack.append(o)
        lo, hi = min(v.co.y for v in part), max(v.co.y for v in part)
        pieces = int(math.ceil((hi - lo) / UV_MAX_LENGTH))
        if pieces < 2:
            continue
        for f in {f for v in part for f in v.link_faces}:
            k = min(pieces - 1, int((f.calc_center_median().y - lo) / (hi - lo) * pieces))
            for loop in f.loops:
                loop[uvl].uv.x += 40.0 * k
    bm.to_mesh(me)
    bm.free()

    def pack():
        # Exact island outlines and free rotation fill the square far better than the default
        # bounding-box packing (about 45% used before, see the coverage line in the log).
        for kw in (dict(rotate=True, rotate_method="ANY", shape_method="CONCAVE", margin_method="ADD", margin=UV_MARGIN),
                   dict(rotate=True, margin=UV_MARGIN), dict(margin=UV_MARGIN)):
            try:
                bpy.ops.uv.pack_islands(**kw)
                return
            except TypeError:
                continue

    # Each texture set is packed on its own into the full 0..1 square.
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    nsets = len(texture_sets())
    mat_sets = [set_of_material(m) for m in ob.data.materials] or [0]
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(ob.data)
    for k in range(nsets):
        mine = [f for f in bm.faces if mat_sets[min(f.material_index, len(mat_sets) - 1)] == k]
        if not mine:
            continue
        for f in bm.faces:              # the packer only sees faces that are visible and selected
            f.hide_set(True)
        for f in mine:
            f.hide_set(False)
            f.select_set(True)
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.uv.select_all(action="SELECT")
        pack()
    for f in bm.faces:
        f.hide_set(False)
        f.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    me = ob.data                           # re-fetch: leaving edit mode rebuilds the mesh data
    uv = me.uv_layers.active.data

    def uv_area(p):
        a, b, c = (uv[li].uv.copy() for li in p.loop_indices)
        return abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2.0

    sets = poly_sets(me)
    for k in range(nsets):
        used = sum(uv_area(p) for p, s in zip(me.polygons, sets) if s == k)
        print("AF7 UV coverage, set %d (%s): %.1f%% of the texture" % (k, texture_sets()[k][0], 100.0 * used))


def drop_small_parts(me, min_size):
    """Delete every loose piece of the mesh whose bounding box diagonal is under min_size."""
    bm = bmesh.new()
    bm.from_mesh(me)
    seen, doomed = set(), []
    for start in bm.verts:
        if start.index in seen:
            continue
        seen.add(start.index)
        island, stack = [start], [start]
        while stack:
            for e in stack.pop().link_edges:
                for o in e.verts:
                    if o.index not in seen:
                        seen.add(o.index)
                        island.append(o)
                        stack.append(o)
        lo = Vector((min(v.co.x for v in island), min(v.co.y for v in island), min(v.co.z for v in island)))
        hi = Vector((max(v.co.x for v in island), max(v.co.y for v in island), max(v.co.z for v in island)))
        if (hi - lo).length < min_size:
            doomed += island
    bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(doomed)


def _collapse(ob, ratio):
    """Collapse-decimate one object in place."""
    mod = ob.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.clear()
    old, ob.data = ob.data, me
    bpy.data.meshes.remove(old)


def decimated(src, col, name, ratio, min_size=0.0):
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    col.objects.link(ob)
    if min_size <= 0.0:
        _collapse(ob, ratio)
    else:
        # Distance LOD. Decimating the whole mesh at once lets the big flat parts (receiver
        # sides, stock) collapse to nothing while fiddly ones keep their triangles. So the mesh
        # is split into its loose pieces and every piece gives up the same share.
        target = ratio * len(src.data.polygons)
        drop_small_parts(ob.data, min_size)
        share = min(1.0, target / max(1, len(ob.data.polygons)))
        activate(ob)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        pieces = [o for o in col.objects if o.select_get() or o is ob]
        for piece in pieces:
            n = len(piece.data.polygons)
            if n > LOD_PIECE_MIN:
                _collapse(piece, max(share, LOD_PIECE_MIN / n))
        for o in bpy.context.view_layer.objects:
            o.select_set(o in pieces)
        bpy.context.view_layer.objects.active = ob
        if len(pieces) > 1:
            bpy.ops.object.join()
    me = ob.data
    ob.name = me.name = name
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(35))
    return ob


# ----------------------------------------------------------------------------
# Baking (procedural materials -> one DayZ texture set)
# ----------------------------------------------------------------------------

def _pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _save(name, rgba, path, colorspace):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, rgba.shape[1], rgba.shape[0], alpha=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(np.ascontiguousarray(rgba, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


def bake_textures(ob, tex_dir, size=TEX_SIZE):
    scene = bpy.context.scene
    mats = [m for m in ob.data.materials if m]
    saved_engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.margin = 8
    scene.render.bake.use_clear = True
    scene.render.bake.use_selected_to_active = False
    if scene.world:
        scene.world.light_settings.distance = 0.04
    hidden = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o is not ob
    activate(ob)

    sets = texture_sets()
    mat_set = {m: set_of_material(m) for m in mats}

    def target(tag, colorspace, fill):
        """One bake image per texture set; every material bakes into the image of its set,
        so a single bake pass fills all the sets."""
        imgs = []
        for k in range(len(sets)):
            name = PREFIX + "Bake_%s_%d" % (tag, k)
            if name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[name])
            img = bpy.data.images.new(name, size, size, alpha=False)
            img.generated_color = fill
            img.colorspace_settings.name = colorspace
            imgs.append(img)
        for m in mats:
            nt = m.node_tree
            node = nt.nodes.get(PREFIX + "BAKE") or nt.nodes.new("ShaderNodeTexImage")
            node.name = PREFIX + "BAKE"
            node.image = imgs[mat_set[m]]
            for n in nt.nodes:
                n.select = False
            node.select = True
            nt.nodes.active = node
        return imgs

    def grab(imgs, channel=None):
        out = [_pixels(i) if channel is None else _pixels(i)[..., channel].copy() for i in imgs]
        for i in imgs:
            bpy.data.images.remove(i)
        return out

    def surface(tap):
        """Route a named tap through an Emission shader (tap=None restores the BSDF)."""
        for m in mats:
            nt = m.node_tree
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            if tap is None:
                bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
                nt.links.new(bsdf.outputs[0], out.inputs[0])
                continue
            em = nt.nodes.get(PREFIX + "EMIT") or nt.nodes.new("ShaderNodeEmission")
            em.name = PREFIX + "EMIT"
            nt.links.new(nt.nodes[PREFIX + tap].outputs[0], em.inputs[0])
            nt.links.new(em.outputs[0], out.inputs[0])

    def set_skin(value):
        for m in mats:
            node = m.node_tree.nodes.get(PREFIX + "SKIN")
            if node:
                node.outputs[0].default_value = value

    has_skin = any(m.node_tree.nodes.get(PREFIX + "SKIN") for m in mats)
    skins = SKINS if has_skin else SKINS[:1]
    result = {}
    try:
        scene.cycles.samples = SAMPLES["EMIT"]
        for suffix, value in skins:
            set_skin(value)
            for tag, tap, cs in (("color", "COLOR", "sRGB"), ("rough", "ROUGH", "Non-Color"), ("metal", "METAL", "Non-Color")):
                imgs = target(tag, cs, (0, 0, 0, 1))
                surface(tap)
                bpy.ops.object.bake(type="EMIT")
                result[tag + suffix] = grab(imgs, None if tag == "color" else 0)
                print("AF7 baked", tag + suffix)
        set_skin(0.0)
        surface(None)
        scene.cycles.samples = SAMPLES["NORMAL"]
        imgs = target("normal", "Non-Color", (0.5, 0.5, 1.0, 1.0))
        # DayZ / Arma normal maps are DirectX style (green pointing down)
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="NEG_Y", normal_b="POS_Z")
        result["normal"] = grab(imgs)
        print("AF7 baked normal")
        scene.cycles.samples = SAMPLES["AO"]
        imgs = target("ao", "Non-Color", (1, 1, 1, 1))
        bpy.ops.object.bake(type="AO")
        result["ao"] = grab(imgs, 0)
        print("AF7 baked ao")
    finally:
        set_skin(0.0)
        surface(None)
        for o, h in hidden.items():
            o.hide_render = h
        scene.render.engine = saved_engine

    os.makedirs(tex_dir, exist_ok=True)
    all_files = []
    for k, (tex_name, _names) in enumerate(sets):
        ao = np.clip(result["ao"][k], 0, 1)
        one = np.ones_like(ao)
        base_metal = np.clip(result["metal"][k], 0, 1)
        amb = np.stack([one, ao, one, one], axis=-1)           # green = ambient shadow
        nohq = result["normal"][k]
        nohq[..., 3] = 1
        outputs = [("nohq", nohq, "Non-Color"), ("as", amb, "Non-Color")]

        for suffix, _value in skins:
            rough = np.clip(result["rough" + suffix][k], 0, 1)
            metal = np.clip(result["metal" + suffix][k], 0, 1)
            co = result["color" + suffix][k]
            co[..., :3] *= (0.78 + 0.22 * ao)[..., None]      # a little baked-in contact shadow
            co[..., 3] = 1
            # Levels matched to the vanilla m4_body_smdi (specular median 0.13, gloss median 0.39).
            # Anything much higher washes the rifle out to white under DayZ's lighting.
            spec = np.clip(SPEC_BASE + SPEC_METAL * metal, 0, 1)
            gloss = np.clip((1.0 - rough) * GLOSS_SCALE, 0, 1)
            if not suffix:
                co[..., :3] *= CO_SCALE                        # DayZ lights colour maps brightly
            if suffix:
                gloss = np.clip(1.0 - rough, 0, 1)
                # Skin: only the ornament reflects (exactly like the old R700 chassis map, which is
                # specular 1 on the gold and 0 everywhere else). The skin's material uses a strong
                # orange environment map; any specular on the black parts turns them orange in game.
                ornament = np.clip(metal - base_metal, 0, 1)
                spec = ornament
            smdi = np.stack([one, spec, gloss, one], axis=-1)
            key = suffix.strip("_") + "_" if suffix else ""
            outputs += [(key + "co", co, "sRGB"), (key + "smdi", smdi, "Non-Color")]

        files = {}
        for suffix, data, cs in outputs:
            path = os.path.join(tex_dir, "%s_%s.png" % (tex_name, suffix))
            files[suffix] = _save(tex_name + "_" + suffix, data, path, cs)
            print("AF7 wrote", path)
        all_files.append(files)
    return all_files


def game_material(files, name="Body_DayZ", skin=""):
    """One material that previews the baked DayZ textures inside Blender.
    skin="gold_" previews the gold floral set."""
    files = dict(files, co=files[skin + "co"], smdi=files[skin + "smdi"])
    mat = bpy.data.materials.get(PREFIX + name) or bpy.data.materials.new(PREFIX + name)
    mat.use_fake_user = True
    try:
        mat.use_nodes = True
    except Exception:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])

    def tex(key):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = files[key]
        return n

    co, smdi, nohq, amb = tex("co"), tex("smdi"), tex("nohq"), tex("as")
    nt.links.new(co.outputs[0], bsdf.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(smdi.outputs[0], sep.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs[2], inv.inputs[1])
    nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
    met = nt.nodes.new("ShaderNodeMapRange")
    # undo the specular encoding used in bake_textures (the skin halves non-ornament specular)
    met.inputs[1].default_value, met.inputs[2].default_value = (0.0, 1.0) if skin else (SPEC_BASE, SPEC_BASE + SPEC_METAL)
    nt.links.new(sep.outputs[1], met.inputs[0])
    nt.links.new(met.outputs[0], bsdf.inputs["Metallic"])
    nsep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(nohq.outputs[0], nsep.inputs[0])
    flip = nt.nodes.new("ShaderNodeMath")
    flip.operation = "SUBTRACT"
    flip.inputs[0].default_value = 1.0
    nt.links.new(nsep.outputs[1], flip.inputs[1])
    ncomb = nt.nodes.new("ShaderNodeCombineColor")
    nt.links.new(nsep.outputs[0], ncomb.inputs[0])
    nt.links.new(flip.outputs[0], ncomb.inputs[1])
    nt.links.new(nsep.outputs[2], ncomb.inputs[2])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(ncomb.outputs[0], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])
    for i, n in enumerate(nt.nodes):
        n.location = (-260 * (len(nt.nodes) - i), -60 * (i % 5))
    return mat


def preview_materials(files_by_set):
    """Preview materials for every set (and the gold skin where it was baked), tagged with their set."""
    mats = []
    for k, files in enumerate(files_by_set):
        tail = "" if k == 0 else "_%d" % k
        if "gold_co" in files and "gold_smdi" in files:   # kept in the file to preview the skin
            game_material(files, "Body_DayZ_Gold" + tail, "gold_")["af_set"] = k
        mat = game_material(files, "Body_DayZ" + tail)
        mat["af_set"] = k
        mats.append(mat)
    return mats


def set_materials(ob, mats):
    """Replace the object's materials by one material per texture set."""
    me = ob.data
    sets = poly_sets(me)
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    for p, s in zip(me.polygons, sets):
        p.material_index = s


# ----------------------------------------------------------------------------
# P3D (MLOD) writer. Conventions were checked against Object Builder's own
# O2Script: same vertex order as Blender after the (x, z, y) swap, stored normals
# point inward, v is flipped, proxy = triangle [origin, origin + 2*up, origin + dir].
# ----------------------------------------------------------------------------

class Lod:
    def __init__(self, resolution):
        self.resolution = resolution
        self.points = []      # (x, y, z, flags) in p3d space
        self.normals = []
        self.faces = []       # ([(point, normal, u, v), ...], texture, material)
        self.selections = {}  # name -> (set(points), set(faces))
        self.sharp = []       # (a, b)
        self.props = []       # (name, value)
        self.mass = None      # per point

    def select(self, name, points=(), faces=()):
        s = self.selections.setdefault(name, (set(), set()))
        s[0].update(points)
        s[1].update(faces)

    def add_proxy(self, path, origin, up, direction, extra=(), index=1):
        o = Vector(origin)
        # Object Builder's own proxies are 2 m x 1 m; same 2:1 shape here, but small,
        # so the triangles don't inflate the model's bounding sphere.
        tri = [o, o + 2.0 * PROXY_SIZE * Vector(up), o + PROXY_SIZE * Vector(direction)]
        base = len(self.points)
        self.points += [(p.x, p.y, p.z, 0x1000000) for p in tri]
        n = (tri[1] - tri[0]).cross(tri[2] - tri[0]).normalized()
        ni = len(self.normals)
        self.normals.append((n.x, n.y, n.z))
        fi = len(self.faces)
        self.faces.append(([(base + k, ni, 0.0, 0.0) for k in range(3)], "", ""))
        for name in ("proxy:%s.%03d" % (path, index),) + tuple(extra):
            self.select(name, range(base, base + 3), [fi])


def lod_from_mesh(ob, resolution, texture, material):
    me = ob.data
    lod = Lod(resolution)
    sets = poly_sets(me) if not isinstance(texture, str) else None
    lod.points = [P(v.co) + (0,) for v in me.vertices]
    uv = me.uv_layers.active.data if me.uv_layers.active else None
    corner_normals = me.corner_normals if hasattr(me, "corner_normals") else None
    index = {}
    for poly in me.polygons:
        verts = []
        for li in poly.loop_indices:
            n = corner_normals[li].vector if corner_normals is not None else me.loops[li].normal
            key = (round(-n[0], 4), round(-n[2], 4), round(-n[1], 4))   # stored inward, in p3d axes
            if key not in index:
                index[key] = len(lod.normals)
                lod.normals.append(key)
            u, v = (uv[li].uv[0], 1.0 - uv[li].uv[1]) if uv else (0.0, 0.0)
            verts.append((me.loops[li].vertex_index, index[key], u, v))
        if sets is None:
            lod.faces.append((verts, texture, material))
        else:
            lod.faces.append((verts, texture[sets[poly.index]], material[sets[poly.index]]))
    for g in ob.vertex_groups:
        pts = set()
        for v in me.vertices:
            for ge in v.groups:
                if ge.group == g.index and ge.weight > 0.5:
                    pts.add(v.index)
        faces = [p.index for p in me.polygons if all(vi in pts for vi in p.vertices)]
        if pts:
            lod.select(g.name, pts, faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if (not e.smooth) or len(e.link_faces) != 2 or any(not f.smooth for f in e.link_faces):
            lod.sharp.append((e.verts[0].index, e.verts[1].index))
    bm.free()
    return lod


def write_p3d(path, lods):
    def z(s):
        return s.encode("latin1") + b"\0"

    def tag(name, data=b""):
        return b"\x01" + z(name) + struct.pack("<I", len(data)) + data

    with open(path, "wb") as f:
        f.write(b"MLOD" + struct.pack("<II", 257, len(lods)))
        for lod in lods:
            npts, nfaces = len(lod.points), len(lod.faces)
            f.write(b"P3DM" + struct.pack("<6I", 28, 256, npts, len(lod.normals), nfaces, 0))
            for x, y, zz, flags in lod.points:
                f.write(struct.pack("<3fI", x, y, zz, flags))
            for n in lod.normals:
                f.write(struct.pack("<3f", *n))
            uvset = bytearray(struct.pack("<I", 0))
            for verts, texture, material in lod.faces:
                f.write(struct.pack("<I", len(verts)))
                for k in range(4):
                    pi, ni, u, v = verts[k] if k < len(verts) else (0, 0, 0.0, 0.0)
                    f.write(struct.pack("<2I2f", pi, ni, u, v))
                    if k < len(verts):
                        uvset += struct.pack("<2f", u, v)
                f.write(struct.pack("<I", 0) + z(texture) + z(material))
            f.write(b"TAGG")
            if lod.sharp:
                f.write(tag("#SharpEdges#", b"".join(struct.pack("<2I", a, b) for a, b in lod.sharp)))
            for name, (pts, faces) in lod.selections.items():
                data = bytearray(npts + nfaces)
                for i in pts:
                    data[i] = 1
                for i in faces:
                    data[npts + i] = 1
                f.write(tag(name, bytes(data)))
            for name, value in lod.props:
                f.write(tag("#Property#", name.encode("latin1").ljust(64, b"\0") + value.encode("latin1").ljust(64, b"\0")))
            if lod.mass is not None:
                f.write(tag("#Mass#", struct.pack("<%df" % npts, *lod.mass)))
            f.write(tag("#UVSet#", bytes(uvset)))
            f.write(tag("#EndOfFile#"))
            f.write(struct.pack("<f", lod.resolution))


def lod1_from_p3d(path, col):
    """Read resolution LOD 1 back out of a .p3d this script wrote: the mesh, its UVs and its
    named selections, without the proxy triangles. Used by export(bake=False), so that an
    export without a new bake keeps exactly the mesh and UVs the textures were baked for.
    Returns None if the file does not exist."""
    if not os.path.isfile(path):
        return None
    d = open(path, "rb").read()
    if d[:4] != b"MLOD":
        return None
    o = 12
    for _ in range(struct.unpack_from("<I", d, 8)[0]):
        npts, nnorm, nfaces = struct.unpack_from("<3I", d, o + 12)
        o += 28
        pts = [struct.unpack_from("<3fI", d, o + 16 * i) for i in range(npts)]
        o += 16 * npts + 12 * nnorm
        faces, face_tex = [], []
        for _ in range(nfaces):
            n = struct.unpack_from("<I", d, o)[0]
            corners = [struct.unpack_from("<2I2f", d, o + 4 + 16 * k) for k in range(n)]
            o += 72
            e = d.index(b"\0", o)
            face_tex.append(d[o:e].decode("latin1").lower())
            o = d.index(b"\0", e + 1) + 1     # material
            faces.append(corners)
        o += 4                          # TAGG
        tags = {}
        while True:
            e = d.index(b"\0", o + 1)
            name = d[o + 1:e].decode("latin1")
            size = struct.unpack_from("<I", d, e + 1)[0]
            tags[name] = d[e + 5:e + 5 + size]
            o = e + 5 + size
            if name == "#EndOfFile#":
                break
        resolution = struct.unpack_from("<f", d, o)[0]
        o += 4
        if abs(resolution - 1.0) > 1e-6:
            continue
        proxy_faces = set()
        for name, data in tags.items():
            if name.startswith("proxy:"):
                proxy_faces.update(i for i in range(nfaces) if data[npts + i])
        keep = [i for i in range(nfaces) if i not in proxy_faces]
        nreal = 1 + max(c[0] for i in keep for c in faces[i])
        me = bpy.data.meshes.new(PREFIX + "LOD_1")
        me.from_pydata([(p[0], p[2], p[1]) for p in pts[:nreal]], [], [[c[0] for c in faces[i]] for i in keep])
        uv = me.uv_layers.new(name="UVMap").data
        for poly, i in zip(me.polygons, keep):
            for li, c in zip(poly.loop_indices, faces[i]):
                uv[li].uv = (c[2], 1.0 - c[3])
            poly.use_smooth = True
        tex_set = {set_texture(k).lower(): k for k in range(len(texture_sets()))}
        for k in range(len(texture_sets())):
            holder = bpy.data.materials.new(PREFIX + "Set%d" % k)
            holder["af_set"] = k
            me.materials.append(holder)
        for poly, i in zip(me.polygons, keep):
            poly.material_index = tex_set.get(face_tex[i], 0)
        me.update()
        if hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=math.radians(35))
        ob = bpy.data.objects.new(PREFIX + "LOD_1", me)
        col.objects.link(ob)
        for name, data in tags.items():
            members = [i for i in range(nreal) if data[i]] if not name.startswith(("#", "proxy:")) else []
            if members:
                ob.vertex_groups.new(name=name).add(members, 1.0, "REPLACE")
        ob["dayz"] = "Resolution LOD 1, read back from the existing .p3d (export without bake)."
        return ob
    return None


# ----------------------------------------------------------------------------
# Special LODs
# ----------------------------------------------------------------------------

BOX_TRIS = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
            (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))


def geometry_object(col, M, name):
    """Convex collision boxes as a Blender mesh (vertex groups Component01...)."""
    verts, faces, comp = [], [], []
    for lo, hi in GEOMETRY:
        base = len(verts)
        corners = [(lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]), (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
                   (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])]
        verts += [tuple(M @ Vector(c)) for c in corners]
        faces += [tuple(base + i for i in t) for t in BOX_TRIS]
        comp.append(range(base, base + 8))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for i, rng in enumerate(comp):
        ob.vertex_groups.new(name="Component%02d" % (i + 1)).add(list(rng), 1.0, "REPLACE")
    ob.display_type = "WIRE"
    ob.hide_render = True
    return ob


def memory_points(M, lod1):
    pts = {}
    for short, name in MEMORY.items():
        e = bpy.data.objects.get(PREFIX + short)
        if e:
            pts[name] = M @ e.matrix_world.translation
    co = [v.co for v in lod1.data.vertices]
    pts["boundingbox_min"] = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    pts["boundingbox_max"] = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    return pts


def memory_object(col, pts, name):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts.values()], [], [])
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for i, n in enumerate(pts):
        ob.vertex_groups.new(name=n).add([i], 1.0, "REPLACE")
    ob.hide_render = True
    return ob


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def export(bake=True, tex_size=TEX_SIZE):
    here = _here()
    repo = os.path.dirname(here)
    tex_dir = os.path.join(here, "textures")
    p3d_path = os.path.join(repo, "source", "AF_Weapons", P3D_FOLDER, P3D_FILE + ".p3d")
    M = export_matrix()
    col = dayz_collection()

    # Bake in the working frame (the logo and wear are projected by position there),
    # then move the finished mesh into the M4 frame.
    # Without a new bake, LOD 1 is read back from the existing .p3d. Rebuilding it could shift
    # the automatic unwrap (it depends on every face), and the textures would no longer fit.
    lod1 = None if bake else lod1_from_p3d(p3d_path, col)
    if lod1 is not None:
        print("AF7 kept LOD 1 and its UVs from", p3d_path)
        loaded = []
        for tex_name, _names in texture_sets():
            files = {}
            for suffix in ("co", "nohq", "smdi", "as", "gold_co", "gold_smdi"):
                png = os.path.join(tex_dir, "%s_%s.png" % (tex_name, suffix))
                if os.path.isfile(png):
                    files[suffix] = bpy.data.images.load(png, check_existing=True)
                    files[suffix].colorspace_settings.name = "sRGB" if suffix.endswith("co") else "Non-Color"
            loaded.append(files)
        if all(all(k in f for k in ("co", "nohq", "smdi", "as")) for f in loaded):   # preview from the last bake
            set_materials(lod1, preview_materials(loaded))
    else:
        lod1 = build_lod1(col, Matrix.Identity(4))
        unwrap(lod1)
        if bake:
            set_materials(lod1, preview_materials(bake_textures(lod1, tex_dir, tex_size)))
        lod1.data.transform(M)
        lod1.data.update()

    visual = [(1.0, lod1)]
    for res, ratio, min_size in LOD_RATIOS:
        ob = decimated(lod1, col, "%sLOD_%d" % (PREFIX, int(res)), ratio, min_size)
        ob["dayz"] = "Resolution LOD %d (about %d%% of LOD 1)." % (int(res), int(ratio * 100))
        visual.append((res, ob))

    proxies, used = [], {}
    for short, (path, up, direction, extra) in PROXIES.items():
        e = bpy.data.objects.get(PREFIX + short)
        if e:
            used[path] = used.get(path, 0) + 1    # a model used twice becomes proxy .001, .002, ...
            proxies.append((path, P(M @ e.matrix_world.translation), up, direction, extra, used[path]))

    lods = []
    for res, ob in visual + [(LOD_VIEW_PILOT, lod1)]:
        nsets = len(texture_sets())
        lod = lod_from_mesh(ob, res, [set_texture(k) for k in range(nsets)], [set_rvmat(k) for k in range(nsets)])
        for path, origin, up, direction, extra, index in proxies:
            lod.add_proxy(path, origin, up, direction, extra, index)
        lods.append(lod)

    geo_ob = geometry_object(col, M, PREFIX + "LOD_Geometry")
    geo_ob["dayz"] = "Geometry / View Geometry / Fire Geometry: four convex boxes, %.1f kg." % MASS_KG
    for res, material in ((LOD_GEOMETRY, ""), (LOD_VIEWGEO, ""), (LOD_FIREGEO, FIRE_MATERIAL)):
        lod = lod_from_mesh(geo_ob, res, "", material)
        if res == LOD_GEOMETRY:
            lod.mass = [MASS_KG / len(lod.points)] * len(lod.points)
            lod.props.append(("autocenter", "0"))
        lods.append(lod)

    pts = memory_points(M, lod1)
    mem_ob = memory_object(col, pts, PREFIX + "LOD_Memory")
    mem_ob["dayz"] = "Memory LOD: one vertex per named point."
    mem = Lod(LOD_MEMORY)
    for i, (name, p) in enumerate(pts.items()):
        mem.points.append(P(p) + (0,))
        mem.select(name, [i])
    lods.append(mem)

    lods.sort(key=lambda l: l.resolution)
    os.makedirs(os.path.dirname(p3d_path), exist_ok=True)
    write_p3d(p3d_path, lods)
    print("AF7 wrote", p3d_path)
    for lod in lods:
        print("AF7 LOD %-8g points=%d faces=%d selections=%s" % (
            lod.resolution, len(lod.points), len(lod.faces), sorted(lod.selections)))

    try:
        os.makedirs(os.path.join(here, "export"), exist_ok=True)
        activate(lod1)
        bpy.ops.export_scene.fbx(filepath=os.path.join(here, "export", P3D_FILE + "_lod1.fbx"),
                                 use_selection=True, object_types={"MESH"}, axis_forward="Y", axis_up="Z")
        print("AF7 wrote FBX")
    except Exception as exc:
        print("AF7 FBX export skipped:", exc)
    return lod1


if __name__ == "__main__":
    export()
    print("AF-7 Vanguard DayZ export finished.")
