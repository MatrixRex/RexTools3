import bpy

class RexTools3PoseToolsPanel(bpy.types.Panel):
    bl_label = "Rig & Pose Tools"
    bl_idname = "VIEW3D_PT_rextools3_pose_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_pose_tools:
                return False
        except Exception:
            pass
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode in {'POSE', 'EDIT'})
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.pose_tools_props
        
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if context.mode == 'POSE':
            # Setup Pose Copier
            if not prefs or prefs.enable_tool_setup_pose_copier:
                box = layout.box()
                col = box.column(align=True)
                col.label(text="Setup Pose Copier", icon='POSE_HLT')
                col.prop(props, "source_armature", text="Source")
                col.separator()
                col.operator("rextools3.setup_pose_copier", text="Setup Pose Copier", icon='POSE_HLT')
                layout.separator()

            # Mute Constraints
            if not prefs or prefs.enable_tool_mute_constraints:
                box = layout.box()
                col = box.column(align=True)
                col.label(text="Mute Constraints", icon='CONSTRAINT_BONE')
                col.prop(props, "mute_constraint_target", text="Constraint")
                col.separator()
                col.operator("rextools3.mute_constraints", text="Mute Constraints", icon='HIDE_OFF')
                layout.separator()

            # Other Pose Tools
            col = layout.column()
            if not prefs or prefs.enable_tool_pose_init_weight:
                col.operator("rextools3.init_weight_paint", text="Init Weight Paint", icon='WPAINT_HLT')
            if not prefs or prefs.enable_tool_flipped_anim:
                col.operator("rextools3.flipped_anim", text="Flipped Anim", icon='DUPLICATE')
            
            layout.separator()

        # Chained Bone Rename
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Chained Bone Rename", icon='BONE_DATA')
        col.prop(props, "chained_bone_base_name", text="Base Name")
        col.separator()
        col.operator("rextools3.chained_bone_name", text="Rename Chain", icon='FILE_REFRESH')
