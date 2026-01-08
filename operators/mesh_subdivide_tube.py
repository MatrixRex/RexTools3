import bpy

class MESH_OT_subdivide_tube(bpy.types.Operator):
    """Subdivide a tube by selecting rings/loops and applying LoopTools Circle."""
    bl_idname = "mesh.subdivide_tube"
    bl_label = "Subdivide Tube"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                context.mode == 'EDIT_MESH')

    def execute(self, context):
        # 1. Ring select
        try:
            bpy.ops.mesh.loop_multi_select(ring=True)
        except Exception as e:
            self.report({'ERROR'}, f"Ring select failed: {str(e)}")
            return {'CANCELLED'}

        # 2. Loop select (converts/adds loops based on the rings)
        try:
            bpy.ops.mesh.loop_multi_select(ring=False)
        except Exception as e:
            self.report({'ERROR'}, f"Loop select failed: {str(e)}")
            return {'CANCELLED'}

        # 3. Subdivide edge ring
        try:
            bpy.ops.mesh.subdivide_edgering(number_cuts=1, interpolation='LINEAR')
        except Exception as e:
            self.report({'ERROR'}, f"Subdivide edge ring failed: {str(e)}")
            return {'CANCELLED'}

        # 4. Check for LoopTools and apply Circle
        if not hasattr(bpy.ops.mesh, "looptools_circle"):
            self.report({'ERROR'}, "LoopTools addon needs to be installed and enabled for this to work")
            return {'CANCELLED'}

        try:
            bpy.ops.mesh.looptools_circle(
                custom_radius=False, 
                fit='best', 
                flatten=True, 
                influence=100, 
                lock_x=False, 
                lock_y=False, 
                lock_z=False, 
                radius=1, 
                angle=0, 
                regular=True
            )
        except Exception as e:
            self.report({'ERROR'}, f"LoopTools Circle failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}
