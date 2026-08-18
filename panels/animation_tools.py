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

        # Keyframe Offset section
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

        # Walk Cycle Creator section
        wc_props = scene.rextools3_walk_cycle_props
        layout.separator()
        col2 = draw_section(layout, "Walk Cycle Creator", icon='ARMATURE_DATA')
        
        col2.prop(wc_props, "walk_mode")
        
        box = col2.box()
        box.label(text="Bones", icon='BONE_DATA')
        obj = context.active_object
        
        if obj and obj.type == 'ARMATURE':
            box.prop_search(wc_props, "bone_leg_l", obj.data, "bones")
            box.prop_search(wc_props, "bone_leg_r", obj.data, "bones")
            if wc_props.walk_mode == 'BIPEDAL':
                box.prop_search(wc_props, "bone_arm_l", obj.data, "bones")
                box.prop_search(wc_props, "bone_arm_r", obj.data, "bones")
            else:
                box.prop_search(wc_props, "bone_arm_l", obj.data, "bones", text="Front Leg L")
                box.prop_search(wc_props, "bone_arm_r", obj.data, "bones", text="Front Leg R")
            
            box.prop_search(wc_props, "bone_hip", obj.data, "bones")
            box.prop_search(wc_props, "bone_head", obj.data, "bones")
        else:
            box.label(text="Please select an armature", icon='ERROR')
            
        col2.separator()
        col2.prop(wc_props, "cycle_length")
        col2.prop(wc_props, "stride_length")
        col2.prop(wc_props, "step_height")
        col2.prop(wc_props, "hip_sway")
        col2.prop(wc_props, "hip_bob")
        if wc_props.walk_mode == 'BIPEDAL':
            col2.prop(wc_props, "arm_swing")
            
        col2.separator()
        draw_call_to_action(col2, "rextools3.walk_cycle_creator", "Create Walk Cycle", icon='PLAY')
