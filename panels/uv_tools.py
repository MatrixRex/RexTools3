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
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_uv_tools:
                return False
        except Exception:
            pass
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        
        # Section 1: UV Seams
        box = layout.box()
        box.label(text="Seams", icon='STRANDS')
        col = box.column(align=True)
        col.operator("rextools3.uv_from_sharp", text="Seam From Sharp", icon='MOD_EDGESPLIT')
