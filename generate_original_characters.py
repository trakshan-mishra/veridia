"""Build Veridia's original rigged low-poly character assets with Blender.

Run from my_proj:
    blender --background --python generate_original_characters.py

It writes five self-contained GLB files into assets/.  Every asset has actual
mesh geometry, an armature, and a looping Idle action; no character billboard
or portrait is used in the world.
"""

from pathlib import Path
import bpy
from math import radians

OUT = Path(__file__).parent / "assets"

CAST = [
    ("village_elder", "Village Elder", (0.95, 0.56, 0.25, 1), (0.34, 0.15, 0.07, 1), "staff"),
    ("vanguard", "Vanguard", (0.34, 0.48, 0.74, 1), (0.13, 0.18, 0.29, 1), "sword"),
    ("chronicler", "Chronicler", (0.93, 0.67, 0.30, 1), (0.25, 0.10, 0.06, 1), "book"),
    ("gatekeeper", "Gatekeeper", (0.38, 0.62, 0.80, 1), (0.08, 0.18, 0.28, 1), "staff"),
    ("bartender_npc", "Rhea", (0.52, 0.25, 0.14, 1), (0.95, 0.78, 0.45, 1), "mug"),
]


def material(name, color, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    m.metallic = metallic
    m.roughness = 0.66
    return m


def primitive(kind, name, location, scale, mat, parent=None, bone=None):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=scale[0], radius2=scale[1], depth=scale[2], location=location)
    elif kind == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=scale[0], depth=scale[1], location=location)
    else:
        bpy.ops.mesh.primitive_cube_add(location=location)
    ob = bpy.context.object
    ob.name = name
    if kind in {"sphere", "cube"}:
        ob.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = kind in {"sphere", "cylinder", "cone"}
    if parent:
        ob.parent = parent
        if bone:
            ob.parent_type = "BONE"
            ob.parent_bone = bone
            ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def rig(name):
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = name + "_Rig"
    arm.data.name = name + "_Skeleton"
    root = arm.data.edit_bones[0]
    root.name = "Root"; root.head = (0, 0, 0); root.tail = (0, 0, 0.9)
    def bone(n, head, tail, parent="Root"):
        b = arm.data.edit_bones.new(n); b.head = head; b.tail = tail; b.parent = arm.data.edit_bones[parent]; return b
    bone("Spine", (0, 0, 0.72), (0, 0, 1.42))
    bone("Head", (0, 0, 1.38), (0, 0, 1.75), "Spine")
    bone("Arm.L", (0.25, 0, 1.3), (0.58, 0, 0.95), "Spine")
    bone("Arm.R", (-0.25, 0, 1.3), (-0.58, 0, 0.95), "Spine")
    bone("Leg.L", (0.15, 0, 0.72), (0.18, 0, 0.05))
    bone("Leg.R", (-0.15, 0, 0.72), (-0.18, 0, 0.05))
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def idle(arm):
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for frame, lift, swing in [(1, 0.0, 0.10), (30, 0.025, -0.10), (60, 0.0, 0.10)]:
        arm.pose.bones["Spine"].location.z = lift
        arm.pose.bones["Spine"].rotation_mode = "XYZ"
        arm.pose.bones["Spine"].rotation_euler.y = radians(swing * 18)
        for side, sign in (("Arm.L", 1), ("Arm.R", -1)):
            arm.pose.bones[side].rotation_mode = "XYZ"
            arm.pose.bones[side].rotation_euler.x = radians(swing * 34 * sign)
        for side, sign in (("Leg.L", -1), ("Leg.R", 1)):
            arm.pose.bones[side].rotation_mode = "XYZ"
            arm.pose.bones[side].rotation_euler.x = radians(swing * 14 * sign)
        for b in ("Spine", "Arm.L", "Arm.R", "Leg.L", "Leg.R"):
            arm.pose.bones[b].keyframe_insert("rotation_euler", frame=frame)
        arm.pose.bones["Spine"].keyframe_insert("location", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")
    action = arm.animation_data.action
    action.name = "Idle"


def character(slug, display, cloth_color, trim_color, prop):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    skin = material("Skin", (0.67, 0.38, 0.22, 1))
    cloth = material("Cloth", cloth_color)
    trim = material("Trim", trim_color, 0.15)
    dark = material("Boots", (0.055, 0.04, 0.035, 1))
    gold = material("Accent", (0.95, 0.58, 0.16, 1), 0.45)
    arm = rig(slug)
    # Coordinates are local-to-bone visual offsets after parenting: this makes the
    # exported skeleton animate the actual mesh rather than just a parent group.
    primitive("cone", "Robe", (0, 0, 0.66), (0.43, 0.25, 1.2), cloth, arm, "Root")
    primitive("sphere", "Head", (0, 0, 1.52), (0.22, 0.20, 0.24), skin, arm, "Head")
    primitive("cone", "Hood", (0, 0.01, 1.65), (0.29, 0.13, 0.42), trim, arm, "Head")
    primitive("cylinder", "Belt", (0, 0, 0.88), (0.31, 0.09), gold, arm, "Root")
    for side, bone_name in ((0.32, "Arm.L"), (-0.32, "Arm.R")):
        arm_obj = primitive("cylinder", "Sleeve", (side, 0, 1.16), (0.105, 0.62), cloth, arm, bone_name)
        arm_obj.rotation_euler.y = radians(18 * (1 if side > 0 else -1))
        primitive("sphere", "Hand", (side * 1.72, 0, 0.86), (0.10, 0.09, 0.11), skin, arm, bone_name)
    for side, bone_name in ((0.15, "Leg.L"), (-0.15, "Leg.R")):
        primitive("cylinder", "Boot", (side, 0.03, 0.27), (0.115, 0.53), dark, arm, bone_name)
    if prop == "staff":
        staff = primitive("cylinder", "Staff", (-0.60, 0.06, 0.68), (0.035, 1.55), trim, arm, "Arm.R")
        staff.rotation_euler.y = radians(-8)
        primitive("sphere", "StaffGem", (-0.69, 0.06, 1.44), (0.11, 0.11, 0.11), gold, arm, "Arm.R")
    elif prop == "sword":
        primitive("cube", "Sword", (-0.62, 0.02, 0.65), (0.055, 0.055, 0.62), trim, arm, "Arm.R")
        primitive("cube", "Guard", (-0.62, 0.02, 0.98), (0.22, 0.055, 0.04), gold, arm, "Arm.R")
    elif prop == "book":
        primitive("cube", "Book", (0.52, -0.08, 0.88), (0.24, 0.08, 0.30), trim, arm, "Arm.L")
    else:
        primitive("cylinder", "Mug", (0.54, 0.0, 0.89), (0.12, 0.22), gold, arm, "Arm.L")
    idle(arm)
    OUT.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{slug}.glb"), export_format="GLB", export_animations=True, export_materials="EXPORT")
    print(f"exported {display}: {OUT / (slug + '.glb')}")


for spec in CAST:
    character(*spec)
