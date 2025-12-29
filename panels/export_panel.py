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
