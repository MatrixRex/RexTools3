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
        # Clear debug preview if active
        bpy.ops.pbr.clear_debug_preview()

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
            # AO is special: it's a Mix node in the Base Color chain
            ao_mix = nodes.get("AOMix")
            if ao_mix:
                # Modern Mix node: Output is 'Result', Input chain is 'A'
                out_sock = ao_mix.outputs.get('Result') or ao_mix.outputs[0]
                a_sock = ao_mix.inputs.get('A') or ao_mix.inputs[1] 
                b_sock = ao_mix.inputs.get('B') or ao_mix.inputs[2]
                
                out_links = list(out_sock.links) if out_sock else []
                a_links = list(a_sock.links) if a_sock else []
                
                # Reconnect A directly to the target (BSDF)
                if a_links and out_links:
                    upstream_socket = a_links[0].from_socket
                    for link in out_links:
                        links.new(upstream_socket, link.to_socket)
                
                # Now remove the AO chain (Mix node + anything behind B)
                to_remove = {ao_mix}
                if b_sock and b_sock.is_linked:
                    # Gather AO texture and helper nodes
                    def gather_local(node, out):
                        if node in out: return
                        out.add(node)
                        for i in node.inputs:
                            if i.is_linked:
                                gather_local(i.links[0].from_node, out)
                    
                    gather_local(b_sock.links[0].from_node, to_remove)
                
                # Clean up specifically named helper nodes if they weren't caught
                for name in ["AOSplit", "AOAdd", "AOMath"]:
                    node = nodes.get(name)
                    if node: to_remove.add(node)

                for node in to_remove:
                    try: nodes.remove(node)
                    except: pass
            return {'FINISHED'}

        if self.input_name == 'Emission':
            inp_socket = principled.inputs.get('Emission Color')
        else:
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
        for node_name in (f"{self.input_name}Split", f"{self.input_name}Math", "EmissionTintMix"):
            leftover = nodes.get(node_name)
            if leftover:
                try:
                    nodes.remove(leftover)
                except RuntimeError:
                    pass

        return {'FINISHED'}
