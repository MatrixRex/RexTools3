import bpy

class REX_OT_mark_seams_from_islands(bpy.types.Operator):
    bl_idname = "rextools3.mark_seams_from_islands"
    bl_label = "Mark Seams from Islands"
    bl_description = "Mark seams around UV island borders (from Edit Mesh mode)"

    
    def execute(self, context):
        area = context.area
        orig_type = area.type
        

          # 1) switch this area to IMAGE_EDITOR so we can reach uv_editor
        orig_type = area.type
        try:
            area.type = 'IMAGE_EDITOR'
            space = area.spaces.active
            uv = space.uv_editor
            bpy.context.area.ui_type = 'UV'
            
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands()
            bpy.ops.uv.select_all(action='DESELECT')

        finally:
            # 2) restore original area type
            area.type = orig_type

        self.report({'INFO'}, "Seams marked from UV islands")
        return {'FINISHED'}


