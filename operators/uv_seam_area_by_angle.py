import bpy, bmesh, gpu, blf
from gpu_extras.batch import batch_for_shader
from bpy.props import FloatProperty
from .. import overlay_drawer
import time
import math

class REXTOOLS3_OT_uvSeamAreaByAngle_modal(bpy.types.Operator):
    bl_idname = "rextools3.uv_seam_area_by_angle_modal"
    bl_label = "Area Seam by Angle (drag mouse to adjust)"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    sensitivity = 0.001

    def invoke(self, context, event):
        obj = context.object
        if not (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'):
            self.report({'ERROR'}, "Must be in Edit Mode on a mesh")
            return {'CANCELLED'}

        # store seed faces
        bm = bmesh.from_edit_mesh(obj.data)
        self.seed_indices = [f.index for f in bm.faces if f.select]         # :contentReference[oaicite:2]{index=2}

        # initial state
        self.start_mouse = (event.mouse_region_x, event.mouse_region_y)
        self.current_mouse = self.start_mouse
        self.threshold = 0.0
        self.option_show_until = 0.0

        # initial select
        self._restore_and_select(context)

        # install overlay
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_overlay, (context,), 'WINDOW', 'POST_PIXEL'
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _restore_and_select(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        # deselect all, reselect seeds
        for f in bm.faces:
            f.select = False
        for idx in self.seed_indices:
            bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)
        # apply angle‐based select
        bpy.ops.mesh.faces_select_linked_flat(sharpness=self.threshold * math.pi)

    def _restore_seeds(self, context):
        """Restore only the original seed faces."""
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        for f in bm.faces:
            f.select = False
        for idx in self.seed_indices:
            bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)

    def _draw_overlay(self, context):
        sx, sy = self.start_mouse
        cx, cy = self.current_mouse
        od = overlay_drawer

        od.draw_line((sx, sy), (cx, cy))
        od.draw_point((sx, sy), radius=6, color=(1, 0, 0, 1))

        od.draw_info_block(
            x=sx, y=sy,
            title="SeamArea by Angle",
            lines=[
                ("Threshold", (self.threshold * 180.0, 0.0, 180.0), "Drag Mouse L/R"),
            ]
        )

    def modal(self, context, event):
        # adjust threshold
        if event.type == 'MOUSEMOVE':
            self.current_mouse = (event.mouse_region_x, event.mouse_region_y)
            dist = abs(self.current_mouse[0] - self.start_mouse[0])
            self.threshold = min(dist * self.sensitivity, 1.0)
            self._restore_and_select(context)
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)
            return {'FINISHED'}

        # **cancel**: restore original seeds, remove overlay, redraw
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self._restore_seeds(context)                                     # :contentReference[oaicite:3]{index=3} adjusted
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if context.area:
                context.area.tag_redraw()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
