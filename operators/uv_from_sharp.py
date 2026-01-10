import bpy
import bmesh
from bpy.types import Operator


class REXTOOLS3_OT_uv_from_sharp(Operator):
    """Mark sharp edges as UV seams and unwrap for all selected objects"""
    bl_idname = "rextools3.uv_from_sharp"
    bl_label = "UV from Sharp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        # Filter for visible, selectable meshes
        selected_meshes = [o for o in context.selected_objects 
                           if o.type == 'MESH' and not o.hide_viewport]
        
        if not selected_meshes:
            self.report({'WARNING'}, "No visible mesh objects selected")
            return {'CANCELLED'}

        original_active = context.view_layer.objects.active
        original_mode = context.mode
        
        # We'll use Multi-Object Edit Mode if possible
        # First, ensure we're in Object mode to reset the selection/active state cleanly
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Ensure all target meshes are selected and one is active
        for obj in selected_meshes:
            obj.select_set(True)
        context.view_layer.objects.active = selected_meshes[0]

        # Enter Edit Mode (this will put all selected objects into Edit Mode)
        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except Exception as e:
            self.report({'ERROR'}, f"Could not enter Edit Mode: {e}")
            return {'CANCELLED'}
        
        total_sharp_edges = 0
        objects_processed = 0

        for obj in selected_meshes:
            # Access bmesh in Edit mode
            try:
                bm = bmesh.from_edit_mesh(obj.data)
            except:
                continue
                
            bm.edges.ensure_lookup_table()

            sharp_count = 0
            for edge in bm.edges:
                if not edge.smooth:
                    if not edge.seam:
                        edge.seam = True
                        sharp_count += 1
            
            if sharp_count > 0:
                bmesh.update_edit_mesh(obj.data)
                total_sharp_edges += sharp_count
                
            objects_processed += 1

        # Select all faces for all objects in edit mode to unwrap everything at once
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.uv.unwrap(method='CONFORMAL')
        except Exception as e:
            self.report({'WARNING'}, f"Unwrap failed: {e}")

        # Restore original state
        if original_active and original_active.name in context.view_layer.objects:
            context.view_layer.objects.active = original_active
            try:
                if original_active.mode != original_mode:
                    bpy.ops.object.mode_set(mode=original_mode)
            except:
                bpy.ops.object.mode_set(mode='OBJECT')
        else:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Show Overlay Message
        from ..core import notify
        
        if objects_processed > 1:
            msg = f"Processed {objects_processed} objects. Marked {total_sharp_edges} seams."
        else:
            msg = f"Marked {total_sharp_edges} sharp edges as seams and unwrapped."
            if total_sharp_edges == 0:
                msg = "No new seams added (UVs updated)."

        notify.info(msg)

        return {'FINISHED'}


class REXTOOLS3_OT_uv_clear_seams(Operator):
    """Clear all UV seams from all selected mesh objects"""
    bl_idname = "rextools3.uv_clear_seams"
    bl_label = "Clear All Seams"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        selected_meshes = [o for o in context.selected_objects 
                           if o.type == 'MESH' and not o.hide_viewport]
        
        if not selected_meshes:
            return {'CANCELLED'}

        original_active = context.view_layer.objects.active
        original_mode = context.mode
        
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj in selected_meshes:
            obj.select_set(True)
        context.view_layer.objects.active = selected_meshes[0]

        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except:
            return {'CANCELLED'}
        
        total_cleared = 0
        objects_processed = 0

        for obj in selected_meshes:
            try:
                bm = bmesh.from_edit_mesh(obj.data)
            except:
                continue
                
            bm.edges.ensure_lookup_table()

            cleared_count = 0
            for edge in bm.edges:
                if edge.seam:
                    edge.seam = False
                    cleared_count += 1
            
            if cleared_count > 0:
                bmesh.update_edit_mesh(obj.data)
                total_cleared += cleared_count
                
            objects_processed += 1

        # Restore original state
        if original_active and original_active.name in context.view_layer.objects:
            context.view_layer.objects.active = original_active
            try:
                if original_active.mode != original_mode:
                    bpy.ops.object.mode_set(mode=original_mode)
            except:
                bpy.ops.object.mode_set(mode='OBJECT')
        else:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Show Overlay Message
        from ..core import notify
        
        if objects_processed > 1:
            msg = f"Cleared seams on {objects_processed} objects ({total_cleared} total)."
        else:
            msg = f"Cleared {total_cleared} seams."
            
        notify.info(msg)

        return {'FINISHED'}
