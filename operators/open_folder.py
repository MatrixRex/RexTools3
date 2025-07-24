# open_folder.py
import bpy
import os
import sys
import subprocess

class REXTOOLS3_OT_open_folder(bpy.types.Operator):
    """Open the folder containing the current .blend file"""
    bl_idname = "rextools3.open_folder"
    bl_label = "Open Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fp = bpy.data.filepath
        if not fp:
            self.report({'ERROR'}, "Blend file is not saved yet. Please save first.")
            return {'CANCELLED'}

        folder = os.path.dirname(fp)
        if sys.platform.startswith('win'):
            os.startfile(folder)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])

        return {'FINISHED'}
