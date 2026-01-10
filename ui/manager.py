import gpu
import bpy
import time
from ..core.theme import Theme

class OverlayManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OverlayManager, cls).__new__(cls)
            cls._instance.overlays = []
            cls._instance.handle = None
            cls._instance.mouse_pos = (0, 0)
        return cls._instance

    def _force_redraw(self):
        if not bpy.context.screen: return
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D': area.tag_redraw()

    def add_overlay(self, overlay):
        if overlay not in self.overlays:
            if getattr(overlay, 'anchor_y', None) == 'BOTTOM':
                bottom_toasts = [ov for ov in self.overlays if getattr(ov, 'anchor_y', None) == 'BOTTOM']
                if len(bottom_toasts) >= 3:
                    oldest = sorted(bottom_toasts, key=lambda x: x.start_time)[0]
                    self.remove_overlay(oldest)
            self.overlays.append(overlay)
        if not self.handle:
            self.handle = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        if not bpy.app.timers.is_registered(self._check_timeouts):
            bpy.app.timers.register(self._check_timeouts, first_interval=0.1)
        if any(ov.close_on_click or ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in self.overlays):
            bpy.ops.rextools3.overlay_event_watcher('INVOKE_DEFAULT')
        self._force_redraw()
        return overlay

    def _check_timeouts(self):
        if not self.overlays: return None
        now = time.time()
        to_remove = [ov for ov in self.overlays if ov.timeout and (now - ov.start_time) > ov.timeout]
        if to_remove:
            for ov in to_remove: self.remove_overlay(ov)
            self._force_redraw()
        return 0.1

    def remove_overlay(self, overlay):
        if overlay in self.overlays: self.overlays.remove(overlay)
        if not self.overlays and self.handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None
        self._force_redraw()

    def clear(self):
        self.overlays.clear()
        if self.handle:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None
        self._force_redraw()

    def draw(self):
        if not self.overlays: return
        gpu.state.blend_set('ALPHA')
        bottom_toasts = [ov for ov in self.overlays if getattr(ov, 'anchor_y', None) == 'BOTTOM']
        bottom_toasts.sort(key=lambda x: x.start_time)
        curr_offset = 0
        for ov in reversed(bottom_toasts):
            ov._stack_offset_y = curr_offset
            ov.update_layout(0, 0)
            curr_offset += ov.height + 10
        for overlay in self.overlays: overlay.draw()
        gpu.state.blend_set('NONE')

class REXTOOLS3_OT_OverlayEventWatcher(bpy.types.Operator):
    bl_idname = "rextools3.overlay_event_watcher"
    bl_label = "Overlay Event Watcher"
    def modal(self, context, event):
        manager = OverlayManager()
        if not manager.overlays: return {'FINISHED'}
        manager.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        if any(ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in manager.overlays):
            self._force_redraw_areas(context)
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE'} and event.value == 'PRESS':
            to_remove = [ov for ov in manager.overlays if ov.close_on_click]
            for ov in to_remove: ov.hide()
            self._force_redraw_areas(context)
            if not any(ov.close_on_click or ov.anchor_x == 'MOUSE' or ov.anchor_y == 'MOUSE' for ov in manager.overlays): return {'FINISHED'}
        return {'PASS_THROUGH'}
    def _force_redraw_areas(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D': area.tag_redraw()
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
