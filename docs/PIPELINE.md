# Adding a weapon to the AF Weapons Pack

The AF-7 Vanguard was built first; the AF M41 Pathfinder, the AF MP40 and the AF P08 were built by following the steps below. They are the repeatable part of the work. A new weapon is three small files in `blender/`, one folder in `source/AF_Weapons/`, and a class in `config.cpp`.

## What is shared and what is per weapon

| Shared (do not copy) | Per weapon |
|---|---|
| `blender/af7_vanguard_detailed.py`: material builder, box / profile / lathe / Boolean helpers, AF logo | `blender/<weapon>_detailed.py`: the shapes, materials and positions |
| `blender/af7_vanguard_dayz_export.py`: LODs, hidden-face removal, UVs, baking, the `.p3d` writer | `blender/<weapon>_dayz_export.py`: about 60 lines of tables |
| `build.bat`, signing key, licence script `AFLicense.c` | `blender/<weapon>_run.py`: one-command headless build with preview renders |
| | `source/AF_Weapons/<weapon>/`: `model.cfg`, `data/*.rvmat`, `data/*.paa` |
| | a class in `config.cpp`, a script class in `scripts/4_World/AF_Weapons/`, loot entries in `server/af_ce/` |

## Steps

### 1. Pick the vanilla weapon to inherit from

Every AF weapon borrows a vanilla weapon's animations, sounds and handling. That choice fixes the frame the model has to be built in.

### 2. Read the vanilla model before modelling anything

The game's own files are the specification. From `DayZ\Addons\weapons_firearms.pbo` (or `weapons_pistols.pbo`):

- **`config.bin`** (convert with `CfgConvert -txt`): base class, attachment slots, ammunition, `PPDOFProperties`, damage levels.
- **The `.p3d`**: skeleton bone names with their parents, proxy paths with position and orientation, memory point names and positions.
- **The `.rvmat` and `_smdi.paa`**: specular, power, fresnel, environment map, and typical specular / gloss levels.

Write the numbers into the header of `<weapon>_detailed.py`. For the M41 they are: bore height, muzzle and butt positions, bolt axis, bolt handle station, trigger pivot, iron-sight eye point, scope proxy.

### 3. Model in the vanilla weapon's frame

Use working axes +Y forward, +Z up, +X right, with the **vanilla origin as the working origin**. Then the export needs no shift (`ORIGIN_EMPTY = None`) and every vanilla number can be typed in directly:

    working x = vanilla z      working y = -vanilla x      working z = vanilla y

Rules that keep the animations working:

- A part that turns must sit on the vanilla axis. The M41's bolt is centred on the Mosin's bolt axis and its handle is at the Mosin's handle station.
- Iron sights must sit on the line through the vanilla `eye` point, parallel to the bore.
- Each moving part is its own Blender object in the `Moving` collection, named in the export's `SELECTIONS` table.

### 4. Fill in the export tables

Copy `afm41_pathfinder_dayz_export.py` and change: file names, `SELECTIONS` (object to vanilla bone), `HIDE_BARREL`, `PROXIES` (vanilla path and orientation), `MEMORY`, `GEOMETRY` boxes, mass, fire-geometry material, `_smdi` levels, UV priorities.

Proxy orientation: the vanilla model stores each proxy as a 3x3 matrix. Its second row is the `up` axis and its third row the `dir` axis used in the `PROXIES` table (checked against the M4, Mosin and UMP tables).

Two things the MP40 added:

- `BODY_BONE`: on some vanilla weapons the whole body is on a bone (the UMP's is `recoil`, with the bolt and charging handle as its children). Read the skeleton's parent names out of the vanilla `.p3d` and set `ex.BODY_BONE` if so.
- A weapon with its own magazine: the magazine is a second model with its own prefix, built in the same Blender file around its own origin, and exported by a second set of tables in the same export script (see `afmp40_dayz_export.py`). The weapon keeps the vanilla magazine proxy path, because the game ties the proxy name to the `magazine` slot and then shows whichever magazine is attached.

### 5. Build and look

    blender -b --factory-startup --python blender/<weapon>_run.py -- model    (shape check, about a minute)
    blender -b --factory-startup --python blender/<weapon>_run.py -- 4096     (full bake and .p3d)

Previews land in `docs/img/`. Convert the four PNGs in `blender/textures/` to `.paa` with ImageToPAA into `source/AF_Weapons/<weapon>/data/`.

### 6. Game files

- `model.cfg`: the vanilla skeleton, same bone order and parents; sections `camo`, `hide_barrel`.
- Three `.rvmat` files (normal, damage, destruct) with the vanilla weapon's lighting values.
- `config.cpp`: a class inheriting the vanilla one; add the vanilla addon to `requiredAddons`.
- Script class inheriting the vanilla script base class, with the licence check.
- Loot: `server/af_ce/` types and spawnable types.

### 7. Verify before it goes out

1. `CfgConvert -bin` on `config.cpp` (syntax and base classes).
2. Object Builder's script engine (`O2Script.exe`) loads the `.p3d`: LOD list, selections, mass, convex collision.
3. `build.bat`: binarize, pack, sign. Then `DSCheckSignatures`.
4. In game: `docs/TESTING.md`.

## What cannot be checked outside the game

- Whether each bone moves the part it was assigned to. Bone names come from the vanilla model; which part each name drives is inferred.
- Hand positions, magazine and attachment fit, sight picture, finish under DayZ lighting.

These are the first things to look at when a new weapon is tested.
