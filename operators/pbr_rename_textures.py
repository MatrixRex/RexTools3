import bpy
from bpy.types import Operator
from ..core import notify

class PBR_OT_RenameTextures(Operator):
    bl_idname = "pbr.rename_textures"
    bl_label = "Rename Textures"
    bl_description = "Rename assigned texture data-blocks to match the material name and their PBR slot role"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.active_material

    def execute(self, context):
        mat = context.active_object.active_material
        if not mat or not mat.use_nodes:
            self.report({'ERROR'}, "Active material does not use nodes")
            return {'CANCELLED'}

        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            self.report({'ERROR'}, "No Principled BSDF found in material")
            return {'CANCELLED'}

        def find_texture_node(node):
            """Finds the first Image Texture node in the chain starting from node."""
            visited = set()
            current = node
            while current and current not in visited:
                visited.add(current)
                if current.type == 'TEX_IMAGE':
                    return current
                
                # Follow the first linked input, prioritizing common texture inputs
                next_node = None
                for name in ['Color', 'Color1', 'Value', 'Image']:
                    inp = current.inputs.get(name)
                    if inp and inp.is_linked:
                        next_node = inp.links[0].from_node
                        break
                
                if not next_node:
                    for inp in current.inputs:
                        if inp.is_linked:
                            next_node = inp.links[0].from_node
                            break
                current = next_node
            return None

        # Gather images assigned to slots
        slots = {} # slot_role -> Image object

        # 1. Base Color -> Color
        bc_inp = principled.inputs.get("Base Color")
        if bc_inp and bc_inp.is_linked:
            curr = bc_inp.links[0].from_node
            src_node = None
            while curr:
                if curr.name == "BaseTex":
                    src_node = curr
                    break
                if curr.name == "BaseTintMix":
                    a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                    if a_sock and a_sock.is_linked:
                        curr = a_sock.links[0].from_node
                        continue
                if curr.name == "AOMix":
                    a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                    if a_sock and a_sock.is_linked:
                        curr = a_sock.links[0].from_node
                        continue
                if curr.type == 'TEX_IMAGE' and curr.name != "AOTex":
                    src_node = curr
                    break
                break
            if src_node:
                tex_node = find_texture_node(src_node)
                if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                    slots["Color"] = tex_node.image

        # 2. Normal -> Normal
        norm_inp = principled.inputs.get("Normal")
        if norm_inp and norm_inp.is_linked:
            tex_node = find_texture_node(norm_inp.links[0].from_node)
            if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                slots["Normal"] = tex_node.image

        # 3. Roughness -> Roughness
        rough_inp = principled.inputs.get("Roughness")
        if rough_inp and rough_inp.is_linked:
            tex_node = find_texture_node(rough_inp.links[0].from_node)
            if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                slots["Roughness"] = tex_node.image

        # 4. Metallic -> Metallic
        metal_inp = principled.inputs.get("Metallic")
        if metal_inp and metal_inp.is_linked:
            tex_node = find_texture_node(metal_inp.links[0].from_node)
            if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                slots["Metallic"] = tex_node.image

        # 5. Emission -> Emission
        em_inp = principled.inputs.get("Emission Color")
        if em_inp and em_inp.is_linked:
            curr = em_inp.links[0].from_node
            src_node = None
            if curr.name == "EmissionTintMix":
                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                if a_sock and a_sock.is_linked:
                    src_node = a_sock.links[0].from_node
            else:
                src_node = curr
            if src_node:
                tex_node = find_texture_node(src_node)
                if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                    slots["Emission"] = tex_node.image

        # 6. Height -> Height
        disp_node = nodes.get("HeightDisplace")
        if disp_node:
            h_sock = disp_node.inputs.get('Height')
            if h_sock and h_sock.is_linked:
                tex_node = find_texture_node(h_sock.links[0].from_node)
                if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                    slots["Height"] = tex_node.image

        # 7. Alpha -> Alpha
        alpha_inp = principled.inputs.get("Alpha")
        if alpha_inp and alpha_inp.is_linked:
            tex_node = find_texture_node(alpha_inp.links[0].from_node)
            if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                slots["Alpha"] = tex_node.image

        # 8. AO -> AO
        ao_mix = nodes.get("AOMix")
        bc_inp = principled.inputs.get("Base Color")
        if ao_mix and bc_inp and bc_inp.is_linked:
            curr = bc_inp.links[0].from_node
            src_node = None
            while curr:
                if curr == ao_mix:
                    b_sock = curr.inputs.get('B') or curr.inputs[2]
                    if b_sock and b_sock.is_linked:
                        src_node = b_sock.links[0].from_node
                    break
                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                curr = a_sock.links[0].from_node if a_sock and a_sock.is_linked else None
            if src_node:
                tex_node = find_texture_node(src_node)
                if tex_node and tex_node.type == 'TEX_IMAGE' and tex_node.image:
                    slots["AO"] = tex_node.image

        if not slots:
            self.report({'INFO'}, "No textures found assigned to standard PBR slots")
            return {'CANCELLED'}

        # Group roles by Image data block to handle shared / packed textures nicely
        image_to_roles = {}
        for role, img in slots.items():
            image_to_roles.setdefault(img, []).append(role)

        # Standard role order for joining multiple roles nicely
        role_order = {
            'Color': 0,
            'Normal': 1,
            'Roughness': 2,
            'Metallic': 3,
            'Emission': 4,
            'Height': 5,
            'Alpha': 6,
            'AO': 7
        }

        renamed_count = 0
        mat_name = mat.name

        for img, roles in image_to_roles.items():
            # If there are multiple roles, sort them or use common packing abbreviations
            roles_set = set(roles)
            if roles_set == {'AO', 'Roughness', 'Metallic'}:
                suffix = "ORM"
            elif roles_set == {'Roughness', 'Metallic'}:
                suffix = "RM"
            elif roles_set == {'AO', 'Roughness'}:
                suffix = "OR"
            elif roles_set == {'Color', 'Alpha'}:
                suffix = "Color"
            else:
                # Sort according to role_order
                sorted_roles = sorted(roles, key=lambda r: role_order.get(r, 99))
                suffix = "_".join(sorted_roles)

            new_name = f"{mat_name}_{suffix}"
            if img.name != new_name:
                img.name = new_name
                renamed_count += 1

        if renamed_count > 0:
            notify.success(f"Renamed {renamed_count} texture(s) to match '{mat_name}_[Role]'")
        else:
            notify.info("Textures are already correctly named")

        return {'FINISHED'}
