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
        default=10.0,
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
                self.crawl(start_edge, start_vert, ref_angle, edges_to_select, angle_tol, straight_tol, stop_at_seam)

        # Apply results
        # NOTE: When the redo panel updates, Blender resets the mesh to the state 
        # BEFORE the first execute. So we just need to set our calculated set.
        for e in edges_to_select:
            e.select = True
            e.seam = True

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}

    def crawl(self, start_edge, start_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam):
        curr_edge = start_edge
        curr_vert = start_vert
        
        for _ in range(self.max_steps):
            next_edge = self.find_next_edge(curr_edge, curr_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam)
            if not next_edge:
                break
            
            visited_edges.add(next_edge)
            # update curr_vert to the other end of next_edge
            curr_vert = next_edge.other_vert(curr_vert)
            curr_edge = next_edge

    def find_next_edge(self, curr_edge, curr_vert, ref_angle, visited_edges, angle_tol, straight_tol, stop_at_seam):
        # 1. Check if we should stop here because of existing seams at this vertex
        if stop_at_seam:
            for edge in curr_vert.link_edges:
                if edge == curr_edge:
                    continue
                # If there's an existing seam that isn't part of our current crawl/selection, stop.
                if edge.seam and (edge not in visited_edges):
                    return None

        # Direction of entry into curr_vert
        v_prev = curr_edge.other_vert(curr_vert).co
        v_curr = curr_vert.co
        dir_in = (v_curr - v_prev).normalized()

        best_edge = None
        best_score = -2.0 # Higher is better (dot product)

        for edge in curr_vert.link_edges:
            if edge == curr_edge:
                continue
            if edge in visited_edges:
                continue
            
            # Geometric direction
            v_next = edge.other_vert(curr_vert).co
            dir_out = (v_next - v_curr).normalized()
            
            dot = dir_in.dot(dir_out)
            # angle_between_edges is the "turn" angle. 0 is straight, PI is U-turn.
            angle_between_edges = math.acos(max(-1.0, min(1.0, dot))) 
            
            if angle_between_edges > straight_tol:
                continue
                
            # Dihedral angle check
            try:
                phi = edge.calc_face_angle()
            except ValueError:
                phi = 0.0
                
            # Check if the face angle is close to our reference
            if abs(phi - ref_angle) > angle_tol:
                continue
                
            # Score is based on straightness (best alignment)
            if dot > best_score:
                best_score = dot
                best_edge = edge
        
        return best_edge

