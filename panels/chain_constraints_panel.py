import bpy
from bpy.types import Panel

class REXTOOLS3_PT_ChainConstraintsAdder(Panel):
    bl_label = "Chain Constrains Adder"
    bl_idname = "REXTOOLS3_PT_chain_constraints_adder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RexTools3"
    bl_context = "posemode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.chain_constraints_props

        box = layout.box()
        
        col = box.column(align=True)
        col.prop(props, "constraint_type")
        
        row = col.row(align=True)
        row.prop(props, "mode", expand=True)
        
        if props.mode == 'FROM_TO':
            sub = col.row(align=True)
            sub.prop(props, "influence_from")
            sub.prop(props, "influence_to")
        else:
            row.prop(props, "influence_value", text="")
        
        col.prop(props, "direction", expand=True)
        
        # Draw template constraint UI
        pb = context.active_pose_bone
        if pb:
            template_con = pb.constraints.get("REX_TEMPLATE")
            if template_con:
                box = layout.box()
                box.label(text=f"Options (on {pb.name}):", icon='PROPERTIES')
                # Trying with only the keyword argument as the error suggested it takes at most 1 arg
                box.template_constraints(use_bone_constraints=True)
            else:
                box = layout.box()
                box.label(text=f"Configure on {pb.name}:")
                box.operator("rex.init_chain_constraint_template", text="Setup Constraints Options", icon='ADD')
        else:
            layout.label(text="Select a bone to configure options", icon='INFO')
        
        layout.separator()
        layout.operator("rex.chain_constraints_adder", text="Execute", icon='PLAY')

        layout.separator()
        layout.operator("rex.remove_all_bone_constraints", text="Remove All Constraints", icon='X')
