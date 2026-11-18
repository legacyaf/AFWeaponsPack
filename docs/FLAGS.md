# Allied Forces Flags

A separate mod from the weapons pack: `@AF_Flags`, addon `AF_Flags.pbo`. No scripts, no licence check, no model of its own.

| | |
|---|---|
| Version | 1.0.0, built and signed 2026-11-18. Not tested in game, not on the Workshop. |
| Item | `Flag_AF_Sierra`, "Allied Forces Flag (Sierra)" |
| Inherits | vanilla `Flag_Base` (model `dz\gear\camping\DZ_Flag.p3d`, slot `Material_FPole_Flag`) |
| Requires | `DZ_Data`, `DZ_Gear_Camping` (both part of the game) |
| Source | `source_flags/AF_Flags/` (`config.cpp`, `data/flag_af_sierra_co.paa`) |
| Artwork | `flags_art/` (the photo, `make_flag.py`, the 1024 x 512 PNG) |
| Build | `build_flags.bat` (signs with the same AlliedForces key as the weapons pack) |

## Texture layout

Read from the vanilla flag textures (`dz\gear\camping\data\flag_*_co.paa`): the whole texture is the flag, 2:1, upright, read left to right. Vanilla uses 512 x 256 and 1024 x 512.

## Adding another flag

1. Make a 1024 x 512 PNG. `flags_art/make_flag.py` crops a photo to 2:1, adds a soft dark edge and scales it:
   `blender -b --factory-startup --python flags_art/make_flag.py -- photo.jpg flags_art/flag_<name>_co.png`
   The crop window and the blanked number-plate area are set for the Sierra photo; change them for another picture.
2. Convert it with ImageToPAA into `source_flags/AF_Flags/data/`.
3. Copy the `Flag_AF_Sierra` class in `config.cpp`, change the class name, texts and texture, and add the class to `units[]`.
4. Add a `types.xml` entry in `@AF_Flags/ServerFiles/af_flags_types.xml`.
5. Run `build_flags.bat`.

## To check in game

- The picture is the right way up and not mirrored on the pole (the back of a flag is always mirrored; that is normal).
- Brightness in daylight: the flag material is the vanilla one, and photos can look brighter than the painted vanilla flags.
