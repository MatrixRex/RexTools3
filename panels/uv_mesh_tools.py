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
        
        box = layout.box()
        box.label(text="Seam", icon='OPTIONS')
        
        box2 = box.box()
        
        
        box2.operator("rextools3.uv_area_seam", text="Area Seam")
        row = box2.row(align=True)
        
        
        row.operator("wm.toggle_clear_inner_seam", depress=wm.clear_inner_uv_area_seam, text="Clear Inner")
        row.operator("wm.toggle_reseam_loop", depress=wm.reseam_uv_area_seam, text="Reseam")
        
        
        box3 = box.box()
        col = box3.column(align=True)
        col.operator("mesh.uv_angle_loop_seam", text="Angle Loop Seam", icon='ORIENTATION_NORMAL')

        # Toggle button styled with depress state
        row = box3.row(align=True)
        row.operator(
            "wm.toggle_stop_at_seam",
            depress=wm.stop_loop_at_seam
        )
        
        layout.operator("rextools3.uv_seam_area_by_angle_modal", text="Area Seam by angle")
        
        box = layout.box()
        box.label(text="Unwrap", icon='OPTIONS')
        
        row = box.row()
        row.operator(
            "rextools3.toggle_live_unwrap",
            text="Live Unwrap",
            depress=live_unwrap
        )
        box.operator_context = 'EXEC_DEFAULT'
        box.operator("uv.follow_active_quads", text="Quad Follow").mode = 'LENGTH_AVERAGE'
        box.separator()
        box.operator("rextools3.mark_seams_from_islands", text="Seam From Island")
        
        # Added: mark sharp edges as seams and clear seams
        row = box.row(align=True)
        row.operator("rextools3.uv_from_sharp", text="From Sharp", icon='MOD_EDGESPLIT')
        row.operator("rextools3.uv_clear_seams", text="Clear Seams", icon='X')
        
            


