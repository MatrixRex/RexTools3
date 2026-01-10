import bpy, bmesh, gpu, blf
from gpu_extras.batch import batch_for_shader
from bpy.props import FloatProperty
from ..ui import overlay as overlay_drawer
import time

class REXTOOLS3_OT_select_similar_modal(bpy.types.Operator):
    bl_idname = "rextools3.select_similar_modal"
    bl_label = "Select by Similar (drag/scroll to adjust)"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    # sensitivity and available types
    sensitivity = 0.001
    SIM_TYPES = ['FACE_NORMAL', 'FACE_COPLANAR','FACE_SMOOTH']

    def invoke(self, context, event):
        obj = context.object
        if not (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'):
            self.report({'ERROR'}, "Must be in Edit Mode on a mesh")
            return {'CANCELLED'}

        # store seed faces
        bm = bmesh.from_edit_mesh(obj.data)
        self.seed_indices = [f.index for f in bm.faces if f.select]

        # initial state
        self.start_mouse = (event.mouse_region_x, event.mouse_region_y)
        self.current_mouse = self.start_mouse
        self.threshold = 0.0
        self.option_show_until = 0.0 

        # start with the first type
        self.type_index = 0
        self.sim_type = self.SIM_TYPES[self.type_index]

        # record start mouse pos & threshold
        self.start_mouse = (event.mouse_region_x, event.mouse_region_y)
        self.threshold = 0.0

        # initial select
        self._restore_and_select(context)

        # install our POST_PIXEL draw handler
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_overlay, (context,), 'WINDOW', 'POST_PIXEL'
        )

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _restore_and_select(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        # deselect all, reselect the seeds
        for f in bm.faces:
            f.select = False
        for idx in self.seed_indices:
            bm.faces[idx].select = True
        bmesh.update_edit_mesh(obj.data)
        # run similarity select
        bpy.ops.mesh.select_similar(
            type=self.sim_type,
            threshold=self.threshold
        )

    def _draw_overlay(self, context):
        sx, sy = self.start_mouse
        cx, cy = self.current_mouse
        od = overlay_drawer
        
        od.draw_line((sx, sy), (cx, cy))
        od.draw_crosshair((sx, sy), size=5, color=od.Theme.COLOR_INFO)

        # New Modal Overlay
        mov = od.ModalOverlay(title="Select Similar", x=sx + 20, y=sy, width=320)
        
        # 1. Type Selector
        is_scrolling = time.time() < self.option_show_until
        mov.add_mode_selector("Type", "Scroll Wheel", self.SIM_TYPES, self.type_index, interacting=is_scrolling)
        
        # 2. Threshold
        mov.add_progress("Threshold", "Drag Mouse L/R", self.threshold, 0.0, 1.0)
        
        mov.draw()



        



    def modal(self, context, event):
        wm = context.window_manager
        
        # ——— scroll wheel switches sim_type ——
        if event.type == 'WHEELUPMOUSE' and event.value == 'PRESS':
            self.type_index = (self.type_index + 1) % len(self.SIM_TYPES)
            self.option_show_until = time.time() + 1.2
        elif event.type == 'WHEELDOWNMOUSE' and event.value == 'PRESS':
            self.type_index = (self.type_index - 1) % len(self.SIM_TYPES)
            self.option_show_until = time.time() + 1.2
        else:
            self.type_index = self.type_index  # no change

        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # update sim_type
            self.sim_type = self.SIM_TYPES[self.type_index]
            # reapply from seeds with same threshold
            self._restore_and_select(context)
            # force redraw for overlay & viewport
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            # update current mouse and threshold
            self.current_mouse = (event.mouse_region_x, event.mouse_region_y)
            dist = abs(self.current_mouse[0] - self.start_mouse[0])
            self.threshold = min(dist * self.sensitivity, 1.0)

            # reapply selection base-on-seed
            self._restore_and_select(context)

            # force redraw so overlay and viewport update
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # finish: remove handler, keep selection, then chain region_to_loop
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            # optional: call next operator
            bpy.ops.mesh.region_to_loop()
            return {'FINISHED'}

        # cancel: remove handler and abort
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    # … _register / _unregister not needed if you use auto_load.py …
