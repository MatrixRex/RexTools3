import bpy
from bpy.types import Operator

class REXTOOLS3_OT_chained_bone_name(Operator):
    """Rename a chain of selected bones sequentially starting from the root"""
    bl_idname = "rextools3.chained_bone_name"
    bl_label = "Chained Bone Name"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode in {'POSE', 'EDIT'})

    def execute(self, context):
        mode = context.mode
        props = context.scene.pose_tools_props
        base_name = props.chained_bone_base_name.strip()
        
        if not base_name:
            self.report({'WARNING'}, "Please specify a base name.")
            return {'CANCELLED'}
            
        if mode == 'POSE':
            selected_bones = context.selected_pose_bones
            if not selected_bones:
                self.report({'WARNING'}, "No bones selected in Pose Mode.")
                return {'CANCELLED'}
                
            # Helper to get overall depth of a PoseBone
            def get_depth(pb):
                depth = 0
                p = pb.parent
                while p:
                    depth += 1
                    p = p.parent
                return depth
                
            sorted_bones = sorted(selected_bones, key=get_depth)
            
            # Rename them
            for i, pb in enumerate(sorted_bones):
                pb.name = f"{base_name}_{i + 1}"
                
        elif mode == 'EDIT':
            selected_bones = context.selected_editable_bones
            if not selected_bones:
                self.report({'WARNING'}, "No bones selected in Edit Mode.")
                return {'CANCELLED'}
                
            # Helper to get overall depth of an EditBone
            def get_depth(eb):
                depth = 0
                p = eb.parent
                while p:
                    depth += 1
                    p = p.parent
                return depth
                
            sorted_bones = sorted(selected_bones, key=get_depth)
            
            # Rename them
            for i, eb in enumerate(sorted_bones):
                eb.name = f"{base_name}_{i + 1}"
                
        self.report({'INFO'}, f"Renamed {len(sorted_bones)} bones to '{base_name}_#'")
        return {'FINISHED'}
