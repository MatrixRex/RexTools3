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
        tool = context.scene.tool_settings
        live_unwrap = tool.use_edge_path_live_unwrap
        
        layout.separator()
        layout.operator("rextools3.uv_area_seam", text="Area Seam")
        layout.prop(wm, "clear_inner_uv_area_seam", text="Clear Inner")
        layout.prop(wm, "reseam_uv_area_seam",      text="Reseam")
        layout.operator("rextools3.uv_seam_area_by_angle_modal", text="Area Seam by angle")
        row = layout.row()
        row.operator(
            "rextools3.toggle_live_unwrap",
            text="Live Unwrap",
            depress=live_unwrap
        )

        layout.separator()
        
        