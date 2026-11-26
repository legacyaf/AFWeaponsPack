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
- **Name:** SCAR is FN's trademark, so the weapon gets our own name. Proposed: "AF Mk 17", the US military
  designation of the SCAR-H, used the same way as "AF M107A1". The owner decides.

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
   - Finishes: black, FDE two-tone (the classic SCAR look), and the gold skin.
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
