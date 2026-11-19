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
| Sync | Two script RPCs on `PlayerBase` (`AFConfig.RPC_REQUEST`, `AFConfig.RPC_SETTINGS`). The player asks when they load and whenever a weapon works out its modifiers before the settings have arrived. |

A new weapon must be added to `AFConfig.BASE_CLASSES`, or it gets no settings.

## Tested

`test\run_test.ps1 -Mission AFConfigTest.ChernarusPlus -TimeoutSeconds 150` (offline, in DayZDiag) prints the loaded settings and each weapon's resulting recoil and sway values to the script log, lines starting `[AFCfg]`.

Checked that way on 2026-11-19: the file is created with defaults; recoil and sway multipliers (global and per weapon) change the values the game uses; a value of 99 is pulled back to 10 and written back; a disabled weapon is removed; the M4A1 and UMP-45 are untouched.

Not checked yet: damage, jam chance, extra wear and bullet immunity in play (they need shooting), and the sync to players on a real server (the offline test has no second PC).
