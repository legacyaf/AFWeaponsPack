# Roadmap

Agreed on 2026-11-19. Each weapon borrows a vanilla weapon's animations, so the order follows how well the gun fits its base (see `docs/PIPELINE.md`).

| Phase | Weapon | Role | Built on | Notes |
|---|---|---|---|---|
| 1 | StG 44 | Assault rifle | AKM | Built for 0.12.0 with its own ZF4-style scope (`docs/STG44.md`); waiting for the in-game test. |
| 1 | Kar98k-style carbine | Short bolt-action | CZ 527 or Mosin | Reuses most of the M41 work. |
| 2 | Thompson M1A1 | .45 submachine gun | UMP-45 | Counterpart to the MP40. |
| 2 | M1 Garand | Semi-automatic rifle | SKS | Internal magazine, loaded from the top. |
| 3 | Trench shotgun (pump) | Close quarters | MP-133 | First shotgun. |
| 3 | Colt-style revolver | Sidearm | Magnum | Revolver animations fit exactly. |
| 4 | Scoped marksman rifle (modern AF design) | Long range | SVD or M14 | A modern partner for the AF-7. |
| 4 | AF carbine (short AF-7) | Compact rifle | M4A1 | Shares the AF-7's parts and textures. |

## Rules for new weapons

- One weapon per release, with standard and gold finishes, its own magazine where needed, and loot entries.
- **No AF logo** on the StG 44 and later weapons. The AF-7, M41, MP40 and P08 keep theirs.
- **"legacy was here"** in small lettering that looks scratched into the gun, on the StG 44 and later weapons.
- The server licence check stays on every weapon.
- After every two weapons, a polish release.

## Server settings and gunplay

The goal set on 2026-11-19: a pack good enough to stand next to A-6, with settings server owners can tune in depth. Everything here applies to this pack's weapons only, never to vanilla or other mods' weapons. Feature ideas come from A-6's public feature lists (gunplay, weapons, optics); the implementation is our own.

| Step | What | State |
|---|---|---|
| 1 | `AF_WeaponsPack.json`: enable/disable per weapon, recoil, sway, damage, jam chance, extra wear, bullet immunity (`docs/SETTINGS.md`) | written; recoil, sway, enable/disable and the file handling tested offline |
| 2 | Weapon repair kit (time, health restored, uses, suppressors) and aim / zoom / zero sounds | written; kit logic tested offline, sounds not heard in game yet |
| 3 | Aim-down-sight speed per weapon and attachment; hip fire from the barrel's direction | needs investigation: both are partly engine-side |
| 4 | Item stats screen (weapon, magazine, attachment) | not started; the largest piece |
| 5 | Attachments of our own that change recoil, sway and aim speed; toggle keys for bipods, lights and lasers | later |
| 6 | Ammunition variants | later; new ammo needs loot and trader entries on every server |
| 7 | Optics: reticle colour and pattern switching, stacked optics | later; the StG 44's scope is the first optic |

## Polish backlog

- Iron-sight views of the MP40 and M41 (the rear of the gun fills too much of the view).
- Gold finish reads as flat yellow at a distance.
- The MP40 borrows the MP5-K sounds.
- P08: firing, the open action and the first-person view have not been checked.

## Left out on purpose

- A belt-fed machine gun: DayZ has no vanilla one to borrow animations from.

## Size

The pack is about 150 MB with four weapons. Small guns (pistols, magazines) use one texture set or 2048 px to keep later releases from growing at the same rate.
