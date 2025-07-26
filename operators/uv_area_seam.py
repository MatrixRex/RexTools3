import bpy, bmesh

class REXTOOLS3_OT_uvAreaSeam(bpy.types.Operator):
    bl_idname = "rextools3.uv_area_seam"
    bl_label = "UV Area Seam"
    bl_description = "Toggle seam on the boundary loop of the current face region"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        
        # 1) Clear Inner: wipe all seams, then region→loop, then mark loop
        if wm.clear_inner_uv_area_seam:
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)
            
        # 2) Reseam: region→loop, then unmark any already-seamed edges
        elif wm.reseam_uv_area_seam:
            bpy.ops.mesh.region_to_loop()
            obj = context.object
            me  = obj.data
            bm  = bmesh.from_edit_mesh(me)
            for e in bm.edges:
                if e.select:
                    e.seam = not e.seam
            bmesh.update_edit_mesh(me)
            
         # 3) Normal: region→loop, then mark seam on loop
        else:
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)

        # return to face-select mode
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        return {'FINISHED'}
