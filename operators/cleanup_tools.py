import bpy
from bpy.types import Operator
from ..core import notify

class REXTOOLS3_OT_CleanObjects(Operator):
    """Clean up selected objects based on toggled settings"""
    bl_idname = "rextools3.clean_objects"
    bl_label = "Clean Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        props = context.scene.rex_cleanup_props
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            notify.warning("No mesh objects selected")
            return {'CANCELLED'}

        active_obj = context.active_object

        for obj in selected_objects:
            # 1. Normals
            if props.normals:
                context.view_layer.objects.active = obj
                bpy.ops.mesh.customdata_custom_splitnormals_clear()

            # 2. Quad
            if props.quad:
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                # Ensure we select everything in edit mode
                bpy.ops.mesh.select_all(action='SELECT')
                
                # Use the correct API for modern Blender with requested defaults
                try:
                    bpy.ops.mesh.tris_convert_to_quads(
                        face_threshold=1.22173, 
                        shape_threshold=1.22173, 
                        uvs=True, 
                        seam=True, 
                        sharp=True, 
                        materials=True
                    )
                except AttributeError:
                    # Fallback for older versions if necessary
                    if hasattr(bpy.ops.mesh, "tris_to_quads"):
                        bpy.ops.mesh.tris_to_quads()
                        
                bpy.ops.object.mode_set(mode='OBJECT')

            # 3. Mats
            if props.mats:
                context.view_layer.objects.active = obj
                
                # Standard Blender: Remove unused material slots
                try:
                    bpy.ops.object.material_slot_remove_unused()
                except Exception as e:
                    print(f"Error removing unused material slots for {obj.name}: {e}")

        # Restore active object
        if active_obj in context.view_layer.objects.values():
            context.view_layer.objects.active = active_obj

        notify.success(f"Cleaned {len(selected_objects)} objects")
        return {'FINISHED'}
