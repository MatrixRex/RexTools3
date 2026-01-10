import bpy
from ..core import notify

class REXTOOLS3_OT_debug_toast(bpy.types.Operator):
    bl_idname = "rextools3.debug_toast"
    bl_label = "Debug Toast"
    bl_description = "Show a debug notification toast"
    bl_options = {'REGISTER'}

    type: bpy.props.EnumProperty(
        items=[
            ('INFO', "Info", ""),
            ('SUCCESS', "Success", ""),
            ('WARNING', "Warning", ""),
            ('ERROR', "Error", ""),
        ],
        default='INFO'
    )

    def execute(self, context):
        msg = f"This is a debug {self.type.lower()} notification."
        
        if self.type == 'SUCCESS':
            notify.success(msg)
        elif self.type == 'WARNING':
            notify.warning(msg)
        elif self.type == 'ERROR':
            notify.error(msg)
        else:
            notify.info(msg)
            
        return {'FINISHED'}
