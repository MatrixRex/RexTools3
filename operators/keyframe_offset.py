import bpy
from bpy.types import Operator

class REXTOOLS3_OT_KeyframeOffset(Operator):
    """Offset keyframes of selected bones sequentially based on hierarchy depth"""
    bl_idname = "rextools3.keyframe_offset"
    bl_label = "Offset Keyframes"
    bl_description = "Offset keyframes of selected bones sequentially based on hierarchy depth"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE' and 
                context.selected_pose_bones)

    def execute(self, context):
        obj = context.active_object
        if not obj.animation_data or not obj.animation_data.action:
            self.report({'WARNING'}, "Active armature has no active action")
            return {'CANCELLED'}

        action = obj.animation_data.action
        props = context.scene.rextools3_keyframe_offset_props
        direction = props.direction
        offset_value = props.offset_value

        # Identify hierarchy within selection
        selected_bones = context.selected_pose_bones
        selected_bone_names = [b.name for b in selected_bones]
        
        # Sort bones by selection depth: Root (depth 0) to Tip (depth N)
        def get_selection_depth(pb):
            depth = 0
            curr = pb.parent
            while curr:
                if curr.name in selected_bone_names:
                    depth += 1
                curr = curr.parent
            return depth

        sorted_bones = sorted(selected_bones, key=get_selection_depth)
        num_bones = len(sorted_bones)
        
        offset_count = 0

        # Offset each bone
        for i, bone in enumerate(sorted_bones):
            # Calculate shift
            if direction == 'FROM_ROOT':
                shift = i * offset_value
            else: # FROM_TIP
                shift = (num_bones - 1 - i) * offset_value

            if shift == 0:
                continue

            # Find F-curves for this bone
            prefix1 = f'pose.bones["{bone.name}"]'
            prefix2 = f"pose.bones['{bone.name}']"
            
            bone_fcurves = []
            for fcurve in action.fcurves:
                if fcurve.data_path.startswith(prefix1) or fcurve.data_path.startswith(prefix2):
                    bone_fcurves.append(fcurve)

            if not bone_fcurves:
                continue

            for fcurve in bone_fcurves:
                for kp in fcurve.keyframe_points:
                    kp.co.x += shift
                    kp.handle_left.x += shift
                    kp.handle_right.x += shift
                fcurve.keyframe_points.update()
                
            offset_count += 1

        if offset_count > 0:
            # Tag redraw for animation editors and 3D Viewport
            for area in context.screen.areas:
                if area.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'VIEW_3D'}:
                    area.tag_redraw()
            self.report({'INFO'}, f"Offset keyframes on {offset_count} bones")
        else:
            self.report({'INFO'}, "No keyframes were offset")

        return {'FINISHED'}
