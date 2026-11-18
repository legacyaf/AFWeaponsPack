# AF Weapons Pack: in-game test checklist

Run this on the test server after every published build. It takes about ten minutes and produces the same set of evidence each time, so a problem is caught in one round.

## Before you start

1. Publish the build and update the mod on the server and your client.
2. Restart the server. The licence check only runs at start.
3. Check the server log for `[AF_Weapons] Server licence OK.` If it says `NOT LICENSED`, stop: the weapons will delete themselves. See the Mod Shop staff panel for the address the server actually called from.

## How to capture

- **Use video (MP4) or SDR screenshots where you can.** HDR screenshots (`.jxr`) clip bright areas when converted and make finishes look washed out.
- Daylight, sun behind you, for anything about colour or finish.
- One weapon at a time: spawn it, do the steps, then the next.

## The checks

Do every step for **each finish** (`AF7_Vanguard`, `AF7_Vanguard_Gold`).

| # | What to do | What to capture | What it tells us |
|---|---|---|---|
| 1 | Open the inventory view of the rifle with no attachments, side-on | Screenshot | Overall look, finish colours, AF plates |
| 2 | Hold the rifle in first person and look down at it | Screenshot | Texture sharpness, scratches, missing surfaces |
| 3 | Third person, standing, from the right and the left | 2 screenshots | Hand positions, how it sits on the body |
| 4 | Aim down the iron sights, no optic | Screenshot | Sight alignment, rear sight visible and not cut off, no blur |
| 5 | Fit an optic and aim | Screenshot | Optic height and position on the rail |
| 6 | Fire five rounds, camera on the ejection port | Short clip | Bolt movement, casing ejection, muzzle flash position |
| 7 | Reload with a 30-round STANAG | Short clip | Reload animation, magazine path into the well |
| 8 | Inventory side-on with each magazine in turn: 30-round STANAG, coupled, 60-round, CMAG, LAR | Screenshot each | Magazine fit |
| 9 | Fit a suppressor, inventory side-on | Screenshot | Suppressor position; muzzle brake hidden underneath |
| 10 | Fit a flashlight, switch it on | Screenshot | Flashlight position and beam direction |
| 11 | Drop the rifle on flat ground and walk around it | Screenshot | Ground pose, collision, shadow |
| 12 | Walk away from the dropped rifle to about 5 m, 20 m, 50 m and 100 m | Screenshot at each | LOD changes: no popping, shape holds, no holes or wrong colours (LODs 5-7 are new in 0.8.2) |
| 13 | Damage the rifle with an admin tool to Damaged and Ruined | Screenshot each | Damage overlays |
| 14 | Chamber a loose 5.56 round, then a loose .308 round | Note what happens | Both calibres chamber by hand |

## Multiplayer

With a second player on the server:

- Each of you sees the other's rifle with the right finish and attachments.
- Fire while the other watches: muzzle flash and sound come from the right place.
- One of you reloads: the magazine swap looks right from the outside.

## Performance

- Note your frame rate holding a vanilla M4, then holding the AF-7, in the same spot.
- Repeat with five AF-7s dropped on the ground nearby.

## Sending results

Send the screenshots and clips in one message with the build version. Say which step each problem belongs to, for example "step 8, 60-round sits too far back".

## AF M41 Pathfinder: first-test checks

Do these for `AFM41_Pathfinder` (and glance at `AFM41_Pathfinder_Gold` for the finish). Steps 1-4, 11-13 of the table above apply as they are. These replace the magazine and bolt steps:

| # | What to do | What to capture | What it tells us |
|---|---|---|---|
| M1 | Load five loose rounds, then cycle the bolt slowly, camera on the right side of the action | Short clip | Whether the handle lifts, and the bolt and cocking piece slide back together |
| M2 | Fire and cycle, first person | Short clip | Hand reaches the bolt knob; casing ejects from the port |
| M3 | Load with a stripper clip | Short clip | Loading animation |
| M8 | (0.8.1) Open the bolt on a loaded rifle, look down into the action; repeat on an empty rifle | 2 screenshots | Two brass rounds show in the magazine when loaded and are gone when empty |
| M9 | (0.8.1) Inventory view, left side of the receiver and both sides of the butt | 3 screenshots | Stamps are readable and the right way round: `AF M41 / 1941`, `No 07386`, the round cartouche, the boxed serial |
| M10 | (0.8.3) Fit a ghillie wrap (any colour) | 2 screenshots, both sides | Wrap pieces sit on the receiver, handguard and butt as they do on the vanilla Mosin; none floating |
| M11 | (0.8.3) Hold the rifle in first and third person, and aim | 2 screenshots | The leather sling hangs under the rifle and does not cut through the hands or the arm |
| M4 | Fit a PU scope, inventory side-on and aimed | 2 screenshots | Scope sits on the receiver, not floating or sunk; scope view works |
| M5 | Fit the compensator, then the improvised suppressor, then the bayonet | Screenshot each | Muzzle attachment positions |
| M6 | Aim down the iron sights | Screenshot | Front blade centred in the rear notch |
| M7 | Carry it on the back and in the hands, third person | 2 screenshots | Length and position against the body |
