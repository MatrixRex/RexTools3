# operators/pbr_assign.py  (full replacement) :contentReference[oaicite:3]{index=3}

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
        mat = context.active_object.active_material
        if not mat:
            self.report({'ERROR'}, "No active material")
            return {'CANCELLED'}

        ok = self.assign_texture_to_input(mat, self.input_name, self.filepath, self.colorspace)
        if not ok:
            self.report({'ERROR'}, "Failed to assign texture")
            return {'CANCELLED'}

        bpy.ops.pbr.arrange_nodes()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @staticmethod
    def assign_texture_to_input(material, input_name, image_path, colorspace='sRGB'):
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = next((n for n in nodes if n.type=='BSDF_PRINCIPLED'), None)
        if not principled:
            return False

        try:
            image = bpy.data.images.load(image_path)
        except:
            return False

        if input_name == 'Base Color':
            image.alpha_mode = 'CHANNEL_PACKED'
        image.colorspace_settings.name = colorspace

        # remove old chain
        def gather(n, out):
            if n in out: return
            out.add(n)
            for i in n.inputs:
                if i.is_linked:
                    gather(i.links[0].from_node, out)
        inp_sock = principled.inputs[input_name]
        if inp_sock.is_linked:
            to_del = set()
            gather(inp_sock.links[0].from_node, to_del)
            for l in list(inp_sock.links):
                links.remove(l)
            for n in to_del:
                try: nodes.remove(n)
                except: pass

        base_pos = {
            'Base Color': 200,
            'Metallic':   100,
            'Roughness':    0,
            'Normal':     -100,
            'Alpha':      -200,
        }
        y = base_pos.get(input_name, 0)
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-400, y)
        tex_node.name = f"PBR Tex {input_name}"

        # Handle each socket
        settings = material.pbr_settings

        if input_name == 'Normal':
            nm = nodes.new('ShaderNodeNormalMap')
            nm.location = (-150, y)
            links.new(tex_node.outputs['Color'], nm.inputs['Color'])
            links.new(nm.outputs['Normal'], principled.inputs['Normal'])
            return True

        if input_name == 'Alpha':
            links.new(tex_node.outputs['Color'], principled.inputs['Alpha'])
            material.blend_method = 'BLEND'
            return True

        if input_name == 'Base Color':
            mix = nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Fac'].default_value = 1.0
            mix.location = (-150, y)
            links.new(tex_node.outputs['Color'], mix.inputs['Color1'])
            tint = principled.inputs['Base Color'].default_value
            mix.inputs['Color2'].default_value = (
                max(0, min(tint[0],1)),
                max(0, min(tint[1],1)),
                max(0, min(tint[2],1)),
                max(0, min(tint[3],1)),
            )
            links.new(mix.outputs['Color'], principled.inputs['Base Color'])
            if not settings.use_separate_alpha_map:
                links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'HASHED'
            return True

        # Roughness / Metallic (always via Math node)
        math = nodes.new('ShaderNodeMath')
        math.operation = 'MULTIPLY'
        math.location = (-150, y)
        math.name = f"PBR Math {input_name}"
        # decide channel now or later on update
        chan = getattr(settings, f"{input_name.lower()}_channel")
        if chan == 'FULL':
            links.new(tex_node.outputs['Color'], math.inputs[0])
        else:
            if chan == 'A':
                src = tex_node.outputs['Alpha']
            else:
                sep = nodes.new('ShaderNodeSeparateRGB')
                sep.name = f"PBR Sep {input_name}"
                sep.location = (-250, y)
                links.new(tex_node.outputs['Color'], sep.inputs['Image'])
                src = sep.outputs[chan]
            links.new(src, math.inputs[0])
        math.inputs[1].default_value = getattr(settings, f"{input_name.lower()}_strength")
        links.new(math.outputs['Value'], principled.inputs[input_name])
        return True
