import bpy
from ..core import notify

class REXTOOLS3_OT_extract_textures(bpy.types.Operator):
    """Pack all textures then unpack them to a local 'textures' folder.
    This helps in organizing external dependencies."""
    bl_idname = "rextools3.extract_textures"
    bl_label = "Extract Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not bpy.data.is_saved:
            notify.warning("Please save the file first!")
            return {'CANCELLED'}
        
        try:
            # First pack everything to ensure we have all textures
            bpy.ops.file.pack_all()
            
            # Then unpack using local folder method
            # USE_LOCAL creates a 'textures' folder relative to the blend file
            bpy.ops.file.unpack_all(method='USE_LOCAL')
            
            notify.success("Textures extracted to local folder.")
            return {'FINISHED'}
        except Exception as e:
            notify.error(f"Error extracting textures: {str(e)}")
            return {'CANCELLED'}
