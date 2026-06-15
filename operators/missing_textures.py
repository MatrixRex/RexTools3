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

        img.filepath = self.filepath
        try:
            img.reload()
        except Exception as e:
            self.report({'ERROR'}, f"Failed to reload image: {e}")
            return {'CANCELLED'}
            
        # Re-trigger the scan to update the UI
        bpy.ops.rextools3.scan_missing_textures()
        
        notify.success(f"Reassigned '{img.name}' to '{os.path.basename(self.filepath)}'")
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
