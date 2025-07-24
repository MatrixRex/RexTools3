
import bpy
from bpy.props import IntProperty, FloatProperty


def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)
    wm.select_similar_threshold = FloatProperty(
        name="Threshold",
        description="Face-normal select similarity threshold",
        default=0.0,
        min=0.0,
        max=1.0
    )

def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.modal_x
    del wm.modal_y
    del wm.select_similar_threshold
