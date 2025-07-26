import bpy, bmesh

class REXTOOLS3_OT_uvAreaSeam(bpy.types.Operator):
    bl_idname = "rextools3.uv_area_seam"
    bl_label = "UV Area Seam"
    bl_description = "Toggle seam on the boundary loop of the current face region"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        
        obj = context.object
        # store original seeds
        bm = bmesh.from_edit_mesh(obj.data) 
        self.seed_indices = [f.index for f in bm.faces if f.select]
        
        # **VALIDATION**: require at least one face selected
        
        
        # 1) Clear Inner: wipe all seams, then region→loop, then mark loop
        if wm.clear_inner_uv_area_seam:
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)
            
        elif wm.reseam_uv_area_seam:
            # 1) mark/unmark seams on selected edges
            bpy.ops.mesh.region_to_loop()
            obj = context.object
            me  = obj.data
            bm  = bmesh.from_edit_mesh(me)
            for e in bm.edges:
                if e.select:
                    e.seam = not e.seam
            bmesh.update_edit_mesh(me)

            # 2) only do an explicit unwrap if Live-Unwrap is enabled
            if context.scene.tool_settings.use_edge_path_live_unwrap:
                # select all faces so unwrap uses every island
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.unwrap(
                    method='MINIMUM_STRETCH',
                    fill_holes=True,
                    correct_aspect=True,
                    use_subsurf_data=False,
                    margin=0,
                    no_flip=False,
                    iterations=10,
                    use_weights=False,
                    weight_group="uv_importance",
                    weight_factor=1
                )
                bpy.ops.mesh.select_all(action='DESELECT')


            
         # 3) Normal: region→loop, then mark seam on loop
        else:
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)

        # return to face-select mode
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        return {'FINISHED'}
