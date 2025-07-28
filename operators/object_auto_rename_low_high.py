import bpy

class MESH_OT_auto_rename_high_low(bpy.types.Operator):
    bl_idname = "mesh.auto_rename_high_low"
    bl_label = "Auto Rename High/Low"
    bl_description = "Rename selected meshes based on vertex count"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        props = context.scene.highlow_renamer_props

        if len(selected_objects) != 2:
            self.report({'ERROR'}, "Need two meshes only")
            return {'CANCELLED'}

        obj1, obj2 = selected_objects
        depsgraph = context.evaluated_depsgraph_get()
        obj1_eval = obj1.evaluated_get(depsgraph)
        obj2_eval = obj2.evaluated_get(depsgraph)

        vertex_count1 = len(obj1_eval.data.vertices)
        vertex_count2 = len(obj2_eval.data.vertices)

        if vertex_count1 > vertex_count2:
            high_poly_obj, low_poly_obj = obj1, obj2
            high_count, low_count = vertex_count1, vertex_count2
        else:
            high_poly_obj, low_poly_obj = obj2, obj1
            high_count, low_count = vertex_count2, vertex_count1

        high_poly_obj.name = props.obj_name + props.high_prefix
        low_poly_obj.name = props.obj_name + props.low_prefix

        self.report({'INFO'}, f"Renamed: {high_poly_obj.name} ({high_count} verts), {low_poly_obj.name} ({low_count} verts)")
        return {'FINISHED'}
