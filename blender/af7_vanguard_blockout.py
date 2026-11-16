"""
AF-7 "Vanguard" - starter blockout for Blender (4.2 LTS or newer).

HOW TO USE
  1. Open Blender, start a new General file.
  2. Go to the Scripting tab, click Open, choose this file, click Run Script (play button).
  3. A rough, real-scale rifle appears. Shape it into your own design.

WHAT YOU GET
  - Units in meters, rifle about 0.89 m long, pointing forward along +Y, up is +Z.
  - Origin (0,0,0) is at the trigger. Keep it there; DayZ animations use it.
  - Collections:
      AF7_Body        static parts of the gun (become one mesh later)
      AF7_Moving      parts that animate (bolt, trigger, ...) - keep them separate
      AF7_Memory      empties marking points DayZ needs (muzzle, eye, ejection...)
      AF7_Proxies     empties marking where attachments sit (optic, magazine, muzzle)
      AF7_Reference   reference only (STANAG magazine, human-hand scale) - DON'T export
  - Each object has a custom property "dayz" explaining what it becomes in DayZ.
    Names marked VERIFY must be checked against
    the vanilla M4 config (see docs/GUIDE.md, step 0).

Running the script again deletes and rebuilds everything it made (objects named AF7_*),
so don't run it again after you've started editing unless you want a fresh start.
"""

import math
import bpy

PREFIX = "AF7_"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def clean():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PREFIX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for col in list(bpy.data.collections):
        if col.name.startswith(PREFIX):
            bpy.data.collections.remove(col)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def collection(name):
    col = bpy.data.collections.new(PREFIX + name)
    bpy.context.scene.collection.children.link(col)
    return col


def material(name, rgb, rough=0.5, metal=0.0):
    mat = bpy.data.materials.get(PREFIX + name) or bpy.data.materials.new(PREFIX + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    mat.diffuse_color = (*rgb, 1.0)  # solid viewport colour
    return mat


def _finish(ob, col, mat, note, bevel):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    col.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    ob["dayz"] = note
    if bevel:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1          # flat chamfers = angular, modern look
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
    return ob


def box(name, col, mat, center, size, rot=(0, 0, 0), bevel=0.002, note=""):
    """center/size in meters, rot in degrees (X, Y, Z)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=center,
                                    rotation=[math.radians(a) for a in rot])
    ob = bpy.context.active_object
    ob.name = PREFIX + name
    ob.data.name = ob.name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, col, mat, note, bevel)


def cyl(name, col, mat, y0, y1, radius, z=0.0, x=0.0, sides=16, bevel=0.0, note=""):
    """Cylinder along the Y axis (the bore direction) from y0 to y1."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=y1 - y0,
                                        location=(x, (y0 + y1) / 2, z),
                                        rotation=(math.radians(90), 0, 0))
    ob = bpy.context.active_object
    ob.name = PREFIX + name
    ob.data.name = ob.name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return _finish(ob, col, mat, note, bevel)


def empty(name, col, loc, note, kind="PLAIN_AXES", size=0.015):
    ob = bpy.data.objects.new(PREFIX + name, None)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    ob.location = loc
    ob["dayz"] = note
    col.objects.link(ob)
    return ob


def cut_slots(target, col, count, start_y, step, z, side_x, size):
    """Cuts a row of slots (M-LOK style) into both sides of `target` (non-destructive)."""
    cutter = box(target.name.replace(PREFIX, "") + "_SlotCutter", col, None,
                 (0, start_y, z), (side_x * 2 + 0.02, size[0], size[1]), bevel=0,
                 note="Boolean cutter - hidden. Apply the Boolean on the handguard, then delete this.")
    arr = cutter.modifiers.new("Array", "ARRAY")
    arr.count = count
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = (0, step, 0)
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    boo = target.modifiers.new("Slots", "BOOLEAN")
    boo.operation = "DIFFERENCE"
    boo.object = cutter
    # keep bevel last so slot edges get chamfered too
    target.modifiers.move(len(target.modifiers) - 1, 0)
    return cutter


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def build():
    clean()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    body = collection("Body")
    moving = collection("Moving")
    memory = collection("Memory")
    proxies = collection("Proxies")
    ref = collection("Reference")

    # Blockout colours: tan furniture, dark grey metal (Allied Forces two-tone)
    m_metal = material("Metal", (0.035, 0.037, 0.04), rough=0.45, metal=0.8)
    m_poly = material("Polymer", (0.42, 0.34, 0.22), rough=0.75)
    m_rubber = material("Rubber", (0.02, 0.02, 0.02), rough=0.9)
    m_move = material("Moving", (0.6, 0.12, 0.08), rough=0.5, metal=0.3)
    m_ref = material("Reference", (0.2, 0.35, 0.6), rough=0.6)

    BORE = 0.055  # height of the barrel centre line above the trigger

    # --- Receiver -----------------------------------------------------------
    box("UpperReceiver", body, m_metal, (0, 0.01, 0.055), (0.032, 0.22, 0.042), bevel=0.004,
        note="Upper receiver. Angular, flat-sided - the main 'Vanguard' shape.")
    box("LowerReceiver", body, m_poly, (0, 0.0, 0.020), (0.030, 0.19, 0.032), bevel=0.003,
        note="Lower receiver.")
    box("MagWell", body, m_poly, (0, 0.075, -0.012), (0.032, 0.07, 0.05), rot=(-6, 0, 0), bevel=0.004,
        note="Magazine well. Inside must fit a vanilla STANAG mag (see AF7_Reference).")
    box("EjectionPort", body, m_metal, (0.0165, 0.035, 0.058), (0.002, 0.065, 0.016), bevel=0.0,
        note="Ejection port outline, right side. Case ejection memory points sit here.")

    # --- Grip, trigger guard ------------------------------------------------
    box("PistolGrip", body, m_poly, (0, -0.045, -0.050), (0.028, 0.034, 0.105), rot=(-20, 0, 0), bevel=0.005,
        note="Pistol grip. The right hand holds here - keep its angle close to an M4 grip.")
    box("TriggerGuard", body, m_poly, (0, 0.010, -0.028), (0.016, 0.075, 0.006), bevel=0.002,
        note="Trigger guard (bottom bar).")

    # --- Handguard (long, angular, monolithic) -------------------------------
    hg = box("Handguard", body, m_poly, (0, 0.29, BORE + 0.002), (0.054, 0.34, 0.060), bevel=0.012,
             note="Handguard. Big chamfers + slots give the modern look. The left hand holds here.")
    cut_slots(hg, body, count=5, start_y=0.17, step=0.055, z=BORE, side_x=0.027, size=(0.032, 0.010))

    # --- Top rail ------------------------------------------------------------
    rail = box("TopRail", body, m_metal, (0, 0.17, 0.083), (0.021, 0.58, 0.008), bevel=0.0015,
               note="Picatinny rail. The optic proxy sits on it (AF7_Proxy_Optic).")
    for i in range(40):  # rail notches
        box(f"RailNotch_{i:02d}", body, m_metal, (0, -0.11 + i * 0.0145, 0.0885), (0.021, 0.0055, 0.003),
            bevel=0, note="Rail notch - join into TopRail when happy.")

    # --- Barrel & muzzle -----------------------------------------------------
    cyl("Barrel", body, m_metal, 0.10, 0.48, 0.0095, z=BORE, sides=20,
        note="Barrel (14.5 in). Mostly hidden by the handguard.")
    cyl("MuzzleBrake", body, m_metal, 0.46, 0.53, 0.0135, z=BORE, sides=8, bevel=0.002,
        note="Muzzle brake, 8-sided for the angular style. Must be in the 'hide_barrel' selection (confirmed from vanilla M4) so it hides when a suppressor is attached.")

    # --- Sights (flip-up backup irons) --------------------------------------
    box("FrontSight", body, m_metal, (0, 0.43, 0.097), (0.012, 0.012, 0.022), bevel=0.002,
        note="Front backup sight. Lines up with AF7_Mem_Eye and rear sight.")
    box("RearSight", body, m_metal, (0, -0.075, 0.097), (0.018, 0.014, 0.022), bevel=0.002,
        note="Rear backup sight (aperture).")

    # --- Stock (skeleton) ----------------------------------------------------
    cyl("BufferTube", body, m_metal, -0.30, -0.095, 0.0155, z=BORE, sides=16,
        note="Buffer tube / stock spine.")
    box("StockTopBar", body, m_poly, (0, -0.235, 0.080), (0.016, 0.22, 0.014), bevel=0.003,
        note="Skeleton stock - top bar, sits on the buffer tube.")
    box("StockLowerBar", body, m_poly, (0, -0.2275, 0.0), (0.016, 0.25, 0.013), rot=(18.8, 0, 0), bevel=0.003,
        note="Skeleton stock - angled lower bar, from the back of the receiver down to the butt pad.")
    box("StockCheek", body, m_poly, (0, -0.25, 0.090), (0.024, 0.08, 0.016), bevel=0.004,
        note="Cheek rest (where the face sits when aiming).")
    box("ButtPad", body, m_rubber, (0, -0.348, 0.0175), (0.034, 0.016, 0.155), bevel=0.005,
        note="Rubber butt pad. Rear end of the rifle.")

    # --- Moving parts (separate objects = separate animated selections) ------
    box("Weapon_Trigger", moving, m_move, (0, 0.012, -0.012), (0.006, 0.006, 0.022), rot=(15, 0, 0), bevel=0.001,
        note="CONFIRMED bone/selection: Weapon_Trigger. Rotates when firing.")
    box("ChargingHandle", moving, m_move, (0, -0.115, 0.072), (0.04, 0.02, 0.008), bevel=0.0015,
        note="Probably one of Weapon_Bone_01..06 - find out which with GUIDE step 9b. Pulled back to chamber.")
    box("Weapon_Bolt", moving, m_move, (0.012, 0.035, 0.057), (0.008, 0.06, 0.012), bevel=0.001,
        note="CONFIRMED bone/selection: Weapon_Bolt. Visible through the ejection port, moves back when firing.")
    box("MagRelease", moving, m_move, (0.0165, 0.06, 0.012), (0.004, 0.01, 0.01), bevel=0.001,
        note="Mag release button, right side. Maybe one of Weapon_Bone_01..06 (GUIDE step 9b), or leave static.")
    box("Safety", moving, m_move, (-0.0165, -0.02, 0.03), (0.004, 0.018, 0.006), bevel=0.001,
        note="Safety selector, left side. Maybe one of Weapon_Bone_01..06 (GUIDE step 9b), or leave static.")

    # --- Memory points -------------------------------------------------------
    empty("Mem_Muzzle", memory, (0, 0.53, BORE),
          "VERIFY name: 'usti hlavne' - muzzle end. Bullets and muzzle flash start here.")
    empty("Mem_BarrelEnd", memory, (0, 0.43, BORE),
          "VERIFY name: 'konec hlavne' - a point behind the muzzle; with the muzzle it sets the firing direction.")
    empty("Mem_Eye", memory, (0, -0.16, 0.097),
          "CONFIRMED name: 'eye' - camera position for iron sights. Must line up with rear + front sight.")
    empty("Mem_CaseStart", memory, (0.017, 0.035, BORE),
          "CONFIRMED name: 'Nabojnicestart' - where spent cases appear.")
    empty("Mem_CaseEnd", memory, (0.09, 0.02, 0.085),
          "CONFIRMED name: 'Nabojniceend' - direction spent cases fly.")

    # --- Attachment proxies --------------------------------------------------
    empty("Proxy_Optic", proxies, (0, 0.0, 0.087),
          "Optic proxy on the rail. Copy the proxy path from the vanilla M4 (see GUIDE).", kind="ARROWS", size=0.03)
    empty("Proxy_Magazine", proxies, (0, 0.075, -0.012),
          "Magazine proxy. Must be in the Weapon_Magazine selection (CONFIRMED) so reloads move it.", kind="ARROWS", size=0.03)
    empty("Proxy_Muzzle", proxies, (0, 0.53, BORE),
          "Muzzle attachment proxy (suppressor / compensator).", kind="ARROWS", size=0.03)

    # --- Reference (don't export) -------------------------------------------
    box("Ref_STANAG_Top", ref, m_ref, (0, 0.075, -0.06), (0.023, 0.062, 0.10), rot=(-6, 0, 0), bevel=0.002,
        note="REFERENCE ONLY. Approx STANAG 30-rnd mag. DayZ shows the real mag via the proxy.")
    box("Ref_STANAG_Bottom", ref, m_ref, (0, 0.092, -0.155), (0.023, 0.060, 0.10), rot=(-14, 0, 0), bevel=0.002,
        note="REFERENCE ONLY.")
    box("Ref_HandSize", ref, m_ref, (0.03, -0.045, -0.05), (0.02, 0.09, 0.10), rot=(-20, 0, 0), bevel=0.01,
        note="REFERENCE ONLY. Roughly the size of a gloved hand around the grip.")
    for ob in ref.objects:
        ob.display_type = "WIRE"
        ob.hide_render = True

    # Viewport niceties
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.color_type = "MATERIAL"
                    space.clip_start = 0.001


if __name__ == "__main__":
    build()
    print("AF-7 Vanguard blockout built.")
