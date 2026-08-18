import bpy
from mathutils import Vector

class REXTOOLS3_OT_walk_cycle_creator(bpy.types.Operator):
    bl_idname = "rextools3.walk_cycle_creator"
    bl_label = "Create Walk Cycle"
    bl_description = "Generates a basic, easily editable walk cycle using selected IK bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE' and context.mode == 'POSE'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.rextools3_walk_cycle_props

        C = props.cycle_length
        f1 = 1
        f2 = 1 + int(C * 0.25)
        f3 = 1 + int(C * 0.5)
        f4 = 1 + int(C * 0.75)
        f5 = 1 + C

        def insert_loc(bone_name, frame, loc_offset):
            if not bone_name:
                return
            bone = obj.pose.bones.get(bone_name)
            if not bone:
                self.report({'WARNING'}, f"Bone '{bone_name}' not found.")
                return
            
            # Add loc_offset to the rest pose location or just set it locally. 
            # Assuming IK bones are localized at (0,0,0) in pose mode.
            bone.location = Vector(loc_offset)
            bone.keyframe_insert(data_path="location", frame=frame)
            
            # Set interpolation to BEZIER
            try:
                action = obj.animation_data.action
                if action:
                    for fcurve in action.fcurves:
                        if fcurve.data_path == f'pose.bones["{bone_name}"].location':
                            for kf in fcurve.keyframe_points:
                                if kf.co.x == frame:
                                    kf.interpolation = 'BEZIER'
            except Exception:
                pass

        # We assume character faces -Y (standard Blender).
        # Let's assume -Y is forward, so Y goes from +stride/2 to -stride/2
        s = props.stride_length / 2.0
        h = props.step_height
        
        # Legs
        # Leg L: Forward -> Mid -> Back -> Lift -> Forward
        insert_loc(props.bone_leg_l, f1, (0, -s, 0))
        insert_loc(props.bone_leg_l, f2, (0, 0, 0))
        insert_loc(props.bone_leg_l, f3, (0, s, 0))
        insert_loc(props.bone_leg_l, f4, (0, 0, h))
        insert_loc(props.bone_leg_l, f5, (0, -s, 0))

        # Leg R: Back -> Lift -> Forward -> Mid -> Back
        insert_loc(props.bone_leg_r, f1, (0, s, 0))
        insert_loc(props.bone_leg_r, f2, (0, 0, h))
        insert_loc(props.bone_leg_r, f3, (0, -s, 0))
        insert_loc(props.bone_leg_r, f4, (0, 0, 0))
        insert_loc(props.bone_leg_r, f5, (0, s, 0))

        if props.walk_mode == 'BIPEDAL':
            a = props.arm_swing / 2.0
            # Arm L: opposite to Leg L
            insert_loc(props.bone_arm_l, f1, (0, a, 0))
            insert_loc(props.bone_arm_l, f2, (0, 0, 0))
            insert_loc(props.bone_arm_l, f3, (0, -a, 0))
            insert_loc(props.bone_arm_l, f4, (0, 0, 0))
            insert_loc(props.bone_arm_l, f5, (0, a, 0))

            # Arm R: opposite to Leg R
            insert_loc(props.bone_arm_r, f1, (0, -a, 0))
            insert_loc(props.bone_arm_r, f2, (0, 0, 0))
            insert_loc(props.bone_arm_r, f3, (0, a, 0))
            insert_loc(props.bone_arm_r, f4, (0, 0, 0))
            insert_loc(props.bone_arm_r, f5, (0, -a, 0))
        else:
            # Quadrupedal: Trot pattern
            # Front L moves with Back R
            insert_loc(props.bone_arm_l, f1, (0, s, 0))
            insert_loc(props.bone_arm_l, f2, (0, 0, h))
            insert_loc(props.bone_arm_l, f3, (0, -s, 0))
            insert_loc(props.bone_arm_l, f4, (0, 0, 0))
            insert_loc(props.bone_arm_l, f5, (0, s, 0))
            
            # Front R moves with Back L
            insert_loc(props.bone_arm_r, f1, (0, -s, 0))
            insert_loc(props.bone_arm_r, f2, (0, 0, 0))
            insert_loc(props.bone_arm_r, f3, (0, s, 0))
            insert_loc(props.bone_arm_r, f4, (0, 0, h))
            insert_loc(props.bone_arm_r, f5, (0, -s, 0))

        # Hips: Bob and Sway
        b = props.hip_bob
        sw = props.hip_sway
        
        insert_loc(props.bone_hip, f1, (0, 0, -b))
        insert_loc(props.bone_hip, f2, (sw, 0, 0))
        insert_loc(props.bone_hip, f3, (0, 0, -b))
        insert_loc(props.bone_hip, f4, (-sw, 0, 0))
        insert_loc(props.bone_hip, f5, (0, 0, -b))

        # Head / Spine: Follow Bob
        hb = b * 0.5
        insert_loc(props.bone_head, f1, (0, 0, -hb))
        insert_loc(props.bone_head, f2, (0, 0, 0))
        insert_loc(props.bone_head, f3, (0, 0, -hb))
        insert_loc(props.bone_head, f4, (0, 0, 0))
        insert_loc(props.bone_head, f5, (0, 0, -hb))

        self.report({'INFO'}, "Walk cycle created successfully!")
        
        # Ensure scene frame range fits cycle
        context.scene.frame_start = 1
        context.scene.frame_end = f5

        return {'FINISHED'}
