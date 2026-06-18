import bpy

class REXTools3EditToolsPanel(bpy.types.Panel):
    bl_label = "Edit Tools"
    bl_idname = "VIEW3D_PT_rextools3_edit_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_edit_tools:
                return False
        except Exception:
            pass
        return context.mode == 'EDIT_MESH'
    
    def draw(self, context):
        layout = self.layout
        
        addon_name = __package__.partition('.')[0]
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if not prefs or prefs.enable_tool_angle_loop_select:
            box = layout.box()
            box.label(text="Selection", icon='RESTRICT_SELECT_OFF')
            box.operator("mesh.angle_loop_select", text="Angle Loop Select", icon='ORIENTATION_NORMAL')
        
        if not prefs or prefs.enable_tool_subdivide_tube:
            box = layout.box()
            box.label(text="Tube Tools", icon='MOD_SCREW')
            box.operator("mesh.subdivide_tube", text="Subdivide Tube", icon='MESH_CYLINDER')
