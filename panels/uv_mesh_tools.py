import bpy

class REXTools3MeshUVPanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_idname = "VIEW3D_PT_rextools3_uv_mesh_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    
    @classmethod
    def poll(cls, context):
        # only show this entire panel in Edit Mesh mode
        return context.mode == 'EDIT_MESH'
    
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        layout.separator()
        layout.operator("rextools3.uv_seam_area_by_angle_modal", text="Area Seam by angle")
        