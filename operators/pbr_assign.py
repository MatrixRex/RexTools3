# operators/pbr_assign.py
import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class PBR_OT_AssignTexture(Operator):
    bl_idname = "pbr.assign_texture"
    bl_label = "Assign Texture"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()
    colorspace: StringProperty(default='sRGB')
    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, "No active material")
            return {'CANCELLED'}
        success = self.assign_texture_to_input(
            obj.active_material,
            self.input_name,
            self.filepath,
            self.colorspace
        )
        if not success:
            self.report({'ERROR'}, "Failed to assign texture")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @staticmethod
    def assign_texture_to_input(material, input_name, image_path, colorspace='sRGB'):
        # Ensure node-based material
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find Principled BSDF
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return False

        # Load the image
        try:
            image = bpy.data.images.load(image_path)
        except:
            return False

        # Always pack alpha for Base Color
        if input_name == 'Base Color':
            image.alpha_mode = 'CHANNEL_PACKED'
        image.colorspace_settings.name = colorspace

        # Helper to gather all upstream nodes
        def gather(node, out):
            if node in out:
                return
            out.add(node)
            for inp in node.inputs:
                if inp.is_linked:
                    gather(inp.links[0].from_node, out)

        # Remove existing chain feeding this socket
        inp_socket = principled.inputs.get(input_name)
        if inp_socket and inp_socket.is_linked:
            to_remove = set()
            gather(inp_socket.links[0].from_node, to_remove)
            for link in list(inp_socket.links):
                links.remove(link)
            for n in to_remove:
                try:
                    nodes.remove(n)
                except RuntimeError:
                    pass

        use_sep = getattr(material.pbr_settings, 'use_separate_alpha_map', False)

        # Create Image Texture node
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-400, 0)

        if input_name == 'Normal':
            nm = nodes.new('ShaderNodeNormalMap')
            nm.location = (-200, 0)
            links.new(tex_node.outputs['Color'], nm.inputs['Color'])
            links.new(nm.outputs['Normal'], principled.inputs['Normal'])

        elif input_name == 'Alpha':
            links.new(tex_node.outputs['Color'], principled.inputs['Alpha'])
            material.blend_method = 'BLEND'

        elif input_name == 'Base Color':
            mix = nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Fac'].default_value = 1.0
            mix.location = (-200, 0)
            # Texture → Mix Color1
            links.new(tex_node.outputs['Color'], mix.inputs['Color1'])
            # Tint → Mix Color2 (clamped)
            tint = principled.inputs['Base Color'].default_value
            mix.inputs['Color2'].default_value = (
                max(0.0, min(tint[0], 1.0)),
                max(0.0, min(tint[1], 1.0)),
                max(0.0, min(tint[2], 1.0)),
                max(0.0, min(tint[3], 1.0)),
            )
            links.new(mix.outputs['Color'], principled.inputs['Base Color'])
            if not use_sep:
                links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'BLEND'

        else:  # Roughness or Metallic
            math = nodes.new('ShaderNodeMath')
            math.operation = 'MULTIPLY'
            math.location = (-200, 0)
            # Texture → Math input 0
            links.new(tex_node.outputs['Color'], math.inputs[0])
            # Clamp the slider default to [0,1]
            default_val = principled.inputs[input_name].default_value
            clamped_val = max(0.0, min(default_val, 1.0))
            math.inputs[1].default_value = clamped_val
            links.new(math.outputs['Value'], principled.inputs[input_name])

        return True
