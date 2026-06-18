import bpy
import os
from pathlib import Path
from bpy.types import Operator
from ..core import notify
from .pbr_assign import PBR_OT_AssignTexture, _find_matches_in_dir

class PBR_OT_BatchInit(Operator):
    """Gather unique materials from selected objects"""
    bl_idname = "pbr.batch_init"
    bl_label = "Get Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.rex_batch_mat_props
        props.items.clear()

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            notify.warning("No mesh objects selected")
            return {'CANCELLED'}

        unique_mats = set()
        for obj in selected_objects:
            for slot in obj.material_slots:
                if slot.material:
                    unique_mats.add(slot.material)

        if not unique_mats:
            notify.warning("No materials found on selected objects")
            return {'CANCELLED'}

        # Sort materials by name for a cleaner list
        sorted_mats = sorted(list(unique_mats), key=lambda m: m.name)

        for mat in sorted_mats:
            item = props.items.add()
            item.material_name = mat.name
            item.status = "Pending"
            item.is_assigned = False

        notify.success(f"Gathered {len(props.items)} materials")
        return {'FINISHED'}


class PBR_OT_BatchAssignTextures(Operator):
    """Batch assign textures to gathered materials"""
    bl_idname = "pbr.batch_assign_textures"
    bl_label = "Batch Assign Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.rex_batch_mat_props
        if not props.items:
            notify.warning("No materials in the list. Run Init first.")
            return {'CANCELLED'}

        folder_path = bpy.path.abspath(props.target_folder)
        if not folder_path or not os.path.exists(folder_path):
            notify.error("Invalid texture folder path")
            return {'CANCELLED'}

        folder = Path(folder_path)
        recursive = props.recursive

        suffix_map = {
            'Base Color': ['albedo', 'basecolor', 'base_color', 'diffuse', 'color', 'col', 'bc', 'd', 'c'],
            'Roughness': ['roughness', 'rough', 'rgh', 'smoothness', 'gloss', 'glossiness', 'r'],
            'Metallic':  ['metallic', 'metal', 'metalness', 'mtl', 'm', 'met'],
            'Normal':    ['normal', 'norm', 'nrm', 'nmap', 'nm', 'n'],
            'Alpha':     ['alpha', 'opacity', 'transparency', 'a'],
            'AO':        ['ao', 'ambientocclusion', 'occ'],
            'Emission':  ['emissive', 'emission', 'emit', 'glow', 'e'],
            'Height':    ['height', 'disp', 'displacement', 'h'],
        }

        # Gather all folders to search
        search_folders = [folder]
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for d in dirs:
                    search_folders.append(Path(root) / d)

        assigned_count = 0
        total_mats = len(props.items)

        for item in props.items:
            mat = bpy.data.materials.get(item.material_name)
            if not mat:
                item.status = "Material not found in data"
                continue

            stems_to_try = [mat.name.lower()]
            if mat.name.lower() != mat.name.rstrip().lower():
                stems_to_try.append(mat.name.rstrip().lower())

            matches = {}

            # Search in all collected folders for each stem
            for stem_val in stems_to_try:
                for f in search_folders:
                    folder_matches = _find_matches_in_dir(stem_val, f, suffix_map)
                    # Merge matches
                    for slot, path in folder_matches.items():
                        if slot not in matches:
                            matches[slot] = path
                    
                    if len(matches) == len(suffix_map):
                        break
                if len(matches) == len(suffix_map):
                    break

            if matches:
                any_ok = False
                slots_assigned = []
                for slot, path in matches.items():
                    colorspace = 'Non-Color' if slot in ('Roughness', 'Metallic', 'Normal', 'Alpha') else 'sRGB'
                    ok = PBR_OT_AssignTexture.assign_texture_to_input(context, mat, slot, str(path), colorspace)
                    if ok:
                        any_ok = True
                        slots_assigned.append(slot)

                if any_ok:
                    formatted_slots = [f"✓ {slot}" for slot in slots_assigned]
                    item.status = ", ".join(formatted_slots)
                    item.is_assigned = True
                    assigned_count += 1
                else:
                    item.status = "Failed to assign"
                    mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)
            else:
                item.status = "No textures found"
                item.is_assigned = False
                mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)

        bpy.ops.pbr.arrange_nodes()
        notify.success(f"Batch assignment complete. {assigned_count}/{total_mats} materials updated.")
        return {'FINISHED'}
