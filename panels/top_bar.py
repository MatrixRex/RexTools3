import bpy

class REXTOOLS3_PT_ExportSettingsPopup(bpy.types.Panel):
    bl_label = "Export Settings"
    bl_idname = "REXTOOLS3_PT_export_settings_popup"
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    
    def draw(self, context):
        layout = self.layout
        # Further reduced width
        layout.ui_units_x = 9
        
        settings = context.scene.rex_export_settings
        
        layout.label(text="Batch Export Settings", icon='SETTINGS')
        layout.separator()
        
        col = layout.column(align=True)
        # Use proportional column for consistent label/property ratio
        col.use_property_split = True
        col.use_property_decorate = False # Keeps it clean
        
        col.prop(settings, "export_path", text="Path")
        col.prop(settings, "export_mode", text="Mode")
        col.prop(settings, "export_limit", text="Limit")
        col.prop(settings, "export_format", text="Format")
        col.prop(settings, "export_preset", text="Preset")

def draw_topbar_export(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("rextools3.export", text="", icon='EXPORT')
    row.popover(panel="REXTOOLS3_PT_export_settings_popup", text="", icon='SETTINGS')

def register():
    # Append the draw function to the top bar editor menus
    bpy.types.TOPBAR_MT_editor_menus.append(draw_topbar_export)

def unregister():
    # Remove the draw function when unregistering
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_topbar_export)
