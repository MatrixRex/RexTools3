import bpy
import bmesh
import math

class MESH_OT_angle_loop_select(bpy.types.Operator):
    """Select edges based on geometric direction and dihedral angle."""
    bl_idname = "mesh.angle_loop_select"
    bl_label = "Angle Loop Select"
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

        selected_seeds = [e for e in bm.edges if e.select]
        if not selected_seeds:
            self.report({'WARNING'}, "No edge selected to start crawling")
            return {'CANCELLED'}

        edges_to_select = set(selected_seeds)
        
        angle_tol = math.radians(self.angle_threshold)
        straight_tol = math.radians(self.straightness_threshold)
        
        for start_edge in selected_seeds:
            try:
                ref_angle = start_edge.calc_face_angle()
            except ValueError:
                ref_angle = 0.0

            for start_vert in start_edge.verts:
                crawl(start_edge, start_vert, ref_angle, edges_to_select, angle_tol, straight_tol, False, self.max_steps)

        for e in edges_to_select:
            e.select = True

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}
