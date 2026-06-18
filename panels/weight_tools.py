import bpy

class REXTOOLS3_PT_weight_tools(bpy.types.Panel):
    bl_label = "Weight Tools"
    bl_idname = "VIEW3D_PT_rextools3_weight_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_weight_tools:
                return False
        except Exception:
            pass
        # Only visible in Weight Paint mode
        return context.mode == 'PAINT_WEIGHT'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.weight_tools_props
        
        addon_name = __package__.partition('.')[0]
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        show_init = not prefs or prefs.enable_tool_weight_init_weight
        show_xray = not prefs or prefs.enable_tool_weight_xray_brush

        if show_init:
            layout.operator("rextools3.init_weight_paint", icon='WPAINT_HLT')
        
        if show_xray:
            if show_init:
                layout.separator()
            layout.prop(props, "xray_brush", toggle=True, icon='XRAY')

