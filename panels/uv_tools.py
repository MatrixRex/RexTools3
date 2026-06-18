import bpy

class REXTools3UVPanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_idname = "VIEW3D_PT_rextools3_uv_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_uv_tools:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        addon_name = __package__.partition('.')[0]
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if not prefs or prefs.enable_tool_uv_seam_from_sharp:
            # Section 1: UV Seams
            box = layout.box()
            box.label(text="Seams", icon='STRANDS')
            col = box.column(align=True)
            col.operator("rextools3.uv_from_sharp", text="Seam From Sharp", icon='MOD_EDGESPLIT')
