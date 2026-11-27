#!/usr/bin/env bash
# Renders the "card" studio shot of every weapon (blender/af_studio.py) for workshop/make_cards.ps1.
#   bash workshop/render_cards.sh <output folder> [samples]
# About two minutes a weapon at 160 samples. Do not run the game while it renders.
set -e
OUT="$(cygpath -w "$1")"; N="${2:-160}"
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
cd "$(dirname "$0")/../blender"
export AF_STUDIO_FLIP=1          # the left side, muzzle to the left
r() { "$B" -b "$@" 2>&1 | grep "STUDIO rendered\|Error\|Traceback\|STUDIO missing" || true; }
r af7_vanguard_dayz.blend --python af_studio.py -- "$OUT" af7 '{"AF7_LOD_1": ["af7_body","af7_furn"]}' "$N" card
r afm41_pathfinder_dayz.blend --python af_studio.py -- "$OUT" m41 '{"M41_LOD_1": ["afm41_body","afm41_wood"]}' "$N" card
r afmp40_dayz.blend --python af_studio.py -- "$OUT" mp40 '{"MP40_LOD_1": ["afmp40_body","afmp40_furn"], "MP40M_LOD_1": ["afmp40_mag"]}' "$N" card
r afp08_dayz.blend --python af_studio.py -- "$OUT" p08 '{"P08_LOD_1": ["afp08_body"], "P08M_LOD_1": ["afp08_mag"]}' "$N" card
r afstg44_dayz.blend --python af_studio.py -- "$OUT" stg44 '{"STG_LOD_1": ["afstg44_body","afstg44_wood"], "STGM_LOD_1": ["afstg44_mag"]}' "$N" card
r afm107_dayz.blend --python afm107_studio_setup.py --python af_studio.py -- "$OUT" m107 '{"M107_LOD_1": ["afm107_body","afm107_lower","afm107_front","afm107_parts"], "M107M_LOD_1": ["afm107_mag"], "M107S_LOD_1": ["afm107_scope"]}' "$N" card
r afpk_dayz.blend --python afpk_studio_setup.py --python af_studio.py -- "$OUT" pk '{"PK_LOD_1": ["afpk_body","afpk_front","afpk_lower","afpk_parts","afpk_counter+afpk_count_20","afpk_gold"], "PKS_LOD_1": ["afpk_stock"]}' "$N" card
echo ALL DONE
