"""python blender/afpk_after_bake.py

Everything The PeaceKeeper's sheets need after a bake (blender/afpk_run.py), in order. Plain Python:
it starts Blender for each step and the DayZ Tools converter at the end.

1. Keeps the raw bake in blender/textures/afpk_raw_last (the levels pass reads from there).
2. Levels: matte black on the upper and the rails (afstg44_levels.py --matte), colour median 0.10 on
   the polymer lower, then the stock and the gold sights (afpk_levels_extra.py).
3. Finish pass (afpk_finish_pass.py) from a fresh copy of the levelled sheets.
4. Round-counter digits (afpk_counter.py).
5. Converts every afpk sheet to .paa in source/AF_Weapons/afpk/data.
Then run build.bat.
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
RAW = os.path.join(TEX, "afpk_raw_last")
DATA = os.path.join(os.path.dirname(HERE), "source", "AF_Weapons", "afpk", "data")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
TOPAA = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"
SHEETS = ("body", "front", "lower", "parts", "counter", "gold", "stock")


def blender(*args, keep=("LEVELS", "AFPK", "WROTE afpk_count_20", "Error", "Traceback")):
    out = subprocess.run([BLENDER, "-b", *args], capture_output=True, text=True, errors="replace")
    for line in (out.stdout + out.stderr).splitlines():
        if any(k in line for k in keep):
            print("   ", line.strip())
    if out.returncode != 0:
        sys.exit("Blender failed: " + " ".join(args))


def main():
    print("1. raw bake ->", RAW)
    if os.path.isdir(RAW):
        shutil.rmtree(RAW)
    os.makedirs(RAW)
    for s in SHEETS:
        for f in glob.glob(os.path.join(TEX, "afpk_%s_*.png" % s)):
            shutil.copy2(f, RAW)
    print("2. levels")
    levels = os.path.join(HERE, "afstg44_levels.py")
    blender("--factory-startup", "--python", levels, "--", RAW, "--matte", "afpk_body", "afpk_front")
    blender("--factory-startup", "--python", levels, "--", RAW, "--median=0.10", "afpk_lower")
    blender("--factory-startup", "--python", os.path.join(HERE, "afpk_levels_extra.py"))
    print("3. finish pass")
    pre = os.path.join(TEX, "afpk_prefinish")
    if os.path.isdir(pre):
        shutil.rmtree(pre)
    blender(os.path.join(HERE, "afpk_dayz.blend"), "--python", os.path.join(HERE, "afpk_finish_pass.py"))
    print("4. counter digits")
    blender(os.path.join(HERE, "afpk_dayz.blend"), "--python", os.path.join(HERE, "afpk_counter.py"))
    print("5. .paa")
    n = 0
    for f in sorted(glob.glob(os.path.join(TEX, "afpk_*.png"))):
        name = os.path.splitext(os.path.basename(f))[0]
        r = subprocess.run([TOPAA, f, os.path.join(DATA, name + ".paa")], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("ImageToPAA failed on " + name)
        n += 1
    print("   %d sheets converted" % n)


main()
