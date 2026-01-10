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
        
        # Section 1: UV Seams
        box = layout.box()
        box.label(text="Seams", icon='STRANDS')
        col = box.column(align=True)
        col.operator("rextools3.uv_from_sharp", text="Seam From Sharp", icon='MOD_EDGESPLIT')
