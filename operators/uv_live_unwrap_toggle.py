import bpy

class REX_OT_toggle_live_unwrap(bpy.types.Operator):
    bl_idname = "rextools3.toggle_live_unwrap"
    bl_label = "Toggle Live Unwrap"
    bl_description = "Temporarily switch this area to UV Editor, toggle live-unwrap, then restore"

    def execute(self, context):
        area = context.area
        tool = context.scene.tool_settings

        # flip the edge-path live unwrap flag
        new_state = not tool.use_edge_path_live_unwrap

        # 1) switch this area to IMAGE_EDITOR so we can reach uv_editor
        orig_type = area.type
        try:
            area.type = 'IMAGE_EDITOR'
            space = area.spaces.active
            uv = space.uv_editor            
            uv.use_live_unwrap = new_state  
        finally:
            # 2) restore original area type
            area.type = orig_type

        # 3) ensure we're in Edit Mesh mode
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        # 4) toggle the scene’s edge-path live unwrap
        tool.use_edge_path_live_unwrap = new_state

        self.report({'INFO'}, f"Live Unwrap {'Enabled' if new_state else 'Disabled'}")
        return {'FINISHED'}
