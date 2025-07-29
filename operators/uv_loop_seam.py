# operators/edge_loop_seam.py
import bpy
import bmesh

class MESH_OT_select_edge_loop_until_seam(bpy.types.Operator):
    """Select edge loop but stop at seam edges"""
    bl_idname = "mesh.select_edge_loop_until_seam"
    bl_label = "Select Edge Loop Until Seam"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                context.mode == 'EDIT_MESH')

    def execute(self, context):
        stop_at_seam = context.window_manager.stop_loop_at_seam
        self.select_edge_loop_until_seam(context, stop_at_seam)
        return {'FINISHED'}

    def select_edge_loop_until_seam(self, context, stop_at_seam):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()

        selected_edges = [e for e in bm.edges if e.select]
        if not selected_edges:
            self.report({'WARNING'}, "No edge selected")
            return

        start_edge = selected_edges[0]

        bpy.ops.mesh.select_all(action='DESELECT')
        start_edge.select = True

        def traverse(start_loop):
            current = start_loop
            for _ in range(1000):
                try:
                    n1 = current.link_loop_next
                    n2 = n1.link_loop_radial_next
                    next_loop = n2.link_loop_next

                    if next_loop.edge == start_edge or next_loop == current:
                        break

                    if stop_at_seam and (next_loop.edge.seam or n1.edge.seam):
                        break

                    next_loop.edge.select = True
                    current = next_loop
                except AttributeError:
                    break

        if start_edge.link_loops:
            traverse(start_edge.link_loops[0])
            if len(start_edge.link_loops) > 1:
                traverse(start_edge.link_loops[1])

        bmesh.update_edit_mesh(obj.data)
        for edge in bm.edges:
            if edge.select:
                edge.seam = True  # Mark selected edges as seams
                
class WM_OT_toggle_stop_at_seam(bpy.types.Operator):
    bl_idname = "wm.toggle_stop_at_seam"
    bl_label = "Stop at Seam"

    def execute(self, context):
        wm = context.window_manager
        wm.stop_loop_at_seam = not wm.stop_loop_at_seam
        return {'FINISHED'}
    
