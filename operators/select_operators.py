import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class REXTOOLS3_OT_SelectByName(Operator):
    bl_idname = "rextools3.select_by_name"
    bl_label = "Select"
    bl_description = "Select the object by its name"
    
    name: StringProperty()
    type: StringProperty() # 'OBJECT' or 'COLLECTION'
    
    def execute(self, context):
        if self.type == 'OBJECT':
            obj = bpy.data.objects.get(self.name)
            if obj:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
        
        elif self.type == 'COLLECTION':
            coll = bpy.data.collections.get(self.name)
            if coll:
                # Optionally select all objects in collection
                bpy.ops.object.select_all(action='DESELECT')
                for o in coll.all_objects:
                    try: o.select_set(True)
                    except: pass
                if coll.all_objects:
                    context.view_layer.objects.active = coll.all_objects[0]
                    
        return {'FINISHED'}

class REXTOOLS3_OT_ClearExportPath(Operator):
    bl_idname = "rextools3.clear_export_path"
    bl_label = "Clear"
    bl_description = "Remove the custom export location override"
    
    name: StringProperty()
    type: StringProperty()
    
    def execute(self, context):
        if self.type == 'OBJECT':
            obj = bpy.data.objects.get(self.name)
            if obj:
                obj.export_location = ""
        elif self.type == 'COLLECTION':
            coll = bpy.data.collections.get(self.name)
            if coll:
                coll.export_location = ""
        return {'FINISHED'}
