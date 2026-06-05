import bpy
from bpy.types import Operator
from .pbr_assign import _get_principled_and_base_tex
from ..core import notify

class PBR_OT_SetViewportColor(Operator):
    """Set material viewport display color from base color"""
    bl_idname = "pbr.set_viewport_color"
    bl_label = "Set Viewport Color"
    bl_description = "Update the viewport display color to match the base color of the active material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.active_material is not None

    def execute(self, context):
        mat = context.active_object.active_material
        if not mat:
            notify.error("No active material found")
            return {'CANCELLED'}

        if not mat.use_nodes:
            # For non-node materials, viewport color is already the main display color
            notify.warning("Material does not use nodes; viewport color matches diffuse color by default")
            return {'FINISHED'}

        nodes = mat.node_tree.nodes
        principled, base_tex, base_img = _get_principled_and_base_tex(mat)

        if not principled:
            notify.warning("No Principled BSDF node found in material")
            return {'CANCELLED'}

        # Default color
        color = [1.0, 1.0, 1.0, 1.0]

        # 1. Get base color from texture or default socket value
        if base_img:
            # Sample pixels
            try:
                width, height = base_img.size
                if width > 0 and height > 0:
                    grid_size = 16
                    r_sum, g_sum, b_sum, a_sum = 0.0, 0.0, 0.0, 0.0
                    count = 0
                    pixels = base_img.pixels
                    
                    # Sample a grid of pixels to calculate average color
                    for y in range(grid_size):
                        py = int((y + 0.5) * height / grid_size)
                        for x in range(grid_size):
                            px = int((x + 0.5) * width / grid_size)
                            idx = (py * width + px) * 4
                            r_sum += pixels[idx]
                            g_sum += pixels[idx+1]
                            b_sum += pixels[idx+2]
                            a_sum += pixels[idx+3]
                            count += 1
                            
                    if count > 0:
                        color = [r_sum / count, g_sum / count, b_sum / count, a_sum / count]
            except Exception as e:
                # Log to console and fall back to white
                print(f"Set Viewport Color: Failed to sample image pixels ({e})")
                color = [1.0, 1.0, 1.0, 1.0]
        else:
            bc_inp = principled.inputs.get('Base Color')
            if bc_inp:
                color = list(bc_inp.default_value)

        # 2. Check for BaseTintMix and multiply color by tint color
        tint_node = nodes.get("BaseTintMix")
        if tint_node:
            tint_sock = tint_node.inputs.get('B') or tint_node.inputs.get('Color2')
            if tint_sock:
                tint_val = tint_sock.default_value
                color[0] *= tint_val[0]
                color[1] *= tint_val[1]
                color[2] *= tint_val[2]
                color[3] *= tint_val[3]

        # 3. Apply the calculated color to material viewport color
        mat.diffuse_color = tuple(color)

        # 4. Also match viewport metallic and roughness if properties exist
        if hasattr(mat, "metallic"):
            met_inp = principled.inputs.get('Metallic')
            if met_inp and not met_inp.is_linked:
                mat.metallic = met_inp.default_value
            elif met_inp and met_inp.is_linked:
                # If metallic is driven by a texture, set a neutral high viewport metallic
                # or default to a reasonable value
                mat.metallic = 0.5
        
        if hasattr(mat, "roughness"):
            rough_inp = principled.inputs.get('Roughness')
            if rough_inp and not rough_inp.is_linked:
                mat.roughness = rough_inp.default_value
            elif rough_inp and rough_inp.is_linked:
                # If roughness is driven by a texture, set a neutral viewport roughness
                mat.roughness = 0.5

        notify.success(f"Set viewport color from base color")
        return {'FINISHED'}
