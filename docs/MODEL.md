# AF-7 Vanguard: model structure, LODs, dependencies and status

Version 0.7.2. This document covers how the model is built, what is in the `.p3d`, what the mod depends on, and where it stands against the quality standard the pack is being built to.

## 1. Files

| Path | What it is |
|---|---|
| `blender/af7_vanguard_detailed.py` | Builds the editable rifle from scratch (parts, materials, logo, gold skin switch). |
| `blender/af7_vanguard_detailed.blend` | The same model, ready to open and edit. |
| `blender/af7_vanguard_dayz_export.py` | Joins the parts, unwraps, bakes textures, builds LODs, writes the `.p3d` and an FBX. |
| `blender/af7_vanguard_dayz.blend` | The exported result: every LOD as a Blender object, with the baked textures applied. |
| `blender/textures/` | Baked PNGs (4096), the AF logo and the gold floral pattern. |
| `source/AF_Weapons/` | The addon source: `config.cpp`, scripts, `af7_vanguard/` (p3d, `model.cfg`, `data/` textures and materials). |
| `server/af_ce/` | Loot files for server owners (also copied to `@AF_WeaponsPack/ServerFiles`). |
| `licensing/supabase/` | The licence-check function and database tables used by the website. |
| `@AF_WeaponsPack/` | The built, signed mod that gets published. |
| `build.bat` | Packs, binarizes and signs the addon with DayZ Tools. |

To change the rifle: edit the detailed `.blend` or script, run the export script in Blender, convert the six PNGs to `.paa` with ImageToPAA, then run `build.bat`.

## 2. Model structure

The working file points along +Y with the trigger at the origin. The export moves it into the vanilla M4's frame: muzzle along -X, +Y up, origin at the magazine proxy. That is what makes the M4 animations line up.

**Parts (separate objects in the working file)**

- Receivers: upper (with a cut ejection port), lower (with an open magazine well, flared lip and recessed logo panels), raised side panels, brass deflector, dust cover, trigger guard, pins.
- Barrel group: stepped barrel, gas block and gas tube, hex muzzle brake with cut ports and an open bore.
- Furniture: hollow handguard with cut slots on the sides, bottom and diagonals; pistol grip; skeleton stock with cutout, cheek rest, latch, sling socket and rubber butt pad.
- Top: continuous Picatinny rail with real tooth profile, front and rear backup sights.
- Moving parts, kept separate: trigger, bolt, charging handle, magazine release, safety.

**Named selections in the `.p3d`**

| Selection | Contents | Animated |
|---|---|---|
| `camo` | Everything except the muzzle brake. Retextured by the skins. | no |
| `hide_barrel` | Muzzle brake. Hidden when a suppressor is fitted. | no |
| `trigger` | Trigger | yes, by the M4 animation |
| `bolt` | Bolt | yes |
| `charging` | Charging handle | yes |
| `magazine` | The magazine proxy | yes |

The safety and bolt catch are static. The M4's `firemode` and `boltrelease` bones rotate around the M4's own pivots, which these parts do not share.

`model.cfg` copies the skeleton built into the vanilla M4 model: the same twelve bone names in the same order. The M4 has no `boneRemap[]`, so matching its skeleton is what lets its animations drive this model.

## 3. LOD configuration

| LOD | Resolution | Triangles | Notes |
|---|---|---|---|
| 1 | 1 | 7,311 | Full detail, hidden faces removed |
| 2 | 2 | 5,483 | 75% |
| 3 | 3 | 3,654 | 50% |
| 4 | 4 | 2,631 | 36% |
| 5 | 5 | 1,926 | Distance LOD; parts under 1.2 cm dropped |
| 6 | 6 | 1,221 | Distance LOD; parts under 2.2 cm dropped |
| 7 | 7 | 820 | Distance LOD; parts under 3.5 cm dropped |
| View Pilot | 1100 | 7,311 | First person; same mesh as LOD 1 |
| Geometry | 1e13 | 48 | Four convex boxes, 3.2 kg, `autocenter = 0` |
| Memory | 1e15 | 7 points | See below |
| View Geometry | 6e15 | 48 | Copy of Geometry |
| Fire Geometry | 7e15 | 48 | Copy of Geometry, vanilla `metalplate` penetration material |

LODs 2 to 4 are made by collapse decimation of LOD 1 and checked by render. LODs 5 to 7 (added in 0.8.2) are for distance: small loose parts are dropped, then every remaining piece is decimated separately so that large flat parts keep their outline. The vanilla M4 and Mosin stop at resolution 4; the extra three mean a rifle on the ground or on a far player costs 800 to 1,900 triangles, not 2,600. They are checked by render only, not in game.

An export without a new bake (`nobake`) reads LOD 1 back from the existing `.p3d` and rebuilds only the other LODs. Rebuilding LOD 1 can shift the automatic unwrap, and the baked textures would no longer fit.

Switch distances are chosen by the engine from the resolution values; they are not set in the model.

**No Shadow LODs, on purpose.** Checked on 2026-11-18: the LOD lists of about 900 vanilla DayZ models were read from the game files (all firearms, pistols, shotguns, melee weapons, launchers, backpacks, tents, tools, wheeled vehicles and residential buildings). None has a ShadowVolume or ShadowBuffer LOD. DayZ draws shadows from the visual LODs, so a shadow LOD would add file size and risk for nothing. The same scan shows vanilla firearms with resolution LODs up to 5 and 6, and a few up to 10 and 15, which is in line with the distance LODs added in 0.8.2.

**Memory points:** `usti hlavne` (muzzle), `konec hlavne` (barrel direction), `eye` (iron sight camera), `nabojnicestart` and `nabojniceend` (case ejection), `boundingbox_min`, `boundingbox_max`.

**Proxies** (names and orientations copied from the vanilla M4):

| Proxy | Slot | Position |
|---|---|---|
| `magazine_stanag30` | magazine | Model origin |
| `optic_acog` | weaponOptics | On the rail, above the receiver |
| `suppressor_556` | weaponMuzzleM4 | 3.5 cm ahead of the muzzle |
| `weaponlight_universal` | weaponFlashlight | Right side of the handguard |

## 4. Textures and materials

One 4096 texture set per skin, baked in Blender from procedural materials:

| File | Content |
|---|---|
| `af7_body_co` / `af7_body_gold_co` | Colour, with the AF logo, edge wear and light contact shadow baked in |
| `af7_body_nohq` | Normal map: rounded edges and surface grain. DirectX style (green down). Shared by both skins. |
| `af7_body_smdi` / `af7_body_gold_smdi` | Green = specular, blue = gloss. Standard skin levels match the vanilla M4's map. |
| `af7_body_as` | Green = ambient shadow. Shared. |

Materials: `af7_body.rvmat` uses the vanilla M4's values. `af7_body_gold.rvmat` uses the lighting values and orange environment map from the old Allied Forces R700 chassis material. Each has `_damage` and `_destruct` versions using the vanilla overlay textures.

UVs come from an automatic unwrap (Smart UV Project). It has no stretching to speak of, but it wastes space on hidden faces and many small islands.

## 4a. Quality pass (0.9.0), both rifles

| Change | Before | After |
|---|---|---|
| Texture layout | automatic packing, about 45% of the texture used | exact-outline packing with free rotation; long parts unwrapped in lengths of 40 cm or less |
| Texture sets | one 4096 set per rifle | two: AF-7 `af7_body` (receiver, steel) 57% used and `af7_furn` (handguard, grip, stock, butt pad) 68% used; M41 `afm41_body` 52% and `afm41_wood` 66% |
| Round parts | 16 to 32 sides | 1.5 times as many sides on every round part with 16 or more (`ROUND_DETAIL`) |
| M41 detail | - | cut checkering on the wrist and fore-end; stamps drawn at nearly twice the resolution |
| Triangles, LOD 1 | AF-7 7,311, M41 8,178 | AF-7 8,162, M41 10,665 |
| Addon size | 55 MB | 101 MB |

Selections: `camo` is set 0, `camo1` is set 1; `hide_barrel` is always in set 0. `config.cpp` lists three hidden selections (`camo`, `hide_barrel`, `camo1`) and two materials per health level, and each set has its own six `.rvmat` files. A new weapon declares its extra sets with `ex.EXTRA_SETS` in its export script.

A full bake now takes about 20 minutes per rifle. Not tested in game: that both sets show, in both finishes and in the damaged states.
## 5. Dependencies

- **Game data:** `DZ_Data`, `DZ_Scripts`, `DZ_Weapons_Firearms`, `DZ_Weapons_Firearms_M4`, `DZ_Weapons_Firearms_FAL`.
- **Inherited from the vanilla M4A1:** animations, sounds, recoil, fire modes, particle effects.
- **Vanilla items used:** STANAG and CMAG magazines, the LAR 20-round magazine, 5.56x45 and .308 Winchester ammunition, the optic, suppressor and flashlight proxies.
- **Vanilla textures referenced:** damage and destruct overlays, penetration material, environment maps.
- **Licence check:** on a dedicated server the mod calls `https://kbifstvpqputwqtalyxz.supabase.co/functions/v1/af-license` once at start. The server needs outbound internet access, and its IP and game port must be in the `af_server_whitelist` table.
- **No other mods are required.**

## 6. Status against the quality standard

Legend: **Done** = built and checked. **Partly** = built, with a known gap. **Not done** = not built.

### 1. 3D modelling and geometry
| Requirement | Status | Notes |
|---|---|---|
| Accurate proportions | Partly | Sized to M4 dimensions (0.89 m, bore and rail heights match). It is an original design, so there is no real rifle to match. |
| Detailed individual components | Partly | All listed parts exist as real geometry. 0.6.0 added a bolt carrier with serrations, forward assist, charging handle latch and ridges, grip and butt pad ribs, handguard screws, bolt catch ridges, mag release fence, castle nut lugs and a sight knob. The safety is still a simple shape. |
| Modelled mechanical detail | Partly | Ports, slots, rail teeth, magazine well and bore are real geometry. Fine detail (screws, grip texture, markings) is in the normal map or absent. |
| Clean, optimized topology | Partly | Efficient, but triangulated from Boolean cuts, not hand-built quads. |
| Separated moving components | Done | |
| Attachment mounting points | Partly | Positions set from vanilla M4 data and two rounds of in-game feedback. The 60-round magazine still looks wrong. |
| Consistent quality across the collection | n/a | One weapon so far. |

### 2. Textures and materials
| Requirement | Status | Notes |
|---|---|---|
| High-resolution baked textures | Done | 4096. |
| UVs with efficient use of space | Partly | Automatic unwrap. 0.7.0 removes 938 never-visible triangles before unwrapping, so no texture space goes to hidden faces; islands are still not hand-arranged. |
| Detailed normal maps | Partly | Edge rounding, grain, scratches, turning marks on steel and moulded texture on polymer and rubber. Still procedural, not baked from a sculpted high-poly model. |
| Roughness and metallic definition | Done | Converted to DayZ's specular/gloss map. |
| Distinct materials | Done | Anodized metal, steel, polymer, coated handguard, rubber. |
| Wear and imperfections | Done | Edge wear, angled scratches, turning marks and roughness variation, all procedural. |
| Consistent look under DayZ lighting | Partly | Shine levels matched to the vanilla M4 after the first test; not yet rechecked in game. |
| Texture compression | Done | `.paa` via ImageToPAA, suffix-based compression. |

### 3. LODs and optimization
| Requirement | Status | Notes |
|---|---|---|
| Multiple resolution LODs | Done | Seven, plus first person. |
| Progressive reduction, silhouette kept | Done | Checked by render. |
| Transitions without popping | Not verified | Needs in-game check at distance. |
| Shadow LODs | n/a | DayZ does not use them; see section 3. |
| Geometry, Fire Geometry, View Geometry, Memory | Done | Loaded and checked in Object Builder's script engine. |
| Overall optimization | Partly | LODs 2-4 are generous, 5-7 are light. No before/after performance numbers. |

### 4. Animations
| Requirement | Status | Notes |
|---|---|---|
| First-person, reload, firing, chambering, third person | Partly | All inherited from the vanilla M4, and seen working in test videos. None are custom. |
| Charging handle, bolt | Done | Driven by the M4 animation. |
| Bolt release, safety | Not done | Static. |
| No clipping | Not verified | Hand position reported acceptable; not checked closely. |

### 5. Attachments
| Requirement | Status | Notes |
|---|---|---|
| Magazines | Partly | STANAG and LAR. 30-round fit corrected; 60-round still off; LAR fit untested. |
| Suppressor | Done | Confirmed fixed in game. |
| Optics | Partly | Mounts on the rail. Sight alignment through optics and irons not verified. |
| Flashlight | Partly | Shows on the handguard; placement not reviewed closely. |
| Stocks, handguards, grips | Not done | Built into the rifle by design; not swappable. |
| Proxies, selections, memory points | Done | Proxy transforms verified in the binarized model. |

### 6. Sound
| Requirement | Status | Notes |
|---|---|---|
| Firing, suppressed, handling sounds | Partly | All inherited from the vanilla M4. Nothing custom. .308 uses the M4's sound. |

### 7. Effects
| Requirement | Status | Notes |
|---|---|---|
| Muzzle flash, smoke, casing ejection | Partly | Inherited from the M4, placed by this model's memory points. Not reviewed in game. |
| Suppressor effects | Not verified | The muzzle memory point stayed at the bare muzzle when the suppressor proxy moved forward. |

### 8. Engine integration
| Requirement | Status | Notes |
|---|---|---|
| P3D structure, selections, memory points | Done | |
| Animation sources and configuration | Done | By matching the vanilla skeleton. |
| Slots, magazines, ammunition | Done | |
| First and third person positioning | Partly | Working; not tuned. |
| No missing dependencies or model errors | Partly | Builds and binarizes cleanly; scripts compile on a server. The server `.RPT` has not been reviewed for warnings. |

### 9. Quality assurance
| Requirement | Status | Notes |
|---|---|---|
| In-game tests | Partly | Done by the owner on the test server across four rounds: loading, licence, firing, reload, attachments, skins. Not done: LOD distances, shadows, collision, performance comparison, sight alignment, multiplayer with several players. |

### 10. Deliverables
| Requirement | Status | Notes |
|---|---|---|
| Blender project files | Done | Two `.blend` files and the scripts that generate them. |
| P3D source | Done | Unbinarized `.p3d` in `source/`. |
| Textures and materials | Done | PNG sources and `.paa`. |
| Configuration files | Done | |
| Animation files | n/a | None of our own. |
| Attachment proxies | n/a | Vanilla proxies only. |
| Compiled, tested mod | Partly | Built and signed. The latest build (0.5.1) has not been tested in game. |
| Documentation | Done | This file, `docs/GUIDE.md`, `README.md`, `ServerFiles/README.txt`. |

## 7. Bookmark: where the AF-7 stands at 0.7.2

Paused here to start a second weapon. Last build: 0.7.2, signed, in `@AF_WeaponsPack`. Last build tested in game: 0.7.1.

**Confirmed working in game**
- Loads, licence check passes, fires, reloads, third-person poses, carry on the back.
- Both finishes. Gold: black receiver, gold floral furniture, brake matches.
- Optic, flashlight and suppressor mount; suppressor clears the handguard.
- 30-round and coupled STANAG magazines sit in the well.
- Iron sights are sharp (aim blur off).

**Built but not yet tested in game (0.7.2)**
- Aiming position moved back to 7.5 cm so the rear sight is not clipped.
- Texture space weighted toward receiver, rail, sights and bolt.

**Open items**
1. LAR magazine overhangs the back of the magazine well by about 2 cm. Needs a decision: lengthen the well backward, shift both magazines forward, or leave it.
2. 60-round STANAG fit.
3. Safety and bolt catch do not animate.
4. Muzzle flash point stays at the bare muzzle when a suppressor is fitted.
5. (Closed) Shadow LODs: not used by DayZ, see section 3.
6. Sounds and animations are all the vanilla M4's.
7. Scratch strength and the standard finish have not been reviewed in a clean daylight SDR capture.

**Lessons for the next weapon**
- Read the vanilla base weapon first: its frame, skeleton bone names, proxies and memory points come from the game's own `.p3d`, and matching them is what makes its animations work.
- Magazine fit has to be measured in game; each magazine model has its own origin.
- Match specular and gloss levels to the base weapon's `_smdi` or the finish washes out.
- A skin's material applies to the whole retextured selection, so any shine on dark parts picks up the environment map's colour.
- HDR `.jxr` screenshots must be tone-mapped before judging brightness.
- Verify every build three ways before it goes out: Object Builder's script engine, a binarize build, and a signature check.