import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from ..core import notify


def check_file_exists(img):
    """Check if an image's external file exists on disk, supporting UDIM textures."""
    if not img.filepath:
        return False
    
    filepath = bpy.path.abspath(img.filepath)
    if os.path.exists(filepath):
        return True
    
    # Handle UDIM tile naming patterns (e.g., texture_<UDIM>.png)
    if "<UDIM>" in filepath:
        if os.path.exists(filepath.replace("<UDIM>", "1001")):
            return True
    if "<udim>" in filepath:
        if os.path.exists(filepath.replace("<udim>", "1001")):
            return True
            
    return False


def find_referencing_materials(img):
    """Find all materials referencing the given image datablock."""
    referencing_mats = []
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image == img:
                    referencing_mats.append(mat.name)
                    break
    return referencing_mats


def trace_slot_from_node(node):
    """Trace from a texture image node to determine its corresponding PBR slot and colorspace."""
    name_lower = node.name.lower()
    label_lower = node.label.lower() if node.label else ""
    
    # 1. Quick detection using names/labels (common in Easy PBR)
    if "base" in name_lower or "base" in label_lower or "diffuse" in name_lower or "diffuse" in label_lower:
        return "Base Color", "sRGB"
    if "rough" in name_lower or "rough" in label_lower:
        return "Roughness", "Non-Color"
    if "metal" in name_lower or "metal" in label_lower:
        return "Metallic", "Non-Color"
    if "normal" in name_lower or "normal" in label_lower:
        return "Normal", "Non-Color"
    if "ao" in name_lower or "ao" in label_lower or "occlusion" in name_lower or "occlusion" in label_lower:
        return "AO", "Non-Color"
    if "alpha" in name_lower or "alpha" in label_lower or "opacity" in name_lower or "opacity" in label_lower:
        return "Alpha", "Non-Color"
    if "height" in name_lower or "height" in label_lower or "displace" in name_lower or "displace" in label_lower or "bump" in name_lower or "bump" in label_lower:
        return "Height", "Non-Color"
    if "emission" in name_lower or "emission" in label_lower:
        return "Emission", "sRGB"
        
    # 2. Trace links forward
    visited = {node}
    queue = [node]
    while queue:
        curr = queue.pop(0)
        for output in curr.outputs:
            for link in output.links:
                to_node = link.to_node
                to_socket = link.to_socket
                
                # Direct links to BSDF_PRINCIPLED
                if to_node.type == 'BSDF_PRINCIPLED':
                    socket_name = to_socket.name
                    if socket_name == 'Base Color':
                        return "Base Color", "sRGB"
                    elif socket_name in ('Roughness', 'Metallic', 'Normal', 'Alpha', 'Emission'):
                        colorspace = 'sRGB' if socket_name in ('Base Color', 'Emission') else 'Non-Color'
                        return socket_name, colorspace
                # Link to helper nodes
                elif to_node.type == 'NORMAL_MAP':
                    return "Normal", "Non-Color"
                elif to_node.type == 'DISPLACEMENT':
                    return "Height", "Non-Color"
                elif to_node.name in ("PBR AO Mix", "AOMix"):
                    return "AO", "Non-Color"
                elif to_node.name == "BaseTintMix":
                    return "Base Color", "sRGB"
                elif to_node.name == "EmissionTintMix":
                    return "Emission", "sRGB"
                
                if to_node not in visited:
                    visited.add(to_node)
                    queue.append(to_node)
                    
    # Fallback default
    return "Base Color", "sRGB"


class REXTOOLS3_OT_ScanMissingTextures(Operator):
    bl_idname = "rextools3.scan_missing_textures"
    bl_label = "Scan Missing Textures"
    bl_description = "Scan the project for missing external texture files and identify referencing materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scanner = context.scene.rex_missing_texture_scanner
        scanner.items.clear()
        
        missing_count = 0
        
        for img in bpy.data.images:
            # Only check external unpacked file-based images
            if img.source not in {'FILE', 'SEQUENCE', 'TILED'}:
                continue
            if img.packed_file is not None:
                continue
                
            if not check_file_exists(img):
                missing_count += 1
                mats = find_referencing_materials(img)
                
                item = scanner.items.add()
                item.image_name = img.name
                item.filepath = bpy.path.abspath(img.filepath) if img.filepath else ""
                item.materials = ", ".join(mats)
                
        scanner.has_scanned = True
        
        if missing_count > 0:
            notify.warning(f"Found {missing_count} missing texture(s)!")
        else:
            notify.success("Scan complete: No missing textures found.")
            
        return {'FINISHED'}


class REXTOOLS3_OT_ReassignMissingTexture(Operator, ImportHelper):
    bl_idname = "rextools3.reassign_missing_texture"
    bl_label = "Reassign Texture"
    bl_description = "Select a replacement file for this missing texture datablock"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to the replacement texture file",
        subtype='FILE_PATH'
    )
    
    # Store target image name to know which image datablock we are reassigning
    image_name: StringProperty(options={'HIDDEN'})

    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff;*.exr;*.bmp;*.webp",
        options={'HIDDEN'}
    )

    def execute(self, context):
        img = bpy.data.images.get(self.image_name)
        if not img:
            self.report({'ERROR'}, f"Image datablock '{self.image_name}' not found")
            return {'CANCELLED'}

        # Identify referencing materials and corresponding slots
        node_slots = []
        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == img:
                        slot_name, colorspace = trace_slot_from_node(node)
                        node_slots.append((mat, slot_name, colorspace))

        # Reassign filepath of the image block first to preserve other references
        img.filepath = self.filepath
        try:
            img.reload()
        except Exception as e:
            self.report({'ERROR'}, f"Failed to reload image: {e}")
            return {'CANCELLED'}

        # Re-assign specifically to Easy PBR slots
        from .pbr_assign import PBR_OT_AssignTexture
        assigned_count = 0
        active_obj = context.active_object
        original_mat = active_obj.active_material if (active_obj and hasattr(active_obj, "active_material")) else None

        for mat, slot_name, colorspace in node_slots:
            if active_obj and hasattr(active_obj, "active_material"):
                active_obj.active_material = mat
            
            ok = PBR_OT_AssignTexture.assign_texture_to_input(context, mat, slot_name, self.filepath, colorspace)
            if ok:
                assigned_count += 1
                try:
                    bpy.ops.pbr.arrange_nodes()
                except Exception:
                    pass

        # Restore original active material
        if active_obj and hasattr(active_obj, "active_material") and original_mat:
            active_obj.active_material = original_mat

        # Clean up old image if no longer used
        if img.users == 0:
            try:
                bpy.data.images.remove(img)
            except Exception:
                pass

        # Re-trigger the scan to update the UI
        bpy.ops.rextools3.scan_missing_textures()
        
        notify.success(f"Reassigned '{self.image_name}' to {assigned_count} slot(s) in reference materials.")
        return {'FINISHED'}


class REXTOOLS3_OT_CleanMissingTexture(Operator):
    bl_idname = "rextools3.clean_missing_texture"
    bl_label = "Clean Missing Texture"
    bl_description = "Remove this missing image datablock and its referencing texture nodes from all materials"
    bl_options = {'REGISTER', 'UNDO'}

    image_name: StringProperty(
        name="Image Name",
        description="Name of the image datablock to clean"
    )

    def execute(self, context):
        if not self.image_name:
            self.report({'ERROR'}, "No image name specified")
            return {'CANCELLED'}

        img = bpy.data.images.get(self.image_name)
        removed_nodes_count = 0
        removed_images_count = 0

        # 1. Clean referencing nodes in materials
        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree:
                nodes_to_remove = []
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == img:
                        nodes_to_remove.append(node)
                        
                for node in nodes_to_remove:
                    try:
                        mat.node_tree.nodes.remove(node)
                        removed_nodes_count += 1
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to remove texture node from material '{mat.name}': {e}")

        # 2. Clean image datablock
        if img:
            try:
                bpy.data.images.remove(img)
                removed_images_count += 1
            except Exception as e:
                self.report({'WARNING'}, f"Failed to remove image datablock '{self.image_name}': {e}")

        # Re-trigger the scan to update the UI
        bpy.ops.rextools3.scan_missing_textures()

        notify.success(f"Removed '{self.image_name}' and {removed_nodes_count} referencing node(s).")
        return {'FINISHED'}


class REXTOOLS3_OT_CleanMissingTextures(Operator):
    bl_idname = "rextools3.clean_missing_textures"
    bl_label = "Clean All Missing"
    bl_description = "Remove all missing image datablocks and their referencing texture nodes from all materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scanner = context.scene.rex_missing_texture_scanner
        return scanner.has_scanned and len(scanner.items) > 0

    def execute(self, context):
        scanner = context.scene.rex_missing_texture_scanner
        
        image_names = [item.image_name for item in scanner.items]
        removed_nodes_count = 0
        removed_images_count = 0
        
        # 1. Clean referencing nodes in materials
        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree:
                nodes_to_remove = []
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image and node.image.name in image_names:
                        nodes_to_remove.append(node)
                        
                for node in nodes_to_remove:
                    try:
                        mat.node_tree.nodes.remove(node)
                        removed_nodes_count += 1
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to remove texture node from material '{mat.name}': {e}")
                        
        # 2. Clean image datablocks
        for img_name in image_names:
            img = bpy.data.images.get(img_name)
            if img:
                try:
                    bpy.data.images.remove(img)
                    removed_images_count += 1
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to remove image datablock '{img_name}': {e}")
                    
        # Reset scanner state
        scanner.items.clear()
        scanner.has_scanned = True
        
        notify.success(f"Removed {removed_images_count} missing image(s) and {removed_nodes_count} node(s).")
        return {'FINISHED'}
