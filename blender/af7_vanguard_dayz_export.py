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
  - LODs: 1, 2, 3, 4, View Pilot (1st person), Geometry, Memory, View Geometry, Fire Geometry.
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

# Texture sets to bake: (file suffix, value of the AF7_SKIN node). The gold skin shares the
# normal and ambient-shadow maps; it only gets its own _co and _smdi (af7_body_gold_co.png ...).
SKINS = (("", 0.0), ("_gold", 1.0))

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


def export_matrix():
    """Working frame (+Y forward, trigger origin) -> vanilla M4 frame, expressed in Blender axes
    (-X forward, +Z up, magazine proxy at the origin)."""
    mag = bpy.data.objects.get(PREFIX + "Proxy_Magazine")
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
        names.append("hide_barrel" if short in HIDE_BARREL else "camo")
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
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        try:
            bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
        except TypeError:
            bpy.ops.uv.pack_islands(margin=0.003)
        bpy.ops.object.mode_set(mode="OBJECT")

    me = ob.data                           # re-fetch: leaving edit mode rebuilds the mesh data
    uv = me.uv_layers.active.data

    def uv_area(p):
        a, b, c = (uv[li].uv.copy() for li in p.loop_indices)
        return abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2.0

    print("AF7 UV coverage: %.1f%% of the texture" % (100.0 * sum(uv_area(p) for p in me.polygons)))


def decimated(src, col, name, ratio):
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    col.objects.link(ob)
    mod = ob.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.clear()
    old, ob.data = ob.data, me
    bpy.data.meshes.remove(old)
    me.name = name
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
    scene.render.bake.margin = 16
    scene.render.bake.use_clear = True
    scene.render.bake.use_selected_to_active = False
    if scene.world:
        scene.world.light_settings.distance = 0.04
    hidden = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o is not ob
    activate(ob)

    def target(tag, colorspace, fill):
        name = PREFIX + "Bake_" + tag
        if name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[name])
        img = bpy.data.images.new(name, size, size, alpha=False)
        img.generated_color = fill
        img.colorspace_settings.name = colorspace
        for m in mats:
            nt = m.node_tree
            node = nt.nodes.get(PREFIX + "BAKE") or nt.nodes.new("ShaderNodeTexImage")
            node.name = PREFIX + "BAKE"
            node.image = img
            for n in nt.nodes:
                n.select = False
            node.select = True
            nt.nodes.active = node
        return img

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
                img = target(tag, cs, (0, 0, 0, 1))
                surface(tap)
                bpy.ops.object.bake(type="EMIT")
                result[tag + suffix] = _pixels(img)
                print("AF7 baked", tag + suffix)
        set_skin(0.0)
        surface(None)
        scene.cycles.samples = SAMPLES["NORMAL"]
        img = target("normal", "Non-Color", (0.5, 0.5, 1.0, 1.0))
        # DayZ / Arma normal maps are DirectX style (green pointing down)
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="NEG_Y", normal_b="POS_Z")
        result["normal"] = _pixels(img)
        print("AF7 baked normal")
        scene.cycles.samples = SAMPLES["AO"]
        img = target("ao", "Non-Color", (1, 1, 1, 1))
        bpy.ops.object.bake(type="AO")
        result["ao"] = _pixels(img)
        print("AF7 baked ao")
    finally:
        set_skin(0.0)
        surface(None)
        for o, h in hidden.items():
            o.hide_render = h
        scene.render.engine = saved_engine

    ao = np.clip(result["ao"][..., 0], 0, 1)
    one = np.ones_like(ao)
    base_metal = np.clip(result["metal"][..., 0], 0, 1)
    amb = np.stack([one, ao, one, one], axis=-1)           # green = ambient shadow
    nohq = result["normal"].copy()
    nohq[..., 3] = 1
    outputs = [("nohq", nohq, "Non-Color"), ("as", amb, "Non-Color")]

    for suffix, _value in skins:
        rough = np.clip(result["rough" + suffix][..., 0], 0, 1)
        metal = np.clip(result["metal" + suffix][..., 0], 0, 1)
        co = result["color" + suffix].copy()
        co[..., :3] *= (0.78 + 0.22 * ao)[..., None]      # a little baked-in contact shadow
        co[..., 3] = 1
        # Levels matched to the vanilla m4_body_smdi (specular median 0.13, gloss median 0.39).
        # Anything much higher washes the rifle out to white under DayZ's lighting.
        spec = np.clip(0.05 + 0.12 * metal, 0, 1)
        gloss = np.clip((1.0 - rough) * 0.75, 0, 1)
        if not suffix:
            co[..., :3] *= 0.85                           # DayZ lights colour maps brightly
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

    os.makedirs(tex_dir, exist_ok=True)
    files = {}
    for suffix, data, cs in outputs:
        path = os.path.join(tex_dir, "af7_body_%s.png" % suffix)
        files[suffix] = _save("af7_body_" + suffix, data, path, cs)
        print("AF7 wrote", path)
    for tag in list(result):
        img = bpy.data.images.get(PREFIX + "Bake_" + tag)
        if img:
            bpy.data.images.remove(img)
    return files


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
    met.inputs[1].default_value, met.inputs[2].default_value = (0.0, 1.0) if skin else (0.05, 0.17)
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


def single_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0


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

    def add_proxy(self, path, origin, up, direction, extra=()):
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
        for name in ("proxy:%s.001" % path,) + tuple(extra):
            self.select(name, range(base, base + 3), [fi])


def lod_from_mesh(ob, resolution, texture, material):
    me = ob.data
    lod = Lod(resolution)
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
        lod.faces.append((verts, texture, material))
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
    p3d_path = os.path.join(repo, "source", "AF_Weapons", "af7_vanguard", "af7_vanguard.p3d")
    M = export_matrix()
    col = dayz_collection()

    # Bake in the working frame (the logo and wear are projected by position there),
    # then move the finished mesh into the M4 frame.
    lod1 = build_lod1(col, Matrix.Identity(4))
    unwrap(lod1)
    if bake:
        files = bake_textures(lod1, tex_dir, tex_size)
        if "gold_co" in files:   # kept in the file so you can swap it onto AF7_LOD_1 to preview the skin
            game_material(files, "Body_DayZ_Gold", "gold_")
        single_material(lod1, game_material(files))
    lod1.data.transform(M)
    lod1.data.update()

    visual = [(1.0, lod1)]
    for res, ratio in ((2.0, 0.75), (3.0, 0.5), (4.0, 0.36)):   # generous: the rifle keeps its shape at distance
        ob = decimated(lod1, col, "%sLOD_%d" % (PREFIX, int(res)), ratio)
        ob["dayz"] = "Resolution LOD %d (about %d%% of LOD 1)." % (int(res), int(ratio * 100))
        visual.append((res, ob))

    proxies = []
    for short, (path, up, direction, extra) in PROXIES.items():
        e = bpy.data.objects.get(PREFIX + short)
        if e:
            proxies.append((path, P(M @ e.matrix_world.translation), up, direction, extra))

    lods = []
    for res, ob in visual + [(LOD_VIEW_PILOT, lod1)]:
        lod = lod_from_mesh(ob, res, P3D_TEXTURE, P3D_MATERIAL)
        for path, origin, up, direction, extra in proxies:
            lod.add_proxy(path, origin, up, direction, extra)
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
        bpy.ops.export_scene.fbx(filepath=os.path.join(here, "export", "af7_vanguard_lod1.fbx"),
                                 use_selection=True, object_types={"MESH"}, axis_forward="Y", axis_up="Z")
        print("AF7 wrote FBX")
    except Exception as exc:
        print("AF7 FBX export skipped:", exc)
    return lod1


if __name__ == "__main__":
    export()
    print("AF-7 Vanguard DayZ export finished.")
