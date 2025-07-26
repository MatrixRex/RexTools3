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
