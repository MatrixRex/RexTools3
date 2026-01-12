import bpy
from ..core import notify

class REXTOOLS3_OT_CopyText(bpy.types.Operator):
    bl_idname = "rextools3.copy_text"
    bl_label = "Copy Text"
    bl_description = "Copy text to clipboard"
    bl_options = {'REGISTER', 'UNDO'}

    text: bpy.props.StringProperty()

    def execute(self, context):
        if self.text:
            context.window_manager.clipboard = self.text
            notify.success(f"Copied: {self.text}")
        return {'FINISHED'}
