import bpy
from ..ui.overlay import ViewportOverlay, Label, Row, Column, ProgressBar, MessageBox
from ..core.theme import Theme

class REXTOOLS3_OT_TestOverlay(bpy.types.Operator):
    bl_idname = "rextools3.test_overlay"
    bl_label = "Test Overlay System"
    bl_description = "Show a test overlay with various closing features"
    
    _overlay = None

    def execute(self, context):
        if REXTOOLS3_OT_TestOverlay._overlay:
            REXTOOLS3_OT_TestOverlay._overlay.hide()
            REXTOOLS3_OT_TestOverlay._overlay = None
            return {'FINISHED'}

        # Create a new overlay
        ov = ViewportOverlay(title="Modular System Test", x='CENTER', y=None)
        
        # Closing features setup
        ov.timeout = 10 # Auto close in 10s
        ov.close_on_click = False # Disabled for timing test
        
        # Section: Description
        sec1 = ov.add(Column())
        sec1.add(Label("CLOSE MODES ENABLED:", color=Theme.COLOR_INFO))
        row = sec1.add(Row())
        row.add(Label("1. Timeout (10s)", size=12, color=Theme.COLOR_WARNING))
        
        sec1.add(Label("----------------------------------", color=Theme.COLOR_SUBTEXT))
        
        # Section: Progress
        sec2 = ov.add(Column())
        pbar = sec2.add(ProgressBar(label="Loading System", width=250))
        pbar.value = 0.42
        
        # Section: Messages
        sec3 = ov.add(Column())
        sec3.add(MessageBox(text="This box will disappear automatically after 10 seconds. Click-to-close is disabled for this test.", type='INFO', width=250))

        ov.show()
        REXTOOLS3_OT_TestOverlay._overlay = ov
        
        self.report({'INFO'}, "Overlay started. Will auto-close in 10s.")
        return {'FINISHED'}


class REXTOOLS3_OT_TestOverlayProgress(bpy.types.Operator):
    bl_idname = "rextools3.test_overlay_progress"
    bl_label = "Test Overlay Progress"
    
    _timer = None
    _overlay = None
    _pbar = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._pbar.value >= 1.0:
                self._pbar.value = 1.0
                # Auto-hide on completion after a small delay
                self._overlay.hide()
                self.cancel(context)
                return {'FINISHED'}
            
            self._pbar.value += 0.02
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        return {'PASS_THROUGH'}

    def execute(self, context):
        ov = ViewportOverlay(title="Task completion", x='CENTER', y='CENTER')
        self._pbar = ov.add(ProgressBar(label="Processing", width=300))
        self._pbar.value = 0
        ov.add(Label("Overlay will auto-close at 100%", color=Theme.COLOR_SUBTEXT))
        
        ov.show()
        self._overlay = ov
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.04, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        if self._overlay:
            self._overlay.hide()
