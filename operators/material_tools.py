import bpy
from bpy.types import Operator
from ..core import notify

class REXTOOLS3_OT_ReplaceMaterials(Operator):
    """Replace materials of all selected objects with the materials from the active object"""
    bl_idname = "rextools3.replace_materials"
    bl_label = "Replace Materials"
    bl_description = "Assign active object's material slots to all selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                len(context.selected_objects) > 1)

    def execute(self, context):
        active_obj = context.active_object
        target_materials = active_obj.data.materials[:]
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != active_obj]
        
        if not selected_meshes:
            notify.warning("No other mesh objects selected")
            return {'CANCELLED'}

        for obj in selected_meshes:
            # Clear existing slots
            obj.data.materials.clear()
            
            # Append new slots in order
            for mat in target_materials:
                obj.data.materials.append(mat)
        
        notify.success(f"Replaced materials on {len(selected_meshes)} objects")
        return {'FINISHED'}
