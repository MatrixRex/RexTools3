import bpy
import bmesh
import math
from mathutils import Vector

class MESH_OT_uv_angle_loop_seam(bpy.types.Operator):
    """Angle-based loop crawling for seams. Works on ngons by following geometric direction."""
    bl_idname = "mesh.uv_angle_loop_seam"
    bl_label = "Angle Based Loop Seam"
    bl_options = {'REGISTER', 'UNDO'}

    angle_threshold: bpy.props.FloatProperty(
        name="Angle Tolerance",
        description="Allowed variance in dihedral (face) angle (in degrees)",
        default=60.0,
        min=0.0,
        max=180.0
    )
    
    straightness_threshold: bpy.props.FloatProperty(
        name="Straightness",
        description="Allowed deviation from straight line (in degrees)",
        default=60.0,
        min=0.0,
        max=180.0
    )

    max_steps: bpy.props.IntProperty(
        name="Max Steps",
        description="Maximum length of the loop",
        default=1000,
        min=1
    )

    def execute(self, context):
        from .mesh_utils import crawl
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh")
            return {'CANCELLED'}
        
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # Identify external seeds (explicitly selected by user)
        # and existing seams to avoid jumping over them in the first step
        selected_seeds = [e for e in bm.edges if e.select]
        if not selected_seeds:
            self.report({'WARNING'}, "No edge selected to start crawling")
            return {'CANCELLED'}

        # We'll build a set of edges that SHOULD be selected/marked
        edges_to_select = set(selected_seeds)
        
        # Convert thresholds to radians
        angle_tol = math.radians(self.angle_threshold)
        straight_tol = math.radians(self.straightness_threshold)
        
        stop_at_seam = context.window_manager.stop_loop_at_seam

        for start_edge in selected_seeds:
            # Initial dihedral angle
            try:
                ref_angle = start_edge.calc_face_angle()
            except ValueError:
                ref_angle = 0.0

            # Crawl both directions from the start edge
            for start_vert in start_edge.verts:
                # We pass 'selected_seeds' to crawl logic as "already visited" 
                # to prevent immediate backtracking or jumping within the seed selection.
                # However, the crawl core needs to know which edges it just added.
                crawl(start_edge, start_vert, ref_angle, edges_to_select, angle_tol, straight_tol, stop_at_seam, self.max_steps)

        # Apply results
        # NOTE: When the redo panel updates, Blender resets the mesh to the state 
        # BEFORE the first execute. So we just need to set our calculated set.
        for e in edges_to_select:
            e.select = True
            e.seam = True

        bmesh.update_edit_mesh(obj.data)

        # Check if live unwrap is toggled on
        if context.scene.tool_settings.use_edge_path_live_unwrap:
            selected_edge_indices = [e.index for e in edges_to_select]
            original_select_mode = context.tool_settings.mesh_select_mode[:]
            
            # Select all faces so unwrap uses every island
            bpy.ops.mesh.select_all(action='SELECT')
            
            try:
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
            except Exception as e:
                self.report({'WARNING'}, f"Unwrap failed: {e}")
            
            # Deselect all to clear face selection
            bpy.ops.mesh.select_all(action='DESELECT')
            
            # Re-select the crawled edges using a fresh bmesh so we don't overwrite UVs
            bm_fresh = bmesh.from_edit_mesh(obj.data)
            bm_fresh.edges.ensure_lookup_table()
            for idx in selected_edge_indices:
                if idx < len(bm_fresh.edges):
                    bm_fresh.edges[idx].select = True
            bmesh.update_edit_mesh(obj.data)
            
            # Restore selection mode
            context.tool_settings.mesh_select_mode = original_select_mode

        return {'FINISHED'}

