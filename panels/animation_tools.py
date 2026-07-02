import bpy
from bpy.types import Panel
from ..ui.utils import draw_section, draw_call_to_action

class REXTOOLS3_PT_AnimationTools(Panel):
    bl_label = "Animation Tools"
    bl_idname = "REXTOOLS3_PT_animation_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    bl_context = "posemode"

    @classmethod
    def poll(cls, context):
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            if not prefs.enable_animation_tools:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.rextools3_keyframe_offset_props

        # Use helper from ui/utils to draw the section
        col = draw_section(layout, "Keyframe Offset", icon='ANIM_DATA')

        # Direction toggle
        row = col.row(align=True)
        row.prop(props, "direction", expand=True)

        col.separator()

        # Offset Value input
        col.prop(props, "offset_value")

        col.separator()
        
        # Execute operator button using draw_call_to_action helper
        draw_call_to_action(col, "rextools3.keyframe_offset", "Offset Keyframes", icon='PLAY')
