import bpy


class RexTools3CommonToolsPanel(bpy.types.Panel):
    bl_label = "Common Tools"
    bl_idname = "VIEW3D_PT_rextools3_common_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    
    
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        layout.operator("rextools3.open_folder", text="Open Folder")
        layout.operator("outliner.orphans_purge", text="Purge Orphans")
        layout.operator("rextools3.replace_materials", text="Replace Mats", icon='SHADING_TEXTURE')
        
        layout.separator()
        
        # Debugging Notifications
        box = layout.box()
        box.label(text="Debug Notifications:", icon='INFO')
        grid = box.grid_flow(columns=2, align=True)
        grid.operator("rextools3.debug_toast", text="Info").type = 'INFO'
        grid.operator("rextools3.debug_toast", text="Success").type = 'SUCCESS'
        grid.operator("rextools3.debug_toast", text="Warning").type = 'WARNING'
        grid.operator("rextools3.debug_toast", text="Error").type = 'ERROR'

        
        
