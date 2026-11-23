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
- **The handguard is deeper than the real one.** As on the real rifle it is a stamped shell round the barrel only, with the gas cylinder bare above it (corrected 2026-11-23; the first version sleeved the gas cylinder). Its underside is at z 0.076, lower than the real one, because that is where the AKM puts the left hand.
- **The magazine may clip during a reload.** The AKM animation draws its magazine out along a 20.7 degree lean; ours is longer and curves forward. To be checked in game.

## Realism and LOD pass (2026-11-22)

At the owner's request ("premium high end", "more realistic"). **In game, 2026-11-23 11:15** (test mission AFStG44Test, Chernarus, midday sun; second bake with edge padding). The handguard now reads as part of the rifle and the stock as slimmer; steel is dark gunmetal and the wood brown rather than orange. The wear is subtle at normal viewing distance: worn rims and edges show close up, the rifle reads as well kept rather than hard used. No seams visible at the distances photographed. Unchanged and still open: the scope view shows a black square round the reticle, and in the iron-sight view the back of the receiver fills the lower part of the picture. The first raised-rifle pictures were taken before the world had loaded (menu overlay) and are not usable.

**Sights, 2026-11-23 13:14** (second run that day, one Factory Blender job alongside; the world and the rifle loaded normally).
- Scope: the reticle and the lens panels are now discs that fill the bore. The black square is gone; the view is a clean round picture with the crosshair.
- Iron sights: the rear notch's shoulders were 2 mm above the front post's top and the V was 2.8 mm wide, so the post hid behind it. Shoulders are now on the sight line (z 0.150, the post's top) and the V is 4.4 mm wide; measured in the exported LOD 1 and in the model. LOD 1 keeps its baked UVs (the exporter's `LOD1_EDIT` hook moves the notch's vertices), so no bake was spent.
- The in-game picture still showed the front sight about 20 px left of the notch, in both runs, with the post behind the notch's left shoulder. The game's own eye point is exactly on the sight line (logged), so this is the test, not the rifle: the test placed its still camera on the eye point once, 1.5 s before the picture, while the held rifle swayed. The test mission now keeps the camera on the eye point every frame until the picture. Run at 13:22: the front post shows centred in the V, its tip level with the shoulders, inside the hood (`docs/img/stg_sights_ingame.jpg`).
- The scope stays a removable attachment (slot `weaponOpticsAFStG`); the iron sights stay on the rifle under it (owner, 2026-11-23).

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

## Finish test and steel calibration (2026-11-22)

Run with the owner's go-ahead.

- **Wood:** reads as oiled beech on the ground and in the hands. Kept as it is.
- **Steel:** right in shade, but in full sun it read as flat light grey next to the vanilla AKM. Measured against the AKM's own maps (medians, Blender readout of the PNGs): our steel colour was about 1.8x the AKM's and less glossy, and the body material had a brighter ambient.
- **Change:** all steel, wear, grime and soot colours in `afstg44_detailed.py` darkened; steel roughness 0.40, metallic 0.35. The body, magazine and ZF4 rvmats now use the AKM's lighting (ambient 0.7, specular 0.79/0.75/0.74, specularPower 70, fresnel 0.8/0.7). Wood rvmats unchanged.
- **Measured after the bake:** body colour 0.111, magazine 0.119, AKM 0.090; gloss body 0.56, magazine 0.53, AKM 0.61; spec 0.122 vs 0.118. LOD 1 is 15,657 triangles. Build, signature and the O2 checks of all three models pass.
- **In game (19:04 run, owner's and Factory's go-ahead, nothing else running):** in sunlight the steel now reads as dark gunmetal, on the ground and in the hands, in line with the vanilla AKM; the wood is unchanged. The close-up and sight pictures from that run are unusable: they were taken before the world had loaded (untextured world, main menu over the scene, the vanilla AKM equally white), so they say nothing about our textures. The scope and iron-sight views still need a clean look.

## Polish pass (2026-11-23)

Audit first, then one bake. An independent reviewer (a sub-agent, read-only) checked the work twice before the bake; its findings were tested against the model and the vanilla AKM's maps before use.

**Shape**
- Handguard: a stamped shell round the barrel, butted against the receiver, six cooling holes; gas cylinder bare above it. (Owner: "looks detached"; reviewer: it was on the wrong tube, which made the rifle read as an AK.)
- Gas block moved back to y 0.336-0.366; the gas plug runs out into the ball-ended stacking rod above the barrel.
- Stock: half width 16-18.5 mm (was 17-21), rounder section (power 2.15), straight belly from the wrist to a toe at z 0.018. (Owner: "way too wide and blocky".)
- The lower rivet row and the stuck-on beads of the magazine housing are gone; the magazine's cross ribs are replaced by two lengthwise flutes.
- LOD 1 is 14,446 triangles (was 15,657).

**Pressed detail** (`_Pen`, `detail_sheet`, `magazine_sheet`, `_sheet`)
- The detail sheet steel carries is drawn once as a height map of each side (10 px/mm) and projected onto the side faces: receiver flute and swage crease, spot welds, a bead round the trigger-housing panel, selector letters E and D, sunk panels and a bead on the magazine housing, a rib on the dust cover, the handguard holes, the magazine flutes. The bake turns it into the normal map.
- Dirt and rub masks are derived from the same heights (creases collect dirt, raised rims lose finish), so colour, gloss and normal agree.

**Finish**
- Wear shows as shine, not as a white outline: bare steel is colour 0.22 with full metal, and the exporter's new `SPEC_WORN` lifts its specular to 0.54 (the vanilla AKM's specular reaches 0.71 at its 90th percentile; ours was a flat 0.12).
- Edge wear only where the rifle is exposed: a broad noise plus the muzzle, the butt plate and the mouth of the magazine housing.
- Gloss breakup in the gloss only (oily patches, wipe marks); dry dust in corners; stamps are recesses with dust in them instead of pale paint.
- Wood about a fifth less saturated (it read orange in game).
- Exporter: `AO_FLOOR` 0.30 (the bolt carrier seen through the port was at 0.13), bolt carrier texel priority 0.5, and normal-map texels pointing into the surface (faces buried in another part: 74,877 on the body sheet) are flattened.

**Measured after the bake** (medians of the PNGs): body colour 0.118 (AKM 0.102 by the same readout), gloss 0.565, specular 0.122 with worn steel at 0.541; no normal-map texel with blue below 0.5 on any of the three models. Build, signature and the O2 checks of all three models pass.

**Second bake, same day.** The reviewer's check of the first bake found it read factory-new: bare-steel specular on 1.6 % of the body sheet (all of it the bolt carrier), one steel tone, wood still orange, and the magazine a slab from below. The first bake's handguard holes had also come out mid grey (0.067) because the handling layers were painted over them. Changed, tested in a 1024 bake, measured, then baked in full:
- Edge wear in two bands broken by a flake noise: a wide band of thinned finish, and inside it a core of bare steel that is weakest where the rifle is sheltered and never quite absent.
- Rims of the pressed detail rub through sooner; stronger mottling and dark oily patches in the steel colour; wider gloss breakup.
- Wood 15 % less saturated and 10 % darker, with grain ridges in the normal and the gloss.
- Holes painted last (median colour 0.024 in the bake; `blender/afstg44_fix_holes.py` was a one-off for the first bake and is not needed).
- Magazine floor plate has its retaining plate and catch button (magazine LOD 1: 1,143 triangles, was 933).

| Body sheet, used texels | first bake | second bake |
|---|---|---|
| colour p5 / p50 / p95 | 0.094 / 0.118 / 0.180 | 0.097 / 0.124 / 0.278 |
| gloss p5 / p50 / p95 | 0.427 / 0.553 / 0.667 | 0.416 / 0.565 / 0.722 |
| specular above 0.3 (bare steel) | 1.6 % | 2.5 % |
| specular 0.15 to 0.3 (thinned finish) | 1.2 % | 7.5 % |
| wood mean rgb | 0.263 0.193 0.130 | 0.254 0.179 0.134 |

No normal-map texel with blue below 0.5 on any sheet; LOD 1 unchanged at 14,446 triangles; build, signature and the three O2 checks pass.

**Edge padding (reviewer's fourth check).** The texels no face uses were black in the colour maps (12 % of the body sheet, 27 % of the wood, 23 % of the magazine, 19 % of the scope), with only an 8-pixel bake margin round each island; smaller mip levels would average that black into the island edges and show dark seams at a distance. `blender/af_pad.py` fills unused texels from the islands round them (used texels are unchanged, asserted). The exporter does it from now on for this rifle (`EDGE_PAD`); `blender/afstg44_pad_maps.py` applied it once to this bake. After padding, "used texels" can no longer be read from the colour map, so the statistics above cannot be re-measured from the committed PNGs.

The same check suggested three further map changes, not made, to be judged on the in-game view: specular following gloss on the flats (79.5 % of body texels share one specular value), a higher specular for the wood, and darker dust in corners under direct sun.

**Distance models and collision (2026-11-23, no bake).**
- Stock crease, LODs 6 to 9: the coarse stock is left with a few broad facets, and the edge between the side and the belly was marked hard, so the belly showed as a darker wedge. The exporter can now shade chosen texture sets smooth in the distance LODs (`SOFT_SETS`, the beech set here; edges sharper than 80 degrees, the stock's end faces, stay hard), and leaves those vertices out of the area weighting. The wedge is gone from LODs 6 to 8; on LOD 9 (about 360 triangles) the stock is a plain block with a faint lighter belly.
- Ejection port, LODs 6 to 9: the farthest rebuilds have no port cut, and their receiver side read the empty texture area where LOD 1 has its port, which was black. The edge padding of the same day filled it with the steel round it; the black rectangle is gone (re-rendered).
- Magazine collision box: now the whole magazine as measured, z -0.1866 to 0.0410 (was -0.1850 to 0.0360: 1.2 mm short of the floor-plate catch and 4.6 mm short of the top round).
- Left: on LOD 9 the trigger guard decimates to a thin sheet that catches the light as a small pale sliver.
- In game (14:25, run limit raised to 480 s so the distance shots are reached; new zoomed 25 m shot): the far models show a smooth stock and no dark port (`docs/img/stg_far_ingame.png`).

Not yet seen in game.

## What still has to be checked in game

Hand fit on the grip and handguard, magazine fit and the reload, bolt travel through the port, the iron-sight picture, the scope view (eye point, reticle, lens), suppressor positions, both finishes under game lighting, and that the vanilla AKM magazine and PU scope are refused. The test mission covers all of these. It waits until the AF Content Factory session can spare the game (owner's rule, 2026-11-21).
