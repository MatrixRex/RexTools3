import os
import bpy
from . import notify

def prepare_target_mesh(obj):
    """Splits target mesh edges and performs UV unwrap."""
    if not obj or obj.type != 'MESH':
        return

    # Store current mode
    original_mode = obj.mode

    # Switch to Object Mode to change selection
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all and select only target
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # 1. Edge Split in Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_split()
    
    # 2. UV Unwrap and Pack
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.uv.pack_islands(margin=0.01)

    # Restore original mode
    bpy.ops.object.mode_set(mode=original_mode)


def setup_displacement_modifier(obj, strength):
    """Ensures Displace modifier exists and sets its strength."""
    modifier_exists = False
    displacement_modifier = None

    for modifier in obj.modifiers:
        if modifier.type == 'DISPLACE' and modifier.name == "Displacement_imposter":
            modifier_exists = True
            displacement_modifier = modifier
            break

    if not modifier_exists:
        displacement_modifier = obj.modifiers.new(name="Displacement_imposter", type='DISPLACE')

    displacement_modifier.strength = strength
    return displacement_modifier


def create_texture_image(name, size, is_transparent=False, is_normal=False):
    """Creates a new Blender image data block, replacing any existing one with same name."""
    existing_img = bpy.data.images.get(name)
    if existing_img:
        bpy.data.images.remove(existing_img)

    img = bpy.data.images.new(name=name, width=size, height=size, alpha=is_transparent)

    if is_normal:
        # Default normal map is neutral blue (0.5, 0.5, 1.0, 1.0)
        pixels = [0.5, 0.5, 1.0, 1.0] * (size * size)
        img.pixels = pixels
        img.generated_color = (0.5, 0.5, 1.0, 1.0)
    elif is_transparent:
        pixels = [0.0, 0.0, 0.0, 0.0] * (size * size)
        img.pixels = pixels

    return img


def setup_imposter_material(obj, size):
    """Sets up a material and nodes on the target object."""
    mat_name = f"mat_{obj.name}_imposter"
    
    # Reuse or create material
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)

    # Link material
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    mat.use_nodes = True
    mat.use_backface_culling = True
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    # Clear nodes to avoid double-setup issues
    nodes.clear()

    # Create Principled BSDF & Output
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.location = (0, 0)

    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (300, 0)
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    # Create new textures
    albedo_img = create_texture_image(f"Albedo_{obj.name}", size, is_transparent=True, is_normal=False)
    normal_img = create_texture_image(f"NormalMap_{obj.name}", size, is_transparent=False, is_normal=True)
    ao_img = create_texture_image(f"AO_{obj.name}", size, is_transparent=False, is_normal=False)

    # Image nodes
    albedo_texture_node = nodes.new(type='ShaderNodeTexImage')
    albedo_texture_node.name = "AlbedoTex_Oven"
    albedo_texture_node.location = (-750, 250)
    albedo_texture_node.image = albedo_img

    ao_texture_node = nodes.new(type='ShaderNodeTexImage')
    ao_texture_node.name = "AOTex_Oven"
    ao_texture_node.location = (-750, 0)
    ao_texture_node.image = ao_img
    ao_img.colorspace_settings.name = 'Non-Color'

    normal_texture_node = nodes.new(type='ShaderNodeTexImage')
    normal_texture_node.name = "NormalTex_Oven"
    normal_texture_node.location = (-750, -200)
    normal_texture_node.image = normal_img
    normal_img.colorspace_settings.name = 'Non-Color'

    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
    normal_map_node.location = (-350, -200)

    mix_color_node = nodes.new(type='ShaderNodeMix')
    mix_color_node.location = (-350, 250)
    mix_color_node.data_type = 'RGBA'
    mix_color_node.blend_type = 'MULTIPLY'
    mix_color_node.inputs[0].default_value = 1.0

    # Links setup with robust name & index fallback
    try:
        links.new(albedo_texture_node.outputs['Color'], mix_color_node.inputs['A'])
    except KeyError:
        links.new(albedo_texture_node.outputs['Color'], mix_color_node.inputs[6])

    try:
        links.new(ao_texture_node.outputs['Color'], mix_color_node.inputs['B'])
    except KeyError:
        links.new(ao_texture_node.outputs['Color'], mix_color_node.inputs[7])

    try:
        links.new(mix_color_node.outputs['Result'], principled_node.inputs['Base Color'])
    except KeyError:
        links.new(mix_color_node.outputs[2], principled_node.inputs['Base Color'])

    links.new(albedo_texture_node.outputs['Alpha'], principled_node.inputs['Alpha'])
    links.new(normal_texture_node.outputs['Color'], normal_map_node.inputs['Color'])
    links.new(normal_map_node.outputs['Normal'], principled_node.inputs['Normal'])

    return albedo_texture_node, ao_texture_node, normal_texture_node


def run_bake_pass(node_tree, active_node, bake_type, samples=1, is_diffuse=False):
    """Selects target node, sets cycles settings, and executes bake."""
    # Deselect all nodes, select target node and make it active
    for node in node_tree.nodes:
        node.select = False
    active_node.select = True
    node_tree.nodes.active = active_node

    # Configure cycles bake details
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.cycles.bake_type = bake_type

    if is_diffuse:
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True

    # Run operator
    bpy.ops.object.bake(type=bake_type)


def bake_imposter(context, props):
    """Main bake imposter logic."""
    target_obj = props.target_object
    source_obj = props.source_object

    if not target_obj or not source_obj:
        notify.error("Target or Source object is missing!")
        return False

    # Store user's original context state to restore in finally
    original_active = context.view_layer.objects.active
    original_selected = context.selected_objects.copy()
    original_engine = context.scene.render.engine
    original_device = context.scene.cycles.device
    original_samples = context.scene.cycles.samples
    original_use_selected_to_active = context.scene.render.bake.use_selected_to_active
    original_bake_margin = context.scene.cycles.bake_margin

    try:
        # 1. Prepare Target Mesh (Splits and UV Unwrap)
        prepare_target_mesh(target_obj)

        # 2. Setup Displacement modifier
        setup_displacement_modifier(target_obj, props.displacement_strength)

        # 3. Setup Material and Texture nodes
        size = int(props.resolution)
        albedo_node, ao_node, normal_node = setup_imposter_material(target_obj, size)

        # 4. Prepare selections for selected-to-active bake
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        source_obj.select_set(True)
        target_obj.select_set(True)
        context.view_layer.objects.active = target_obj

        # 5. Cycles Bake engine settings
        context.scene.render.engine = 'CYCLES'
        context.scene.cycles.device = 'GPU'
        context.scene.cycles.bake_margin = 2
        context.scene.render.bake.use_selected_to_active = True

        node_tree = target_obj.active_material.node_tree

        # Bake Diffuse
        notify.info("Baking Diffuse/Albedo Map...")
        run_bake_pass(node_tree, albedo_node, 'DIFFUSE', samples=1, is_diffuse=True)

        # Bake AO
        notify.info("Baking Ambient Occlusion Map...")
        run_bake_pass(node_tree, ao_node, 'AO', samples=props.ao_sample_count)

        # Bake Normals
        notify.info("Baking Normal Map...")
        run_bake_pass(node_tree, normal_node, 'NORMAL', samples=1)

        # Hiding high-poly source mesh
        source_obj.hide_set(True, view_layer=context.view_layer)

        notify.success("Bake complete! Imposter is ready.")
        return True

    except Exception as e:
        notify.error(f"Bake failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Restore original render engine settings
        context.scene.render.engine = original_engine
        context.scene.cycles.device = original_device
        context.scene.cycles.samples = original_samples
        context.scene.render.bake.use_selected_to_active = original_use_selected_to_active
        context.scene.cycles.bake_margin = original_bake_margin

        # Restore selections
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected:
            try:
                obj.select_set(True)
            except Exception:
                pass
        context.view_layer.objects.active = original_active


def save_baked_textures(target_obj, save_dir):
    """Saves baked textures directly using image.save() without switching spaces."""
    if not target_obj or not target_obj.active_material:
        notify.error("No active material found on Target mesh!")
        return

    if not save_dir:
        notify.error("No save directory specified!")
        return

    # Create folder if it doesn't exist
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir, exist_ok=True)
        except Exception as e:
            notify.error(f"Failed to create directory: {str(e)}")
            return

    mat = target_obj.active_material
    nodes = mat.node_tree.nodes
    
    saved_files = []

    texture_node_names = {
        "AlbedoTex_Oven": "Albedo",
        "AOTex_Oven": "AO",
        "NormalTex_Oven": "NormalMap"
    }

    for node_name, label in texture_node_names.items():
        node = nodes.get(node_name)
        if node and node.image:
            image = node.image
            filename = f"{image.name}.png"
            file_path = os.path.join(save_dir, filename)
            
            # Save the image
            image.filepath_raw = file_path
            image.file_format = 'PNG'
            try:
                image.save()
                saved_files.append(filename)
            except Exception as e:
                notify.error(f"Failed to save {filename}: {str(e)}")

    if saved_files:
        notify.success(f"Saved: {', '.join(saved_files)} to {save_dir}")
    else:
        notify.warning("No Oven texture nodes found to save.")
