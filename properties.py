
import bpy
from bpy.props import IntProperty

def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)

def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.modal_x
    del wm.modal_y
