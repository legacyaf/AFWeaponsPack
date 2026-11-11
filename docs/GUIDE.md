# AF-7 Vanguard: step-by-step guide (Blender to DayZ)

Follow the steps in order. Each step says what you should end up with.
Anything marked **VERIFY** is a DayZ name I couldn't confirm without the game files. Step 0 shows you how to check them.

---

## Step 0: One-time setup (about 1 hour)

1. **Blender:** install 4.2 LTS or newer from blender.org.
2. **DayZ Tools:** install from Steam (Library > Tools > DayZ Tools).
3. **P: drive:** open DayZ Tools, then **Workdrive**:
   - Click **Mount** to create the `P:\` drive.
   - Click **Extract game data**. This takes a while and needs about 20 GB of free space.
   - From then on, the vanilla configs are in `P:\DZ\...`.
4. **Copy the source folder:** copy `source/AF_Weapons` from this repo to `P:\AF_Weapons`. Work there from now on.
5. **Check the VERIFY names.** Already checked from the vanilla M4 config: the slot names, `eye`, `Nabojnicestart` / `Nabojniceend`, `hide_barrel` and `camo`. The bone names are confirmed from the M4 animation file: `Weapon_Trigger`, `Weapon_Bolt`, `Weapon_Magazine`, `Weapon_Bullet` and `Weapon_Bone_01` to `_06`. **Still unknown:** what Bone_01 to _06 do (see step 9b) and the muzzle memory point names. Here's the original checklist: open `P:\DZ\weapons\firearms\m4\config.cpp` in Notepad++ or VS Code. If you only find `config.bin`, convert it with **DayZ Tools > CfgConvert**. Find `class M4A1_Base` and write down:
   - `boneRemap[]`: the **first** name of each pair (`"bolt"`, `"magazine"`, ...) is a selection name. Your model needs exactly those names. Fix `model.cfg` and your Blender object names to match.
   - `attachments[]`: the slot names. Copy the optic, muzzle and flashlight slots into the `[MODEL]` attachments line in `config.cpp`.
   - Any memory point names, such as `"usti hlavne"`, `"konec hlavne"`, `"eye"` and `"nabojnicestart"`. Compare them with the empties in `AF7_Memory`.
6. **Blender add-on for P3D files:** install the **"Arma 3 Object Builder"** add-on by MrClock, which is free on GitHub. It lets Blender save `.p3d` files with LODs, named selections and proxies directly. Check that it supports your Blender version. If it doesn't, use FBX export and import into Object Builder instead (step 7, option B).

**Done when:** `P:\DZ` exists and you've written down the real names.

---

## Step 1: Load the blockout (5 minutes)

Use either option:
- **Option A:** open `blender/af7_vanguard_blockout.blend`.
- **Option B:** in a new Blender file, go to the **Scripting** tab, click **Open**, choose `af7_vanguard_blockout.py`, then click **Run Script**.

Look around. Red parts move in game. Wireframe blue parts are reference only. Click any object and look in **Object Properties > Custom Properties > dayz** to see what it's for.

**Rules that keep DayZ happy:**
- The rifle points along **+Y**, up is **+Z**, units are **meters**.
- Don't move the **origin** (0,0,0, at the trigger). DayZ's M4 animations hold the gun relative to it.
- Keep the grip, handguard and stock roughly where they are. The hands and shoulder from the M4 animations land there.
- The STANAG reference magazine must fit inside your mag well.

---

## Step 2: Make it yours (the fun part, several evenings)

Turn the boxes into the Vanguard. Modeling basics to learn: **Edit mode (Tab), extrude (E), inset (I), loop cut (Ctrl+R), bevel (Ctrl+B)**. The free "Blender hard surface for beginners" videos on YouTube cover all of these.

Style tips for the Vanguard:
- **Shape:** flat sides with big chamfers (45° cut corners). Avoid round, soft shapes.
- **Colors:** a two-tone look. Tan polymer furniture against a dark grey metal receiver.
- **Details:** slots in the handguard, a hex-shaped muzzle brake, and a skeleton stock with cut-outs.
- **Detail level:** put detail where the player looks: the top of the receiver, the rail and the iron sights. The bottom of the stock barely matters.

**Polygon budget:** about **10,000–15,000 triangles** for the main model. Turn on **Statistics** in the viewport Overlays menu to see your count.

**Done when:** you like how it looks, and the moving parts are still separate objects.

---

## Step 3: Clean up the mesh

1. **Apply modifiers:** apply the Booleans on the handguard first, then the Bevels. Delete the `*_SlotCutter` objects.
2. **Join parts:** join all the body parts into one object, `AF7_Body` (select them, then press **Ctrl+J**). Keep the moving parts separate.
3. **Shading:** select everything you'll export and choose **Shade Auto Smooth**, or add a **Weighted Normal** modifier. This gives crisp edges on flat surfaces.
4. **Scale:** select everything you'll export and press **Ctrl+A > All Transforms**.

---

## Step 4: UV unwrap

1. **Seams:** mark seams along hard edges and hidden areas, like the underside and the inside of the mag well.
2. **Unwrap:** press **U > Unwrap**.
3. **Pack:** in the UV editor, choose **UV > Pack Islands**, with a small margin.
4. **Texel density:** keep it even. Parts the player sees up close, like the receiver top and the rail, can get more space.
5. **Material:** use one material for the whole gun. It's simpler, and it matches `hiddenSelections[] = {"camo"}`.

---

## Step 5: Textures

Make these maps, all the same size (2048×2048 is fine for a first gun):

| File | What it is | How to make it |
|---|---|---|
| `af7_body_co` | Color | Paint in Blender, or use Substance Painter / ArmorPaint |
| `af7_body_nohq` | Normal map | Bake from a high-poly version, or paint fine detail |
| `af7_body_smdi` | Shininess | Green = specular, Blue = gloss |
| `af7_body_as` | Ambient occlusion | Bake in Blender (Cycles > Bake > Ambient Occlusion) |

1. **Export:** save each map as PNG or TGA.
2. **Convert:** convert them to `.paa` with **DayZ Tools > ImageToPAA**. Keep the suffixes (`_co`, `_nohq`, ...), because DayZ uses them to pick the compression.
3. **Place:** put them in `P:\AF_Weapons\af7_vanguard\data\`.
4. **Material values:** compare `af7_body.rvmat` with a vanilla M4 rvmat in `P:\DZ\weapons\firearms\m4\data\` and copy over any values that differ.

**Free option:** **ArmorPaint** is free and works like Substance Painter.

---

## Step 6: LODs and special parts

A DayZ model is several versions of the gun (LODs) in one `.p3d` file:

| LOD | What goes in it |
|---|---|
| **Resolution 0** | Your full model (10–15k triangles), with moving parts and proxies |
| **Resolution 1, 2, 3** | Simpler copies at about 50%, 25% and 10% (use the Decimate modifier, then fix by hand) |
| **Geometry** | 3–6 simple closed boxes around the gun, with mass set to about 3.2 kg total. Add the named property `autocenter = 0` |
| **Fire Geometry** | A copy of the Geometry LOD |
| **Memory** | The memory points (from `AF7_Memory`), as single vertices with the names you checked in step 0 |

**Named selections:**
- Each moving part needs a named selection matching its bone name in `model.cfg` (`Weapon_Bolt`, `Weapon_Trigger`, ...). Do this in **every** resolution LOD.
- The whole body goes in `camo`.

**Proxies:** proxies are placeholders that show attachments.
1. In Object Builder, look at how the **vanilla M4** places its optic, magazine and muzzle proxies. The paths look like `\dz\weapons\...\proxy\...`.
2. Copy those proxy paths onto the `AF7_Proxies` positions.
3. Put the **magazine proxy** in the `Weapon_Magazine` selection, so the reload animation moves it.

**Done when:** `P:\AF_Weapons\af7_vanguard\af7_vanguard.p3d` exists.

---

## Step 7: Get it into a .p3d

- **Option A (recommended):** the Arma 3 Object Builder add-on in Blender. Set each LOD collection's type, then export straight to `.p3d`.
- **Option B:**
  1. In Blender, choose **File > Export > FBX**, with **Apply Transform** on and **Forward = Y, Up = Z**.
  2. In **Object Builder**, choose **File > Import > FBX**.
  3. Create the LODs, named selections, proxies and memory points by hand, then save the `.p3d`.

Then open the `.p3d` in **Object Builder** anyway, to check:
- the mass is set
- the named selections exist in every LOD
- the proxies show up

---

## Step 8: Switch the config to your model

In `P:\AF_Weapons\config.cpp`, remove the `//` in front of every line marked `[MODEL]`. Save it.

---

## Step 9: Build and test

1. **Build:** run `build.bat`. Point its `SRC` path at `P:\AF_Weapons` if you're working on P:.
2. **Test offline first:** start **DayZDiag_x64.exe** with `-mod=@AF_WeaponsPack` on an offline mission, or run your own test server.
3. **Spawn it:** spawn `AF7_Vanguard` with an admin tool.

**Check:**
- [ ] Hands sit on the grip and handguard. If they're off, **move the model, not the origin**, then rebuild.
- [ ] The iron sights line up when aiming. If not, move the `eye` memory point.
- [ ] Bullets leave the muzzle, and spent cases come out of the ejection port.
- [ ] A STANAG magazine attaches and reloads, and optics sit on the rail.
- [ ] It looks right at a distance, which means the LODs switch properly.
- [ ] There are no `AF_Weapons` errors in the `.RPT` log, in `%localappdata%\DayZ`.

### Step 9b: Work out what Weapon_Bone_01 to _06 do

The M4 animation moves six extra bones, but the file doesn't say what they are.

1. In a **test build**, put a small, obvious cube in each one: a cube in the `Weapon_Bone_01` selection, another in `Weapon_Bone_02`, and so on. Place them in different spots on the gun, and add matching names to `model.cfg`.
2. In game, reload, fire, and switch fire modes.
3. Watch which cube moves like a charging handle, dust cover, bolt catch, mag release or safety.
4. Write the results down, then put your real parts in the right selections and delete the test cubes.

**Expect the first test to have problems:** usually the hand position or a wrong selection name. Fix one thing, rebuild, and test again.

---

## When something breaks

Copy the `AF_Weapons` lines from the `.RPT` log and send them to Claude.
