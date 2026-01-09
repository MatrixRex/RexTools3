import bpy
from ..ui import utils

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
        
        main_col = utils.draw_section(layout, "Batch Export Settings", icon='SETTINGS')
        main_col.use_property_split = True
        main_col.use_property_decorate = False
        
        main_col.prop(settings, "export_path", text="Path")
        main_col.prop(settings, "export_mode", text="Mode")
        main_col.prop(settings, "export_limit", text="Limit")
        main_col.prop(settings, "export_format", text="Format")
        main_col.prop(settings, "export_preset", text="Preset")

        layout.separator()

        from ..operators.export_operators import get_export_groups
        groups = get_export_groups(context, settings)
        
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_preview", 
                 icon='TRIA_DOWN' if settings.show_preview else 'TRIA_RIGHT', 
                 text=f"Preview ({len(groups)})",
                 emboss=False)
        
        if settings.show_preview:
            if groups:
                p_col = box.column(align=True)
                for name in sorted(groups.keys()):
                    item_row = p_col.row()
                    item_row.label(text=name, icon='OBJECT_DATA')
            else:
                box.label(text="No items", icon='ERROR')

        layout.separator()
        
        # Custom Locations Overrides
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_custom_locations",
                 icon='TRIA_DOWN' if settings.show_custom_locations else 'TRIA_RIGHT',
                 text="Overrides",
                 emboss=False)
        
        if settings.show_custom_locations:
            # Simplified logic for adding overrides
            row = box.row(align=True)
            mode = settings.export_mode
            sel_count = len(context.selected_objects)

            if sel_count > 0:
                if mode in {'OBJECTS', 'PARENTS'} and sel_count == 1:
                    op = row.operator("rextools3.browse_export_path", text="", icon='ADD')
                    op.target = 'OBJECT'
                    op.target_name = context.active_object.name
                elif mode == 'COLLECTIONS':
                    op = row.operator("rextools3.browse_export_path", text="", icon='OUTLINER_COLLECTION')
                    op.target = 'COLLECTION'
                    op.target_name = context.view_layer.active_layer_collection.collection.name
            
            box.separator()

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
                p_col = box.column(align=True)
                for type, item in custom_items:
                    row = p_col.row(align=True)
                    op = row.operator("rextools3.select_by_name", text="", icon='RESTRICT_SELECT_OFF')
                    op.name = item.name
                    op.type = type
                    row.prop(item, "export_location", text=item.name)
                    # Clear button
                    clear_op = row.operator("rextools3.clear_export_path", text="", icon='X')
                    clear_op.name = item.name
                    clear_op.type = type
            else:
                box.label(text="None", icon='INFO')

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
