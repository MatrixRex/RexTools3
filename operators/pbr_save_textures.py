import bpy
from bpy.types import Operator
from ..core import notify

class PBR_OT_SaveTextures(Operator):
    bl_idname = "pbr.save_textures"
    bl_label = "Save Textures"
    bl_description = "Pack and unpack all textures used by this material, saving them to a local 'textures' directory"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.active_material and obj.active_material.use_nodes

    def execute(self, context):
        if not bpy.data.is_saved:
            notify.warning("Please save the blend file first!")
            return {'CANCELLED'}

        mat = context.active_object.active_material
        nodes = mat.node_tree.nodes

        # Gather all unique file/sequence based images in the material
        images = set()
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                img = node.image
                if img.source in {'FILE', 'SEQUENCE'}:
                    images.add(img)

        if not images:
            notify.info("No file-based textures found in this material.")
            return {'CANCELLED'}

        import os
        blend_dir = os.path.dirname(bpy.data.filepath)
        textures_dir = os.path.join(blend_dir, "textures")
        os.makedirs(textures_dir, exist_ok=True)

        saved_count = 0
        for img in images:
            # Determine extension from original filepath or fallback to file format
            ext = ""
            if img.filepath:
                ext = os.path.splitext(img.filepath)[1]
            if not ext:
                FORMAT_EXTENSIONS = {
                    'BMP': '.bmp',
                    'PNG': '.png',
                    'JPEG': '.jpg',
                    'JPEG2000': '.jp2',
                    'TARGA': '.tga',
                    'TARGA_RAW': '.tga',
                    'CINEON': '.cin',
                    'DPX': '.dpx',
                    'MULTILAYER': '.exr',
                    'OPEN_EXR': '.exr',
                    'OPEN_EXR_MULTILAYER': '.exr',
                    'HDR': '.hdr',
                    'TIFF': '.tif',
                    'WEBP': '.webp',
                }
                ext = FORMAT_EXTENSIONS.get(img.file_format, '.png')

            # Clean the image's renamed name in Blender to make it a valid filename
            clean_name = "".join(c for c in img.name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not clean_name:
                clean_name = "texture"
            filename = f"{clean_name}{ext}"

            dest_path = os.path.join(textures_dir, filename)

            try:
                if img.source == 'SEQUENCE':
                    # Fallback for image sequences: use native pack & unpack
                    if not img.packed_file:
                        img.pack()
                    img.filepath = f"//textures/{filename}"
                    override = context.copy()
                    override["edit_image"] = img
                    with context.temp_override(**override):
                        bpy.ops.image.unpack(id=img.name, method='USE_LOCAL')
                else:
                    # For normal FILE textures, force load pixels into memory if not loaded
                    if not img.has_data:
                        _ = img.pixels[0]

                    # Save the image from memory to the destination path.
                    # We temporarily set filepath_raw to the absolute target path, which prevents
                    # Blender from trying to read/verify a non-existent relative path or clearing
                    # the pixels in memory, then call save().
                    img.filepath_raw = dest_path
                    img.save()

                    # Link to the newly saved local relative path
                    img.filepath = f"//textures/{filename}"

                saved_count += 1
            except Exception as e:
                self.report({'ERROR'}, f"Failed to save texture {img.name}: {str(e)}")

        if saved_count > 0:
            notify.success(f"Successfully saved {saved_count} texture(s) to local 'textures' folder.")
        else:
            notify.warning("No textures were saved.")

        return {'FINISHED'}
