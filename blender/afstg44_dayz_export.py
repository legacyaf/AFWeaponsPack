"""
AF StG 44 - DayZ export (Blender 4.2+ / tested on 5.3).

Run AFTER afstg44_detailed.py in the same Blender file.

A thin wrapper: all the work (LODs, UVs, baking, the .p3d writer) is done by
af7_vanguard_dayz_export.py. This file only sets the tables, three times: for the rifle
(export), for its magazine (export_magazine) and for its scope (export_scope).

The rifle follows the vanilla AKM (dz\\weapons\\firearms\\AKM\\akm.p3d): bone names, proxy
paths and orientations, memory point names. It is built on x = 0 and shifted onto the AKM's
centre line (x = -0.0102) by the empty 'Origin' (ORIGIN_EMPTY).

The scope is an optic of its own (slot weaponOpticsAFStG, see config.cpp). Its reticle and
lens glass are flat faces with the vanilla PU scope's textures and materials (ex.RAW_QUADS).

WHAT IT MAKES
  blender/textures/afstg44_body_*.png, afstg44_wood_*.png, afstg44_mag_*.png, afzf4_*.png
  source/AF_Weapons/afstg44/afstg44.p3d, afstg44_mag.p3d and afzf4.p3d
"""

import math
import os
import sys

import bpy


def _here():
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand and os.path.isdir(os.path.dirname(cand)):
            return os.path.dirname(os.path.abspath(cand))
    raise RuntimeError("Save the .blend next to this script first.")


if _here() not in sys.path:
    sys.path.insert(0, _here())
import af7_vanguard_dayz_export as ex  # noqa: E402

AK_MAG = "\\dz\\weapons\\attachments\\magazine\\magazine_akm_30rnd"
SCOPE_P3D = "\\af_weapons\\afstg44\\afzf4"
WRAP = "\\dz\\weapons\\attachments\\support\\ghillie_wrap"
OPTICS = "dz\\weapons\\attachments\\optics\\data\\"


def _common():
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    ex.P3D_FOLDER = "afstg44"
    ex.MOD_DIR = "af_weapons\\afstg44"
    ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\metalplate.rvmat"
    ex.RAW_QUADS = ()
    ex.LOD1_EDIT = None
    # Steel as on the MP40 and P08, whose level was settled against vanilla guns in the in-game tests.
    ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.18, 0.88, 0.90
    # Bare steel shines (the vanilla AKM's specular map reaches 0.7 at its 90th percentile); parts
    # seen through openings are not left pitch black by the ambient-shadow map.
    ex.SPEC_WORN, ex.AO_FLOOR = 0.30, 0.30
    ex.EDGE_PAD = True


def _gun_tables():
    _common()
    ex.PREFIX = "STG_"
    ex.ORIGIN_EMPTY = "Origin"
    ex.TEX_NAME = "afstg44_body"
    ex.P3D_FILE = "afstg44"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afstg44_body_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afstg44_body.rvmat"
    ex.MASS_KG = 4.6
    ex.SKINS = (("", 0.0), ("_gold", 1.0))            # gold = black furniture with the gold floral pattern
    ex.EXTRA_SETS = (("afstg44_wood", ("Beech",)),)    # stock and grip panels
    ex.BODY_BONE = None                               # the AKM's bones have no parents
    ex.SELECTIONS = {"Weapon_Trigger": "trigger", "BoltCarrier": "bolt", "CockingHandle": "bolt"}
    ex.HIDE_BARREL = ("MuzzleNut",)
    ex.UV_PRIORITY = {
        "Receiver": 1.4, "RearSightBase": 1.4, "RearSightLeaf": 1.4, "RearSightNotch": 1.6, "RearSightSlider": 1.4,
        "FrontSightPost": 1.5, "FrontSightHood": 1.2, "CockingHandle": 1.4, "BoltCarrier": 0.5, "Weapon_Trigger": 1.3,
        "TriggerHousing": 1.2, "MagWell": 1.2, "ScopeRail": 1.2, "Selector": 1.2,
        "Barrel": 0.7, "GasTube": 0.8, "Stock": 0.9, "ButtPlate": 0.7, "HingePin": 0.8, "SearPin": 0.8,
        "SlingLoopFront": 0.7, "SlingLoopRear": 0.7,
    }
    ex.LOD1_EDIT = _reshape_notch
    ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
                 "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend"}
    # (p3d path, up axis, dir axis, extra selections). In the vanilla model's 3x3 proxy matrix the second
    # row is 'up' and the third row is 'dir'. The magazine and scope proxies are upright (the AKM's
    # magazine leans 20.7 degrees); the game shows whatever is attached to the slot at the proxy.
    ex.PROXIES = {
        "Proxy_Magazine": (AK_MAG, (0, 1, 0), (0, 0, 1), ("magazine",)),
        "Proxy_Scope": (SCOPE_P3D, (0, 1, 0), (0, 0, 1), ()),
        "Proxy_Suppressor": ("\\dz\\weapons\\attachments\\muzzle\\suppressor_545", (1, 0, 0), (0, 0, 1), ()),
        "Proxy_Bottle": ("\\dz\\weapons\\attachments\\muzzle\\bottle_suppressor", (1, 0, 0), (0, 0, -1), ()),
        "Proxy_Wrap1": (WRAP, (0, 1, 0), (0, 0, 1), ()),
        "Proxy_Wrap2": (WRAP, (0, 1, 0), (0, 0, -1), ()),
    }
    # Collision boxes in the working frame (min xyz, max xyz)
    ex.GEOMETRY = [((-0.019, -0.406, 0.016), (0.019, -0.152, 0.136)),      # stock
                   ((-0.020, -0.150, 0.044), (0.022, 0.105, 0.152)),       # receiver and trigger housing
                   ((-0.016, -0.158, -0.040), (0.016, -0.086, 0.058)),     # pistol grip
                   ((-0.022, 0.105, 0.072), (0.022, 0.470, 0.152))]        # handguard, barrel and sights


NOTCH = dict(zb=0.1461, z_old=0.1520, z_new=0.1500, x_old=0.0014, x_new=0.0022, x_out=0.0070)


def _reshape_notch(lod1, M):
    """The rear sight's V notch as first built sat 2 mm above the front post and was 2.8 mm wide: in
    game the post hid behind it. Its top is now on the sight line (the post's top) and the V is 4.4 mm
    wide. This moves the vertices of the notch in LOD 1 as kept from the .p3d, so the baked textures
    stay valid (the notch's own texels stretch a little; they are plain steel). afstg44_detailed.py
    builds the same shape, for the distance LODs and for the next bake."""
    import zlib
    me = lod1.data
    part = me.attributes.get("af7_part")
    pid = zlib.crc32(b"RearSightNotch") & 0x7FFFFFFF
    mine = {p.index for p in me.polygons if part.data[p.index].value == pid}
    owner = {}
    for p in me.polygons:
        for v in p.vertices:
            owner.setdefault(v, set()).add(p.index in mine)
    verts = [v for v, s in owner.items() if s == {True}]
    shared = sum(1 for v, s in owner.items() if s == {True, False})
    n = NOTCH
    Mi = M.inverted()
    for i in verts:
        w = Mi @ me.vertices[i].co
        if w.z > n["zb"]:
            w.z = n["zb"] + (w.z - n["zb"]) * (n["z_new"] - n["zb"]) / (n["z_old"] - n["zb"])
        ax = abs(w.x)
        if ax <= n["x_old"]:
            ax *= n["x_new"] / n["x_old"]
        elif ax < n["x_out"]:
            ax = n["x_new"] + (ax - n["x_old"]) * (n["x_out"] - n["x_new"]) / (n["x_out"] - n["x_old"])
        w.x = ax if w.x >= 0 else -ax
        me.vertices[i].co = M @ w
    me.update()
    print("STG rear sight notch reshaped: %d faces, %d vertices moved, %d shared with other parts (left)" % (len(mine), len(verts), shared))


def _magazine_tables():
    _common()
    ex.PREFIX = "STGM_"
    ex.ORIGIN_EMPTY = None
    ex.TEX_NAME = "afstg44_mag"
    ex.P3D_FILE = "afstg44_mag"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afstg44_mag_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afstg44_mag.rvmat"
    ex.MASS_KG = 0.4
    ex.SKINS = (("", 0.0),)
    ex.EXTRA_SETS = ()
    ex.BODY_BONE = None
    ex.SELECTIONS = {}
    ex.HIDE_BARREL = ()
    ex.UV_PRIORITY = {"Round": 0.8, "RoundSlug": 0.8}
    ex.MEMORY = {}
    ex.PROXIES = {}
    ex.GEOMETRY = [((-0.0145, -0.0320, -0.1850), (0.0145, 0.1000, 0.0360))]


def _scope_tables():
    import afstg44_detailed as model
    _common()
    ex.PREFIX = "STGS_"
    ex.ORIGIN_EMPTY = None
    ex.TEX_NAME = "afzf4"
    ex.P3D_FILE = "afzf4"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afzf4_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afzf4.rvmat"
    ex.MASS_KG = 0.6
    ex.SKINS = (("", 0.0),)
    ex.EXTRA_SETS = ()
    ex.BODY_BONE = None
    ex.SELECTIONS = {}
    ex.HIDE_BARREL = ()
    ex.UV_PRIORITY = {"Tube": 1.2, "Turrets": 1.2, "TubeInside": 0.3}
    ex.MEMORY = {"Mem_EyeScope": "eyescope", "Mem_CameraDir": "cameradir"}
    ex.PROXIES = {}
    ex.GEOMETRY = [((-0.016, model.SCOPE_REAR, -0.026), (0.020, model.SCOPE_FRONT, 0.026))]
    # Reticle in the middle of the tube, lens glass at both ends: the vanilla PU scope's own textures.
    # Round, not square: each is a fan of quads filling the bore exactly where it sits (the square
    # reticle showed its black corners as a black square round the view, in game on 2026-11-22/23).
    # The reticle texture's clear circle reaches about 0.96 of its width, so the disc edge is mapped there.
    def disc(y, r, texture, material, uv_r=0.5, n=12):
        quads = []
        for k in range(n):
            a = [2 * math.pi * (k + t / 2.0) / n + math.pi for t in (0, 1, 2)]
            pts = [(0.0, 0.0)] + [(r * math.cos(t), r * math.sin(t)) for t in a]
            corners = tuple((x, y, z) for x, z in pts)
            uvs = tuple((0.5 + uv_r * x / r, 0.5 - uv_r * z / r) for x, z in pts)
            quads.append((corners, uvs, texture, material, 3.0))
        return tuple(quads)
    clear = "dz\\weapons\\attachments\\data\\scope_alpha_clear_ca.paa"
    ex.RAW_QUADS = (disc(model.SCOPE_REAR + 0.0400, 0.0107, OPTICS + "reticle_pu_ca.paa", OPTICS + "forceddiffuse.rvmat", 0.48)
                    + disc(model.SCOPE_REAR + 0.0030, 0.0117, clear, OPTICS + "lensglass_standard.rvmat")
                    + disc(model.SCOPE_FRONT - 0.0030, 0.0125, clear, OPTICS + "lensglass_standard.rvmat"))


def export(bake=True, tex_size=ex.TEX_SIZE):
    _gun_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_magazine(bake=True, tex_size=1024):
    _magazine_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_scope(bake=True, tex_size=1024):
    _scope_tables()
    return ex.export(bake=bake, tex_size=tex_size)


if __name__ == "__main__":
    export()
    export_magazine()
    export_scope()
    print("AF StG 44 DayZ export finished.")
