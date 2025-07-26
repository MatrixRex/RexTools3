import bpy, bmesh, gpu, blf
from gpu_extras.batch import batch_for_shader
from .. import overlay_drawer
import time
import math

class REXTOOLS3_OT_uvSeamAreaByAngle_modal(bpy.types.Operator):
    bl_idname = "rextools3.uv_seam_area_by_angle_modal"
    bl_label = "Area Seam by Angle (drag mouse to adjust)"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    sensitivity = 0.0005
    MODES = ['Angle', 'Coplanar', 'Normal']

    def invoke(self, context, event):
        obj = context.object
        if not (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'):
            self.report({'ERROR'}, "Must be in Edit Mode on a mesh")
            return {'CANCELLED'}

        # store original seeds
        bm = bmesh.from_edit_mesh(obj.data)
        self.seed_indices = [f.index for f in bm.faces if f.select]

        # initial state
        self.start_mouse        = (event.mouse_region_x, event.mouse_region_y)
        self.current_mouse      = self.start_mouse
        self.threshold          = 0.0
        self.type_index         = 0
        self.mode               = self.MODES[self.type_index]
        self.option_show_until  = 0.0
        self.clear_inner        = False

        # first select
        self._restore_and_select(context)

        # install overlay
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_overlay, (context,), 'WINDOW', 'POST_PIXEL'
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _restore_and_select(self, context):
        # reset to original seeds
        obj = context.object
        bm  = bmesh.from_edit_mesh(obj.data)
        for f in bm.faces: f.select = False
        for idx in self.seed_indices: bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)

        # apply based on current mode
        if self.mode == 'Linked Flat':
            bpy.ops.mesh.faces_select_linked_flat(sharpness=self.threshold * math.pi)
        elif self.mode == 'Coplanar':
            bpy.ops.mesh.select_similar(type='FACE_COPLANAR', threshold=self.threshold)
        else:  # 'Normal'
            bpy.ops.mesh.select_similar(type='FACE_NORMAL',   threshold=self.threshold)

    def _restore_seeds(self, context):
        obj = context.object
        bm  = bmesh.from_edit_mesh(obj.data)
        for f in bm.faces: f.select = False
        for idx in self.seed_indices: bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)

    def _draw_overlay(self, context):
        sx, sy = self.start_mouse
        cx, cy = self.current_mouse
        od      = overlay_drawer

        od.draw_line((sx, sy), (cx, cy))
        od.draw_point((sx, sy), radius=6, color=(1, 0, 0, 1))

        # decide threshold display range per mode
        if self.mode == 'Linked Flat':
            thr_value, thr_min, thr_max = self.threshold * 180.0, 0.0, 180.0
        else:
            thr_value, thr_min, thr_max = self.threshold,       0.0, 1.0

        od.draw_info_block(
            x=sx, y=sy,
            title="SeamArea by Angle",
            lines=[
                ("Mode",      (self.MODES, self.mode),    "Scroll Wheel"),
                ("Threshold", (thr_value, thr_min, thr_max),"Drag Mouse L/R"),
                ("Clear Inner", str(self.clear_inner),     "Press A"),
            ],
            show_until_map={"Mode": self.option_show_until}
        )

    def modal(self, context, event):
        # ——— mode switch on scroll ———
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            if event.type == 'WHEELUPMOUSE':
                self.type_index = (self.type_index + 1) % len(self.MODES)
            else:
                self.type_index = (self.type_index - 1) % len(self.MODES)
            self.mode              = self.MODES[self.type_index]
            self.option_show_until = time.time() + 1.2
            self._restore_and_select(context)
            if context.area: context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # ——— adjust threshold by drag ———
        if event.type == 'MOUSEMOVE':
            self.current_mouse = (event.mouse_region_x, event.mouse_region_y)
            dist = abs(self.current_mouse[0] - self.start_mouse[0])
            self.threshold = min(dist * self.sensitivity, 1.0)
            self._restore_and_select(context)
            if context.area: context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # ——— toggle clear-inner ———
        if event.type == 'A' and event.value == 'PRESS':
            self.clear_inner = not self.clear_inner
            if context.area: context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # ——— confirm ———
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if self.clear_inner:
                bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_seam(clear=False)
            return {'FINISHED'}

        # ——— cancel ———
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self._restore_seeds(context)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if context.area: context.area.tag_redraw()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
