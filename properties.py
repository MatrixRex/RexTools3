import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, PointerProperty
from bpy.types import PropertyGroup

class HighLowRenamerProperties(PropertyGroup):
    obj_name: StringProperty(
        name="Object Name",
        description="Base name for the objects",
        default="Asset"
    )
    high_prefix: StringProperty(
        name="High Prefix",
        description="Prefix for high poly mesh",
        default="_high"
    )
    low_prefix: StringProperty(
        name="Low Prefix",
        description="Prefix for low poly mesh",
        default="_low"
    )

def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)

    bpy.types.Scene.highlow_renamer_props = PointerProperty(type=HighLowRenamerProperties)

    wm.select_similar_threshold = FloatProperty(
        name="Threshold",
        description="Face-normal select similarity threshold",
        default=0.0,
        min=0.0,
        max=1.0
    )
    wm.clear_inner_uv_area_seam = BoolProperty(
        name="Clear Inner",
        description="Clear all seams before marking the loop seam",
        default=False
    )
    wm.reseam_uv_area_seam = BoolProperty(
        name="Reseam",
        description="Deselect seams on the selected loop instead of marking",
        default=False
    )

def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.modal_x
    del wm.modal_y

    del bpy.types.Scene.highlow_renamer_props

    del wm.select_similar_threshold
    del wm.clear_inner_uv_area_seam
    del wm.reseam_uv_area_seam
