import bpy
from ..ui import utils

class REXTOOLS3_PT_ExportSettingsPopup(bpy.types.Panel):
    bl_label = "Export Quick Settings"
    bl_idname = "REXTOOLS3_PT_export_settings_popup"
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    
    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 10
        
        settings = context.scene.rex_export_settings
        
        # --- ACTION ---
        col = layout.column()
        col.scale_y = 1.4
        col.operator("rextools3.export", text="Batch Export", icon='EXPORT')

        layout.separator()

        # --- QUICK CONFIG ---
        col = utils.draw_section(layout, "Config", icon='SETTINGS')
        col.use_property_split = True
        col.use_property_decorate = False
        
        # Path selection (removed redundant button)
        col.prop(settings, "export_path", text="Path")
        
        col.prop(settings, "export_mode", text="Mode")
        col.separator()
        col.prop(settings, "export_limit", text="Limit")
        col.prop(settings, "export_format", text="Format")
        col.prop(settings, "export_preset", text="Preset")

        layout.separator()

        # --- PREVIEW ---
        from ..operators.export_operators import get_export_groups
        groups = get_export_groups(context, settings)
        
        tbox = layout.box()
        trow = tbox.row()
        trow.prop(settings, "show_preview", 
                 icon='TRIA_DOWN' if settings.show_preview else 'TRIA_RIGHT', 
                 text=f"Targets ({len(groups)})",
                 emboss=False)
        
        if settings.show_preview:
            if groups:
                p_col = tbox.column(align=True)
                for name in sorted(groups.keys()):
                    p_col.label(text=name, icon='OBJECT_DATA')
            else:
                tbox.label(text="None", icon='ERROR')

        layout.separator()
        
        # --- OVERRIDES ---
        obox = layout.box()
        orow = obox.row()
        orow.prop(settings, "show_custom_locations",
                 icon='TRIA_DOWN' if settings.show_custom_locations else 'TRIA_RIGHT',
                 text="Overrides",
                 emboss=False)
        
        if settings.show_custom_locations:
            mode = settings.export_mode
            sel_count = len(context.selected_objects)

            if sel_count > 0:
                row = obox.row(align=True)
                if mode in {'OBJECTS', 'PARENTS'} and context.active_object:
                    op = row.operator("rextools3.browse_export_path", text="", icon='ADD')
                    op.target = 'OBJECT'
                    op.target_name = context.active_object.name
                elif mode == 'COLLECTIONS' and context.view_layer.active_layer_collection:
                    op = row.operator("rextools3.browse_export_path", text="", icon='OUTLINER_COLLECTION')
                    op.target = 'COLLECTION'
                    op.target_name = context.view_layer.active_layer_collection.collection.name
            
            obox.separator()
            custom_items = []
            if mode == 'COLLECTIONS':
                for coll in bpy.data.collections:
                    if coll.export_location:
                        custom_items.append(('COLLECTION', coll))
            else:
                for obj in bpy.data.objects:
                    if obj.export_location:
                        custom_items.append(('OBJECT', obj))
            
            if custom_items:
                for type, item in custom_items:
                    row = obox.row(align=True)
                    op = row.operator("rextools3.select_by_name", text="", icon='RESTRICT_SELECT_OFF')
                    op.name = item.name
                    op.type = type
                    row.prop(item, "export_location", text=item.name)
                    clear_op = row.operator("rextools3.clear_export_path", text="", icon='X')
                    clear_op.name = item.name
                    clear_op.type = type
            else:
                obox.label(text="None", icon='INFO')



def draw_topbar_export(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("rextools3.export", text="Export", icon='EXPORT')
    row.popover(panel="REXTOOLS3_PT_export_settings_popup", text="", icon='SETTINGS')

def register():
    # Append the draw function to the top bar editor menus
    bpy.types.TOPBAR_MT_editor_menus.append(draw_topbar_export)

def unregister():
    # Remove the draw function when unregistering
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_topbar_export)
