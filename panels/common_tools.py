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
        
        layout.separator()
        
        common = context.scene.rex_common_settings
        box = layout.box()
        box.operator("rextools3.clean_modifiers", text="Clean Modifiers")
        row = box.row(align=True)
        row.prop(common, "clean_modifiers_all", text="All", toggle=True)
        row.prop(common, "clean_modifiers_hidden", text="Hidden", toggle=True)
        
        