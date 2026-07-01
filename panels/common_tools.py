import bpy
from ..ui.utils import draw_section, draw_input_group


class RexTools3CommonToolsPanel(bpy.types.Panel):
    bl_label = "Common Tools"
    bl_idname = "VIEW3D_PT_rextools3_common_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # sidebar
    bl_category = "RexTools3"  # tab name
    
    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_common_tools:
                return False
        except Exception:
            pass
        return True
    
    def draw(self, context):
        layout = self.layout
        
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if not prefs or prefs.enable_tool_open_folder:
            layout.operator("rextools3.open_folder", text="Open Folder")

        if not prefs or prefs.enable_tool_object_transform:
            obj = context.active_object
            if obj and obj.select_get():
                if not prefs or prefs.enable_tool_open_folder:
                    layout.separator()
                
                col = draw_section(layout, "Object Transform", icon='OBJECT_DATA')
                
                # Position
                col.label(text="Position")
                row = col.row(align=True)
                row.prop(obj, "location", text="")
                
                col.separator()
                
                # Rotation
                col.label(text="Rotation")
                row = col.row(align=True)
                if obj.rotation_mode == 'QUATERNION':
                    row.prop(obj, "rotation_quaternion", text="")
                elif obj.rotation_mode == 'AXIS_ANGLE':
                    row.prop(obj, "rotation_axis_angle", text="")
                else:
                    row.prop(obj, "rotation_euler", text="")
                    
                col.separator()
                
                # Scale
                col.label(text="Scale")
                row = col.row(align=True)
                row.prop(obj, "scale", text="")

        
        
