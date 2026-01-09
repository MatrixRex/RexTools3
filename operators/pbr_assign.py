import bpy
import os
import re
from pathlib import Path
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_principled_and_base_tex(material):
    """Return (principled_node, base_texture_node, base_image) or (None,None,None)."""
    if not material or not material.use_nodes:
        return None, None, None
    nodes = material.node_tree.nodes
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return None, None, None

    # 1. Easy check: Look for the named BaseTex directly
    base_tex = nodes.get("BaseTex")
    if base_tex and base_tex.type == 'TEX_IMAGE' and base_tex.image:
        return principled, base_tex, base_tex.image

    # 2. Fallback: Crawl back from BSDF
    base_inp = principled.inputs.get('Base Color')
    if not base_inp or not base_inp.is_linked:
        return principled, None, None

    curr = base_inp.links[0].from_node
    tex = None
    
    # Simple loop to step back through any Tint or AO mix nodes
    # We follow the 'A' or 'Color1' slot back
    while curr:
        if curr.type == 'TEX_IMAGE':
            tex = curr
            break
        
        # Follow the chain backwards
        next_node = None
        # Handle BaseTintMix, AOMix, or generic Mix nodes
        if curr.type in ('MIX', 'MIX_RGB'):
            # Slot A for 'MIX', Slot Color1 for 'MIX_RGB'
            a_sock = curr.inputs.get('A') or curr.inputs.get('Color1')
            if a_sock and a_sock.is_linked:
                next_node = a_sock.links[0].from_node
        
        if not next_node: break
        curr = next_node

    img = tex.image if tex else None
    return principled, tex, img


def _derive_stem_from_base(filename_no_ext_lower: str) -> str:
    """
    Try to peel off common base-color suffixes (and combos) from the end
    to derive a 'stem' for matching. Handles cases like:
      MCX_Mat_AlbedoTransparency -> mcx_mat
      bullet_albedo               -> bullet
    """
    # allow compound endings like "albedotransparency"
    suffixes = [
        'albedo', 'basecolor', 'base_color', 'base-colour', 'basecolour',
        'diffuse', 'color', 'colour', 'col',
        'opacity', 'transparency'
    ]
    # Try compound endings first (albedo+opacity/transparency)
    patt_combo = r'(.+?)(?:[_\-]?(?:albedo|basecolor|base_color|base\-colour|basecolour|diffuse|color|colour|col))' \
                 r'(?:[_\-]?(?:opacity|transparency))$'
    m = re.match(patt_combo, filename_no_ext_lower, re.IGNORECASE)
    if m:
        return m.group(1)

    # Then single endings
    patt_single = r'(.+?)(?:[_\-]?(?:' + '|'.join(suffixes) + r'))$'
    m = re.match(patt_single, filename_no_ext_lower, re.IGNORECASE)
    if m:
        return m.group(1)

    return filename_no_ext_lower


def _find_matches_in_dir(stem_lower: str, folder: Path, mapping: dict) -> dict:
    """Return dict slot->Path for first found match per slot."""
    exts = {'.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff', '.exr', '.bmp', '.webp'}
    results = {}
    if not folder.exists() or not folder.is_dir():
        return results

    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    names = [(p, p.stem.lower()) for p in files]

    for slot, suffixes in mapping.items():
        found = None
        # prefer longer suffix tokens
        for suf in sorted(suffixes, key=len, reverse=True):
            for p, n in names:
                # common pattern in studios: "{stem}_[...]_{suffix}" or "{stem}_{suffix}[...]"
                if n.startswith(stem_lower) and suf in n:
                    found = p
                    break
            if found:
                break
        if found:
            results[slot] = found
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Assign Texture Operator (existing)
# ─────────────────────────────────────────────────────────────────────────────

class PBR_OT_AssignTexture(Operator):
    bl_idname = "pbr.assign_texture"
    bl_label = "Assign Texture"
    bl_options = {'REGISTER', 'UNDO'}

    input_name: StringProperty()
    colorspace: StringProperty(default='sRGB')
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff;*.exr;*.bmp;*.webp', options={'HIDDEN'})
    filter_image: BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        mat = context.active_object.active_material
        if not mat:
            self.report({'ERROR'}, "No active material")
            return {'CANCELLED'}

        ok = self.assign_texture_to_input(mat, self.input_name, self.filepath, self.colorspace)
        if not ok:
            self.report({'ERROR'}, "Failed to assign texture")
            return {'CANCELLED'}

        bpy.ops.pbr.arrange_nodes()
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filter_image = True
        self.filter_glob = '*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff;*.exr;*.bmp;*.webp'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @staticmethod
    def assign_texture_to_input(material, input_name, image_path, colorspace='sRGB'):
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        principled = next((n for n in nodes if n.type=='BSDF_PRINCIPLED'), None)
        if not principled:
            return False

        try:
            image = bpy.data.images.load(image_path)
        except Exception:
            return False

        if input_name == 'Base Color':
            image.alpha_mode = 'CHANNEL_PACKED'
        image.colorspace_settings.name = colorspace

        # Capture current tint if we are assigning to Base Color, so we can preserve it
        current_tint = (1.0, 1.0, 1.0, 1.0)
        if input_name == 'Base Color':
            bc_inp = principled.inputs.get('Base Color')
            if bc_inp:
                if bc_inp.is_linked:
                    src = bc_inp.links[0].from_node
                    if src.type == 'MIX_RGB':
                        current_tint = src.inputs['Color2'].default_value[:]
                else:
                    current_tint = bc_inp.default_value[:]

        # remove old chain
        def gather(n, out):
            if n in out: return
            out.add(n)
            for i in n.inputs:
                if i.is_linked:
                    gather(i.links[0].from_node, out)

        if input_name == 'AO':
            # For AO, we check our specific Mix node instead of a BSDF socket
            ao_mix = nodes.get("PBR AO Mix")
            if ao_mix:
                to_del = set()
                # Gather everything behind Color2 (which is the AO side)
                ao_in = ao_mix.inputs.get('Color2')
                if ao_in and ao_in.is_linked:
                    gather(ao_in.links[0].from_node, to_del)
                # Note: we don't remove the ao_mix itself here because we recreate it below
                # or the logic below will handle it. Actually, easiest is to just delete if it exists.
                for n in to_del:
                    try: nodes.remove(n)
                    except: pass
                # Clean up the specific named helper nodes too
                for name in ["AOSplit", "AOMix", "AOTex"]:
                    node = nodes.get(name)
                    if node:
                        try: nodes.remove(node)
                        except: pass
        else:
            # Standard BSDF socket logic
            inp_sock = principled.inputs.get(input_name)
            if inp_sock and inp_sock.is_linked:
                to_del = set()
                gather(inp_sock.links[0].from_node, to_del)
                for l in list(inp_sock.links):
                    links.remove(l)
                for n in to_del:
                    try:
                        nodes.remove(n)
                    except Exception:
                        pass

        base_pos = {
            'Base Color': 200,
            'Metallic':   100,
            'Roughness':    0,
            'Normal':     -100,
            'Alpha':      -200,
            'AO':         250,
        }
        y = base_pos.get(input_name, 0)
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-400, y)
        if input_name == 'Base Color':
            tex_node.name = "BaseTex"
        elif input_name == 'AO':
            tex_node.name = "AOTex"
        else:
            tex_node.name = f"{input_name}Tex"
            
        settings = material.pbr_settings

        settings = material.pbr_settings

        if input_name == 'Normal':
            nm = nodes.new('ShaderNodeNormalMap')
            nm.location = (-150, y)
            links.new(tex_node.outputs['Color'], nm.inputs['Color'])
            links.new(nm.outputs['Normal'], principled.inputs['Normal'])
            return True

        if input_name == 'Alpha':
            links.new(tex_node.outputs['Color'], principled.inputs['Alpha'])
            material.blend_method = 'BLEND'
            return True

        if input_name == 'Base Color':
            mix = nodes.new('ShaderNodeMix')
            mix.name = "BaseTintMix"
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.location = (-150, y)
            links.new(tex_node.outputs['Color'], mix.inputs['A'])
            mix.inputs['B'].default_value = current_tint
            links.new(mix.outputs['Result'], principled.inputs['Base Color'])
            if not settings.use_separate_alpha_map:
                links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'HASHED'
            return True

        if input_name == 'AO':
            # Create the AOMix node
            ao_mix = nodes.new('ShaderNodeMix')
            ao_mix.name = "AOMix"
            ao_mix.data_type = 'RGBA'
            ao_mix.blend_type = 'MULTIPLY'
            ao_mix.location = (-50, y)
            ao_mix.inputs['Factor'].default_value = getattr(settings, "ao_strength")
            
            # AO source (channeled or full)
            chan = getattr(settings, "ao_channel")
            src = tex_node.outputs['Color']
            if chan == 'A':
                src = tex_node.outputs['Alpha']
            elif chan != 'FULL':
                sep = nodes.new('ShaderNodeSeparateRGB')
                sep.name = "AOSplit"
                sep.location = (-250, y)
                links.new(tex_node.outputs['Color'], sep.inputs['Image'])
                src = sep.outputs[chan]
            
            # Mix Setup: slot A (Base Color chain) * slot B (AO) -> BSDF
            bc_inp = principled.inputs['Base Color']
            if bc_inp.is_linked:
                old_out = bc_inp.links[0].from_socket
                links.new(old_out, ao_mix.inputs['A'])
            else:
                ao_mix.inputs['A'].default_value = bc_inp.default_value
                
            links.new(src, ao_mix.inputs['B'])
            links.new(ao_mix.outputs['Result'], bc_inp)
            return True

        # Roughness / Metallic (always via Math node)
        math = nodes.new('ShaderNodeMath')
        math.operation = 'MULTIPLY'
        math.use_clamp = True  # keep outputs within 0..1
        math.location = (-150, y)
        math.name = f"{input_name}Math"

        chan = getattr(settings, f"{input_name.lower()}_channel")
        if chan == 'FULL':
            links.new(tex_node.outputs['Color'], math.inputs[0])
        else:
            if chan == 'A':
                src = tex_node.outputs['Alpha']
            else:
                sep = nodes.new('ShaderNodeSeparateRGB')
                sep.name = f"{input_name}Split"
                sep.location = (-250, y)
                links.new(tex_node.outputs['Color'], sep.inputs['Image'])
                src = sep.outputs[chan]
            links.new(src, math.inputs[0])

        math.inputs[1].default_value = getattr(settings, f"{input_name.lower()}_strength")
        links.new(math.outputs['Value'], principled.inputs[input_name])
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Auto Load Operator
# ─────────────────────────────────────────────────────────────────────────────

class PBR_OT_AutoLoadTextures(Operator):
    bl_idname = "pbr.auto_load_textures"
    bl_label = "Auto Load PBR Textures"
    bl_options = {'REGISTER', 'UNDO'}

    

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            return False
        mat = obj.active_material
        principled, tex_node, img = _get_principled_and_base_tex(mat)
        if not img:
            return False
        # Ensure it has a resolvable filepath (not purely packed)
        fp = bpy.path.abspath(img.filepath, library=img.library) if hasattr(img, 'library') else bpy.path.abspath(img.filepath)
        return bool(fp)

    def execute(self, context):
        obj = context.active_object
        mat = obj.active_material
        if not mat:
            self.report({'ERROR'}, "No active material")
            return {'CANCELLED'}

        principled, base_tex, base_img = _get_principled_and_base_tex(mat)
        if not base_img:
            self.report({'ERROR'}, "Assign Base Color first")
            return {'CANCELLED'}

        base_path = bpy.path.abspath(base_img.filepath, library=base_img.library) if hasattr(base_img, 'library') else bpy.path.abspath(base_img.filepath)
        if not base_path or not os.path.exists(base_path):
            self.report({'ERROR'}, "Base Color image path not found on disk")
            return {'CANCELLED'}

        base_path = Path(base_path)
        folder = base_path.parent
        # Read the toggle + custom name from the material settings, not the operator
        use_auto = getattr(mat.pbr_settings, "use_auto_common_name", True)
        custom  = (getattr(mat.pbr_settings, "common_name", "") or "").strip().lower()

        stem_lower = (
            _derive_stem_from_base(base_path.stem.lower())
            if use_auto
            else (custom if custom else base_path.stem.lower())
        )


        # Slot -> acceptable suffix tokens (lowercase)
        suffix_map = {
            'Roughness': ['_roughness', '_rough', '_rgh', '_r','_smoothness'],
            'Metallic':  ['_metallic', '_metal', '_metalness', '_mtl', '_m', '_metalSmoothness'],
            'Normal':    ['_normal', '_norm', '_nrm', '_normalgl', '_normal_dx', '_normal_ogl','_n'],
            'Alpha':     ['_alpha', '_opacity', '_transparency'],
            'AO':        ['_ao', '_ambientocclusion', '_ambient_occlusion', '_occ'],
        }

        matches = _find_matches_in_dir(stem_lower, folder, suffix_map)

        assigned_slots = []  # List to keep track of assigned texture slots

        # Assign found textures
        any_assigned = False
        for slot, file_path in matches.items():
            colorspace = 'Non-Color' if slot in ('Roughness', 'Metallic', 'Normal', 'Alpha') else 'sRGB'
            ok = PBR_OT_AssignTexture.assign_texture_to_input(mat, slot, str(file_path), colorspace)
            if ok:
                assigned_slots.append(f"{slot}")
                any_assigned = True

        if any_assigned:
            # Reporting which slots were filled
            self.report({'INFO'}, f"Textures assigned: {', '.join(assigned_slots)}")
            bpy.ops.pbr.arrange_nodes()
            return {'FINISHED'}
        else:
            self.report({'INFO'}, "No matching textures found in folder.")
            return {'CANCELLED'}

