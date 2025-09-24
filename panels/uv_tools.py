import bpy

class REXTools3UVPanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_idname = "VIEW3D_PT_rextools3_uv_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager 
        tool = context.scene.tool_settings
        
        box = layout.box()
        row = box.row(align=True)
        row.operator("rextools3.uv_from_sharp", text="From Sharp", icon='MOD_EDGESPLIT')
        row.operator("rextools3.uv_clear_seams", text="Clear Seams", icon='X')