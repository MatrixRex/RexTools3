import bpy
from bpy.types import Operator

class REX_OT_InitChainConstraintTemplate(Operator):
    """Create a template constraint on the active bone to configure settings"""
    bl_idname = "rex.init_chain_constraint_template"
    bl_label = "Setup Options"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE' and 
                context.active_pose_bone)

    def execute(self, context):
        props = context.scene.chain_constraints_props
        # Trigger the update logic manually
        # Since update_constraint_type is in properties.py, we can just call it
        # but to be safe we'll re-implement or call it here if possible.
        # It's better to just ensure the constraint exists.
        
        pb = context.active_pose_bone
        con_name = "REX_TEMPLATE"
        con = pb.constraints.get(con_name)
        
        if con and con.type != props.constraint_type:
            pb.constraints.remove(con)
            con = None
            
        if not con:
            con = pb.constraints.new(type=props.constraint_type)
            con.name = con_name
        
        con.mute = True
        return {'FINISHED'}


class REX_OT_RemoveAllBoneConstraints(Operator):
    """Remove all constraints from selected bones"""
    bl_idname = "rex.remove_all_bone_constraints"
    bl_label = "Remove All Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE' and 
                context.selected_pose_bones)

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        removed_count = 0
        
        for pb in selected_bones:
            # We must iterate backwards or over a copy because remove() 
            # modifies the collection size
            for con in list(pb.constraints):
                pb.constraints.remove(con)
                removed_count += 1
        
        self.report({'INFO'}, f"Removed {removed_count} constraints from {len(selected_bones)} bones")
        return {'FINISHED'}


class REX_OT_ChainConstraintsAdder(Operator):
    """Add a chain of constraints to selected bones"""
    bl_idname = "rex.chain_constraints_adder"
    bl_label = "Add Chain Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and 
                context.mode == 'POSE' and
                len(context.selected_pose_bones) > 1)

    def execute(self, context):
        props = context.scene.chain_constraints_props
        armature = context.active_object
        selected_bones = context.selected_pose_bones
        
        # Identify hierarchy within selection
        selected_bone_names = [b.name for b in selected_bones]
        
        # Sort bones by hierarchy
        # We can sort them by the number of parents they have in the selection
        def get_selection_depth(pb):
            depth = 0
            curr = pb.parent
            while curr:
                if curr.name in selected_bone_names:
                    depth += 1
                curr = curr.parent
            return depth

        # Sort selected bones: Root (depth 0) to Tip (depth N)
        sorted_bones = sorted(selected_bones, key=get_selection_depth)
        
        if len(sorted_bones) < 2:
            self.report({'WARNING'}, "Select at least 2 connected bones")
            return {'CANCELLED'}

        # Daisy-chain logic
        # Example: b1, b2, b3, b4
        # From Tip: (b3,b4), (b2,b3), (b1,b2)
        # From Root: (b2,b1), (b3,b2), (b4,b3)

        pairs = []
        if props.direction == 'FROM_TIP':
            # actionable: b3, b2, b1
            # targets: b4, b3, b2
            for i in range(len(sorted_bones) - 1, 0, -1):
                bone = sorted_bones[i-1]
                target = sorted_bones[i]
                pairs.append((bone, target))
        else: # FROM_ROOT
            # actionable: b2, b3, b4
            # targets: b1, b2, b3
            for i in range(1, len(sorted_bones)):
                bone = sorted_bones[i]
                target = sorted_bones[i-1]
                pairs.append((bone, target))

        influence_step = props.influence_value
        num_constraints = len(pairs)
        
        def copy_constraint_props(src, dst):
            # List of attributes to skip (manually handled or internal)
            skip = {'name', 'type', 'target', 'subtarget', 'influence', 'mute'}
            for attr in dir(src):
                if attr.startswith("_") or attr in skip:
                    continue
                try:
                    setattr(dst, attr, getattr(src, attr))
                except (AttributeError, TypeError):
                    # Some attributes are read-only or not applicable
                    pass

        # Find template constraint
        template_con = context.active_pose_bone.constraints.get("REX_TEMPLATE")
        
        for i, (pb, target_pb) in enumerate(pairs):
            con = pb.constraints.new(type=props.constraint_type)
            
            # Copy settings from template if it exists
            if template_con:
                copy_constraint_props(template_con, con)
            
            con.target = armature
            con.subtarget = target_pb.name
            con.mute = False # Ensure the new one is active
            
            if props.mode == 'DECREASE':
                influence = 1.0 - (i * influence_step)
            elif props.mode == 'INCREASE':
                influence = (i + 1) * influence_step
            else: # FROM_TO
                if num_constraints > 1:
                    t = i / (num_constraints - 1)
                else:
                    t = 0
                influence = props.influence_from + t * (props.influence_to - props.influence_from)
                
            con.influence = max(0.0, min(1.0, influence))

        # Cleanup template constraint
        active_pb = context.active_pose_bone
        if active_pb:
            con = active_pb.constraints.get("REX_TEMPLATE")
            if con:
                active_pb.constraints.remove(con)

        self.report({'INFO'}, f"Added {len(pairs)} constraints")
        return {'FINISHED'}
