# The PeaceKeeper (AF modern battle rifle, our SCAR): plan

Owner, 2026-11-26: "lets do our version of the scar using the new scar vanilla weapon as a reference".
The next weapon after 0.13.0, and the first built with the full professional workflow from day one.

## Base and reference

- **Base:** the vanilla SCAR-H (`DZ\weapons\firearms\scarh`, base game). The SCAR-L is in the Nasdara DLC, so
  basing on it would force every player to own that DLC.
- **Inherited from the base:** its animations, handling and sounds, the way the M107A1 inherits the SVD and the
  StG 44 the AKM.
- **The vanilla SCAR is a reference only.** We measure its frame in game with the public script API, as done
  for the SVD (docs/M107.md): memory points, hand positions, magazine and optic proxies, bones. Nothing is
  copied from its files (owner's Bohemia rule).
- **Proportions:** a reference board of real photos (orthographic side, top, front, plus close-ups), used for
  measuring only, never published or committed.
- **Name:** SCAR is FN's trademark, so the weapon gets our own name: **The PeaceKeeper** (owner's choice, below).

## Our own design

The weapon is in the SCAR family but recognisably ours:

- an AF-pattern handguard (slot layout and rail lengths);
- our muzzle brake;
- our own stock shape and cheek riser;
- our own markings: the roll mark names only this mod's rifle, with no maker's name or logo; "legacy was here"
  in small scratched lettering, per the roadmap rule;
- no AF logo (roadmap rule from the StG 44 on).

## Build, using everything learned so far

1. **Topology:** clean, hand-laid from the start (`af_topo`). No Boolean cuts. Openings by loop cuts, ladder and
   scanline caps, quad caps on round parts.
2. **Detail:** real geometry for:
   - fasteners;
   - the charging handle;
   - the ambidextrous safety;
   - the bolt release;
   - the folding-stock hinge;
   - the rail slots.
3. **Textures:** several 4096 sheets from the start, sized to at least 7 texels per mm. High-to-low bake from a
   saved high-detail master.
4. **Finish:** `af_finish` layers.
   - Colour medians matched to vanilla from the first bake: dark metal about 0.095 to 0.10, FDE about 0.32.
     The 0.13.0 audit showed that lighter values read grey or cream in DayZ's light.
   - Finish: matte black with the orange trim (owner's decisions below).
5. **In-game checks:**
   - fit in the hands;
   - sights;
   - the scope view;
   - noon, overcast, evening and morning, beside the vanilla SCAR-H.
6. **Deliverables:**
   - the game model with its LODs;
   - the master .blend;
   - the PBR texture set;
   - studio renders;
   - loot entries;
   - server settings;
   - change notes.

## The vanilla SCAR-H's frame (measured in game, 2026-11-26)

Read by the probe mission `test/AFScarProbe.ChernarusPlus` through the public script API (config, memory
points, attachment transforms, the player's hand bones). DayZ model space: -x forward, +y up, +z left/right.
Working frame of the Blender scripts: y = -x_dayz, z = y_dayz, x = z_dayz.

**Classes:**
- `SCARH_Base` (scope 0, from `Rifle_Base`), with `SCARH` and `SCARH_Black` (scope 2) under it.
- `SCARL_Base`, `SCARL` and `SCARL_Black` also exist.
- Magazines: `Mag_SCARH_20Rnd` and `Mag_SCARH_20Rnd_Black`.
- Model: `\DZ\weapons\firearms\SCARH\ScarH.p3d`. Hidden selections: `camo1`, `camo2`.
- Fire modes: `SemiAuto` (reloadTime 0.12) and `FullAuto` (0.098, about 610 rounds a minute). It has
  **no burst mode**, so ours adds one.
- Attachment slots include `weaponButtstockSCAR` (**the stock is a separate attachment**: the bare rifle ends
  at x 0.158) and `weaponWrap`, plus others; the probe printed only the start of the list. The front sight is
  an attachment too (`Scarh_Front_Sight`).

| Point | DayZ model space (m) | Working frame (y forward, z up) |
|---|---|---|
| `usti hlavne` (muzzle) | -0.5423, 0.0887, 0 | y 0.5423, z 0.0887 |
| `konec hlavne` (barrel end) | -0.0741, 0.0888, 0 | y 0.0741, z 0.0888 |
| `eye` (iron sights) | 0.1470, 0.1720, 0 | y -0.1470, z 0.1720 |
| `trigger_axis` | 0.0361, 0.0367, -0.0200 | y -0.0361, z 0.0367 |
| `bolt_axis` | -0.2415, 0.1175, 0 | y 0.2415, z 0.1175 |
| `nabojnicestart` / `nabojniceend` | -0.0037, 0.0968, 0.0225 / 0.0621, 0.1224, 0.0870 | |
| Magazine attachment origin | -0.0567, 0.0245, -0.0001; upright | y 0.0567, z 0.0245 |
| Front sight attachment origin | -0.3044, 0.1314, 0.0002 | y 0.3044, z 0.1314 |
| Right hand (index finger base) | 0.0816, 0.0231, 0.0298 | y -0.0816, z 0.0231 |
| Left hand | -0.1361, 0.0364, -0.0703 | y 0.1361, z 0.0364 |
| Collision box (no stock) | -0.562, -0.076, -0.017 .. 0.158, 0.143, 0.010 | |

**Attachment slots (full list):**
- `weaponButtstockSCAR`
- `weaponWrap`
- `weaponOptics`
- `suppressorImpro`
- `Scarh_FrontSight`
- `weaponFlashlight`

There is no muzzle slot apart from the improvised suppressor.

**Stocks:** `SCAR_StockBttstck`, `SCAR_PrecisionBttstck` and their `_Black` versions, all from `Inventory_Base`.
A fitted `SCAR_StockBttstck` has its origin at -/+: 0.2897, 0.0715, -0.0002 (working frame y -0.2897, z 0.0715).
It is turned: its model's up (+y) points along the rifle's +x (backwards), its +z along the rifle's +z, so its
model's +x points down. Our AF stock item is built in that frame, so it sits where vanilla stocks do.

`magazine_axis`, `firemode_axis`, `charging_axis` and the other names tried are not in this model.
The hands are the same at rest and raised (within 2 mm).

**What this means for the build:**
- The bore is at z 0.0887 and the iron-sight eye 83 mm above it. The left hand sits 217 mm ahead of the
  trigger, on the handguard.
- The magazine proxy point is fixed: the vanilla magazines must sit in our well exactly there.
- **The stock (owner, 2026-11-26: "Both"):**
  - Keep the `weaponButtstockSCAR` slot, so vanilla SCAR stocks fit.
  - Add our own AF PeaceKeeper stock as a separate item for that slot, matte black with the orange trim, with
    its own model and loot entry.
  - The rifle spawns with the AF stock fitted.

## Owner decisions (2026-11-26)

- **Name:** **The PeaceKeeper** (owner, 2026-11-26; replaces "SCAR-AF"). Display name "AF PeaceKeeper", class
  name `AF_PeaceKeeper`. It has no trademark issue.
- **Magazine:** takes the vanilla SCAR-H magazines (no magazine of our own).
- **Finish:**
  - matte black, with an **orange trim line running along the body** (the AF accent colour, as on the AF-7's
    logo panels);
  - the **iron sights gold, with a red tip** on the front post.
  - **No gold version** (owner).
- The earlier "Our own design" points still stand (AF handguard, brake, stock, roll mark, no AF logo).

## Finish notes for the build

- Matte black body: colour median about 0.095, matte levels pass (as the M107A1's Cerakote).
- Orange trim: a painted stripe in the colour map, not geometry, along the receiver's sides at the line where
  the upper and lower meet.
  - It gets the same wear as the coat: chipped at the edges, dulled by grime.
  - It needs its own colour target: bright enough to read in sun, about orange (0.75, 0.30, 0.05) linear before
    the levels pass. The colour-only pass must not darken it, so it needs its own mask or its own texture set.
- Gold sights: a separate material and sheet (the sights and the front-post tip), polished gold with worn edges.
  The red tip is a small painted dot on the front post's top, as on fibre or painted post sights.

## What makes it special (owner: "i want this gun to be SPECIAL", 2026-11-26)

The owner chose two mechanics:

- **Live round counter.** A small orange display on the receiver shows the rounds left. It updates as you fire,
  reload and swap magazines, and glows faintly in the dark.
  - Built from digit textures 0 to 20 (and "--" with no magazine), swapped by script on a hidden selection,
    with an emissive material.
  - Needs an in-game check that it updates in third and first person and on other players' rifles
    (multiplayer: the count must come from the synced magazine state, not a local guess).
- **Three fire modes:** semi, 3-round burst, full auto, by config, as vanilla rifles do it. Each mode is tuned so
  it stays controllable: burst and auto with a little more recoil than semi.

Ideas offered and not chosen (for later, if wanted): less-lethal PeaceKeeper rounds, barrel heat.

The visual side is part of what makes it special too: matte black with the orange trim, gold sights with a red
tip, and the orange counter glowing beside the trim.
