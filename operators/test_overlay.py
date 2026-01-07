import bpy
from ..overlay_drawer import ViewportOverlay, Label, Row, Column, ProgressBar, MessageBox, Theme

class REXTOOLS3_OT_TestOverlay(bpy.types.Operator):
    bl_idname = "rextools3.test_overlay"
    bl_label = "Test Overlay System"
    bl_description = "Show a test overlay with various components"
    
    _overlay = None

    def execute(self, context):
        if REXTOOLS3_OT_TestOverlay._overlay:
            REXTOOLS3_OT_TestOverlay._overlay.hide()
            REXTOOLS3_OT_TestOverlay._overlay = None
            return {'FINISHED'}

        # Create a new overlay
        ov = ViewportOverlay(title="RexTools System Test", x='CENTER', y=None)
        
        # Section 1: Labels and Rows
        sec1 = ov.add(Column())
        row1 = sec1.add(Row())
        row1.add(Label("Status:", color=Theme.COLOR_INFO))
        row1.add(Label("Ready", color=Theme.COLOR_SUCCESS))
        
        sec1.add(Label("This is a modular layout system.", size=12, color=Theme.COLOR_SUBTEXT))
        
        # Section 2: Progress Bars
        sec2 = ov.add(Column())
        sec2.add(Label("Operation Progress", size=14))
        pbar = sec2.add(ProgressBar(label="Exporting", width=250))
        pbar.value = 0.75
        
        # Section 3: Messages
        sec3 = ov.add(Column())
        sec3.add(MessageBox(text="Export finished successfully! All files are in the target directory.", type='INFO', width=250))
        sec3.add(MessageBox(text="Warning: Some objects have missing UV maps and were skipped.", type='WARNING', width=250))

        ov.show()
        REXTOOLS3_OT_TestOverlay._overlay = ov
        
        self.report({'INFO'}, "Overlay test started. Run again to hide.")
        return {'FINISHED'}

# Test for progress updates (Complex test)
class REXTOOLS3_OT_TestOverlayProgress(bpy.types.Operator):
    bl_idname = "rextools3.test_overlay_progress"
    bl_label = "Test Overlay Progress"
    
    _timer = None
    _overlay = None
    _pbar = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._pbar.value >= 1.0:
                self.cancel(context)
                return {'FINISHED'}
            
            self._pbar.value += 0.01
            # Redraw view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        return {'PASS_THROUGH'}

    def execute(self, context):
        ov = ViewportOverlay(title="Animation Test", x='CENTER', y='CENTER')
        self._pbar = ov.add(ProgressBar(label="Simulating", width=300))
        self._pbar.value = 0
        ov.add(Label("Testing modal updates...", color=Theme.COLOR_SUBTEXT))
        
        ov.show()
        self._overlay = ov
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        if self._overlay:
            self._overlay.hide()
