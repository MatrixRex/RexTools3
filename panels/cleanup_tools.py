import bpy

class RexTools3CleanupToolsPanel(bpy.types.Panel):
    bl_label = "Cleanup Tools"
    bl_idname = "VIEW3D_PT_rextools3_cleanup_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        props = context.scene.rex_cleanup_props

        layout.operator("rextools3.clean_objects", text="Clean Objects", icon='BRUSH_DATA')

        row = layout.row(align=True)
        row.prop(props, "normals", text="Normals", toggle=True)
        row.prop(props, "quad", text="Quad", toggle=True)
        row.prop(props, "mats", text="Mats", toggle=True)
