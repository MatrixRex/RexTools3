# operators/select_similar_modal.py

import bpy, bmesh
from bpy.props import FloatProperty

class REXTOOLS3_OT_select_similar_modal(bpy.types.Operator):
    """Select similar faces by normal—and drag to tweak the threshold."""
    bl_idname = "rextools3.select_similar_modal"
    bl_label = "Select by Normal (drag to adjust)"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    threshold: FloatProperty(
        name="Threshold",
        description="Face-normal similarity threshold",
        default=0.0, min=0.0, max=1.0
    )
    sensitivity = 0.001  # px → threshold

    def invoke(self, context, event):
        obj = context.object
        if not (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'):
            self.report({'ERROR'}, "Must be in Edit Mode on a mesh")
            return {'CANCELLED'}

        # 1️⃣ Store original seed face indices
        bm = bmesh.from_edit_mesh(obj.data)
        self.seed_indices = [f.index for f in bm.faces if f.select]

        # 2️⃣ Initialize threshold & record start X
        self.threshold = 0.0
        self.start_x = event.mouse_region_x

        # 3️⃣ Do first select (so you see initial effect)
        self._restore_and_select(context)

        # 4️⃣ Enter modal loop
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _restore_and_select(self, context):
        """Deselect all, reselect seed faces, then run select_similar."""
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)

        # Deselect everything
        for f in bm.faces:
            f.select = False
        # Reselect only the seeds
        for idx in self.seed_indices:
            bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)

        # Now extend selection by normal similarity
        bpy.ops.mesh.select_similar(type='FACE_NORMAL',
                                    threshold=self.threshold)

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            # 5️⃣ Compute new threshold from original click distance
            dist = abs(event.mouse_region_x - self.start_x)
            self.threshold = min(dist * self.sensitivity, 1.0)

            # 6️⃣ Restore seed + reapply select_similar
            self._restore_and_select(context)

            # 7️⃣ Force a redraw so you see it live
            if context.area:
                context.area.tag_redraw()

            return {'RUNNING_MODAL'}

        # ✅ Finish on left-click
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}

        # ❌ Cancel on right-click or Esc
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
