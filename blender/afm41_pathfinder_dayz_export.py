"""
AF M41 "Pathfinder" - DayZ export (Blender 4.2+ / tested on 5.3).

Run AFTER afm41_pathfinder_detailed.py in the same Blender file.

This is a thin wrapper: all the work (LODs, UVs, baking, the .p3d writer) is done by
af7_vanguard_dayz_export.py. Only the per-weapon tables are set here. A third weapon
needs a copy of this file with its own tables, nothing more.

Everything follows the vanilla Mosin 91/30 (dz\\weapons\\firearms\\mosin9130\\mosin9130.p3d):
bone names, proxy paths and orientations, memory point names. The model is already
built in the Mosin's frame, so there is no origin shift (ORIGIN_EMPTY = None).

WHAT IT MAKES
  blender/textures/afm41_body_co.png, _nohq.png, _smdi.png, _as.png
  source/AF_Weapons/afm41_pathfinder/afm41_pathfinder.p3d
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

ex.PREFIX = "M41_"
ex.TEX_NAME = "afm41_body"
ex.P3D_FOLDER = "afm41_pathfinder"
ex.P3D_FILE = "afm41_pathfinder"
ex.ORIGIN_EMPTY = None
ex.MOD_DIR = "af_weapons\\afm41_pathfinder"
ex.P3D_TEXTURE = ex.MOD_DIR + "\\data\\afm41_body_co.paa"
ex.P3D_MATERIAL = ex.MOD_DIR + "\\data\\afm41_body.rvmat"
ex.FIRE_MATERIAL = "dz\\data\\data\\penetration\\wood.rvmat"     # same as the vanilla Mosin
ex.MASS_KG = 4.0
ex.SKINS = (("", 0.0), ("_gold", 1.0))   # gold = black furniture with gold floral, like the AF-7 Gold
# Matched to the vanilla mosin_9130_smdi (specular: wood about 0.05, steel up to 0.7; gloss 0.42-0.65),
# because the rifle uses the Mosin's material values (specular 0.4, power 50).
ex.SPEC_BASE, ex.SPEC_METAL, ex.GLOSS_SCALE, ex.CO_SCALE = 0.06, 0.50, 0.90, 0.90

# Blender object (without M41_) -> vanilla Mosin skeleton bone
ex.SELECTIONS = {"Weapon_Trigger": "trigger", "BoltBody": "boltbody", "BoltHandle": "bolthandle",
                 "BoltCocking": "boltbodys",
                 # The vanilla model carries two display rounds in the magazine, on these two bones.
                 "Round_Top": "bullet1", "Round_TopSlug": "bullet1", "Round_Low": "bullet", "Round_LowSlug": "bullet"}
ex.HIDE_BARREL = ("MuzzleCrown",)

ex.UV_PRIORITY = {
    "Receiver": 1.6, "ReceiverRing": 1.5, "BoltBody": 1.5, "BoltHandle": 1.6, "BoltCocking": 1.5,
    "RearSightBase": 1.5, "RearSightLeaf": 1.5, "RearSightNotch": 1.6, "RearSightSlider": 1.5,
    "FrontSightPost": 1.5, "FrontSightBlock": 1.3, "StockDisc_R": 2.2, "StockDisc_L": 2.2,
    "Weapon_Trigger": 1.3, "TriggerGuard": 1.2,
    "Round_Top": 0.7, "Round_TopSlug": 0.7, "Round_Low": 0.5, "Round_LowSlug": 0.5, "MagazineBox": 0.5,
    "Sling": 0.7, "SlingKeeper_F": 0.6, "SlingKeeper_R": 0.6, "Stock": 0.85, "Barrel": 0.6, "CleaningRod": 0.6, "ButtPlate": 0.7, "CrossBolt": 0.8,
}

ex.MEMORY = {"Mem_Muzzle": "usti hlavne", "Mem_BarrelEnd": "konec hlavne", "Mem_Eye": "eye",
             "Mem_EyeScope": "eyescope", "Mem_CaseStart": "nabojnicestart", "Mem_CaseEnd": "nabojniceend"}

# (p3d path, up axis, dir axis, extra selections) - orientations read from the vanilla model
ex.PROXIES = {
    "Proxy_Optic": ("\\dz\\weapons\\attachments\\optics\\optic_puscope", (1, 0, 0), (0, 0, -1), ()),
    "Proxy_Compensator": ("\\dz\\weapons\\attachments\\muzzle\\mosin_compensator", (0, 1, 0), (0, 0, 1), ()),
    "Proxy_Suppressor": ("\\dz\\weapons\\attachments\\muzzle\\bottle_suppressor", (1, 0, 0), (0, 0, -1), ()),
    "Proxy_Bayonet": ("\\dz\\weapons\\attachments\\muzzle\\bayonet_mosin", (-1, 0, 0), (0, 0, 1), ()),
    # Ghillie wrap (slot weaponWrap): the vanilla Mosin carries three proxies of the same model,
    # on the receiver, on the handguard and under the butt. Order matters: .001, .002, .003.
    "Proxy_Wrap1": ("\\dz\\weapons\\attachments\\support\\ghillie_wrap", (0, 1, 0), (0, 0, 1), ()),
    "Proxy_Wrap2": ("\\dz\\weapons\\attachments\\support\\ghillie_wrap", (0, 1, 0), (0, 0, -1), ()),
    "Proxy_Wrap3": ("\\dz\\weapons\\attachments\\support\\ghillie_wrap", (0.1001, 0.99498, 0), (0, 0, -1), ()),
}

# Collision boxes in the working frame (min xyz, max xyz)
ex.GEOMETRY = [((-0.021, -0.409, -0.043), (0.021, -0.130, 0.100)),    # butt
               ((-0.021, -0.130, 0.022), (0.021, 0.240, 0.140)),      # action
               ((-0.019, 0.240, 0.070), (0.019, 0.670, 0.137)),       # fore-end
               ((-0.009, 0.670, 0.092), (0.009, 0.8305, 0.141))]      # barrel


def export(bake=True, tex_size=ex.TEX_SIZE):
    ex.__file__ = os.path.join(_here(), "af7_vanguard_dayz_export.py")
    return ex.export(bake=bake, tex_size=tex_size)


if __name__ == "__main__":
    export()
    print("AF M41 Pathfinder DayZ export finished.")
