import bpy
from bpy.types import Operator

class REXTOOLS3_OT_delete_linked_ex(Operator):
    bl_idname = "rextools3.delete_linked_ex"
    bl_label  = "Delete Linked"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.select_linked(delimit=set())
        bpy.ops.mesh.delete(type='VERT')
        return {'FINISHED'}


class REXTOOLS3_OT_checker_dissolve(Operator):
    bl_idname = "rextools3.checker_dissolve"
    bl_label  = "Checker Dissolve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.loop_multi_select(ring=True)
        bpy.ops.mesh.select_nth(nth=1)
        bpy.ops.mesh.loop_multi_select(ring=False)
        bpy.ops.mesh.dissolve_edges()
        return {'FINISHED'}


class REXTOOLS3_OT_checker_dissolve_selected(Operator):
    bl_idname = "rextools3.checker_dissolve_selected"
    bl_label  = "Checker Dissolve Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
       
        bpy.ops.mesh.select_nth(skip=1)
        bpy.ops.mesh.loop_multi_select(ring=False)
        bpy.ops.mesh.dissolve_edges()
        return {'FINISHED'}


class REXTOOLS3_OT_loop_dissolve_ex(Operator):
    bl_idname = "rextools3.loop_dissolve_ex"
    bl_label  = "Loop Dissolve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.loop_multi_select(ring=False)
        bpy.ops.mesh.dissolve_edges()
        return {'FINISHED'}

class REXTOOLS3_OT_fill_loop_inner_region(Operator):
    bl_idname = "rextools3.fill_loop_inner_region"
    bl_label = "Fill Loop Inner Region"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        loop_to_region = bpy.ops.mesh.loop_to_region()
        if 'CANCELLED' in loop_to_region:
            self.report({'WARNING'}, 'Select a complete edge loop.')
            return {'CANCELLED'}

        face_add = bpy.ops.mesh.edge_face_add()
        if 'FINISHED' not in face_add:
            fill_result = bpy.ops.mesh.fill()
            if 'FINISHED' not in fill_result:
                self.report({'WARNING'}, 'Could not create faces from selection.')
                return {'CANCELLED'}

        context.tool_settings.mesh_select_mode = (False, True, False)
        return {'FINISHED'}
