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

        saved_count = 0
        for img in images:
            try:
                # Pack the image first if it's not packed
                if not img.packed_file:
                    img.pack()
                
                # Unpack the image locally using context override
                override = context.copy()
                override["edit_image"] = img
                with context.temp_override(**override):
                    bpy.ops.image.unpack(id=img.name, method='USE_LOCAL')
                saved_count += 1
            except Exception as e:
                self.report({'ERROR'}, f"Failed to save texture {img.name}: {str(e)}")

        if saved_count > 0:
            notify.success(f"Successfully saved {saved_count} texture(s) to local 'textures' folder.")
        else:
            notify.warning("No textures were saved.")

        return {'FINISHED'}
