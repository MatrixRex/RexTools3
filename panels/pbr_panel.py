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

        # toggle: separate alpha map
        box = layout.box()
        box.prop(mat.pbr_settings, "use_separate_alpha_map", text="Use Separate Alpha Map")
        layout.separator()

        if not mat.use_nodes:
            layout.operator("pbr.create_material", text="Enable Nodes", icon='NODETREE')
            return

        princ = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not princ:
            layout.label(text="No Principled BSDF found")
            layout.operator("pbr.create_material", text="Setup PBR Material", icon='MATERIAL')
            return

        layout.prop(mat, "name", text="Material")
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

            inp = princ.inputs.get(socket)
            linked = inp and inp.is_linked

            if linked:
                row.operator("pbr.remove_texture", text="", icon='X').input_name = socket
                node = inp.links[0].from_node

                # determine source image name
                if socket == "Base Color" and node.type == 'MIX_RGB':
                    tex_node = node.inputs['Color1'].links[0].from_node
                    name = tex_node.image.name if tex_node.image else "No Image"
                elif node.type == 'TEX_IMAGE':
                    name = node.image.name if node.image else "No Image"
                elif node.type == 'NORMAL_MAP':
                    name = "Normal Map"
                else:
                    name = node.type

                box.label(text=f"Texture: {name}")

                # sliders target Mix/Math node inputs
                if socket == "Base Color" and node.type == 'MIX_RGB':
                    box.prop(node.inputs['Color2'], "default_value", text="Tint")
                elif socket == "Normal" and node.type == 'NORMAL_MAP':
                    box.prop(node.inputs['Strength'], "default_value", text="Strength")
                elif socket in ("Roughness", "Metallic") and node.type == 'MATH':
                    box.prop(node.inputs[1], "default_value", text="Strength")
                elif socket == "Alpha":
                    box.prop(princ.inputs['Alpha'], "default_value", text="Alpha")

            else:
                op = row.operator("pbr.assign_texture", text="Assign", icon='FILEBROWSER')
                op.input_name = socket
                op.colorspace = cs
                if socket != "Normal":
                    if socket == "Base Color":
                        box.prop(princ.inputs[socket], "default_value", text="Color")
                    else:
                        box.prop(princ.inputs[socket], "default_value", text="Value")

        layout.separator()

        ms = layout.box()
        ms.label(text="Material Settings", icon='MATERIAL')
        row = ms.row(align=True)
        row.label(text="Blend Mode")
        row.prop_enum(mat, "blend_method", 'BLEND', text="Blend")
        row.prop_enum(mat, "blend_method", 'HASHED', text="Hashed")
        ms.prop(mat, "use_backface_culling", text="Backface Culling")
