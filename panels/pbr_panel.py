import bpy
from bpy.types import Panel

# Define the panel class
class PBR_PT_MaterialPanel(Panel):
    bl_label = "Easy PBR"
    bl_idname = "PBR_PT_material_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_category = "PBR Tools"  # This ensures the panel appears under the "PBR Tools" tab

    def find_texture_node(self, node):
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

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if not obj:
            layout.label(text="No active object")
            return

        mat = obj.active_material
        if not mat:
            layout.operator("pbr.create_material", icon='ADD')
            return

        # Header: separate-alpha toggle
        box = layout.box()
        box.prop(mat.pbr_settings, "use_separate_alpha_map", text="Use Separate Alpha Map")
        layout.separator()

        # Ensure nodes
        if not mat.use_nodes:
            layout.operator("pbr.create_material", text="Enable Nodes", icon='NODETREE')
            return

        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            layout.label(text="No Principled BSDF found")
            layout.operator("pbr.create_material", text="Setup PBR Material", icon='MATERIAL')
            return

        # Top row: material name + arrange button + auto-load button
        row = layout.row(align=True)
        row.prop(mat, "name", text="Material")
        row.operator("pbr.arrange_nodes", text="", icon='NODETREE')

        # Auto Load toggle and input field
        row = layout.row(align=True)
        row.operator("pbr.auto_load_textures", text="Auto Load", icon='FILE_REFRESH')

        auto_load_toggle = layout.prop(mat.pbr_settings, "use_auto_common_name", text="Use Auto-Detected Name", toggle=True)
        if not mat.pbr_settings.use_auto_common_name:
            layout.prop(mat.pbr_settings, "common_name", text="Common Name")

        layout.separator()

        # Build our list of sockets
        inputs = [
            ("Base Color", "Base Color", "sRGB"),
            ("Normal",     "Normal",     "Non-Color"),
            ("Roughness",  "Roughness",  "Non-Color"),
            ("Metallic",   "Metallic",   "Non-Color"),
        ]
        if mat.pbr_settings.use_separate_alpha_map:
            inputs.append(("Alpha", "Alpha", "Non-Color"))

        # Draw each socket block
        for label, socket, colorspace in inputs:
            box = layout.box()
            row = box.row()
            row.label(text=label, icon='TEXTURE')
            
            # Use try-except or check principled.inputs.get(socket) to be safe
            inp = principled.inputs.get(socket)
            if not inp:
                continue

            # If already linked, show remove + controls
            if inp.is_linked:
                row.operator("pbr.remove_texture", text="", icon='X').input_name = socket
                src_node = inp.links[0].from_node

                # Find the texture node by crawling the chain
                tex_node = self.find_texture_node(src_node)
                if tex_node and tex_node.type == 'TEX_IMAGE':
                    name = tex_node.image.name if tex_node.image else "No Image"
                else:
                    name = src_node.type.replace('_', ' ').title()
                
                box.label(text=f"Texture: {name}")

                # Per-socket extra controls
                if socket == "Base Color" and src_node.type == 'MIX_RGB':
                    r = box.row(align=True)
                    r.prop(src_node.inputs['Color2'], "default_value", text="Tint")
                    r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH')
                elif socket == "Normal" and src_node.type == 'NORMAL_MAP':
                    box.prop(src_node.inputs['Strength'], "default_value", text="Strength")
                elif socket in ("Roughness", "Metallic") and src_node.type == 'MATH':
                    key = socket.lower() + "_strength"
                    box.prop(mat.pbr_settings, key, text="Strength", slider=True)
                elif socket == "Alpha":
                    box.prop(principled.inputs['Alpha'], "default_value", text="Alpha")

            # If not linked, show assign UI
            else:
                op = row.operator("pbr.assign_texture", text="Assign", icon='FILEBROWSER')
                op.input_name = socket  # Ensure the input_name is correctly assigned
                op.colorspace = colorspace

                if socket != "Normal":
                    if socket == "Base Color":
                        r = box.row(align=True)
                        r.prop(principled.inputs['Base Color'], "default_value", text="Color")
                        r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH')
                    else:
                        box.prop(principled.inputs[socket], "default_value", text="Value")

            # ─── Channel dropdown (always shown for non-BaseColor, non-Normal) ───
            if socket not in ("Base Color", "Normal"):
                box.prop(
                    mat.pbr_settings,
                    f"{socket.lower()}_channel",
                    text="Channel"
                )

        # Material settings footer
        layout.separator()
        ms = layout.box()
        ms.label(text="Material Settings", icon='MATERIAL')
        row = ms.row(align=True)
        row.label(text="Blend Mode")
        row.prop_enum(mat, "blend_method", 'BLEND',  text="Blend")
        row.prop_enum(mat, "blend_method", 'HASHED', text="Hashed")
        ms.prop(mat, "use_backface_culling", text="Backface Culling")

        layout.separator()
        layout.operator("pbr.arrange_nodes", text="Arrange All Nodes", icon='NODETREE')




