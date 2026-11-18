Allied Forces Flags - server setup

1. Load the mod on the server and clients:  -mod=@AF_Flags
2. Copy Keys\AlliedForces.bikey into the server's keys folder
   (the same key as the Allied Forces Weapons Pack; skip if it is already there).
3. Merge ServerFiles\af_flags_types.xml into the mission's types.xml.

Item class:  Flag_AF_Sierra
It does not spawn as loot by default (nominal 0). Spawn it with an admin tool,
sell it at a trader, or raise nominal/min in the types entry.
It goes on the territory flagpole like any vanilla flag.
