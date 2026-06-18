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
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
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
            if self.mode == 'NESTED' and self.current_category is not None and event.type == 'ESC':
                self.current_category = None
                return {'RUNNING_MODAL'}
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'X' and event.value == 'PRESS':
            self.cancel(context)
            return {'CANCELLED'}

        if event.value == 'PRESS':
            if self.mode == 'NESTED' and self.current_category is not None and event.type == 'BACKSPACE':
                self.current_category = None
                return {'RUNNING_MODAL'}
                
            result = self.handle_shortcuts(context, event)
            if result is not None:
                return result

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found")
            return {'CANCELLED'}

        # Get preference mode
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            self.mode = prefs.quick_delete_mode
        except Exception:
            self.mode = 'NESTED'
            
        self.current_category = None
        self.shift_held = event.shift
        self.alt_held = event.alt
        self.ctrl_held = event.ctrl

        # Initialize UI at mouse position
        self.ui = ModalOverlay(title="Quick Delete", x=event.mouse_region_x, y=event.mouse_region_y)
        self.ui.visible = True
        
        # Add a callback to draw the HUD
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def handle_shortcuts(self, context, event):
        if self.mode == 'NESTED':
            return self.handle_nested_mode(context, event)
        elif self.mode == 'GRID':
            return self.handle_grid_mode(context, event)
        elif self.mode == 'MODIFIER':
            return self.handle_modifier_mode(context, event)
        return None

    def handle_nested_mode(self, context, event):
        key = event.type
        if self.current_category is None:
            if key == 'A':
                self.current_category = 'DELETE'
            elif key == 'D':
                self.current_category = 'DISSOLVE'
            elif key == 'S':
                self.current_category = 'MERGE'
            elif key == 'W':
                self.current_category = 'EXTRAS'
            return None
        
        cat = self.current_category
        if cat == 'DELETE':
            if key == 'A':
                bpy.ops.mesh.delete(type='VERT')
            elif key == 'W':
                bpy.ops.mesh.delete(type='EDGE')
            elif key == 'D':
                bpy.ops.mesh.delete(type='FACE')
            elif key == 'S':
                bpy.ops.mesh.delete(type='EDGE_FACE')
            elif key == 'Q':
                bpy.ops.mesh.delete(type='ONLY_FACE')
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'DISSOLVE':
            if key == 'A':
                bpy.ops.mesh.dissolve_verts()
            elif key == 'W':
                bpy.ops.mesh.dissolve_edges()
            elif key == 'D':
                bpy.ops.mesh.dissolve_faces()
            elif key == 'S':
                bpy.ops.mesh.edge_collapse()
            elif key == 'Q':
                bpy.ops.mesh.dissolve_limited()
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'MERGE':
            if key == 'A':
                bpy.ops.mesh.merge(type='CENTER')
            elif key == 'W':
                bpy.ops.mesh.merge(type='CURSOR')
            elif key == 'D':
                bpy.ops.mesh.remove_doubles()
            elif key == 'S':
                bpy.ops.mesh.merge(type='COLLAPSE')
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'EXTRAS':
            if key == 'A':
                bpy.ops.rextools3.delete_linked_ex()
            elif key == 'W':
                bpy.ops.mesh.checker_dissolve()
            elif key == 'D':
                bpy.ops.rextools3.loop_dissolve_ex()
            elif key == 'S':
                bpy.ops.rextools3.fill_loop_inner_region()
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        return None

    def handle_grid_mode(self, context, event):
        key = event.type
        if key == 'Q':
            bpy.ops.mesh.delete(type='VERT')
        elif key == 'W':
            bpy.ops.mesh.delete(type='EDGE')
        elif key == 'E':
            bpy.ops.mesh.delete(type='FACE')
        elif key == 'R':
            bpy.ops.rextools3.delete_linked_ex()
        elif key == 'A':
            bpy.ops.mesh.dissolve_verts()
        elif key == 'S':
            bpy.ops.mesh.dissolve_edges()
        elif key == 'D':
            bpy.ops.mesh.dissolve_faces()
        elif key == 'F':
            bpy.ops.mesh.checker_dissolve()
        elif key == 'Z':
            bpy.ops.mesh.merge(type='CENTER')
        elif key == 'X':
            bpy.ops.mesh.remove_doubles()
        elif key == 'C':
            bpy.ops.rextools3.loop_dissolve_ex()
        elif key == 'V':
            bpy.ops.rextools3.fill_loop_inner_region()
        else:
            return None
            
        self.finish(context); return {'FINISHED'}

    def handle_modifier_mode(self, context, event):
        key = event.type
        if event.shift:
            if key == 'A':
                bpy.ops.mesh.dissolve_verts()
            elif key == 'W':
                bpy.ops.mesh.dissolve_edges()
            elif key == 'D':
                bpy.ops.mesh.dissolve_faces()
            elif key == 'S':
                bpy.ops.mesh.dissolve_limited()
            else:
                return None
        elif event.alt:
            if key == 'A':
                bpy.ops.mesh.merge(type='CENTER')
            elif key == 'W':
                bpy.ops.mesh.merge(type='CURSOR')
            elif key == 'D':
                bpy.ops.mesh.remove_doubles()
            elif key == 'S':
                bpy.ops.mesh.merge(type='COLLAPSE')
            else:
                return None
        elif event.ctrl:
            if key == 'A':
                bpy.ops.rextools3.delete_linked_ex()
            elif key == 'W':
                bpy.ops.mesh.checker_dissolve()
            elif key == 'D':
                bpy.ops.rextools3.loop_dissolve_ex()
            elif key == 'S':
                bpy.ops.rextools3.fill_loop_inner_region()
            else:
                return None
        else:
            if key == 'A':
                bpy.ops.mesh.delete(type='VERT')
            elif key == 'W':
                bpy.ops.mesh.delete(type='EDGE')
            elif key == 'D':
                bpy.ops.mesh.delete(type='FACE')
            elif key == 'S':
                bpy.ops.mesh.delete(type='EDGE_FACE')
            else:
                return None
                
        self.finish(context); return {'FINISHED'}

    def draw_callback(self, context):
        if not hasattr(self, 'ui'): return
        
        self.ui.items = []
        
        if self.mode == 'NESTED':
            if self.current_category is None:
                self.ui.title = "Quick Delete: Select Category"
                self.ui.add_value("Delete Options", "A", "➔")
                self.ui.add_value("Dissolve Options", "D", "➔")
                self.ui.add_value("Merge Options", "S", "➔")
                self.ui.add_value("Extras Options", "W", "➔")
            else:
                cat = self.current_category
                self.ui.title = f"Quick Delete: {cat.title()}"
                if cat == 'DELETE':
                    self.ui.add_value("Vertices", "A", "Delete")
                    self.ui.add_value("Edges", "W", "Delete")
                    self.ui.add_value("Faces", "D", "Delete")
                    self.ui.add_value("Only Edges & Faces", "S", "Delete")
                    self.ui.add_value("Only Faces", "Q", "Delete")
                elif cat == 'DISSOLVE':
                    self.ui.add_value("Vertices", "A", "Dissolve")
                    self.ui.add_value("Edges", "W", "Dissolve")
                    self.ui.add_value("Faces", "D", "Dissolve")
                    self.ui.add_value("Collapse Edges", "S", "Dissolve")
                    self.ui.add_value("Limited Dissolve", "Q", "Dissolve")
                elif cat == 'MERGE':
                    self.ui.add_value("Merge Center", "A", "Merge")
                    self.ui.add_value("Merge At Cursor", "W", "Merge")
                    self.ui.add_value("Merge By Distance", "D", "Merge")
                    self.ui.add_value("Merge Collapse", "S", "Merge")
                elif cat == 'EXTRAS':
                    self.ui.add_value("Delete Linked", "A", "Execute")
                    self.ui.add_value("Checker Dissolve", "W", "Execute")
                    self.ui.add_value("Loop Dissolve", "D", "Execute")
                    self.ui.add_value("Fill Loop Region", "S", "Execute")
                self.ui.add_value("Back to Main Menu", "Backspace/ESC", "")

        elif self.mode == 'GRID':
            self.ui.title = "Quick Delete: Direct Grid"
            self.ui.add_value("Delete: Vert / Edge / Face / Linked", "Q / W / E / R", "DELETE")
            self.ui.add_value("Dissolve: Vert / Edge / Face / Checker", "A / S / D / F", "DISSOLVE")
            self.ui.add_value("Merge: Center / By Dist", "Z / X", "MERGE")
            self.ui.add_value("Extras: Loop Dissolve / Fill Loop", "C / V", "EXTRAS")

        elif self.mode == 'MODIFIER':
            action_label = "DELETE"
            if self.shift_held:
                action_label = "DISSOLVE"
            elif self.alt_held:
                action_label = "MERGE"
            elif self.ctrl_held:
                action_label = "EXTRAS"
                
            self.ui.title = f"Quick {action_label.title()}"
            
            if not self.shift_held and not self.alt_held and not self.ctrl_held:
                self.ui.add_value("Vertices", "A", "Delete")
                self.ui.add_value("Edges", "W", "Delete")
                self.ui.add_value("Faces", "D", "Delete")
                self.ui.add_value("Only Edges/Faces", "S", "Delete")
            elif self.shift_held:
                self.ui.add_value("Vertices", "Shift+A", "Dissolve")
                self.ui.add_value("Edges", "Shift+W", "Dissolve")
                self.ui.add_value("Faces", "Shift+D", "Dissolve")
                self.ui.add_value("Limited Dissolve", "Shift+S", "Dissolve")
            elif self.alt_held:
                self.ui.add_value("Merge Center", "Alt+A", "Merge")
                self.ui.add_value("Merge At Cursor", "Alt+W", "Merge")
                self.ui.add_value("Merge By Distance", "Alt+D", "Merge")
                self.ui.add_value("Merge Collapse", "Alt+S", "Merge")
            elif self.ctrl_held:
                self.ui.add_value("Delete Linked", "Ctrl+A", "Execute")
                self.ui.add_value("Checker Dissolve", "Ctrl+W", "Execute")
                self.ui.add_value("Loop Dissolve", "Ctrl+D", "Execute")
                self.ui.add_value("Fill Loop Region", "Ctrl+S", "Execute")
                
            self.ui.add_value("Modifiers Guide", "Shift / Alt / Ctrl", "Switch Actions")

        self.ui.draw()

    def finish(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

def register():
    pass

def unregister():
    pass
