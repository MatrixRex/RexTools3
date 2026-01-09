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

        if self.input_name == 'AO':
            # AO is special: it's a MixRGB node in the Base Color chain
            ao_mix = nodes.get("PBR AO Mix")
            if ao_mix:
                # Find where it's connected (likely Principled BSDF or another MixRGB)
                out_links = list(ao_mix.outputs['Color'].links)
                c1_links = list(ao_mix.inputs['Color1'].links)
                
                # Reconnect Color1 directly to the target
                if c1_links and out_links:
                    upstream_socket = c1_links[0].from_socket
                    for link in out_links:
                        links.new(upstream_socket, link.to_socket)
                
                # Now remove the AO chain
                to_remove = {ao_mix}
                math_node = nodes.get("PBR Math AO")
                if math_node:
                    to_remove.add(math_node)
                    if math_node.inputs[0].is_linked:
                        gather(math_node.inputs[0].links[0].from_node, to_remove)
                    sep_node = nodes.get("PBR Sep AO")
                    if sep_node: to_remove.add(sep_node)
                
                for node in to_remove:
                    try: nodes.remove(node)
                    except: pass
            return {'FINISHED'}

        inp_socket = principled.inputs.get(self.input_name)
        if not inp_socket or not inp_socket.is_linked:
            return {'FINISHED'}

        # Recursively gather all nodes feeding into this socket
        to_del = set()
        def gather_rec(node):
            if node in to_del:
                return
            to_del.add(node)
            for inp in node.inputs:
                if inp.is_linked:
                    upstream = inp.links[0].from_node
                    gather_rec(upstream)

        # Start gathering from the node linked into this socket
        first_node = inp_socket.links[0].from_node
        gather_rec(first_node)

        # Unlink the BSDF socket
        for link in list(inp_socket.links):
            links.remove(link)

        # Delete all gathered nodes, ignoring any that are gone already
        for node in to_del:
            try:
                nodes.remove(node)
            except RuntimeError:
                pass

        # ─── Cleanup any leftover channel-packing nodes ───────────────────
        # Remove our named SeparateRGB and Math nodes if they remain
        for node_name in (f"PBR Sep {self.input_name}", f"PBR Math {self.input_name}"):
            leftover = nodes.get(node_name)
            if leftover:
                try:
                    nodes.remove(leftover)
                except RuntimeError:
                    pass

        return {'FINISHED'}
