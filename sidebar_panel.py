import bpy

class REXTools3Panel(bpy.types.Panel):
    bl_label = "RexTools3"
    bl_idname = "VIEW3D_PT_rextools3"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'      # sidebar
    bl_category = "RexTools3"  # tab name

    def draw(self, context):
        layout = self.layout
        layout.label(text="welcome")
