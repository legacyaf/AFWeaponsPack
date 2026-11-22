# AF StG 44

WW2-style assault rifle with its own curved magazine and its own scope. Fifth weapon of the pack, and the first built under the rules for new weapons: no AF logo, and "legacy was here" scratched into the receiver.

| | |
|---|---|
| Classes | `AF_StG44` (beech furniture), `AF_StG44_Gold` (gold floral furniture on black), `Mag_AFStG44_30Rnd` (magazine), `AF_ZF4Optic` (scope) |
| Pack version | 0.12.0 (built, signed and checked in Object Builder on 2026-11-21; **not yet tested in game**, not uploaded) |
| Size | rifle LOD 1: 15,657 triangles (finish pass, 2026-11-22); LODs 2-9: 10,333 / 6,889 / 4,018 / 2,950 / 1,675 / 1,189 / 706 / 373; two 4096 px texture sets (`afstg44_body` steel, `afstg44_wood` stock and grip panels). Magazine LOD 1: 1,073 triangles, 2048 px (`afstg44_mag`). Scope LOD 1: 3,590 triangles, 1024 px (`afzf4`). Together about 47 MB of textures |
| Inherits | vanilla `AKM` (animations, sounds, recoil, handling); the magazine inherits `Mag_AKM_30Rnd`; the scope inherits `PUScopeOptic` |
| Different from the AKM | its own magazine and scope, about 570 rounds a minute instead of 610, recoil x0.9, 4.6 kg, no stock, handguard or bayonet slots |
| Attachments | its own scope (slot `weaponOpticsAFStG`, new in `CfgSlots`), AK suppressor, improvised suppressor, ghillie wrap |
| Models | `source/AF_Weapons/afstg44/afstg44.p3d`, `afstg44_mag.p3d`, `afzf4.p3d` |
| Blender | `blender/afstg44_detailed.py` (rifle, magazine and scope), `afstg44_dayz_export.py`, `afstg44_run.py` |
| Test mission | `test\AFStG44Test.ChernarusPlus` |

## Look

Stamped receiver with a rounded top and pressed side ribs, ejection port with the bolt carrier showing, cocking handle in a slot on the right, long magazine housing, trigger housing running back to the stock, pistol grip with wooden panels, beech butt stock with a steel butt plate. In front: a ventilated steel sleeve over the gas cylinder, the gas cylinder lying on the barrel up to the gas block, front sight with its hood on a tall base, muzzle nut. Tangent rear sight on the receiver top and a scope rail on its right side. "AF STG 44" and a serial number are stamped on the left; "legacy was here" is scratched on the right, behind the ejection port.

## Frame and numbers taken from the vanilla AKM

Read from `dz\weapons\firearms\AKM\akm.p3d` (see the header of `blender/afstg44_detailed.py` for the full list). The AKM's centre line is 10.2 mm left of its origin; the rifle is built on x = 0 and shifted by the export (`ex.ORIGIN_EMPTY`).

| Vanilla feature | Working-frame value |
|---|---|
| Bore line | z = 0.0976 |
| Muzzle (AKM / StG) | y = 0.433 / y = 0.470 (so `WeaponLength` 0.937) |
| Eye point (iron sights) | y = -0.230, z = 0.150 |
| Trigger pivot | y = -0.072, z = 0.0672 |
| Pistol grip | top y -0.144..-0.084 at z 0.060, bottom y -0.155..-0.117 at z -0.038 |
| Magazine proxy | y = 0.035, z = 0.030 (the AKM's leans 20.7 degrees; ours is upright, the magazine carries its own curve) |
| Left hand | under the handguard, y 0.10..0.30, underside z = 0.075 |

## Bones

The AKM's bones have no parents: `magazine`, `trigger`, `bolt`, `firemode`, `mag_release`, `bullet`.

| Bone | Part |
|---|---|
| `bolt` | bolt carrier and cocking handle |
| `trigger` | trigger |
| `magazine` | the magazine proxy |
| `firemode`, `mag_release`, `bullet` | nothing: the selector and magazine catch do not move |

## Known compromises

All of these come from borrowing the AKM's animations.

- **Cocking handle on the right.** The real one is on the left; the AKM animation puts the hand on the right.
- **7.62x39, not 7.92x33.** It fires the AKM's ammunition from its own magazine, so no new cartridge is needed in loot.
- **The handguard sleeve comes down round the barrel.** On the real rifle it covers only the gas cylinder; here it reaches z 0.076 because that is where the AKM puts the left hand.
- **The magazine may clip during a reload.** The AKM animation draws its magazine out along a 20.7 degree lean; ours is longer and curves forward. To be checked in game.

## Realism and LOD pass (2026-11-22)

At the owner's request ("premium high end", "more realistic"). Not yet seen in game.

- **Receiver:** one pressing with the side swage line and a rolled lower edge, instead of stuck-on strips; domed rivets; rear end cap and stock collar with a push pin.
- **Grip:** a rounded grip on the AKM's grip line (so the hand still fits): steel front and back straps, wooden panels proud of the sides, one screw. Grooves were tried and left out (not sure enough of the real pattern).
- **Controls:** cross-bolt fire selector above the grip, besides the safety lever.
- **Magazine housing:** flared mouth, front stiffening rib, pressed side beads.
- **Front end:** figure-of-eight gas block, gas cylinder nut with spanner notches, round-ended vent slots.
- **Rear sight:** release buttons on the range slider, graduations on the leaf.
- **Stock:** pear-shaped section, slimmer wrist, no gap at the receiver; butt plate trap door with hinge and two screws; rear sling loop on a screwed base plate.
- **LODs** (`docs/img/stg_lods.jpg`, LOD 1-9 with the baked textures): thin overlays are built only at the finer detail levels. Two fixes in the shared exporter, which every weapon gets at its next export: faces of a reduced rebuild take their texture only from the same part of LOD 1 (attribute `af7_part`; before, a big face could take the bolt's texture through the ejection port), and a loose piece is never decimated below 12 triangles (`LOD_PIECE_MIN`; 6 folded a plain box).

## Finish pass (2026-11-22)

At the owner's request ("as if you were a professional DayZ texture and 3D model artist"). Not yet seen in game.

- **Steel** (`_phosphate` in `afstg44_detailed.py`): matte phosphate (roughness 0.60, metal 0.50) with cloudy mottling; grime and rust specks in the corners (ambient occlusion); the finish rubbed thin on edges and through to bright steel only on the sharpest, broken into chips (bevel mask); polish and fine scratches only where hands rub (grip, handguard, front of the magazine housing, cocking handle); a few faint long scratches; soot at the muzzle. The old blanket scratch layer (white flecks on every face) is gone.
- **Wood** (`_stock_wood`): oiled red-brown beech; darker and smoother where cheek and hands rest; dents with dirt in them; rubbed lighter edges; grime in the corners. None of it on the gold skin.
- **Front sight:** a longer, thicker sheet-steel hood on a broader, flared base.
- **Preview caveat:** Blender's preview turns the matte half-metal steel milky grey under its grey sky. The baked colour map itself is dark (mean 0.21 in the stored colour, against 0.17 for the previous bake), and the in-game specular is lower than before (0.15 against 0.24). How dark it reads has to be judged in game.

## First in-game test (2026-11-22)

Run with the AF Content Factory session's go-ahead (`test\AFStG44Test.ChernarusPlus`).

- **Worked:** every class spawns; magazine, scope, AK suppressor and improvised suppressor attach; the vanilla AKM magazine and the PU scope are refused. In the hands both hands close on the grip and the handguard, the stock sits in the shoulder, the magazine seats in its housing, and the magazine swap ran (`CanSwap=true`). Firing reported `CanFire=true`.
- **Bug, fixed:** the ZF4 scope was drawn on every rifle, attached or not. The scope proxy had no `CfgNonAIVehicles` entry tying it to its slot; `Proxyafzf4` now does.
- **Bug, fixed:** the magazine showed the vanilla AKM magazine texture (stripes), because it inherited the AKM magazine's `hiddenSelectionsTextures`. It now sets its own.
- Magazines of rifles lying on the ground sink into the runway; the vanilla AKM next to them does the same.

Both fixes are built and signed but not yet seen in game.

## Second in-game test (2026-11-22)

Run with the owner's go-ahead.

- **Both fixes confirmed:** the scope appears only on rifles that have one attached, and the magazine shows its own dark steel.
- **Scope view:** taken from the ZF4's `eyescope` point. The crosshair is centred and the view through the lens is clear. A black square stuck out round the eyepiece: the flat lens and reticle panels are square and their corners poked through the tube. They are now smaller (corners inside the tube wall); rebuilt, not yet seen in game.
- **Iron sights:** taken from the `eye` point looking at the muzzle, which tilts the camera about 4 degrees down compared with the game's own aiming view. The front sight shows above the rounded receiver top, but the top of the receiver fills the lower half of the picture. Worth a look in real play before deciding whether to lower the receiver top.

## Third and fourth in-game tests (2026-11-22)

- Third: the smaller panels were exported without a bake, and the exporter read the old panels back as body faces, so the scope view showed the texture sheet. Fixed in `af7_vanguard_dayz_export.py` (`lod1_from_p3d` now skips `RAW_QUADS` faces); the ZF4 was re-exported from the earlier file.
- Fourth: crosshair and lens are back and centred. A smaller black square is still visible inside the eyepiece opening, now within the tube. Most likely the black corners of the vanilla PU reticle texture, which the game's own aiming view normally covers with its round optics mask; the test's still camera does not apply that mask, so this has to be judged by aiming in real play.

## What still has to be checked in game

Hand fit on the grip and handguard, magazine fit and the reload, bolt travel through the port, the iron-sight picture, the scope view (eye point, reticle, lens), suppressor positions, both finishes under game lighting, and that the vanilla AKM magazine and PU scope are refused. The test mission covers all of these. It waits until the AF Content Factory session can spare the game (owner's rule, 2026-11-21).
