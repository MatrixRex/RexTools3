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


def update_constraint_type(self, context):
    if not (context.active_object and context.active_object.type == 'ARMATURE' and context.mode == 'POSE'):
        return
    
    pb = context.active_pose_bone
    if not pb:
        return
        
    con_name = "REX_TEMPLATE"
    con = pb.constraints.get(con_name)
    
    if con:
        if con.type != self.constraint_type:
            # Replace existing template with new type
            pb.constraints.remove(con)
            con = pb.constraints.new(type=self.constraint_type)
            con.name = con_name
            con.mute = True


class ChainConstraintsAdderProperties(PropertyGroup):
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=[
            ('COPY_LOCATION', "Copy Location", ""),
            ('COPY_ROTATION', "Copy Rotation", ""),
            ('COPY_SCALE', "Copy Scale", ""),
            ('COPY_TRANSFORMS', "Copy Transforms", ""),
            ('LIMIT_DISTANCE', "Limit Distance", ""),
            ('LIMIT_LOCATION', "Limit Location", ""),
            ('LIMIT_ROTATION', "Limit Rotation", ""),
            ('LIMIT_SCALE', "Limit Scale", ""),
            ('MAINTAIN_VOLUME', "Maintain Volume", ""),
            ('TRANSFORM_CACHE', "Transform Cache", ""),
            ('CLAMP_TO', "Clamp To", ""),
            ('DAMPED_TRACK', "Damped Track", ""),
            ('IK', "IK", ""),
            ('LOCKED_TRACK', "Locked Track", ""),
            ('SPLINE_IK', "Spline IK", ""),
            ('STRETCH_TO', "Stretch To", ""),
            ('TRACK_TO', "Track To", ""),
            ('ACTION', "Action", ""),
            ('ARMATURE', "Armature", ""),
            ('CHILD_OF', "Child Of", ""),
            ('FLOOR', "Floor", ""),
            ('FOLLOW_PATH', "Follow Path", ""),
            ('FOLLOW_TRACK', "Follow Track", ""),
            ('KINEMATIC', "Kinematic", ""),
            ('OBJECT_SOLVER', "Object Solver", ""),
            ('PIVOT', "Pivot", ""),
            ('SHRINKWRAP', "Shrinkwrap", ""),
        ],
        default='COPY_ROTATION',
        update=update_constraint_type
    )
    mode: EnumProperty(
        name="Mode",
        items=[
            ('INCREASE', "Increase", ""),
            ('DECREASE', "Decrease", ""),
            ('FROM_TO', "From and To", ""),
        ],
        default='DECREASE'
    )
    influence_value: FloatProperty(
        name="Value",
        default=0.1,
        min=0.0,
        max=1.0
    )
    influence_from: FloatProperty(
        name="From",
        default=0.0,
        min=0.0,
        max=1.0
    )
    influence_to: FloatProperty(
        name="To",
        default=1.0,
        min=0.0,
        max=1.0
    )
    direction: EnumProperty(
        name="Direction",
        items=[
            ('FROM_ROOT', "From Root", ""),
            ('FROM_TIP', "From Tip", ""),
        ],
        default='FROM_TIP'
    )


class RexExportSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Global directory for exports",
        default="",
        subtype='DIR_PATH'
    )
    export_mode: EnumProperty(
        name="Export Mode",
        items=[
            ('OBJECTS', "Objects", "Each object as 1 mesh"),
            ('PARENTS', "Parents", "Each top most parent as 1 mesh"),
            ('COLLECTIONS', "Collections", "Each collection as 1 mesh"),
        ],
        default='OBJECTS'
    )
    export_limit: EnumProperty(
        name="Limit",
        items=[
            ('VISIBLE', "Visible", "All scene visible objects"),
            ('SELECTED', "Selected", "Only selected objects"),
            ('RENDER', "Render Visible", "Only objects visible for render"),
        ],
        default='SELECTED'
    )
    export_format: EnumProperty(
        name="Format",
        items=[
            ('FBX', "FBX", "Export as FBX"),
            ('GLTF', "GLTF", "Export as GLTF"),
            ('OBJ', "OBJ", "Export as OBJ"),
        ],
        default='FBX'
    )
    
    def get_presets(self, context):
        import os
        import bpy
        
        presets = [('NONE', "No Preset", "")]
        
        # Determine preset folder based on format
        fmt = self.export_format.lower()
        if fmt == 'fbx':
            folder = "export_scene.fbx"
        elif fmt == 'gltf':
            folder = "export_scene.gltf"
        elif fmt == 'obj':
            folder = "export_scene.obj"
        else:
            return presets

        paths = bpy.utils.preset_paths(os.path.join("operator", folder))
        for p in paths:
            for f in os.listdir(p):
                if f.endswith(".py"):
                    name = f[:-3]
                    presets.append((name, name.replace("_", " ").title(), ""))
        
        return presets

    export_preset: EnumProperty(
        name="Preset",
        items=get_presets,
    )
    last_export_path: StringProperty(
        name="Last Export Path",
        default="",
        subtype='DIR_PATH'
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

    bpy.types.Scene.rex_export_settings = PointerProperty(type=RexExportSettings)
    bpy.types.Collection.export_location = StringProperty(
        name="Export Location",
        subtype='DIR_PATH'
    )
    bpy.types.Object.export_location = StringProperty(
        name="Export Location",
        subtype='DIR_PATH'
    )
    bpy.types.Scene.chain_constraints_props = PointerProperty(type=ChainConstraintsAdderProperties)


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
    
    del bpy.types.Scene.rex_export_settings
    del bpy.types.Collection.export_location
    del bpy.types.Object.export_location
    del bpy.types.Scene.chain_constraints_props
