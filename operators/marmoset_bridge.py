import bpy
import os
import tempfile
import subprocess
import glob
from bpy.types import Operator
from .object_auto_rename_low_high import MESH_OT_auto_rename_high_low
from ..core import notify

def ensure_image_on_disk(img, export_dir):
    if not img:
        return None
    
    path = bpy.path.abspath(img.filepath)
    if path and os.path.exists(path) and not img.packed_file:
        return path
        
    # If packed or missing, save to export directory
    safe_name = bpy.path.clean_name(img.name)
    ext = os.path.splitext(path)[1] if path else ".png"
    if not ext:
        ext = ".png"
        
    temp_path = os.path.normpath(os.path.join(export_dir, f"_temp_tex_{safe_name}{ext}"))
    try:
        # Temporarily redirect filepath to save the image data to disk, then restore it
        orig_filepath = img.filepath_raw
        try:
            img.filepath_raw = temp_path
            img.save()
        finally:
            img.filepath_raw = orig_filepath
        return temp_path
    except Exception as e:
        # Fallback to save_render if save fails
        try:
            img.save_render(temp_path)
            return temp_path
        except Exception as e2:
            print(f"RexTools3: Failed to save image {img.name} to disk: {e} | {e2}")
            return None

def find_material_textures(material, export_dir):
    textures = {}
    if not material or not material.use_nodes:
        return textures
    
    nodes = material.node_tree.nodes
    
    # 1. Easy PBR System Node Names (Highest priority)
    pbr_mapping = {
        'albedo': 'BaseTex',
        'normal': 'NormalTex',
        'roughness': 'RoughnessTex',
        'metallic': 'MetallicTex',
    }
    
    for key, node_name in pbr_mapping.items():
        node = nodes.get(node_name)
        if node and node.type == 'TEX_IMAGE' and node.image:
            path = ensure_image_on_disk(node.image, export_dir)
            if path:
                textures[key] = os.path.normpath(path).replace("\\", "/")
                
    # 2. Standard Principled BSDF Socket Tracing (Medium priority)
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if principled:
        def get_image_path(socket):
            if not socket.is_linked:
                return None
            
            # Follow the link back
            link = socket.links[0]
            node = link.from_node
            
            # If it is direct image node
            if node.type == 'TEX_IMAGE' and node.image:
                return ensure_image_on_disk(node.image, export_dir)
                
            # If it is a normal map node
            if node.type in {'NORMAL_MAP', 'BUMP'}:
                col_sock = node.inputs.get('Color')
                if col_sock and col_sock.is_linked:
                    tex_node = col_sock.links[0].from_node
                    if tex_node.type == 'TEX_IMAGE' and tex_node.image:
                        return ensure_image_on_disk(tex_node.image, export_dir)
                        
            # If it is a mix node
            if node.type in {'MIX', 'MIX_RGB'}:
                # Check inputs Color1 / Color2 (or A / B in newer blender versions)
                for sock_name in ('A', 'B', 'Color1', 'Color2'):
                    in_sock = node.inputs.get(sock_name)
                    if in_sock and in_sock.is_linked:
                        from_n = in_sock.links[0].from_node
                        if from_n.type == 'TEX_IMAGE' and from_n.image:
                            return ensure_image_on_disk(from_n.image, export_dir)
            return None

        # Map Principled BSDF inputs to map types
        mappings = {
            'Base Color': 'albedo',
            'Roughness': 'roughness',
            'Metallic': 'metallic',
            'Normal': 'normal',
        }
        
        for socket_name, key in mappings.items():
            if key in textures:
                continue # Already found via Easy PBR
            sock = principled.inputs.get(socket_name)
            if sock:
                path = get_image_path(sock)
                if path:
                    textures[key] = os.path.normpath(path).replace("\\", "/")

    # 3. Fallback/Supplementary scan: scan all Image Texture nodes in the material
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            # Skip if we already found everything
            if all(k in textures for k in ['albedo', 'normal', 'roughness', 'metallic']):
                break
                
            img = node.image
            path = ensure_image_on_disk(img, export_dir)
            if not path:
                continue
                
            path_esc = os.path.normpath(path).replace("\\", "/")
            img_name_lower = img.name.lower()
            file_name_lower = os.path.basename(path).lower()
            
            # Helper to check if name matches pattern
            def matches(keywords):
                return any(kw in img_name_lower or kw in file_name_lower for kw in keywords)
                
            # Guess role if not already assigned by BSDF tracing
            if 'albedo' not in textures and matches(['albedo', 'diffuse', 'basecolor', 'base_color', 'color', 'diff']):
                textures['albedo'] = path_esc
            elif 'normal' not in textures and matches(['normal', 'nrm', 'nor_']):
                textures['normal'] = path_esc
            elif 'roughness' not in textures and matches(['roughness', 'rough', 'rgh']):
                textures['roughness'] = path_esc
            elif 'metallic' not in textures and matches(['metallic', 'metal', 'met_']):
                textures['metallic'] = path_esc
                
    return textures


class REXTOOLS3_OT_marmoset_bridge_prep(Operator):
    bl_idname = "rextools3.marmoset_bridge_prep"
    bl_label = "Prepare Meshes & Materials"
    bl_description = "Auto rename selected high/low meshes and materials, ensuring proper suffix setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(selected_objects) == 2

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        # Get bridge properties and renamer properties
        bridge_props = context.scene.rex_marmoset_bridge_props
        renamer_props = context.scene.highlow_renamer_props
        
        # 1. Detect high and low poly objects
        low_poly, high_poly = MESH_OT_auto_rename_high_low.detect_low_high(selected_objects, context)
        if not low_poly or not high_poly:
            self.report({'ERROR'}, "Could not differentiate High and Low poly objects")
            return {'CANCELLED'}
            
        # Determine asset name if empty
        asset_name = bridge_props.asset_name.strip()
        if not asset_name:
            asset_name = MESH_OT_auto_rename_high_low.clean_base_name(low_poly.name)
            if not asset_name:
                asset_name = "Asset"
            bridge_props.asset_name = asset_name
            
        # Sync asset name to highlow renamer properties before renaming
        renamer_props.obj_name = bridge_props.asset_name
            
        # 2. Run high-low renamer
        bpy.ops.mesh.auto_rename_high_low()
        
        # Retrieve renamed meshes
        target_low_name = renamer_props.obj_name + renamer_props.low_prefix
        target_high_name = renamer_props.obj_name + renamer_props.high_prefix
        
        low_poly = bpy.data.objects.get(target_low_name)
        high_poly = bpy.data.objects.get(target_high_name)
        
        if not low_poly or not high_poly:
            self.report({'ERROR'}, f"Failed to retrieve renamed objects: {target_low_name}, {target_high_name}")
            return {'CANCELLED'}
            
        # 3. Rename and match materials
        high_suffix = renamer_props.high_prefix
        low_suffix = renamer_props.low_prefix
        
        for i, slot in enumerate(high_poly.material_slots):
            high_mat = slot.material
            if not high_mat:
                continue
                
            orig_name = high_mat.name
            
            # Clean existing suffixes
            if orig_name.endswith(high_suffix):
                base_name = orig_name[:-len(high_suffix)]
            elif orig_name.endswith(low_suffix):
                base_name = orig_name[:-len(low_suffix)]
            else:
                base_name = orig_name
                
            target_high_mat_name = base_name + high_suffix
            target_low_mat_name = base_name
            
            # Rename high material
            if high_mat.name != target_high_mat_name:
                high_mat.name = target_high_mat_name
                
            # Get or create low material
            low_mat = bpy.data.materials.get(target_low_mat_name)
            if not low_mat:
                low_mat = bpy.data.materials.new(name=target_low_mat_name)
                low_mat.use_nodes = True
                
            # Assign corresponding material to low-poly
            while len(low_poly.material_slots) < i + 1:
                low_poly.data.materials.append(None)
            low_poly.material_slots[i].material = low_mat
            
        notify.success(f"Prepared meshes and materials for {renamer_props.obj_name}")
        return {'FINISHED'}


class REXTOOLS3_OT_marmoset_bridge_send(Operator):
    bl_idname = "rextools3.marmoset_bridge_send"
    bl_label = "Send to Marmoset"
    bl_description = "Export high/low poly meshes to FBX and launch Marmoset Toolbag with bake setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Must have exactly 2 meshes selected
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(selected_objects) == 2

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        # Get bridge and renamer properties
        props = context.scene.rex_marmoset_bridge_props
        renamer_props = context.scene.highlow_renamer_props
        
        # Check marmoset path in preferences
        addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
        prefs = context.preferences.addons[addon_name].preferences
        marmoset_path = bpy.path.abspath(prefs.marmoset_path)
        
        if not marmoset_path or not os.path.exists(marmoset_path):
            self.report({'ERROR'}, f"Marmoset Toolbag executable not found at: {marmoset_path}. Configure in Preferences.")
            return {'CANCELLED'}
            
        # Determine export directory
        export_dir = bpy.path.abspath(props.export_path)
        if not export_dir:
            if bpy.data.filepath:
                export_dir = os.path.dirname(bpy.data.filepath)
            else:
                self.report({'ERROR'}, "Save the blend file first, or specify a Bake Output Path.")
                return {'CANCELLED'}
                
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        # 1. Run prep logic if enabled
        if props.auto_rename:
            bpy.ops.rextools3.marmoset_bridge_prep()
            
            # Retrieve renamed meshes
            target_low_name = renamer_props.obj_name + renamer_props.low_prefix
            target_high_name = renamer_props.obj_name + renamer_props.high_prefix
            low_poly = bpy.data.objects.get(target_low_name)
            high_poly = bpy.data.objects.get(target_high_name)
        else:
            # Find the high and low poly meshes directly
            low_poly, high_poly = MESH_OT_auto_rename_high_low.detect_low_high(selected_objects, context)
            
        if not low_poly or not high_poly:
            self.report({'ERROR'}, "Failed to resolve High/Low poly meshes for sending")
            return {'CANCELLED'}
            
        # Determine asset name
        asset_name = props.asset_name.strip()
        if not asset_name:
            # Fallback to cleaned low poly base name
            asset_name = MESH_OT_auto_rename_high_low.clean_base_name(low_poly.name)
            if not asset_name:
                asset_name = "Asset"
            props.asset_name = asset_name
            
        # Export paths
        low_fbx_path = os.path.join(export_dir, f"{asset_name}_low.fbx")
        high_fbx_path = os.path.join(export_dir, f"{asset_name}_high.fbx")
        
        # 2. Export meshes to FBX
        # Save selection state
        active_obj = context.view_layer.objects.active
        selected_objs = list(context.selected_objects)
        
        try:
            # Export low-poly
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = low_poly
            low_poly.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=low_fbx_path,
                use_selection=True,
                object_types={'MESH'},
                add_leaf_bones=False,
                bake_anim=False
            )
            
            # Export high-poly
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = high_poly
            high_poly.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=high_fbx_path,
                use_selection=True,
                object_types={'MESH'},
                add_leaf_bones=False,
                bake_anim=False
            )
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export meshes: {e}")
            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for o in selected_objs:
                o.select_set(True)
            context.view_layer.objects.active = active_obj
            return {'CANCELLED'}
            
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for o in selected_objs:
            o.select_set(True)
        context.view_layer.objects.active = active_obj
        
        # 3. Scan high-poly textures if enabled
        texture_assignments = {}
        expected_mats = []
        if props.send_textures:
            for slot in high_poly.material_slots:
                if slot.material:
                    tex_dict = find_material_textures(slot.material, export_dir)
                    if tex_dict:
                        texture_assignments[slot.material.name] = tex_dict
                        expected_mats.append(slot.material.name)
                        
        # 4. Generate Marmoset Script
        ext = props.file_format.lower()
        script_output_base = os.path.join(export_dir, f"{asset_name}.{ext}").replace("\\", "/")
        low_fbx_path_esc = os.path.normpath(low_fbx_path).replace("\\", "/")
        high_fbx_path_esc = os.path.normpath(high_fbx_path).replace("\\", "/")
        
        # Serialize texture assignments and expected mats to python literals
        import json
        tex_assign_str = json.dumps(texture_assignments)
        expected_mats_str = json.dumps(expected_mats)
        
        script_content = f"""import mset
import os
import time

mset.newScene()
baker = mset.BakerObject()
baker.outputPath = r"{script_output_base}"
baker.outputWidth = {props.resolution}
baker.outputHeight = {props.resolution}
baker.outputBits = 8
baker.outputSamples = 16


# Setup suffixes for auto sorting
normal_map = baker.getMap("Normals")
if normal_map:
    normal_map.enabled = True
    normal_map.suffix = "_normal"

ao_map = baker.getMap("Ambient Occlusion")
if ao_map:
    ao_map.enabled = True
    ao_map.suffix = "_ao"

curvature_map = baker.getMap("Curvature")
if curvature_map:
    curvature_map.enabled = True
    curvature_map.suffix = "_curvature"

# Import models via Quick Loader
baker.importModel(r"{low_fbx_path_esc}")
baker.importModel(r"{high_fbx_path_esc}")

# Asynchronous wait loop for FBX models to finish importing
expected_mats = {expected_mats_str}
start_time = time.time()
while time.time() - start_time < 8.0:
    current_mats = [m.name for m in mset.getAllMaterials()]
    matched_count = 0
    for exp_name in expected_mats:
        exp_clean = exp_name.lower().replace(" ", "").replace("_", "")
        for curr_name in current_mats:
            curr_clean = curr_name.lower().replace(" ", "").replace("_", "")
            if exp_clean == curr_clean or exp_clean in curr_clean or curr_clean in exp_clean:
                matched_count += 1
                break
    if matched_count >= len(expected_mats):
        break
    time.sleep(0.1)

# Assign high poly textures to materials
all_mats = {{m.name: m for m in mset.getAllMaterials()}}
texture_assignments = {tex_assign_str}

for mat_name, tex_dict in texture_assignments.items():
    mat = None
    if mat_name in all_mats:
        mat = all_mats[mat_name]
    else:
        # Case-insensitive fuzzy matching ignoring spaces, underscores, and suffixes
        target_clean = mat_name.lower().replace(" ", "").replace("_", "")
        for m_name, m_obj in all_mats.items():
            m_clean = m_name.lower().replace(" ", "").replace("_", "")
            if target_clean == m_clean or target_clean in m_clean or m_clean in target_clean:
                mat = m_obj
                break
                
    if mat:
        if 'albedo' in tex_dict and os.path.exists(tex_dict['albedo']):
            mat.setSubroutine("albedo", "Albedo")
            mat.albedo.setField("Albedo Map", mset.Texture(tex_dict['albedo']))
            
        if 'normal' in tex_dict and os.path.exists(tex_dict['normal']):
            mat.setSubroutine("surface", "Normals")
            mat.surface.setField("Normal Map", mset.Texture(tex_dict['normal']))
            
        if 'roughness' in tex_dict and os.path.exists(tex_dict['roughness']):
            mat.setSubroutine("microsurface", "Roughness")
            mat.microsurface.setField("Roughness Map", mset.Texture(tex_dict['roughness']))
            
        if 'metallic' in tex_dict and os.path.exists(tex_dict['metallic']):
            mat.setSubroutine("reflectivity", "Metalness")
            mat.reflectivity.setField("Metalness Map", mset.Texture(tex_dict['metallic']))

print("Marmoset Toolbag 5 setup complete.")
"""
        
        # Write to temporary file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp_name = tmp.name
        tmp.close() # Close immediately to release Windows locks!
        try:
            with open(tmp_name, "w", encoding="utf-8") as f:
                f.write(script_content)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write temp script: {e}")
            return {'CANCELLED'}
            
        # Launch Marmoset
        try:
            subprocess.Popen([marmoset_path, "-py", tmp_name])
            self.report({'INFO'}, "Sent meshes to Marmoset Toolbag 5")
            notify.success(f"FBX exported & Marmoset launched for {asset_name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to launch Marmoset Toolbag: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}


class REXTOOLS3_OT_marmoset_bridge_get_textures(Operator):
    bl_idname = "rextools3.marmoset_bridge_get_textures"
    bl_label = "Import Baked Textures"
    bl_description = "Scan the export path for baked maps and assign them to the low-poly material nodes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.rex_marmoset_bridge_props
        
        # Determine export directory
        export_dir = bpy.path.abspath(props.export_path)
        if not export_dir:
            if bpy.data.filepath:
                export_dir = os.path.dirname(bpy.data.filepath)
            else:
                self.report({'ERROR'}, "Save the blend file first, or specify a Bake Output Path.")
                return {'CANCELLED'}
                
        # Resolve asset name
        asset_name = props.asset_name.strip()
        if not asset_name:
            asset_name = MESH_OT_auto_rename_high_low.clean_base_name(obj.name)
            if not asset_name:
                self.report({'ERROR'}, "Please specify the Asset Name.")
                return {'CANCELLED'}
                
        if not os.path.exists(export_dir):
            self.report({'ERROR'}, f"Bake Output Path does not exist: {export_dir}")
            return {'CANCELLED'}
            
        # Search for baked files
        pattern = os.path.join(export_dir, f"{asset_name}*")
        files = glob.glob(pattern)
        
        if not files:
            self.report({'WARNING'}, f"No baked files found starting with '{asset_name}' in: {export_dir}")
            return {'CANCELLED'}
            
        # Suffix matching lists
        map_types = {
            'Normal': ['_normal', '_normals', '_normal_map'],
            'AO': ['_ao', '_ambient_occlusion', '_occlusion'],
            'Height': ['_height', '_displacement'],
            'Curvature': ['_curvature', '_curve'],
            'Thickness': ['_thickness'],
        }
        
        # Associate map types with found files
        found_maps = {}
        for filepath in files:
            filename = os.path.basename(filepath)
            name_no_ext, _ = os.path.splitext(filename)
            name_no_ext = name_no_ext.lower()
            
            for m_type, suffixes in map_types.items():
                for suffix in suffixes:
                    if name_no_ext.endswith(suffix):
                        found_maps[m_type] = filepath
                        break
                        
        if not found_maps:
            self.report({'WARNING'}, f"No baked map matching suffixes (like _normal, _ao) found for '{asset_name}'")
            return {'CANCELLED'}
            
        # Assign to all materials on the active low-poly object
        assigned_mats_count = 0
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
                
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            # Find or create Principled BSDF
            principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if not principled:
                principled = nodes.new('ShaderNodeBsdfPrincipled')
                principled.location = (0, 0)
                
            # Find or create Material Output
            output_node = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
            if not output_node:
                output_node = nodes.new('ShaderNodeOutputMaterial')
                output_node.location = (300, 0)
                
            # Link BSDF to output
            surface_input = output_node.inputs.get('Surface')
            if surface_input and not surface_input.is_linked:
                links.new(principled.outputs['BSDF'], surface_input)
                
            # Connect maps
            for map_type, filepath in found_maps.items():
                img_name = os.path.basename(filepath)
                
                # Check for existing image block to prevent duplicates
                img = bpy.data.images.get(img_name)
                if img:
                    img.filepath = filepath
                    img.reload()
                else:
                    img = bpy.data.images.load(filepath)
                    
                # Always set to Non-Color for data maps
                img.colorspace_settings.name = 'Non-Color'
                
                # Find or create image node
                tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.label == f"Baked {map_type}"), None)
                if not tex_node:
                    tex_node = nodes.new('ShaderNodeTexImage')
                    tex_node.label = f"Baked {map_type}"
                    
                tex_node.image = img
                
                # Position node dynamically
                y_offsets = {
                    'Normal': -150,
                    'AO': 300,
                    'Height': -300,
                    'Curvature': -450,
                    'Thickness': -600
                }
                tex_node.location = (-600, y_offsets.get(map_type, 0))
                
                # Link based on type
                if map_type == 'Normal':
                    # Create Normal Map helper node
                    normal_map_node = next((n for n in nodes if n.type == 'NORMAL_MAP'), None)
                    if not normal_map_node:
                        normal_map_node = nodes.new('ShaderNodeNormalMap')
                        normal_map_node.location = (-300, -150)
                        
                    links.new(tex_node.outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    
                elif map_type == 'AO':
                    # Multiply Albedo with AO
                    base_color_input = principled.inputs.get('Base Color')
                    if base_color_input:
                        ao_mix = next((n for n in nodes if n.type in {'MIX', 'MIX_RGB'} and n.label == "AO Multiply"), None)
                        if not ao_mix:
                            ao_mix = nodes.new('ShaderNodeMix')
                            ao_mix.label = "AO Multiply"
                            ao_mix.data_type = 'RGBA'
                            ao_mix.blend_type = 'MULTIPLY'
                            ao_mix.inputs['Factor'].default_value = 1.0
                            ao_mix.location = (-150, 200)
                            
                            # Wire original link to slot A
                            if base_color_input.is_linked:
                                old_out = base_color_input.links[0].from_socket
                                links.new(old_out, ao_mix.inputs['A'])
                            else:
                                ao_mix.inputs['A'].default_value = base_color_input.default_value
                                
                            links.new(ao_mix.outputs['Result'], base_color_input)
                            
                        links.new(tex_node.outputs['Color'], ao_mix.inputs['B'])
                else:
                    # Height, Curvature, Thickness - place node without automatic links to BSDF (optional utility maps)
                    pass
                    
            assigned_mats_count += 1
            
        if assigned_mats_count > 0:
            notify.success(f"Assigned {len(found_maps)} baked maps to {assigned_mats_count} material(s) on {obj.name}")
        else:
            self.report({'WARNING'}, "No materials found on active object to assign textures")
            return {'CANCELLED'}
            
        return {'FINISHED'}
