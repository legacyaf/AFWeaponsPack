"""
AF P08 - DayZ export (Blender 4.2+ / tested on 5.3).

Run AFTER afp08_detailed.py in the same Blender file.

A thin wrapper: all the work (LODs, UVs, baking, the .p3d writer) is done by
af7_vanguard_dayz_export.py. This file only sets the tables, twice: once for the pistol
(export) and once for its magazine (export_magazine), which is a model of its own.

Everything follows the vanilla P1 (dz\\weapons\\pistols\\p1\\p1.p3d): bone names, proxy paths
and orientations, memory point names. The pistol is already built in the P1's frame, so there
is no origin shift (ORIGIN_EMPTY = None).

WHAT IT MAKES
  blender/textures/afp08_body_*.png, afp08_mag_*.png
  source/AF_Weapons/afp08/afp08.p3d and afp08_mag.p3d
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

P1_MAG = "\\dz\\weapons\\attachments\\magazine\\magazine_p1"


def _common():
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    ex.P3D_FOLDER = "afp08"
    ex.ORIGIN_EMPTY = None
    ex.MOD_DIR = "af_weapons\\afp08"
    ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\armor_3mm_plate.rvmat"     # as on the vanilla P1
    # The materials use the M41's lighting values (specular 0.4, power 50). Steel as on the MP40,
    # whose level was settled against vanilla guns in the in-game tests.
    ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.20, 0.88, 0.90


def _gun_tables():
    _common()
    ex.PREFIX = "P08_"
    ex.TEX_NAME = "afp08_body"
    ex.P3D_FILE = "afp08"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afp08_body_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afp08_body.rvmat"
    ex.MASS_KG = 0.87
    ex.SKINS = (("", 0.0), ("_gold", 1.0))            # gold = black grips with the gold floral pattern
    ex.EXTRA_SETS = ()                                # one texture set is plenty for a pistol
    # The P1's frame is on the bone 'recoil'; its slide is on 'bolt' (a child of recoil).
    ex.BODY_BONE = "recoil"
    ex.SELECTIONS = {"Weapon_Trigger": "trigger", "BreechBlock": "bolt", "Extractor": "bolt"}
    ex.HIDE_BARREL = ()
    ex.UV_PRIORITY = {
        "ToggleKnob_R": 1.4, "ToggleKnob_L": 1.4, "ToggleRearLink": 1.4, "ToggleFrontLink": 1.4, "RearSight": 1.6,
        "BreechBlock": 1.3, "Extractor": 1.3, "FrontSightBlade": 1.5, "Receiver": 1.2, "GripPanels": 1.2,
        "Weapon_Trigger": 1.2, "SafetyLever": 1.2, "TakedownLever": 1.2,
        "TriggerPin": 0.8, "FramePin": 0.8, "ToggleAxle": 0.8, "LanyardLoop": 0.8, "StockLug": 0.8,
    }
    ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
                 "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend"}
    # (p3d path, up axis, dir axis, extra selections). In the vanilla model's 3x3 proxy matrix the
    # second row is 'up' and the third row is 'dir'; these are the P1's own rows.
    ex.PROXIES = {
        "Proxy_Magazine": (P1_MAG, (0, 1, 0), (0, 0, 1), ("magazine",)),
        "Proxy_Bottle": ("\\dz\\weapons\\attachments\\muzzle\\bottle_suppressor", (1, 0, 0), (0, 0, -1), ("recoil",)),
        "Proxy_Suppressor": ("\\dz\\weapons\\attachments\\muzzle\\suppressor_45acp", (1, 0, 0), (0, 0, 1), ("recoil",)),
    }
    # Collision boxes in the working frame (min xyz, max xyz)
    ex.GEOMETRY = [((-0.013, -0.014, 0.034), (0.013, 0.114, 0.082)),      # frame and receiver
                   ((-0.007, 0.114, 0.060), (0.007, 0.205, 0.084)),       # barrel
                   ((-0.016, -0.030, -0.050), (0.016, 0.064, 0.034))]     # grip


def _magazine_tables():
    _common()
    ex.PREFIX = "P08M_"
    ex.TEX_NAME = "afp08_mag"
    ex.P3D_FILE = "afp08_mag"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afp08_mag_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afp08_mag.rvmat"
    ex.MASS_KG = 0.08
    ex.SKINS = (("", 0.0),)
    ex.EXTRA_SETS = ()
    ex.BODY_BONE = None
    ex.SELECTIONS = {}
    ex.HIDE_BARREL = ()
    ex.UV_PRIORITY = {"Round": 0.8, "RoundSlug": 0.8, "FollowerButton": 0.8}
    ex.MEMORY = {}
    ex.PROXIES = {}
    ex.GEOMETRY = [((-0.0075, -0.0400, -0.0580), (0.0075, 0.0370, 0.0560))]


def export(bake=True, tex_size=ex.TEX_SIZE):
    _gun_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_magazine(bake=True, tex_size=1024):
    _magazine_tables()
    return ex.export(bake=bake, tex_size=tex_size)


if __name__ == "__main__":
    export()
    export_magazine()
    print("AF P08 DayZ export finished.")
