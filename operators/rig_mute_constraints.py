import bpy
from bpy.types import Operator

class REXTOOLS3_OT_MuteConstraints(Operator):
    """Mute or unmute constraints on selected bones"""
    bl_idname = "rextools3.mute_constraints"
    bl_label = "Mute Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE' and 
                context.selected_pose_bones)

    def execute(self, context):
        props = context.scene.pose_tools_props
        target_prop = props.mute_constraint_target
        selected_bones = context.selected_pose_bones

        matching_constraints = []

        for pb in selected_bones:
            for con in pb.constraints:
                if target_prop == 'ALL':
                    matching_constraints.append(con)
                elif target_prop.startswith("NAME:"):
                    name = target_prop[5:]
                    if con.name == name:
                        matching_constraints.append(con)
                elif target_prop.startswith("TYPE:"):
                    c_type = target_prop[5:]
                    if con.type == c_type:
                        matching_constraints.append(con)
                else:
                    if con.name == target_prop or con.type == target_prop:
                        matching_constraints.append(con)

        if not matching_constraints:
            self.report({'WARNING'}, "No matching constraints found on selected bone(s)")
            return {'CANCELLED'}

        any_unmuted = any(not con.mute for con in matching_constraints)

        new_mute_state = True if any_unmuted else False
        for con in matching_constraints:
            con.mute = new_mute_state

        action_str = "Muted" if new_mute_state else "Unmuted"
        count = len(matching_constraints)
        bone_count = len(selected_bones)
        self.report({'INFO'}, f"{action_str} {count} constraint(s) on {bone_count} bone(s)")

        return {'FINISHED'}
