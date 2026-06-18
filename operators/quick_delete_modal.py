import bpy
import gpu
from bgl import *
from bpy.types import Operator
from ..ui.templates import ModalOverlay
from ..core.theme import Theme

class REXTOOLS3_OT_quick_delete_modal(Operator):
    """Refined Quick Delete Menu with Modifier Support"""
    bl_idname = "rextools3.quick_delete_modal"
    bl_label = "Quick Delete"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            addon_name = __package__.partition('.')[0]
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_quick_delete:
                return False
        except Exception:
            pass
        return context.mode == 'EDIT_MESH'

    def modal(self, context, event):
        context.area.tag_redraw()
        self.shift_held = event.shift
        self.alt_held = event.alt
        self.ctrl_held = event.ctrl
        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'X' and event.value == 'PRESS':
            # Toggle off if pressed again
            self.cancel(context)
            return {'CANCELLED'}

        # Handle Shortcuts
        if event.value == 'PRESS':
            # Priority 1: Shift -> Dissolve
            if event.shift:
                if event.type == 'Q':
                    bpy.ops.mesh.dissolve_verts()
                    self.finish(context); return {'FINISHED'}
                elif event.type == 'W':
                    bpy.ops.mesh.dissolve_edges()
                    self.finish(context); return {'FINISHED'}
                elif event.type == 'E':
                    bpy.ops.mesh.dissolve_faces()
                    self.finish(context); return {'FINISHED'}
            
            # Priority 2: Base Keys -> Delete
            elif not event.shift and not event.ctrl and not event.alt:
                if event.type == 'Q':
                    bpy.ops.mesh.delete(type='VERT')
                    self.finish(context); return {'FINISHED'}
                elif event.type == 'W':
                    bpy.ops.mesh.delete(type='EDGE')
                    self.finish(context); return {'FINISHED'}
                elif event.type == 'E':
                    bpy.ops.mesh.delete(type='FACE')
                    self.finish(context); return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found")
            return {'CANCELLED'}

        # Initialize UI at mouse position
        self.ui = ModalOverlay(title="Quick Delete", x=event.mouse_region_x, y=event.mouse_region_y)
        self.ui.visible = True
        
        # Add a callback to draw the HUD
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def draw_callback(self, context):
        if not hasattr(self, 'ui'): return
        
        self.ui.items = []
        
        # Decide Main Action Label
        action_label = "DELETE"
        theme_color = Theme.COLOR_INFO
        
        if getattr(self, 'shift_held', False):
            action_label = "DISSOLVE"
            theme_color = Theme.COLOR_SUCCESS
        elif getattr(self, 'alt_held', False):
            action_label = "MERGE"
            theme_color = Theme.COLOR_WARNING
        elif getattr(self, 'ctrl_held', False):
            action_label = "SELECT"
            theme_color = (0.3, 0.6, 1.0, 1.0) # Blueish
            
        self.ui.title = f"Quick {action_label.title()}"
        
        # We can dynamically change the color of the UI using Theme if it was designed to be reactive,
        # but here we'll just show it in the label and items.
        
        shortcut_q = "Q" if not getattr(self, 'shift_held', False) else "Shift+Q"
        shortcut_w = "W" if not getattr(self, 'shift_held', False) else "Shift+W"
        shortcut_e = "E" if not getattr(self, 'shift_held', False) else "Shift+E"
        
        self.ui.add_value("Vertices", shortcut_q, f"{action_label}")
        self.ui.add_value("Edges",    shortcut_w, f"{action_label}")
        self.ui.add_value("Faces",    shortcut_e, f"{action_label}")
        
        # Add hint for modifiers
        self.ui.add_value("Modifiers", "Shift/Alt/Ctrl", "Switch Modes")
        
        self.ui.draw()

    def finish(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

def register():
    pass

def unregister():
    pass
