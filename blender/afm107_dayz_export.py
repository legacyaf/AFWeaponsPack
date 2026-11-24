"""
AF M107A1 - DayZ export (Blender 5.3).

A thin wrapper round af7_vanguard_dayz_export.py (LODs, UVs, baking, the .p3d writer): it only sets
the tables, three times - the rifle (export), its magazine (export_magazine) and its built-in scope
(export_scope).

The rifle follows the vanilla SVD (dz\\weapons\\firearms\\svd\\svd.p3d): its skeleton (magazine,
trigger, bolt, firemode, bullet, mag_release, no parents), its memory point names, and its magazine
proxy path and position, all measured in game (docs/M107.md). The model is built in the SVD's own
frame, so there is no origin shift (ORIGIN_EMPTY = None).

WHAT IT MAKES
  blender/textures/afm107_body_*.png, afm107_mag_*.png, afm107_scope_*.png
  source/AF_Weapons/afm107/afm107.p3d, afm107_mag.p3d, afm107_scope.p3d
"""

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
import afm107_detailed as model  # noqa: E402

SVD_MAG = "\\dz\\weapons\\attachments\\magazine\\magazine_svd"
SCOPE_P3D = "\\af_weapons\\afm107\\afm107_scope"
Y, Zm, fx, P = model.Y, model.Zm, model.fx, model.P


def _common():
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    ex.P3D_FOLDER = "afm107"
    ex.MOD_DIR = "af_weapons\\afm107"
    ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\metalplate.rvmat"
    ex.RAW_QUADS = ()
    ex.LOD1_EDIT = None
    ex.SOFT_SETS = ()
    ex.HIGH_DETAIL, ex.HIGH_EDGE_STEPS = None, None
    ex.SPEC_VAR, ex.SPEC_CAVITY, ex.SPEC_SET_BASE = 0.60, 0.35, {}
    ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.18, 0.88, 0.90
    ex.SPEC_WORN, ex.AO_FLOOR = 0.30, 0.30
    ex.EDGE_PAD = True
    ex.ORIGIN_EMPTY = None
    ex.BODY_BONE = None
    ex.SKINS = (("", 0.0),)
    ex.EXTRA_SETS = ()
    ex.HIDE_BARREL = ()
    ex.PROXIES = {}
    ex.SELECTIONS = {}
    ex.UV_PRIORITY = {}
    ex.MEMORY = {}


def _box(x0, x1, y0, y1, z0, z1):
    return ((x0, y0, z0), (x1, y1, z1))


def _gun_tables():
    _common()
    ex.PREFIX = "M107_"
    ex.TEX_NAME = "afm107_body"
    ex.P3D_FILE = "afm107"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afm107_body_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afm107_body.rvmat"
    ex.MASS_KG = 12.5
    ex.SELECTIONS = {"Weapon_Trigger": "trigger", "BoltCarrier": "bolt"}
    ex.UV_PRIORITY = {"UpperReceiver": 1.2, "Handguard": 1.2, "BoltCarrier": 0.5, "Barrel": 0.8, "LockPins": 0.6}
    ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
                 "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend", "Mem_TriggerAxis": "trigger_axis",
                 "Mem_BoltAxis": "bolt_axis", "Mem_MagAxis": "magazine_axis", "Mem_MagAxis2": "magazine_axis2"}
    # (p3d path, up axis, dir axis, extra selections): the magazine keeps the SVD's proxy path (the
    # game ties it to the magazine slot and shows whichever magazine is attached).
    ex.PROXIES = {
        "Proxy_Magazine": (SVD_MAG, (0, 1, 0), (0, 0, 1), ("magazine",)),
        "Proxy_Scope": (SCOPE_P3D, (0, 1, 0), (0, 0, 1), ()),
    }
    # Collision boxes in the working frame (min xyz, max xyz).
    ex.GEOMETRY = [
        _box(-0.027, 0.027, Y(-6), Y(fx(180)), Zm(-137), Zm(36)),             # butt, stock, rear grip
        _box(-0.038, 0.038, Y(fx(180)), Y(fx(560)), Zm(-94), Zm(61)),          # receiver, lower and rail
        _box(-0.036, 0.036, Y(fx(240)), Y(fx(505)), Zm(-217), Zm(-60)),        # grip and magazine well
        _box(-0.032, 0.032, Y(fx(560)), Y(fx(905)), Zm(-60), Zm(61)),          # handguard
        _box(-0.028, 0.028, Y(fx(905)), Y(fx(1443)), Zm(-28), Zm(28)),         # barrel and brake
    ]


def _magazine_tables():
    _common()
    ex.PREFIX = "M107M_"
    ex.TEX_NAME = "afm107_mag"
    ex.P3D_FILE = "afm107_mag"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afm107_mag_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afm107_mag.rvmat"
    ex.MASS_KG = 1.3
    mx0, mx1, mz0, mz1 = P["mag"]
    my, mz = model.MAG_PROXY[1], model.MAG_PROXY[2]
    ex.GEOMETRY = [_box(-0.032, 0.032, Y(mx0) - my, Y(mx1) - my, Zm(mz0) - mz - 0.005, Zm(mz1) - mz)]


def _scope_tables():
    _common()
    ex.PREFIX = "M107S_"
    ex.TEX_NAME = "afm107_scope"
    ex.P3D_FILE = "afm107_scope"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afm107_scope_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afm107_scope.rvmat"
    ex.MASS_KG = 1.1
    ex.MEMORY = {"Mem_EyeScope": "eyescope", "Mem_CameraDir": "cameradir"}
    ex.GEOMETRY = [_box(-0.040, 0.040, -0.195, 0.195, -0.035, 0.033)]


def export(bake=True, tex_size=ex.TEX_SIZE):
    _gun_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_magazine(bake=True, tex_size=1024):
    _magazine_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_scope(bake=True, tex_size=1024):
    _scope_tables()
    return ex.export(bake=bake, tex_size=tex_size)
