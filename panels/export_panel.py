import bpy
from bpy.types import Panel

class REXTOOLS3_PT_ExportManager(Panel):
    bl_label = "Export Manager"
    bl_idname = "REXTOOLS3_PT_export_manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.rex_export_settings
        
        box = layout.box()
        box.label(text="Global Settings", icon='WORLD')
        
        row = box.row(align=True)
        row.prop(settings, "export_path", text="")
        # The subtype='DIR_PATH' already adds a folder icon, 
        # but the user asked for a button next to it. 
        # Blender's default prop with DIR_PATH is quite standard.
        
        col = layout.column(align=True)
        col.prop(settings, "export_mode")
        col.prop(settings, "export_limit")
        col.prop(settings, "export_format")
        col.prop(settings, "export_preset")
        
        layout.separator()
        
        # Preview list
        from ..operators.export_operators import get_export_groups
        groups = get_export_groups(context, settings)
        
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_preview", 
                 icon='TRIA_DOWN' if settings.show_preview else 'TRIA_RIGHT', 
                 text=f"Export Preview ({len(groups)})",
                 emboss=False)
        
        if settings.show_preview:
            if groups:
                col = box.column(align=True)
                for name in sorted(groups.keys()):
                    item_row = col.row()
                    item_row.label(text=name, icon='OBJECT_DATA')
            else:
                box.label(text="No items to export", icon='ERROR')

        # Custom Locations Overrides
        layout.separator()
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_custom_locations",
                 icon='TRIA_DOWN' if settings.show_custom_locations else 'TRIA_RIGHT',
                 text="Custom Locations Overrides",
                 emboss=False)
        
        if settings.show_custom_locations:
            # Simplified logic for adding overrides
            row = box.row(align=True)
            mode = settings.export_mode
            sel_count = len(context.selected_objects)

            if sel_count > 0:
                if mode in {'OBJECTS', 'PARENTS'} and sel_count == 1:
                    op = row.operator("rextools3.browse_export_path", text="Add Object Override", icon='ADD')
                    op.target = 'OBJECT'
                    op.target_name = context.active_object.name
                
                elif mode == 'COLLECTIONS':
                    op = row.operator("rextools3.browse_export_path", text="Add Collection Override", icon='ADD')
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
                col = box.column(align=True)
                for type, item in custom_items:
                    row = col.row(align=True)
                    row.label(text=item.name, icon='OBJECT_DATA' if type == 'OBJECT' else 'OUTLINER_COLLECTION')
                    op = row.operator("rextools3.select_by_name", text="", icon='RESTRICT_SELECT_OFF')
                    op.name = item.name
                    op.type = type
                    row.prop(item, "export_location", text="")
                    
                    # Add a clear button
                    remove_op = row.operator("rextools3.clear_export_path", text="", icon='X')
                    remove_op.name = item.name
                    remove_op.type = type
            else:
                box.label(text="No overrides found", icon='INFO')

        layout.separator()
        layout.operator("rextools3.export", text="Batch Export", icon='EXPORT')

        if settings.last_export_path:
            layout.separator()
            layout.operator("rextools3.open_export_folder", text="Open Export Folder", icon='FILE_FOLDER')

class REXTOOLS3_PT_CollectionExportPath(Panel):
    bl_label = "RexTools Export Settings"
    bl_idname = "REXTOOLS3_PT_collection_export_path"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"
    
    def draw(self, context):
        layout = self.layout
        coll = context.collection
        if coll:
            layout.prop(coll, "export_location", text="Location")

class REXTOOLS3_PT_ObjectExportPath(Panel):
    bl_label = "RexTools Export Settings"
    bl_idname = "REXTOOLS3_PT_object_export_path"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj and obj.type == 'MESH':
            layout.prop(obj, "export_location", text="Location")
