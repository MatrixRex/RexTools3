import bpy
from bpy.props import StringProperty, BoolProperty

class REXTOOLS3_OT_pick_folder(bpy.types.Operator):
    """Select a directory"""
    bl_idname = "rextools3.pick_folder"
    bl_label = "Accept"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    directory: StringProperty(
        name="Outdir Path",
        description="Choose a directory",
        subtype='DIR_PATH',
    )
    
    filter_folder: BoolProperty(
        default=True,
        options={'HIDDEN'},
    )
    
    target_path: StringProperty()
    
    def update_reset(self, context):
        if self.reset_to_blend:
            if bpy.data.is_saved and bpy.data.filepath:
                self.directory = bpy.path.abspath("//")
            self.reset_to_blend = False

    reset_to_blend: BoolProperty(
        name="Reset to Blend Folder",
        description="Go to the directory of the current blend file",
        update=update_reset
    )
    
    def invoke(self, context, event):
        if self.target_path:
            try:
                parts = self.target_path.split('.')
                obj = context
                for p in parts[:-1]:
                    if p == 'scene': obj = context.scene
                    elif p == 'collection': obj = context.collection
                    elif p == 'object': obj = context.object
                    else: obj = getattr(obj, p)
                current_val = getattr(obj, parts[-1])
                
                if current_val:
                    self.directory = bpy.path.abspath(current_val)
                elif bpy.data.is_saved and bpy.data.filepath:
                    self.directory = bpy.path.abspath("//")
            except Exception as e:
                print(f"[RexTools3] Error resolving path for pick_folder: {e}")
                
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "reset_to_blend", icon='FILE_REFRESH', toggle=True)
        
    def execute(self, context):
        if self.target_path and self.directory:
            try:
                parts = self.target_path.split('.')
                obj = context
                for p in parts[:-1]:
                    if p == 'scene': obj = context.scene
                    elif p == 'collection': obj = context.collection
                    elif p == 'object': obj = context.object
                    else: obj = getattr(obj, p)
                    
                setattr(obj, parts[-1], self.directory)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to set path: {e}")
                
        return {'FINISHED'}
