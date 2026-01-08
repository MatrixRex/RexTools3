import bpy


class RexTools3ObjectToolsPanel(bpy.types.Panel):
    bl_label = "Object Tools"
    bl_idname = "VIEW3D_PT_rextools3_object_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        # Only show in Object Mode
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator("mesh.rextools3_smart_join", text="Smart Join (UV Check)")
