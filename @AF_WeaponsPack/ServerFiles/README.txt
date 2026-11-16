Allied Forces Weapons Pack - loot files for server owners
==========================================================

These files make the AF-7 Vanguard spawn as loot. They only matter on the
server; players do not need them. Your server also needs a licence for the
mod to work at all (see the Workshop page).

Files
  af_weapons_types.xml            what spawns, how many, and where
  af_weapons_spawnabletypes.xml   what can spawn attached (optic, magazine)

Class names
  AF7_Vanguard        standard finish. Spawns: 3 on the map, Military, Tier 3-4.
  AF7_Vanguard_Gold   gold floral finish. Does NOT spawn by default (nominal 0).
                      Raise nominal and min in af_weapons_types.xml to change that.

OPTION A - paste into your existing files (simplest)
  1. Open af_weapons_types.xml and copy everything between <types> and </types>.
     Paste it into your mission's db\types.xml, just before the final </types>.
  2. Open af_weapons_spawnabletypes.xml and copy everything between
     <spawnabletypes> and </spawnabletypes>. Paste it into your mission's
     cfgspawnabletypes.xml, just before the final </spawnabletypes>.
  3. Restart the server.

OPTION B - keep the files separate
  1. Copy this whole folder into your mission folder and name it af_ce, e.g.
       mpmissions\dayzOffline.chernarusplus\af_ce\
  2. Open cfgeconomycore.xml in the mission folder and add this inside
     <economycore>, before </economycore>:

       <ce folder="af_ce">
           <file name="af_weapons_types.xml" type="types" />
           <file name="af_weapons_spawnabletypes.xml" type="spawnabletypes" />
       </ce>

  3. Restart the server.

Use one option, not both: the same class listed twice causes warnings.

Notes
  - The usage and value tags (Military, Tier3, Tier4) are for Chernarus and
    Livonia. Other maps may use different tag names; match them to your map's
    cfglimitsdefinition.xml or the rifle will not spawn.
  - Ammo: the rifle takes 5.56x45 from STANAG and CMAG magazines, and
    .308 Winchester from LAR magazines. Those are vanilla items and already spawn.
