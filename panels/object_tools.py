import bpy


class RexTools3ObjectToolsPanel(bpy.types.Panel):
    bl_label = "Object Tools"
    bl_idname = "VIEW3D_PT_rextools3_object_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        # Only show in Object Mode
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        layout = self.layout
        common = context.scene.rex_common_settings
        
        box = layout.box()
        box.label(text="Join Tools", icon='AUTOMERGE_ON')
        col = box.column(align=True)
        col.prop(common, "smart_join_apply_modifiers", text="Apply Modifiers", icon='MODIFIER')
        col.operator("object.rextools3_smart_join", text="Smart Join (UV Check)")
