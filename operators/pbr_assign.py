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
        if obj and obj.active_material:
            success = self.assign_texture_to_input(
                obj.active_material,
                self.input_name,
                self.filepath,
                self.colorspace
            )
            if success:
                self.report({'INFO'}, f"Assigned texture to {self.input_name}")
            else:
                self.report({'ERROR'}, "Failed to assign texture")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @staticmethod
    def assign_texture_to_input(material, input_name, image_path, colorspace='sRGB'):
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            return False

        try:
            image = bpy.data.images.load(image_path)
        except:
            return False

        # always pack alpha on Base Color imports
        if input_name == 'Base Color':
            image.alpha_mode = 'CHANNEL_PACKED'
        image.colorspace_settings.name = colorspace

        # remove existing node on this socket
        inp = principled.inputs.get(input_name)
        if inp and inp.is_linked:
            old = inp.links[0].from_node
            if old.type == 'TEX_IMAGE':
                nodes.remove(old)
            elif old.type == 'NORMAL_MAP':
                col_link = old.inputs.get('Color')
                if col_link and col_link.is_linked:
                    tex = col_link.links[0].from_node
                    if tex.type == 'TEX_IMAGE':
                        nodes.remove(tex)
                nodes.remove(old)

        # create new Image Texture node
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-400, 0)

        use_sep = getattr(material.pbr_settings, 'use_separate_alpha_map', False)

        if input_name == 'Normal':
            nm = nodes.new('ShaderNodeNormalMap')
            nm.location = (-200, 0)
            links.new(tex_node.outputs['Color'], nm.inputs['Color'])
            links.new(nm.outputs['Normal'], principled.inputs['Normal'])

        elif input_name == 'Alpha':
            links.new(tex_node.outputs['Color'], principled.inputs['Alpha'])
            material.blend_method = 'HASHED'

        else:  # Base Color, Roughness, Metallic, etc.
            links.new(tex_node.outputs['Color'], principled.inputs[input_name])
            # if Base Color & not using separate, also hook its alpha
            if input_name == 'Base Color' and not use_sep:
                links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'HASHED'

        return True
