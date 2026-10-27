import bpy
import math

# ============================================================
# Silverreed PointCam - final model generator
# Units are modeled in millimetres.
# ============================================================

# ---------- Reset scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001

# ---------- Main body ----------
W = 30.0
D = 11.6
H = 6.7

# ---------- U-shaped notches ----------
SLOT_W = 1.6
SLOT_D = 5.0
SLOT_H = 6.2
SLOT_XS = [-9.75, -3.25, 3.25, 9.75]

# ---------- Square recess ----------
RECESS_W = 5.2
RECESS_D = 5.2
RECESS_H = 5.0
RECESS_X = 0.05
RECESS_Y = 1.91

# ---------- Bottom pegs ----------
PEG_D = 1.5
PEG_H = 1.5
PEG_XS = [-13.0, -6.5, 6.5, 13.0]
PEG_Y = -0.48

# ---------- Top emboss ----------
TEXT_BODY = "6.5"
TEXT_SIZE_MM = 6.35       # approximately 18 pt
TEXT_EMBOSS_H = 0.25
TEXT_X = 0.0
TEXT_Y = 1.35

# ---------- Center mark ----------
MARK_BAR_W = 0.80
MARK_BAR_D = 1.60
MARK_EMBOSS_H = 0.25
MARK_Y = -4.55

# ---------- Chamfers ----------
OUTER_CHAMFER_W = 0.30
CUT_CHAMFER_W = 0.20

EPS = 0.02


def add_box(name, center, size):
    bpy.ops.mesh.primitive_cube_add(location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_cylinder(name, center, radius, height, vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=height,
        location=center
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def boolean_apply(target, tool, operation):
    mod = target.modifiers.new(name=f"{operation}_{tool.name}", type='BOOLEAN')
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.object = tool

    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    bpy.data.objects.remove(tool, do_unlink=True)


def bevel_all_edges(obj, width):
    """Apply the outer 0.30 mm chamfer before Boolean cuts."""
    mod = obj.modifiers.new(name="Outer_Chamfer", type='BEVEL')
    mod.width = width
    mod.segments = 1
    mod.profile = 0.5
    mod.limit_method = 'NONE'
    mod.miter_outer = 'MITER_SHARP'
    mod.miter_inner = 'MITER_SHARP'

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def bevel_cut_edges(obj, width):
    """Chamfer new 90-degree straight edges produced by Boolean cuts."""
    mod = obj.modifiers.new(name="Cut_Edge_Chamfer", type='BEVEL')
    mod.width = width
    mod.segments = 1
    mod.profile = 0.5
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(80.0)
    mod.miter_outer = 'MITER_SHARP'
    mod.miter_inner = 'MITER_SHARP'

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def create_text_mesh(text, name, size_mm, x, y, base_z, height_mm):
    bpy.ops.object.text_add(location=(x, y, base_z))
    txt = bpy.context.object
    txt.name = name
    txt.data.body = text
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'CENTER'
    txt.data.size = size_mm
    txt.data.extrude = height_mm
    txt.data.bevel_depth = 0.03
    txt.data.bevel_resolution = 2
    txt.data.fill_mode = 'BOTH'

    bpy.context.view_layer.objects.active = txt
    txt.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return bpy.context.object


# ============================================================
# Main body
# Bottom Z=0 / Top Z=6.7
# ============================================================

body = add_box(
    "Silverreed_PointCam",
    (0.0, 0.0, H / 2.0),
    (W, D, H)
)

# Guarantee outer perimeter chamfer before Boolean operations.
bevel_all_edges(body, OUTER_CHAMFER_W)


# ============================================================
# Four U-shaped notches
# ============================================================

front_y = -D / 2.0
slot_r = SLOT_W / 2.0
straight_d = SLOT_D - slot_r

slot_cutter_h = SLOT_H + EPS
slot_cutter_z = (SLOT_H - EPS) / 2.0

for i, x in enumerate(SLOT_XS, start=1):
    rect_y_min = front_y - EPS
    rect_y_max = front_y + straight_d
    rect_y = (rect_y_min + rect_y_max) / 2.0
    rect_d = rect_y_max - rect_y_min

    rect = add_box(
        f"Slot_{i}_Rect",
        (x, rect_y, slot_cutter_z),
        (SLOT_W, rect_d, slot_cutter_h)
    )
    boolean_apply(body, rect, 'DIFFERENCE')

    round_y = front_y + straight_d
    rnd = add_cylinder(
        f"Slot_{i}_Round",
        (x, round_y, slot_cutter_z),
        slot_r,
        slot_cutter_h
    )
    boolean_apply(body, rnd, 'DIFFERENCE')


# ============================================================
# Square recess
# Opens from the bottom and has a flat bottom.
# ============================================================

recess_cutter_h = RECESS_H + EPS
recess_z = (RECESS_H - EPS) / 2.0

recess = add_box(
    "Square_Recess",
    (RECESS_X, RECESS_Y, recess_z),
    (RECESS_W, RECESS_D, recess_cutter_h)
)
boolean_apply(body, recess, 'DIFFERENCE')

# Chamfer the newly created sharp straight edges.
bevel_cut_edges(body, CUT_CHAMFER_W)


# ============================================================
# Four bottom pegs
# ============================================================

peg_r = PEG_D / 2.0
peg_union_h = PEG_H + EPS
peg_z = (-PEG_H + EPS) / 2.0

for i, x in enumerate(PEG_XS, start=1):
    peg = add_cylinder(
        f"Peg_{i}",
        (x, PEG_Y, peg_z),
        peg_r,
        peg_union_h
    )
    boolean_apply(body, peg, 'UNION')


# ============================================================
# Embossed "6.5"
# ============================================================

text_base_z = H - 0.03

text_obj = create_text_mesh(
    TEXT_BODY,
    "Emboss_6_5",
    TEXT_SIZE_MM,
    TEXT_X,
    TEXT_Y,
    text_base_z,
    TEXT_EMBOSS_H + 0.03
)
boolean_apply(body, text_obj, 'UNION')


# ============================================================
# Center mark: thick straight raised line, no arrow tip
# ============================================================

mark_base_z = H - 0.03

bar = add_box(
    "Center_Mark",
    (
        0.0,
        MARK_Y,
        mark_base_z + (MARK_EMBOSS_H + 0.03) / 2.0
    ),
    (
        MARK_BAR_W,
        MARK_BAR_D,
        MARK_EMBOSS_H + 0.03
    )
)
boolean_apply(body, bar, 'UNION')


# ---------- Finish ----------
bpy.context.view_layer.objects.active = body
body.select_set(True)
body.name = "Silverreed_PointCam"

print("Silverreed PointCam generated.")
print(f"Body: {W} x {D} x {H} mm")
print(f"U slots X: {SLOT_XS}")
print(f"Square recess: {RECESS_W} x {RECESS_D} x {RECESS_H} mm")
print(f"Pegs: diameter {PEG_D} mm, height {PEG_H} mm, X={PEG_XS}")
print(f"Outer chamfer: {OUTER_CHAMFER_W} mm")
print(f"Cut-edge chamfer: {CUT_CHAMFER_W} mm")
