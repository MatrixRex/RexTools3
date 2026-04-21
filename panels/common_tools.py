import bpy


class RexTools3CommonToolsPanel(bpy.types.Panel):
    bl_label = "Common Tools"
    bl_idname = "VIEW3D_PT_rextools3_common_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    
    
    
    def draw(self, context):
        layout = self.layout
        rex_common = context.scene.rex_common_settings
        
        layout.operator("rextools3.open_folder", text="Open Folder")
        layout.operator("rextools3.extract_textures", text="Extract Textures", icon='PACKAGE')
        layout.operator("outliner.orphans_purge", text="Purge Orphans")
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

        
        
