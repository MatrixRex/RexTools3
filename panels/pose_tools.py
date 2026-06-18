import bpy

class RexTools3PoseToolsPanel(bpy.types.Panel):
    bl_label = "Pose Tools"
    bl_idname = "VIEW3D_PT_rextools3_pose_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_pose_tools:
                return False
        except Exception:
            pass
        return context.mode == 'POSE'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.pose_tools_props
        
        addon_name = __package__.partition('.')[0]
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        col = layout.column(align=True)
        col.prop(props, "source_armature", text="Source")
        
        layout.separator()
        
        col = layout.column()
        if not prefs or prefs.enable_tool_pose_init_weight:
            col.operator("rextools3.init_weight_paint", text="Init Weight Paint", icon='WPAINT_HLT')
        if not prefs or prefs.enable_tool_setup_pose_copier:
            col.operator("rextools3.setup_pose_copier", text="Setup Pose Copier", icon='POSE_HLT')
        if not prefs or prefs.enable_tool_flipped_anim:
            col.operator("rextools3.flipped_anim", text="Flipped Anim", icon='DUPLICATE')
