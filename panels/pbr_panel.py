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

        # Toggle: use separate alpha map or base-color alpha
        box = layout.box()
        box.prop(mat.pbr_settings, "use_separate_alpha_map", text="Use Separate Alpha Map")
        layout.separator()

        if not mat.use_nodes:
            layout.operator("pbr.create_material", text="Enable Nodes", icon='NODETREE')
            return

        principled = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not principled:
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

            inp = principled.inputs.get(socket)
            linked = inp and inp.is_linked

            if linked:
                row.operator("pbr.remove_texture", text="", icon='X').input_name = socket
                node = inp.links[0].from_node
                img = getattr(node, 'image', None)
                name = img.name if img else node.type
                box.label(text=f"Texture: {name}")

                if socket == "Base Color":
                    box.prop(principled.inputs['Base Color'], "default_value", text="Tint")
                elif socket == "Normal" and node.type == 'NORMAL_MAP':
                    box.prop(node.inputs['Strength'], "default_value", text="Strength")
                elif socket in ("Roughness", "Metallic"):
                    box.prop(principled.inputs[socket], "default_value", text="Strength")
                elif socket == "Alpha":
                    box.prop(principled.inputs['Alpha'], "default_value", text="Alpha")

            else:
                op = row.operator("pbr.assign_texture", text="Assign", icon='FILEBROWSER')
                op.input_name = socket
                op.colorspace = cs
                if socket != "Normal":
                    if socket == "Base Color":
                        box.prop(principled.inputs[socket], "default_value", text="Color")
                    else:
                        box.prop(principled.inputs[socket], "default_value", text="Value")

        layout.separator()

        # Material Settings (Blender 4.5 API)
        ms = layout.box()
        ms.label(text="Material Settings", icon='MATERIAL')

        row = ms.row(align=True)
        row.label(text="Blend Mode")
        row.prop_enum(mat, "blend_method", 'BLEND', text="Blend")
        row.prop_enum(mat, "blend_method", 'HASHED', text="Hashed")

        ms.prop(mat, "use_backface_culling", text="Backface Culling")
