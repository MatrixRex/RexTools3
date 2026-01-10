import bpy

class RexTools3CleanupToolsPanel(bpy.types.Panel):
    bl_label = "Cleanup Tools"
    bl_idname = "VIEW3D_PT_rextools3_cleanup_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'EDIT_MESH'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_cleanup_props
        common = context.scene.rex_common_settings

        # Clean Objects Box
        box = layout.box()
        box.operator("rextools3.clean_objects", text="Clean Objects", icon='BRUSH_DATA')
        row = box.row(align=True)
        row.prop(props, "normals", text="Normals", toggle=True)
        row.prop(props, "quad", text="Quad", toggle=True)
        row.prop(props, "mats", text="Mats", toggle=True)
        
        # Added: Checker Dissolve for Edit Mode
        if context.mode == 'EDIT_MESH':
            box.operator("mesh.checker_dissolve", text="Checker Dissolve", icon='MOD_DECIM')
        
        # Added Clear Seams to cleanup tools
        box.operator("rextools3.uv_clear_seams", text="Clear Seams", icon='X')

        layout.separator()

        # Clean Modifiers Box
        box = layout.box()
        box.operator("rextools3.clean_modifiers", text="Clean Modifiers", icon='MODIFIER')
        row = box.row(align=True)
        row.prop(common, "clean_modifiers_all", text="All", toggle=True)
        row.prop(common, "clean_modifiers_hidden", text="Hidden", toggle=True)
