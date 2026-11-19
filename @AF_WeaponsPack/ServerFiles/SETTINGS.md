# Server settings

Server owners tune the pack's weapons in one file. Nothing here touches vanilla weapons or other mods' weapons: the settings apply only to the weapons of this pack and their finishes.

## The file

    <server profiles folder>\AF_WeaponsPack.json

- The server writes it with default values the first time it starts with the mod.
- It is rewritten on every start, so settings and weapons added by a newer version of the mod appear in it. Your values are kept.
- A value outside its range is pulled back into range and written back (multipliers: 0 to 10).
- If the file has a mistake in it (a missing comma or bracket), the server says so in its script log, uses the defaults and leaves your file alone so you can fix it.
- The server sends the settings to every player when they join. Change the file, restart the server, and players pick the new values up on their next join.

## Settings for the whole pack

| Setting | Default | What it does |
|---|---|---|
| `EnableSettings` | 1 | 0 switches everything in this file off; the weapons behave as built. |
| `GlobalRecoilMultiplier` | 1.0 | Recoil of every weapon in the pack. 0.5 is half, 2.0 is double. |
| `GlobalSwayMultiplier` | 1.0 | How far and how fast the weapons wander when aimed. |
| `GlobalDamageMultiplier` | 1.0 | Damage to players, infected and animals. |
| `GlobalJamChanceMultiplier` | 1.0 | Chance of a jam. 0 means the pack's weapons never jam. |
| `WeaponsImmuneToBulletDamage` | 0 | 1: a bullet that hits one of the pack's weapons does not damage it. |

## Weapon repair kit

The item `AF_WeaponRepairKit` looks like the game's weapon cleaning kit and is used the same way: combine it with the weapon (kit in the hands and the weapon in front of you, or drag one onto the other in the inventory). It only works on weapons of this pack. It needs a loot or trader entry to reach players; `ServerFiles` has one.

| Setting | Default | What it does |
|---|---|---|
| `RepairKitEnabled` | 1 | 0: the kit does nothing. |
| `RepairKitSeconds` | 8.0 | How long one repair takes (1 to 120). |
| `RepairKitHealthAdd` | 1.0 | Share of full health one use restores. 1.0 is back to pristine, 0.25 a quarter. |
| `RepairKitUses` | 4 | Uses in one kit (1 to 100). |
| `RepairKitRepairsRuined` | 1 | 0: a ruined weapon stays ruined. |
| `RepairKitWorksOnSuppressors` | 0 | 1: the kit also repairs suppressors. Suppressors are vanilla items, so this is the one setting that reaches outside the pack. |

## Aim, zoom and zero sounds

When a player aims a weapon of this pack, changes its zeroing or changes the zoom of its scope, they and the players near them hear a short sound. The sounds are the game's own; any sound set name the game knows can be put in instead.

| Setting | Default | What it does |
|---|---|---|
| `AimSoundsEnabled` | 1 | 0: no sounds. |
| `AimSoundRadius` | 10.0 | Metres. Players further away are not sent the sound (0 to 100). |
| `AimSoundSetRifle` | `Weapon_Movement_Rifle_walkRasErc_SoundSet` | Played when a rifle or submachine gun is aimed. |
| `AimSoundSetPistol` | `Weapon_Movement_Pistol_walkRasErc_SoundSet` | Played when a pistol is aimed. |
| `ZeroSoundSet` | `combinationlock_changedial_SoundSet` | Played when the zeroing changes. |
| `ZoomSoundSet` | `Fire_Mode_Switch_Simple_Click_SoundSet` | Played when a scope's zoom changes. |

An empty name (`""`) switches that one sound off.

## Settings for one weapon

One entry per weapon under `Weapons`. `ClassName` is the standard finish; the gold finish follows the same entry. A weapon's own multiplier is multiplied with the global one, and with whatever its attachments already do.

| Setting | Default | What it does |
|---|---|---|
| `Enabled` | 1 | 0 removes the weapon wherever it appears (loot, admin spawns, traders). |
| `RecoilMultiplier` | 1.0 | |
| `SwayMultiplier` | 1.0 | |
| `DamageMultiplier` | 1.0 | |
| `JamChanceMultiplier` | 1.0 | |
| `ExtraWearPerShot` | 0.0 | Health the weapon loses with every shot, on top of the game's own barrel wear. A weapon has 200 to 250 health. |

Class names: `AF7_Vanguard`, `AFM41_Pathfinder`, `AF_MP40`, `AF_P08`.

## Example

Half recoil for the whole pack, a harder-hitting M41, no MP40 on the server:

    {
        "ConfigVersion": 1,
        "EnableSettings": 1,
        "GlobalRecoilMultiplier": 0.5,
        "GlobalSwayMultiplier": 1.0,
        "GlobalDamageMultiplier": 1.0,
        "GlobalJamChanceMultiplier": 1.0,
        "WeaponsImmuneToBulletDamage": 0,
        "Weapons": [
            { "ClassName": "AF7_Vanguard", "Enabled": 1, "RecoilMultiplier": 1.0, "SwayMultiplier": 1.0, "DamageMultiplier": 1.0, "JamChanceMultiplier": 1.0, "ExtraWearPerShot": 0.0 },
            { "ClassName": "AFM41_Pathfinder", "Enabled": 1, "RecoilMultiplier": 1.0, "SwayMultiplier": 1.0, "DamageMultiplier": 1.25, "JamChanceMultiplier": 1.0, "ExtraWearPerShot": 0.0 },
            { "ClassName": "AF_MP40", "Enabled": 0, "RecoilMultiplier": 1.0, "SwayMultiplier": 1.0, "DamageMultiplier": 1.0, "JamChanceMultiplier": 1.0, "ExtraWearPerShot": 0.0 },
            { "ClassName": "AF_P08", "Enabled": 1, "RecoilMultiplier": 1.0, "SwayMultiplier": 1.0, "DamageMultiplier": 1.0, "JamChanceMultiplier": 1.0, "ExtraWearPerShot": 0.0 }
        ]
    }

## What cannot be a setting

Fire rate, magazine size, ammunition and attachment slots are fixed when the mod is built (`config.cpp`). They cannot be changed from a file on the server.

## How it works (for whoever maintains the mod)

Everything is in `source/AF_Weapons/scripts/4_World/AF_Weapons/AFConfig.c`.

| Setting | Where it is applied |
|---|---|
| Recoil, sway | `PropertyModifiers.UpdateModifiers`: the object the game already uses to combine a weapon's `recoilModifier` and `swayModifier` with its attachments'. Worked out on the player's PC and on the server, which is why the settings are sent to players. |
| Damage | `EEOnDamageCalculated` on players, infected and animals: the hit is cancelled and applied again with `ProcessDirectDamage` at the scaled strength, so bleeding and hit reactions still happen. |
| Jam chance | `Weapon_Base.JamCheck`, on the final chance (the game adds the magazine's share in several weapon base classes). |
| Extra wear | `Weapon_Base.EEFired`, server only. |
| Bullet immunity | `Weapon_Base.EEOnDamageCalculated`. |
| Enabled | `Weapon_Base.EEInit`, server only, three seconds after the weapon appears. |
| Repair kit | `AFRepairKit.c`: a recipe (`AFRepairWeapon`) registered with the game's recipe manager; its length is read from the settings each time. |
| Sounds | `PlayerBase.CommandHandler` on the PC of the player holding the weapon notices the change, plays the sound and tells the server (`RPC_SOUND`); the server passes it to players within the radius (`RPC_SOUND_PLAY`). The server only accepts it from the player themself, at most ten a second, and only while they hold a weapon of the pack. |
| Sync | Two script RPCs on `PlayerBase` (`AFConfig.RPC_REQUEST`, `AFConfig.RPC_SETTINGS`). The player asks when they load and whenever a weapon works out its modifiers before the settings have arrived. |

A new weapon must be added to `AFConfig.BASE_CLASSES`, or it gets no settings.

## Tested

`test\run_test.ps1 -Mission AFConfigTest.ChernarusPlus -TimeoutSeconds 150` (offline, in DayZDiag) prints the loaded settings and each weapon's resulting recoil and sway values to the script log, lines starting `[AFCfg]`.

Checked that way on 2026-11-19: the file is created with defaults; recoil and sway multipliers (global and per weapon) change the values the game uses; a value of 99 is pulled back to 10 and written back; a disabled weapon is removed; the M4A1 and UMP-45 are untouched.

Also checked that way: the repair kit refuses a vanilla M4A1, brings a ruined P08 back to pristine, and is used up after the configured four uses.

Not checked yet: damage, jam chance, extra wear and bullet immunity in play (they need shooting); the repair kit through the real crafting action (the test calls the recipe directly); the aim, zoom and zero sounds (they need a player aiming); and the sync to players on a real server (the offline test has no second PC).
