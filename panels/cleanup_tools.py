import bpy
from ..ui import utils

class RexTools3CleanupToolsPanel(bpy.types.Panel):
    bl_label = "Cleanup Tools"
    bl_idname = "VIEW3D_PT_rextools3_cleanup_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name

    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_cleanup_tools:
                return False
        except Exception:
            pass
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

        layout.separator(factor=1.5)

        scanner = context.scene.rex_missing_texture_scanner
        col = utils.draw_section(layout, "Missing Textures", icon='IMAGE_DATA')
        
        # Scan Button
        col.operator("rextools3.scan_missing_textures", text="Scan Missing Textures", icon='VIEWZOOM')

        if scanner.has_scanned:
            col.separator()
            if not scanner.items:
                row = col.row()
                row.label(text="No missing textures found", icon='CHECKMARK')
            else:
                utils.draw_call_to_action(col, "rextools3.clean_missing_textures", "Clean All Missing", icon='TRASH', type='PRIMARY')
                col.separator()

                # List each missing image
                for item in scanner.items:
                    card = col.box()
                    
                    row = card.row(align=True)
                    row.label(text=item.image_name, icon='IMAGE_BACKGROUND')
                    
                    reassign_op = row.operator("rextools3.reassign_missing_texture", text="", icon='FILE_FOLDER')
                    reassign_op.image_name = item.image_name
                    
                    if item.materials:
                        mat_box = card.box()
                        for mat_name in item.materials.split(", "):
                            mat_box.label(text=mat_name, icon='MATERIAL')
                    else:
                        card.label(text="Not referenced in materials", icon='ERROR')
