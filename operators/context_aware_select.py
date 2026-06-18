import bpy
import bmesh
from bpy.types import Operator

addon_keymaps = []

def opposite_edge_in_quad(face, edge):
    for e in face.edges:
        if not any(v in edge.verts for v in e.verts):
            return e
    return None

def traverse_face_loop(bm, start_face, start_edge):
    loop_faces = [start_face]
    current_face = start_face
    current_edge = start_edge

    # Limit to prevent infinite loop
    for _ in range(1000):
        next_faces = [f for f in current_edge.link_faces if f != current_face]
        if not next_faces:
            break
        next_face = next_faces[0]
        
        if next_face in loop_faces:
            break
            
        if len(next_face.edges) != 4:
            loop_faces.append(next_face)
            break
            
        loop_faces.append(next_face)
        opp_edge = opposite_edge_in_quad(next_face, current_edge)
        if not opp_edge:
            break
        current_face = next_face
        current_edge = opp_edge
        
    return loop_faces

def get_face_loop_from_adjacent(bm, face_a, face_b):
    shared_edges = [e for e in face_a.edges if e in face_b.edges]
    if len(shared_edges) != 1:
        return None
    shared_edge = shared_edges[0]
    
    if len(face_a.edges) != 4 or len(face_b.edges) != 4:
        return {face_a, face_b}
        
    opp_edge_a = opposite_edge_in_quad(face_a, shared_edge)
    opp_edge_b = opposite_edge_in_quad(face_b, shared_edge)
    
    loop_dir_a = traverse_face_loop(bm, face_a, opp_edge_a)
    loop_dir_b = traverse_face_loop(bm, face_b, opp_edge_b)
    
    return set(loop_dir_a + loop_dir_b)

def are_edges_parallel(edge1, edge2):
    # If they share a vertex, they are connected, so not parallel
    if any(v in edge2.verts for v in edge1.verts):
        return False
        
    # Check if they share a quad face and are opposite
    shared_faces = [f for f in edge1.link_faces if f in edge2.link_faces]
    for f in shared_faces:
        if len(f.edges) == 4:
            return True
            
    # Geometric check fallback
    v1 = (edge1.verts[1].co - edge1.verts[0].co).normalized()
    v2 = (edge2.verts[1].co - edge2.verts[0].co).normalized()
    return abs(v1.dot(v2)) > 0.707

def traverse_edge_loop(bm, start_edge):
    loop_edges = {start_edge}
    
    # Traverse in both directions from the start edge's vertices
    for start_vert in start_edge.verts:
        current_edge = start_edge
        current_vert = start_vert
        
        while True:
            next_edge = None
            edges_at_vert = list(current_vert.link_edges)
            if len(edges_at_vert) == 4:
                current_faces = set(current_edge.link_faces)
                if current_faces:
                    for e in edges_at_vert:
                        if e != current_edge:
                            if not current_faces.intersection(set(e.link_faces)):
                                next_edge = e
                                break
            
            if not next_edge or next_edge in loop_edges:
                break
                
            loop_edges.add(next_edge)
            current_vert = next_edge.other_vert(current_vert)
            current_edge = next_edge
            
    return loop_edges

class REXTOOLS3_OT_ContextAwareSelect(Operator):
    """Context-aware selection: Linked select for Vertices/Faces/Curves, Loop select for Edges, triggered on double-click"""
    bl_idname = "rextools3.context_aware_select"
    bl_label = "Context Aware Select"
    bl_description = "Double-click to select linked (vertices/faces/curves) or loops (edges)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_context_select:
                return False
        except Exception:
            pass
        return True

    # Linked Selection properties (Vertex/Face Mode)
    delimit: bpy.props.EnumProperty(
        name="Delimit",
        description="Limit selection boundaries",
        options={'ENUM_FLAG'},
        items=(
            ('NORMAL', "Normal", "Delimit by face directions"),
            ('MATERIAL', "Material", "Delimit by face material"),
            ('SEAM', "Seam", "Delimit by edge seams"),
            ('SHARP', "Sharp", "Delimit by sharp edges"),
            ('UV', "UV", "Delimit by UV coordinates"),
        ),
        default=set(),
    )

    # Loop Selection properties (Edge Mode)
    ring: bpy.props.BoolProperty(
        name="Ring",
        description="Select an edge ring instead of a loop",
        default=False,
    )

    # Hidden toggle property to track shift modifier between invoke and execute
    toggle_loop: bpy.props.BoolProperty(
        name="Toggle Loop",
        options={'HIDDEN'},
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode
            if select_mode[0] or select_mode[2]:
                # Show delimit options in Vertex or Face selection mode
                layout.prop(self, "delimit")
            elif select_mode[1]:
                # Show ring select options in Edge selection mode
                layout.prop(self, "ring")

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}

        if obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode

            if select_mode[0] or select_mode[2]:
                # Run linked selection
                bpy.ops.mesh.select_linked(delimit=self.delimit)
                return {'FINISHED'}

            elif select_mode[1]:
                # In execute (Redo adjustments), use loop_multi_select.
                # This works on the seed selection restored by Blender's undo stack,
                # converting the selection between loop/ring without needing mouse coordinates.
                bpy.ops.mesh.loop_multi_select(ring=self.ring)
                return {'FINISHED'}

        elif obj.type == 'CURVE' and context.mode == 'EDIT_CURVE':
            # Check if there is any selected control point/bezier point
            has_selection = False
            for spline in obj.data.splines:
                if any(p.select_control_point for p in spline.bezier_points) or any(p.select for p in spline.points):
                    has_selection = True
                    break

            if not has_selection:
                return {'CANCELLED'}

            # Run curve linked selection
            bpy.ops.curve.select_linked()
            return {'FINISHED'}

        return {'CANCELLED'}

    def invoke(self, context, event):
        # Pass through if any other modifier keys are held
        if event.ctrl or event.alt or event.oskey:
            return {'PASS_THROUGH'}

        # Ensure we are in Edit Mode on a mesh or curve object
        obj = context.active_object
        if not obj:
            return {'PASS_THROUGH'}

        if obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            select_mode = context.tool_settings.mesh_select_mode
            bm = bmesh.from_edit_mesh(obj.data)

            # Check if there is any selection in the active selection mode
            has_selection = False
            if select_mode[0]:
                has_selection = any(v.select for v in bm.verts)
            elif select_mode[2]:
                has_selection = any(f.select for f in bm.faces)
            elif select_mode[1]:
                has_selection = any(e.select for e in bm.edges)

            # If no elements are selected, pass through
            if not has_selection:
                return {'PASS_THROUGH'}

            # Set initial toggle state based on shift modifier
            self.toggle_loop = event.shift

            # For initial selection in Edge mode, invoke the viewport-based loop_select
            # which utilizes mouse coordinates and correctly toggles/extends selection.
            if select_mode[1]:
                ring = self.ring
                if event.shift:
                    if len(bm.select_history) >= 2:
                        hist = list(bm.select_history)
                        edge1 = hist[-1]
                        edge2 = hist[-2]
                        if isinstance(edge1, bmesh.types.BMEdge) and isinstance(edge2, bmesh.types.BMEdge):
                            if are_edges_parallel(edge1, edge2):
                                ring = True
                            else:
                                ring = False
                bpy.ops.mesh.loop_select(
                    'INVOKE_DEFAULT',
                    extend=self.toggle_loop,
                    deselect=False,
                    toggle=self.toggle_loop,
                    ring=ring
                )
                return {'FINISHED'}

            # For Face mode, if Shift is held, try to select the face loop between
            # the last two selected adjacent faces.
            if select_mode[2] and event.shift:
                if len(bm.select_history) >= 2:
                    hist = list(bm.select_history)
                    face1 = hist[-1]
                    face2 = hist[-2]
                    if isinstance(face1, bmesh.types.BMFace) and isinstance(face2, bmesh.types.BMFace):
                        face_loop = get_face_loop_from_adjacent(bm, face1, face2)
                        if face_loop:
                            for f in face_loop:
                                f.select = True
                            bm.select_flush(True)
                            bmesh.update_edit_mesh(obj.data)
                            return {'FINISHED'}
                # Fallback to select linked pick
                bpy.ops.mesh.select_linked_pick('INVOKE_DEFAULT', deselect=False, delimit=self.delimit)
                return {'FINISHED'}

            # For Vertex mode, if Shift is held, try to select the vertex loop
            # between the last two selected adjacent vertices.
            if select_mode[0] and event.shift:
                if len(bm.select_history) >= 2:
                    hist = list(bm.select_history)
                    v1 = hist[-1]
                    v2 = hist[-2]
                    if isinstance(v1, bmesh.types.BMVert) and isinstance(v2, bmesh.types.BMVert):
                        shared_edges = [e for e in v1.link_edges if e in v2.link_edges]
                        if len(shared_edges) == 1:
                            connecting_edge = shared_edges[0]
                            loop_edges = traverse_edge_loop(bm, connecting_edge)
                            if loop_edges:
                                for e in loop_edges:
                                    for v in e.verts:
                                        v.select = True
                                bm.select_flush(True)
                                bmesh.update_edit_mesh(obj.data)
                                return {'FINISHED'}
                # Fallback to select linked pick
                bpy.ops.mesh.select_linked_pick('INVOKE_DEFAULT', deselect=False, delimit=self.delimit)
                return {'FINISHED'}

            # For Vertex/Face modes (without Shift), execute directly
            return self.execute(context)

        elif obj.type == 'CURVE' and context.mode == 'EDIT_CURVE':
            # Check if there is any selected spline point
            has_selection = False
            for spline in obj.data.splines:
                if any(p.select_control_point for p in spline.bezier_points) or any(p.select for p in spline.points):
                    has_selection = True
                    break

            # If no elements are selected, pass through
            if not has_selection:
                return {'PASS_THROUGH'}

            # For Curve mode, if Shift is held, we want to retain the previous selection
            # and select linked on the spline point under the mouse cursor.
            if event.shift:
                bpy.ops.curve.select_linked_pick('INVOKE_DEFAULT', deselect=False)
                return {'FINISHED'}

            return self.execute(context)

        return {'PASS_THROUGH'}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # Load preference state
        active_state = True
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = bpy.context.preferences.addons[addon_name].preferences
            active_state = prefs.enable_context_select
        except Exception:
            pass

        # 1. Mesh Edit Mode Keymap
        km_mesh = kc.keymaps.get('Mesh')
        if not km_mesh:
            km_mesh = kc.keymaps.new(name='Mesh', space_type='EMPTY')

        kmi_mesh = km_mesh.keymap_items.new(
            REXTOOLS3_OT_ContextAwareSelect.bl_idname,
            type='LEFTMOUSE',
            value='DOUBLE_CLICK',
            any=True
        )
        kmi_mesh.active = active_state
        addon_keymaps.append((km_mesh, kmi_mesh))

        # 2. Curve Edit Mode Keymap
        km_curve = kc.keymaps.get('Curve')
        if not km_curve:
            km_curve = kc.keymaps.new(name='Curve', space_type='EMPTY')

        kmi_curve = km_curve.keymap_items.new(
            REXTOOLS3_OT_ContextAwareSelect.bl_idname,
            type='LEFTMOUSE',
            value='DOUBLE_CLICK',
            any=True
        )
        kmi_curve.active = active_state
        addon_keymaps.append((km_curve, kmi_curve))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
