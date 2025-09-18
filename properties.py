import bpy
from bpy.props import (
    IntProperty, FloatProperty,
    BoolProperty, StringProperty,
    PointerProperty, EnumProperty
)
from bpy.types import PropertyGroup


def update_use_sep_alpha(self, context):
    mat = self.id_data
    if not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return

    alpha_inp = principled.inputs['Alpha']
    for link in list(alpha_inp.links):
        links.remove(link)

    if not self.use_separate_alpha_map:
        base_inp = principled.inputs['Base Color']
        if base_inp.is_linked:
            base_node = base_inp.links[0].from_node
            if base_node.type == 'TEX_IMAGE':
                links.new(base_node.outputs['Alpha'], alpha_inp)
                mat.blend_method = 'HASHED'


# ─────────────────────────────────────────────────────────────────────────────
# Channel mapping updates
# ─────────────────────────────────────────────────────────────────────────────

def update_channel_map(self, context, input_name):
    mat = self.id_data
    if not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return

    inp = principled.inputs.get(input_name)
    if not inp or not inp.is_linked:
        return

    # Find the Image Texture node we created
    tex_node = next((n for n in nodes 
                     if n.type=='TEX_IMAGE' and n.name==f"PBR Tex {input_name}"), 
                    None)
    if not tex_node:
        return

    chan = getattr(self, f"{input_name.lower()}_channel")

    # — Handle Alpha channel on its own —
    if input_name == 'Alpha':
        # 1) clear existing links into Alpha socket
        for link in list(inp.links):
            links.remove(link)

        # 2) full = Color output, A = direct Alpha output, else SeparateRGB
        if chan == 'FULL':
            links.new(tex_node.outputs['Color'], inp)
        elif chan == 'A':
            links.new(tex_node.outputs['Alpha'], inp)
        else:
            sep = nodes.get(f"PBR Sep {input_name}") \
                  or nodes.new('ShaderNodeSeparateRGB')
            sep.name = f"PBR Sep {input_name}"
            sep.location = (tex_node.location.x + 150, tex_node.location.y)
            # reconnect its input
            if sep.inputs['Image'].is_linked:
                links.remove(sep.inputs['Image'].links[0])
            links.new(tex_node.outputs['Color'], sep.inputs['Image'])
            links.new(sep.outputs[chan], inp)

        mat.blend_method = 'BLEND'
        return

    # — Roughness & Metallic use the Math node we named earlier —
    math = next((n for n in nodes if n.name == f"PBR Math {input_name}"), None)
    if not math:
        return

    # Remove old connection into math.inputs[0]
    if math.inputs[0].is_linked:
        links.remove(math.inputs[0].links[0])

    # Full or Alpha directly from the texture
    if chan == 'FULL':
        links.new(tex_node.outputs['Color'], math.inputs[0])
    elif chan == 'A':
        links.new(tex_node.outputs['Alpha'], math.inputs[0])
    else:
        sep = nodes.get(f"PBR Sep {input_name}") \
              or nodes.new('ShaderNodeSeparateRGB')
        sep.name = f"PBR Sep {input_name}"
        sep.location = (tex_node.location.x + 150, tex_node.location.y)
        if sep.inputs['Image'].is_linked:
            links.remove(sep.inputs['Image'].links[0])
        links.new(tex_node.outputs['Color'], sep.inputs['Image'])
        links.new(sep.outputs[chan], math.inputs[0])


def update_roughness_channel(self, context):
    update_channel_map(self, context, 'Roughness')


def update_metallic_channel(self, context):
    update_channel_map(self, context, 'Metallic')


def update_alpha_channel(self, context):
    update_channel_map(self, context, 'Alpha')


# ─────────────────────────────────────────────────────────────────────────────
# Strength updates (Roughness/Metallic)
# ─────────────────────────────────────────────────────────────────────────────

def update_strength(self, context, input_name):
    mat = self.id_data
    if not mat or not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes
    math = nodes.get(f"PBR Math {input_name}")
    if not math:
        return
    value = getattr(self, f"{input_name.lower()}_strength", 1.0)
    try:
        math.inputs[1].default_value = float(value)
    except Exception:
        pass


class BoneRenameProperties(PropertyGroup):
    find_text: StringProperty(name="Find", default="")
    replace_text: StringProperty(name="Replace", default="")
    prefix_text: StringProperty(name="Prefix", default="")
    suffix_text: StringProperty(name="Suffix", default="")
    apply_prefix_suffix_to_matches_only: BoolProperty(default=False)


class HighLowRenamerProperties(PropertyGroup):
    obj_name: StringProperty(name="Object Name", default="Asset")
    high_prefix: StringProperty(name="High Prefix", default="_high")
    low_prefix: StringProperty(name="Low Prefix", default="_low")


class PBRMaterialSettings(PropertyGroup):
    use_auto_common_name: BoolProperty(
        name="Use Auto-Detected Name",
        default=True,
    )
    common_name: StringProperty(
        name="Common Name",
        default="",
    )
    use_separate_alpha_map: BoolProperty(
        name="Use Separate Alpha Map",
        default=False,
        update=update_use_sep_alpha
    )
    roughness_strength: FloatProperty(
        name="Roughness Strength",
        default=1.0, min=0.0, max=1.0,
        update=lambda self, ctx: update_strength(self, ctx, 'Roughness')
    )
    metallic_strength: FloatProperty(
        name="Metallic Strength",
        default=1.0, min=0.0, max=1.0,
        update=lambda self, ctx: update_strength(self, ctx, 'Metallic')
    )

    channel_items = [
        ('FULL', "Full", "Use full RGBA"),
        ('R',    "R",    "Use Red channel"),
        ('G',    "G",    "Use Green channel"),
        ('B',    "B",    "Use Blue channel"),
        ('A',    "A",    "Use Alpha channel"),
    ]
    roughness_channel: EnumProperty(
        name="Roughness Channel",
        items=channel_items,
        default='FULL',
        update=update_roughness_channel
    )
    metallic_channel: EnumProperty(
        name="Metallic Channel",
        items=channel_items,
        default='FULL',
        update=update_metallic_channel
    )
    alpha_channel: EnumProperty(
        name="Alpha Channel",
        items=channel_items,
        default='FULL',
        update=update_alpha_channel
    )


def register_properties():
    wm = bpy.types.WindowManager
    wm.modal_x = IntProperty(name="Mouse X", default=0)
    wm.modal_y = IntProperty(name="Mouse Y", default=0)

    bpy.types.Scene.bone_rename_props     = PointerProperty(type=BoneRenameProperties)
    bpy.types.Scene.highlow_renamer_props = PointerProperty(type=HighLowRenamerProperties)

    wm.select_similar_threshold   = FloatProperty(name="Threshold", default=0.0, min=0.0, max=1.0)
    wm.clear_inner_uv_area_seam   = BoolProperty(name="Clear Inner", default=False)
    wm.reseam_uv_area_seam        = BoolProperty(name="Reseam", default=False)
    wm.stop_loop_at_seam          = BoolProperty(name="Stop at Seam", default=True)
    bpy.types.Material.pbr_settings = PointerProperty(type=PBRMaterialSettings)


def unregister_properties():
    wm = bpy.types.WindowManager
    del wm.modal_x
    del wm.modal_y

    del bpy.types.Scene.bone_rename_props
    del bpy.types.Scene.highlow_renamer_props

    del wm.select_similar_threshold
    del wm.clear_inner_uv_area_seam
    del wm.reseam_uv_area_seam
    del wm.stop_loop_at_seam
    
    del bpy.types.Material.pbr_settings
