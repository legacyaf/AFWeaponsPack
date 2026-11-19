"""
AF MP40 - DayZ export (Blender 4.2+ / tested on 5.3).

Run AFTER afmp40_detailed.py in the same Blender file.

A thin wrapper: all the work (LODs, UVs, baking, the .p3d writer) is done by
af7_vanguard_dayz_export.py. This file only sets the tables, twice: once for the gun
(export) and once for its magazine (export_magazine), which is a model of its own.

Everything follows the vanilla UMP-45 (dz\\weapons\\firearms\\UMP45\\ump.p3d): bone names,
proxy paths and orientations, memory point names. The gun is already built in the UMP's
frame, so there is no origin shift (ORIGIN_EMPTY = None).

WHAT IT MAKES
  blender/textures/afmp40_body_*.png, afmp40_furn_*.png, afmp40_mag_*.png
  source/AF_Weapons/afmp40/afmp40.p3d and afmp40_mag.p3d
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

UMP_MAG = "\\dz\\weapons\\attachments\\magazine\\magazine_ump45_25rnd"


def _common():
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    ex.P3D_FOLDER = "afmp40"
    ex.ORIGIN_EMPTY = None
    ex.MOD_DIR = "af_weapons\\afmp40"
    ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\metalplate.rvmat"     # as on the vanilla UMP
    # The materials use the Mosin's lighting values (specular 0.4, power 50), like the M41.
    # Much less specular than the M41 (0.50; tried 0.32 first): in the in-game tests the big smooth receiver tube
    # reflected the sky and read light grey next to the vanilla UMP.
    ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.18, 0.88, 0.90


def _gun_tables():
    _common()
    ex.PREFIX = "MP40_"
    ex.TEX_NAME = "afmp40_body"
    ex.P3D_FILE = "afmp40"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afmp40_body_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afmp40_body.rvmat"
    ex.MASS_KG = 4.0
    ex.SKINS = (("", 0.0), ("_gold", 1.0))            # gold = black furniture with the gold floral pattern
    ex.EXTRA_SETS = (("afmp40_furn", ("Bakelite",)),)  # lower frame, grip panels and resting bar
    # The UMP's whole body is on the bone 'recoil'; bolt and charging handle are its children.
    ex.BODY_BONE = "recoil"
    ex.SELECTIONS = {"Weapon_Trigger": "trigger", "Bolt": "bolt", "CockingHandle": "charging"}
    ex.HIDE_BARREL = ("MuzzleNut",)
    ex.UV_PRIORITY = {
        "Receiver": 1.5, "Bolt": 1.4, "CockingHandle": 1.5, "RearSightBase": 1.5, "RearSightNotch": 1.6,
        "RearSightLeaf": 1.5, "RearSightEar_R": 1.5, "RearSightEar_L": 1.5, "FrontSightPost": 1.5,
        "FrontSightHood": 1.3, "EndCap": 1.3, "MagHousing": 1.2, "MagRelease": 1.3, "Weapon_Trigger": 1.3,
        "LowerFrame": 1.2, "GripPanels": 1.1,
        "SpringTube": 0.5, "Barrel": 0.7, "StockStrut_R": 0.7, "StockStrut_L": 0.7, "ButtPlate": 0.7,
        "ButtPlateRibs": 0.7, "ButtHinge": 0.7, "TriggerPin": 0.8, "FramePin": 0.8, "SearPin": 0.8,
    }
    ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
                 "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend"}
    # (p3d path, up axis, dir axis, extra selections). In the vanilla model's 3x3 proxy matrix the
    # second row is 'up' and the third row is 'dir'. The magazine proxy is upright here (the UMP's
    # leans 13 degrees); the game shows whatever magazine is attached at this proxy.
    ex.PROXIES = {
        "Proxy_Magazine": (UMP_MAG, (0, 1, 0), (0, 0, 1), ("magazine",)),
        "Proxy_Suppressor": ("\\dz\\weapons\\attachments\\muzzle\\suppressor_45acp", (1, 0, 0), (0, 0, 1), ("recoil",)),
        "Proxy_Wrap": ("\\dz\\weapons\\attachments\\support\\ghillie_wrap", (0, 1, 0), (0, 0, -1), ("recoil",)),
    }
    # Collision boxes in the working frame (min xyz, max xyz)
    ex.GEOMETRY = [((-0.020, -0.187, 0.020), (0.020, 0.154, 0.092)),     # receiver and lower frame
                   ((-0.011, 0.154, 0.038), (0.011, 0.403, 0.110)),      # barrel and resting bar
                   ((-0.016, -0.160, -0.078), (0.016, -0.072, 0.030)),   # pistol grip
                   ((-0.022, -0.392, -0.068), (0.022, -0.160, 0.052))]   # stock


def _magazine_tables():
    _common()
    ex.PREFIX = "MP40M_"
    ex.TEX_NAME = "afmp40_mag"
    ex.P3D_FILE = "afmp40_mag"
    ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afmp40_mag_co.paa"
    ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afmp40_mag.rvmat"
    ex.MASS_KG = 0.35
    ex.SKINS = (("", 0.0),)
    ex.EXTRA_SETS = ()
    ex.BODY_BONE = None
    ex.SELECTIONS = {}
    ex.HIDE_BARREL = ()
    ex.UV_PRIORITY = {"Round": 0.8, "RoundSlug": 0.8, "FloorCatch": 0.8}
    ex.MEMORY = {}
    ex.PROXIES = {}
    ex.GEOMETRY = [((-0.0135, -0.0200, -0.1050), (0.0135, 0.0200, 0.1060))]


def export(bake=True, tex_size=ex.TEX_SIZE):
    _gun_tables()
    return ex.export(bake=bake, tex_size=tex_size)


def export_magazine(bake=True, tex_size=2048):
    _magazine_tables()
    return ex.export(bake=bake, tex_size=tex_size)


if __name__ == "__main__":
    export()
    export_magazine()
    print("AF MP40 DayZ export finished.")
