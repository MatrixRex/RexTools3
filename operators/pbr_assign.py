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
        # ensure nodes
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return False

        # load image
        try:
            image = bpy.data.images.load(image_path)
        except:
            return False

        # always pack alpha for base color
        if input_name == 'Base Color':
            image.alpha_mode = 'CHANNEL_PACKED'
        image.colorspace_settings.name = colorspace

        # gather and remove existing chain
        def gather(n, out):
            if n in out:
                return
            out.add(n)
            for inp in n.inputs:
                if inp.is_linked:
                    gather(inp.links[0].from_node, out)

        inp_socket = principled.inputs.get(input_name)
        if inp_socket and inp_socket.is_linked:
            to_remove = set()
            gather(inp_socket.links[0].from_node, to_remove)
            # unlink from BSDF
            for link in list(inp_socket.links):
                links.remove(link)
            # delete nodes
            for n in to_remove:
                if n in nodes:
                    nodes.remove(n)

        use_sep = getattr(material.pbr_settings, 'use_separate_alpha_map', False)

        # create image texture node
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
            # texture → mix Color1
            links.new(tex_node.outputs['Color'], mix.inputs['Color1'])
            # tint → mix Color2
            mix.inputs['Color2'].default_value = principled.inputs['Base Color'].default_value
            links.new(mix.outputs['Color'], principled.inputs['Base Color'])
            if not use_sep:
                links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'BLEND'

        else:  # Roughness, Metallic
            math = nodes.new('ShaderNodeMath')
            math.operation = 'MULTIPLY'
            math.location = (-200, 0)
            links.new(tex_node.outputs['Color'], math.inputs[0])
            math.inputs[1].default_value = principled.inputs[input_name].default_value
            links.new(math.outputs['Value'], principled.inputs[input_name])

        return True
