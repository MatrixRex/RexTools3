# panels/pbr_panel.py

import bpy
from bpy.types import Panel

class PBR_PT_MaterialPanel(Panel):
    bl_label = "Easy PBR"
    bl_idname = "PBR_PT_material_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

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

        box = layout.box()
        box.prop(mat.pbr_settings, "use_separate_alpha_map", text="Use Separate Alpha Map")
        layout.separator()

        if not mat.use_nodes:
            layout.operator("pbr.create_material", text="Enable Nodes", icon='NODETREE')
            return

        nodes = mat.node_tree.nodes
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
            layout.label(text="No Principled BSDF found")
            layout.operator("pbr.create_material", text="Setup PBR Material", icon='MATERIAL')
            return

        row = layout.row()
        row.prop(mat, "name", text="Material")
        row.operator("pbr.arrange_nodes", text="", icon='NODETREE')
        layout.separator()

        inputs = [
            ("Base Color", "Base Color", "sRGB"),
            ("Normal",     "Normal",     "Non-Color"),
            ("Roughness",  "Roughness",  "Non-Color"),
            ("Metallic",   "Metallic",   "Non-Color"),
        ]
        if mat.pbr_settings.use_separate_alpha_map:
            inputs.append(("Alpha", "Alpha", "Non-Color"))

        for label, socket, cs in inputs:
            box = layout.box()
            row = box.row()
            row.label(text=label, icon='TEXTURE')
            inp = principled.inputs[socket]

            if inp.is_linked:
                row.operator("pbr.remove_texture", text="", icon='X').input_name = socket
                node = inp.links[0].from_node
                # (existing display logic unchanged) …
                if socket == "Base Color" and node.type == 'MIX_RGB':
                    tex = node.inputs['Color1'].links[0].from_node
                    name = tex.image.name if tex.image else "No Image"
                elif node.type == 'TEX_IMAGE':
                    name = node.image.name if node.image else "No Image"
                else:
                    name = node.type
                box.label(text=f"Texture: {name}")

                if socket == "Base Color" and node.type == 'MIX_RGB':
                    row = box.row(align=True)
                    row.prop(node.inputs['Color2'], "default_value", text="Tint")
                    row.operator("pbr.reset_tint", text="", icon='FILE_REFRESH')
                elif socket == "Normal" and node.type == 'NORMAL_MAP':
                    box.prop(node.inputs['Strength'], "default_value", text="Strength")
                elif socket in ("Roughness", "Metallic") and node.type == 'MATH':
                    key = socket.lower() + "_strength"
                    box.prop(mat.pbr_settings, key, text="Strength", slider=True)
                elif socket == "Alpha":
                    box.prop(principled.inputs['Alpha'], "default_value", text="Alpha")

            else:
                op = row.operator("pbr.assign_texture", text="Assign", icon='FILEBROWSER')
                op.input_name = socket
                op.colorspace = cs

                # default-value slider
                if socket != "Normal":
                    if socket == "Base Color":
                        box.prop(principled.inputs['Base Color'], "default_value", text="Color")
                    else:
                        box.prop(principled.inputs[socket], "default_value", text="Value")

                # **channel dropdown for packing support**
                if socket != "Base Color":
                    prop_name = socket.lower() + "_channel"
                    box.prop(mat.pbr_settings, prop_name, text="Channel")

        layout.separator()
        ms = layout.box()
        ms.label(text="Material Settings", icon='MATERIAL')
        row = ms.row(align=True)
        row.label(text="Blend Mode")
        row.prop_enum(mat, "blend_method", 'BLEND', text="Blend")
        row.prop_enum(mat, "blend_method", 'HASHED', text="Hashed")
        ms.prop(mat, "use_backface_culling", text="Backface Culling")

        layout.separator()
        layout.operator("pbr.arrange_nodes", text="Arrange All Nodes", icon='NODETREE')
