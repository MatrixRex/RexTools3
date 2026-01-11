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

        # Debug Preview Active Alert
        if mat.pbr_settings.debug_preview_mode != 'OFF':
            box = layout.box()
            box.alert = True
            row = box.row()
            row.label(text=f"DEBUG PREVIEW: {mat.pbr_settings.debug_preview_slot} ({mat.pbr_settings.debug_preview_mode.title()})", icon='VIEWZOOM')
            row.operator("pbr.clear_debug_preview", text="Clear", icon='X')
            layout.separator()

        # Build our list of sockets
        inputs = [
            ("Base Color", "Base Color", "sRGB"),
            ("Normal",     "Normal",     "Non-Color"),
            ("Roughness",  "Roughness",  "Non-Color"),
            ("Metallic",   "Metallic",   "Non-Color"),
            ("Emission",   "Emission",   "sRGB"),
        ]
        if mat.pbr_settings.use_separate_alpha_map:
            inputs.append(("Alpha", "Alpha", "Non-Color"))
        
        # Add AO slot (custom logic since it's not a Principled BSDF input)
        # We append a special identifier to handle it in the draw loop
        inputs.append(("AO", "AO", "Non-Color"))

        # Draw each socket block
        for label, socket, colorspace in inputs:
            # Highlight active preview
            is_preview = (mat.pbr_settings.debug_preview_slot == label and mat.pbr_settings.debug_preview_mode != 'OFF')
            
            box = layout.box()
            if is_preview:
                box.alert = True
                
            row = box.row()
            row.label(text=label, icon='TEXTURE')
            
            linked = False
            src_node = None
            
            if socket == "AO":
                # AO is special: check for AOMix node
                ao_mix = nodes.get("AOMix")
                bc_inp = principled.inputs.get("Base Color")
                if ao_mix and bc_inp and bc_inp.is_linked:
                    # Check if AOMix is in the chain starting from BSDF
                    curr = bc_inp.links[0].from_node
                    while curr:
                        if curr == ao_mix:
                            linked = True
                            # AO texture is connected to 'B'
                            b_sock = curr.inputs.get('B') or curr.inputs[2]
                            if b_sock and b_sock.is_linked:
                                src_node = b_sock.links[0].from_node
                            break
                        
                        # Move backwards through 'A' slot
                        a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                        curr = a_sock.links[0].from_node if a_sock and a_sock.is_linked else None
            elif socket == "Emission":
                em_inp = principled.inputs.get("Emission Color")
                if em_inp and em_inp.is_linked:
                    linked = True
                    curr = em_inp.links[0].from_node
                    if curr.name == "EmissionTintMix":
                        # Texture is behind the tint mix
                        a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                        if a_sock and a_sock.is_linked:
                            src_node = a_sock.links[0].from_node
                    else:
                        src_node = curr
            else:
                inp = principled.inputs.get(socket)
                if not inp:
                    continue
                if inp.is_linked:
                    # Specific check for Base Color to avoid picking up AO texture
                    if socket == "Base Color":
                        # Look for BaseTex or BaseTintMix
                        curr = inp.links[0].from_node
                        while curr:
                            if curr.name == "BaseTex":
                                linked = True
                                src_node = curr
                                break
                            if curr.name == "BaseTintMix":
                                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                                if a_sock and a_sock.is_linked:
                                    # Behind the tint is either another mix (AO) or the texture
                                    curr = a_sock.links[0].from_node
                                    continue
                            if curr.name == "AOMix":
                                a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
                                if a_sock and a_sock.is_linked:
                                    curr = a_sock.links[0].from_node
                                    continue
                            # Fallback if no names match but we have a direct TexImage
                            if curr.type == 'TEX_IMAGE' and curr.name != "AOTex":
                                linked = True
                                src_node = curr
                                break
                            break
                    else:
                        linked = True
                        src_node = inp.links[0].from_node

            # If already linked, show remove + controls
            if linked:
                row.operator("pbr.remove_texture", text="", icon='X').input_name = socket
                
                name = "Unknown"
                if src_node:
                    tex_node = self.find_texture_node(src_node)
                    if tex_node and tex_node.type == 'TEX_IMAGE':
                        name = tex_node.image.name if tex_node.image else "No Image"
                    else:
                        name = src_node.type.replace('_', ' ').title()
                
                box.label(text=f"Texture: {name}")

                # Per-socket extra controls
                if socket == "Base Color":
                    tint_node = nodes.get("BaseTintMix")
                    if tint_node:
                        r = box.row(align=True)
                        tint_sock = tint_node.inputs.get('B') or tint_node.inputs.get('Color2')
                        if tint_sock:
                            r.prop(tint_sock, "default_value", text="Tint")
                            r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH').mode = 'BASE'

                elif socket == "Normal" and src_node.type == 'NORMAL_MAP':
                    box.prop(src_node.inputs['Strength'], "default_value", text="Strength")
                elif socket == "Emission":
                    tint_node = nodes.get("EmissionTintMix")
                    if tint_node:
                        r = box.row(align=True)
                        tint_sock = tint_node.inputs.get('B') or tint_node.inputs.get('Color2')
                        if tint_sock:
                            r.prop(tint_sock, "default_value", text="Tint")
                            r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH').mode = 'EMISSION'
                    box.prop(mat.pbr_settings, "emission_strength", text="Strength")
                elif socket in ("Roughness", "Metallic", "AO"):
                    key = socket.lower() + "_strength"
                    box.prop(mat.pbr_settings, key, text="Strength", slider=True)
                elif socket == "Alpha":
                    box.prop(principled.inputs['Alpha'], "default_value", text="Alpha")

            # If not linked, show assign UI
            else:
                op = row.operator("pbr.assign_texture", text="Assign", icon='FILEBROWSER')
                op.input_name = socket
                op.colorspace = colorspace

                if socket not in ("Normal", "AO"):
                    if socket == "Base Color":
                        r = box.row(align=True)
                        r.prop(principled.inputs['Base Color'], "default_value", text="Color")
                        r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH').mode = 'BASE'
                    elif socket == "Emission":
                        r = box.row(align=True)
                        r.prop(principled.inputs['Emission Color'], "default_value", text="Color")
                        r.operator("pbr.reset_tint", text="", icon='FILE_REFRESH').mode = 'EMISSION'
                    else:
                        box.prop(principled.inputs[socket], "default_value", text="Value")

            # ─── Channel dropdown (always shown for non-BaseColor, non-Normal) ───
            if socket not in ("Base Color", "Normal"):
                box.prop(
                    mat.pbr_settings,
                    f"{socket.lower()}_channel",
                    text="Channel"
                )
            
            # ─── Debug Buttons (if linked) ───
            if linked:
                row = box.row(align=True)
                row.label(text="Debug Preview:", icon='VIEWZOOM')
                
                # Direct
                d_op = row.operator("pbr.debug_preview", text="Direct", depress=(is_preview and mat.pbr_settings.debug_preview_mode == 'DIRECT'))
                d_op.slot = label
                d_op.mode = 'DIRECT'
                
                # Mixed
                if label in ("Base Color", "Normal", "Emission"):
                    m_op = row.operator("pbr.debug_preview", text="Mixed", depress=(is_preview and mat.pbr_settings.debug_preview_mode == 'MIXED'))
                    m_op.slot = label
                    m_op.mode = 'MIXED'
                
                if is_preview:
                    row.operator("pbr.clear_debug_preview", text="", icon='X')

        # Material settings footer
        layout.separator()
        ms = layout.box()
        ms.label(text="Material Settings", icon='MATERIAL')
        row = ms.row(align=True)
        row.label(text="Blend Mode")
        row.prop_enum(mat, "blend_method", 'BLEND',  text="Blend")
        row.prop_enum(mat, "blend_method", 'HASHED', text="Hashed")
        ms.prop(mat, "use_backface_culling", text="Backface Culling", toggle=True)

        layout.separator()
        layout.operator("pbr.arrange_nodes", text="Arrange All Nodes", icon='NODETREE')




