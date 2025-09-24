import bpy
import bmesh
from bpy.types import Operator


class REXTOOLS3_OT_uv_from_sharp(Operator):
    """Mark sharp edges as UV seams"""
    bl_idname = "rextools3.uv_from_sharp"
    bl_label = "UV from Sharp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data is not None)

    def execute(self, context):
        obj = context.object

        # Store the original mode
        original_mode = obj.mode

        # Ensure we're in Edit mode
        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Get bmesh representation
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        sharp_edges_count = 0

        for edge in bm.edges:
            if not edge.smooth:
                if not edge.seam:
                    edge.seam = True
                    sharp_edges_count += 1

        if obj.mode == 'EDIT':
            bmesh.update_edit_mesh(obj.data)
        else:
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
        # Run unwrap in Edit mode so the new seams are applied to UVs
        unwrap_run = False
        if obj.mode == 'EDIT' and sharp_edges_count > 0:
            try:
                bpy.ops.uv.unwrap(method='CONFORMAL')
                unwrap_run = True
            except Exception as e:
                self.report({'WARNING'}, f"Unwrap failed: {e}")

        # Restore original mode
        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode=original_mode)

        if sharp_edges_count > 0:
            msg = f"Marked {sharp_edges_count} sharp edges as seams"
            if unwrap_run:
                msg += " and unwrapped (CONFORMAL)"
            self.report({'INFO'}, msg)
        else:
            self.report({'INFO'}, "No new seams added (all sharp edges were already seams)")

        return {'FINISHED'}


class REXTOOLS3_OT_uv_clear_seams(Operator):
    """Clear all UV seams from the mesh"""
    bl_idname = "rextools3.uv_clear_seams"
    bl_label = "Clear All Seams"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data is not None)

    def execute(self, context):
        obj = context.object
        original_mode = obj.mode

        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        bm.edges.ensure_lookup_table()

        cleared_count = 0
        for edge in bm.edges:
            if edge.seam:
                edge.seam = False
                cleared_count += 1

        if obj.mode == 'EDIT':
            bmesh.update_edit_mesh(obj.data)
        else:
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()

        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, f"Cleared {cleared_count} seams")
        return {'FINISHED'}
