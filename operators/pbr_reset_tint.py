# operators/pbr_reset_tint.py
import bpy
from bpy.types import Operator

class PBR_OT_ResetTint(Operator):
    """Reset Base Color tint to white"""
    bl_idname = "pbr.reset_tint"
    bl_label = "Reset Tint"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            return {'CANCELLED'}
        mat = obj.active_material
        if not mat.use_nodes:
            return {'CANCELLED'}

        nodes = mat.node_tree.nodes
        # find the mix node driving Base Color
        principled = next((n for n in nodes if n.type=='BSDF_PRINCIPLED'), None)
        if not principled:
            return {'CANCELLED'}

        base_inp = principled.inputs.get('Base Color')
        if base_inp.is_linked:
            mix = base_inp.links[0].from_node
            if mix.type == 'MIX_RGB':
                mix.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
                return {'FINISHED'}

        # fallback: reset the default Base Color
        principled.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        return {'FINISHED'}
