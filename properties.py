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

    # AO is not a direct socket on BSDF, so we skip the socket check for it
    if input_name not in ('AO', 'Emission'):
        inp = principled.inputs.get(input_name)
        if not inp or not inp.is_linked:
            return
    
    # Map input name to actual BSDF socket name
    socket_map = {
        'Emission': 'Emission Color',
    }
    actual_socket_name = socket_map.get(input_name, input_name)
    
    # Target socket for texture linking
    # For Roughness, Metallic, Alpha, AO, we link to a helper node first
    math_node = nodes.get(f"{input_name}Math")
    ao_add = nodes.get("AOAdd")
    em_mix = nodes.get("EmissionTintMix")
    
    target_sock = None
    if math_node:
        target_sock = math_node.inputs[0]
    elif input_name == 'AO' and ao_add:
        target_sock = ao_add.inputs[0]
    elif input_name == 'Emission' and em_mix:
        target_sock = em_mix.inputs.get('A') or em_mix.inputs[0]
    else:
        # Fallback to direct BSDF socket
        target_sock = principled.inputs.get(actual_socket_name)

    if not target_sock:
        return

    # Find relevant image texture node
    target_name = "BaseTex" if input_name == 'Base Color' else ("AOTex" if input_name == 'AO' else f"{input_name}Tex")
    tex_node = nodes.get(target_name)
    if not tex_node:
        return

    chan = getattr(self, f"{input_name.lower()}_channel")

    # 1) Clear existing links into target socket
    for link in list(target_sock.links):
        links.remove(link)

    # 2) Full or A directly from the texture
    if chan in ('FULL', 'A'):
        # Cleanup split node
        sep = nodes.get(f"{input_name}Split")
        if sep: nodes.remove(sep)
        
        if chan == 'FULL':
            links.new(tex_node.outputs['Color'], target_sock)
        else: # 'A'
            links.new(tex_node.outputs['Alpha'], target_sock)
    else:
        sep = nodes.get(f"{input_name}Split") or nodes.new('ShaderNodeSeparateRGB')
        sep.name = f"{input_name}Split"
        sep.location = (tex_node.location.x + 150, tex_node.location.y)
        if sep.inputs['Image'].is_linked:
            links.remove(sep.inputs['Image'].links[0])
        links.new(tex_node.outputs['Color'], sep.inputs['Image'])
        links.new(sep.outputs[chan], target_sock)

    if input_name == 'Alpha':
        mat.blend_method = 'BLEND'
    
    bpy.ops.pbr.arrange_nodes()
    return
    
    bpy.ops.pbr.arrange_nodes()


def update_roughness_channel(self, context):
    update_channel_map(self, context, 'Roughness')


def update_metallic_channel(self, context):
    update_channel_map(self, context, 'Metallic')


def update_alpha_channel(self, context):
    update_channel_map(self, context, 'Alpha')


def update_ao_channel(self, context):
    update_channel_map(self, context, 'AO')


def update_emission_channel(self, context):
    update_channel_map(self, context, 'Emission')


# ─────────────────────────────────────────────────────────────────────────────
# Strength updates (Roughness/Metallic)
# ─────────────────────────────────────────────────────────────────────────────

def update_strength(self, context, input_name):
    mat = self.id_data
    if not mat or not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes

    if input_name == 'AO':
        node = nodes.get("AOAdd")
        if node:
            # Math node ADD: input[1] is the value to add
            node.inputs[1].default_value = 1.0 - float(getattr(self, "ao_strength", 1.0))
        return

    if input_name == 'Emission':
        # For Emission, strength often goes to the BSDF socket directly
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if principled:
            principled.inputs['Emission Strength'].default_value = float(getattr(self, "emission_strength", 1.0))
        return

    # Check for both slot-named Math node and generic principled input fallback
    math = nodes.get(f"{input_name}Math")
    if math:
        value = getattr(self, f"{input_name.lower()}_strength", 1.0)
        try:
            math.inputs[1].default_value = float(value)
        except Exception:
            pass
    elif input_name == 'Alpha':
        # Fallback for Alpha if no node exists yet (direct BSDF input)
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if principled:
            principled.inputs['Alpha'].default_value = float(getattr(self, "alpha_strength", 1.0))


class BoneRenameProperties(PropertyGroup):
    find_text: StringProperty(name="Find", default="")
    replace_text: StringProperty(name="Replace", default="")
    prefix_text: StringProperty(name="Prefix", default="")
    suffix_text: StringProperty(name="Suffix", default="")
    apply_prefix_suffix_to_matches_only: BoolProperty(default=False)


class HighLowRenamerProperties(PropertyGroup):
    obj_name: StringProperty(name="Object Name", default="")
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
    alpha_strength: FloatProperty(
        name="Alpha Strength",
        default=1.0, min=0.0, max=1.0,
        update=lambda self, ctx: update_strength(self, ctx, 'Alpha')
    )
    ao_strength: FloatProperty(
        name="AO Strength",
        default=1.0, min=0.0, max=1.0,
        update=lambda self, ctx: update_strength(self, ctx, 'AO')
    )
    emission_strength: FloatProperty(
        name="Emission Strength",
        default=1.0, min=0.0, max=1000.0,
        update=lambda self, ctx: update_strength(self, ctx, 'Emission')
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
    ao_channel: EnumProperty(
        name="AO Channel",
        items=channel_items,
        default='FULL',
        update=update_ao_channel
    )
    emission_channel: EnumProperty(
        name="Emission Channel",
        items=channel_items,
        default='FULL',
        update=update_emission_channel
    )
    debug_preview_mode: EnumProperty(
        name="Debug Preview Mode",
        items=[
            ('OFF', "Off", ""),
            ('DIRECT', "Direct", ""),
            ('MIXED', "Mixed", ""),
        ],
        default='OFF'
    )
    debug_preview_slot: StringProperty(
        name="Debug Preview Slot",
        default=""
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


class CleanupProperties(PropertyGroup):
    normals: BoolProperty(name="Normals", default=True)
    quad: BoolProperty(name="Quad", default=True)
    mats: BoolProperty(name="Mats", default=True)


class RexCommonSettings(PropertyGroup):
    clean_modifiers_all: BoolProperty(
        name="All",
        description="Operate on all visible objects, selected or not",
        default=False
    )
    clean_modifiers_hidden: BoolProperty(
        name="Hidden",
        description="Also remove modifiers that are hidden in the viewport",
        default=False
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
    show_preview: BoolProperty(
        name="Show Export Preview",
        description="Show a list of unique models that will be exported",
        default=False
    )
    show_custom_locations: BoolProperty(
        name="Show Custom Locations",
        description="Show a list of objects/collections with custom export paths",
        default=False
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
    bpy.types.Scene.rex_common_settings = PointerProperty(type=RexCommonSettings)
    bpy.types.Scene.rex_auto_frame_range = BoolProperty(
        name="Auto Frame Range",
        description="Auto calculate start and end frame based on active action",
        default=False
    )
    bpy.types.Scene.rex_cleanup_props = PointerProperty(type=CleanupProperties)


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
    del bpy.types.Scene.rex_common_settings
    del bpy.types.Scene.rex_auto_frame_range
    del bpy.types.Scene.rex_cleanup_props
