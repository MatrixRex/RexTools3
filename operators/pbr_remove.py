import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class PBR_OT_RemoveTexture(Operator):
    bl_idname = "pbr.remove_texture"
    bl_label = "Remove Texture"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'WARNING'}, "No active material")
            return {'CANCELLED'}

        material = obj.active_material
        material.use_nodes = True
        nodes = material.node_tree.nodes

        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            self.report({'WARNING'}, "No Principled BSDF found")
            return {'CANCELLED'}

        input_socket = principled.inputs.get(self.input_name)
        if input_socket and input_socket.is_linked:
            connected_node = input_socket.links[0].from_node
            if connected_node.type == 'TEX_IMAGE':
                nodes.remove(connected_node)
            elif connected_node.type in ['NORMAL_MAP', 'SEPARATE_COLOR']:
                tex_node = self.find_texture_in_chain(connected_node)
                if tex_node:
                    nodes.remove(tex_node)
                if connected_node.type == 'NORMAL_MAP':
                    nodes.remove(connected_node)

        return {'FINISHED'}

    def find_texture_in_chain(self, node):
        if node.type == 'TEX_IMAGE':
            return node
        for input_socket in node.inputs:
            if input_socket.is_linked:
                return self.find_texture_in_chain(input_socket.links[0].from_node)
        return None
