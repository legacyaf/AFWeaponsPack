# AF StG 44: The Finish Update

The AF StG 44 has been rebuilt from the surface up. New shape where it mattered, a finish that tells you where the rifle has been, sights that actually line up, and a scope you can see through cleanly. Here's everything that changed.

---

## A rifle that looks used, not factory fresh

Every scrape and polished patch is now placed where a soldier's hands, kit and sling would really wear it, not scattered at random:

- **Selector and magazine catch.** Thumb-worn: the edges are rubbed back towards bare steel.
- **Cocking handle and its slot.** Polished by the hand that works it every reload.
- **Mouth of the magazine housing.** Scuffed by every magazine slammed home.
- **Trigger guard.** Its underside is worn bright.
- **Sling loops, front and rear.** Rubbed by the sling.
- **Under the handguard.** Smoothed where the support hand grips.
- **Left side of the receiver.** Dulled where the rifle rides slung against your back.
- **Front sight hood.** Knocked about, like every front sight that has ever caught on a doorframe.
- **The magazine has its own history:** worn feed lips, a battered floor plate, and a body smoothed by pouches.

The finish has a direction too. The top of the rifle carries a faint handled sheen, and oil darkens the bottom of the receiver and its seams. In sun it reads as a rifle that has been carried, cleaned and used again.

## Steel that catches the light

The steel now shines the way real worn steel does. Oily, polished patches gleam, dusty corners stay dull, and the rubbed edges flash when the sun hits them.

We measured it against the vanilla AKM's textures and matched its range of shine. In noon sun the receiver top now catches the light along its whole length, and the steel shows light and dark mottling instead of a flat matte. It was checked in four lights: noon sun, full overcast, low evening sun and early morning.

## Real beech

The stock and grip panels are proper beech now:

- Broad growth bands along the stock.
- The little lens-shaped **ray flecks** that mark beech out from every other gunstock wood, each with its own sheen.
- Hand-oiled darkening where your cheek and hand rest.
- Dings with dirt in them, and fine scratches across the grain.

## Pressed-steel detail

The StG 44 was a stamped-steel rifle, and now it shows. These are pressed into the steel rather than painted on:

- The receiver flute and its swage line.
- A row of spot welds.
- A raised bead framing the trigger housing.
- Sunk panels on the magazine housing.
- Two long flutes down the magazine.
- **E** and **D** selector markings.
- A serial number on the left of the receiver.
- *"legacy was here"* scratched into the right side.

Dirt collects in the pressings and the finish wears off their raised rims, just like the real thing.

## Smoother, rounder, sharper detail

The surface detail is now baked from a far more detailed version of the rifle, about 30,000 triangles. That's the same high-to-low method professional game artists use. Rounded edges, rims and small round parts look smooth and solid up close, while the in-game model stays light at 14,446 triangles.

## New shape where it counted

- **The handguard is a proper stamped-steel shell** around the barrel, butted tight against the receiver, with six cooling holes. No more floating handguard.
- **A slimmer, rounder stock.** No more plank of wood.
- **Gas block and stacking rod** moved to where they belong.
- **The magazine floor plate** now has its retaining plate and catch button, so it's no longer a bare slab from below.

## Iron sights that line up

The rear notch now sits level with the front post and is wider. When you aim, the front post sits centred in the notch with light on both sides. Previously the post hid behind the notch.

## A clean scope view

The ZF4's view through the tube is now a clean round picture with the crosshair. The black square that used to frame the reticle is gone.

The scope is still a normal attachment: take it off in the inventory to use the iron sights.

## Looks right at any distance

- **No more crease along the stock** on the distance models.
- **No black rectangle** where the ejection port is on far-away rifles.
- **No dark seams** at range: the texture edges are padded.
- **The magazine's collision box** now covers the whole magazine.

---

## Under the hood

For the curious, here is what drives all of this:

- **One shared height map per side.** The pressed detail is drawn once at 10 pixels per millimetre, and it drives the surface relief, the dirt and the wear together. That way the three always agree.
- **High-to-low normal bake.** Shape normals come from the detailed version of the rifle, and the fine bump detail comes from the game model. The two are combined with reoriented normal mapping.
- **Shine with a range.** Specular follows the gloss and darkens in corners, then is matched to the range measured on the vanilla AKM's maps.
- **Edge padding.** Every texture is filled out beyond its edges, so the game's smaller texture levels never pull dark pixels into the rifle at range.
- **Checked in game.** In-game test captures cover noon sun, overcast, evening and morning, side by side with the vanilla AKM.
- **Built and signed clean.** The build, signature and model checks all pass.

---

*Next version: reshaping the magazine housing and stock so they match the chamfered detail of the vanilla rifles.*
