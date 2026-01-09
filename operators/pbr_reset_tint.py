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
        # 1. Look for the named Tint node directly
        tint_node = nodes.get("BaseTintMix")
        
        # 2. Fallback: Crawl the Base Color chain to find a Mix/MixRGB node
        if not tint_node:
            principled = next((n for n in nodes if n.type=='BSDF_PRINCIPLED'), None)
            if principled:
                inp = principled.inputs.get('Base Color')
                if inp and inp.is_linked:
                    curr = inp.links[0].from_node
                    while curr:
                        if curr.name == "AOMix":
                            # Go behind AO
                            a_sock = curr.inputs.get('A') or curr.inputs[1]
                            curr = a_sock.links[0].from_node if a_sock.is_linked else None
                            continue
                        if curr.type in ('MIX_RGB', 'MIX'):
                            tint_node = curr
                            break
                        break
        
        # Reset the tint node if found
        if tint_node:
            # Modern Mix uses 'B', old MixRGB uses 'Color2'
            sock = tint_node.inputs.get('B') or tint_node.inputs.get('Color2')
            if sock:
                sock.default_value = (1.0, 1.0, 1.0, 1.0)
                return {'FINISHED'}

        # Final fallback: reset the default Base Color socket value
        principled = next((n for n in nodes if n.type=='BSDF_PRINCIPLED'), None)
        if principled:
            principled.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            
        return {'FINISHED'}
