import bpy
import bmesh
from bpy.types import Operator, Panel
from bpy.props import IntProperty


def _bm_from_context(context):
    obj = context.active_object
    if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
        return None, None
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    return bm, me


class MESH_OT_checker_dissolve(Operator):
    """Ring → Checker → Loop → Dissolve Edges (with verts). Redo uses the original seed selection."""
    bl_idname = "mesh.checker_dissolve"
    bl_label = "Checker Dissolve"
    bl_options = {'REGISTER', 'UNDO'}  # keep redo panel on OUR operator

    # Redo props (match Checker Deselect UI)
    deselected: IntProperty(name="Deselected", default=1, min=0)
    selected:   IntProperty(name="Selected",   default=1, min=1)
    offset:     IntProperty(name="Offset",     default=0)

    # persistent seed captured at invoke-time
    _seed_edge_indices: list[int] | None = None
    _seed_edge_keys: list[tuple[int, int]] | None = None  # sorted (v0_idx, v1_idx) per edge

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def _capture_seed(self, context):
        bm, _ = _bm_from_context(context)
        if not bm:
            return False
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        sel_edges = [e for e in bm.edges if e.select]
        if not sel_edges:
            return False

        self._seed_edge_indices = [e.index for e in sel_edges]
        # Back up with stable-ish keys = pairs of vertex indices
        self._seed_edge_keys = [tuple(sorted((e.verts[0].index, e.verts[1].index))) for e in sel_edges]
        return True

    def _restore_seed(self, context):
        """Try to restore the original seed selection. Prefer original indices; if those
        are invalid after topology changes, fall back to edge keys (pairs of vert indices)."""
        bm, me = _bm_from_context(context)
        if not bm:
            return False

        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # clear current selection
        for e in bm.edges:
            e.select_set(False)

        restored = 0

        # 1) Try via indices (fast path)
        if self._seed_edge_indices:
            for idx in self._seed_edge_indices:
                if 0 <= idx < len(bm.edges):
                    try:
                        bm.edges[idx].select_set(True)
                        restored += 1
                    except IndexError:
                        # table might still be stale; ensure and skip
                        bm.edges.ensure_lookup_table()

        # 2) If nothing restored, try via edge keys (pairs of vert indices)
        if restored == 0 and self._seed_edge_keys:
            for a, b in self._seed_edge_keys:
                if 0 <= a < len(bm.verts) and 0 <= b < len(bm.verts):
                    va = bm.verts[a]
                    vb = bm.verts[b]
                    # find an edge connecting va-vb if it still exists
                    found = None
                    for e in va.link_edges:
                        v0, v1 = e.verts
                        if (v0 == va and v1 == vb) or (v0 == vb and v1 == va):
                            found = e
                            break
                    if found:
                        found.select_set(True)
                        restored += 1

        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
        return restored > 0

    def invoke(self, context, event):
        if not context.tool_settings.mesh_select_mode[1]:
            self.report({'WARNING'}, "Switch to Edge Select mode first.")
            return {'CANCELLED'}
        if not self._capture_seed(context):
            self.report({'WARNING'}, "Select at least one edge.")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        # Ensure edge select and we have a seed to replay from
        if not context.tool_settings.mesh_select_mode[1]:
            self.report({'WARNING'}, "Switch to Edge Select mode first.")
            return {'CANCELLED'}

        if not self._restore_seed(context):
            self.report({'WARNING'}, "Could not restore original selection. Re-select an edge and run again.")
            return {'CANCELLED'}

        # === exact Blender sequence (operators) ===
        # 1) edge ring from the seed
        bpy.ops.mesh.loop_multi_select(ring=True)

        # 2) checker deselect with our redo-able props
        bpy.ops.mesh.select_nth(skip=self.deselected, nth=self.selected, offset=self.offset)

        # 3) loop select (perpendicular)
        bpy.ops.mesh.loop_multi_select(ring=False)

        # 4) dissolve edges — now with verts (matches "regular" dissolve)
        bpy.ops.mesh.dissolve_edges(use_verts=True, use_face_split=False)

        # IMPORTANT: do not call any other registered operator after this point.
        # Returning FINISHED keeps *this* operator ("Checker Dissolve") active in the redo panel.
        return {'FINISHED'}


class VIEW3D_PT_mesh_cleanup(Panel):
    bl_label = "Mesh Cleanup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None and
            context.active_object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def draw(self, context):
        self.layout.operator(MESH_OT_checker_dissolve.bl_idname, icon='MOD_DECIM')
