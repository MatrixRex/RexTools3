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
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
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

        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        # Clean Objects Box
        show_clean_box = (
            not prefs or 
            prefs.enable_tool_clean_objects or 
            (prefs.enable_tool_checker_dissolve and context.mode == 'EDIT_MESH') or 
            prefs.enable_tool_clear_seams
        )
        if show_clean_box:
            box = layout.box()
            if not prefs or prefs.enable_tool_clean_objects:
                box.operator("rextools3.clean_objects", text="Clean Objects", icon='BRUSH_DATA')
                row = box.row(align=True)
                row.prop(props, "normals", text="Normals", toggle=True)
                row.prop(props, "quad", text="Quad", toggle=True)
                row.prop(props, "mats", text="Mats", toggle=True)
            
            if context.mode == 'EDIT_MESH' and (not prefs or prefs.enable_tool_checker_dissolve):
                box.operator("mesh.checker_dissolve", text="Checker Dissolve", icon='MOD_DECIM')
            
            if not prefs or prefs.enable_tool_clear_seams:
                box.operator("rextools3.uv_clear_seams", text="Clear Seams", icon='X')

        # Clean Modifiers Box
        if not prefs or prefs.enable_tool_clean_modifiers:
            if show_clean_box:
                layout.separator()
            box = layout.box()
            box.operator("rextools3.clean_modifiers", text="Clean Modifiers", icon='MODIFIER')
            row = box.row(align=True)
            row.prop(common, "clean_modifiers_all", text="All", toggle=True)
            row.prop(common, "clean_modifiers_hidden", text="Hidden", toggle=True)

        # Missing Textures Scanner
        if not prefs or prefs.enable_tool_missing_textures:
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
