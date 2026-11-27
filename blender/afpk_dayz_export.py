"""
The PeaceKeeper - DayZ export (Blender 5.3).

A thin wrapper round af7_vanguard_dayz_export.py (LODs, UVs, baking, the .p3d writer): it sets the
tables twice, for the rifle (export) and for the AF stock (export_stock).

The rifle follows the vanilla SCAR-H (dz\\weapons\\firearms\\scarh\\scarh.p3d): its skeleton (magazine,
trigger, bolt, bullet, charging, firemode, boltrelease, front_sight, no parents), its memory point
names and its proxies, with the positions and orientations measured in game (docs/AF_SCAR.md). The
model is built in the SCAR-H's own frame, so there is no origin shift.

WHAT IT MAKES
  blender/textures/afpk_body_*.png, afpk_front_*, afpk_lower_*, afpk_parts_*, afpk_counter_*, afpk_stock_*
  source/AF_Weapons/afpk/afpk.p3d, afpk_stock.p3d
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
import afpk_detailed as model  # noqa: E402

ATT = "\\dz\\weapons\\attachments\\"


def _common():
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    ex.P3D_FOLDER = "afpk"
    ex.MOD_DIR = "af_weapons\\afpk"
    ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\metalplate.rvmat"
    ex.RAW_QUADS = ()
    ex.LOD1_EDIT = None
    ex.SOFT_SETS = ()
    # The professional bake settings of 0.13.0 (the StG 44's and the M107A1's).
    ex.HIGH_DETAIL = ("high", 4.0, 6, 7.5, True)
    ex.HIGH_EDGE_STEPS = ((0.0010, 6), (0.0005, 4), (0.0002, 2))
    ex.HIGH_CAGE, ex.HIGH_RAY = 0.0008, 0.0016
    ex.SAMPLES = dict(ex.SAMPLES, NORMAL=64)
    ex.SPEC_VAR, ex.SPEC_CAVITY, ex.SPEC_SET_BASE = 0.60, 0.35, {}
    ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.18, 0.88, 0.90
    ex.SPEC_WORN, ex.AO_FLOOR = 0.30, 0.30
    ex.EDGE_PAD = True
    ex.REGION_WEIGHTS = True
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
    ex.PREFIX = model.PREFIX
    ex.TEX_NAME = "afpk_body"
    ex.P3D_FILE = "afpk"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afpk_body_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afpk_body.rvmat"
    ex.MASS_KG = 3.6
    # Five sheets: the upper (set 0), the rails and muzzle, the polymer lower, the small parts, and the
    # round counter's display on its own (camo4), so the script can swap its texture for the count.
    ex.EXTRA_SETS = (("afpk_front", ("AnodisedRail",)),
                     ("afpk_lower", ("Polymer", "GripPolymer")),
                     ("afpk_parts", ("Steel", "Gold", "Red", "Orange")),
                     ("afpk_counter", ("Counter",)))
    ex.SELECTIONS = {"Trigger": "trigger", "BoltCarrier": "bolt", "ChargingHandle": "charging",
                     "ChargingKnob": "charging", "Safety": "firemode", "BoltRelease": "boltrelease"}
    ex.UV_PRIORITY = {"Upper": 1.2, "Lower": 1.2, "Grip": 1.1, "CounterDisplay": 2.0, "BoltCarrier": 0.5,
                      "LowerParts": 0.6, "RailScrews": 0.5}
    ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
                 "Mem_EyeScope": "eyescope", "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend",
                 "Mem_TriggerAxis": "trigger_axis", "Mem_BoltAxis": "bolt_axis",
                 "Mem_FrontSightAxis": "frontsight_axis", "Mem_MagOutAxis": "magout_axis",
                 "Mem_InvView": "invview", "Mem_CeCenter": "ce_center"}
    # (p3d path, up axis, dir axis, extra selections), as the probe read the vanilla attachments.
    ex.PROXIES = {
        "Proxy_Magazine": (ATT + "magazine\\magazine_scarh_20rnd", (0, 1, 0), (0, 0, 1), ("magazine",)),
        "Proxy_Stock": (ATT + "support\\buttstock_scar_stock", (1, 0, 0), (0, 0, 1), ()),
        "Proxy_Optic": (ATT + "optics\\optic_acog", (1, 0, 0), (0, 0, -1), ()),
        "Proxy_Light": (ATT + "light\\weaponlight_universal", (0, 1, 0), (0, 0, -1), ()),
        "Proxy_Suppressor": (ATT + "muzzle\\bottle_suppressor", (1, 0, 0), (0, 0, 1), ()),
        "Proxy_Wrap": (ATT + "support\\ghillie_wrap", (0, 1, 0), (0, 0, 1), ()),
    }
    # Collision boxes in the working frame (min xyz, max xyz).
    ex.GEOMETRY = [
        _box(-0.026, 0.026, model.REAR, model.UP_FRONT + 0.03, 0.058, 0.132),     # upper, rail, gas block
        _box(-0.023, 0.023, -0.122, 0.112, -0.073, 0.076),                         # lower, guard, grip, well
        _box(-0.014, 0.014, model.UP_FRONT + 0.03, model.MUZZLE, 0.074, 0.103),    # barrel and brake
    ]


def _stock_tables():
    _common()
    ex.PREFIX = model.STOCK_PREFIX
    ex.TEX_NAME = "afpk_stock"
    ex.P3D_FILE = "afpk_stock"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afpk_stock_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afpk_stock.rvmat"
    ex.MASS_KG = 0.6
    # In the stock slot's frame (afpk_detailed.STOCK_MATRIX): x across, y up the rifle, z backwards.
    ex.GEOMETRY = [_box(-0.023, 0.023, -0.081, 0.067, -0.112, 0.159)]


def export(bake=True, tex_size=ex.TEX_SIZE):
    _gun_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_stock(bake=True, tex_size=4096):
    _stock_tables()
    return ex.export(bake=bake, tex_size=tex_size)
