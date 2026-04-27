import bpy
from bpy.types import Operator

class REXTOOLS3_OT_NlaCreateTrackFromAction(Operator):
    """Create a new NLA track from the current action and clear the active action"""
    bl_idname = "rextools3.nla_create_track_from_action"
    bl_label = "New Track"
    bl_description = "Create a new NLA track, add current action as a strip at frame 0, rename track to action name, and clear active action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.animation_data and obj.animation_data.action

    def execute(self, context):
        obj = context.active_object
        anim_data = obj.animation_data
        action = anim_data.action

        # 1. Create a new NLA track
        track = anim_data.nla_tracks.new()
        
        # 2. Rename track name to that action name
        track.name = action.name
        
        # 3. Add the current action to that track as a strip
        # track.strips.new(name, start, action)
        strip = track.strips.new(action.name, 0, action)
        
        # 4. On that tracks active strip property set frame start to be 0
        strip.frame_start = 0
        
        # 5. Clear the active action as requested
        anim_data.action = None
        
        self.report({'INFO'}, f"Action '{action.name}' pushed to NLA track '{track.name}'")
        
        return {'FINISHED'}

def draw_nla_button(self, context):
    # Only show in Action Editor mode
    if context.space_data.type == 'DOPESHEET_EDITOR' and context.space_data.mode == 'ACTION':
        layout = self.layout
        layout.separator()
        layout.operator("rextools3.nla_create_track_from_action", text="New Track", icon='NLA')

def register():
    # Append the UI to the Action Editor header
    bpy.types.DOPESHEET_HT_header.append(draw_nla_button)

def unregister():
    # Remove the UI from the Action Editor header
    bpy.types.DOPESHEET_HT_header.remove(draw_nla_button)
