# operators/pbr_remove.py
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

        mat = obj.active_material
        mat.use_nodes = True
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        # Find Principled BSDF
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            self.report({'WARNING'}, "No Principled BSDF found")
            return {'CANCELLED'}

        inp_socket = principled.inputs.get(self.input_name)
        if not inp_socket or not inp_socket.is_linked:
            return {'FINISHED'}

        # Recursively gather all nodes feeding into this socket
        to_remove = set()
        def gather(node):
            if node in to_remove:
                return
            to_remove.add(node)
            for inp in node.inputs:
                if inp.is_linked:
                    upstream = inp.links[0].from_node
                    gather(upstream)

        # Start gathering from the node linked into this socket
        first_node = inp_socket.links[0].from_node
        gather(first_node)

        # Unlink the BSDF socket
        for link in list(inp_socket.links):
            links.remove(link)

        # Delete all gathered nodes, ignoring any that are gone already
        for node in to_remove:
            try:
                nodes.remove(node)
            except RuntimeError:
                pass  # node already removed or never existed in this tree

        return {'FINISHED'}
