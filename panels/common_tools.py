import bpy


class RexTools3CommonToolsPanel(bpy.types.Panel):
    bl_label = "Common Tools"
    bl_idname = "VIEW3D_PT_rextools3_common_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_common_tools:
                return False
        except Exception:
            pass
        return True
    
    def draw(self, context):
        layout = self.layout
        rex_common = context.scene.rex_common_settings
        
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if not prefs or prefs.enable_tool_open_folder:
            layout.operator("rextools3.open_folder", text="Open Folder")
        if not prefs or prefs.enable_tool_extract_textures:
            layout.operator("rextools3.extract_textures", text="Extract Textures", icon='PACKAGE')
        if not prefs or prefs.enable_tool_purge_orphans:
            layout.operator("outliner.orphans_purge", text="Purge Orphans")
        if not prefs or prefs.enable_tool_replace_materials:
            layout.operator("rextools3.replace_materials", text="Replace Mats", icon='SHADING_TEXTURE')
        
        if rex_common.show_debug_notifications:
            layout.separator()
            
            # Debugging Notifications
            box = layout.box()
            box.label(text="Debug Notifications:", icon='INFO')
            grid = box.grid_flow(columns=2, align=True)
            grid.operator("rextools3.debug_toast", text="Info").type = 'INFO'
            grid.operator("rextools3.debug_toast", text="Success").type = 'SUCCESS'
            grid.operator("rextools3.debug_toast", text="Warning").type = 'WARNING'
            grid.operator("rextools3.debug_toast", text="Error").type = 'ERROR'

        # Small toggle for showing debug tools if needed
        row = layout.row()
        row.alignment = 'RIGHT'
        row.prop(rex_common, "show_debug_notifications", text="", icon='SETTINGS', emboss=False)

        
        
