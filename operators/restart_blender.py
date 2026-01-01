import bpy
import subprocess
import sys
import os

class REXTOOLS3_OT_restart_blender(bpy.types.Operator):
    bl_idname = "rextools3.restart_blender"
    bl_label = "Restart Blender"
    bl_description = "Close Blender and reopen it with the current file"
    bl_options = {'REGISTER'}

    def execute(self, context):
        filepath = bpy.data.filepath
        executable = sys.executable
        
        args = [executable]
        if filepath and os.path.exists(filepath):
            args.append(filepath)
            
        try:
            if os.name == 'nt':
                # Windows: Create a truly independent process
                # DETACHED_PROCESS (0x00000008) + CREATE_NEW_PROCESS_GROUP (0x00000200)
                # Redirecting all I/O to DEVNULL is critical for some setups
                # Also, using shell=True can sometimes help with 'detached' processes on Windows
                creation_flags = 0x00000008 | 0x00000200
                subprocess.Popen(
                    args, 
                    creationflags=creation_flags, 
                    close_fds=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Unix-like
                subprocess.Popen(args, start_new_session=True)
                
            # Quit Blender
            # We use a short timer to ensure the subprocess has a chance to start 
            # before the parent process completely shuts down, although Popen is non-blocking.
            bpy.ops.wm.quit_blender()
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to restart: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

def register():
    pass

def unregister():
    pass
