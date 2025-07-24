import bpy

class REXTOOLS3_OT_modal_example(bpy.types.Operator):
    """Example Modal Operator"""
    bl_idname = "rextools3.modal_example"
    bl_label = "Run Modal Example"
    bl_options = {'REGISTER', 'UNDO'}

    # no __init__ override!

    def invoke(self, context, event):
        # store initial mouse position here
        self.start_mouse = (event.mouse_region_x, event.mouse_region_y)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, f"Modal started at {self.start_mouse}")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm = context.window_manager
        
        if event.type == 'MOUSEMOVE':
           wm = context.window_manager
           wm.modal_x = event.mouse_region_x
           wm.modal_y = event.mouse_region_y

           # force the 3D‑View sidebar to redraw so the panel shows the new X/Y
           if context.area:
               context.area.tag_redraw()

           return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.report({'INFO'}, "Modal finished")
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.report({'WARNING'}, "Modal cancelled")
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
