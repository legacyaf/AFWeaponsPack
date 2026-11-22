# AF StG 44

WW2-style assault rifle with its own curved magazine and its own scope. Fifth weapon of the pack, and the first built under the rules for new weapons: no AF logo, and "legacy was here" scratched into the receiver.

| | |
|---|---|
| Classes | `AF_StG44` (beech furniture), `AF_StG44_Gold` (gold floral furniture on black), `Mag_AFStG44_30Rnd` (magazine), `AF_ZF4Optic` (scope) |
| Pack version | 0.12.0 (built, signed and checked in Object Builder on 2026-11-21; **not yet tested in game**, not uploaded) |
| Size | rifle LOD 1: 10,544 triangles; LODs 2-9: 6,959 / 4,638 / 3,056 / 2,055 / 1,177 / 709 / 460 / 217; two 4096 px texture sets (`afstg44_body` steel, `afstg44_wood` stock and grip panels). Magazine LOD 1: 1,073 triangles, 2048 px (`afstg44_mag`). Scope LOD 1: 3,590 triangles, 1024 px (`afzf4`). Together about 47 MB of textures |
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

## What still has to be checked in game

Hand fit on the grip and handguard, magazine fit and the reload, bolt travel through the port, the iron-sight picture, the scope view (eye point, reticle, lens), suppressor positions, both finishes under game lighting, and that the vanilla AKM magazine and PU scope are refused. The test mission covers all of these. It waits until the AF Content Factory session can spare the game (owner's rule, 2026-11-21).
